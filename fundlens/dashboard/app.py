"""Streamlit entry point. Run with: streamlit run fundlens/dashboard/app.py"""

import streamlit as st

st.set_page_config(
    page_title="FundLens",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("FundLens")
st.markdown("NAV pipeline · Predictive model comparison · Dynamic correlations")
st.info("Use the sidebar to navigate between views.")
