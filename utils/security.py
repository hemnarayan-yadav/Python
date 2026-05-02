import os
from passlib.context import CryptContext
from jose import jwt
from datetime import datetime, timedelta, timezone

# Read JWT settings from environment (loaded by database.py via load_dotenv()).
# Fail fast at import time if SECRET_KEY is missing -- a clear error now is
# much better than a silent security hole later.
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY is not set in environment (.env)")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# hash password
def hash_password(password: str) -> str:
    return pwd_context.hash(password)


# verify password
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


# create JWT token
def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    # Use timezone-aware UTC; datetime.utcnow() is deprecated in Python 3.12+.
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
