from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path

import models
from database import engine
from routes.user_routes import router as user_router
from routes.auth_routes import router as auth_router
from routes.ai_routes import router as ai_router

BASE_DIR = Path(__file__).resolve().parent

# Create the FastAPI application instance.
app = FastAPI(title="NexusAI — Smart User Intelligence", version="2.0.0")

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create all tables that don't yet exist in the DB.
models.Base.metadata.create_all(bind=engine)

# Mount routes
app.include_router(user_router)
app.include_router(auth_router)
app.include_router(ai_router)


@app.get("/", response_class=HTMLResponse, tags=["UI"])
def dashboard():
    html_path = BASE_DIR / "templates" / "index.html"
    return HTMLResponse(content=html_path.read_text(encoding="utf-8"))


@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok", "service": "NexusAI"}