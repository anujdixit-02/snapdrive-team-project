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