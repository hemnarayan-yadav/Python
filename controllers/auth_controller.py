import models
import schemas
from database import SessionLocal

from utils.security import hash_password, verify_password, create_access_token
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def register_user( user: schemas.UserRegistration, db: Session = Depends(get_db)) -> models.User:
    hashed = hash_password(user.password)

    new_user = models.User(
        name=user.name, email=user.email, age=user.age, password=hashed
    )
    db.add(new_user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email already exists.",
        )

    db.refresh(new_user)

    return new_user


def login_user(user: schemas.UserLogin, db: Session = Depends(get_db)) -> dict:
    db_user = db.query(models.User).filter(models.User.email == user.email).first()

    # Same 401 for "no such user" and "wrong password" -- prevents
    # attackers from enumerating which emails are registered.
    if not db_user or not verify_password(user.password, db_user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    token = create_access_token({"sub": db_user.email})
    return {"access_token": token, "token_type": "bearer"}

    