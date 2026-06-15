import numpy as np
import pandas as pd
import yfinance as yf
from loguru import logger

from fundlens.ingestion.base import DataSource


class YFinanceSource(DataSource):
    """Primary data source using yfinance (no API key required)."""

    SOURCE_NAME = "yfinance"

    def fetch(self, ticker: str, start: str, end: str) -> pd.DataFrame:
        logger.debug(f"yfinance fetch: {ticker} [{start} → {end}]")
        raw = yf.download(ticker, start=start, end=end, progress=False, auto_adjust=True)

        if raw.empty:
            logger.warning(f"yfinance returned empty data for {ticker}")
            return pd.DataFrame(columns=["date", "nav", "log_return", "source"])

        df = raw[["Close"]].rename(columns={"Close": "nav"}).reset_index()
        df.columns = ["date", "nav"]
        df["date"] = pd.to_datetime(df["date"]).dt.date
        df["nav"] = df["nav"].astype(float)

        df["log_return"] = np.log(df["nav"] / df["nav"].shift(1))
        df["source"] = self.SOURCE_NAME

        # Drop rows with NaN nav (should not happen, but defensive)
        df = df.dropna(subset=["nav"])
        return df.reset_index(drop=True)

    def is_available(self) -> bool:
        try:
            test = yf.download("SPY", period="1d", progress=False)
            return not test.empty
        except Exception:
            return False
