"""ARIMA model — Phase 2."""
import pandas as pd
from fundlens.models.base_model import BaseModel


class ArimaModel(BaseModel):
    """Auto-ARIMA wrapper using pmdarima.auto_arima for order selection."""

    name = "arima"

    def fit(self, prices: pd.Series) -> None:
        # TODO: implement in Phase 2
        raise NotImplementedError

    def predict(self, horizon: int) -> pd.DataFrame:
        raise NotImplementedError

    def score(self, prices: pd.Series, horizon: int, n_splits: int = 20) -> dict[str, float]:
        raise NotImplementedError
