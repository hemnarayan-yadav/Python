"""
Data Controller — manages data sources, records pipeline, email, analytics.
"""

from typing import Any, Dict, List, Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

import models
import schemas
from services.data_pipeline import (
    get_source_data,
    get_all_sources_summary,
    get_cached_data,
    fetch_from_source,
    save_to_cache,
    build_dynamic_table,
    auto_generate_field_configs,
)
from services.email_service import (
    create_template,
    get_templates,
    get_template,
    delete_template,
    send_bulk_email,
    get_email_logs,
    render_template,
)
from services.analytics_service import (
    aggregate_data,
    compute_field_stats,
    generate_summary,
    log_action,
)


# ═══════════════════════ DATA SOURCES ════════════════════════


def list_sources(user: models.User, db: Session) -> List[schemas.DataSourceResponse]:
    org = _require_org(user)
    sources = db.query(models.DataSource).filter(
        models.DataSource.org_id == org.id,
    ).order_by(models.DataSource.created_at).all()
    return [_source_response(s) for s in sources]


def create_source(
    payload: schemas.DataSourceCreate, user: models.User, db: Session,
) -> schemas.DataSourceResponse:
    org = _require_org(user)

    source = models.DataSource(
        org_id=org.id,
        name=payload.name,
        description=payload.description,
        api_url=payload.api_url,
        auth_type=payload.auth_type,
        auth_value=payload.auth_value,
        auth_header=payload.auth_header,
        http_method=payload.http_method,
        request_headers=payload.request_headers,
        request_body=payload.request_body,
        data_path=payload.data_path,
        refresh_interval=payload.refresh_interval,
        is_active=True,
    )
    db.add(source)
    db.commit()
    db.refresh(source)

    log_action(org.id, user.id, "create_source", db, source_id=source.id,
               action_detail={"name": source.name, "api_url": source.api_url})

    return _source_response(source)


def update_source(
    source_id: int, payload: schemas.DataSourceUpdate, user: models.User, db: Session,
) -> schemas.DataSourceResponse:
    source = _require_source(source_id, user, db)

    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(source, key, value)

    db.commit()
    db.refresh(source)
    return _source_response(source)


def delete_source(source_id: int, user: models.User, db: Session) -> dict:
    source = _require_source(source_id, user, db)
    db.delete(source)
    db.commit()
    return {"detail": "Data source deleted"}


def get_sources_summary(user: models.User, db: Session) -> schemas.MultiSourceSummary:
    org = _require_org(user)
    summary = get_all_sources_summary(org.id, db)
    return schemas.MultiSourceSummary(**summary)


# ═══════════════════════ RECORDS (PIPELINE) ══════════════════


async def query_records(
    params: schemas.DataQueryParams, user: models.User, db: Session,
) -> schemas.PaginatedRecordsResponse:
    org = _require_org(user)

    if params.source_id:
        source = _require_source(params.source_id, user, db)
    else:
        # Default: first active source
        source = db.query(models.DataSource).filter(
            models.DataSource.org_id == org.id,
            models.DataSource.is_active == True,
        ).first()
        if not source:
            raise HTTPException(404, "No data sources configured")

    try:
        result = await get_source_data(
            source, db,
            search=params.search,
            sort_by=params.sort_by,
            sort_order=params.sort_order,
            page=params.page,
            page_size=params.page_size,
            filters=params.filters,
            force_refresh=params.force_refresh,
        )
    except Exception as exc:
        log_action(org.id, user.id, "fetch", db, source_id=source.id,
                   status="failed", result_summary=str(exc))
        raise HTTPException(502, f"Failed to fetch from data source: {exc}") from exc

    log_action(org.id, user.id, "fetch", db, source_id=source.id,
               action_detail={"search": params.search, "page": params.page, "cached": result["is_cached"]})

    return schemas.PaginatedRecordsResponse(**result)


async def refresh_source(source_id: int, user: models.User, db: Session) -> dict:
    source = _require_source(source_id, user, db)
    try:
        raw_rows = await fetch_from_source(source)
        table = build_dynamic_table(raw_rows)
        save_to_cache(source, table["rows"], table["schema"], db)
        auto_generate_field_configs(source, table["columns"], table["schema"], db)
    except Exception as exc:
        raise HTTPException(502, f"Refresh failed: {exc}") from exc

    return {"detail": "Source refreshed", "row_count": table["total"]}


# ═══════════════════════ FIELD CONFIG ════════════════════════


def get_field_configs(source_id: int, user: models.User, db: Session) -> List[schemas.FieldConfigResponse]:
    source = _require_source(source_id, user, db)
    configs = db.query(models.FieldConfig).filter(
        models.FieldConfig.source_id == source.id,
    ).order_by(models.FieldConfig.display_order).all()
    return [schemas.FieldConfigResponse.model_validate(fc) for fc in configs]


def update_field_configs(
    source_id: int, payload: schemas.BulkFieldConfigUpdate, user: models.User, db: Session,
) -> List[schemas.FieldConfigResponse]:
    source = _require_source(source_id, user, db)

    for cfg in payload.configs:
        field_key = cfg.pop("field_key", None)
        if not field_key:
            continue
        fc = db.query(models.FieldConfig).filter(
            models.FieldConfig.source_id == source.id,
            models.FieldConfig.field_key == field_key,
        ).first()
        if fc:
            for key, value in cfg.items():
                if hasattr(fc, key):
                    setattr(fc, key, value)

    db.commit()
    return get_field_configs(source_id, user, db)


# ═══════════════════════ EMAIL ═══════════════════════════════


def list_email_templates(user: models.User, db: Session) -> List[schemas.EmailTemplateResponse]:
    org = _require_org(user)
    templates = get_templates(org.id, db)
    return [schemas.EmailTemplateResponse.model_validate(t) for t in templates]


def create_email_template(
    payload: schemas.EmailTemplateCreate, user: models.User, db: Session,
) -> schemas.EmailTemplateResponse:
    org = _require_org(user)
    template = create_template(org.id, payload.name, payload.subject, payload.body_html, db)
    return schemas.EmailTemplateResponse.model_validate(template)


def delete_email_template(template_id: int, user: models.User, db: Session) -> dict:
    org = _require_org(user)
    if not delete_template(template_id, org.id, db):
        raise HTTPException(404, "Template not found")
    return {"detail": "Template deleted"}


async def send_emails(
    payload: schemas.SendEmailRequest, user: models.User, db: Session,
) -> schemas.SendEmailResponse:
    org = _require_org(user)
    source = _require_source(payload.source_id, user, db)

    # Get cached data
    cache = get_cached_data(source, db)
    if not cache:
        raise HTTPException(400, "No cached data. Fetch records first.")

    rows = cache.raw_data

    # Filter rows if specified
    if payload.row_ids is not None:
        rows = [rows[i] for i in payload.row_ids if i < len(rows)]
    elif payload.filters:
        from services.data_pipeline import apply_filters
        rows = apply_filters(rows, payload.filters)

    if not rows:
        raise HTTPException(400, "No matching rows to send emails to")

    # Determine email & name fields
    email_field = payload.email_field
    name_field = payload.name_field

    if not email_field:
        field_configs = db.query(models.FieldConfig).filter(
            models.FieldConfig.source_id == source.id,
            models.FieldConfig.is_email_field == True,
        ).first()
        email_field = field_configs.field_key if field_configs else None

    if not email_field:
        raise HTTPException(400, "No email field specified or auto-detected")

    if not name_field:
        field_configs = db.query(models.FieldConfig).filter(
            models.FieldConfig.source_id == source.id,
            models.FieldConfig.is_name_field == True,
        ).first()
        name_field = field_configs.field_key if field_configs else None

    # Template or inline
    subject = payload.subject or ""
    body = payload.body_html or ""
    template_id = None

    if payload.template_id:
        template = get_template(payload.template_id, org.id, db)
        if not template:
            raise HTTPException(404, "Email template not found")
        subject = template.subject
        body = template.body_html
        template_id = template.id

    if not subject or not body:
        raise HTTPException(400, "Subject and body required (inline or via template)")

    result = send_bulk_email(
        org.id, user.id, source.id, rows,
        email_field, name_field, subject, body, db, template_id,
    )

    log_action(org.id, user.id, "email", db, source_id=source.id,
               action_detail={"recipients": result["total_recipients"]},
               result_summary=f"Sent: {result['queued']}, Failed: {result['failed']}")

    return schemas.SendEmailResponse(**result)


# ═══════════════════════ ANALYTICS ═══════════════════════════


async def run_analytics(
    payload: schemas.AnalyticsRequest, user: models.User, db: Session,
) -> schemas.AnalyticsResponse:
    org = _require_org(user)
    source = _require_source(payload.source_id, user, db)

    cache = get_cached_data(source, db)
    if not cache:
        raise HTTPException(400, "No cached data. Fetch records first.")

    rows = cache.raw_data
    schema = cache.schema_snapshot

    result = aggregate_data(
        rows,
        group_by=payload.group_by,
        aggregate=payload.aggregate or "count",
        aggregate_field=payload.aggregate_field,
        filters=payload.filters,
    )

    summary = generate_summary(rows, schema)

    log_action(org.id, user.id, "analysis", db, source_id=source.id,
               action_detail={"group_by": payload.group_by, "aggregate": payload.aggregate})

    return schemas.AnalyticsResponse(
        source_id=source.id,
        source_name=source.name,
        result=result,
        summary=summary,
        generated_at=__import__("datetime").datetime.now(
            __import__("datetime").timezone.utc
        ).isoformat(),
    )


def get_field_analytics(
    source_id: int, field_key: str, user: models.User, db: Session,
) -> Dict[str, Any]:
    source = _require_source(source_id, user, db)
    cache = get_cached_data(source, db)
    if not cache:
        raise HTTPException(400, "No cached data. Fetch records first.")

    return compute_field_stats(cache.raw_data, field_key)


def get_action_history(
    user: models.User, db: Session, limit: int = 50,
) -> List[schemas.ActionLogResponse]:
    org = _require_org(user)
    logs = db.query(models.ActionLog).filter(
        models.ActionLog.org_id == org.id,
    ).order_by(models.ActionLog.created_at.desc()).limit(limit).all()
    return [schemas.ActionLogResponse.model_validate(log) for log in logs]


# ═══════════════════════ HELPERS ═════════════════════════════


def _require_org(user: models.User) -> models.Organization:
    if not user.organization:
        raise HTTPException(404, "Organization not found")
    return user.organization


def _require_source(source_id: int, user: models.User, db: Session) -> models.DataSource:
    org = _require_org(user)
    source = db.query(models.DataSource).filter(
        models.DataSource.id == source_id,
        models.DataSource.org_id == org.id,
    ).first()
    if not source:
        raise HTTPException(404, "Data source not found")
    return source


def _source_response(source: models.DataSource) -> schemas.DataSourceResponse:
    return schemas.DataSourceResponse(
        id=source.id,
        org_id=source.org_id,
        name=source.name,
        description=source.description,
        api_url=source.api_url,
        auth_type=source.auth_type,
        has_auth=bool(source.auth_value),
        auth_header=source.auth_header,
        http_method=source.http_method,
        request_headers=source.request_headers,
        data_path=source.data_path,
        refresh_interval=source.refresh_interval,
        is_active=source.is_active,
        created_at=source.created_at,
        updated_at=source.updated_at,
    )
