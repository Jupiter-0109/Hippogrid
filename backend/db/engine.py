"""SQLAlchemy Engine configuration for HippoGrid Supabase PostgreSQL."""
from sqlalchemy import create_engine
from backend.core.config import get_settings

settings = get_settings()

engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    pool_recycle=1800,
    connect_args={"connect_timeout": 5} if "postgresql" in settings.DATABASE_URL else {},
)
