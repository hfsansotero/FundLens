"""Shared data loading and metric helpers for dashboard pages."""

from datetime import date, timedelta
import numpy as np
import pandas as pd
import streamlit as st

from fundlens.storage.database import get_session
from fundlens.storage import repository as repo

PERIOD_OPTIONS = ["1W", "2W", "1M", "3M", "6M", "1Y", "3Y", "5Y", "All", "Custom"]
_PERIOD_DELTA = {
    "1W": timedelta(weeks=1), "2W": timedelta(weeks=2), "1M": timedelta(days=30),
    "3M": timedelta(days=91), "6M": timedelta(days=182), "1Y": timedelta(days=365),
    "3Y": timedelta(days=365 * 3), "5Y": timedelta(days=365 * 5),
}


@st.cache_data(ttl=300)
def load_funds() -> list[dict]:
    with get_session() as session:
        return [
            {"id": f.id, "ticker": f.ticker, "name": f.name or f.ticker,
             "category": f.category, "manager": f.manager}
            for f in repo.get_all_active_funds(session)
        ]


def fund_label(f: dict) -> str:
    """Ticker + name (+ category/manager) — lets st.selectbox's built-in
    type-to-filter double as a search across all of those fields."""
    bits = [f["ticker"], f["name"], f.get("category"), f.get("manager")]
    return " — ".join(b for b in bits if b)


@st.cache_data(ttl=300)
def load_prices(fund_id: int) -> pd.DataFrame:
    with get_session() as session:
        return repo.get_prices_df(session, fund_id)


def period_picker(key: str, default: str = "1Y") -> tuple[date | None, date | None]:
    """Period radio (incl. custom date range). Returns (start, end); both None = 'All'."""
    period = st.radio("Period", PERIOD_OPTIONS, horizontal=True,
                       index=PERIOD_OPTIONS.index(default), key=f"{key}_period")
    today = date.today()
    if period == "All":
        return None, None
    if period != "Custom":
        return today - _PERIOD_DELTA[period], today

    lo = today - timedelta(days=365 * 10)
    to_key, from_key = f"{key}_to", f"{key}_from"
    cur_to = st.session_state.get(to_key, today)
    cur_from = st.session_state.get(from_key, today - timedelta(days=365))
    c1, c2 = st.columns(2)
    start = c1.date_input("From", value=cur_from, min_value=lo,
                           max_value=min(cur_to - timedelta(days=1), today), key=from_key)
    end = c2.date_input("To", value=cur_to, min_value=start + timedelta(days=1),
                         max_value=today, key=to_key)
    return start, end


def filter_range(df: pd.DataFrame, start: date | None, end: date | None) -> pd.DataFrame:
    if df.empty:
        return df
    out = df
    if start is not None:
        out = out[out["date"] >= start]
    if end is not None:
        out = out[out["date"] <= end]
    return out.reset_index(drop=True)


def period_return(df: pd.DataFrame) -> float:
    """% change from the first to the last NAV in an already-filtered df."""
    if len(df) < 2:
        return float("nan")
    return (float(df.iloc[-1]["nav"]) / float(df.iloc[0]["nav"]) - 1) * 100


def day_change(df: pd.DataFrame) -> float:
    """Latest 1-day NAV change %, from the full (unfiltered) series — independent
    of the period selector, so the Overview table has something that moves daily."""
    if len(df) < 2:
        return float("nan")
    return (float(df.iloc[-1]["nav"]) / float(df.iloc[-2]["nav"]) - 1) * 100


def vol_30d(df: pd.DataFrame) -> float:
    lr = df["log_return"].dropna()
    return float(lr.tail(30).std() * np.sqrt(252) * 100) if len(lr) >= 20 else float("nan")


def max_drawdown(nav: pd.Series) -> float:
    return float((nav / nav.cummax() - 1).min() * 100) if len(nav) else float("nan")


def drawdown_series(nav: pd.Series) -> pd.Series:
    return (nav / nav.cummax() - 1) * 100


def arrow(pct: float) -> str:
    """📈/📉 prefix — paired with colorize() below for actual green/red text."""
    if pd.isna(pct):
        return "—"
    return f"📈 {pct:+.2f}%" if pct >= 0 else f"📉 {pct:+.2f}%"


def _arrow_color(v: str) -> str:
    if isinstance(v, str) and v.startswith("📈"):
        return "color: #1a7f37; font-weight: 600"
    if isinstance(v, str) and v.startswith("📉"):
        return "color: #cf222e; font-weight: 600"
    return ""


def colorize(df: pd.DataFrame, arrow_cols: list[str], fmt: dict | None = None):
    """Styler with green/red text on arrow_cols (from arrow()) + optional number formats."""
    styler = df.style
    if fmt:
        styler = styler.format(fmt)
    return styler.map(_arrow_color, subset=arrow_cols)
