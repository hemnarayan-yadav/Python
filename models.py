from sqlalchemy import (
    Column, Integer, String, TIMESTAMP, Text, ForeignKey, Boolean, JSON, func,
)
from sqlalchemy.orm import relationship
from database import Base


# ──────────────────────────── Core Models ────────────────────────────


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(150), unique=True, index=True, nullable=False)
    password = Column(String(255))
    age = Column(Integer, nullable=False)
    onboarding_completed = Column(Boolean, default=False, nullable=False, server_default="0")
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)

    organization = relationship("Organization", back_populates="owner", uselist=False)
    chat_messages = relationship("ChatMessage", back_populates="user")
    ai_contents = relationship("AIContent", back_populates="user")


class Organization(Base):
    __tablename__ = "organizations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    industry = Column(String(100), nullable=True)
    api_url = Column(String(500), nullable=True)
    api_key = Column(String(500), nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)

    owner = relationship("User", back_populates="organization")
    data_sources = relationship("DataSource", back_populates="organization", cascade="all, delete-orphan")


# ──────────────────────── Data Pipeline Models ───────────────────────


class DataSource(Base):
    """Each organization can have multiple external data sources (APIs)."""
    __tablename__ = "data_sources"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    name = Column(String(200), nullable=False)
    description = Column(String(500), nullable=True)
    api_url = Column(String(1000), nullable=False)
    auth_type = Column(String(50), default="bearer")        # bearer | api_key | header | none
    auth_value = Column(String(1000), nullable=True)         # encrypted token / key
    auth_header = Column(String(100), nullable=True)          # custom header name
    http_method = Column(String(10), default="GET")
    request_headers = Column(JSON, nullable=True)             # extra headers as dict
    request_body = Column(JSON, nullable=True)                # body for POST sources
    data_path = Column(String(200), nullable=True)            # JSONPath to data array (e.g. "data.users")
    refresh_interval = Column(Integer, default=300)           # seconds between auto-refresh
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now(), nullable=False)

    organization = relationship("Organization", back_populates="data_sources")
    cache = relationship("DataCache", back_populates="data_source", uselist=False, cascade="all, delete-orphan")
    field_configs = relationship("FieldConfig", back_populates="data_source", cascade="all, delete-orphan")


class DataCache(Base):
    """Cached copy of fetched data — avoids hitting external APIs on every request."""
    __tablename__ = "data_cache"

    id = Column(Integer, primary_key=True, index=True)
    source_id = Column(Integer, ForeignKey("data_sources.id"), unique=True, nullable=False, index=True)
    raw_data = Column(JSON, nullable=False)                   # full normalized rows
    schema_snapshot = Column(JSON, nullable=False)             # column schema at fetch time
    row_count = Column(Integer, default=0)
    fetched_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    expires_at = Column(TIMESTAMP, nullable=False)

    data_source = relationship("DataSource", back_populates="cache")


class FieldConfig(Base):
    """Per-source field display & behaviour configuration."""
    __tablename__ = "field_configs"

    id = Column(Integer, primary_key=True, index=True)
    source_id = Column(Integer, ForeignKey("data_sources.id"), nullable=False, index=True)
    field_key = Column(String(200), nullable=False)           # original JSON key
    display_label = Column(String(200), nullable=True)        # custom label override
    field_type = Column(String(50), nullable=True)            # type override
    is_visible = Column(Boolean, default=True)
    is_searchable = Column(Boolean, default=True)
    is_sortable = Column(Boolean, default=True)
    is_filterable = Column(Boolean, default=True)
    display_order = Column(Integer, default=0)
    format_pattern = Column(String(200), nullable=True)       # e.g. date format, number format
    is_email_field = Column(Boolean, default=False)           # marks this as an email column
    is_name_field = Column(Boolean, default=False)            # marks this as a name column
    is_phone_field = Column(Boolean, default=False)           # marks this as a phone column

    data_source = relationship("DataSource", back_populates="field_configs")


# ──────────────────────── Action & Log Models ────────────────────────


class ActionLog(Base):
    """Audit trail for every action performed on organization data."""
    __tablename__ = "action_logs"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    source_id = Column(Integer, ForeignKey("data_sources.id"), nullable=True)
    action_type = Column(String(50), nullable=False)          # fetch | email | export | analysis | filter
    action_detail = Column(JSON, nullable=True)               # parameters, filters, row IDs, etc.
    status = Column(String(20), default="success")            # success | failed | pending
    result_summary = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)


class EmailTemplate(Base):
    """Reusable email templates per organization."""
    __tablename__ = "email_templates"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    name = Column(String(200), nullable=False)
    subject = Column(String(500), nullable=False)
    body_html = Column(Text, nullable=False)
    placeholders = Column(JSON, nullable=True)                # list of {{field_key}} vars
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now(), nullable=False)


class EmailLog(Base):
    """Track every email sent through the platform."""
    __tablename__ = "email_logs"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    source_id = Column(Integer, ForeignKey("data_sources.id"), nullable=True)
    template_id = Column(Integer, ForeignKey("email_templates.id"), nullable=True)
    recipient_email = Column(String(300), nullable=False)
    recipient_name = Column(String(200), nullable=True)
    subject = Column(String(500), nullable=False)
    body_html = Column(Text, nullable=False)
    status = Column(String(20), default="pending")            # pending | sent | failed | bounced
    sent_at = Column(TIMESTAMP, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)


# ──────────────────────── Chat & AI (existing) ───────────────────────


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    role = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)

    user = relationship("User", back_populates="chat_messages")


class AIContent(Base):
    __tablename__ = "ai_contents"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    content_type = Column(String(50), nullable=False)
    prompt = Column(Text, nullable=False)
    result = Column(Text, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)

    user = relationship("User", back_populates="ai_contents")
