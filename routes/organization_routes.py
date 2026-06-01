from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from controllers import organization_controller
from database import get_db
from schemas import OrganizationCreate, OrganizationResponse, DynamicRecordsResponse
from utils.dependencies import get_current_user, require_onboarding_complete
import models

router = APIRouter(prefix="/organization", tags=["Organization"])


@router.get("/me", response_model=OrganizationResponse)
def get_my_organization(
    current_user: models.User = Depends(get_current_user),
):
    return organization_controller.get_organization(current_user)


@router.post(
    "/setup",
    response_model=OrganizationResponse,
    status_code=status.HTTP_201_CREATED,
)
def setup_organization(
    payload: OrganizationCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return organization_controller.create_or_update_organization(
        payload, current_user, db
    )


@router.get("/records", response_model=DynamicRecordsResponse)
async def get_organization_records(
    current_user: models.User = Depends(require_onboarding_complete),
):
    return await organization_controller.get_records(current_user)
