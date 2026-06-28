from fastapi import FastAPI, Depends, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from database import Base, engine, get_db
from models import User, FileRecord, ActivityLog, SharedFile, FolderRecord, Notification, SharedFolder
from file_service import upload_file_service, search_files_service, get_file_by_id
from storage_service import get_storage_details
from activity_service import log_activity

from fastapi.middleware.cors import CORSMiddleware

# Authentication Router
from auth_routes import router as auth_router

# Create all database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="SnapDrive Backend API",
    description="Authentication, File Upload, Download, Search, Storage Tracking and Activity Logging",
    version="1.0.0"
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # allow all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Register Authentication APIs
app.include_router(auth_router)


@app.get("/")
def home():
    return FileResponse("fronthend/index.html")


# -----------------------------
# FILE UPLOAD
# -----------------------------
@app.post("/files/upload")
async def upload_file(
    user_id: int,
    folder_id: int = None,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    uploaded_file = await upload_file_service(db, user_id, file, folder_id)

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
# VIEW/PREVIEW FILE
# -----------------------------
@app.get("/files/{file_id}/view")
def view_file_inline(
    file_id: int,
    user_id: int,
    db: Session = Depends(get_db)
):
    # Check if user owns the file or it's shared with them
    file_record = db.query(FileRecord).filter(FileRecord.id == file_id).first()
    if not file_record:
        raise HTTPException(status_code=404, detail="File not found")
        
    is_owner = file_record.user_id == user_id
    is_shared = db.query(SharedFile).filter(SharedFile.file_id == file_id, SharedFile.target_user_id == user_id).first()
    is_folder_shared = False
    if file_record.folder_id:
        is_folder_shared = db.query(SharedFolder).filter(
            SharedFolder.folder_id == file_record.folder_id,
            SharedFolder.target_user_id == user_id
        ).first() is not None
    
    if not is_owner and not is_shared and not is_folder_shared:
        raise HTTPException(status_code=403, detail="Permission denied")
    
    # Try to guess media type based on original name
    import mimetypes
    media_type, _ = mimetypes.guess_type(file_record.original_name)
    if not media_type:
        media_type = "application/octet-stream"

    log_activity(
        db=db,
        user_id=user_id,
        action="VIEW",
        file_id=file_record.id,
        description=f"Viewed file: {file_record.original_name}"
    )

    return FileResponse(
        path=file_record.file_path,
        media_type=media_type,
        content_disposition_type="inline"
    )


# -----------------------------
# DOWNLOAD FILE
# -----------------------------
@app.get("/files/{file_id}/download")
def download_file(
    file_id: int,
    user_id: int,
    db: Session = Depends(get_db)
):
    file_record = db.query(FileRecord).filter(FileRecord.id == file_id).first()
    if not file_record:
        raise HTTPException(status_code=404, detail="File not found")
        
    is_owner = file_record.user_id == user_id
    is_shared = db.query(SharedFile).filter(SharedFile.file_id == file_id, SharedFile.target_user_id == user_id).first()
    is_folder_shared = False
    if file_record.folder_id:
        is_folder_shared = db.query(SharedFolder).filter(
            SharedFolder.folder_id == file_record.folder_id,
            SharedFolder.target_user_id == user_id
        ).first() is not None
    
    if not is_owner and not is_shared and not is_folder_shared:
        raise HTTPException(status_code=403, detail="Permission denied")

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
# USER SEARCH
# -----------------------------
@app.get("/users/search")
def search_users(
    query: str,
    exclude_user_id: int = None,
    db: Session = Depends(get_db)
):
    query_filter = (User.username.ilike(f"%{query}%")) | (User.email.ilike(f"%{query}%"))
    
    q = db.query(User).filter(query_filter)
    if exclude_user_id:
        q = q.filter(User.id != exclude_user_id)
        
    users = q.limit(5).all()

    return {
        "users": [
            {"id": u.id, "username": u.username, "email": u.email}
            for u in users
        ]
    }


# -----------------------------
# SHARE FILE
# -----------------------------
@app.post("/files/{file_id}/share")
def share_file(
    file_id: int,
    target_user_id: int,
    user_id: int,
    db: Session = Depends(get_db)
):
    file_record = get_file_by_id(db, user_id, file_id)
    target_user = db.query(User).filter(User.id == target_user_id).first()
    
    if not target_user:
        raise HTTPException(status_code=404, detail="Target user not found")

    # Save shared record
    shared_record = SharedFile(
        file_id=file_id,
        owner_id=user_id,
        target_user_id=target_user_id
    )
    db.add(shared_record)

    # Fetch sender info
    sender = db.query(User).filter(User.id == user_id).first()
    sender_name = sender.username if sender else "Someone"

    # Create notification for target user
    notification = Notification(
        user_id=target_user_id,
        message=f"@{sender_name} shared a file with you: {file_record.original_name}"
    )
    db.add(notification)
    db.commit()

    log_activity(
        db=db,
        user_id=user_id,
        action="SHARE",
        file_id=file_id,
        description=f"Shared {file_record.original_name} with {target_user.username}"
    )

    return {"status": "success", "message": f"Shared with {target_user.username}"}


@app.get("/files/shared-with-me")
def list_shared_files(
    user_id: int,
    db: Session = Depends(get_db)
):
    # 1. Explicitly shared files
    shared_entries = db.query(SharedFile).filter(SharedFile.target_user_id == user_id).all()
    
    results = []
    seen_file_ids = set()
    
    for entry in shared_entries:
        file = db.query(FileRecord).filter(FileRecord.id == entry.file_id).first()
        owner = db.query(User).filter(User.id == entry.owner_id).first()
        if file and not file.is_deleted:
            seen_file_ids.add(file.id)
            results.append({
                "id": file.id,
                "original_name": file.original_name,
                "file_type": file.file_type,
                "file_size": file.file_size,
                "shared_at": entry.shared_at,
                "owner_name": owner.username if owner else "Unknown",
                "folder_id": file.folder_id
            })
            
    # 2. Files inside shared folders
    shared_folders = db.query(SharedFolder).filter(SharedFolder.target_user_id == user_id).all()
    for sf in shared_folders:
        folder_files = db.query(FileRecord).filter(
            FileRecord.folder_id == sf.folder_id,
            FileRecord.is_deleted == False
        ).all()
        owner = db.query(User).filter(User.id == sf.owner_id).first()
        for file in folder_files:
            if file.id not in seen_file_ids:
                seen_file_ids.add(file.id)
                results.append({
                    "id": file.id,
                    "original_name": file.original_name,
                    "file_type": file.file_type,
                    "file_size": file.file_size,
                    "shared_at": sf.shared_at,
                    "owner_name": owner.username if owner else "Unknown",
                    "folder_id": file.folder_id
                })
            
    return {"shared_files": results}


@app.post("/folders/{folder_id}/share")
def share_folder(
    folder_id: int,
    target_user_id: int,
    user_id: int,
    db: Session = Depends(get_db)
):
    folder = db.query(FolderRecord).filter(
        FolderRecord.id == folder_id,
        FolderRecord.user_id == user_id,
        FolderRecord.is_deleted == False
    ).first()
    
    if not folder:
        raise HTTPException(status_code=404, detail="Folder not found")
        
    target_user = db.query(User).filter(User.id == target_user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="Target user not found")
        
    # Check if already shared
    existing = db.query(SharedFolder).filter(
        SharedFolder.folder_id == folder_id,
        SharedFolder.target_user_id == target_user_id
    ).first()
    
    if not existing:
        shared_record = SharedFolder(
            folder_id=folder_id,
            owner_id=user_id,
            target_user_id=target_user_id
        )
        db.add(shared_record)
        
    # Fetch sender info
    sender = db.query(User).filter(User.id == user_id).first()
    sender_name = sender.username if sender else "Someone"

    # Create notification for target user
    notification = Notification(
        user_id=target_user_id,
        message=f"@{sender_name} shared a folder with you: {folder.name}"
    )
    db.add(notification)
    db.commit()

    log_activity(
        db=db,
        user_id=user_id,
        action="SHARE_FOLDER",
        file_id=None,
        description=f"Shared folder {folder.name} with {target_user.username}"
    )

    return {"status": "success", "message": f"Shared folder with {target_user.username}"}


@app.get("/folders/shared-with-me")
def list_shared_folders(
    user_id: int,
    db: Session = Depends(get_db)
):
    shared_entries = db.query(SharedFolder).filter(SharedFolder.target_user_id == user_id).all()
    
    results = []
    for entry in shared_entries:
        folder = db.query(FolderRecord).filter(FolderRecord.id == entry.folder_id).first()
        owner = db.query(User).filter(User.id == entry.owner_id).first()
        if folder and not folder.is_deleted:
            results.append({
                "id": folder.id,
                "name": folder.name,
                "shared_at": entry.shared_at,
                "owner_name": owner.username if owner else "Unknown"
            })
            
    return {"shared_folders": results}


@app.get("/files/search")
def search_files(
    user_id: int,
    query: str = "",
    folder_id: str = "all",
    db: Session = Depends(get_db)
):
    # Owned files
    files = search_files_service(db, user_id, query, folder_id)
    
    # Owned folders
    folders = []
    if query:
        folders = db.query(FolderRecord).filter(
            FolderRecord.user_id == user_id,
            FolderRecord.name.like(f"%{query}%"),
            FolderRecord.is_deleted == False
        ).all()
        
    # Shared files & folders matching query
    if query:
        # Get shared files (explicitly shared)
        shared_file_entries = db.query(SharedFile).filter(SharedFile.target_user_id == user_id).all()
        shared_file_ids = [se.file_id for se in shared_file_entries]
        
        # Get shared folders
        shared_folder_entries = db.query(SharedFolder).filter(SharedFolder.target_user_id == user_id).all()
        shared_folder_ids = [sfe.folder_id for sfe in shared_folder_entries]
        
        # Search shared files
        matching_shared_files = db.query(FileRecord).filter(
            FileRecord.id.in_(shared_file_ids),
            FileRecord.original_name.like(f"%{query}%"),
            FileRecord.is_deleted == False
        ).all()
        
        # Search files in shared folders
        matching_folder_files = db.query(FileRecord).filter(
            FileRecord.folder_id.in_(shared_folder_ids),
            FileRecord.original_name.like(f"%{query}%"),
            FileRecord.is_deleted == False
        ).all()
        
        # Search shared folders
        matching_shared_folders = db.query(FolderRecord).filter(
            FolderRecord.id.in_(shared_folder_ids),
            FolderRecord.name.like(f"%{query}%"),
            FolderRecord.is_deleted == False
        ).all()
        
        # Merge folders
        seen_folder_ids = {f.id for f in folders}
        for sf in matching_shared_folders:
            if sf.id not in seen_folder_ids:
                seen_folder_ids.add(sf.id)
                folders.append(sf)
                
        # Merge files
        seen_file_ids = {f.id for f in files}
        for mf in matching_shared_files:
            if mf.id not in seen_file_ids:
                seen_file_ids.add(mf.id)
                files.append(mf)
        for mf in matching_folder_files:
            if mf.id not in seen_file_ids:
                seen_file_ids.add(mf.id)
                files.append(mf)

    return {
        "query": query,
        "total_results": len(files) + len(folders),
        "files": [
            {
                "id": file.id,
                "user_id": file.user_id,
                "original_name": file.original_name,
                "file_type": file.file_type,
                "file_size": file.file_size,
                "uploaded_at": file.uploaded_at,
                "folder_id": file.folder_id
            }
            for file in files
        ],
        "folders": [
            {
                "id": fold.id,
                "user_id": fold.user_id,
                "name": fold.name,
                "created_at": fold.created_at
            }
            for fold in folders
        ]
    }



# -----------------------------
# SHARED HISTORY & REVOCATION
# -----------------------------
@app.get("/files/shared-by-me")
def list_shared_by_me(
    user_id: int,
    db: Session = Depends(get_db)
):
    # Query shared files
    shared_files = db.query(SharedFile).filter(SharedFile.owner_id == user_id).all()
    files_list = []
    for sf in shared_files:
        file = db.query(FileRecord).filter(FileRecord.id == sf.file_id).first()
        target = db.query(User).filter(User.id == sf.target_user_id).first()
        if file and not file.is_deleted:
            files_list.append({
                "share_id": sf.id,
                "item_id": file.id,
                "name": file.original_name,
                "type": "file",
                "shared_with": target.username if target else "Unknown",
                "shared_with_email": target.email if target else "",
                "shared_at": sf.shared_at
            })
            
    # Query shared folders
    shared_folders = db.query(SharedFolder).filter(SharedFolder.owner_id == user_id).all()
    folders_list = []
    for sf in shared_folders:
        folder = db.query(FolderRecord).filter(FolderRecord.id == sf.folder_id).first()
        target = db.query(User).filter(User.id == sf.target_user_id).first()
        if folder and not folder.is_deleted:
            folders_list.append({
                "share_id": sf.id,
                "item_id": folder.id,
                "name": folder.name,
                "type": "folder",
                "shared_with": target.username if target else "Unknown",
                "shared_with_email": target.email if target else "",
                "shared_at": sf.shared_at
            })
            
    # Sort by shared date newest first
    shares = files_list + folders_list
    shares.sort(key=lambda x: x["shared_at"] or "", reverse=True)
    return {"shares": shares}


@app.delete("/shares/{share_type}/{share_id}")
def revoke_share(
    share_type: str,
    share_id: int,
    user_id: int,
    db: Session = Depends(get_db)
):
    if share_type == "file":
        share = db.query(SharedFile).filter(SharedFile.id == share_id, SharedFile.owner_id == user_id).first()
        if not share:
            raise HTTPException(status_code=404, detail="Share record not found")
        
        file = db.query(FileRecord).filter(FileRecord.id == share.file_id).first()
        item_name = file.original_name if file else "file"
        db.delete(share)
        db.commit()
        
        log_activity(
            db=db,
            user_id=user_id,
            action="REVOKE_SHARE",
            file_id=share.file_id,
            description=f"Revoked share for file {item_name}"
        )
    elif share_type == "folder":
        share = db.query(SharedFolder).filter(SharedFolder.id == share_id, SharedFolder.owner_id == user_id).first()
        if not share:
            raise HTTPException(status_code=404, detail="Share record not found")
            
        folder = db.query(FolderRecord).filter(FolderRecord.id == share.folder_id).first()
        item_name = folder.name if folder else "folder"
        db.delete(share)
        db.commit()
        
        log_activity(
            db=db,
            user_id=user_id,
            action="REVOKE_SHARE_FOLDER",
            file_id=None,
            description=f"Revoked share for folder {item_name}"
        )
    else:
        raise HTTPException(status_code=400, detail="Invalid share type")
        
    return {"status": "success", "message": "Share revoked successfully"}


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


# -----------------------------
# FOLDER MANAGEMENT
# -----------------------------
@app.post("/folders")
def create_folder(
    user_id: int,
    name: str,
    db: Session = Depends(get_db)
):
    folder = FolderRecord(
        user_id=user_id,
        name=name
    )
    db.add(folder)
    db.commit()
    db.refresh(folder)

    log_activity(
        db=db,
        user_id=user_id,
        action="CREATE_FOLDER",
        file_id=None,
        description=f"Created folder: {name}"
    )

    return {"status": "success", "folder": {"id": folder.id, "name": folder.name, "created_at": folder.created_at}}


@app.get("/folders")
def list_folders(
    user_id: int,
    db: Session = Depends(get_db)
):
    folders = db.query(FolderRecord).filter(
        FolderRecord.user_id == user_id,
        FolderRecord.is_deleted == False
    ).order_by(FolderRecord.created_at.desc()).all()

    return {
        "folders": [
            {
                "id": f.id,
                "name": f.name,
                "created_at": f.created_at
            }
            for f in folders
        ]
    }


@app.delete("/folders/{folder_id}")
def delete_folder(
    folder_id: int,
    user_id: int,
    db: Session = Depends(get_db)
):
    folder = db.query(FolderRecord).filter(
        FolderRecord.id == folder_id,
        FolderRecord.user_id == user_id,
        FolderRecord.is_deleted == False
    ).first()

    if not folder:
        raise HTTPException(status_code=404, detail="Folder not found")

    folder.is_deleted = True
    
    # Soft delete all files inside the folder too
    db.query(FileRecord).filter(
        FileRecord.folder_id == folder_id,
        FileRecord.user_id == user_id
    ).update({FileRecord.is_deleted: True})

    db.commit()

    log_activity(
        db=db,
        user_id=user_id,
        action="DELETE_FOLDER",
        file_id=None,
        description=f"Deleted folder: {folder.name}"
    )

    return {"status": "success", "message": "Folder deleted successfully"}


# -----------------------------
# NOTIFICATIONS
# -----------------------------
@app.get("/notifications")
def list_notifications(
    user_id: int,
    db: Session = Depends(get_db)
):
    notifications = db.query(Notification).filter(
        Notification.user_id == user_id
    ).order_by(Notification.created_at.desc()).all()

    return {
        "notifications": [
            {
                "id": n.id,
                "message": n.message,
                "is_read": n.is_read,
                "created_at": n.created_at
            }
            for n in notifications
        ]
    }


@app.post("/notifications/read-all")
def read_all_notifications(
    user_id: int,
    db: Session = Depends(get_db)
):
    db.query(Notification).filter(
        Notification.user_id == user_id,
        Notification.is_read == False
    ).update({Notification.is_read: True})
    db.commit()

    return {"status": "success", "message": "All notifications marked as read"}


from fastapi.staticfiles import StaticFiles
app.mount("/", StaticFiles(directory="fronthend"), name="fronthend")
 