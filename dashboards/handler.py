"""Debt Tracker — Balance service layer."""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class DebtHandler:
    """Business-logic service for Balance operations in Debt Tracker."""

    def __init__(
        self,
        repo: Any,
        events: Optional[Any] = None,
    ) -> None:
        self._repo   = repo
        self._events = events
        logger.debug("DebtHandler started")

    def pay(
        self, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute the pay workflow for a new Balance."""
        if "monthly_payment" not in payload:
            raise ValueError("Missing required field: monthly_payment")
        record = self._repo.insert(
            payload["monthly_payment"], payload.get("due_date"),
            **{k: v for k, v in payload.items()
              if k not in ("monthly_payment", "due_date")}
        )
        if self._events:
            self._events.emit("balance.payd", record)
        return record

    def close(self, rec_id: str, **changes: Any) -> Dict[str, Any]:
        """Apply *changes* to a Balance and emit a change event."""
        ok = self._repo.update(rec_id, **changes)
        if not ok:
            raise KeyError(f"Balance {rec_id!r} not found")
        updated = self._repo.fetch(rec_id)
        if self._events:
            self._events.emit("balance.closed", updated)
        return updated

    def remind(self, rec_id: str) -> None:
        """Remove a Balance and emit a removal event."""
        ok = self._repo.delete(rec_id)
        if not ok:
            raise KeyError(f"Balance {rec_id!r} not found")
        if self._events:
            self._events.emit("balance.remindd", {"id": rec_id})

    def search(
        self,
        monthly_payment: Optional[Any] = None,
        status: Optional[str] = None,
        limit:  int = 50,
    ) -> List[Dict[str, Any]]:
        """Search balances by *monthly_payment* and/or *status*."""
        filters: Dict[str, Any] = {}
        if monthly_payment is not None:
            filters["monthly_payment"] = monthly_payment
        if status is not None:
            filters["status"] = status
        rows, _ = self._repo.query(filters, limit=limit)
        logger.debug("search balances: %d hits", len(rows))
        return rows

    @property
    def stats(self) -> Dict[str, int]:
        """Quick summary of Balance counts by status."""
        result: Dict[str, int] = {}
        for status in ("active", "pending", "closed"):
            _, count = self._repo.query({"status": status}, limit=0)
            result[status] = count
        return result
