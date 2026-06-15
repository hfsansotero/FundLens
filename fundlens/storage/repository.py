"""All DB reads and writes go through here. No raw SQL outside this module."""

from datetime import date
from typing import Optional
import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy import select

from fundlens.storage.models import Fund, Price, Metric, IngestionLog


# ── Funds ─────────────────────────────────────────────────────────────────────

def get_or_create_fund(session: Session, ticker: str, **kwargs) -> Fund:
    fund = session.scalar(select(Fund).where(Fund.ticker == ticker))
    if fund is None:
        fund = Fund(ticker=ticker, **kwargs)
        session.add(fund)
        session.flush()
    return fund


def get_all_active_funds(session: Session) -> list[Fund]:
    return list(session.scalars(select(Fund).where(Fund.active == True)))  # noqa: E712


# ── Prices ────────────────────────────────────────────────────────────────────

def upsert_prices(session: Session, fund_id: int, df: pd.DataFrame) -> int:
    """Insert price rows, skip existing (fund_id, date) pairs. Returns inserted count."""
    existing = {
        row.date
        for row in session.scalars(
            select(Price.date).where(Price.fund_id == fund_id)
        )
    }
    new_rows = [
        Price(
            fund_id=fund_id,
            date=row["date"],
            nav=row["nav"],
            log_return=row.get("log_return"),
            source=row.get("source"),
        )
        for _, row in df.iterrows()
        if row["date"] not in existing
    ]
    session.add_all(new_rows)
    return len(new_rows)


def get_prices_df(session: Session, fund_id: int, start: Optional[date] = None, end: Optional[date] = None) -> pd.DataFrame:
    stmt = select(Price).where(Price.fund_id == fund_id).order_by(Price.date)
    if start:
        stmt = stmt.where(Price.date >= start)
    if end:
        stmt = stmt.where(Price.date <= end)
    rows = session.scalars(stmt).all()
    return pd.DataFrame(
        [{"date": r.date, "nav": float(r.nav), "log_return": float(r.log_return) if r.log_return else None}
         for r in rows]
    )


# ── Ingestion Log ─────────────────────────────────────────────────────────────

def log_ingestion(session: Session, fund_id: Optional[int], date_: date, status: str,
                  source: Optional[str] = None, error_msg: Optional[str] = None) -> None:
    session.add(IngestionLog(fund_id=fund_id, date=date_, status=status, source=source, error_msg=error_msg))
