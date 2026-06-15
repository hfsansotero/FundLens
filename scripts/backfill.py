"""Backfill missing NAV rows for a date range.

Usage:
    python scripts/backfill.py --start 2024-01-01 --end 2024-03-31
    python scripts/backfill.py --ticker VFINX --start 2024-01-01 --end 2024-01-31
"""

import argparse
from loguru import logger

from fundlens.ingestion.yfinance_source import YFinanceSource
from fundlens.storage.database import get_session
from fundlens.storage import repository as repo


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--start", required=True, help="Start date YYYY-MM-DD")
    p.add_argument("--end", required=True, help="End date YYYY-MM-DD")
    p.add_argument("--ticker", help="Only backfill this ticker (omit for all active funds)")
    return p.parse_args()


def main():
    args = parse_args()
    source = YFinanceSource()

    with get_session() as session:
        funds = repo.get_all_active_funds(session)
        if args.ticker:
            funds = [f for f in funds if f.ticker == args.ticker]

        for fund in funds:
            logger.info(f"Backfilling {fund.ticker} [{args.start} → {args.end}]")
            try:
                df = source.fetch(fund.ticker, args.start, args.end)
                if not df.empty:
                    inserted = repo.upsert_prices(session, fund.id, df)
                    logger.success(f"{fund.ticker}: {inserted} new rows")
                else:
                    logger.warning(f"{fund.ticker}: empty response")
            except Exception as e:
                logger.error(f"{fund.ticker}: {e}")

        session.commit()


if __name__ == "__main__":
    main()
