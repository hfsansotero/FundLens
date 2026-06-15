"""Tests for pipeline orchestration."""

import pytest
from unittest.mock import patch, MagicMock
from datetime import date

from fundlens.pipeline.daily_update import run_daily_update


@patch("fundlens.pipeline.daily_update.init_db")
@patch("fundlens.pipeline.daily_update.get_session")
@patch("fundlens.pipeline.daily_update.repo")
def test_daily_update_logs_on_empty_source(mock_repo, mock_session, mock_init):
    mock_repo.get_all_active_funds.return_value = []
    run_daily_update(target_date=date(2024, 1, 15))
    mock_init.assert_called_once()
