from typing import List
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

import models
import schemas
from database import SessionLocal


# ---- Dependency: provides a DB session per request and always closes it ----
# Defining it here (instead of main.py) keeps controllers self-contained.
def get_db():
    db = SessionLocal()
    try:
        yield db          # FastAPI injects this into route functions
    finally:
        db.close()        # always close, even if an exception is raised


# ===================== CRUD =====================
# Note the type hints on every parameter:
#   - `user: schemas.UserCreate`   -> FastAPI parses & validates the JSON body
#   - `db: Session = Depends(...)` -> FastAPI injects a DB session
# Without these hints, FastAPI cannot wire the route correctly.
# That was the main bug in the original code.


# ---- CREATE ----
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)) -> models.User:
    # Build the ORM object from validated input.
    # We never trust the client to set `id` or `created_at`.
    new_user = models.User(name=user.name, email=user.email, age=user.age)

    db.add(new_user)
    try:
        db.commit()                # actually write to MySQL
    except IntegrityError:
        # Hits when the unique-email constraint is violated.
        db.rollback()              # leave the session in a clean state
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email already exists.",
        )
    db.refresh(new_user)           # reload to get DB-generated id & created_at
    return new_user


# ---- READ (list) ----
# skip/limit are basic pagination. Never return ALL rows -
# it can crash the server when the table grows.
def list_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)) -> List[models.User]:
    return db.query(models.User).offset(skip).limit(limit).all()


# ---- READ (one) ----
def get_user(user_id: int, db: Session = Depends(get_db)) -> models.User:
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if user is None:
        # Always return 404 for "not found" - never silently return None.
        raise HTTPException(status_code=404, detail="User not found")
    return user


# ---- UPDATE (partial) ----
def update_user(
    user_id: int,
    payload: schemas.UserUpdate,
    db: Session = Depends(get_db),
) -> models.User:
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    # exclude_unset=True -> only fields the client actually sent are updated.
    # That is what makes it a true PATCH (vs PUT which replaces everything).
    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Email already in use.")
    db.refresh(user)
    return user


# ---- DELETE ----
def delete_user(user_id: int, db: Session = Depends(get_db)) -> dict:
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    db.delete(user)
    db.commit()
    return {"detail": f"User {user_id} deleted"}