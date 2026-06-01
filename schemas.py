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


# ──────────────────── DataSource schemas ─────────────────────


class DataSourceCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=500)
    api_url: str = Field(..., min_length=1, max_length=1000)
    auth_type: str = Field("bearer", pattern="^(bearer|api_key|header|none)$")
    auth_value: Optional[str] = Field(None, max_length=1000)
    auth_header: Optional[str] = Field(None, max_length=100)
    http_method: str = Field("GET", pattern="^(GET|POST)$")
    request_headers: Optional[Dict[str, str]] = None
    request_body: Optional[Dict[str, Any]] = None
    data_path: Optional[str] = Field(None, max_length=200)
    refresh_interval: int = Field(300, ge=60, le=86400)


class DataSourceUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=500)
    api_url: Optional[str] = Field(None, min_length=1, max_length=1000)
    auth_type: Optional[str] = Field(None, pattern="^(bearer|api_key|header|none)$")
    auth_value: Optional[str] = Field(None, max_length=1000)
    auth_header: Optional[str] = Field(None, max_length=100)
    http_method: Optional[str] = Field(None, pattern="^(GET|POST)$")
    request_headers: Optional[Dict[str, str]] = None
    request_body: Optional[Dict[str, Any]] = None
    data_path: Optional[str] = Field(None, max_length=200)
    refresh_interval: Optional[int] = Field(None, ge=60, le=86400)
    is_active: Optional[bool] = None


class DataSourceResponse(BaseModel):
    id: int
    org_id: int
    name: str
    description: Optional[str] = None
    api_url: str
    auth_type: str
    has_auth: bool = False
    auth_header: Optional[str] = None
    http_method: str
    request_headers: Optional[Dict[str, str]] = None
    data_path: Optional[str] = None
    refresh_interval: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


# ──────────────────── FieldConfig schemas ────────────────────


class FieldConfigUpdate(BaseModel):
    display_label: Optional[str] = Field(None, max_length=200)
    field_type: Optional[str] = Field(None, max_length=50)
    is_visible: Optional[bool] = None
    is_searchable: Optional[bool] = None
    is_sortable: Optional[bool] = None
    is_filterable: Optional[bool] = None
    display_order: Optional[int] = None
    format_pattern: Optional[str] = Field(None, max_length=200)
    is_email_field: Optional[bool] = None
    is_name_field: Optional[bool] = None
    is_phone_field: Optional[bool] = None


class FieldConfigResponse(BaseModel):
    id: int
    source_id: int
    field_key: str
    display_label: Optional[str] = None
    field_type: Optional[str] = None
    is_visible: bool
    is_searchable: bool
    is_sortable: bool
    is_filterable: bool
    display_order: int
    format_pattern: Optional[str] = None
    is_email_field: bool
    is_name_field: bool
    is_phone_field: bool
    model_config = ConfigDict(from_attributes=True)


class BulkFieldConfigUpdate(BaseModel):
    configs: List[Dict[str, Any]]   # [{field_key: str, ...FieldConfigUpdate fields}]


# ──────────────── Enhanced Records (with pipeline) ───────────


class DataQueryParams(BaseModel):
    source_id: Optional[int] = None
    search: Optional[str] = Field(None, max_length=500)
    sort_by: Optional[str] = Field(None, max_length=200)
    sort_order: str = Field("asc", pattern="^(asc|desc)$")
    page: int = Field(1, ge=1)
    page_size: int = Field(50, ge=1, le=500)
    filters: Optional[Dict[str, Any]] = None   # {field_key: value_or_operator}
    force_refresh: bool = False


class PaginatedRecordsResponse(BaseModel):
    columns: List[str]
    schema_info: List[ColumnSchema]
    rows: List[Dict[str, Any]]
    total: int
    page: int
    page_size: int
    total_pages: int
    source_id: int
    source_name: str
    fetched_at: str
    is_cached: bool
    cache_expires_at: Optional[str] = None


class MultiSourceSummary(BaseModel):
    sources: List[Dict[str, Any]]   # [{id, name, row_count, columns, last_fetched, is_active}]
    total_sources: int
    total_records: int


# ──────────────────── Email schemas ──────────────────────────


class EmailTemplateCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    subject: str = Field(..., min_length=1, max_length=500)
    body_html: str = Field(..., min_length=1)
    placeholders: Optional[List[str]] = None


class EmailTemplateResponse(BaseModel):
    id: int
    org_id: int
    name: str
    subject: str
    body_html: str
    placeholders: Optional[List[str]] = None
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class SendEmailRequest(BaseModel):
    source_id: int
    template_id: Optional[int] = None
    subject: Optional[str] = Field(None, max_length=500)
    body_html: Optional[str] = None
    row_ids: Optional[List[int]] = None          # specific row indices
    filters: Optional[Dict[str, Any]] = None     # or filter criteria
    email_field: Optional[str] = None            # which field has email
    name_field: Optional[str] = None             # which field has name


class SendEmailResponse(BaseModel):
    total_recipients: int
    queued: int
    failed: int
    details: List[Dict[str, Any]]


# ──────────────────── Analytics schemas ──────────────────────


class AnalyticsRequest(BaseModel):
    source_id: int
    group_by: Optional[str] = None
    aggregate: Optional[str] = Field(None, pattern="^(count|sum|avg|min|max)$")
    aggregate_field: Optional[str] = None
    filters: Optional[Dict[str, Any]] = None


class AnalyticsResponse(BaseModel):
    source_id: int
    source_name: str
    result: List[Dict[str, Any]]
    summary: Dict[str, Any]
    generated_at: str


class ActionLogResponse(BaseModel):
    id: int
    action_type: str
    action_detail: Optional[Dict[str, Any]] = None
    status: str
    result_summary: Optional[str] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
