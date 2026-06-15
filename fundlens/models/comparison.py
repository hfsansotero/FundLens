"""Walk-forward model comparison engine — Phase 2."""
import pandas as pd
from fundlens.models.base_model import BaseModel


def compare_models(models: list[BaseModel], prices: pd.Series, horizons: list[int] = [5, 10, 20]) -> pd.DataFrame:
    """Run walk-forward evaluation for each model × horizon. Returns tidy DataFrame.

    Columns: model, horizon_days, mae, rmse, mape
    """
    # TODO: implement in Phase 2
    raise NotImplementedError
