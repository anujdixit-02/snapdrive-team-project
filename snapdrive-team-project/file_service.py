import uuid

from fastapi import UploadFile, HTTPException

from models import FileRecord
from activity_service import log_activity
from storage_service import can_upload_file

from s3_service import (
    upload_file_to_s3,
    file_exists_in_s3
)


# ============================================================
# FILE CONFIGURATION
# ============================================================

ALLOWED_EXTENSIONS = {
    "pdf",
    "doc",
    "docx",
    "txt",
    "jpg",
    "jpeg",
    "png",
    "mp4",
    "zip"
}


MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB


# ============================================================
# FILE EXTENSION
# ============================================================

def get_file_extension(filename: str) -> str:

    if not filename:
        return ""

    if "." not in filename:
        return ""

    return filename.rsplit(".", 1)[1].lower()


# ============================================================
# FILE VALIDATION
# ============================================================

def validate_file(
    filename: str,
    file_size: int
):
    extension = get_file_extension(filename)

    if extension not in ALLOWED_EXTENSIONS:

        raise HTTPException(
            status_code=400,
            detail=(
                f"File type .{extension} is not allowed. "
                f"Allowed types: "
                f"{', '.join(sorted(ALLOWED_EXTENSIONS))}"
            )
        )

    if file_size <= 0:

        raise HTTPException(
            status_code=400,
            detail="Cannot upload an empty file."
        )

    if file_size > MAX_FILE_SIZE:

        raise HTTPException(
            status_code=400,
            detail="File size exceeds 50 MB limit."
        )


# ============================================================
# UNIQUE FILE NAME
# ============================================================

def generate_unique_filename(
    original_filename: str
) -> str:

    extension = get_file_extension(
        original_filename
    )

    unique_id = str(uuid.uuid4())

    return f"{unique_id}.{extension}"


# ============================================================
# S3 OBJECT KEY
# ============================================================

def generate_s3_object_key(
    user_id: int,
    stored_name: str
) -> str:

    return f"snapdrive/{user_id}/{stored_name}"


# ============================================================
# UPLOAD FILE
# ============================================================

async def upload_file_service(
    db,
    user_id: int,
    file: UploadFile,
    folder_id: int = None
):

    if not file.filename:

        raise HTTPException(
            status_code=400,
            detail="No file selected."
        )


    # --------------------------------------------------------
    # READ FILE
    # --------------------------------------------------------

    file_content = await file.read()

    file_size = len(file_content)


    # --------------------------------------------------------
    # VALIDATE
    # --------------------------------------------------------

    validate_file(
        file.filename,
        file_size
    )


    # --------------------------------------------------------
    # CHECK STORAGE QUOTA
    # --------------------------------------------------------

    if not can_upload_file(
        db,
        user_id,
        file_size
    ):

        raise HTTPException(
            status_code=400,
            detail="Storage limit exceeded."
        )


    # --------------------------------------------------------
    # GENERATE UNIQUE NAME
    # --------------------------------------------------------

    stored_name = generate_unique_filename(
        file.filename
    )


    # --------------------------------------------------------
    # GENERATE S3 KEY
    # --------------------------------------------------------

    object_key = generate_s3_object_key(
        user_id,
        stored_name
    )


    # --------------------------------------------------------
    # UPLOAD TO S3
    # --------------------------------------------------------

    try:

        upload_file_to_s3(
            file_content=file_content,
            object_key=object_key,
            content_type=file.content_type
        )

    except Exception as e:

        print(
            "S3 upload failed:",
            e
        )

        raise HTTPException(
            status_code=500,
            detail="Failed to upload file to cloud storage."
        )


    # --------------------------------------------------------
    # SAVE METADATA IN DATABASE
    # --------------------------------------------------------

    file_record = FileRecord(
        user_id=user_id,
        original_name=file.filename,
        stored_name=stored_name,
        file_path=object_key,
        file_type=get_file_extension(
            file.filename
        ),
        file_size=file_size,
        folder_id=folder_id
    )


    try:

        db.add(file_record)

        db.commit()

        db.refresh(file_record)

    except Exception as e:

        db.rollback()

        print(
            "Database save failed after S3 upload:",
            e
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "File uploaded to storage but "
                "metadata could not be saved."
            )
        )


    # --------------------------------------------------------
    # ACTIVITY LOG
    # --------------------------------------------------------

    log_activity(
        db=db,
        user_id=user_id,
        action="UPLOAD",
        file_id=file_record.id,
        description=(
            f"Uploaded file: "
            f"{file.filename}"
        )
    )


    return file_record


# ============================================================
# SEARCH FILES
# ============================================================

def search_files_service(
    db,
    user_id: int,
    query: str,
    folder_id: str = "all"
):

    q = db.query(FileRecord).filter(
        FileRecord.user_id == user_id,
        FileRecord.is_deleted == False
    )


    # --------------------------------------------------------
    # SEARCH BY NAME
    # --------------------------------------------------------

    if query:

        q = q.filter(
            FileRecord.original_name.ilike(
                f"%{query}%"
            )
        )


    # --------------------------------------------------------
    # FOLDER FILTER
    # --------------------------------------------------------

    if folder_id == "root":

        q = q.filter(
            FileRecord.folder_id == None
        )

    elif folder_id != "all":

        try:

            folder_id_int = int(
                folder_id
            )

            q = q.filter(
                FileRecord.folder_id
                == folder_id_int
            )

        except ValueError:

            pass


    return q.order_by(
        FileRecord.uploaded_at.desc()
    ).all()


# ============================================================
# GET FILE
# ============================================================

def get_file_by_id(
    db,
    user_id: int,
    file_id: int
):

    file_record = db.query(
        FileRecord
    ).filter(
        FileRecord.id == file_id,
        FileRecord.user_id == user_id,
        FileRecord.is_deleted == False
    ).first()


    if not file_record:

        raise HTTPException(
            status_code=404,
            detail="File not found."
        )


    # --------------------------------------------------------
    # VERIFY S3 OBJECT
    # --------------------------------------------------------

    try:

        exists = file_exists_in_s3(
            file_record.file_path
        )

    except Exception as e:

        print(
            "S3 existence check failed:",
            e
        )

        raise HTTPException(
            status_code=500,
            detail="Could not verify file storage."
        )


    if not exists:

        raise HTTPException(
            status_code=404,
            detail="File is missing from cloud storage."
        )


    return file_record