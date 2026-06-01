"""
Data Pipeline Service — fetch, cache, transform, serve organization data.

Architecture:
    External API → Fetch → Normalize → Cache (DB) → Query (filter/sort/paginate) → Response

Supports:
    - Multiple data sources per organization
    - Automatic schema discovery & field config generation
    - TTL-based caching (avoids hitting external APIs on every request)
    - Server-side search, filter, sort, paginate
    - Auto-detection of email/name/phone fields
"""

from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Set
import json
import re

import httpx
from sqlalchemy.orm import Session

import models
from services.records_service import (
    _normalize_rows,
    _flatten_value,
    _infer_type,
    _labelize,
    build_column_schema,
    build_dynamic_table,
    _demo_records,
)

# ──────────────── Email / Name / Phone field heuristics ──────────────

_EMAIL_PATTERNS = re.compile(r"e[-_]?mail|email[-_]?addr", re.IGNORECASE)
_NAME_PATTERNS = re.compile(
    r"^(name|full[-_]?name|display[-_]?name|first[-_]?name|user[-_]?name|contact[-_]?name)$",
    re.IGNORECASE,
)
_PHONE_PATTERNS = re.compile(r"phone|mobile|cell|tel|contact[-_]?number", re.IGNORECASE)


def _guess_email_field(keys: List[str]) -> Optional[str]:
    for k in keys:
        if _EMAIL_PATTERNS.search(k):
            return k
    return None


def _guess_name_field(keys: List[str]) -> Optional[str]:
    for k in keys:
        if _NAME_PATTERNS.search(k):
            return k
    return None


def _guess_phone_field(keys: List[str]) -> Optional[str]:
    for k in keys:
        if _PHONE_PATTERNS.search(k):
            return k
    return None


# ──────────────── JSONPath-like data extraction ──────────────────────


def _extract_by_path(data: Any, path: str) -> Any:
    """Extract nested data using dot-notation path, e.g. 'data.users'."""
    parts = path.split(".")
    current = data
    for part in parts:
        if isinstance(current, dict):
            current = current.get(part)
        elif isinstance(current, list) and part.isdigit():
            idx = int(part)
            current = current[idx] if idx < len(current) else None
        else:
            return None
    return current


# ──────────────── Core: Fetch from external API ─────────────────────


def _build_headers(source: models.DataSource) -> Dict[str, str]:
    """Build HTTP headers from source auth config."""
    headers: Dict[str, str] = {"Accept": "application/json"}

    if source.auth_type == "bearer" and source.auth_value:
        headers["Authorization"] = f"Bearer {source.auth_value}"
    elif source.auth_type == "api_key" and source.auth_value:
        header_name = source.auth_header or "X-API-Key"
        headers[header_name] = source.auth_value
    elif source.auth_type == "header" and source.auth_header and source.auth_value:
        headers[source.auth_header] = source.auth_value

    if source.request_headers:
        headers.update(source.request_headers)

    return headers


def _detect_pagination(payload: Any, data_path: str | None) -> Dict[str, Any] | None:
    """Try to find pagination info in the API response."""
    if not isinstance(payload, dict):
        return None

    # Check common pagination locations
    target = payload
    if data_path:
        # Navigate to parent of data_path (e.g. data_path="data.prospects" → check "data")
        parts = data_path.split(".")
        for part in parts[:-1]:
            if isinstance(target, dict):
                target = target.get(part, {})

    # Look for pagination object
    for key in ("pagination", "paging", "meta", "page_info", "paginate"):
        pag = None
        if isinstance(target, dict):
            pag = target.get(key)
        if not pag and isinstance(payload, dict):
            pag = payload.get(key)
        if isinstance(pag, dict):
            total = pag.get("total") or pag.get("totalRecords") or pag.get("total_count") or pag.get("count")
            total_pages = pag.get("totalPages") or pag.get("total_pages") or pag.get("last_page")
            has_next = pag.get("hasNextPage") or pag.get("has_next_page") or pag.get("has_next") or pag.get("has_more")
            current_page = pag.get("currentPage") or pag.get("current_page") or pag.get("page") or 1
            limit = pag.get("limit") or pag.get("per_page") or pag.get("pageSize") or pag.get("size")
            return {
                "total": int(total) if total else None,
                "total_pages": int(total_pages) if total_pages else None,
                "has_next": bool(has_next),
                "current_page": int(current_page) if current_page else 1,
                "limit": int(limit) if limit else None,
            }
    return None


def _get_page_url(base_url: str, page: int, limit: int) -> str:
    """Build paginated URL by updating/adding page & limit query params."""
    from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
    parsed = urlparse(base_url)
    params = parse_qs(parsed.query, keep_blank_values=True)
    params["page"] = [str(page)]
    params["limit"] = [str(limit)]
    new_query = urlencode(params, doseq=True)
    return urlunparse(parsed._replace(query=new_query))


async def fetch_from_source(
    source: models.DataSource,
    fetch_all_pages: bool = True,
    max_pages: int = 50,
) -> List[Dict[str, Any]]:
    """Fetch data from a DataSource's external API with auto-pagination."""
    headers = _build_headers(source)
    all_rows: List[Dict[str, Any]] = []

    async with httpx.AsyncClient(timeout=30.0) as client:
        # First request
        url = source.api_url.strip()
        if source.http_method == "POST":
            response = await client.post(url, headers=headers, json=source.request_body)
        else:
            response = await client.get(url, headers=headers)
        response.raise_for_status()
        payload = response.json()

        # Extract data using data_path
        data_payload = payload
        if source.data_path:
            data_payload = _extract_by_path(payload, source.data_path)
            if data_payload is None:
                raise ValueError(f"data_path '{source.data_path}' returned no data")

        rows = _normalize_rows(data_payload)
        if not rows:
            raise ValueError(
                "API response must be a JSON array of objects or an object "
                "containing a data array."
            )
        all_rows.extend(rows)

        # Auto-paginate if API has pagination
        if fetch_all_pages:
            pag = _detect_pagination(payload, source.data_path)
            if pag and pag.get("has_next") and pag.get("total_pages"):
                limit = pag.get("limit") or len(rows)
                current = pag.get("current_page", 1)
                total_pages = min(pag["total_pages"], max_pages)

                for page_num in range(current + 1, total_pages + 1):
                    page_url = _get_page_url(source.api_url.strip(), page_num, limit)
                    try:
                        if source.http_method == "POST":
                            resp = await client.post(page_url, headers=headers, json=source.request_body)
                        else:
                            resp = await client.get(page_url, headers=headers)
                        resp.raise_for_status()
                        page_payload = resp.json()

                        page_data = page_payload
                        if source.data_path:
                            page_data = _extract_by_path(page_payload, source.data_path)
                        page_rows = _normalize_rows(page_data) if page_data else []
                        if page_rows:
                            all_rows.extend(page_rows)
                        else:
                            break  # No more data
                    except Exception:
                        break  # Stop on error, return what we have

    return all_rows


# ──────────────── Cache Management ──────────────────────────────────


def get_cached_data(source: models.DataSource, db: Session) -> Optional[models.DataCache]:
    """Return cached data if it exists and hasn't expired."""
    cache = db.query(models.DataCache).filter(
        models.DataCache.source_id == source.id,
    ).first()

    if not cache:
        return None

    now = datetime.now(timezone.utc)
    expires = cache.expires_at.replace(tzinfo=timezone.utc) if cache.expires_at.tzinfo is None else cache.expires_at
    if now > expires:
        return None   # expired

    return cache


def save_to_cache(
    source: models.DataSource,
    rows: List[Dict[str, Any]],
    schema: List[Dict[str, Any]],
    db: Session,
) -> models.DataCache:
    """Upsert cached data for a data source."""
    now = datetime.now(timezone.utc)
    expires = now + timedelta(seconds=source.refresh_interval)

    cache = db.query(models.DataCache).filter(
        models.DataCache.source_id == source.id,
    ).first()

    if cache:
        cache.raw_data = rows
        cache.schema_snapshot = schema
        cache.row_count = len(rows)
        cache.fetched_at = now
        cache.expires_at = expires
    else:
        cache = models.DataCache(
            source_id=source.id,
            raw_data=rows,
            schema_snapshot=schema,
            row_count=len(rows),
            fetched_at=now,
            expires_at=expires,
        )
        db.add(cache)

    db.commit()
    db.refresh(cache)
    return cache


# ──────────────── Auto-generate FieldConfigs ────────────────────────


def auto_generate_field_configs(
    source: models.DataSource,
    columns: List[str],
    schema: List[Dict[str, Any]],
    db: Session,
) -> None:
    """Create FieldConfig entries for newly discovered fields."""
    existing_keys = {
        fc.field_key
        for fc in db.query(models.FieldConfig).filter(
            models.FieldConfig.source_id == source.id,
        ).all()
    }

    email_field = _guess_email_field(columns)
    name_field = _guess_name_field(columns)
    phone_field = _guess_phone_field(columns)

    schema_map = {s["key"]: s for s in schema}

    for order, col in enumerate(columns):
        if col in existing_keys:
            continue
        col_schema = schema_map.get(col, {})
        fc = models.FieldConfig(
            source_id=source.id,
            field_key=col,
            display_label=_labelize(col),
            field_type=col_schema.get("type", "string"),
            is_visible=True,
            is_searchable=True,
            is_sortable=True,
            is_filterable=True,
            display_order=order,
            is_email_field=(col == email_field),
            is_name_field=(col == name_field),
            is_phone_field=(col == phone_field),
        )
        db.add(fc)

    db.commit()


# ──────────────── Query Engine (filter / sort / search / paginate) ──


def apply_search(rows: List[Dict[str, Any]], search: str, searchable_keys: Set[str]) -> List[Dict[str, Any]]:
    """Full-text search across searchable fields."""
    term = search.lower()
    result = []
    for row in rows:
        for key in searchable_keys:
            val = row.get(key)
            if val is not None and term in str(val).lower():
                result.append(row)
                break
    return result


def apply_filters(rows: List[Dict[str, Any]], filters: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Apply field-level filters. Supports: exact match, gt/lt/gte/lte, contains."""
    result = []
    for row in rows:
        match = True
        for field, condition in filters.items():
            val = row.get(field)
            if isinstance(condition, dict):
                # Operator-based: {"gt": 10, "lt": 50}
                for op, target in condition.items():
                    if op == "gt" and not (val is not None and val > target):
                        match = False
                    elif op == "lt" and not (val is not None and val < target):
                        match = False
                    elif op == "gte" and not (val is not None and val >= target):
                        match = False
                    elif op == "lte" and not (val is not None and val <= target):
                        match = False
                    elif op == "contains" and not (val is not None and str(target).lower() in str(val).lower()):
                        match = False
                    elif op == "ne" and val == target:
                        match = False
            else:
                # Exact match
                if str(val).lower() != str(condition).lower():
                    match = False
            if not match:
                break
        if match:
            result.append(row)
    return result


def apply_sort(rows: List[Dict[str, Any]], sort_by: str, sort_order: str) -> List[Dict[str, Any]]:
    """Sort rows by a field."""
    reverse = sort_order == "desc"
    return sorted(
        rows,
        key=lambda r: (r.get(sort_by) is None, r.get(sort_by, "")),
        reverse=reverse,
    )


def paginate(rows: List[Dict[str, Any]], page: int, page_size: int) -> List[Dict[str, Any]]:
    """Return a page slice."""
    start = (page - 1) * page_size
    return rows[start : start + page_size]


# ──────────────── Main Pipeline Orchestrator ────────────────────────


async def get_source_data(
    source: models.DataSource,
    db: Session,
    search: Optional[str] = None,
    sort_by: Optional[str] = None,
    sort_order: str = "asc",
    page: int = 1,
    page_size: int = 50,
    filters: Optional[Dict[str, Any]] = None,
    force_refresh: bool = False,
) -> Dict[str, Any]:
    """Full pipeline: cache check → fetch if needed → query → paginated response."""

    is_cached = False
    fetched_at = datetime.now(timezone.utc).isoformat()

    # 1) Try cache
    cache = None if force_refresh else get_cached_data(source, db)

    if cache:
        rows = cache.raw_data
        schema = cache.schema_snapshot
        is_cached = True
        fetched_at = cache.fetched_at.isoformat() if cache.fetched_at else fetched_at
        cache_expires = cache.expires_at.isoformat() if cache.expires_at else None
    else:
        # 2) Fetch from external API
        raw_rows = await fetch_from_source(source)
        table = build_dynamic_table(raw_rows)
        rows = table["rows"]
        schema = table["schema"]
        columns = table["columns"]
        cache_expires = None

        # 3) Save to cache
        saved_cache = save_to_cache(source, rows, schema, db)
        cache_expires = saved_cache.expires_at.isoformat() if saved_cache.expires_at else None

        # 4) Auto-generate field configs for new fields
        auto_generate_field_configs(source, columns, schema, db)

    # Load field configs
    field_configs = db.query(models.FieldConfig).filter(
        models.FieldConfig.source_id == source.id,
    ).order_by(models.FieldConfig.display_order).all()

    # Build searchable / visible sets
    searchable_keys = {fc.field_key for fc in field_configs if fc.is_searchable}
    visible_keys = [fc.field_key for fc in field_configs if fc.is_visible]

    # If no field configs yet, use all columns
    if not field_configs:
        all_keys = set()
        for row in rows[:1]:
            all_keys.update(row.keys())
        searchable_keys = all_keys
        visible_keys = list(all_keys)

    # 5) Apply search
    if search:
        rows = apply_search(rows, search, searchable_keys)

    # 6) Apply filters
    if filters:
        rows = apply_filters(rows, filters)

    total = len(rows)

    # 7) Sort
    if sort_by:
        rows = apply_sort(rows, sort_by, sort_order)

    # 8) Paginate
    total_pages = max(1, (total + page_size - 1) // page_size)
    paged_rows = paginate(rows, page, page_size)

    # Filter columns to visible only
    visible_schema = [s for s in schema if s["key"] in visible_keys]
    display_columns = [k for k in visible_keys if any(s["key"] == k for s in schema)]

    return {
        "columns": display_columns,
        "schema_info": visible_schema,
        "rows": paged_rows,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
        "source_id": source.id,
        "source_name": source.name,
        "fetched_at": fetched_at,
        "is_cached": is_cached,
        "cache_expires_at": cache_expires,
    }


# ──────────────── Backward Compatibility (legacy org records) ───────


async def get_legacy_org_records(
    org: models.Organization, db: Session,
) -> Dict[str, Any]:
    """
    Backward-compatible: if org has no DataSources yet but has api_url,
    create a default DataSource and route through the pipeline.
    """
    # Check if org already has data sources
    source = db.query(models.DataSource).filter(
        models.DataSource.org_id == org.id,
    ).first()

    if not source and org.api_url:
        # Auto-migrate: create a DataSource from the org's api_url
        source = models.DataSource(
            org_id=org.id,
            name=f"{org.name} — Primary API",
            api_url=org.api_url,
            auth_type="bearer" if org.api_key else "none",
            auth_value=org.api_key,
            refresh_interval=300,
            is_active=True,
        )
        db.add(source)
        db.commit()
        db.refresh(source)

    if source:
        return await get_source_data(source, db)

    # No API configured — return demo data
    from services.records_service import fetch_organization_records
    return await fetch_organization_records(None, None)


def get_all_sources_summary(org_id: int, db: Session) -> Dict[str, Any]:
    """Summary of all data sources for an organization."""
    sources = db.query(models.DataSource).filter(
        models.DataSource.org_id == org_id,
    ).all()

    source_list = []
    total_records = 0

    for src in sources:
        cache = db.query(models.DataCache).filter(
            models.DataCache.source_id == src.id,
        ).first()

        row_count = cache.row_count if cache else 0
        columns = len(cache.schema_snapshot) if cache and cache.schema_snapshot else 0
        last_fetched = cache.fetched_at.isoformat() if cache and cache.fetched_at else None

        total_records += row_count
        source_list.append({
            "id": src.id,
            "name": src.name,
            "description": src.description,
            "api_url": src.api_url,
            "is_active": src.is_active,
            "row_count": row_count,
            "columns": columns,
            "last_fetched": last_fetched,
            "refresh_interval": src.refresh_interval,
        })

    return {
        "sources": source_list,
        "total_sources": len(sources),
        "total_records": total_records,
    }
