from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import inspect, text

import models
from database import engine
from routes.user_routes import router as user_router
from routes.auth_routes import router as auth_router
from routes.ai_routes import router as ai_router
from routes.organization_routes import router as organization_router

BASE_DIR = Path(__file__).resolve().parent
FRONTEND_DIST = BASE_DIR / "frontend" / "dist"


def run_migrations():
    """Add new columns/tables on existing databases (create_all alone won't alter)."""
    inspector = inspect(engine)
    tables = inspector.get_table_names()

    if "users" in tables:
        cols = {c["name"] for c in inspector.get_columns("users")}
        if "onboarding_completed" not in cols:
            with engine.begin() as conn:
                conn.execute(
                    text(
                        "ALTER TABLE users ADD COLUMN onboarding_completed "
                        "BOOLEAN NOT NULL DEFAULT 0"
                    )
                )

    required_org_cols = {
        "id",
        "user_id",
        "name",
        "industry",
        "api_url",
        "api_key",
        "created_at",
    }
    if "organizations" in tables:
        org_cols = {c["name"] for c in inspector.get_columns("organizations")}
        if not required_org_cols.issubset(org_cols):
            with engine.begin() as conn:
                conn.execute(text("DROP TABLE IF EXISTS organizations"))


app = FastAPI(title="NexusAI — Smart User Intelligence", version="3.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

run_migrations()
models.Base.metadata.create_all(bind=engine)

app.include_router(user_router)
app.include_router(auth_router)
app.include_router(ai_router)
app.include_router(organization_router)


@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok", "service": "NexusAI"}


if FRONTEND_DIST.exists():
    assets_dir = FRONTEND_DIST / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    def serve_spa(full_path: str):
        index = FRONTEND_DIST / "index.html"
        file_path = FRONTEND_DIST / full_path
        if full_path and file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(index)

else:

    @app.get("/", tags=["UI"])
    def root_hint():
        return {
            "message": "Frontend not built. Run: cd frontend && npm install && npm run build"
        }
