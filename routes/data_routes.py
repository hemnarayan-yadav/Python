"""Routes for the enhanced data pipeline, email, and analytics system."""

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

import schemas
from controllers import data_controller
from database import get_db
from utils.dependencies import get_current_user, require_onboarding_complete

router = APIRouter(prefix="/data", tags=["Data Pipeline"])


# ─────────────── Data Sources CRUD ──────────────────────────


@router.get("/sources", response_model=list[schemas.DataSourceResponse])
def list_sources(
    current_user=Depends(require_onboarding_complete),
    db: Session = Depends(get_db),
):
    return data_controller.list_sources(current_user, db)


@router.post("/sources", response_model=schemas.DataSourceResponse, status_code=201)
def create_source(
    payload: schemas.DataSourceCreate,
    current_user=Depends(require_onboarding_complete),
    db: Session = Depends(get_db),
):
    return data_controller.create_source(payload, current_user, db)


@router.patch("/sources/{source_id}", response_model=schemas.DataSourceResponse)
def update_source(
    source_id: int,
    payload: schemas.DataSourceUpdate,
    current_user=Depends(require_onboarding_complete),
    db: Session = Depends(get_db),
):
    return data_controller.update_source(source_id, payload, current_user, db)


@router.delete("/sources/{source_id}")
def delete_source(
    source_id: int,
    current_user=Depends(require_onboarding_complete),
    db: Session = Depends(get_db),
):
    return data_controller.delete_source(source_id, current_user, db)


@router.get("/sources/summary", response_model=schemas.MultiSourceSummary)
def sources_summary(
    current_user=Depends(require_onboarding_complete),
    db: Session = Depends(get_db),
):
    return data_controller.get_sources_summary(current_user, db)


@router.post("/sources/{source_id}/refresh")
async def refresh_source(
    source_id: int,
    current_user=Depends(require_onboarding_complete),
    db: Session = Depends(get_db),
):
    return await data_controller.refresh_source(source_id, current_user, db)


# ─────────────── Records Query (the main pipeline) ──────────


@router.post("/records", response_model=schemas.PaginatedRecordsResponse)
async def query_records(
    params: schemas.DataQueryParams,
    current_user=Depends(require_onboarding_complete),
    db: Session = Depends(get_db),
):
    return await data_controller.query_records(params, current_user, db)


# ─────────────── Field Configuration ────────────────────────


@router.get("/sources/{source_id}/fields", response_model=list[schemas.FieldConfigResponse])
def get_field_configs(
    source_id: int,
    current_user=Depends(require_onboarding_complete),
    db: Session = Depends(get_db),
):
    return data_controller.get_field_configs(source_id, current_user, db)


@router.put("/sources/{source_id}/fields", response_model=list[schemas.FieldConfigResponse])
def update_field_configs(
    source_id: int,
    payload: schemas.BulkFieldConfigUpdate,
    current_user=Depends(require_onboarding_complete),
    db: Session = Depends(get_db),
):
    return data_controller.update_field_configs(source_id, payload, current_user, db)


# ─────────────── Email Templates & Sending ──────────────────


@router.get("/email/templates", response_model=list[schemas.EmailTemplateResponse])
def list_email_templates(
    current_user=Depends(require_onboarding_complete),
    db: Session = Depends(get_db),
):
    return data_controller.list_email_templates(current_user, db)


@router.post("/email/templates", response_model=schemas.EmailTemplateResponse, status_code=201)
def create_email_template(
    payload: schemas.EmailTemplateCreate,
    current_user=Depends(require_onboarding_complete),
    db: Session = Depends(get_db),
):
    return data_controller.create_email_template(payload, current_user, db)


@router.delete("/email/templates/{template_id}")
def delete_email_template(
    template_id: int,
    current_user=Depends(require_onboarding_complete),
    db: Session = Depends(get_db),
):
    return data_controller.delete_email_template(template_id, current_user, db)


@router.post("/email/send", response_model=schemas.SendEmailResponse)
async def send_emails(
    payload: schemas.SendEmailRequest,
    current_user=Depends(require_onboarding_complete),
    db: Session = Depends(get_db),
):
    return await data_controller.send_emails(payload, current_user, db)


# ─────────────── Analytics ──────────────────────────────────


@router.post("/analytics", response_model=schemas.AnalyticsResponse)
async def run_analytics(
    payload: schemas.AnalyticsRequest,
    current_user=Depends(require_onboarding_complete),
    db: Session = Depends(get_db),
):
    return await data_controller.run_analytics(payload, current_user, db)


@router.get("/analytics/{source_id}/field/{field_key}")
def field_analytics(
    source_id: int,
    field_key: str,
    current_user=Depends(require_onboarding_complete),
    db: Session = Depends(get_db),
):
    return data_controller.get_field_analytics(source_id, field_key, current_user, db)


# ─────────────── Action History ─────────────────────────────


@router.get("/actions", response_model=list[schemas.ActionLogResponse])
def action_history(
    limit: int = Query(50, ge=1, le=200),
    current_user=Depends(require_onboarding_complete),
    db: Session = Depends(get_db),
):
    return data_controller.get_action_history(current_user, db, limit)
