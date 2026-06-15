"""Model predictions comparison page."""

import streamlit as st

st.set_page_config(page_title="Predictions · FundLens", layout="wide")
st.title("Model Predictions")
st.info("Phase 2: ARIMA vs Prophet vs GARCH — forecast chart + walk-forward score table.")
