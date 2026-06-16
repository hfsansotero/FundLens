"""GARCH(1,1) volatility forecaster — standalone, not a price predictor."""

import numpy as np
import pandas as pd


class GarchModel:
    """Forecasts conditional volatility (daily std dev of log returns).

    Not a BaseModel — predicts volatility, not NAV levels.
    Use for risk analysis / vol forecasting, not price comparison.
    """

    name = "garch"

    def fit(self, prices: pd.Series) -> None:
        from arch import arch_model  # lazy: not in [dev]
        log_ret = np.log(prices / prices.shift(1)).dropna() * 100  # in pct
        self._result = arch_model(log_ret, vol="Garch", p=1, q=1,
                                   rescale=False).fit(disp="off")
        self._prices = prices

    def forecast_vol(self, horizon: int) -> pd.DataFrame:
        """Return annualized vol forecast for each day in horizon."""
        fc = self._result.forecast(horizon=horizon, reindex=False)
        daily_vol = np.sqrt(fc.variance.values[-1]) / 100  # back to decimal
        annual_vol = daily_vol * np.sqrt(252) * 100  # annualized %

        from fundlens.models.comparison import future_dates
        return pd.DataFrame({
            "date": future_dates(self._prices, horizon),
            "forecasted_vol_pct": annual_vol,
        })
