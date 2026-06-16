"""Dynamic correlations — heatmap + rolling pairwise."""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from fundlens.dashboard._data import filter_period, load_funds, load_prices

st.set_page_config(page_title="Correlations · FundLens", layout="wide")
st.title("Dynamic Correlations")

funds = load_funds()
if not funds:
    st.warning("No funds loaded.")
    st.stop()

period = st.radio("Period", ["1Y", "3Y", "5Y", "All"], horizontal=True, index=2)

returns = pd.DataFrame({
    f["ticker"]: filter_period(load_prices(f["id"]), period).set_index("date")["log_return"]
    for f in funds
    if not load_prices(f["id"]).empty
}).dropna()

if returns.empty:
    st.warning("Not enough data to compute correlations.")
    st.stop()

corr = returns.corr()
st.plotly_chart(
    px.imshow(corr, text_auto=".2f", color_continuous_scale="RdBu_r",
              zmin=-1, zmax=1, title="Return Correlation Matrix"),
    use_container_width=True,
)

# Rolling 60d correlation for a selected pair
st.subheader("Rolling 60d Correlation")
tickers = list(returns.columns)
c1, c2 = st.columns(2)
t1 = c1.selectbox("Fund A", tickers, index=0)
t2 = c2.selectbox("Fund B", tickers, index=min(1, len(tickers) - 1))

if t1 != t2:
    roll_corr = returns[t1].rolling(60, min_periods=30).corr(returns[t2]).dropna().reset_index()
    roll_corr.columns = ["date", "correlation"]
    fig = go.Figure(go.Scatter(x=roll_corr["date"], y=roll_corr["correlation"], mode="lines"))
    fig.update_layout(
        title=f"Rolling 60d Correlation: {t1} vs {t2}",
        yaxis={"range": [-1, 1], "title": "Correlation"},
        xaxis_title="",
    )
    fig.add_hline(y=0, line_dash="dash", line_color="gray")
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Select two different funds.")
