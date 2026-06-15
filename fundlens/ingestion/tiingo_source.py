import numpy as np
import pandas as pd
import requests
from loguru import logger

from fundlens.ingestion.base import DataSource
from config.settings import settings


class TiingoSource(DataSource):
    """Backup data source using Tiingo REST API (free API key required)."""

    SOURCE_NAME = "tiingo"
    BASE_URL = "https://api.tiingo.com/tiingo/daily"

    def __init__(self) -> None:
        self._api_key = settings.tiingo_api_key

    def fetch(self, ticker: str, start: str, end: str) -> pd.DataFrame:
        if not self._api_key:
            raise ValueError("TIINGO_API_KEY not set in .env")

        logger.debug(f"Tiingo fetch: {ticker} [{start} → {end}]")
        url = f"{self.BASE_URL}/{ticker}/prices"
        params = {"startDate": start, "endDate": end, "token": self._api_key}
        resp = requests.get(url, params=params, timeout=15)
        resp.raise_for_status()

        raw = resp.json()
        if not raw:
            logger.warning(f"Tiingo returned empty data for {ticker}")
            return pd.DataFrame(columns=["date", "nav", "log_return", "source"])

        df = pd.DataFrame(raw)[["date", "adjClose"]].rename(columns={"adjClose": "nav"})
        df["date"] = pd.to_datetime(df["date"]).dt.date
        df["nav"] = df["nav"].astype(float)
        df = df.sort_values("date").reset_index(drop=True)

        df["log_return"] = np.log(df["nav"] / df["nav"].shift(1))
        df["source"] = self.SOURCE_NAME
        return df

    def is_available(self) -> bool:
        if not self._api_key:
            return False
        try:
            url = f"{self.BASE_URL}/SPY/prices"
            resp = requests.get(url, params={"token": self._api_key, "startDate": "2024-01-01", "endDate": "2024-01-05"}, timeout=10)
            return resp.status_code == 200
        except Exception:
            return False
