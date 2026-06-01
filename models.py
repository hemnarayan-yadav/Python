from sqlalchemy import Column, Integer, String, TIMESTAMP, Text, ForeignKey, Boolean, func
from sqlalchemy.orm import relationship
from database import Base


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
