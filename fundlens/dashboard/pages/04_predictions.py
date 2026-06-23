"""Model predictions — forecast chart + walk-forward score comparison."""

import importlib.util

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from fundlens.dashboard._data import filter_range, fund_label, load_funds, load_prices, period_picker

st.title("Model Predictions")

funds = load_funds()
if not funds:
    st.warning("No funds loaded.")
    st.stop()

ticker_map = {f["ticker"]: f for f in funds}
col_f, col_h = st.columns([2, 2])
selected = col_f.selectbox("Fund", list(ticker_map.keys()), format_func=lambda t: fund_label(ticker_map[t]))
horizon = col_h.selectbox("Forecast horizon (days)", [5, 10, 20, 30], index=3)
start, end = period_picker("pred", default="3Y")

df = filter_range(load_prices(ticker_map[selected]["id"]), start, end)
if df.empty:
    st.info("No data in the selected period.")
    st.stop()

nav = df.set_index(pd.to_datetime(df["date"]))["nav"]

# ── Model selector + forecast ──────────────────────────────────────────────────
# Module behind each model — used to detect what this deployment actually has installed
# (Render's free tier skips torch/xgboost/lightgbm, ~1GB+, too heavy for 512MB RAM).
MODEL_DEPS = {
    "arima": "statsmodels", "ets": "statsmodels", "linear": "sklearn",
    "xgboost": "xgboost", "lightgbm": "lightgbm", "prophet": "prophet", "lstm": "torch",
}
MODEL_OPTIONS = list(MODEL_DEPS)
AVAILABLE = {m: importlib.util.find_spec(dep) is not None for m, dep in MODEL_DEPS.items()}


def _model_label(name: str) -> str:
    return name if AVAILABLE[name] else f"❌ {name} (unavailable in this deployment)"


model_name = st.selectbox("Model", MODEL_OPTIONS, format_func=_model_label)
model_unavailable = not AVAILABLE[model_name]
if model_unavailable:
    st.caption(f"❌ **{model_name}** needs `{MODEL_DEPS[model_name]}`, not installed in this "
               "deployment — available when running locally with the full `ml` extra.")


def _build_model(name: str):
    # Import lazily — ML deps may not be installed
    from fundlens.models.arima_model import ArimaModel
    from fundlens.models.ets_model import ETSModel
    from fundlens.models.linear_model import LinearModel
    from fundlens.models.tree_models import XGBoostModel, LGBMModel
    from fundlens.models.prophet_model import ProphetModel
    from fundlens.models.lstm_model import LSTMModel
    return {
        "arima": ArimaModel, "ets": ETSModel, "linear": LinearModel,
        "xgboost": XGBoostModel, "lightgbm": LGBMModel,
        "prophet": ProphetModel, "lstm": LSTMModel,
    }[name]()


@st.cache_data(show_spinner="Running forecast…", ttl=600)
def run_forecast(ticker: str, start, end, horizon: int, model_name: str) -> pd.DataFrame:
    df_ = filter_range(load_prices(ticker_map[ticker]["id"]), start, end)
    nav_ = df_.set_index(pd.to_datetime(df_["date"]))["nav"]
    model = _build_model(model_name)
    model.fit(nav_)
    return model.predict(horizon)


if st.button(f"Run {model_name.upper()} forecast", disabled=model_unavailable):
    fc = run_forecast(selected, start, end, horizon, model_name)

    fig = go.Figure()
    hist = df.tail(120)
    fig.add_trace(go.Scatter(x=pd.to_datetime(hist["date"]), y=hist["nav"],
                             name="Historical", line={"color": "steelblue"}))
    fig.add_trace(go.Scatter(x=pd.to_datetime(fc["date"]), y=fc["predicted_value"],
                             name="Forecast", line={"color": "orange", "dash": "dash"}))
    if fc["upper_bound"].notna().any():
        fig.add_trace(go.Scatter(
            x=pd.to_datetime(fc["date"]).tolist() + pd.to_datetime(fc["date"]).tolist()[::-1],
            y=fc["upper_bound"].tolist() + fc["lower_bound"].tolist()[::-1],
            fill="toself", fillcolor="rgba(255,165,0,0.15)", line={"color": "rgba(0,0,0,0)"},
            name="95% CI",
        ))
    fig.update_layout(title=f"{selected} — {model_name.upper()} {horizon}d Forecast",
                      xaxis_title="", yaxis_title="NAV ($)")
    st.plotly_chart(fig, width="stretch")

    st.dataframe(
        fc.rename(columns={"predicted_value": "Forecast", "lower_bound": "Lower",
                            "upper_bound": "Upper"}),
        width="stretch", hide_index=True,
    )

# ── GARCH volatility forecast ──────────────────────────────────────────────────
st.divider()
st.subheader("Volatility Forecast (GARCH)")

@st.cache_data(show_spinner="Running GARCH…", ttl=600)
def run_garch(ticker: str, start, end, horizon: int) -> pd.DataFrame:
    from fundlens.models.garch_model import GarchModel
    df_ = filter_range(load_prices(ticker_map[ticker]["id"]), start, end)
    nav_ = df_.set_index(pd.to_datetime(df_["date"]))["nav"]
    m = GarchModel()
    m.fit(nav_)
    return m.forecast_vol(horizon)


garch_unavailable = importlib.util.find_spec("arch") is None
if garch_unavailable:
    st.caption("❌ GARCH needs `arch`, not installed in this deployment.")
if st.button("Run GARCH volatility forecast", disabled=garch_unavailable):
    vol_fc = run_garch(selected, start, end, horizon)
    st.plotly_chart(
        px.bar(vol_fc, x="date", y="forecasted_vol_pct",
               title=f"{selected} — GARCH {horizon}d Annualized Vol Forecast (%)",
               labels={"forecasted_vol_pct": "Vol (%)", "date": ""}),
        width="stretch",
    )

# ── Walk-forward comparison ────────────────────────────────────────────────────
st.divider()
st.subheader("Walk-Forward Score Comparison")
st.caption(
    "Each model is **walk-forward validated**: trained on data up to a point in time, "
    "asked to forecast the next *N* days, then the window slides forward and it repeats. "
    "The metrics below compare those forecasts against what actually happened:"
)
st.markdown(
    "- **MAE** — average forecast error, in NAV units (e.g. dollars).\n"
    "- **RMSE** — like MAE, but penalizes large misses more heavily.\n"
    "- **MAPE** — average error as a % of NAV, easier to compare across funds.\n\n"
    "Lower is better on all three. The model marked **best** below is simply the one with "
    "the lowest MAE for *this* fund and horizon — not a claim that it's the most "
    "sophisticated, just the one whose backtested forecasts came closest historically."
)
st.caption("Fast models (~1 min), Prophet/LSTM are slow (5–15 min). Results cached for 10 min.")

fast_models = st.multiselect(
    "Models to compare",
    MODEL_OPTIONS,
    default=[m for m in ["arima", "ets", "linear", "xgboost", "lightgbm"] if AVAILABLE[m]],
    format_func=_model_label,
)
cmp_horizon = st.selectbox("Horizon", [5, 10, 20], key="cmp_h")


@st.cache_data(show_spinner="Running walk-forward comparison…", ttl=600)
def run_comparison(ticker: str, start, end, horizon: int, models: list[str]) -> pd.DataFrame:
    from fundlens.models.comparison import walk_forward as wf
    df_ = filter_range(load_prices(ticker_map[ticker]["id"]), start, end)
    nav_ = df_.set_index(pd.to_datetime(df_["date"]))["nav"]
    rows = []
    for name in models:
        try:
            scores = wf(_build_model(name), nav_, horizon)
            rows.append({"Model": name, **scores})
        except Exception as e:
            rows.append({"Model": name, "mae": None, "rmse": None, "mape": None, "error": str(e)})
    return pd.DataFrame(rows)


if st.button("Run comparison"):
    results = run_comparison(selected, start, end, cmp_horizon, fast_models)
    st.dataframe(
        results.sort_values("mae"),
        width="stretch",
        hide_index=True,
        column_config={
            "mae": st.column_config.NumberColumn("MAE", format="%.4f"),
            "rmse": st.column_config.NumberColumn("RMSE", format="%.4f"),
            "mape": st.column_config.NumberColumn("MAPE (%)", format="%.2f%%"),
        },
    )
    if "mae" in results.columns and results["mae"].notna().any():
        best = results.loc[results["mae"].idxmin(), "Model"]
        st.success(f"Best MAE: **{best}** — closest backtested forecasts for {selected} at this horizon.")
