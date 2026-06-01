import models
import schemas
from database import get_db
from utils.security import hash_password, verify_password, create_access_token
from utils.dependencies import get_current_user
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError


def _auth_user(user: models.User) -> schemas.AuthUserResponse:
    org = None
    # Sirf onboarding complete hone par org load karo — register par lazy-load crash avoid
    if user.onboarding_completed and user.organization:
        org = schemas.OrganizationResponse(
            id=user.organization.id,
            name=user.organization.name,
            industry=user.organization.industry,
            api_url=user.organization.api_url,
            has_api_key=bool(user.organization.api_key),
            created_at=user.organization.created_at,
        )
    return schemas.AuthUserResponse(
        id=user.id,
        name=user.name,
        email=user.email,
        age=user.age,
        onboarding_completed=user.onboarding_completed,
        organization=org,
    )


def register_user(
    user: schemas.UserRegistration,
    db: Session = Depends(get_db),
) -> schemas.RegisterResponse:
    hashed = hash_password(user.password)
    new_user = models.User(
        name=user.name,
        email=user.email,
        age=user.age,
        password=hashed,
        onboarding_completed=False,
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

    token = create_access_token({"sub": new_user.email})
    return schemas.RegisterResponse(
        access_token=token,
        onboarding_completed=False,
        user=_auth_user(new_user),
    )


def login_user(
    user: schemas.UserLogin,
    db: Session = Depends(get_db),
) -> schemas.TokenResponse:
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if not db_user or not verify_password(user.password, db_user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    token = create_access_token({"sub": db_user.email})
    return schemas.TokenResponse(
        access_token=token,
        onboarding_completed=db_user.onboarding_completed,
    )


def get_current_user_profile(
    current_user: models.User = Depends(get_current_user),
) -> schemas.AuthUserResponse:
    return _auth_user(current_user)
