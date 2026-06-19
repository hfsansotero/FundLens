"""Drawdown analysis — underwater chart + max drawdown table."""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from fundlens.dashboard._data import (
    arrow, colorize, filter_range, fund_label, load_funds, load_prices, period_picker,
)

st.title("Drawdown Analysis")

funds = load_funds()
if not funds:
    st.warning("No funds loaded.")
    st.stop()

start, end = period_picker("dd", default="5Y")

fig = go.Figure()
rows = []

for f in funds:
    df = filter_range(load_prices(f["id"]), start, end)
    if df.empty:
        continue
    dd = (df["nav"] / df["nav"].cummax() - 1) * 100
    max_idx = dd.idxmin()
    current_dd = float(dd.iloc[-1])
    rows.append({
        "Fund": fund_label(f),
        "Max DD (%)": round(float(dd.min()), 2),
        "Date of Max DD": str(df.loc[max_idx, "date"]),
        "Current DD": "📈 At peak" if current_dd >= -0.01 else arrow(current_dd),
    })
    fig.add_trace(go.Scatter(
        x=df["date"], y=dd,
        name=f["ticker"], mode="lines", fill="tozeroy", opacity=0.6,
    ))

if not rows:
    st.info("No data in the selected period.")
    st.stop()

fig.update_layout(
    title="Underwater Chart",
    yaxis_title="Drawdown (%)",
    xaxis_title="",
    hovermode="x unified",
)
fig.add_hline(y=0, line_color="black", line_width=1)
st.plotly_chart(fig, width="stretch")

st.subheader("Max Drawdown by Fund")
styled = colorize(
    pd.DataFrame(rows).sort_values("Max DD (%)"), ["Current DD"],
    fmt={"Max DD (%)": "{:.2f}%"},
)
st.dataframe(styled, width="stretch", hide_index=True)
