"""SQLAlchemy engine, session factory, and FastAPI DB dependency."""
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app import config


def _build_url() -> URL | str:
    if config.DATABASE_URL_OVERRIDE:
        return config.DATABASE_URL_OVERRIDE
    return URL.create(
        "mysql+pymysql",
        username=config.DB_USER,
        password=config.DB_PASSWORD,
        host=config.DB_HOST,
        port=config.DB_PORT,
        database=config.DB_NAME,
        query={"charset": "utf8mb4"},
    )


_url = _build_url()
_is_sqlite = str(_url).startswith("sqlite")

engine = create_engine(
    _url,
    pool_pre_ping=True,
    **({"connect_args": {"check_same_thread": False}} if _is_sqlite else {}),
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def ensure_database_exists() -> None:
    """Create the p{PAIR}_handshake database if it is missing (MySQL only)."""
    if _is_sqlite:
        return
    server_url = URL.create(
        "mysql+pymysql",
        username=config.DB_USER,
        password=config.DB_PASSWORD,
        host=config.DB_HOST,
        port=config.DB_PORT,
    )
    server_engine = create_engine(server_url, isolation_level="AUTOCOMMIT")
    with server_engine.connect() as conn:
        conn.execute(
            text(
                f"CREATE DATABASE IF NOT EXISTS `{config.DB_NAME}` "
                "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
        )
    server_engine.dispose()


def init_db() -> None:
    """Create the database (if needed) and all tables."""
    from app import models  # noqa: F401  (registers tables on Base.metadata)

    ensure_database_exists()
    Base.metadata.create_all(bind=engine)
