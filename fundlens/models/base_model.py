from abc import ABC, abstractmethod
import pandas as pd


class BaseModel(ABC):
    """Contract for all predictive models in FundLens.

    fit() trains on a price series.
    predict() returns a DataFrame with columns: date, predicted_value, lower_bound, upper_bound.
    score() returns dict with MAE, RMSE, MAPE for the given horizon using walk-forward validation.
    """

    @abstractmethod
    def fit(self, prices: pd.Series) -> None: ...

    @abstractmethod
    def predict(self, horizon: int) -> pd.DataFrame: ...

    @abstractmethod
    def score(self, prices: pd.Series, horizon: int, n_splits: int = 20) -> dict[str, float]: ...

    @property
    @abstractmethod
    def name(self) -> str: ...
