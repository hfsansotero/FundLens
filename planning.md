# FundLens — Project Architecture & Planning

> *Alternativas de nombre al final del documento*

---

## Visión General

Pipeline automatizada de ingesta, almacenamiento, análisis y visualización de NAVs diarios de Mutual Funds, con comparación de modelos predictivos (ARIMA/GARCH vs Prophet) y análisis de correlaciones dinámicas entre fondos.

**Objetivo inicial:** Didáctico, robusto, escalable desde el primer día.
**Objetivo futuro:** Herramienta diferenciada de análisis de fondos con perspectiva temporal.

---

## Fondos Iniciales Sugeridos (Fase 1)

Empezar con 5-6 fondos representativos de categorías distintas para que el análisis de correlaciones sea interesante desde el principio:

| Ticker | Nombre | Categoría | Gestora |
|--------|--------|-----------|---------|
| VFINX | Vanguard 500 Index | Large Blend (US) | Vanguard |
| FCNTX | Fidelity Contrafund | Large Growth (US) | Fidelity |
| VBMFX | Vanguard Total Bond Market | Bonds | Vanguard |
| VGTSX | Vanguard Total Intl Stock | International | Vanguard |
| PRHSX | T. Rowe Price Health Sciences | Sector (Health) | T. Rowe |
| FAGIX | Fidelity Capital & Income | High Yield Bonds | Fidelity |

> Esta selección cubre renta variable US, internacional, bonos y sector, lo que garantiza correlaciones interesantes. En Fase 3 se amplía con fondos equivalentes de otras gestoras para las comparativas same-category cross-gestora.

---

## Stack Tecnológico

```
Capa               Herramienta               Motivo
─────────────────────────────────────────────────────────────
Ingesta de datos   yfinance + tiingo (backup) Gratuito, cubre NAVs de fondos
Scheduling         APScheduler (embedded)     Sin servidor externo en Fase 1
                   → Prefect                  Migración limpia en Fase 2+
Almacenamiento     DuckDB (local/dev)         Sin servidor, SQL completo
                   → Neon PostgreSQL (cloud)  Free tier, no pausa, misma URL
ORM / Acceso       SQLAlchemy 2.x             Abstracción que hace la
                                              migración DuckDB→Postgres
                                              con cambiar una línea
Procesamiento      pandas + numpy             Estándar
Modelos            statsmodels (ARIMA/ETS/GARCH) Clásicos robustos
                   prophet                    Facebook/Meta Prophet
                   scikit-learn               Linear/Ridge regression
                   xgboost + lightgbm         Gradient boosting (lag features)
                   torch (PyTorch)            LSTM 2 capas (CPU)
                   arch                       GARCH volatilidad
Dashboard          Streamlit                  Rápido, pythónico, suficiente
Hosting dashboard  Render.com (free tier)     Deploy Streamlit como web service
Cloud DB           Neon PostgreSQL (free)     0.5 GB, no pausa, compatible SQLAlchemy
Alertas (Fase 2)   smtplib / python-telegram-bot  Sin overhead
Tests              pytest + pytest-cov        Calidad desde el inicio
Config             python-dotenv + pydantic   Settings validados y tipados
Logs               loguru                     Mejor que logging stdlib
Entorno            conda (environment.yml)    Reproducibilidad en conda
```

### Decisión de hosting (dashboard)

**Estrategia híbrida elegida:**
- **Fase 0-1 (local):** DuckDB local + Streamlit en `localhost:8501`. Pipeline corre en la máquina local.
- **Fase 1 end (deploy):** Cambiar `DATABASE_URL` a **Neon PostgreSQL** (free tier, no pausa — a diferencia de Supabase que pausa tras 1 semana). Deploy de Streamlit en **Render.com** (free tier, web service). La pipeline sigue corriendo localmente y escribe en Neon.
- **Fase 3+ (full cloud):** Evaluar mover la pipeline también a la nube (Railway worker, GitHub Actions cron, etc.).

> Streamlit Community Cloud se descartó porque requiere que la DB sea accesible públicamente, y Supabase free tier se descartó porque pausa el proyecto tras 1 semana de inactividad — fatal para una pipeline diaria.

### Sobre la migración DuckDB → PostgreSQL

Con SQLAlchemy como capa de acceso, el cambio es literalmente una línea en el fichero de configuración:

```python
# DuckDB (desarrollo / Fase 1)
DATABASE_URL = "duckdb:///./data/fundlens.duckdb"

# PostgreSQL (producción / Fase 3+)
DATABASE_URL = "postgresql://user:pass@localhost:5432/fundlens"
```

El resto del código (queries, modelos ORM) no cambia. Se añade `alembic` en Fase 2 para migraciones versionadas.

---

## Arquitectura de Directorios

```
fundlens/
│
├── .env                          # Variables de entorno (nunca a git)
├── .env.example                  # Template de variables
├── .gitignore
├── pyproject.toml                # Dependencias y config del proyecto
├── environment.yml               # Conda environment (Python 3.11 + pip deps)
├── README.md
│
├── config/

│   ├── __init__.py
│   ├── settings.py               # Pydantic Settings: carga .env, valida tipos
│   └── funds.yaml                # Lista de fondos a monitorizar (editable sin código)
│
├── data/
│   ├── fundlens.duckdb           # Base de datos principal (ignorada en git)
│   └── exports/                  # CSVs de backup opcionales
│
├── fundlens/                     # Paquete principal
│   ├── __init__.py
│   │
│   ├── ingestion/                # Capa de ingesta de datos
│   │   ├── __init__.py
│   │   ├── base.py               # Clase abstracta DataSource
│   │   ├── yfinance_source.py    # Implementación yfinance
│   │   └── tiingo_source.py      # Implementación Tiingo (backup)
│   │
│   ├── storage/                  # Capa de almacenamiento

│   │   ├── __init__.py
│   │   ├── database.py           # Engine SQLAlchemy, sesiones
│   │   ├── models.py             # Modelos ORM (tablas)
│   │   └── repository.py        # CRUD operations (nunca SQL crudo fuera de aquí)

│   │

│   ├── processing/               # Transformaciones y features
│   │   ├── __init__.py
│   │   ├── returns.py            # Log-returns, retornos acumulados
│   │   ├── volatility.py         # Rolling vol, EWMA vol
│   │   └── features.py           # Feature engineering para modelos
│   │
│   ├── analysis/                 # Análisis estadístico
│   │   ├── __init__.py
│   │   ├── correlations.py       # Correlaciones estáticas y rolling
│   │   ├── regimes.py            # Detección de regímenes (HMM, Fase 2)
│   │   └── drawdown.py           # Drawdown, tiempo de recuperación
│   │
│   ├── models/                   # Modelos predictivos
│   │   ├── __init__.py
│   │   ├── base_model.py         # Clase abstracta: fit(), predict(), score()
│   │   ├── arima_model.py        # ARIMA(1,1,1) — statsmodels
│   │   ├── prophet_model.py      # Prophet — Meta
│   │   ├── ets_model.py          # Holt-Winters amortiguado — statsmodels
│   │   ├── linear_model.py       # Ridge regression sobre lags — sklearn
│   │   ├── tree_models.py        # XGBoost + LightGBM con lags recursivos
│   │   ├── lstm_model.py         # LSTM 2 capas — PyTorch
│   │   ├── garch_model.py        # GARCH(1,1) vol forecaster (no precio)
│   │   └── comparison.py         # Motor walk-forward + compare_models()
│   │
│   ├── pipeline/                 # Orquestación
│   │   ├── __init__.py
│   │   ├── daily_update.py       # Job diario: ingestar + procesar + re-entrenar
│   │   └── scheduler.py          # APScheduler config (→ Prefect en Fase 2)
│   │
│   └── dashboard/                # Interfaz web (Streamlit)
│       ├── __init__.py
│       ├── app.py                # Punto de entrada Streamlit

│       └── pages/
│           ├── 01_overview.py    # Vista general de todos los fondos

│           ├── 02_fund_detail.py # Análisis en profundidad de un fondo
│           ├── 03_correlations.py # Correlaciones dinámicas entre fondos
│           ├── 04_predictions.py  # Comparativa de modelos predictivos
│           └── 05_drawdown.py     # Análisis de caídas y recuperación
│
├── scripts/                      # Scripts de uso puntual
│   ├── initial_load.py           # Carga histórica inicial (años de datos)
│   └── backfill.py               # Rellenar huecos si falla algún día
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py               # Fixtures compartidas (DB en memoria, datos mock)

│   ├── test_ingestion.py
│   ├── test_storage.py
│   ├── test_processing.py
│   ├── test_models.py

│   └── test_pipeline.py
│

└── notebooks/                    # Exploración y prototipado
    ├── 01_eda_inicial.ipynb
    ├── 02_arima_exploration.ipynb
    └── 03_prophet_exploration.ipynb
```

---

## Esquema de Base de Datos

```sql
-- Catálogo de fondos
TABLE funds (
    id          INTEGER PRIMARY KEY,
    ticker      VARCHAR(20) UNIQUE NOT NULL,
    name        VARCHAR(200),
    category    VARCHAR(100),      -- 'Large Blend', 'Bonds', etc.
    manager     VARCHAR(100),      -- 'Vanguard', 'Fidelity', etc.
    currency    VARCHAR(10) DEFAULT 'USD',
    active      BOOLEAN DEFAULT TRUE,
    created_at  TIMESTAMP DEFAULT NOW()
)

-- Serie temporal de precios NAV
TABLE prices (
    id          INTEGER PRIMARY KEY,
    fund_id     INTEGER REFERENCES funds(id),

    date        DATE NOT NULL,
    nav         DECIMAL(12, 4) NOT NULL,   -- Net Asset Value
    log_return  DECIMAL(10, 6),            -- ln(NAV_t / NAV_{t-1})
    source      VARCHAR(50),               -- 'yfinance', 'tiingo'
    created_at  TIMESTAMP DEFAULT NOW(),
    UNIQUE(fund_id, date)
)

-- Métricas calculadas por ventana temporal
TABLE metrics (
    id              INTEGER PRIMARY KEY,
    fund_id         INTEGER REFERENCES funds(id),
    date            DATE NOT NULL,
    rolling_vol_30  DECIMAL(10, 6),    -- Volatilidad rolling 30d
    rolling_vol_90  DECIMAL(10, 6),    -- Volatilidad rolling 90d
    sharpe_90       DECIMAL(10, 6),    -- Sharpe ratio 90d (vs rf=0)
    max_drawdown    DECIMAL(10, 6),    -- Drawdown máximo histórico hasta esa fecha
    UNIQUE(fund_id, date)
)

-- Predicciones almacenadas
TABLE predictions (
    id              INTEGER PRIMARY KEY,
    fund_id         INTEGER REFERENCES funds(id),
    model_name      VARCHAR(50),       -- 'arima', 'prophet', 'garch'

    predicted_for   DATE NOT NULL,     -- Fecha que se predijo
    predicted_at    DATE NOT NULL,     -- Fecha en que se hizo la predicción
    predicted_value DECIMAL(12, 4),
    lower_bound     DECIMAL(12, 4),
    upper_bound     DECIMAL(12, 4),
    model_params    JSON               -- Hiperparámetros usados
)

-- Resultados de comparación de modelos
TABLE model_scores (
    id          INTEGER PRIMARY KEY,
    fund_id     INTEGER REFERENCES funds(id),
    model_name  VARCHAR(50),
    eval_date   DATE NOT NULL,
    mae         DECIMAL(10, 6),
    rmse        DECIMAL(10, 6),
    mape        DECIMAL(10, 6),
    horizon_days INTEGER             -- A cuántos días se predijo
)

-- Trazabilidad de cada intento de ingesta
TABLE ingestion_log (
    id           INTEGER PRIMARY KEY,
    fund_id      INTEGER REFERENCES funds(id),
    date         DATE NOT NULL,
    status       VARCHAR(20),   -- 'success', 'failed', 'missing_from_source'
    source       VARCHAR(50),   -- 'yfinance', 'tiingo', 'initial_load'

    error_msg    TEXT,          -- Mensaje de error si status = 'failed'
    attempted_at TIMESTAMP DEFAULT NOW()
)
```

> **Nota importante:** poblar `ingestion_log` desde el primer momento, incluyendo durante la carga histórica inicial (`initial_load.py`), no solo en el job diario. Así se tiene trazabilidad completa desde el día uno — si algo falla en medio del backfill, el log indica exactamente en qué fondo y qué fecha se cortó, sin tener que deducirlo comparando contra el calendario de mercado.

---

## Planning por Fases

### FASE 0 — Fundamentos (Semana 1-2)

*Objetivo: proyecto corriendo localmente, datos entrando, nada roto*

- [x] Crear estructura de directorios y `pyproject.toml` + `environment.yml`
- [x] Configurar `settings.py` con Pydantic (API keys, paths, lista de fondos)
- [x] Implementar `yfinance_source.py` con manejo de errores y reintentos
- [x] Crear modelos ORM y `database.py` con DuckDB + SQLAlchemy
- [x] Script `initial_load.py` para cargar histórico (mínimo 5 años)
- [x] Tests básicos de ingesta y almacenamiento
- [x] Crear conda env → `conda env create -f environment.yml`
- [x] `cp .env.example .env`
- [x] Ejecutar `python scripts/initial_load.py --all-funds --years 5`
- [x] CI/CD con GitHub Actions (push a `dev` + PR a `main`)

**Entregable:** ✅ `python scripts/initial_load.py` funciona y hay 5+ años de NAVs en DuckDB.

---

### FASE 1 — Pipeline Básica + Análisis (Semana 3-5)

*Objetivo: pipeline diaria automática y primeros análisis*

- [ ] `daily_update.py`: job que cada día laboral a las 18:00 descarga el NAV del día
- [ ] `scheduler.py`: APScheduler corriendo en background
- [x] `returns.py`: cálculo de log-returns y retornos acumulados
- [x] `volatility.py`: volatilidad rolling (30d, 90d), Sharpe
- [x] `correlations.py`: matriz de correlaciones estática y rolling
- [x] `drawdown.py`: cálculo de drawdown (recovery_periods pendiente)
- [x] Dashboard Streamlit — 5 páginas en vivo: overview, fund detail, correlations, predictions, drawdown

**Entregable:** ✅ Dashboard en `localhost:8501` con datos reales. Pendiente: scheduler diario.

#### Deploy al final de Fase 1 (opcional pero recomendado)

```bash
# 1. Crear DB en Neon (neon.tech, free tier)
#    → copiar connection string, actualizar DATABASE_URL en .env

# 2. Re-ejecutar initial_load.py apuntando a Neon
DATABASE_URL=postgresql://... python scripts/initial_load.py --all-funds --years 5

# 3. Deploy Streamlit en Render.com
#    → New Web Service → connect repo → Start command:
streamlit run fundlens/dashboard/app.py --server.port $PORT --server.address 0.0.0.0
```

---

### FASE 2 — Modelos Predictivos + Comparación (Semana 6-9)

*Objetivo: el núcleo de ML del proyecto*

- [x] `base_model.py`: interfaz abstracta `fit()`, `predict()`, `score()`
- [x] `arima_model.py`: ARIMA(1,1,1) con statsmodels
- [x] `garch_model.py`: GARCH(1,1) — forecaster de volatilidad (no de precio)
- [x] `prophet_model.py`: wrapper Prophet con estacionalidad semanal/anual
- [x] `ets_model.py`: Holt-Winters amortiguado (statsmodels, sin deps extra)
- [x] `linear_model.py`: Ridge regression sobre lag features (sklearn)
- [x] `tree_models.py`: XGBoost + LightGBM con lag features recursivos
- [x] `lstm_model.py`: LSTM 2 capas con PyTorch (ventana=60, normalización z-score)
- [x] `comparison.py`: motor walk-forward, cálculo de MAE/RMSE/MAPE por horizonte
- [x] Página `04_predictions.py`: forecast chart, GARCH vol, comparativa walk-forward
- [ ] Almacenamiento de scores walk-forward en `model_scores` (DB)
- [ ] Almacenamiento de predicciones en `predictions` (DB)
- [ ] Notebooks de exploración

**Entregable:** 🔄 Dashboard muestra predicciones y comparativa de 7 modelos. Pendiente: persistencia en DB.**

---

### FASE 3 — Ampliación y Diferenciación (Semana 10+)

*Objetivo: hacer el proyecto interesante y único*

- [ ] Añadir fondos equivalentes de otras gestoras (same-category cross-gestora)

- [ ] `regimes.py`: detección de regímenes con HMM (bull/bear/volatile)
- [ ] Análisis de correlaciones en crisis vs. mercado normal
- [ ] Integración de variables macro (VIX, tipos Fed via FRED API — gratuita)
- [ ] Sistema de alertas (email/Telegram) cuando hay anomalías
- [ ] Migración a Prefect para orquestación más robusta
- [ ] Evaluar migración DuckDB → PostgreSQL si la DB supera ~500MB

---

## Decisiones de Diseño Importantes

### Por qué log-returns y no precios absolutos

Trabajar con `ln(P_t / P_{t-1})` en lugar de precios tiene varias ventajas:

- Son (aproximadamente) estacionarios → los modelos de series temporales lo agradecen
- Son comparables entre fondos con distintos rangos de precio
- Son aditivos en el tiempo: retorno de 2 días = suma de retornos diarios

### Manejo de días sin datos

Los fondos no tienen NAV en fines de semana ni festivos de mercado. La pipeline debe:

1. No crear filas con NAV nulo — simplemente no insertar
2. Al calcular rolling metrics, usar `min_periods` para evitar NaN en bordes
3. En el dashboard, mostrar solo días de mercado (no rellenar huecos)

### Walk-forward validation (no train/test split estático)

Para evaluar modelos de series temporales, nunca un split fijo. Usar walk-forward:

- Entrenar con datos hasta fecha T, predecir T+h
- Avanzar T un paso, repetir
- Promediar errores — esto simula uso real

### Abstracción de fuente de datos

`base.py` define una interfaz `DataSource` con método `fetch(ticker, start, end)`.
Si yfinance falla o cambia su API, se cambia solo `yfinance_source.py` sin tocar nada más.

---

## Primeros Pasos Concretos (Esta Semana)

```bash
# 1. Crear el proyecto
mkdir fundlens && cd fundlens
git init

# 2. Configurar pyproject.toml con estas dependencias
# yfinance, duckdb, sqlalchemy, pandas, numpy,
# streamlit, statsmodels, prophet, scikit-learn,
# pydantic-settings, python-dotenv, loguru,
# apscheduler, pytest, pytest-cov


# 3. Crear .env desde .env.example
cp .env.example .env

# 4. Primer objetivo: que este script funcione

python scripts/initial_load.py --tickers VFINX FCNTX VBMFX --years 5
```

El primer hito concreto y verificable es tener esos datos en DuckDB y poder hacer una query simple:

```sql
SELECT date, nav, log_return
FROM prices p
JOIN funds f ON f.id = p.fund_id
WHERE f.ticker = 'VFINX'

ORDER BY date DESC

LIMIT 10;
```

Cuando eso funcione, todo lo demás se construye encima.
