from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    DateTime,
    ForeignKey,
)

from database import Base


# ============================================================
# USER MODEL
# ============================================================

class User(Base):
    __tablename__ = "users"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    username = Column(
        String,
        unique=True,
        nullable=False
    )

    email = Column(
        String,
        unique=True,
        nullable=False
    )

    hashed_password = Column(
        String,
        nullable=False
    )

    is_verified = Column(
        Boolean,
        default=False,
        nullable=False
    )

    verification_token_hash = Column(
        String,
        nullable=True
    )

    verification_token_expires = Column(
        DateTime,
        nullable=True
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )


# ============================================================
# FOLDER MODEL
# ============================================================

class FolderRecord(Base):
    __tablename__ = "folders"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        index=True
    )

    name = Column(
        String,
        nullable=False
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )

    is_deleted = Column(
        Boolean,
        default=False
    )


# ============================================================
# FILE MODEL
# ============================================================

class FileRecord(Base):
    __tablename__ = "files"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        index=True
    )

    original_name = Column(
        String,
        nullable=False
    )

    stored_name = Column(
        String,
        unique=True,
        nullable=False
    )

    file_path = Column(
        String,
        nullable=False
    )

    file_type = Column(
        String,
        nullable=True
    )

    file_size = Column(
        Integer,
        nullable=True
    )

    uploaded_at = Column(
        DateTime,
        default=datetime.utcnow
    )

    is_deleted = Column(
        Boolean,
        default=False
    )

    folder_id = Column(
        Integer,
        ForeignKey("folders.id"),
        nullable=True,
        index=True
    )


# ============================================================
# SHARED FILE MODEL
# ============================================================

class SharedFile(Base):
    __tablename__ = "shared_files"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    file_id = Column(
        Integer,
        ForeignKey("files.id"),
        nullable=False,
        index=True
    )

    owner_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False
    )

    target_user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        index=True
    )

    shared_at = Column(
        DateTime,
        default=datetime.utcnow
    )


# ============================================================
# SHARED FOLDER MODEL
# ============================================================

class SharedFolder(Base):
    __tablename__ = "shared_folders"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    folder_id = Column(
        Integer,
        ForeignKey("folders.id"),
        nullable=False,
        index=True
    )

    owner_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False
    )

    target_user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        index=True
    )

    shared_at = Column(
        DateTime,
        default=datetime.utcnow
    )


# ============================================================
# NOTIFICATION MODEL
# ============================================================

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        index=True
    )

    message = Column(
        String,
        nullable=False
    )

    is_read = Column(
        Boolean,
        default=False
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )


# ============================================================
# ACTIVITY LOG MODEL
# ============================================================

class ActivityLog(Base):
    __tablename__ = "activity_logs"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

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

    action = Column(
        String,
        nullable=False
    )

    description = Column(
        String,
        nullable=True
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )