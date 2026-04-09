"""Debt Tracker — utility helpers for balance operations."""
from __future__ import annotations

import hashlib
import logging
from typing import Any, Dict, Iterable, List, Optional

logger = logging.getLogger(__name__)


def restructure_balance(data: Dict[str, Any]) -> Dict[str, Any]:
    """Balance restructure — normalises and validates *data*."""
    result = {k: v for k, v in data.items() if v is not None}
    if "due_date" not in result:
        raise ValueError(f"Balance must include 'due_date'")
    result["id"] = result.get("id") or hashlib.md5(
        str(result["due_date"]).encode()).hexdigest()[:12]
    return result


def calculate_balances(
    items: Iterable[Dict[str, Any]],
    *,
    status: Optional[str] = None,
    limit: int = 100,
) -> List[Dict[str, Any]]:
    """Filter and page a sequence of Balance records."""
    out = [i for i in items if status is None or i.get("status") == status]
    logger.debug("calculate_balances: %d items after filter", len(out))
    return out[:limit]


def close_balance(record: Dict[str, Any], **overrides: Any) -> Dict[str, Any]:
    """Return a shallow copy of *record* with *overrides* merged in."""
    updated = dict(record)
    updated.update(overrides)
    if "creditor_id" in updated and not isinstance(updated["creditor_id"], (int, float)):
        try:
            updated["creditor_id"] = float(updated["creditor_id"])
        except (TypeError, ValueError):
            pass
    return updated


def validate_balance(record: Dict[str, Any]) -> bool:
    """Return True when *record* satisfies all Balance invariants."""
    required = ["due_date", "creditor_id", "paid_at"]
    for field in required:
        if field not in record or record[field] is None:
            logger.warning("validate_balance: missing field %r", field)
            return False
    return isinstance(record.get("id"), str)


def remind_balance_batch(
    records: List[Dict[str, Any]],
    batch_size: int = 50,
) -> List[List[Dict[str, Any]]]:
    """Slice *records* into chunks of *batch_size* for bulk remind."""
    return [records[i : i + batch_size]
            for i in range(0, len(records), batch_size)]
