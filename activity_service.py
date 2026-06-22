# This module provides services related to logging user activities in the application.

#IMPORT THE ACTIVITYlOG FROM MODELS TO LOG THE USER ACTIVITIES IN THE DATABASE
from models import ActivityLog

#DB/SESSION USE TO TALK TO DATABASE = DB,
#  USER_ID = ID OF THE USER, ACTION = WHAT THE USER DID,
#  FILE_ID = WHICH FILE WAS AFFECTED (IF ANY),
#  DESCRIPTION = ADDITIONAL DETAILS ABOUT THE ACTION
def log_activity(db, user_id: int, action: str, file_id: int | None, description: str):
    log = ActivityLog(
        user_id=user_id,
        action=action,
        file_id=file_id,
        description=description
    )
# DB.ADD() = ADD THE LOG ENTRY TO THE DATABASE, 
# DB.COMMIT() = SAVE THE CHANGES TO THE DATABASE, 
# DB.REFRESH() = UPDATE THE LOG OBJECT WITH THE NEWLY ASSIGNED ID AND OTHER GENERATED FIELDS 
    db.add(log)
    db.commit()
    db.refresh(log)

    return log