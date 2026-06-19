"""Dynamic correlations — heatmap + rolling pairwise."""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from fundlens.dashboard._data import filter_range, fund_label, load_funds, load_prices, period_picker

st.title("Dynamic Correlations")

funds = load_funds()
if not funds:
    st.warning("No funds loaded.")
    st.stop()

start, end = period_picker("corr", default="5Y")

returns = pd.DataFrame({
    f["ticker"]: filter_range(load_prices(f["id"]), start, end).set_index("date")["log_return"]
    for f in funds
    if not load_prices(f["id"]).empty
}).dropna()

if returns.empty:
    st.info("No data in the selected period.")
    st.stop()

corr = returns.corr()
st.plotly_chart(
    px.imshow(corr, text_auto=".2f",
              color_continuous_scale=["red", "white", "green"],
              zmin=-1, zmax=1, title="Return Correlation Matrix"),
    width="stretch",
)

# Rolling 60d correlation for a selected pair
st.subheader("Rolling 60d Correlation")
label_map = {fund_label(f): f["ticker"] for f in funds if f["ticker"] in returns.columns}
labels = list(label_map.keys())
c1, c2 = st.columns(2)
l1 = c1.selectbox("Fund A (type to search)", labels, index=0)
l2 = c2.selectbox("Fund B (type to search)", labels, index=min(1, len(labels) - 1))
t1, t2 = label_map[l1], label_map[l2]

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
    st.plotly_chart(fig, width="stretch")
else:
    st.info("Select two different funds.")
