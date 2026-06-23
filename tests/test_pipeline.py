"""Tests for pipeline orchestration."""

import pytest
from unittest.mock import patch, MagicMock
from datetime import date

from fundlens.pipeline.daily_update import run_daily_update, _update_fund


@patch("fundlens.pipeline.daily_update.init_db")
@patch("fundlens.pipeline.daily_update.get_session")
@patch("fundlens.pipeline.daily_update.repo")
def test_daily_update_logs_on_empty_source(mock_repo, mock_session, mock_init):
    mock_repo.get_all_active_funds.return_value = []
    run_daily_update(target_date=date(2024, 1, 15))
    mock_init.assert_called_once()


@patch("fundlens.pipeline.daily_update.repo")
def test_update_fund_uses_exclusive_end_date(mock_repo):
    """yfinance's `end` is exclusive — start==end would always return empty."""
    fund = MagicMock(ticker="VFINX", id=1)
    source = MagicMock()
    source.is_available.return_value = True
    source.fetch.return_value = MagicMock(empty=True)

    _update_fund(MagicMock(), fund, date(2024, 1, 15), source, MagicMock())

    source.fetch.assert_called_once_with("VFINX", "2024-01-15", "2024-01-16")
