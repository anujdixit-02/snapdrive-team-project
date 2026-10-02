from datetime import timedelta
import os

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status
)

from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from database import get_db
from models import User

from auth_service import (
    create_user,
    authenticate_user,
    verify_email_token,
    generate_new_verification_token
)

from auth_utils import (
    create_access_token,
    get_current_user_id
)

from email_service import (
    send_verification_email
)


# ============================================================
# ROUTER
# ============================================================

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)


# ============================================================
# CONFIGURATION
# ============================================================

FRONTEND_URL = os.getenv(
    "FRONTEND_URL",
    "http://127.0.0.1:8000"
)


# ============================================================
# REQUEST MODELS
# ============================================================

class RegisterRequest(BaseModel):

    username: str

    email: EmailStr

    password: str


class LoginRequest(BaseModel):

    email: EmailStr

    password: str


class ResendVerificationRequest(BaseModel):

    email: EmailStr


# ============================================================
# REGISTER
# ============================================================

@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED
)
def register(
    request: RegisterRequest,
    db: Session = Depends(get_db)
):

    user, verification_token = create_user(
        db=db,
        username=request.username,
        email=request.email,
        password=request.password
    )


    # --------------------------------------------------------
    # BUILD VERIFICATION URL
    # --------------------------------------------------------

    verification_url = (
        f"{FRONTEND_URL.rstrip('/')}"
        f"/verify-email.html"
        f"?token={verification_token}"
    )


    # --------------------------------------------------------
    # SEND EMAIL
    # --------------------------------------------------------

    try:

        send_verification_email(
            to_email=user.email,
            username=user.username,
            verification_url=verification_url
        )

    except Exception as e:

        print(
            "Verification email failed:",
            e
        )


    return {
        "message": (
            "Registration successful. "
            "Please check your email to verify your account."
        ),
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "is_verified": user.is_verified
        }
    }


# ============================================================
# VERIFY EMAIL
# ============================================================

@router.get(
    "/verify-email"
)
def verify_email(
    token: str,
    db: Session = Depends(get_db)
):

    user = verify_email_token(
        db,
        token
    )


    return {
        "message": "Email verified successfully.",
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "is_verified": user.is_verified
        }
    }


# ============================================================
# RESEND VERIFICATION EMAIL
# ============================================================

@router.post(
    "/resend-verification"
)
def resend_verification(
    request: ResendVerificationRequest,
    db: Session = Depends(get_db)
):

    email = request.email.strip().lower()


    user = db.query(
        User
    ).filter(
        User.email == email
    ).first()


    if not user:

        raise HTTPException(
            status_code=404,
            detail="User not found."
        )


    if user.is_verified:

        return {
            "message": "Email is already verified."
        }


    token = generate_new_verification_token(
        db,
        user
    )


    verification_url = (
        f"{FRONTEND_URL.rstrip('/')}"
        f"/verify-email.html"
        f"?token={token}"
    )


    try:

        send_verification_email(
            to_email=user.email,
            username=user.username,
            verification_url=verification_url
        )

    except Exception as e:

        print(
            "Verification email failed:",
            e
        )

        raise HTTPException(
            status_code=500,
            detail="Could not send verification email."
        )


    return {
        "message": "Verification email sent successfully."
    }


# ============================================================
# LOGIN
# ============================================================

@router.post(
    "/login"
)
def login(
    request: LoginRequest,
    db: Session = Depends(get_db)
):

    user = authenticate_user(
        db=db,
        email=request.email,
        password=request.password
    )


    if not user:

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password."
        )


    if not user.is_verified:

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "Please verify your email before logging in."
            )
        )


    access_token = create_access_token(
        data={
            "sub": str(user.id)
        }
    )


    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "is_verified": user.is_verified
        }
    }


# ============================================================
# CURRENT USER
# ============================================================

@router.get(
    "/me"
)
def get_current_user(
    db: Session = Depends(get_db),
    user_id: int = Depends(
        get_current_user_id
    )
):

    user = db.query(
        User
    ).filter(
        User.id == user_id
    ).first()


    if not user:

        raise HTTPException(
            status_code=404,
            detail="User not found."
        )


    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "is_verified": user.is_verified,
        "created_at": user.created_at
    }