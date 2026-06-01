"""Organization records: fetch external JSON, infer schema, build dynamic table."""

from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional, Set
import httpx

_PREFERRED_COLUMNS = (
    "id",
    "name",
    "email",
    "phone",
    "age",
    "city",
    "status",
    "created_at",
    "updated_at",
)

ColumnType = Literal["string", "number", "boolean", "json", "null"]


def _normalize_rows(payload: Any) -> List[Dict[str, Any]]:
    if isinstance(payload, list):
        return [r for r in payload if isinstance(r, dict)]
    if isinstance(payload, dict):
        for key in ("data", "users", "records", "results", "items", "payload"):
            inner = payload.get(key)
            if isinstance(inner, list):
                return [r for r in inner if isinstance(r, dict)]
        if all(isinstance(v, dict) for v in payload.values()):
            return list(payload.values())
    return []


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
        flat = {k: _flatten_value(v) for k, v in row.items()}
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
