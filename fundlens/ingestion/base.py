from abc import ABC, abstractmethod
import pandas as pd


class DataSource(ABC):
    """Contract that every data source must satisfy.

    fetch() must return a DataFrame with columns: date (DATE), nav (float),
    log_return (float | None), source (str). One row per trading day.
    Missing days (weekends, holidays) must be omitted — never NaN rows.
    """

    @abstractmethod
    def fetch(self, ticker: str, start: str, end: str) -> pd.DataFrame:
        """Fetch NAV series for ticker between start and end (YYYY-MM-DD)."""
        ...

    @abstractmethod
    def is_available(self) -> bool:
        """Return True if the source is reachable (e.g. API key valid, network ok)."""
        ...
