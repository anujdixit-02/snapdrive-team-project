from sqlalchemy import create_engine #CREATE ENGINE MAKE THE CONNECTION BETWEEN DATABASE AND PYTHON IMPORT FROM SQLALCHEMY
from sqlalchemy.orm import sessionmaker, declarative_base # SESSIONMAKER = CREATE SESSION, SESSION CONVERSATION B/W DATABASE 

DATABASE_URL = "sqlite:///./snapdrive.db" # TELL SQLALCHEMY WHERE THE DATABASE IS 

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} # ALLOW FASTAPI TO USE DTATBASE SAFELY, ALLOW MULTI THREADS
)

SessionLocal = sessionmaker(
    # CRAETE SESSION

    autocommit=False, #DB DO NOT SAVE AUTOMATICALLY
    
    autoflush=False,# DO NOT AUTOMATICALLY PUSH CHANGES
    
    bind=engine #USE ENGIN THAT CONNECT TO FOLDER
)

Base = declarative_base()# CREATE PARENT CLASS FOR DATABASE TABLE


def get_db(): # PROVIDE DATABASE CONNECTION TO API'S
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()