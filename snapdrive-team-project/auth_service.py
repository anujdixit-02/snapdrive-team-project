import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from models import User


# ============================================================
# PASSWORD HASHING
# ============================================================

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)


# ============================================================
# PASSWORD FUNCTIONS
# ============================================================

def hash_password(
    password: str
) -> str:

    return pwd_context.hash(
        password
    )


def verify_password(
    plain_password: str,
    hashed_password: str
) -> bool:

    return pwd_context.verify(
        plain_password,
        hashed_password
    )


# ============================================================
# VERIFICATION TOKEN
# ============================================================

VERIFICATION_TOKEN_EXPIRE_MINUTES = 30


def create_verification_token():

    raw_token = secrets.token_urlsafe(
        32
    )

    token_hash = hashlib.sha256(
        raw_token.encode()
    ).hexdigest()

    expires_at = (
        datetime.now(timezone.utc)
        + timedelta(
            minutes=VERIFICATION_TOKEN_EXPIRE_MINUTES
        )
    )

    return (
        raw_token,
        token_hash,
        expires_at
    )


# ============================================================
# CREATE USER
# ============================================================

def create_user(
    db: Session,
    username: str,
    email: str,
    password: str
):

    username = username.strip()
    email = email.strip().lower()


    # --------------------------------------------------------
    # CHECK USERNAME
    # --------------------------------------------------------

    existing_username = db.query(
        User
    ).filter(
        User.username == username
    ).first()


    if existing_username:

        raise HTTPException(
            status_code=400,
            detail="Username already exists."
        )


    # --------------------------------------------------------
    # CHECK EMAIL
    # --------------------------------------------------------

    existing_email = db.query(
        User
    ).filter(
        User.email == email
    ).first()


    if existing_email:

        raise HTTPException(
            status_code=400,
            detail="Email already registered."
        )


    # --------------------------------------------------------
    # PASSWORD VALIDATION
    # --------------------------------------------------------

    if len(password) < 6:

        raise HTTPException(
            status_code=400,
            detail="Password must contain at least 6 characters."
        )


    # --------------------------------------------------------
    # VERIFICATION TOKEN
    # --------------------------------------------------------

    (
        raw_token,
        token_hash,
        expires_at
    ) = create_verification_token()


    # --------------------------------------------------------
    # CREATE USER
    # --------------------------------------------------------

    new_user = User(
        username=username,
        email=email,
        hashed_password=hash_password(
            password
        ),
        is_verified=False,
        verification_token_hash=token_hash,
        verification_token_expires=expires_at
    )


    db.add(new_user)
    db.commit()
    db.refresh(new_user)


    return new_user, raw_token


# ============================================================
# AUTHENTICATE USER
# ============================================================

def authenticate_user(
    db: Session,
    email: str,
    password: str
):

    email = email.strip().lower()


    user = db.query(
        User
    ).filter(
        User.email == email
    ).first()


    if not user:

        return None


    if not verify_password(
        password,
        user.hashed_password
    ):

        return None


    return user


# ============================================================
# VERIFY EMAIL TOKEN
# ============================================================

def verify_email_token(
    db: Session,
    token: str
):

    token_hash = hashlib.sha256(
        token.encode()
    ).hexdigest()


    user = db.query(
        User
    ).filter(
        User.verification_token_hash
        == token_hash
    ).first()


    if not user:

        raise HTTPException(
            status_code=400,
            detail="Invalid verification token."
        )


    if user.verification_token_expires:

        expires_at = user.verification_token_expires

        if expires_at.tzinfo is None:

            expires_at = expires_at.replace(
                tzinfo=timezone.utc
            )


        if (
            datetime.now(timezone.utc)
            > expires_at
        ):

            raise HTTPException(
                status_code=400,
                detail="Verification token has expired."
            )


    user.is_verified = True

    user.verification_token_hash = None

    user.verification_token_expires = None


    db.commit()
    db.refresh(user)


    return user


# ============================================================
# RESEND VERIFICATION TOKEN
# ============================================================

def generate_new_verification_token(
    db: Session,
    user: User
):

    (
        raw_token,
        token_hash,
        expires_at
    ) = create_verification_token()


    user.verification_token_hash = token_hash

    user.verification_token_expires = expires_at


    db.commit()
    db.refresh(user)


    return raw_token