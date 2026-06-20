"""Historical data load. Run once to seed the DB with N years of NAVs.

Usage:
    python scripts/initial_load.py --tickers VFINX FCNTX VBMFX --years 5
    python scripts/initial_load.py --all-funds --years 10
"""

import argparse
from datetime import date, timedelta

import yaml
from loguru import logger

from config.settings import settings
from fundlens.ingestion.yfinance_source import YFinanceSource
from fundlens.ingestion.tiingo_source import TiingoSource
from fundlens.storage.database import get_session, init_db
from fundlens.storage import repository as repo


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--tickers", nargs="+", help="Specific tickers to load")
    p.add_argument("--all-funds", action="store_true", help="Load all funds from config/funds.yaml")
    p.add_argument("--years", type=int, default=5, help="Years of history to load (default: 5)")
    return p.parse_args()


def load_fund_config() -> list[dict]:
    with open(settings.funds_config) as f:
        return yaml.safe_load(f)["funds"]


def main():
    args = parse_args()
    init_db()

    fund_configs = load_fund_config()

    if args.all_funds:
        targets = fund_configs
    elif args.tickers:
        config_map = {f["ticker"]: f for f in fund_configs}
        targets = [config_map.get(t, {"ticker": t}) for t in args.tickers]
    else:
        logger.error("Specify --tickers or --all-funds")
        raise SystemExit(1)

    end = date.today().isoformat()
    start = (date.today() - timedelta(days=args.years * 365)).isoformat()
    source = YFinanceSource()

    logger.info(f"Loading {len(targets)} fund(s) from {start} to {end}")

    with get_session() as session:
        for fund_cfg in targets:
            ticker = fund_cfg["ticker"]
            logger.info(f"Fetching {ticker}...")

            fund = repo.get_or_create_fund(
                session, ticker,
                isin=fund_cfg.get("isin"),
                name=fund_cfg.get("name"),
                category=fund_cfg.get("category"),
                manager=fund_cfg.get("manager"),
                currency=fund_cfg.get("currency", "USD"),
            )

            try:
                df = source.fetch(ticker, start, end)
                if df.empty:
                    logger.warning(f"{ticker}: no data returned")
                    repo.log_ingestion(session, fund.id, date.today(), "missing_from_source", "yfinance")
                    continue

                inserted = repo.upsert_prices(session, fund.id, df)
                repo.log_ingestion(session, fund.id, date.today(), "success", "yfinance/initial_load")
                logger.success(f"{ticker}: {inserted} rows inserted ({len(df)} total fetched)")
            except Exception as e:
                repo.log_ingestion(session, fund.id, date.today(), "failed", None, str(e))
                logger.error(f"{ticker} failed: {e}")

        session.commit()

    logger.success("Initial load complete.")


if __name__ == "__main__":
    main()
