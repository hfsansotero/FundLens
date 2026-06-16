"""Walk-forward model comparison engine."""

import numpy as np
import pandas as pd

from fundlens.models.base_model import BaseModel


def future_dates(prices: pd.Series, horizon: int) -> list:
    last = prices.index[-1]
    try:
        start = last if isinstance(prices.index, pd.DatetimeIndex) else pd.Timestamp(last)
    except Exception:
        return [None] * horizon
    return pd.bdate_range(start=start, periods=horizon + 1)[1:].date.tolist()


def walk_forward(model: BaseModel, prices: pd.Series, horizon: int, n_splits: int = 20) -> dict[str, float]:
    min_train = max(252, len(prices) // 3)
    available = len(prices) - min_train - horizon
    if available <= 0:
        raise ValueError(f"Not enough data ({len(prices)} rows, need >{min_train + horizon})")

    step = max(1, available // n_splits)
    maes, rmses, mapes = [], [], []

    for i in range(n_splits):
        split = min_train + i * step
        if split + horizon > len(prices):
            break
        train = prices.iloc[:split]
        actual = prices.iloc[split:split + horizon].values

        model.fit(train)
        pred = model.predict(horizon)["predicted_value"].values[:len(actual)]

        maes.append(np.mean(np.abs(pred - actual)))
        rmses.append(np.sqrt(np.mean((pred - actual) ** 2)))
        mapes.append(np.mean(np.abs((pred - actual) / actual)) * 100)

    return {
        "mae": float(np.mean(maes)),
        "rmse": float(np.mean(rmses)),
        "mape": float(np.mean(mapes)),
    }


def compare_models(
    models: list[BaseModel],
    prices: pd.Series,
    horizons: list[int] = [5, 10, 20],
) -> pd.DataFrame:
    rows = []
    for model in models:
        for h in horizons:
            try:
                scores = walk_forward(model, prices, h)
                rows.append({"model": model.name, "horizon_days": h, **scores})
            except Exception as exc:
                rows.append({"model": model.name, "horizon_days": h,
                             "mae": None, "rmse": None, "mape": None, "error": str(exc)})
    return pd.DataFrame(rows)
