"""ETS / Holt-Winters exponential smoothing forecaster."""

import numpy as np
import pandas as pd

from fundlens.models.base_model import BaseModel
from fundlens.models.comparison import future_dates, walk_forward


class ETSModel(BaseModel):
    name = "ets"

    def fit(self, prices: pd.Series) -> None:
        from statsmodels.tsa.holtwinters import ExponentialSmoothing  # lazy: not in [dev]
        self._model = ExponentialSmoothing(
            prices.values, trend="add", seasonal=None, damped_trend=True
        ).fit(optimized=True)
        self._prices = prices

    def predict(self, horizon: int) -> pd.DataFrame:
        fc = self._model.forecast(horizon)
        return pd.DataFrame({
            "date": future_dates(self._prices, horizon),
            "predicted_value": fc,
            "lower_bound": None,
            "upper_bound": None,
        })

    def score(self, prices: pd.Series, horizon: int, n_splits: int = 20) -> dict[str, float]:
        return walk_forward(self, prices, horizon, n_splits)
