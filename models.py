# MODULE IS THE BLUE PRINT OF THE DATABASE TABLES
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from datetime import datetime
from database import Base

# CREATE THE TABLE MODULE, REPRESENTS UPLOADED FILES. 
class FileRecord(Base):
    __tablename__ = "files"# TABLE NAME IN SQLite 

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    original_name = Column(String)
    stored_name = Column(String, unique=True)
    file_path = Column(String)
    file_type = Column(String)
    file_size = Column(Integer)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    is_deleted = Column(Boolean, default=False)

# SECOND TABLE, TRACK  USER ACTIVITIES.
class ActivityLog(Base):
    __tablename__ = "activity_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    file_id = Column(Integer, ForeignKey("files.id"), nullable=True)
    action = Column(String)
    description = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)