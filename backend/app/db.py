from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import Settings, get_settings
from app.models.base import Base

_engine: Engine | None = None
_session_factory: sessionmaker[Session] | None = None


def _create_engine(settings: Settings) -> Engine:
    url = settings.sqlalchemy_url
    is_sqlite = url.startswith("sqlite")
    engine = create_engine(
        url,
        future=True,
        pool_pre_ping=True,
        connect_args={"check_same_thread": False, "timeout": 30} if is_sqlite else {},
    )
    if is_sqlite:

        @event.listens_for(engine, "connect")
        def _sqlite_pragmas(dbapi_connection, _record):  # pragma: no cover - driver hook
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA synchronous=NORMAL")
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    return engine


def get_engine() -> Engine:
    global _engine
    if _engine is None:
        _engine = _create_engine(get_settings())
    return _engine


def get_session_factory() -> sessionmaker[Session]:
    global _session_factory
    if _session_factory is None:
        _session_factory = sessionmaker(bind=get_engine(), expire_on_commit=False, future=True)
    return _session_factory


def _add_missing_columns(engine: Engine) -> None:
    """Bring an existing SQLite file up to the current model.

    `create_all` only creates whole tables, so a database written before a new
    optional column existed would keep failing every query that mentions it.
    Every column this project has added since v1 is nullable, which is exactly
    what SQLite can add in place.
    """
    if not engine.url.get_backend_name().startswith("sqlite"):
        return

    with engine.begin() as connection:
        for table in Base.metadata.sorted_tables:
            existing = {
                row[1] for row in connection.execute(text(f"PRAGMA table_info('{table.name}')"))
            }
            if not existing:
                continue  # table is new; create_all already made it correctly
            for column in table.columns:
                if column.name in existing or not column.nullable:
                    continue
                kind = column.type.compile(dialect=engine.dialect)
                connection.execute(
                    text(f'ALTER TABLE "{table.name}" ADD COLUMN "{column.name}" {kind}')
                )


def init_db() -> None:
    settings = get_settings()
    settings.ensure_directories()
    engine = get_engine()
    Base.metadata.create_all(bind=engine)
    _add_missing_columns(engine)


def reset_engine() -> None:
    """Drop cached engine/session factory so a new configuration is picked up (tests)."""
    global _engine, _session_factory
    if _engine is not None:
        _engine.dispose()
    _engine = None
    _session_factory = None


@contextmanager
def session_scope() -> Iterator[Session]:
    session = get_session_factory()()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_db() -> Iterator[Session]:
    """FastAPI dependency."""
    session = get_session_factory()()
    try:
        yield session
    finally:
        session.close()
