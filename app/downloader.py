import hashlib
import io
import os
import re
import zipfile
from pathlib import Path
from typing import Optional, Tuple, List
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from app.config import settings


class DownloaderError(Exception):
    """Custom exception for downloader operations."""
    pass


class DatasetDownloader:
    """Robust dataset downloader with URL normalization, retries, file caching, and ZIP extraction."""

    def __init__(self, cache_dir: Optional[str] = None):
        self.cache_dir = Path(cache_dir or settings.DATA_CACHE_DIR)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.max_size_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024

    @staticmethod
    def normalize_url(url: str) -> str:
        """Converts user-provided URLs to direct download links (GitHub raw, Google Sheets export, etc.)."""
        url = url.strip()

        # Handle GitHub blob URL -> raw content URL
        github_blob_pattern = r"^https?://github\.com/([^/]+)/([^/]+)/blob/(.+)$"
        gh_match = re.match(github_blob_pattern, url)
        if gh_match:
            user, repo, path = gh_match.groups()
            return f"https://raw.githubusercontent.com/{user}/{repo}/{path}"

        # Handle Google Sheets URL -> export as CSV
        gsheet_pattern = r"^https?://docs\.google\.com/spreadsheets/d/([^/]+)/"
        gs_match = re.match(gsheet_pattern, url)
        if gs_match:
            doc_id = gs_match.group(1)
            return f"https://docs.google.com/spreadsheets/d/{doc_id}/export?format=csv"

        return url

    def get_cache_path(self, url: str, file_ext: str = "") -> Path:
        """Generates a unique cache file path based on URL md5 hash."""
        url_hash = hashlib.md5(url.encode("utf-8")).hexdigest()
        filename = f"{url_hash}{file_ext}"
        return self.cache_dir / filename

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.HTTPError, httpx.TimeoutException)),
        reraise=True
    )
    async def download_file(self, url: str) -> Tuple[Path, str]:
        """
        Downloads file from URL async with retries and caching.
        Returns (cached_file_path, content_type_or_extension).
        """
        normalized_url = self.normalize_url(url)
        cache_path_raw = self.get_cache_path(normalized_url)

        # Return cached file if exists
        if cache_path_raw.exists() and cache_path_raw.stat().st_size > 0:
            return cache_path_raw, self._infer_extension(cache_path_raw)

        async with httpx.AsyncClient(timeout=settings.REQUEST_TIMEOUT, follow_redirects=True) as client:
            try:
                response = await client.get(normalized_url)
                response.raise_for_status()
            except Exception as e:
                raise DownloaderError(f"Failed to download URL '{url}': {str(e)}") from e

            # Check file size limit
            content_length = response.headers.get("content-length")
            if content_length and int(content_length) > self.max_size_bytes:
                raise DownloaderError(f"File size exceeds maximum allowed size ({settings.MAX_FILE_SIZE_MB}MB).")

            content = response.content
            if len(content) > self.max_size_bytes:
                raise DownloaderError(f"Downloaded content exceeds maximum allowed size ({settings.MAX_FILE_SIZE_MB}MB).")

            # Determine extension
            content_type = response.headers.get("content-type", "").lower()
            ext = self._get_extension_from_url_or_header(normalized_url, content_type)

            final_cache_path = self.get_cache_path(normalized_url, ext)

            # Check if zip file and contains single csv/json
            if ext == ".zip" or content.startswith(b"PK\x03\x04"):
                extracted_path = self._handle_zip_archive(content, final_cache_path)
                return extracted_path, self._infer_extension(extracted_path)

            with open(final_cache_path, "wb") as f:
                f.write(content)

            return final_cache_path, ext

    def _handle_zip_archive(self, zip_bytes: bytes, cache_path: Path) -> Path:
        """Extracts zip archive and returns the path to primary tabular file."""
        try:
            with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
                file_list = zf.namelist()
                # Find csv, tsv, json, parquet files
                candidates = [f for f in file_list if f.lower().endswith((".csv", ".tsv", ".json", ".parquet", ".xlsx"))]
                if not candidates:
                    candidates = [f for f in file_list if not f.endswith("/")]

                if not candidates:
                    raise DownloaderError("Zip archive contains no readable data files.")

                target_file = candidates[0]
                extracted_bytes = zf.read(target_file)

                ext = Path(target_file).suffix.lower() or ".csv"
                extracted_path = cache_path.with_suffix(ext)
                with open(extracted_path, "wb") as f:
                    f.write(extracted_bytes)
                return extracted_path
        except zipfile.BadZipFile as e:
            raise DownloaderError("Downloaded file is an invalid or corrupted ZIP archive.") from e

    def _get_extension_from_url_or_header(self, url: str, content_type: str) -> str:
        url_path = Path(url.split("?")[0])
        ext = url_path.suffix.lower()
        if ext in [".csv", ".tsv", ".json", ".parquet", ".xlsx", ".xls", ".zip"]:
            return ext

        if "json" in content_type:
            return ".json"
        elif "excel" in content_type or "spreadsheet" in content_type:
            return ".xlsx"
        elif "zip" in content_type:
            return ".zip"
        elif "parquet" in content_type:
            return ".parquet"
        return ".csv"

    def _infer_extension(self, path: Path) -> str:
        return path.suffix.lower() or ".csv"


downloader_instance = DatasetDownloader()
