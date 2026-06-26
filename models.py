from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from datetime import datetime

from database import Base


# -----------------------------
# USER TABLE
# -----------------------------
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    username = Column(String, unique=True, nullable=False)

    email = Column(String, unique=True, nullable=False)

    hashed_password = Column(String, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow)


# -----------------------------
# FILES TABLE
# -----------------------------
class FileRecord(Base):
    __tablename__ = "files"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        index=True
    )

    original_name = Column(String, nullable=False)

    stored_name = Column(String, unique=True, nullable=False)

    file_path = Column(String, nullable=False)

    file_type = Column(String)

    file_size = Column(Integer)

    uploaded_at = Column(DateTime, default=datetime.utcnow)

    is_deleted = Column(Boolean, default=False)


# -----------------------------
# ACTIVITY LOG TABLE
# -----------------------------
class ActivityLog(Base):
    __tablename__ = "activity_logs"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        index=True
    )

    file_id = Column(
        Integer,
        ForeignKey("files.id"),
        nullable=True
    )

    action = Column(String, nullable=False)

    description = Column(String)

    created_at = Column(DateTime, default=datetime.utcnow)