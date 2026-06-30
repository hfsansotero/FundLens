"""About — glossary of concepts and disclaimer."""

from datetime import datetime
from zoneinfo import ZoneInfo  # stdlib — handles DST automatically

import streamlit as st

st.title("About FundLens")


def _local_time(hour: int, minute: int, tz: str) -> str:
    today = datetime.now(ZoneInfo("UTC")).date()
    utc = datetime(today.year, today.month, today.day, hour, minute, tzinfo=ZoneInfo("UTC"))
    return utc.astimezone(ZoneInfo(tz)).strftime("%H:%M")


_RUNS = [("First attempt", 23, 30), ("Retry (if data was missing)", 1, 30)]
_TZS = [("UTC", "UTC"), ("US Eastern", "America/New_York"), ("Central Europe", "Europe/Madrid")]

st.warning(
    "**Not investment advice.** FundLens is an analytics and research tool. "
    "Nothing shown here — metrics, charts, or model forecasts — is a "
    "recommendation to buy, hold, or sell any fund. Predictive models are "
    "fitted on historical data only; past performance and statistical "
    "patterns are not a guarantee of future results. Always do your own "
    "research or consult a licensed financial advisor before investing."
)

st.markdown("""
FundLens tracks a set of mutual funds / ETFs over time and surfaces a few
standard ways analysts look at performance and risk. Quick definitions of
what each tab is showing:

#### Overview
A snapshot of every tracked fund: latest NAV (Net Asset Value, the fund's
price per share), year-to-date return, recent volatility, and max drawdown.

#### Fund Detail
A deep dive on a single fund: NAV history, the distribution of its daily
log returns, a rolling 30-day volatility chart, and its drawdown profile.

#### Correlations
How funds move together. A value near **+1** (green) means two funds tend
to rise and fall together; near **-1** (red) means they move oppositely;
near **0** (white) means little relationship. Useful for diversification —
pairing low/negatively correlated funds reduces portfolio swings.

#### Predictions
Statistical and machine-learning models fitted on each fund's price
history, used to project a possible path forward with an uncertainty band.
Models are compared by walk-forward backtesting (MAE / RMSE / MAPE — lower
is better) rather than by how plausible the chart looks.

#### Drawdown
How far each fund has fallen from its prior peak at any point in time —
a common way to gauge the worst-case pain an investor would have felt
holding it.
""")

st.markdown("#### Data Freshness")
st.caption(
    "NAV data is fetched on weekdays only (no run on weekends or when a "
    "market is closed for a holiday). Times below are for *today*, "
    "converted automatically for daylight saving."
)
header = "| Run | " + " | ".join(name for name, _ in _TZS) + " |"
sep = "|---" * (len(_TZS) + 1) + "|"
rows = [
    "| " + label + " | " + " | ".join(_local_time(h, m, tz) for _, tz in _TZS) + " |"
    for label, h, m in _RUNS
]
st.markdown("\n".join([header, sep, *rows]))
st.caption(
    "European (EUR-denominated) funds often publish their NAV later than "
    "US funds, so they can lag a day behind right after the run."
)

st.markdown("""
---

#### Glossary

- **NAV (Net Asset Value):** the price of one share/unit of the fund.
- **Log return:** `ln(price_t / price_t-1)` — the standard way to measure
  day-to-day percentage change in finance, because log returns are
  additive over time.
- **Volatility:** the standard deviation of returns, annualized
  (`σ_daily × √252`) — a measure of how much a fund's value swings.
- **Sharpe ratio:** return earned per unit of volatility (risk) taken.
  Higher is generally better.
- **Drawdown:** the percentage decline from a fund's running peak value.
  **Max drawdown** is the worst such decline in the period shown.
- **Correlation:** how similarly two funds' returns move, from -1 to +1.
- **Walk-forward validation:** a backtesting method that only ever trains
  a model on data *before* the period it's being tested on, to avoid
  look-ahead bias.
""")
