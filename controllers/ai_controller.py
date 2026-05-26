import os
import logging
from pathlib import Path
from typing import List, Optional

from dotenv import load_dotenv
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func

import models
import schemas
from database import SessionLocal

# Ensure .env is loaded before reading any keys
load_dotenv(Path(__file__).resolve().parent.parent / ".env", override=True)

logger = logging.getLogger("nexusai")

# ──────────────────────────────────────────────────────────────
# Multi-Provider AI Engine — auto-fallback: OpenAI → Gemini → Groq
# ──────────────────────────────────────────────────────────────

class AIProvider:
    """Base class for AI providers."""
    name: str = "base"

    def is_available(self) -> bool:
        return False

    def chat_completion(self, messages: list, max_tokens: int = 1000, temperature: float = 0.7) -> str:
        raise NotImplementedError


class OpenAIProvider(AIProvider):
    name = "OpenAI"

    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY", "")

    def is_available(self) -> bool:
        return bool(self.api_key and self.api_key.startswith("sk-"))

    def chat_completion(self, messages, max_tokens=1000, temperature=0.7) -> str:
        from openai import OpenAI
        client = OpenAI(api_key=self.api_key)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        return response.choices[0].message.content


class GeminiProvider(AIProvider):
    name = "Gemini"

    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY", "")

    def is_available(self) -> bool:
        return bool(self.api_key)

    def chat_completion(self, messages, max_tokens=1000, temperature=0.7) -> str:
        import google.generativeai as genai
        genai.configure(api_key=self.api_key)
        model = genai.GenerativeModel("gemini-2.0-flash")

        # Convert OpenAI-style messages to Gemini format
        system_text = ""
        chat_parts = []
        for msg in messages:
            if msg["role"] == "system":
                system_text = msg["content"]
            elif msg["role"] == "user":
                chat_parts.append({"role": "user", "parts": [msg["content"]]})
            elif msg["role"] == "assistant":
                chat_parts.append({"role": "model", "parts": [msg["content"]]})

        # Prepend system prompt to first user message
        if system_text and chat_parts:
            chat_parts[0]["parts"][0] = f"[System Instructions]: {system_text}\n\n{chat_parts[0]['parts'][0]}"

        response = model.generate_content(
            chat_parts[-1]["parts"][0] if len(chat_parts) == 1 else chat_parts,
            generation_config=genai.types.GenerationConfig(
                max_output_tokens=max_tokens,
                temperature=temperature,
            ),
        )
        return response.text


class GroqProvider(AIProvider):
    name = "Groq"

    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY", "")

    def is_available(self) -> bool:
        return bool(self.api_key)

    def chat_completion(self, messages, max_tokens=1000, temperature=0.7) -> str:
        from groq import Groq
        client = Groq(api_key=self.api_key)
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        return response.choices[0].message.content


# ── Initialize providers in priority order ──
_providers = [OpenAIProvider(), GeminiProvider(), GroqProvider()]
_available = [p for p in _providers if p.is_available()]

if _available:
    logger.info(f"AI providers available: {[p.name for p in _available]}")
else:
    logger.warning("No AI provider API keys configured! Set OPENAI_API_KEY, GEMINI_API_KEY, or GROQ_API_KEY in .env")


def _call_ai(messages: list, max_tokens: int = 1000, temperature: float = 0.7) -> tuple[str, str]:
    """Try each provider in order. Returns (response_text, provider_name)."""
    errors = []
    for provider in _available:
        try:
            logger.info(f"Trying AI provider: {provider.name}")
            result = provider.chat_completion(messages, max_tokens, temperature)
            logger.info(f"Success with {provider.name}")
            return result, provider.name
        except Exception as e:
            error_msg = str(e)
            logger.warning(f"{provider.name} failed: {error_msg}")
            errors.append(f"{provider.name}: {error_msg}")
            continue

    if not _available:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="No AI providers configured. Add OPENAI_API_KEY, GEMINI_API_KEY, or GROQ_API_KEY to your .env file.",
        )
    raise HTTPException(
        status_code=status.HTTP_502_BAD_GATEWAY,
        detail=f"All AI providers failed: {' | '.join(errors)}",
    )


SYSTEM_PROMPT = """You are NexusAI, an intelligent assistant for a user management platform.
You help analyze user data, generate content, and provide insights.
Be concise, professional, and helpful. Use markdown formatting when appropriate."""


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _get_user_context(db: Session, user_id: Optional[int] = None) -> str:
    """Build context string from user data for AI prompts."""
    if user_id:
        user = db.query(models.User).filter(models.User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return f"User: {user.name}, Email: {user.email}, Age: {user.age}, Joined: {user.created_at}"

    users = db.query(models.User).limit(50).all()
    if not users:
        return "No users in the system yet."
    lines = [f"- {u.name} (age {u.age}, {u.email}, joined {u.created_at})" for u in users]
    return f"Total users: {len(users)}\n" + "\n".join(lines)


def get_providers_status() -> dict:
    """Return status of all AI providers."""
    return {
        "providers": [
            {"name": p.name, "available": p.is_available(), "priority": i + 1}
            for i, p in enumerate(_providers)
        ],
        "active": _available[0].name if _available else None,
    }


def chat(request: schemas.ChatRequest, db: Session = Depends(get_db)) -> dict:
    """AI chat that is aware of your user database."""
    user_context = _get_user_context(db)

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT + f"\n\nCurrent user data:\n{user_context}"},
        {"role": "user", "content": request.message},
    ]

    reply, provider = _call_ai(messages, max_tokens=1000, temperature=0.7)

    db.add(models.ChatMessage(role="user", content=request.message))
    db.add(models.ChatMessage(role="assistant", content=reply))
    db.commit()

    return {"reply": reply}


def generate_content(
    request: schemas.ContentGenerateRequest, db: Session = Depends(get_db)
) -> dict:
    """Generate AI content (email, bio, report, social post) for a user."""
    user_context = _get_user_context(db, request.user_id)

    type_prompts = {
        "email": "Write a professional welcome email for this user.",
        "bio": "Write a creative professional bio for this user's profile.",
        "report": "Generate a brief analytics report about this user or all users.",
        "social_post": "Write an engaging social media post introducing this user.",
    }

    prompt = type_prompts.get(request.content_type, "Generate content for this user.")
    if request.extra_instructions:
        prompt += f"\nAdditional instructions: {request.extra_instructions}"

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"{prompt}\n\nContext:\n{user_context}"},
    ]

    result, provider = _call_ai(messages, max_tokens=1500, temperature=0.8)

    ai_content = models.AIContent(
        user_id=request.user_id,
        content_type=request.content_type,
        prompt=prompt,
        result=result,
    )
    db.add(ai_content)
    db.commit()

    return {"content_type": request.content_type, "result": result}


def get_insights(
    request: schemas.InsightRequest, db: Session = Depends(get_db)
) -> dict:
    """AI-powered analytics insights about your user base."""
    user_count = db.query(func.count(models.User.id)).scalar()
    avg_age = db.query(func.avg(models.User.age)).scalar()

    user_context = _get_user_context(db)
    question = request.question or "Provide a summary of the user base with key insights and recommendations."

    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT + "\nYou are analyzing user data. Provide actionable insights with statistics.",
        },
        {
            "role": "user",
            "content": f"Question: {question}\n\nData:\n{user_context}\n\nStats: {user_count} total users, average age: {avg_age:.1f}" if avg_age else f"Question: {question}\n\nData:\n{user_context}",
        },
    ]

    insight, provider = _call_ai(messages, max_tokens=1000, temperature=0.5)

    return {
        "insight": insight,
        "user_count": user_count,
        "avg_age": round(avg_age, 1) if avg_age else None,
    }


def get_chat_history(db: Session = Depends(get_db)) -> List[dict]:
    """Return recent chat history."""
    messages = (
        db.query(models.ChatMessage)
        .order_by(models.ChatMessage.created_at.desc())
        .limit(50)
        .all()
    )
    return [
        {"role": m.role, "content": m.content, "created_at": str(m.created_at)}
        for m in reversed(messages)
    ]
