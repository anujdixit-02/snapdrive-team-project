from sqlalchemy.orm import Session

from models import User
from auth_utils import hash_password, verify_password


# -----------------------------
# GET USER BY EMAIL
# -----------------------------
def get_user_by_email(db: Session, email: str):
    """
    Returns a user if the email exists.
    """

    return (
        db.query(User)
        .filter(User.email == email)
        .first()
    )


# -----------------------------
# CREATE NEW USER
# -----------------------------
def create_user(
    db: Session,
    username: str,
    email: str,
    password: str
):
    """
    Creates a new user after hashing the password.
    """

    # Check if email already exists
    existing_user = get_user_by_email(db, email)

    if existing_user:
        return None

    hashed_pw = hash_password(password)

    new_user = User(
        username=username,
        email=email,
        hashed_password=hashed_pw
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user


# -----------------------------
# AUTHENTICATE USER
# -----------------------------
def authenticate_user(
    db: Session,
    email: str,
    password: str
):
    """
    Verify email and password.
    """

    user = get_user_by_email(db, email)

    if not user:
        return None

    if not verify_password(
        password,
        user.hashed_password
    ):
        return None

    return user