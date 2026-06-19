"""Fund detail — deep dive into a single fund."""

import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from fundlens.dashboard._data import (
    drawdown_series, filter_range, fund_label, load_funds, load_prices,
    period_picker, period_return,
)

st.title("Fund Detail")

funds = load_funds()
if not funds:
    st.warning("No funds loaded.")
    st.stop()

label_map = {fund_label(f): f for f in funds}
selected_label = st.selectbox("Fund (type to search by ticker, name, category or manager)",
                               list(label_map.keys()))
fund = label_map[selected_label]
start, end = period_picker("fd", default="5Y")

df = filter_range(load_prices(fund["id"]), start, end)
if df.empty:
    st.info("No data in the selected period.")
    st.stop()

lr = df["log_return"].dropna()
vol = float(lr.std() * np.sqrt(252) * 100) if len(lr) >= 5 else float("nan")
sharpe = float(lr.mean() / lr.std() * np.sqrt(252)) if len(lr) >= 5 else float("nan")

m1, m2, m3, m4 = st.columns(4)
m1.metric("Latest NAV", f"${float(df.iloc[-1]['nav']):.2f}")
m2.metric("Period Return", f"{period_return(df):.2f}%")
m3.metric("Vol (period)", f"{vol:.2f}%" if not np.isnan(vol) else "—")
m4.metric("Sharpe (period)", f"{sharpe:.2f}" if not np.isnan(sharpe) else "—")

# NAV chart
st.plotly_chart(
    px.line(df, x="date", y="nav", title=f"{fund['ticker']} — NAV", labels={"nav": "NAV ($)", "date": ""}),
    width="stretch",
)

# Log-return histogram + rolling 30d vol
df = df.copy()
df["vol_30"] = df["log_return"].rolling(30, min_periods=15).std() * np.sqrt(252) * 100

c1, c2 = st.columns(2)
with c1:
    st.plotly_chart(
        px.histogram(lr, nbins=60, title="Log-Return Distribution", labels={"value": "Log Return", "count": "Days"}),
        width="stretch",
    )
with c2:
    st.plotly_chart(
        px.line(df.dropna(subset=["vol_30"]), x="date", y="vol_30",
                title="Rolling 30d Volatility (annualized %)", labels={"vol_30": "Vol (%)", "date": ""}),
        width="stretch",
    )

# Drawdown
df["drawdown"] = drawdown_series(df["nav"])
fig_dd = go.Figure(go.Scatter(
    x=df["date"], y=df["drawdown"],
    fill="tozeroy", mode="lines",
    line={"color": "crimson"},
    name="Drawdown",
))
fig_dd.update_layout(title="Drawdown (%)", yaxis_title="Drawdown (%)", xaxis_title="")
st.plotly_chart(fig_dd, width="stretch")
