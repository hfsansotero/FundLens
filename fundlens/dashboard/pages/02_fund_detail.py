"""Fund detail — deep dive into a single fund."""

import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from fundlens.dashboard._data import (
    drawdown_series, filter_period, load_funds, load_prices, vol_30d, ytd_return,
)

st.set_page_config(page_title="Fund Detail · FundLens", layout="wide")
st.title("Fund Detail")

funds = load_funds()
if not funds:
    st.warning("No funds loaded.")
    st.stop()

ticker_map = {f["ticker"]: f for f in funds}
col_sel, col_per = st.columns([2, 3])
selected = col_sel.selectbox("Fund", list(ticker_map.keys()))
period = col_per.radio("Period", ["1Y", "3Y", "5Y", "All"], horizontal=True, index=2)

df = filter_period(load_prices(ticker_map[selected]["id"]), period)
if df.empty:
    st.warning("No price data for this fund.")
    st.stop()

lr = df["log_return"].dropna()
trailing_sharpe = float(lr.tail(90).mean() / lr.tail(90).std() * np.sqrt(252)) if len(lr) >= 30 else float("nan")

m1, m2, m3, m4 = st.columns(4)
m1.metric("Latest NAV", f"${float(df.iloc[-1]['nav']):.2f}")
m2.metric("YTD Return", f"{ytd_return(df):.2f}%")
m3.metric("30d Vol", f"{vol_30d(df):.2f}%")
m4.metric("Sharpe (90d)", f"{trailing_sharpe:.2f}" if not np.isnan(trailing_sharpe) else "—")

# NAV chart
st.plotly_chart(
    px.line(df, x="date", y="nav", title=f"{selected} — NAV", labels={"nav": "NAV ($)", "date": ""}),
    use_container_width=True,
)

# Log-return histogram + rolling 30d vol
df = df.copy()
df["vol_30"] = df["log_return"].rolling(30, min_periods=15).std() * np.sqrt(252) * 100

c1, c2 = st.columns(2)
with c1:
    st.plotly_chart(
        px.histogram(lr, nbins=60, title="Log-Return Distribution", labels={"value": "Log Return", "count": "Days"}),
        use_container_width=True,
    )
with c2:
    st.plotly_chart(
        px.line(df.dropna(subset=["vol_30"]), x="date", y="vol_30",
                title="Rolling 30d Volatility (annualized %)", labels={"vol_30": "Vol (%)", "date": ""}),
        use_container_width=True,
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
st.plotly_chart(fig_dd, use_container_width=True)
