"""LSTM price forecaster — PyTorch."""

import numpy as np
import pandas as pd

from fundlens.models.base_model import BaseModel
from fundlens.models.comparison import future_dates, walk_forward

_WINDOW = 60


class LSTMModel(BaseModel):
    name = "lstm"

    def __init__(self, hidden: int = 64, epochs: int = 80, lr: float = 1e-3):
        self._hidden = hidden
        self._epochs = epochs
        self._lr = lr

    def fit(self, prices: pd.Series) -> None:
        import torch
        import torch.nn as nn  # lazy: not in [dev]

        class _Net(nn.Module):
            def __init__(self, hidden: int, n_layers: int = 2):
                super().__init__()
                self.lstm = nn.LSTM(1, hidden, n_layers, batch_first=True, dropout=0.2)
                self.fc = nn.Linear(hidden, 1)

            def forward(self, x):
                out, _ = self.lstm(x)
                return self.fc(out[:, -1, :])

        vals = prices.values.astype(float)
        self._mu, self._sigma = vals.mean(), vals.std() + 1e-8
        norm = (vals - self._mu) / self._sigma

        X = torch.tensor(
            np.array([norm[i - _WINDOW:i] for i in range(_WINDOW, len(norm))]),
            dtype=torch.float32,
        ).unsqueeze(-1)
        y = torch.tensor(norm[_WINDOW:], dtype=torch.float32).unsqueeze(-1)

        torch.manual_seed(42)
        self._net = _Net(self._hidden)
        opt = torch.optim.Adam(self._net.parameters(), lr=self._lr)
        loss_fn = nn.MSELoss()

        self._net.train()
        for _ in range(self._epochs):
            opt.zero_grad()
            loss_fn(self._net(X), y).backward()
            opt.step()

        self._buf = list(norm[-_WINDOW:])
        self._prices = prices

    def predict(self, horizon: int) -> pd.DataFrame:
        import torch

        self._net.eval()
        buf = self._buf.copy()
        preds_norm = []
        with torch.no_grad():
            for _ in range(horizon):
                x = torch.tensor(buf[-_WINDOW:], dtype=torch.float32).view(1, _WINDOW, 1)
                p = float(self._net(x).item())
                preds_norm.append(p)
                buf.append(p)
        preds = np.array(preds_norm) * self._sigma + self._mu
        return pd.DataFrame({
            "date": future_dates(self._prices, horizon),
            "predicted_value": preds,
            "lower_bound": None,
            "upper_bound": None,
        })

    def score(self, prices: pd.Series, horizon: int, n_splits: int = 5) -> dict[str, float]:
        # ponytail: n_splits=5 — retraining a neural net 20× takes ~15 min
        return walk_forward(self, prices, horizon, n_splits)
