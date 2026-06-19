"""Streamlit entry point. Run with: streamlit run fundlens/dashboard/app.py"""

import streamlit as st

st.set_page_config(
    page_title="FundLens",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

pg = st.navigation([
    st.Page("pages/00_about.py", title="About", icon="ℹ️", default=True),
    st.Page("pages/01_overview.py", title="Overview", icon="📋"),
    st.Page("pages/02_fund_detail.py", title="Fund Detail", icon="📈"),
    st.Page("pages/03_correlations.py", title="Correlations", icon="🔗"),
    st.Page("pages/04_predictions.py", title="Predictions", icon="🔮"),
    st.Page("pages/05_drawdown.py", title="Drawdown", icon="📉"),
])
pg.run()
