from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from schemas import UserRegister, UserLogin, UserResponse, Token
from auth_service import (
    create_user,
    authenticate_user
)
from auth_utils import create_access_token


# -----------------------------
# ROUTER CONFIGURATION
# -----------------------------
router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)


# -----------------------------
# REGISTER USER
# -----------------------------
@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED
)
def register(
    user: UserRegister,
    db: Session = Depends(get_db)
):

    new_user = create_user(
        db=db,
        username=user.username,
        email=user.email,
        password=user.password
    )

    if new_user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered."
        )

    return new_user


# -----------------------------
# LOGIN USER
# -----------------------------
@router.post(
    "/login",
    response_model=Token
)
def login(
    user: UserLogin,
    db: Session = Depends(get_db)
):

    authenticated_user = authenticate_user(
        db=db,
        email=user.email,
        password=user.password
    )

    if authenticated_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password."
        )

    access_token = create_access_token(
        {
            "sub": str(authenticated_user.id)
        }
    )

    return Token(
        access_token=access_token,
        token_type="bearer"
    )