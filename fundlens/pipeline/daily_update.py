"""Daily pipeline job: fetch today's NAV → store → update metrics."""

from datetime import date, timedelta
from loguru import logger

from fundlens.ingestion.yfinance_source import YFinanceSource
from fundlens.ingestion.tiingo_source import TiingoSource
from fundlens.storage.database import get_session, init_db
from fundlens.storage import repository as repo


def run_daily_update(target_date: date | None = None) -> None:
    target_date = target_date or date.today()
    logger.info(f"Daily update started for {target_date}")

    primary = YFinanceSource()
    backup = TiingoSource()

    init_db()
    with get_session() as session:
        funds = repo.get_all_active_funds(session)
        for fund in funds:
            _update_fund(session, fund, target_date, primary, backup)
        session.commit()

    logger.info("Daily update complete")


def _update_fund(session, fund, target_date, primary, backup):
    # yfinance's end is exclusive — same start/end always returns empty.
    start = str(target_date)
    end = str(target_date + timedelta(days=1))
    source = primary if primary.is_available() else backup

    try:
        df = source.fetch(fund.ticker, start, end)
        if df.empty:
            repo.log_ingestion(session, fund.id, target_date, "missing_from_source", source.SOURCE_NAME)
            return
        inserted = repo.upsert_prices(session, fund.id, df)
        repo.log_ingestion(session, fund.id, target_date, "success", source.SOURCE_NAME)
        logger.info(f"{fund.ticker}: {inserted} row(s) inserted")
    except Exception as e:
        repo.log_ingestion(session, fund.id, target_date, "failed", None, str(e))
        logger.error(f"{fund.ticker} failed: {e}")
