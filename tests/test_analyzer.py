import pandas as pd
import pytest
from app.analyzer import DataAnalyzer, AnalysisError


@pytest.fixture
def sample_df():
    return pd.DataFrame({
        "state": ["Assam", "Bihar", "Goa", "Assam", "Bihar"],
        "income": [1000, 2000, 3000, 1500, 2500],
        "score": [10.0, 20.0, 30.0, 40.0, 50.0]
    })


def test_register_and_duckdb_query(sample_df):
    analyzer = DataAnalyzer()
    analyzer.register_dataframe("test_df", sample_df)

    res_df = analyzer.run_duckdb("SELECT state, AVG(income) as avg_inc FROM test_df GROUP BY state ORDER BY state")
    assert len(res_df) == 3
    assert "avg_inc" in res_df.columns
    assert float(res_df[res_df["state"] == "Assam"]["avg_inc"].iloc[0]) == 1250.0


def test_execute_python_code(sample_df):
    analyzer = DataAnalyzer()
    code = "result = float(df['income'].mean())"
    res = analyzer.execute_python_code(code, {"df": sample_df})
    assert res == 2000.0


def test_compute_summary_stats(sample_df):
    analyzer = DataAnalyzer()
    stats = analyzer.compute_summary_stats(sample_df, "income")
    assert stats["count"] == 5
    assert stats["mean"] == 2000.0
    assert stats["median"] == 2000.0
    assert stats["min"] == 1000.0
    assert stats["max"] == 3000.0


def test_compute_correlation(sample_df):
    analyzer = DataAnalyzer()
    corr = analyzer.compute_correlation(sample_df, "income", "score")
    assert pytest.approx(corr, 0.01) == 0.5



def test_compute_linear_regression(sample_df):
    analyzer = DataAnalyzer()
    reg = analyzer.compute_linear_regression(sample_df, "income", "score")
    assert "slope" in reg
    assert "intercept" in reg
    assert "r_squared" in reg
    assert reg["slope"] > 0
