# FundLens

Automated pipeline for ingesting, storing, analyzing, and visualizing daily NAVs (Net Asset Values) of mutual funds — with predictive model comparison (ARIMA, Prophet, ETS, Linear, XGBoost, LightGBM, LSTM) and dynamic correlation analysis.

> **Status:** Phase 1 complete and deployed — live at **[fundlens-n43k.onrender.com](https://fundlens-n43k.onrender.com)**. Phase 2 in progress (models implemented, DB persistence pending).

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
| Scheduling | GitHub Actions cron (prod) + APScheduler (local, optional) | No external server needed |
| Database | DuckDB (local) → Neon PostgreSQL (cloud) | SQLAlchemy abstraction = one-line swap |
| ORM | SQLAlchemy 2.x | Typed mapped columns |
| Processing | pandas + numpy | — |
| Models | statsmodels, prophet, scikit-learn, xgboost, lightgbm, arch, torch | Phase 2 |
| Dashboard | Streamlit + Plotly | Hosted on Render.com |
| Config | pydantic-settings + python-dotenv | Validated, typed settings |
| Logging | loguru | — |
| Tests | pytest + pytest-cov | — |
| Environment | conda (Python 3.11) or plain venv + pip | `environment.yml` for conda; `pyproject.toml` extras for venv |

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
│   ├── analysis/             # Correlations, drawdown, regime detection (Phase 3, stub)
│   ├── models/               # 7 price models + GARCH vol + walk-forward comparison engine
│   ├── pipeline/             # Daily update job + APScheduler config
│   └── dashboard/            # Streamlit app + 6 pages
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

### 1. Create an environment and install the package

Pick whichever you already have set up — the rest of this guide is identical either way.

**Option A — conda (recommended, used for development)**

```bash
conda env create -f environment.yml
conda activate fundlens
pip install -e .
# Phase 2 ML — install PyTorch CPU-only (avoids a conda Intel VTune symbol conflict):
pip install torch --index-url https://download.pytorch.org/whl/cpu
```

**Option B — venv + pip (no conda required)**

```bash
python3.11 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install --upgrade pip
pip install -e ".[ml,dev]"
# Phase 2 ML — CPU-only PyTorch wheel (smaller download if you don't have a CUDA GPU):
pip install torch --index-url https://download.pytorch.org/whl/cpu
```

> **Note (both options):** `prophet` compiles a Stan model via `cmdstanpy` on first install, which can take a few minutes and needs a C++ compiler available (Xcode Command Line Tools on macOS, `build-essential` on Linux, MSVC Build Tools on Windows). If you only want to test the dashboard/pipeline without the ML models, skip the `[ml,dev]` extras / PyTorch step — `fundlens.models` imports lazily and degrades gracefully without them; only `pytest`-related and ML-specific commands will fail.

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env — add TIINGO_API_KEY if you have one (optional for Phase 0)
```

### 3. Load historical data

```bash
python scripts/initial_load.py --all-funds --years 5
# or specific tickers:
python scripts/initial_load.py --tickers VFINX FCNTX VBMFX --years 5
```

### 4. Verify data

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

### 5. Launch dashboard

```bash
streamlit run fundlens/dashboard/app.py
# Opens at http://localhost:8501
```

### 6. Start daily scheduler (optional)

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

## Funds Tracked

14 funds (6 USD, 8 EUR) — edit `config/funds.yaml` to change the list.

| Ticker | Name | Category | Manager | Currency |
|---|---|---|---|---|
| VFINX | Vanguard 500 Index | Large Blend | Vanguard | USD |
| FCNTX | Fidelity Contrafund | Large Growth | Fidelity | USD |
| VBMFX | Vanguard Total Bond Market | Bonds | Vanguard | USD |
| VGTSX | Vanguard Total International Stock | International | Vanguard | USD |
| PRHSX | T. Rowe Price Health Sciences | Sector Health | T. Rowe Price | USD |
| FAGIX | Fidelity Capital & Income | High Yield Bonds | Fidelity | USD |
| 0P0001CLDK.F | Fidelity MSCI World Index Fund P-ACC-EUR | Large Blend (Global) | Fidelity | EUR |
| 0P00012I6A.F | Vanguard Emerging Markets Stock Index Acc | Emerging Markets | Vanguard | EUR |
| 0P00015OFP.F | Fidelity Global Technology A-Acc-EUR | Sector Technology | Fidelity | EUR |
| 0P0001XF42.F | iShares US Index (IE) S Acc | Large Blend (US) | iShares (BlackRock) | EUR |
| 0P0001CLDI.F | Fidelity MSCI Japan Index EUR P Acc | Japan Equity | Fidelity | EUR |
| 0P0001CJGN.F | Fidelity MSCI Europe Index EUR P Acc | Europe Equity | Fidelity | EUR |
| 0P00006TV8.F | Vanguard U.S. 500 Stock Index EUR Hedged Acc | Large Blend (US, EUR Hedged) | Vanguard | EUR |
| 0P0001COSJ | Fidelity MSCI Pacific ex Japan Index USD P Acc | Asia Pacific ex Japan | Fidelity | USD |

---

## Running Tests

```bash
pytest
# With coverage report:
pytest --cov=fundlens --cov-report=html
```

---

## Cloud Deployment (live)

Currently deployed at **[fundlens-n43k.onrender.com](https://fundlens-n43k.onrender.com)**. To reproduce:

1. **Database:** Create a free project at [neon.tech](https://neon.tech), copy the connection string (Neon dashboard → **Connect**).
2. **Migrate data:** `export DATABASE_URL=<neon-connection-string>` then re-run `python scripts/initial_load.py --all-funds --years 5`.
3. **Dashboard:** Deploy to [Render.com](https://render.com) as a web service, connected to this repo's `main` branch.
   - Build command: `pip install -e ".[postgres,ml-light]"` (the plain `.` install skips the `psycopg2` driver and all prediction models)
   - Start command: `streamlit run fundlens/dashboard/app.py --server.port $PORT --server.address 0.0.0.0`
   - Add `DATABASE_URL` as an environment variable in the Render dashboard (never in code). Render auto-redeploys on every push to the tracked branch.
4. **Daily ingestion:** GitHub Actions workflow `.github/workflows/daily_update.yml` runs twice on weekdays, fixed at **23:30 UTC** (first attempt) and **01:30 UTC** (retry, if data was missing) — cron is UTC-pinned, so the ET-equivalent shifts by an hour with US daylight saving (see the dashboard's About tab for the live local-time conversion). Runs against the same Neon `DATABASE_URL` — set as a repo secret (Settings → Secrets and variables → Actions). Scheduled triggers only fire from workflow files on the default branch (`main`).
5. **Tiingo:** intentionally not configured in production — its free-tier license is "internal use only" and forbids sharing the data publicly. The pipeline already falls back cleanly to yfinance-only when `TIINGO_API_KEY` is unset.
6. **Prediction models:** only the lightweight ones (ARIMA, ETS, Linear/Ridge, Prophet, GARCH — `ml-light` extra, ~160MB) run in production. LSTM (torch), XGBoost and LightGBM pull in ~1GB+ of deps — too heavy for Render's free 512MB RAM — so the dashboard greys them out (❌) when their package isn't installed. They still work locally with `pip install -e ".[ml]"`.

---

## Roadmap

| Phase | Goal | Status |
|---|---|---|
| 0 — Foundations | Project structure, ingestion, DB, initial load | ✅ Complete |
| 1 — Pipeline + Analysis | Returns/vol/drawdown processing, full dashboard (6 pages incl. About) | ✅ Complete (daily cron live via GitHub Actions) |
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
