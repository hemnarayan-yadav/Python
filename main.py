from fastapi import FastAPI

import models
from database import engine
from routes.user_routes import router as user_router
from routes.auth_routes import router as auth_router


# Create the FastAPI application instance.
# Visit http://127.0.0.1:8000/docs once running for interactive Swagger UI.
app = FastAPI(title="Users CRUD API", version="1.0.0")

# Create all tables that don't yet exist in the DB.
# NOTE: Fine for learning / small projects. For real apps use Alembic
# migrations so schema changes are versioned and reversible.
models.Base.metadata.create_all(bind=engine)

# Mount the /users routes onto the main app.
app.include_router(user_router)
app.include_router(auth_router)


@app.get("/", tags=["Health"])
def root():
    # Tiny health-check endpoint. Useful for uptime monitors.
    return {"status": "ok"}