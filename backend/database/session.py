"""
Database session management — SQLAlchemy async-compatible.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from configs.settings import get_settings

settings = get_settings()

raw_url = str(settings.database_url).strip().strip("'").strip('"').strip()
is_sqlite = raw_url.startswith("sqlite")

if is_sqlite:
    # Ensure parent directory exists for SQLite database file
    db_path = raw_url.replace("sqlite:///", "")
    if db_path and not db_path.startswith(":memory:"):
        os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)

    engine = create_engine(
        raw_url,
        connect_args={"check_same_thread": False},
        echo=settings.debug,
    )
    from sqlalchemy import event
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
else:
    db_url = raw_url
    if db_url.startswith("postgresql://"):
        db_url = db_url.replace("postgresql://", "postgresql+psycopg2://", 1)

    engine = create_engine(
        db_url,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20,
        echo=settings.debug,
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency: yields a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    """Create all tables from ORM models (dev convenience; use Alembic in prod)."""
    from backend.models.orm import Base
    Base.metadata.create_all(bind=engine)
