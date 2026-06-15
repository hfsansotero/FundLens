from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from loguru import logger

from config.settings import settings


class Base(DeclarativeBase):
    pass


def _get_engine():
    url = settings.database_url
    logger.debug(f"Creating DB engine: {url.split('://')[0]}")
    engine = create_engine(url, echo=False)

    # DuckDB-specific: enable unsigned integers extension
    if url.startswith("duckdb"):
        @event.listens_for(engine, "connect")
        def connect(dbapi_conn, _):
            dbapi_conn.execute("INSTALL json; LOAD json;")

    return engine


engine = _get_engine()
Session = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_session():
    """Context-manager style session. Use with `with get_session() as s:`."""
    return Session()


def init_db() -> None:
    """Create all tables. Safe to call multiple times (CREATE IF NOT EXISTS)."""
    from fundlens.storage import models  # noqa: F401 — ensure models are registered
    Base.metadata.create_all(engine)
    logger.info("Database schema initialized")
