"""Tests for ingestion layer."""

import pandas as pd
import pytest
from unittest.mock import patch, MagicMock

from fundlens.ingestion.yfinance_source import YFinanceSource


def test_yfinance_returns_expected_columns():
    mock_df = pd.DataFrame({
        "Date": pd.to_datetime(["2024-01-02", "2024-01-03"]),
        "Close": [100.0, 101.5],
    }).set_index("Date")

    with patch("yfinance.download", return_value=mock_df):
        source = YFinanceSource()
        result = source.fetch("VFINX", "2024-01-02", "2024-01-03")

    assert set(["date", "nav", "log_return", "source"]).issubset(result.columns)
    assert len(result) == 2
    assert result["source"].iloc[0] == "yfinance"


def test_yfinance_empty_response_returns_empty_df():
    with patch("yfinance.download", return_value=pd.DataFrame()):
        source = YFinanceSource()
        result = source.fetch("FAKE", "2024-01-02", "2024-01-03")

    assert result.empty
