"""Tests for storage layer."""

from fundlens.storage import repository as repo
from fundlens.storage.models import Fund, Price


def test_get_or_create_fund_idempotent(session):
    f1 = repo.get_or_create_fund(session, "VFINX", name="Vanguard 500")
    f2 = repo.get_or_create_fund(session, "VFINX")
    assert f1.id == f2.id


def test_upsert_prices_no_duplicates(session, sample_df):
    fund = repo.get_or_create_fund(session, "TEST")
    first = repo.upsert_prices(session, fund.id, sample_df)
    second = repo.upsert_prices(session, fund.id, sample_df)
    assert first == len(sample_df)
    assert second == 0  # all already present


def test_get_prices_df_returns_sorted(session, sample_df):
    fund = repo.get_or_create_fund(session, "SORT_TEST")
    repo.upsert_prices(session, fund.id, sample_df)
    result = repo.get_prices_df(session, fund.id)
    assert list(result["date"]) == sorted(result["date"])
