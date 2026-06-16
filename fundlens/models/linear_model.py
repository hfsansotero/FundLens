"""Ridge regression on lag features — simple autoregressive baseline."""

import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge

from fundlens.models.base_model import BaseModel
from fundlens.models.comparison import future_dates, walk_forward

_WINDOW = 20


def _lag_features(vals: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    X = [vals[i - _WINDOW:i] for i in range(_WINDOW, len(vals))]
    y = [vals[i] for i in range(_WINDOW, len(vals))]
    return np.array(X), np.array(y)


class LinearModel(BaseModel):
    name = "linear"

    def fit(self, prices: pd.Series) -> None:
        X, y = _lag_features(prices.values)
        self._model = Ridge(alpha=1.0).fit(X, y)
        self._buf = list(prices.values[-_WINDOW:])
        self._prices = prices

    def predict(self, horizon: int) -> pd.DataFrame:
        buf = self._buf.copy()
        preds = []
        for _ in range(horizon):
            p = float(self._model.predict([buf[-_WINDOW:]])[0])
            preds.append(p)
            buf.append(p)
        return pd.DataFrame({
            "date": future_dates(self._prices, horizon),
            "predicted_value": preds,
            "lower_bound": None,
            "upper_bound": None,
        })

    def score(self, prices: pd.Series, horizon: int, n_splits: int = 20) -> dict[str, float]:
        return walk_forward(self, prices, horizon, n_splits)
