"""SQLAlchemy database engine, session factory, and table management."""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from app.config import settings


engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=1,
    max_overflow=2,
    pool_recycle=300,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""
    pass


def get_db():
    """FastAPI dependency that yields a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    """Create all tables defined in models. Safe to call multiple times."""
    from app import models  # noqa: F401 — import to register models
    Base.metadata.create_all(bind=engine)


def drop_tables():
    """Drop all tables. USE WITH CAUTION."""
    from app import models  # noqa: F401
    Base.metadata.drop_all(bind=engine)
