"""Gradient-boosted tree models: XGBoost and LightGBM."""

import numpy as np
import pandas as pd

from fundlens.models.base_model import BaseModel
from fundlens.models.comparison import future_dates, walk_forward

_WINDOW = 20


def _lag_features(vals: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    X = [vals[i - _WINDOW:i] for i in range(_WINDOW, len(vals))]
    y = [vals[i] for i in range(_WINDOW, len(vals))]
    return np.array(X), np.array(y)


def _recursive_predict(model, buf: list, horizon: int, prices: pd.Series) -> pd.DataFrame:
    buf = buf.copy()
    preds = []
    for _ in range(horizon):
        p = float(model.predict(np.array(buf[-_WINDOW:]).reshape(1, -1))[0])
        preds.append(p)
        buf.append(p)
    return pd.DataFrame({
        "date": future_dates(prices, horizon),
        "predicted_value": preds,
        "lower_bound": None,
        "upper_bound": None,
    })


class XGBoostModel(BaseModel):
    name = "xgboost"

    def fit(self, prices: pd.Series) -> None:
        import xgboost as xgb  # lazy: not in [dev]
        X, y = _lag_features(prices.values)
        self._model = xgb.XGBRegressor(n_estimators=100, learning_rate=0.1,
                                        max_depth=4, verbosity=0)
        self._model.fit(X, y)
        self._buf = list(prices.values[-_WINDOW:])
        self._prices = prices

    def predict(self, horizon: int) -> pd.DataFrame:
        return _recursive_predict(self._model, self._buf, horizon, self._prices)

    def score(self, prices: pd.Series, horizon: int, n_splits: int = 20) -> dict[str, float]:
        return walk_forward(self, prices, horizon, n_splits)


class LGBMModel(BaseModel):
    name = "lightgbm"

    def fit(self, prices: pd.Series) -> None:
        import lightgbm as lgb  # lazy: not in [dev]
        X, y = _lag_features(prices.values)
        self._model = lgb.LGBMRegressor(n_estimators=100, learning_rate=0.1,
                                          num_leaves=31, verbose=-1)
        self._model.fit(X, y)
        self._buf = list(prices.values[-_WINDOW:])
        self._prices = prices

    def predict(self, horizon: int) -> pd.DataFrame:
        return _recursive_predict(self._model, self._buf, horizon, self._prices)

    def score(self, prices: pd.Series, horizon: int, n_splits: int = 20) -> dict[str, float]:
        return walk_forward(self, prices, horizon, n_splits)
