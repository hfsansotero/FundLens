"""Shared data loading and metric helpers for dashboard pages."""

from datetime import date
import numpy as np
import pandas as pd
import streamlit as st

from fundlens.storage.database import get_session
from fundlens.storage import repository as repo

PERIOD_DAYS = {"1Y": 252, "3Y": 756, "5Y": 1260, "All": None}


@st.cache_data(ttl=300)
def load_funds() -> list[dict]:
    with get_session() as session:
        return [
            {"id": f.id, "ticker": f.ticker, "name": f.name or f.ticker}
            for f in repo.get_all_active_funds(session)
        ]


@st.cache_data(ttl=300)
def load_prices(fund_id: int) -> pd.DataFrame:
    with get_session() as session:
        return repo.get_prices_df(session, fund_id)


def filter_period(df: pd.DataFrame, period: str) -> pd.DataFrame:
    days = PERIOD_DAYS[period]
    return df.tail(days).reset_index(drop=True) if days else df.reset_index(drop=True)


def ytd_return(df: pd.DataFrame) -> float:
    ytd = df[df["date"] >= date(date.today().year, 1, 1)]
    if ytd.empty or df.empty:
        return float("nan")
    return (float(df.iloc[-1]["nav"]) / float(ytd.iloc[0]["nav"]) - 1) * 100


def vol_30d(df: pd.DataFrame) -> float:
    lr = df["log_return"].dropna()
    return float(lr.tail(30).std() * np.sqrt(252) * 100) if len(lr) >= 20 else float("nan")


def max_drawdown(nav: pd.Series) -> float:
    return float((nav / nav.cummax() - 1).min() * 100)


def drawdown_series(nav: pd.Series) -> pd.Series:
    return (nav / nav.cummax() - 1) * 100
