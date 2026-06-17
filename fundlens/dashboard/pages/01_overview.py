"""Overview — all funds at a glance."""

import pandas as pd
import streamlit as st

from fundlens.dashboard._data import load_funds, load_prices, ytd_return, vol_30d, max_drawdown

st.set_page_config(page_title="Overview · FundLens", layout="wide")
st.title("Fund Overview")

funds = load_funds()
if not funds:
    st.warning("No funds loaded. Run `scripts/initial_load.py --all-funds --years 5` first.")
    st.stop()

rows = []
for f in funds:
    df = load_prices(f["id"])
    if df.empty:
        continue
    rows.append({
        "Ticker": f["ticker"],
        "Name": f["name"],
        "Latest NAV": float(df.iloc[-1]["nav"]),
        "As of": df.iloc[-1]["date"],
        "YTD (%)": round(ytd_return(df), 2),
        "30d Vol (%)": round(vol_30d(df), 2),
        "Max DD (%)": round(max_drawdown(df["nav"]), 2),
    })

st.dataframe(
    pd.DataFrame(rows),
    use_container_width=True,
    hide_index=True,
    column_config={
        "Latest NAV": st.column_config.NumberColumn(format="$%.2f"),
        "YTD (%)": st.column_config.NumberColumn(format="%.2f%%"),
        "30d Vol (%)": st.column_config.NumberColumn(format="%.2f%%"),
        "Max DD (%)": st.column_config.NumberColumn(format="%.2f%%"),
    },
)
