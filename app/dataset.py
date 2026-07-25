import io
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import pandas as pd
import polars as pl
from app.schemas import DatasetInfo


class DatasetLoader:
    """Parses, loads, and summarizes tabular datasets from files, URLs, or inline message text."""

    @staticmethod
    def extract_urls(text: str) -> List[str]:
        """Extracts HTTP/HTTPS dataset URLs from text message."""
        clean_text = re.sub(r'[\xa0\u2000-\u200b\u202f\u205f\u3000]', ' ', text)
        url_pattern = r'https?://[^\s<>"]+|www\.[^\s<>"]+'
        matches = re.findall(url_pattern, clean_text)
        return [m.rstrip(".,;)") for m in matches]

    @staticmethod
    def parse_inline_dataset(text: str) -> Optional[pd.DataFrame]:
        """Attempts to parse inline dataset embedded in text message (CSV, JSON, Markdown table)."""
        clean_text = re.sub(r'[\xa0\u2000-\u200b\u202f\u205f\u3000]', ' ', text)
        text_strip = clean_text.strip()

        # Check for JSON array or object anywhere in text
        json_matches = re.findall(r"(\[[\s\S]*?\]|\{[\s\S]*?\})", clean_text)
        for json_str in json_matches:
            try:
                data = json.loads(json_str.strip())
                if isinstance(data, list) and len(data) > 0:
                    return pd.DataFrame(data)
                elif isinstance(data, dict) and len(data) > 0:
                    return pd.DataFrame(data if any(isinstance(v, list) for v in data.values()) else [data])
            except Exception:
                continue


        # Check for code blocks containing CSV or JSON
        code_block_match = re.search(r"```(?:csv|json|text|data)?\s*\n(.*?)\n```", text, re.DOTALL | re.IGNORECASE)
        if code_block_match:
            block_content = code_block_match.group(1).strip()
            df = DatasetLoader.parse_inline_dataset(block_content)
            if df is not None:
                return df

        # Check for Markdown table format (| col1 | col2 |)
        if "|" in text_strip and "\n" in text_strip:
            lines = [line.strip() for line in text_strip.split("\n") if line.strip().startswith("|")]
            if len(lines) >= 2:
                try:
                    # Remove border pipes and clean headers/rows
                    clean_lines = []
                    for line in lines:
                        parts = [p.strip() for p in line.split("|")[1:-1]]
                        if all(re.match(r"^:?-+:?$", p) for p in parts):  # skip divider row |---|---|
                            continue
                        clean_lines.append(parts)

                    if len(clean_lines) >= 2:
                        headers = clean_lines[0]
                        rows = clean_lines[1:]
                        return pd.DataFrame(rows, columns=headers)
                except Exception:
                    pass

        # Check for CSV text (has commas/newlines and multiple lines)
        if "\n" in text_strip and ("," in text_strip or "\t" in text_strip):
            try:
                sep = "\t" if "\t" in text_strip and "," not in text_strip else ","
                df = pd.read_csv(io.StringIO(text_strip), sep=sep)
                if len(df.columns) > 1 and len(df) > 0:
                    return df
            except Exception:
                pass

        return None

    @staticmethod
    def load_file(file_path: Path) -> pd.DataFrame:
        """Loads file into Pandas DataFrame based on file extension."""
        ext = file_path.suffix.lower()
        try:
            if ext in [".csv", ".txt"]:
                # Try UTF-8 first, fallback to latin-1
                try:
                    return pd.read_csv(file_path)
                except UnicodeDecodeError:
                    return pd.read_csv(file_path, encoding="latin-1")
            elif ext == ".tsv":
                return pd.read_csv(file_path, sep="\t")
            elif ext == ".json":
                return pd.read_json(file_path)
            elif ext in [".xlsx", ".xls"]:
                return pd.read_excel(file_path)
            elif ext == ".parquet":
                return pd.read_parquet(file_path)
            else:
                # Default fallback: attempt read_csv
                return pd.read_csv(file_path)
        except Exception as e:
            raise ValueError(f"Unable to parse dataset file '{file_path.name}': {str(e)}") from e

    @staticmethod
    def summarize_dataframe(df: pd.DataFrame, source: str = "dataset") -> DatasetInfo:
        """Generates structured summary metadata of a DataFrame for LLM inspection."""
        row_count, col_count = df.shape
        columns = list(df.columns.astype(str))
        dtypes = {col: str(df[col].dtype) for col in df.columns}

        # Convert sample data (first 5 rows) handling NaNs and timestamps
        sample_df = df.head(5).copy()
        sample_data = json.loads(sample_df.to_json(orient="records", date_format="iso"))

        # Numeric summary stats
        summary_stats = {}
        try:
            numeric_cols = df.select_dtypes(include=["number"]).columns
            if len(numeric_cols) > 0:
                describe_dict = json.loads(df[numeric_cols].describe().to_json())
                summary_stats = describe_dict
        except Exception:
            pass

        return DatasetInfo(
            source=source,
            file_type="dataframe",
            row_count=row_count,
            column_count=col_count,
            columns=columns,
            sample_data=sample_data,
            dtypes=dtypes,
            summary_stats=summary_stats
        )


dataset_loader = DatasetLoader()
