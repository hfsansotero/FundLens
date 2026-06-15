"""Tests for predictive model stubs — Phase 2 implementations."""

import pytest
from fundlens.models.arima_model import ArimaModel
from fundlens.models.prophet_model import ProphetModel
from fundlens.models.garch_model import GarchModel


@pytest.mark.skip(reason="Phase 2: not yet implemented")
def test_arima_fit_predict(sample_prices):
    model = ArimaModel()
    model.fit(sample_prices)
    pred = model.predict(horizon=5)
    assert len(pred) == 5


@pytest.mark.skip(reason="Phase 2: not yet implemented")
def test_prophet_fit_predict(sample_prices):
    model = ProphetModel()
    model.fit(sample_prices)
    pred = model.predict(horizon=10)
    assert "predicted_value" in pred.columns
