"""SQLAlchemy database session management for HippoGrid."""
import logging
import time
from typing import Any, Dict, Generator
from sqlalchemy import text
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from backend.core.config import get_settings
from backend.db.engine import engine

logger = logging.getLogger("hippogrid.db")
settings = get_settings()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """Dependency for obtaining a database session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_db_connection(target_engine=None) -> Dict[str, Any]:
    """Verify live connectivity to PostgreSQL database."""
    eng = target_engine or engine
    start_time = time.perf_counter()
    try:
        with eng.connect() as connection:
            result = connection.execute(text("SELECT 1")).scalar()
            latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
            if result == 1:
                return {
                    "connected": True,
                    "status": "healthy",
                    "latency_ms": latency_ms,
                    "database_url": settings.DATABASE_URL.split("@")[-1] if "@" in settings.DATABASE_URL else "configured",
                }
            return {
                "connected": False,
                "status": "unexpected_result",
                "error": f"Expected 1, got {result}",
                "latency_ms": latency_ms,
            }
    except Exception as exc:
        latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
        logger.warning(f"Database connection check failed: {exc}")
        return {
            "connected": False,
            "status": "error",
            "error": str(exc),
            "latency_ms": latency_ms,
        }
