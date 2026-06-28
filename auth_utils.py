import os
from datetime import datetime, timedelta, timezone

from dotenv import load_dotenv
from jose import JWTError, jwt

# Patch bcrypt to prevent passlib AttributeError on Python 3.12+ (Vercel)
try:
    import bcrypt
    if not hasattr(bcrypt, "__about__"):
        bcrypt.__about__ = type("About", (object,), {"__version__": bcrypt.__version__})
except ImportError:
    pass

from passlib.context import CryptContext


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
    Verify JWT token.
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
 