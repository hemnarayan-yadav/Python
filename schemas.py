from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, EmailStr, Field, ConfigDict


# ---------- User schemas ----------

class UserCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    age: int = Field(..., gt=0, lt=150)


class UserUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    email: Optional[EmailStr] = None
    age: Optional[int] = Field(None, gt=0, lt=150)


class UserResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    age: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class UserRegistration(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    age: int = Field(..., gt=1, lt=100)
    password: str = Field(..., min_length=3, max_length=200)


class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=3, max_length=200)


class OrganizationCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    industry: Optional[str] = Field(None, max_length=100)
    api_url: Optional[str] = Field(None, max_length=500)
    api_key: Optional[str] = Field(None, max_length=500)


class OrganizationResponse(BaseModel):
    id: int
    name: str
    industry: Optional[str] = None
    api_url: Optional[str] = None
    has_api_key: bool = False
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class AuthUserResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    age: int
    onboarding_completed: bool
    organization: Optional[OrganizationResponse] = None
    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    onboarding_completed: bool


class RegisterResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    onboarding_completed: bool
    user: AuthUserResponse


class ColumnSchema(BaseModel):
    key: str
    label: str
    type: str  # string | number | boolean | json | null
    nullable: bool


class DynamicRecordsResponse(BaseModel):
    columns: List[str]
    schema: List[ColumnSchema]
    rows: List[Dict[str, Any]]
    total: int
    source: str
    fetched_at: str


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
