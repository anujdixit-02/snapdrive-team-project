from models import FileRecord


# ============================================================
# STORAGE LIMIT
# ============================================================

MAX_STORAGE_LIMIT = 1024 * 1024 * 1024  # 1 GB per user


# ============================================================
# GET USED STORAGE
# ============================================================

def get_used_storage(db, user_id: int):
    """
    Calculate total storage currently used by a user.

    Deleted files are excluded.
    """

    files = db.query(FileRecord).filter(
        FileRecord.user_id == user_id,
        FileRecord.is_deleted == False
    ).all()

    total_size = sum(
        file.file_size for file in files
    )

    return total_size


# ============================================================
# CHECK WHETHER USER CAN UPLOAD
# ============================================================

def can_upload_file(
    db,
    user_id: int,
    new_file_size: int
):
    """
    Check whether a new file can be uploaded
    without exceeding the 1 GB user limit.
    """

    used_storage = get_used_storage(
        db,
        user_id
    )

    if used_storage + new_file_size > MAX_STORAGE_LIMIT:
        return False

    return True


# ============================================================
# GET STORAGE DETAILS
# ============================================================

def get_storage_details(
    db,
    user_id: int
):
    """
    Return complete storage information for a user.
    """

    used_storage = get_used_storage(
        db,
        user_id
    )

    remaining_storage = (
        MAX_STORAGE_LIMIT - used_storage
    )

    return {
        "user_id": user_id,

        "used_storage_bytes": used_storage,
        "remaining_storage_bytes": remaining_storage,
        "total_storage_bytes": MAX_STORAGE_LIMIT,

        "used_storage_mb": round(
            used_storage / (1024 * 1024),
            2
        ),

        "remaining_storage_mb": round(
            remaining_storage / (1024 * 1024),
            2
        ),

        "total_storage_mb": round(
            MAX_STORAGE_LIMIT / (1024 * 1024),
            2
        )
    }