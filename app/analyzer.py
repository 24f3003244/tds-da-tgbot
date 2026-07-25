import math
import re
from typing import Any, Dict, List, Optional, Union
import duckdb
import numpy as np
import pandas as pd
import polars as pl


class AnalysisError(Exception):
    """Custom exception raised during data analysis execution."""
    pass


class DataAnalyzer:
    """
    Data Analysis Engine combining Pandas, Polars, and DuckDB SQL query execution.
    Provides execution capabilities for statistical computations and dataset transformations.
    """

    def __init__(self):
        self.duckdb_conn = duckdb.connect(database=":memory:")

    def register_dataframe(self, name: str, df: pd.DataFrame) -> None:
        """Registers a pandas DataFrame into DuckDB memory for SQL queries."""
        # Sanitize name to valid SQL identifier
        safe_name = re.sub(r"\W+", "_", name).strip("_") or "df"
        try:
            self.duckdb_conn.register(safe_name, df)
        except Exception as e:
            raise AnalysisError(f"Failed to register DataFrame '{safe_name}' in DuckDB: {str(e)}")

    def run_duckdb(self, query: str) -> pd.DataFrame:
        """Executes DuckDB SQL query and returns result as Pandas DataFrame."""
        try:
            return self.duckdb_conn.execute(query).df()
        except Exception as e:
            raise AnalysisError(f"DuckDB SQL execution error: {str(e)}")

    def execute_python_code(self, code: str, dfs: Dict[str, pd.DataFrame]) -> Any:
        """
        Executes Python data analysis code in a safe execution scope.
        Returns the variable `result` assigned by the code.
        """
        local_scope = {
            "pd": pd,
            "np": np,
            "pl": pl,
            "duckdb": self.duckdb_conn,
            "math": math,
            "result": None,
            "dfs": dfs,
        }

        # Add DataFrames to local scope by key
        for name, df in dfs.items():
            safe_var = re.sub(r"\W+", "_", name).strip("_") or "df"
            local_scope[safe_var] = df
            self.register_dataframe(safe_var, df)
            if "df" not in local_scope:
                local_scope["df"] = df

        try:
            exec(code, {"__builtins__": __builtins__}, local_scope)
            return local_scope.get("result")
        except Exception as e:
            raise AnalysisError(f"Python code execution failed: {str(e)}")

    # High-level helper methods for analytical tasks
    def compute_summary_stats(self, df: pd.DataFrame, column: str) -> Dict[str, Any]:
        """Computes statistical metrics (mean, median, mode, std, var, min, max, missing count)."""
        if column not in df.columns:
            raise AnalysisError(f"Column '{column}' not found in dataset.")

        series = df[column].dropna()
        if series.empty:
            return {"count": 0, "missing": len(df)}

        is_numeric = pd.api.types.is_numeric_dtype(series)

        stats = {
            "count": int(len(series)),
            "missing": int(df[column].isna().sum()),
        }

        if is_numeric:
            stats.update({
                "mean": float(series.mean()),
                "median": float(series.median()),
                "std": float(series.std()) if len(series) > 1 else 0.0,
                "var": float(series.var()) if len(series) > 1 else 0.0,
                "min": float(series.min()),
                "max": float(series.max()),
            })
            mode_val = series.mode()
            if not mode_val.empty:
                stats["mode"] = float(mode_val.iloc[0])

        return stats

    def compute_correlation(self, df: pd.DataFrame, col1: str, col2: str) -> float:
        """Computes Pearson correlation coefficient between two numeric columns."""
        if col1 not in df.columns or col2 not in df.columns:
            raise AnalysisError(f"Columns '{col1}' or '{col2}' not found.")

        clean_df = df[[col1, col2]].dropna()
        if len(clean_df) < 2:
            return 0.0

        corr = clean_df[col1].corr(clean_df[col2])
        return float(corr) if not pd.isna(corr) else 0.0

    def compute_linear_regression(self, df: pd.DataFrame, x_col: str, y_col: str) -> Dict[str, float]:
        """Computes linear regression (slope, intercept, r_value) for x_col -> y_col."""
        clean_df = df[[x_col, y_col]].dropna()
        if len(clean_df) < 2:
            return {"slope": 0.0, "intercept": 0.0, "r_squared": 0.0}

        x = clean_df[x_col].values
        y = clean_df[y_col].values

        slope, intercept = np.polyfit(x, y, 1)
        r_matrix = np.corrcoef(x, y)
        r = r_matrix[0, 1] if r_matrix.shape == (2, 2) else 0.0

        return {
            "slope": float(slope),
            "intercept": float(intercept),
            "r_squared": float(r ** 2)
        }


analyzer_instance = DataAnalyzer()
