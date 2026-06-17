"""Prophet price forecaster (Meta/Facebook)."""

import logging
import pandas as pd

from fundlens.models.base_model import BaseModel
from fundlens.models.comparison import walk_forward


class ProphetModel(BaseModel):
    name = "prophet"

    def fit(self, prices: pd.Series) -> None:
        from prophet import Prophet  # lazy: not in [dev]
        logging.getLogger("prophet").setLevel(logging.WARNING)
        logging.getLogger("cmdstanpy").setLevel(logging.WARNING)
        if isinstance(prices.index, pd.DatetimeIndex):
            ds = prices.index
        else:
            ds = pd.bdate_range(end=pd.Timestamp.today(), periods=len(prices))
        df = pd.DataFrame({"ds": ds, "y": prices.values})
        self._model = Prophet(daily_seasonality=False, yearly_seasonality=True,
                               weekly_seasonality=True, changepoint_prior_scale=0.05)
        self._model.fit(df)
        self._last_ds = df["ds"].iloc[-1]
        self._prices = prices

    def predict(self, horizon: int) -> pd.DataFrame:
        future = self._model.make_future_dataframe(periods=horizon, freq="B")
        fc = self._model.predict(future).tail(horizon)
        return pd.DataFrame({
            "date": fc["ds"].dt.date.values,
            "predicted_value": fc["yhat"].values,
            "lower_bound": fc["yhat_lower"].values,
            "upper_bound": fc["yhat_upper"].values,
        })

    def score(self, prices: pd.Series, horizon: int, n_splits: int = 10) -> dict[str, float]:
        # ponytail: fewer splits — Prophet fit takes ~5s, 20 splits × 3 horizons = 5 min
        return walk_forward(self, prices, horizon, n_splits)
