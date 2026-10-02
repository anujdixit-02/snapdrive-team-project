import mimetypes

from fastapi import (
    FastAPI,
    Depends,
    UploadFile,
    File,
    HTTPException
)

from fastapi.responses import (
    FileResponse,
    RedirectResponse
)

from fastapi.staticfiles import StaticFiles

from sqlalchemy.orm import Session

from fastapi.middleware.cors import CORSMiddleware


# ============================================================
# DATABASE
# ============================================================

from database import (
    Base,
    engine,
    get_db
)


# ============================================================
# MODELS
# ============================================================

from models import (
    User,
    FileRecord,
    ActivityLog,
    SharedFile,
    FolderRecord,
    Notification,
    SharedFolder
)


# ============================================================
# SERVICES
# ============================================================

from file_service import (
    upload_file_service,
    search_files_service,
    get_file_by_id
)

from storage_service import (
    get_storage_details
)

from activity_service import (
    log_activity
)


# ============================================================
# AUTHENTICATION
# ============================================================

from auth_utils import (
    get_current_user_id
)

from auth_routes import (
    router as auth_router
)


# ============================================================
# S3
# ============================================================

from s3_service import (
    generate_presigned_download_url
)


# ============================================================
# CREATE DATABASE TABLES
# ============================================================

Base.metadata.create_all(
    bind=engine
)


# ============================================================
# FASTAPI APPLICATION
# ============================================================

app = FastAPI(
    title="SnapDrive Backend API",
    description=(
        "Cloud File Storage and Sharing Platform "
        "with Authentication, S3 Storage, "
        "File Management, Sharing, Search, "
        "Storage Tracking and Activity Logging."
    ),
    version="2.0.0"
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,

    allow_origins=["*"],

    allow_credentials=True,

    allow_methods=["*"],

    allow_headers=["*"]
)


# ============================================================
# AUTH ROUTER
# ============================================================

app.include_router(
    auth_router
)


# ============================================================
# HOME
# ============================================================

@app.get("/")
def home():

    return FileResponse(
        "fronthend/index.html"
    )


# ============================================================
# FILE UPLOAD
# ============================================================

@app.post("/files/upload")
async def upload_file(
    folder_id: int = None,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):

    uploaded_file = await upload_file_service(
        db=db,
        user_id=user_id,
        file=file,
        folder_id=folder_id
    )


    return {
        "message": "File uploaded successfully",

        "file": {
            "id": uploaded_file.id,
            "original_name": uploaded_file.original_name,
            "stored_name": uploaded_file.stored_name,
            "file_type": uploaded_file.file_type,
            "file_size": uploaded_file.file_size,
            "uploaded_at": uploaded_file.uploaded_at,
            "folder_id": uploaded_file.folder_id
        }
    }


# ============================================================
# FILE VIEW / PREVIEW
# ============================================================

@app.get("/files/{file_id}/view")
def view_file_inline(
    file_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):

    file_record = db.query(
        FileRecord
    ).filter(
        FileRecord.id == file_id
    ).first()


    if not file_record:

        raise HTTPException(
            status_code=404,
            detail="File not found."
        )


    # --------------------------------------------------------
    # ACCESS CHECK
    # --------------------------------------------------------

    is_owner = (
        file_record.user_id
        == user_id
    )


    is_shared = db.query(
        SharedFile
    ).filter(
        SharedFile.file_id == file_id,
        SharedFile.target_user_id == user_id
    ).first()


    is_folder_shared = False


    if file_record.folder_id:

        is_folder_shared = (
            db.query(
                SharedFolder
            ).filter(
                SharedFolder.folder_id
                == file_record.folder_id,

                SharedFolder.target_user_id
                == user_id
            ).first()
            is not None
        )


    if not (
        is_owner
        or is_shared
        or is_folder_shared
    ):

        raise HTTPException(
            status_code=403,
            detail="Permission denied."
        )


    if file_record.is_deleted:

        raise HTTPException(
            status_code=404,
            detail="File not found."
        )


    # --------------------------------------------------------
    # GENERATE S3 URL
    # --------------------------------------------------------

    media_type, _ = mimetypes.guess_type(
        file_record.original_name
    )


    if not media_type:

        media_type = (
            "application/octet-stream"
        )


    try:

        presigned_url = (
            generate_presigned_download_url(
                object_key=file_record.file_path,
                expiration=3600,
                inline=True
            )
        )

    except Exception as e:

        print(
            "S3 VIEW ERROR:",
            e
        )

        raise HTTPException(
            status_code=500,
            detail="Could not generate preview URL."
        )


    # --------------------------------------------------------
    # ACTIVITY
    # --------------------------------------------------------

    log_activity(
        db=db,
        user_id=user_id,
        action="VIEW",
        file_id=file_record.id,
        description=(
            f"Viewed file: "
            f"{file_record.original_name}"
        )
    )


    return RedirectResponse(
        url=presigned_url,
        status_code=307
    )


# ============================================================
# FILE DOWNLOAD
# ============================================================

@app.get("/files/{file_id}/download")
def download_file(
    file_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):

    file_record = db.query(
        FileRecord
    ).filter(
        FileRecord.id == file_id
    ).first()


    if not file_record:

        raise HTTPException(
            status_code=404,
            detail="File not found."
        )


    # --------------------------------------------------------
    # ACCESS CHECK
    # --------------------------------------------------------

    is_owner = (
        file_record.user_id
        == user_id
    )


    is_shared = db.query(
        SharedFile
    ).filter(
        SharedFile.file_id == file_id,
        SharedFile.target_user_id == user_id
    ).first()


    is_folder_shared = False


    if file_record.folder_id:

        is_folder_shared = (
            db.query(
                SharedFolder
            ).filter(
                SharedFolder.folder_id
                == file_record.folder_id,

                SharedFolder.target_user_id
                == user_id
            ).first()
            is not None
        )


    if not (
        is_owner
        or is_shared
        or is_folder_shared
    ):

        raise HTTPException(
            status_code=403,
            detail="Permission denied."
        )


    if file_record.is_deleted:

        raise HTTPException(
            status_code=404,
            detail="File not found."
        )


    # --------------------------------------------------------
    # PRESIGNED DOWNLOAD URL
    # --------------------------------------------------------

    try:

        presigned_url = (
            generate_presigned_download_url(
                object_key=file_record.file_path,
                expiration=3600,
                download_filename=file_record.original_name,
                inline=False
            )
        )

    except Exception as e:

        print(
            "S3 DOWNLOAD ERROR:",
            e
        )

        raise HTTPException(
            status_code=500,
            detail="Could not generate download URL."
        )


    # --------------------------------------------------------
    # ACTIVITY
    # --------------------------------------------------------

    log_activity(
        db=db,
        user_id=user_id,
        action="DOWNLOAD",
        file_id=file_record.id,
        description=(
            f"Downloaded file: "
            f"{file_record.original_name}"
        )
    )


    return RedirectResponse(
        url=presigned_url,
        status_code=307
    )


# ============================================================
# DELETE FILE
# ============================================================

@app.delete("/files/{file_id}")
def delete_file(
    file_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):

    file_record = get_file_by_id(
        db,
        user_id,
        file_id
    )


    # --------------------------------------------------------
    # SOFT DELETE
    # --------------------------------------------------------

    file_record.is_deleted = True

    db.commit()


    log_activity(
        db=db,
        user_id=user_id,
        action="DELETE",
        file_id=file_record.id,
        description=(
            f"Deleted file: "
            f"{file_record.original_name}"
        )
    )


    return {
        "status": "success",
        "message": "File deleted successfully.",
        "file_id": file_id
    }


# ============================================================
# LIST FILES
# ============================================================

@app.get("/files")
def list_files(
    folder_id: str = "all",
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):

    query = db.query(
        FileRecord
    ).filter(
        FileRecord.user_id == user_id,
        FileRecord.is_deleted == False
    )


    if folder_id == "root":

        query = query.filter(
            FileRecord.folder_id == None
        )

    elif folder_id != "all":

        try:

            folder_id_int = int(
                folder_id
            )

            query = query.filter(
                FileRecord.folder_id
                == folder_id_int
            )

        except ValueError:

            pass


    files = query.order_by(
        FileRecord.uploaded_at.desc()
    ).all()


    return {
        "files": [
            {
                "id": f.id,
                "original_name": f.original_name,
                "file_type": f.file_type,
                "file_size": f.file_size,
                "uploaded_at": f.uploaded_at,
                "folder_id": f.folder_id
            }

            for f in files
        ]
    }


# ============================================================
# CREATE FOLDER
# ============================================================

@app.post("/folders")
def create_folder(
    name: str,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):

    name = name.strip()


    if not name:

        raise HTTPException(
            status_code=400,
            detail="Folder name is required."
        )


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
        description=(
            f"Created folder: {name}"
        )
    )


    return {
        "status": "success",

        "folder": {
            "id": folder.id,
            "name": folder.name,
            "created_at": folder.created_at
        }
    }


# ============================================================
# LIST FOLDERS
# ============================================================

@app.get("/folders")
def list_folders(
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):

    folders = db.query(
        FolderRecord
    ).filter(
        FolderRecord.user_id == user_id,
        FolderRecord.is_deleted == False
    ).order_by(
        FolderRecord.created_at.desc()
    ).all()


    return {
        "folders": [
            {
                "id": folder.id,
                "name": folder.name,
                "created_at": folder.created_at
            }

            for folder in folders
        ]
    }


# ============================================================
# GET FOLDER CONTENT
# ============================================================

@app.get("/folders/{folder_id}")
def get_folder_contents(
    folder_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):

    folder = db.query(
        FolderRecord
    ).filter(
        FolderRecord.id == folder_id,
        FolderRecord.user_id == user_id,
        FolderRecord.is_deleted == False
    ).first()


    if not folder:

        raise HTTPException(
            status_code=404,
            detail="Folder not found."
        )


    files = db.query(
        FileRecord
    ).filter(
        FileRecord.folder_id == folder_id,
        FileRecord.is_deleted == False
    ).order_by(
        FileRecord.uploaded_at.desc()
    ).all()


    return {
        "folder": {
            "id": folder.id,
            "name": folder.name,
            "created_at": folder.created_at
        },

        "files": [
            {
                "id": f.id,
                "original_name": f.original_name,
                "file_type": f.file_type,
                "file_size": f.file_size,
                "uploaded_at": f.uploaded_at
            }

            for f in files
        ]
    }


# ============================================================
# DELETE FOLDER
# ============================================================

@app.delete("/folders/{folder_id}")
def delete_folder(
    folder_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):

    folder = db.query(
        FolderRecord
    ).filter(
        FolderRecord.id == folder_id,
        FolderRecord.user_id == user_id,
        FolderRecord.is_deleted == False
    ).first()


    if not folder:

        raise HTTPException(
            status_code=404,
            detail="Folder not found."
        )


    folder.is_deleted = True


    db.query(
        FileRecord
    ).filter(
        FileRecord.folder_id == folder_id,
        FileRecord.user_id == user_id
    ).update({
        FileRecord.is_deleted: True
    })


    db.commit()


    log_activity(
        db=db,
        user_id=user_id,
        action="DELETE_FOLDER",
        file_id=None,
        description=(
            f"Deleted folder: "
            f"{folder.name}"
        )
    )


    return {
        "status": "success",
        "message": "Folder deleted successfully."
    }


# ============================================================
# SHARE FILE
# ============================================================

@app.post("/files/{file_id}/share")
def share_file(
    file_id: int,
    target_user_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):

    file_record = get_file_by_id(
        db,
        user_id,
        file_id
    )


    if target_user_id == user_id:

        raise HTTPException(
            status_code=400,
            detail="You cannot share a file with yourself."
        )


    target_user = db.query(
        User
    ).filter(
        User.id == target_user_id
    ).first()


    if not target_user:

        raise HTTPException(
            status_code=404,
            detail="Target user not found."
        )


    existing = db.query(
        SharedFile
    ).filter(
        SharedFile.file_id == file_id,
        SharedFile.owner_id == user_id,
        SharedFile.target_user_id == target_user_id
    ).first()


    if existing:

        raise HTTPException(
            status_code=400,
            detail="File already shared with this user."
        )


    shared_record = SharedFile(
        file_id=file_id,
        owner_id=user_id,
        target_user_id=target_user_id
    )


    db.add(shared_record)


    sender = db.query(
        User
    ).filter(
        User.id == user_id
    ).first()


    sender_name = (
        sender.username
        if sender
        else "Someone"
    )


    notification = Notification(
        user_id=target_user_id,
        message=(
            f"@{sender_name} shared a file "
            f"with you: "
            f"{file_record.original_name}"
        )
    )


    db.add(notification)

    db.commit()


    log_activity(
        db=db,
        user_id=user_id,
        action="SHARE",
        file_id=file_id,
        description=(
            f"Shared "
            f"{file_record.original_name} "
            f"with "
            f"{target_user.username}"
        )
    )


    return {
        "status": "success",
        "message": (
            f"Shared with "
            f"{target_user.username}"
        )
    }


# ============================================================
# SHARE FOLDER
# ============================================================

@app.post("/folders/{folder_id}/share")
def share_folder(
    folder_id: int,
    target_user_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):

    folder = db.query(
        FolderRecord
    ).filter(
        FolderRecord.id == folder_id,
        FolderRecord.user_id == user_id,
        FolderRecord.is_deleted == False
    ).first()


    if not folder:

        raise HTTPException(
            status_code=404,
            detail="Folder not found."
        )


    if target_user_id == user_id:

        raise HTTPException(
            status_code=400,
            detail="You cannot share a folder with yourself."
        )


    target_user = db.query(
        User
    ).filter(
        User.id == target_user_id
    ).first()


    if not target_user:

        raise HTTPException(
            status_code=404,
            detail="Target user not found."
        )


    existing = db.query(
        SharedFolder
    ).filter(
        SharedFolder.folder_id == folder_id,
        SharedFolder.owner_id == user_id,
        SharedFolder.target_user_id == target_user_id
    ).first()


    if existing:

        raise HTTPException(
            status_code=400,
            detail="Folder already shared with this user."
        )


    shared_record = SharedFolder(
        folder_id=folder_id,
        owner_id=user_id,
        target_user_id=target_user_id
    )


    db.add(shared_record)


    sender = db.query(
        User
    ).filter(
        User.id == user_id
    ).first()


    sender_name = (
        sender.username
        if sender
        else "Someone"
    )


    notification = Notification(
        user_id=target_user_id,
        message=(
            f"@{sender_name} shared a folder "
            f"with you: {folder.name}"
        )
    )


    db.add(notification)

    db.commit()


    log_activity(
        db=db,
        user_id=user_id,
        action="SHARE_FOLDER",
        file_id=None,
        description=(
            f"Shared folder "
            f"{folder.name} "
            f"with "
            f"{target_user.username}"
        )
    )


    return {
        "status": "success",
        "message": (
            f"Shared folder with "
            f"{target_user.username}"
        )
    }


# ============================================================
# SHARED FILES
# ============================================================

@app.get("/files/shared-with-me")
def list_shared_files(
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):

    shared_entries = db.query(
        SharedFile
    ).filter(
        SharedFile.target_user_id == user_id
    ).all()


    results = []

    seen_file_ids = set()


    # --------------------------------------------------------
    # EXPLICIT SHARES
    # --------------------------------------------------------

    for entry in shared_entries:

        file = db.query(
            FileRecord
        ).filter(
            FileRecord.id == entry.file_id
        ).first()


        owner = db.query(
            User
        ).filter(
            User.id == entry.owner_id
        ).first()


        if file and not file.is_deleted:

            seen_file_ids.add(
                file.id
            )


            results.append({
                "id": file.id,
                "original_name": file.original_name,
                "file_type": file.file_type,
                "file_size": file.file_size,
                "shared_at": entry.shared_at,
                "owner_name": (
                    owner.username
                    if owner
                    else "Unknown"
                ),
                "folder_id": file.folder_id
            })


    # --------------------------------------------------------
    # SHARED FOLDERS
    # --------------------------------------------------------

    shared_folders = db.query(
        SharedFolder
    ).filter(
        SharedFolder.target_user_id == user_id
    ).all()


    for shared_folder in shared_folders:

        folder_files = db.query(
            FileRecord
        ).filter(
            FileRecord.folder_id
            == shared_folder.folder_id,

            FileRecord.is_deleted == False
        ).all()


        owner = db.query(
            User
        ).filter(
            User.id
            == shared_folder.owner_id
        ).first()


        for file in folder_files:

            if file.id in seen_file_ids:
                continue


            seen_file_ids.add(
                file.id
            )


            results.append({
                "id": file.id,
                "original_name": file.original_name,
                "file_type": file.file_type,
                "file_size": file.file_size,
                "shared_at": shared_folder.shared_at,
                "owner_name": (
                    owner.username
                    if owner
                    else "Unknown"
                ),
                "folder_id": file.folder_id
            })


    return {
        "shared_files": results
    }


# ============================================================
# SHARED FOLDERS
# ============================================================

@app.get("/folders/shared-with-me")
def list_shared_folders(
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):

    shared_entries = db.query(
        SharedFolder
    ).filter(
        SharedFolder.target_user_id == user_id
    ).all()


    results = []


    for entry in shared_entries:

        folder = db.query(
            FolderRecord
        ).filter(
            FolderRecord.id == entry.folder_id
        ).first()


        owner = db.query(
            User
        ).filter(
            User.id == entry.owner_id
        ).first()


        if folder and not folder.is_deleted:

            results.append({
                "id": folder.id,
                "name": folder.name,
                "shared_at": entry.shared_at,
                "owner_name": (
                    owner.username
                    if owner
                    else "Unknown"
                )
            })


    return {
        "shared_folders": results
    }


# ============================================================
# SHARED BY ME
# ============================================================

@app.get("/files/shared-by-me")
def list_shared_by_me(
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):

    shares = []


    # --------------------------------------------------------
    # SHARED FILES
    # --------------------------------------------------------

    shared_files = db.query(
        SharedFile
    ).filter(
        SharedFile.owner_id == user_id
    ).all()


    for share in shared_files:

        file = db.query(
            FileRecord
        ).filter(
            FileRecord.id == share.file_id
        ).first()


        target = db.query(
            User
        ).filter(
            User.id == share.target_user_id
        ).first()


        if file and not file.is_deleted:

            shares.append({
                "share_id": share.id,
                "item_id": file.id,
                "name": file.original_name,
                "type": "file",
                "shared_with": (
                    target.username
                    if target
                    else "Unknown"
                ),
                "shared_with_email": (
                    target.email
                    if target
                    else ""
                ),
                "shared_at": share.shared_at
            })


    # --------------------------------------------------------
    # SHARED FOLDERS
    # --------------------------------------------------------

    shared_folders = db.query(
        SharedFolder
    ).filter(
        SharedFolder.owner_id == user_id
    ).all()


    for share in shared_folders:

        folder = db.query(
            FolderRecord
        ).filter(
            FolderRecord.id == share.folder_id
        ).first()


        target = db.query(
            User
        ).filter(
            User.id == share.target_user_id
        ).first()


        if folder and not folder.is_deleted:

            shares.append({
                "share_id": share.id,
                "item_id": folder.id,
                "name": folder.name,
                "type": "folder",
                "shared_with": (
                    target.username
                    if target
                    else "Unknown"
                ),
                "shared_with_email": (
                    target.email
                    if target
                    else ""
                ),
                "shared_at": share.shared_at
            })


    shares.sort(
        key=lambda item: (
            item["shared_at"]
            or ""
        ),
        reverse=True
    )


    return {
        "shares": shares
    }


# ============================================================
# REVOKE SHARE
# ============================================================

@app.delete("/shares/{share_type}/{share_id}")
def revoke_share(
    share_type: str,
    share_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):

    if share_type == "file":

        share = db.query(
            SharedFile
        ).filter(
            SharedFile.id == share_id,
            SharedFile.owner_id == user_id
        ).first()


        if not share:

            raise HTTPException(
                status_code=404,
                detail="Share record not found."
            )


        file_id = share.file_id


        file = db.query(
            FileRecord
        ).filter(
            FileRecord.id == file_id
        ).first()


        item_name = (
            file.original_name
            if file
            else "file"
        )


        db.delete(
            share
        )

        db.commit()


        log_activity(
            db=db,
            user_id=user_id,
            action="REVOKE_SHARE",
            file_id=file_id,
            description=(
                f"Revoked share for "
                f"file {item_name}"
            )
        )


    elif share_type == "folder":

        share = db.query(
            SharedFolder
        ).filter(
            SharedFolder.id == share_id,
            SharedFolder.owner_id == user_id
        ).first()


        if not share:

            raise HTTPException(
                status_code=404,
                detail="Share record not found."
            )


        folder_id = share.folder_id


        folder = db.query(
            FolderRecord
        ).filter(
            FolderRecord.id == folder_id
        ).first()


        item_name = (
            folder.name
            if folder
            else "folder"
        )


        db.delete(
            share
        )

        db.commit()


        log_activity(
            db=db,
            user_id=user_id,
            action="REVOKE_SHARE_FOLDER",
            file_id=None,
            description=(
                f"Revoked share for "
                f"folder {item_name}"
            )
        )


    else:

        raise HTTPException(
            status_code=400,
            detail="Invalid share type."
        )


    return {
        "status": "success",
        "message": "Share revoked successfully."
    }


# ============================================================
# SEARCH
# ============================================================

@app.get("/search")
def search_files(
    query: str = "",
    folder_id: str = "all",
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):

    files = search_files_service(
        db,
        user_id,
        query,
        folder_id
    )


    folders = []


    # --------------------------------------------------------
    # SEARCH OWNED FOLDERS
    # --------------------------------------------------------

    if query:

        folders = db.query(
            FolderRecord
        ).filter(
            FolderRecord.user_id == user_id,
            FolderRecord.name.ilike(
                f"%{query}%"
            ),
            FolderRecord.is_deleted == False
        ).all()


    # --------------------------------------------------------
    # SEARCH SHARED CONTENT
    # --------------------------------------------------------

    if query:

        shared_file_entries = db.query(
            SharedFile
        ).filter(
            SharedFile.target_user_id
            == user_id
        ).all()


        shared_file_ids = [
            entry.file_id
            for entry in shared_file_entries
        ]


        shared_folder_entries = db.query(
            SharedFolder
        ).filter(
            SharedFolder.target_user_id
            == user_id
        ).all()


        shared_folder_ids = [
            entry.folder_id
            for entry in shared_folder_entries
        ]


        # Shared files
        if shared_file_ids:

            matching_shared_files = db.query(
                FileRecord
            ).filter(
                FileRecord.id.in_(
                    shared_file_ids
                ),
                FileRecord.original_name.ilike(
                    f"%{query}%"
                ),
                FileRecord.is_deleted == False
            ).all()

        else:

            matching_shared_files = []


        # Files in shared folders
        if shared_folder_ids:

            matching_folder_files = db.query(
                FileRecord
            ).filter(
                FileRecord.folder_id.in_(
                    shared_folder_ids
                ),
                FileRecord.original_name.ilike(
                    f"%{query}%"
                ),
                FileRecord.is_deleted == False
            ).all()

        else:

            matching_folder_files = []


        # Shared folders
        if shared_folder_ids:

            matching_shared_folders = db.query(
                FolderRecord
            ).filter(
                FolderRecord.id.in_(
                    shared_folder_ids
                ),
                FolderRecord.name.ilike(
                    f"%{query}%"
                ),
                FolderRecord.is_deleted == False
            ).all()

        else:

            matching_shared_folders = []


        # Merge folders
        seen_folder_ids = {
            folder.id
            for folder in folders
        }


        for folder in matching_shared_folders:

            if folder.id not in seen_folder_ids:

                seen_folder_ids.add(
                    folder.id
                )

                folders.append(
                    folder
                )


        # Merge files
        seen_file_ids = {
            file.id
            for file in files
        }


        for file in (
            matching_shared_files
            + matching_folder_files
        ):

            if file.id not in seen_file_ids:

                seen_file_ids.add(
                    file.id
                )

                files.append(
                    file
                )


    return {
        "query": query,

        "total_results": (
            len(files)
            + len(folders)
        ),

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
                "id": folder.id,
                "user_id": folder.user_id,
                "name": folder.name,
                "created_at": folder.created_at
            }

            for folder in folders
        ]
    }


# ============================================================
# USER SEARCH
# ============================================================

@app.get("/users/search")
def search_users(
    query: str,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):

    query = query.strip()


    if not query:

        return {
            "users": []
        }


    users = db.query(
        User
    ).filter(
        (
            User.username.ilike(
                f"%{query}%"
            )
            |
            User.email.ilike(
                f"%{query}%"
            )
        ),

        User.id != user_id

    ).limit(10).all()


    return {
        "users": [
            {
                "id": user.id,
                "username": user.username,
                "email": user.email
            }

            for user in users
        ]
    }


# ============================================================
# STORAGE USAGE
# ============================================================

@app.get("/storage/usage")
def storage_usage(
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):

    return get_storage_details(
        db,
        user_id
    )


# ============================================================
# ACTIVITY LOGS
# ============================================================

@app.get("/activity/logs")
def activity_logs(
    limit: int = 50,
    skip: int = 0,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):

    if limit < 1:
        limit = 1

    if limit > 100:
        limit = 100

    if skip < 0:
        skip = 0


    logs = db.query(
        ActivityLog
    ).filter(
        ActivityLog.user_id == user_id
    ).order_by(
        ActivityLog.created_at.desc()
    ).offset(
        skip
    ).limit(
        limit
    ).all()


    total = db.query(
        ActivityLog
    ).filter(
        ActivityLog.user_id == user_id
    ).count()


    return {
        "user_id": user_id,

        "total": total,

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


# ============================================================
# NOTIFICATIONS
# ============================================================

@app.get("/notifications")
def list_notifications(
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):

    notifications = db.query(
        Notification
    ).filter(
        Notification.user_id == user_id
    ).order_by(
        Notification.created_at.desc()
    ).all()


    unread_count = db.query(
        Notification
    ).filter(
        Notification.user_id == user_id,
        Notification.is_read == False
    ).count()


    return {
        "unread_count": unread_count,

        "notifications": [
            {
                "id": notification.id,
                "message": notification.message,
                "is_read": notification.is_read,
                "created_at": notification.created_at
            }

            for notification in notifications
        ]
    }


# ============================================================
# MARK ALL NOTIFICATIONS READ
# ============================================================

@app.post("/notifications/read-all")
def read_all_notifications(
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):

    db.query(
        Notification
    ).filter(
        Notification.user_id == user_id,
        Notification.is_read == False
    ).update({
        Notification.is_read: True
    })


    db.commit()


    return {
        "status": "success",
        "message": (
            "All notifications marked as read."
        )
    }

@app.get("/storage")
def get_storage(
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    return get_storage_details(db, user_id)
# ============================================================
# MARK SINGLE NOTIFICATION READ
# ============================================================

@app.put(
    "/notifications/{notification_id}/read"
)
def mark_notification_read(
    notification_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):

    notification = db.query(
        Notification
    ).filter(
        Notification.id == notification_id,
        Notification.user_id == user_id
    ).first()


    if not notification:

        raise HTTPException(
            status_code=404,
            detail="Notification not found."
        )


    notification.is_read = True

    db.commit()


    return {
        "status": "success",
        "message": (
            "Notification marked as read."
        )
    }


# ============================================================
# STATIC FRONTEND
#
# THIS MUST BE LAST
# ============================================================

app.mount(
    "/",
    StaticFiles(
        directory="fronthend",
        html=True
    ),
    name="fronthend"
)