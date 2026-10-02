from pydantic import BaseModel, EmailStr, ConfigDict


# -----------------------------
# USER REGISTRATION REQUEST
# -----------------------------
class UserRegister(BaseModel):
    username: str
    email: EmailStr
    password: str


# -----------------------------
# USER LOGIN REQUEST
# -----------------------------
class UserLogin(BaseModel):
    email: EmailStr
    password: str


# -----------------------------
# USER RESPONSE
# -----------------------------
class UserResponse(BaseModel):
    id: int
    username: str
    email: EmailStr

    model_config = ConfigDict(from_attributes=True)


# -----------------------------
# JWT TOKEN RESPONSE
# -----------------------------
class Token(BaseModel):
    access_token: str
    token_type: str
    user_id: int
    username: str
    email: str


# -----------------------------
# FORGOT PASSWORD REQUEST
# -----------------------------
class ForgotPassword(BaseModel):
    email: EmailStr
    new_password: str


# -----------------------------
# UPDATE PROFILE REQUEST
# -----------------------------
class UpdateProfile(BaseModel):
    username: str
    email: EmailStr


# -----------------------------
# CHANGE PASSWORD REQUEST
# -----------------------------
class ChangePassword(BaseModel):
    current_password: str
    new_password: str
 