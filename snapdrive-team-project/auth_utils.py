import os
from datetime import datetime, timedelta, timezone

from dotenv import load_dotenv
from jose import JWTError, jwt
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer

from passlib.context import CryptContext


# Patch bcrypt to prevent passlib AttributeError on Python 3.12+ (Vercel)
try:
    import bcrypt
    if not hasattr(bcrypt, "__about__"):
        bcrypt.__about__ = type("About", (object,), {"__version__": bcrypt.__version__})
except ImportError:
    pass


# -----------------------------
# LOAD ENVIRONMENT VARIABLES
# -----------------------------
load_dotenv()


# -----------------------------
# SECURITY CONFIGURATION
# -----------------------------
SECRET_KEY = os.getenv("SECRET_KEY", "default-fallback-secret-key-snapdrive-12345")

ALGORITHM = os.getenv("ALGORITHM", "HS256")

ACCESS_TOKEN_EXPIRE_MINUTES = int(
    os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 60)
)


# -----------------------------
# PASSWORD HASHING
# -----------------------------
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)


def hash_password(password: str) -> str:
    """
    Hash a plain text password.
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify plain password against hashed password.
    """
    return pwd_context.verify(
        plain_password,
        hashed_password
    )


# -----------------------------
# JWT TOKEN CREATION
# -----------------------------
def create_access_token(data: dict) -> str:
    """
    Create JWT access token.
    """

    to_encode = data.copy()

    expire = datetime.now(timezone.utc) + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )

    to_encode.update({
        "exp": expire
    })

    encoded_jwt = jwt.encode(
        to_encode,
        SECRET_KEY,
        algorithm=ALGORITHM
    )

    return encoded_jwt


# -----------------------------
# JWT TOKEN VERIFICATION
# -----------------------------
def verify_access_token(token: str):
    """
    Verify JWT token and return payload.
    """

    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        return payload

    except JWTError:
        return None


# -----------------------------
# JWT DEPENDENCY FOR FASTAPI - UPDATED FOR FASTAPI COMPATIBILITY
# -----------------------------
security = HTTPBearer()

def get_current_user_id(credentials = Depends(security)) -> int:
    """
    Extract and verify JWT token from Authorization header, return user_id.
    
    This dependency ensures only authenticated users can access the endpoint.
    Usage in route:
        @app.get("/protected")
        def protected_route(user_id: int = Depends(get_current_user_id)):
            ...
    """
    
    # Extract token from credentials object
    token = credentials.credentials
    
    # Verify the token
    payload = verify_access_token(token)
    
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Extract user_id from payload
    user_id = payload.get("sub")
    
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token: missing user_id",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        return int(user_id)
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token: invalid user_id format",
            headers={"WWW-Authenticate": "Bearer"},
        )