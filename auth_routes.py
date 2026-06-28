from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from schemas import UserRegister, UserLogin, UserResponse, Token, ForgotPassword, UpdateProfile, ChangePassword
from auth_service import (
    create_user,
    authenticate_user,
    get_user_by_email
)
from auth_utils import create_access_token, hash_password, verify_password
from models import User


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
        token_type="bearer",
        user_id=authenticated_user.id,
        username=authenticated_user.username,
        email=authenticated_user.email
    )


# -----------------------------
# FORGOT PASSWORD
# -----------------------------
@router.post("/forgot-password")
def forgot_password(
    data: ForgotPassword,
    db: Session = Depends(get_db)
):
    user = get_user_by_email(db, data.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No account found with this email address."
        )

    user.hashed_password = hash_password(data.new_password)
    db.commit()

    return {"status": "success", "message": "Password has been reset successfully."}


# -----------------------------
# UPDATE PROFILE
# -----------------------------
@router.put("/update-profile")
def update_profile(
    user_id: int,
    data: UpdateProfile,
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Check if new email is already taken by another user
    if data.email != user.email:
        existing = db.query(User).filter(User.email == data.email, User.id != user_id).first()
        if existing:
            raise HTTPException(status_code=400, detail="Email already in use by another account.")

    # Check if new username is already taken by another user
    if data.username != user.username:
        existing = db.query(User).filter(User.username == data.username, User.id != user_id).first()
        if existing:
            raise HTTPException(status_code=400, detail="Username already taken.")

    user.username = data.username
    user.email = data.email
    db.commit()
    db.refresh(user)

    return {
        "status": "success",
        "message": "Profile updated successfully.",
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email
        }
    }


# -----------------------------
# CHANGE PASSWORD
# -----------------------------
@router.put("/change-password")
def change_password(
    user_id: int,
    data: ChangePassword,
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not verify_password(data.current_password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Current password is incorrect.")

    user.hashed_password = hash_password(data.new_password)
    db.commit()

    return {"status": "success", "message": "Password changed successfully."}
 