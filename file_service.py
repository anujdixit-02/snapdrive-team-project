import os
import uuid
from fastapi import UploadFile, HTTPException
from models import FileRecord
from activity_service import log_activity
from storage_service import can_upload_file

UPLOAD_FOLDER = "uploads"

ALLOWED_EXTENSIONS = {
    "pdf", "doc", "docx", "txt", "jpg", "jpeg", "png", "mp4", "zip"
}

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB per file


def get_file_extension(filename: str):
    if "." not in filename:
        return ""

    return filename.rsplit(".", 1)[1].lower()


def validate_file(filename: str, file_size: int):
    extension = get_file_extension(filename)

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"File type .{extension} is not allowed"
        )

    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail="File size exceeds 50 MB limit"
        )


def generate_unique_filename(original_filename: str):
    extension = get_file_extension(original_filename)
    unique_id = str(uuid.uuid4())

    return f"{unique_id}.{extension}"


async def upload_file_service(db, user_id: int, file: UploadFile):
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

    file_content = await file.read()
    file_size = len(file_content)

    validate_file(file.filename, file_size)

    if not can_upload_file(db, user_id, file_size):
        raise HTTPException(
            status_code=400,
            detail="Storage limit exceeded"
        )

    stored_name = generate_unique_filename(file.filename)
    file_path = os.path.join(UPLOAD_FOLDER, stored_name)

    with open(file_path, "wb") as f:
        f.write(file_content)

    file_record = FileRecord(
        user_id=user_id,
        original_name=file.filename,
        stored_name=stored_name,
        file_path=file_path,
        file_type=get_file_extension(file.filename),
        file_size=file_size
    )

    db.add(file_record)
    db.commit()
    db.refresh(file_record)

    log_activity(
        db=db,
        user_id=user_id,
        action="UPLOAD",
        file_id=file_record.id,
        description=f"Uploaded file: {file.filename}"
    )

    return file_record


def search_files_service(db, user_id: int, query: str):
    files = db.query(FileRecord).filter(
        FileRecord.user_id == user_id,
        FileRecord.is_deleted == False,
        FileRecord.original_name.ilike(f"%{query}%")
    ).all()

    return files


def get_file_by_id(db, user_id: int, file_id: int):
    file_record = db.query(FileRecord).filter(
        FileRecord.id == file_id,
        FileRecord.user_id == user_id,
        FileRecord.is_deleted == False
    ).first()

    if not file_record:
        raise HTTPException(
            status_code=404,
            detail="File not found"
        )

    if not os.path.exists(file_record.file_path):
        raise HTTPException(
            status_code=404,
            detail="File missing from storage"
        )

    return file_record