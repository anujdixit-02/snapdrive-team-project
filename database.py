import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Determine database URL
DATABASE_URL = os.environ.get("DATABASE_URL")

if DATABASE_URL:
    # SQLAlchemy requires postgresql:// instead of postgres://
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
else:
    if "VERCEL" in os.environ:
        DATABASE_URL = "sqlite:////tmp/snapdrive.db"
    else:
        DATABASE_URL = "sqlite:///./snapdrive.db"

# Create database engine
connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args
)

# Create database session
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Base class for all database models
Base = declarative_base()


# Dependency used in FastAPI
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
 