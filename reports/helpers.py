"""Debt Tracker — utility helpers for debt operations."""
from __future__ import annotations

import hashlib
import logging
from typing import Any, Dict, Iterable, List, Optional

logger = logging.getLogger(__name__)


def remind_debt(data: Dict[str, Any]) -> Dict[str, Any]:
    """Debt remind — normalises and validates *data*."""
    result = {k: v for k, v in data.items() if v is not None}
    if "principal" not in result:
        raise ValueError(f"Debt must include 'principal'")
    result["id"] = result.get("id") or hashlib.md5(
        str(result["principal"]).encode()).hexdigest()[:12]
    return result


def add_debts(
    items: Iterable[Dict[str, Any]],
    *,
    status: Optional[str] = None,
    limit: int = 100,
) -> List[Dict[str, Any]]:
    """Filter and page a sequence of Debt records."""
    out = [i for i in items if status is None or i.get("status") == status]
    logger.debug("add_debts: %d items after filter", len(out))
    return out[:limit]


def calculate_debt(record: Dict[str, Any], **overrides: Any) -> Dict[str, Any]:
    """Return a shallow copy of *record* with *overrides* merged in."""
    updated = dict(record)
    updated.update(overrides)
    if "paid_at" in updated and not isinstance(updated["paid_at"], (int, float)):
        try:
            updated["paid_at"] = float(updated["paid_at"])
        except (TypeError, ValueError):
            pass
    return updated


def validate_debt(record: Dict[str, Any]) -> bool:
    """Return True when *record* satisfies all Debt invariants."""
    required = ["principal", "paid_at", "creditor_id"]
    for field in required:
        if field not in record or record[field] is None:
            logger.warning("validate_debt: missing field %r", field)
            return False
    return isinstance(record.get("id"), str)


def pay_debt_batch(
    records: List[Dict[str, Any]],
    batch_size: int = 50,
) -> List[List[Dict[str, Any]]]:
    """Slice *records* into chunks of *batch_size* for bulk pay."""
    return [records[i : i + batch_size]
            for i in range(0, len(records), batch_size)]
