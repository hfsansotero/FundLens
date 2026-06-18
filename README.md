# FundLens

Automated pipeline for ingesting, storing, analyzing, and visualizing daily NAVs (Net Asset Values) of mutual funds — with predictive model comparison (ARIMA, Prophet, ETS, Linear, XGBoost, LightGBM, LSTM) and dynamic correlation analysis.

> **Status:** Phase 1 complete (dashboard live). Phase 2 in progress (models implemented, scheduler pending).

---

## Features

- **Daily NAV ingestion** via yfinance (primary) + Tiingo (backup), scheduled automatically
- **Time-series analysis** — log-returns, rolling volatility, Sharpe ratio, drawdown
- **Dynamic correlations** — static and rolling pairwise correlation between funds
- **Predictive models** — ARIMA, Prophet, ETS, Linear, XGBoost, LightGBM, LSTM; walk-forward comparison by MAE/RMSE/MAPE
- **Volatility forecasting** — GARCH(1,1) conditional vol
- **Streamlit dashboard** — multi-page interactive visualization
- **DB-agnostic storage** — DuckDB for local dev, one-line swap to PostgreSQL for production

---

## Tech Stack

| Layer | Tool | Notes |
|---|---|---|
| Data ingestion | yfinance + Tiingo | No cost; Tiingo requires free API key |
| Scheduling | APScheduler → Prefect (Phase 2) | Embedded scheduler, no external server |
| Database | DuckDB (local) → Neon PostgreSQL (cloud) | SQLAlchemy abstraction = one-line swap |
| ORM | SQLAlchemy 2.x | Typed mapped columns |
| Processing | pandas + numpy | — |
| Models | statsmodels, prophet, scikit-learn, xgboost, lightgbm, arch, torch | Phase 2 |
| Dashboard | Streamlit + Plotly | Hosted on Render.com |
| Config | pydantic-settings + python-dotenv | Validated, typed settings |
| Logging | loguru | — |
| Tests | pytest + pytest-cov | — |
| Environment | conda (Python 3.11) | `environment.yml` provided |

---

## Project Structure

```
FundLens/
├── .env.example              # Copy to .env and fill in values
├── environment.yml           # Conda environment definition
├── pyproject.toml            # Package metadata and dependencies
│
├── config/
│   ├── settings.py           # Pydantic Settings — loads .env, validates types
│   └── funds.yaml            # Funds list (edit without touching code)
│
├── fundlens/                 # Main package
│   ├── ingestion/            # DataSource abstraction + yfinance/Tiingo implementations
│   ├── storage/              # SQLAlchemy ORM models, engine, repository (all DB access)
│   ├── processing/           # Log-returns, volatility, feature engineering
│   ├── analysis/             # Correlations, drawdown, regime detection (Phase 2)
│   ├── models/               # 7 price models + GARCH vol + walk-forward comparison engine
│   ├── pipeline/             # Daily update job + APScheduler config
│   └── dashboard/            # Streamlit app + 5 pages
│
├── scripts/
│   ├── initial_load.py       # One-time historical load (5+ years)
│   └── backfill.py           # Fill gaps if ingestion fails
│
├── tests/                    # pytest — conftest fixtures, one file per layer
├── notebooks/                # EDA and model exploration (outputs stripped before commit)
└── data/                     # .gitignored — DuckDB file lives here
```

---

## Quick Start

### 1. Create conda environment

```bash
conda env create -f environment.yml
conda activate fundlens
# Phase 2 ML — install PyTorch CPU-only (avoids conda Intel VTune conflict):
pip install torch --index-url https://download.pytorch.org/whl/cpu
```

### 2. Install the package

```bash
pip install -e .
```

### 3. Configure environment

```bash
cp .env.example .env
# Edit .env — add TIINGO_API_KEY if you have one (optional for Phase 0)
```

### 4. Load historical data

```bash
python scripts/initial_load.py --all-funds --years 5
# or specific tickers:
python scripts/initial_load.py --tickers VFINX FCNTX VBMFX --years 5
```

### 5. Verify data

```bash
python - <<'EOF'
from fundlens.storage.database import get_session
from fundlens.storage import repository as repo

with get_session() as s:
    for f in repo.get_all_active_funds(s):
        df = repo.get_prices_df(s, f.id)
        print(f"{f.ticker}: {len(df)} rows | {df['date'].min()} → {df['date'].max()}")
EOF
```

### 6. Launch dashboard

```bash
streamlit run fundlens/dashboard/app.py
# Opens at http://localhost:8501
```

### 7. Start daily scheduler (optional)

```bash
python fundlens/pipeline/scheduler.py
# Runs NAV ingestion every weekday at 18:00 ET
```

---

## Configuration

All settings live in `.env` (never committed). See `.env.example` for all available variables.

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | `duckdb:///./data/fundlens.duckdb` | Swap to PostgreSQL URL for cloud deploy |
| `TIINGO_API_KEY` | _(empty)_ | Free at [tiingo.com](https://tiingo.com) — backup data source |
| `DAILY_UPDATE_HOUR` | `18` | Hour (ET, 24h) for daily NAV job |
| `DAILY_UPDATE_MINUTE` | `0` | Minute for daily NAV job |
| `LOG_LEVEL` | `INFO` | DEBUG / INFO / WARNING / ERROR |

### Adding or removing funds

Edit `config/funds.yaml` — no code changes needed. The initial load and daily pipeline read from this file.

---

## Funds (Phase 1)

| Ticker | Name | Category | Manager |
|---|---|---|---|
| VFINX | Vanguard 500 Index | Large Blend | Vanguard |
| FCNTX | Fidelity Contrafund | Large Growth | Fidelity |
| VBMFX | Vanguard Total Bond Market | Bonds | Vanguard |
| VGTSX | Vanguard Total Intl Stock | International | Vanguard |
| PRHSX | T. Rowe Price Health Sciences | Sector Health | T. Rowe Price |
| FAGIX | Fidelity Capital & Income | High Yield Bonds | Fidelity |

---

## Running Tests

```bash
pytest
# With coverage report:
pytest --cov=fundlens --cov-report=html
```

---

## Cloud Deployment (Phase 1 end)

1. **Database:** Create a free project at [neon.tech](https://neon.tech), copy the connection string.
2. **Migrate data:** Set `DATABASE_URL` to the Neon URL, re-run `initial_load.py`.
3. **Dashboard:** Deploy to [Render.com](https://render.com) as a web service.
   - Start command: `streamlit run fundlens/dashboard/app.py --server.port $PORT --server.address 0.0.0.0`
   - Add `DATABASE_URL` as an environment variable in the Render dashboard (never in code).

---

## Roadmap

| Phase | Goal | Status |
|---|---|---|
| 0 — Foundations | Project structure, ingestion, DB, initial load | ✅ Complete |
| 1 — Pipeline + Analysis | Returns/vol/drawdown processing, full dashboard (6 pages incl. About) | ✅ Complete (scheduler pending) |
| 2 — Predictive Models | ARIMA, Prophet, ETS, Linear, XGBoost, LightGBM, LSTM, GARCH vol, walk-forward | 🔄 In progress (models done, DB persistence pending) |
| 3 — Expansion | Macro variables (VIX/FRED), regime detection (HMM), alerts | Pending |
| 4 — User Accounts | Login, per-user fund watchlist (capped), configurable model parameters (ARIMA order, Prophet/XGBoost/LightGBM/LSTM hyperparameters) | Pending — requires hosting (Phase 1 deploy) first |

---

## Security

- **Never commit `.env`** — it is gitignored. Use `.env.example` as a template.
- **Database file is gitignored** — `data/` is excluded entirely.
- **API keys** go in `.env` only. Never hardcode them.
- **Notebook outputs** — strip cell outputs before committing (`Edit → Clear All Outputs` in JupyterLab). Outputs can contain raw data or error messages with connection strings.
- **PostgreSQL connection strings** — set as environment variables in your hosting platform (Render, Railway, etc.), never in code or config files.

---

## License

MIT
