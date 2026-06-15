"""Feature engineering for predictive models."""

import pandas as pd
from fundlens.processing.returns import log_returns
from fundlens.processing.volatility import rolling_volatility


def build_features(prices: pd.Series) -> pd.DataFrame:
    """Return a DataFrame of model-ready features indexed by date."""
    lr = log_returns(prices)
    df = pd.DataFrame({"nav": prices, "log_return": lr})
    df["vol_30"] = rolling_volatility(lr, 30)
    df["vol_90"] = rolling_volatility(lr, 90)
    df["momentum_20"] = lr.rolling(20).sum()
    df["momentum_60"] = lr.rolling(60).sum()
    return df.dropna()
