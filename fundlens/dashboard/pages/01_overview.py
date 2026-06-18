"""Overview — all funds at a glance."""

import pandas as pd
import streamlit as st

from fundlens.dashboard._data import (
    arrow, day_change, filter_range, fund_label, load_funds, load_prices,
    max_drawdown, period_picker, period_return, vol_30d,
)

st.title("Fund Overview")

funds = load_funds()
if not funds:
    st.warning("No funds loaded. Run `scripts/initial_load.py --all-funds --years 5` first.")
    st.stop()

st.caption("1D Δ always reflects the latest close. Period Return and Max DD are "
           "measured over the period selected below.")
start, end = period_picker("ov", default="1Y")

rows = []
for f in funds:
    full = load_prices(f["id"])
    if full.empty:
        continue
    df = filter_range(full, start, end)
    if df.empty:
        continue
    rows.append({
        "Fund": fund_label(f),
        "Latest NAV": float(full.iloc[-1]["nav"]),
        "As of": full.iloc[-1]["date"],
        "1D Δ": arrow(day_change(full)),
        "Period Return": arrow(period_return(df)),
        "30d Vol (%)": round(vol_30d(full), 2),
        "Max DD (%)": round(max_drawdown(df["nav"]), 2),
    })

if not rows:
    st.info("No data in the selected period.")
    st.stop()

st.dataframe(
    pd.DataFrame(rows),
    width="stretch",
    hide_index=True,
    column_config={
        "Latest NAV": st.column_config.NumberColumn(format="$%.2f"),
        "30d Vol (%)": st.column_config.NumberColumn(format="%.2f%%"),
        "Max DD (%)": st.column_config.NumberColumn(format="%.2f%%"),
    },
)
