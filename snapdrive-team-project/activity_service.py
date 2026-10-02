from models import ActivityLog


def log_activity(
    db,
    user_id: int,
    action: str,
    file_id: int | None,
    description: str
):
    """
    Create and store an activity log.
    """

    log = ActivityLog(
        user_id=user_id,
        action=action,
        file_id=file_id,
        description=description
    )

    db.add(log)
    db.commit()
    db.refresh(log)

    return log