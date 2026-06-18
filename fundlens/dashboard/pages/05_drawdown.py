"""Drawdown analysis — underwater chart + max drawdown table."""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from fundlens.dashboard._data import filter_period, load_funds, load_prices

st.title("Drawdown Analysis")

funds = load_funds()
if not funds:
    st.warning("No funds loaded.")
    st.stop()

period = st.radio("Period", ["1Y", "3Y", "5Y", "All"], horizontal=True, index=2)

fig = go.Figure()
rows = []

for f in funds:
    df = filter_period(load_prices(f["id"]), period)
    if df.empty:
        continue
    dd = (df["nav"] / df["nav"].cummax() - 1) * 100
    max_idx = dd.idxmin()
    rows.append({
        "Ticker": f["ticker"],
        "Max DD (%)": round(float(dd.min()), 2),
        "Date of Max DD": str(df.loc[max_idx, "date"]),
    })
    fig.add_trace(go.Scatter(
        x=df["date"], y=dd,
        name=f["ticker"], mode="lines", fill="tozeroy", opacity=0.6,
    ))

fig.update_layout(
    title="Underwater Chart",
    yaxis_title="Drawdown (%)",
    xaxis_title="",
    hovermode="x unified",
)
fig.add_hline(y=0, line_color="black", line_width=1)
st.plotly_chart(fig, width="stretch")

st.subheader("Max Drawdown by Fund")
st.dataframe(
    pd.DataFrame(rows).sort_values("Max DD (%)"),
    width="stretch",
    hide_index=True,
    column_config={"Max DD (%)": st.column_config.NumberColumn(format="%.2f%%")},
)
