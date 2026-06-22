from models import FileRecord #IMPORT THE FILERECORD TABLE FROM MODULE.PY

MAX_STORAGE_LIMIT = 1024 * 1024 * 1024  # 1 GB per user


def get_used_storage(db, user_id: int):# CALCULATE TOTAL STORAGE USED BY A USER
    files = db.query(FileRecord).filter(# QUERY SAY'S GIVE ME ALL FILES.
        FileRecord.user_id == user_id,# ONLY GET FILE BELONG TO PERTICULAR USER.
        FileRecord.is_deleted == False#ONLY COUNT ACTIVE FILE IF USER DELETED THE FILE DON'T COUNT IT .
    ).all()# FATCH ALL MATCHING FILES .

    total_size = sum(file.file_size for file in files)#SUM OF ALL THE FILE

    return total_size # RETURN SUM


def can_upload_file(db, user_id: int, new_file_size: int):
    used_storage = get_used_storage(db, user_id)# TELL HOW MUCH STORAGE IS USED BY USER.

    if used_storage + new_file_size > MAX_STORAGE_LIMIT:#IF ALL THE STORAGE IS USED NO NEW FILES IS ADDED
        return False

    return True


def get_storage_details(db, user_id: int): # PROVIDE COMPLETE STORAGE INFOMATION
    used_storage = get_used_storage(db, user_id)
    remaining_storage = MAX_STORAGE_LIMIT - used_storage

    return {
        "user_id": user_id,
        "used_storage_bytes": used_storage,
        "remaining_storage_bytes": remaining_storage,
        "total_storage_bytes": MAX_STORAGE_LIMIT,
        "used_storage_mb": round(used_storage / (1024 * 1024), 2),
        "remaining_storage_mb": round(remaining_storage / (1024 * 1024), 2),
        "total_storage_mb": round(MAX_STORAGE_LIMIT / (1024 * 1024), 2)
    }