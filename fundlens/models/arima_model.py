"""ARIMA(1,1,1) price forecaster using statsmodels."""

import warnings
import numpy as np
import pandas as pd

from fundlens.models.base_model import BaseModel
from fundlens.models.comparison import future_dates, walk_forward


class ArimaModel(BaseModel):
    name = "arima"

    def fit(self, prices: pd.Series) -> None:
        from statsmodels.tsa.arima.model import ARIMA  # lazy: not in [dev]
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            self._result = ARIMA(prices.values, order=(1, 1, 1)).fit()
        self._prices = prices

    def predict(self, horizon: int) -> pd.DataFrame:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            fc = self._result.get_forecast(steps=horizon)
        pred = fc.predicted_mean
        ci = fc.conf_int()
        return pd.DataFrame({
            "date": future_dates(self._prices, horizon),
            "predicted_value": pred,
            "lower_bound": ci.iloc[:, 0].values,
            "upper_bound": ci.iloc[:, 1].values,
        })

    def score(self, prices: pd.Series, horizon: int, n_splits: int = 20) -> dict[str, float]:
        return walk_forward(self, prices, horizon, n_splits)
