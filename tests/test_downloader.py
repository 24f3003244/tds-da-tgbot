import pytest
from pathlib import Path
from app.downloader import DatasetDownloader


def test_url_normalization():
    downloader = DatasetDownloader()

    # Test GitHub blob URL normalization
    gh_url = "https://github.com/user/repo/blob/main/data.csv"
    norm_gh = downloader.normalize_url(gh_url)
    assert norm_gh == "https://raw.githubusercontent.com/user/repo/main/data.csv"

    # Test Google Sheets URL normalization
    gs_url = "https://docs.google.com/spreadsheets/d/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms/edit#gid=0"
    norm_gs = downloader.normalize_url(gs_url)
    assert norm_gs == "https://docs.google.com/spreadsheets/d/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms/export?format=csv"


def test_cache_path_generation(tmp_path):
    downloader = DatasetDownloader(cache_dir=str(tmp_path))
    url = "https://example.com/test.csv"
    path = downloader.get_cache_path(url, ".csv")
    assert str(path).startswith(str(tmp_path))
    assert path.suffix == ".csv"
