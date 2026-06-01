import models
import schemas
from services.records_service import fetch_organization_records
from services.data_pipeline import get_legacy_org_records
from fastapi import HTTPException, status
from sqlalchemy.orm import Session


def _org_response(org: models.Organization) -> schemas.OrganizationResponse:
    return schemas.OrganizationResponse(
        id=org.id,
        name=org.name,
        industry=org.industry,
        api_url=org.api_url,
        has_api_key=bool(org.api_key),
        created_at=org.created_at,
    )


def get_organization(
    current_user: models.User,
) -> schemas.OrganizationResponse:
    if not current_user.organization:
        raise HTTPException(status_code=404, detail="Organization not found")
    return _org_response(current_user.organization)


def create_or_update_organization(
    payload: schemas.OrganizationCreate,
    current_user: models.User,
    db: Session,
) -> schemas.OrganizationResponse:
    if current_user.organization:
        org = current_user.organization
        org.name = payload.name
        org.industry = payload.industry
        org.api_url = payload.api_url
        if payload.api_key is not None:
            org.api_key = payload.api_key or None
    else:
        org = models.Organization(
            user_id=current_user.id,
            name=payload.name,
            industry=payload.industry,
            api_url=payload.api_url,
            api_key=payload.api_key,
        )
        db.add(org)

    current_user.onboarding_completed = True
    db.commit()
    db.refresh(current_user)
    db.refresh(org)
    return _org_response(org)


async def get_records(
    current_user: models.User,
    db: Session,
) -> schemas.DynamicRecordsResponse:
    org = current_user.organization
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    try:
        result = await get_legacy_org_records(org, db)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to fetch records from organization API: {exc}",
        ) from exc

    return schemas.DynamicRecordsResponse(
        columns=result["columns"],
        schema=result.get("schema_info", result.get("schema", [])),
        rows=result["rows"],
        total=result["total"],
        source=result.get("source", result.get("source_name", "api")),
        fetched_at=result["fetched_at"],
    )
