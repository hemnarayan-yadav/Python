from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, ConfigDict


# Pydantic schemas define the SHAPE of data going IN/OUT of the API.
# They are separate from SQLAlchemy models (which describe DB tables).
# Why separate? -> security (don't leak internal fields), validation, versioning.


# ---------- INPUT schemas ----------

class UserCreate(BaseModel):
    # "..." = required. min/max_length blocks empty or huge strings.
    name: str = Field(..., min_length=1, max_length=100)

    # EmailStr validates the email format automatically.
    # Requires:  pip install "pydantic[email]"
    email: EmailStr

    # gt=0 -> must be > 0; lt=150 -> sane upper bound.
    age: int = Field(..., gt=0, lt=150)


class UserUpdate(BaseModel):
    # All fields optional -> partial update (PATCH-style).
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    email: Optional[EmailStr] = None
    age: Optional[int] = Field(None, gt=0, lt=150)


# ---------- OUTPUT schema ----------

class UserResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    age: int
    created_at: datetime  # let the client know when the user was created

    # Pydantic v2 way of saying "read attributes from ORM objects".
    # Without this, FastAPI cannot turn a SQLAlchemy `User` into JSON.
    # (In Pydantic v1 this was: class Config: orm_mode = True)
    model_config = ConfigDict(from_attributes=True)
class UserRegistration(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    age: int = Field(..., gt=1, lt=100)
    password: str = Field(..., min_length=3, max_length=200)


class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=3, max_length=200)


# Standard OAuth2 token response shape.
# NEVER return the password (even hashed) to clients.
class TokenResponse(BaseModel):
    access_token: str


# ---------- AI schemas ----------

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)


class ChatResponse(BaseModel):
    reply: str
    model_config = ConfigDict(from_attributes=True)


class ContentGenerateRequest(BaseModel):
    user_id: Optional[int] = None
    content_type: str = Field(..., pattern="^(email|bio|report|social_post)$")
    extra_instructions: Optional[str] = Field(None, max_length=500)


class ContentGenerateResponse(BaseModel):
    content_type: str
    result: str
    model_config = ConfigDict(from_attributes=True)


class InsightRequest(BaseModel):
    question: Optional[str] = Field(None, max_length=500)


class InsightResponse(BaseModel):
    insight: str
    user_count: int
    avg_age: Optional[float] = None
    token_type: str = "bearer"

