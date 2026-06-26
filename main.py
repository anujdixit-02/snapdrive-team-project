from fastapi import FastAPI, Depends, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from database import Base, engine, get_db
from models import FileRecord, ActivityLog
from file_service import upload_file_service, search_files_service, get_file_by_id
from storage_service import get_storage_details
from activity_service import log_activity

# Authentication Router
from auth_routes import router as auth_router

# Create all database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="SnapDrive Backend API",
    description="Authentication, File Upload, Download, Search, Storage Tracking and Activity Logging",
    version="1.0.0"
)

# Register Authentication APIs
app.include_router(auth_router)


@app.get("/")
def home():
    return {
        "message": "SnapDrive Backend API is running successfully!",
        "modules": [
            "Authentication",
            "File Upload",
            "File Download",
            "File Search",
            "Storage Tracking",
            "Activity Logging"
        ]
    }


# -----------------------------
# FILE UPLOAD
# -----------------------------
@app.post("/files/upload")
async def upload_file(
    user_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    uploaded_file = await upload_file_service(db, user_id, file)

    return {
        "message": "File uploaded successfully",
        "file": {
            "id": uploaded_file.id,
            "original_name": uploaded_file.original_name,
            "stored_name": uploaded_file.stored_name,
            "file_type": uploaded_file.file_type,
            "file_size": uploaded_file.file_size,
            "uploaded_at": uploaded_file.uploaded_at
        }
    }


# -----------------------------
# DOWNLOAD FILE
# -----------------------------
@app.get("/files/{file_id}/download")
def download_file(
    file_id: int,
    user_id: int,
    db: Session = Depends(get_db)
):
    file_record = get_file_by_id(db, user_id, file_id)

    log_activity(
        db=db,
        user_id=user_id,
        action="DOWNLOAD",
        file_id=file_record.id,
        description=f"Downloaded file: {file_record.original_name}"
    )

    return FileResponse(
        path=file_record.file_path,
        filename=file_record.original_name,
        media_type="application/octet-stream"
    )


# -----------------------------
# SEARCH FILES
# -----------------------------
@app.get("/files/search")
def search_files(
    user_id: int,
    query: str,
    db: Session = Depends(get_db)
):
    files = search_files_service(db, user_id, query)

    return {
        "query": query,
        "total_results": len(files),
        "files": [
            {
                "id": file.id,
                "original_name": file.original_name,
                "file_type": file.file_type,
                "file_size": file.file_size,
                "uploaded_at": file.uploaded_at
            }
            for file in files
        ]
    }


# -----------------------------
# STORAGE USAGE
# -----------------------------
@app.get("/storage/usage")
def storage_usage(
    user_id: int,
    db: Session = Depends(get_db)
):
    return get_storage_details(db, user_id)


# -----------------------------
# ACTIVITY LOGS
# -----------------------------
@app.get("/activity/logs")
def activity_logs(
    user_id: int,
    db: Session = Depends(get_db)
):
    logs = db.query(ActivityLog).filter(
        ActivityLog.user_id == user_id
    ).order_by(ActivityLog.created_at.desc()).all()

    return {
        "user_id": user_id,
        "logs": [
            {
                "id": log.id,
                "action": log.action,
                "file_id": log.file_id,
                "description": log.description,
                "created_at": log.created_at
            }
            for log in logs
        ]
    }


# -----------------------------
# DELETE FILE
# -----------------------------
@app.delete("/files/{file_id}")
def delete_file(
    file_id: int,
    user_id: int,
    db: Session = Depends(get_db)
):
    file_record = get_file_by_id(db, user_id, file_id)

    file_record.is_deleted = True
    db.commit()

    log_activity(
        db=db,
        user_id=user_id,
        action="DELETE",
        file_id=file_record.id,
        description=f"Deleted file: {file_record.original_name}"
    )

    return {
        "message": "File deleted successfully",
        "file_id": file_id
    }