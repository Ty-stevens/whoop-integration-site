import os
from pathlib import Path

from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401
from app.core.config import get_settings
from app.db.base import Base


def _sqlite_path(database_url: str) -> Path | None:
    prefix = "sqlite:///"
    if not database_url.startswith(prefix):
        return None
    raw_path = database_url.removeprefix(prefix)
    if raw_path == ":memory:":
        return None
    return Path(raw_path)


def initialize_database(database_url: str | None = None) -> None:
    url = database_url or get_settings().database_url
    db_path = _sqlite_path(url)
    if db_path is not None:
        db_path.parent.mkdir(parents=True, exist_ok=True)


def normalize_database_url(database_url: str) -> str:
    if database_url.startswith("postgres://"):
        return database_url.replace("postgres://", "postgresql+psycopg://", 1)
    if database_url.startswith("postgresql://"):
        return database_url.replace("postgresql://", "postgresql+psycopg://", 1)
    return database_url


def _vercel_sqlite_fallback(database_url: str) -> str:
    if not os.getenv("VERCEL"):
        return database_url
    if not database_url.startswith("sqlite:///"):
        return database_url
    if database_url == "sqlite:///:memory:":
        return database_url

    sqlite_path = _sqlite_path(database_url)
    if sqlite_path is None:
        return database_url

    # Vercel runtime filesystem is read-only except /tmp.
    if not sqlite_path.is_absolute() or str(sqlite_path).startswith("data"):
        return "sqlite:////tmp/endurasync.db"

    return database_url


def create_engine_for_url(database_url: str) -> Engine:
    normalized_url = normalize_database_url(_vercel_sqlite_fallback(database_url))
    try:
        initialize_database(normalized_url)
    except OSError:
        if os.getenv("VERCEL") and normalized_url.startswith("sqlite:///"):
            normalized_url = "sqlite:////tmp/endurasync.db"
            initialize_database(normalized_url)
        else:
            raise

    connect_args = {"check_same_thread": False} if normalized_url.startswith("sqlite") else {}
    engine_kwargs = {"connect_args": connect_args, "future": True}
    if normalized_url == "sqlite:///:memory:":
        engine_kwargs["poolclass"] = StaticPool
    engine = create_engine(normalized_url, **engine_kwargs)

    if normalized_url.startswith("sqlite"):

        @event.listens_for(engine, "connect")
        def enable_sqlite_wal(dbapi_connection, _connection_record) -> None:  # type: ignore[no-untyped-def]
            cursor = dbapi_connection.cursor()
            try:
                cursor.execute("PRAGMA journal_mode=WAL")
                cursor.execute("PRAGMA foreign_keys=ON")
            finally:
                cursor.close()

    # Serverless deployments and fresh local installs start with empty databases.
    # Ensure the application schema exists before any route touches the DB.
    Base.metadata.create_all(bind=engine)

    return engine


settings = get_settings()
engine = create_engine_for_url(settings.database_url)
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
    future=True,
)


def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_database() -> bool:
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
    return True
