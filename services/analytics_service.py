"""
Analytics Service — aggregate, group, and analyze organization data.

Supports:
    - Group-by aggregation (count, sum, avg, min, max)
    - Field-level statistics (distribution, null %, unique values)
    - Summary stats across all data
"""

from collections import Counter, defaultdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

import models


def _safe_numeric(val: Any) -> Optional[float]:
    """Try to convert a value to float."""
    if val is None:
        return None
    if isinstance(val, (int, float)) and not isinstance(val, bool):
        return float(val)
    if isinstance(val, str):
        try:
            return float(val)
        except ValueError:
            return None
    return None


def compute_field_stats(rows: List[Dict[str, Any]], field: str) -> Dict[str, Any]:
    """Compute stats for a single field across all rows."""
    values = [r.get(field) for r in rows]
    total = len(values)
    non_null = [v for v in values if v is not None and v != ""]
    nulls = total - len(non_null)

    stats: Dict[str, Any] = {
        "field": field,
        "total": total,
        "non_null": len(non_null),
        "null_count": nulls,
        "null_pct": round(nulls / total * 100, 1) if total else 0,
    }

    # Numeric stats
    numerics = [_safe_numeric(v) for v in non_null]
    numerics = [n for n in numerics if n is not None]
    if numerics:
        stats["min"] = min(numerics)
        stats["max"] = max(numerics)
        stats["avg"] = round(sum(numerics) / len(numerics), 2)
        stats["sum"] = round(sum(numerics), 2)
        stats["numeric_count"] = len(numerics)

    # Unique values
    str_values = [str(v) for v in non_null]
    unique = set(str_values)
    stats["unique_count"] = len(unique)
    if len(unique) <= 20:
        stats["value_distribution"] = dict(Counter(str_values).most_common(20))

    return stats


def aggregate_data(
    rows: List[Dict[str, Any]],
    group_by: Optional[str] = None,
    aggregate: str = "count",
    aggregate_field: Optional[str] = None,
    filters: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    """Group rows and apply aggregation function."""

    # Apply filters first
    if filters:
        from services.data_pipeline import apply_filters
        rows = apply_filters(rows, filters)

    if not group_by:
        # No grouping — aggregate entire dataset
        val = _aggregate_list(rows, aggregate, aggregate_field)
        return [{"_group": "all", "_value": val, "_count": len(rows)}]

    # Group rows by field value
    groups: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for row in rows:
        key = str(row.get(group_by, "(empty)"))
        groups[key].append(row)

    result = []
    for group_key, group_rows in sorted(groups.items()):
        val = _aggregate_list(group_rows, aggregate, aggregate_field)
        result.append({
            "_group": group_key,
            "_value": val,
            "_count": len(group_rows),
        })

    return result


def _aggregate_list(
    rows: List[Dict[str, Any]], aggregate: str, field: Optional[str],
) -> Any:
    """Apply aggregate function to a list of rows."""
    if aggregate == "count":
        return len(rows)

    if not field:
        return len(rows)

    values = [_safe_numeric(r.get(field)) for r in rows]
    values = [v for v in values if v is not None]

    if not values:
        return 0

    if aggregate == "sum":
        return round(sum(values), 2)
    elif aggregate == "avg":
        return round(sum(values) / len(values), 2)
    elif aggregate == "min":
        return min(values)
    elif aggregate == "max":
        return max(values)
    return len(rows)


def generate_summary(
    rows: List[Dict[str, Any]],
    schema: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Generate overall summary stats for a dataset."""
    if not rows:
        return {"total_rows": 0, "total_columns": 0, "fields": []}

    columns = list(rows[0].keys()) if rows else []
    numeric_cols = [
        s["key"] for s in schema if s.get("type") == "number"
    ]
    string_cols = [
        s["key"] for s in schema if s.get("type") == "string"
    ]

    summary: Dict[str, Any] = {
        "total_rows": len(rows),
        "total_columns": len(columns),
        "numeric_columns": len(numeric_cols),
        "text_columns": len(string_cols),
    }

    # Top-level numeric summaries
    for col in numeric_cols[:10]:   # limit to first 10 numeric cols
        stats = compute_field_stats(rows, col)
        summary[f"{col}_avg"] = stats.get("avg")
        summary[f"{col}_min"] = stats.get("min")
        summary[f"{col}_max"] = stats.get("max")

    return summary


def log_action(
    org_id: int,
    user_id: int,
    action_type: str,
    db: Session,
    source_id: Optional[int] = None,
    action_detail: Optional[Dict[str, Any]] = None,
    status: str = "success",
    result_summary: Optional[str] = None,
) -> models.ActionLog:
    """Write an entry to the action log."""
    log = models.ActionLog(
        org_id=org_id,
        user_id=user_id,
        source_id=source_id,
        action_type=action_type,
        action_detail=action_detail,
        status=status,
        result_summary=result_summary,
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log
