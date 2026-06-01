"""Organization records: fetch external JSON, infer schema, build dynamic table."""

from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional, Set
import httpx

_PREFERRED_COLUMNS = (
    "id",
    "name",
    "first_name",
    "last_name",
    "email",
    "phone",
    "age",
    "gender",
    "city",
    "status",
    "created_at",
    "updated_at",
)

ColumnType = Literal["string", "number", "boolean", "json", "null"]


def _normalize_rows(payload: Any) -> List[Dict[str, Any]]:
    """Extract list-of-dicts from various API response shapes."""
    if isinstance(payload, list):
        return [r for r in payload if isinstance(r, dict)]
    if isinstance(payload, dict):
        # First try common wrapper keys (including nested paths like data.prospects)
        for key in ("data", "users", "records", "results", "items", "payload",
                     "prospects", "members", "contacts", "entries", "list"):
            inner = payload.get(key)
            if isinstance(inner, list):
                return [r for r in inner if isinstance(r, dict)]
            # Handle nested data: {"data": {"prospects": [...]}}
            if isinstance(inner, dict):
                for subkey in ("prospects", "users", "records", "results",
                               "items", "list", "entries", "members", "contacts"):
                    sub_inner = inner.get(subkey)
                    if isinstance(sub_inner, list):
                        return [r for r in sub_inner if isinstance(r, dict)]
        if all(isinstance(v, dict) for v in payload.values()):
            return list(payload.values())
    return []


def _flatten_row(row: Dict[str, Any], prefix: str = "", sep: str = "_") -> Dict[str, Any]:
    """
    Recursively flatten nested dicts into top-level columns.

    Example:
        {"id": 1, "user_detail": {"email": "a@b.com", "first_name": "X"}}
      →
        {"id": 1, "email": "a@b.com", "first_name": "X"}

    If a flattened key would collide with an existing key, it uses the prefixed
    version (e.g. "user_detail_email").
    """
    flat: Dict[str, Any] = {}
    nested_entries: List[tuple] = []  # (full_key, child_key, value)

    for key, value in row.items():
        full_key = f"{prefix}{sep}{key}" if prefix else key

        if isinstance(value, dict) and not isinstance(value, type(None)):
            # Recurse into nested dict
            child = _flatten_row(value, prefix=full_key, sep=sep)
            for ck, cv in child.items():
                # Use the original child key (without parent prefix) if possible
                # e.g. "user_detail_email" → try "email" first
                child_key = ck[len(full_key) + 1:] if ck.startswith(full_key + sep) else ck
                nested_entries.append((ck, child_key, cv))
        elif isinstance(value, list):
            flat[full_key if prefix else key] = _flatten_value(value)
        else:
            flat[full_key if prefix else key] = _flatten_value(value)

    # Merge nested entries — prefer short key unless it collides
    for full_key, child_key, value in nested_entries:
        if child_key and child_key not in flat:
            flat[child_key] = value
        else:
            flat[full_key] = value

    return flat


def _flatten_value(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, (list, dict)):
        import json
        try:
            return json.dumps(value, ensure_ascii=False)
        except (TypeError, ValueError):
            return str(value)
    return str(value)


def _infer_type(values: List[Any]) -> ColumnType:
    non_null = [v for v in values if v is not None and v != ""]
    if not non_null:
        return "null"
    if all(isinstance(v, bool) for v in non_null):
        return "boolean"
    if all(isinstance(v, (int, float)) and not isinstance(v, bool) for v in non_null):
        return "number"
    if all(isinstance(v, str) for v in non_null):
        return "string"
    return "json"


def _labelize(key: str) -> str:
    return key.replace("_", " ").replace("-", " ").title()


def build_column_schema(
    columns: List[str], rows: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    schema: List[Dict[str, Any]] = []
    for col in columns:
        values = [row.get(col) for row in rows]
        col_type = _infer_type(values)
        nullable = any(v is None or v == "" for v in values)
        schema.append(
            {
                "key": col,
                "label": _labelize(col),
                "type": col_type,
                "nullable": nullable,
            }
        )
    return schema


def build_dynamic_table(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    column_set: Set[str] = set()
    normalized_rows: List[Dict[str, Any]] = []

    for row in rows:
        flat = _flatten_row(row)
        normalized_rows.append(flat)
        column_set.update(flat.keys())

    ordered: List[str] = []
    for col in _PREFERRED_COLUMNS:
        if col in column_set:
            ordered.append(col)
            column_set.discard(col)
    ordered.extend(sorted(column_set))

    schema = build_column_schema(ordered, normalized_rows)

    return {
        "columns": ordered,
        "schema": schema,
        "rows": normalized_rows,
        "total": len(normalized_rows),
    }


async def fetch_organization_records(
    api_url: Optional[str],
    api_key: Optional[str] = None,
) -> Dict[str, Any]:
    fetched_at = datetime.now(timezone.utc).isoformat()

    if not api_url or not api_url.strip():
        table = build_dynamic_table(_demo_records())
        return {**table, "source": "demo", "fetched_at": fetched_at}

    headers: Dict[str, str] = {"Accept": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(api_url.strip(), headers=headers)
        response.raise_for_status()
        payload = response.json()

    rows = _normalize_rows(payload)
    if not rows:
        raise ValueError(
            "API response must be a JSON array of objects, or an object with "
            "data/users/records/results/items containing that array."
        )

    table = build_dynamic_table(rows)
    return {**table, "source": "api", "fetched_at": fetched_at}


def _demo_records() -> List[Dict[str, Any]]:
    """Demo: mixed row shapes so column union behaves like real multi-tenant APIs."""
    wide = {f"metric_{i}": i * 100 for i in range(1, 41)}
    wide.update(
        {
            "id": 99,
            "name": "Enterprise Row (40+ extra keys)",
            "email": "enterprise@example.com",
            "segment": "Enterprise",
        }
    )

    return [
        {
            "id": 1,
            "name": "Rahul Sharma",
            "email": "rahul@example.com",
            "department": "Sales",
            "revenue": 120000,
            "active": True,
            "city": "Delhi",
        },
        {
            "id": 2,
            "name": "Priya Patel",
            "email": "priya@example.com",
            "department": "Marketing",
            "campaign_score": 92,
            "city": "Mumbai",
            "social_handle": "@priya",
        },
        {
            "customer_tier": "Gold",
            "lifetime_value": 45000,
            "last_purchase": "2025-11-02",
            "region": "West",
            "loyalty_points": 880,
        },
        wide,
    ]
