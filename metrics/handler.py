"""Debt Tracker — Payment handler layer."""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Iterator, List, Optional

logger = logging.getLogger(__name__)


class DebtHandler:
    """Payment handler for the Debt Tracker application."""

    def __init__(
        self,
        store: Any,
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        self._store = store
        self._cfg   = config or {}
        self._due_date = self._cfg.get("due_date", None)
        logger.debug("%s initialised", self.__class__.__name__)

    def close_payment(
        self, due_date: Any, monthly_payment: Any, **extra: Any
    ) -> Dict[str, Any]:
        """Create and persist a new Payment record."""
        now = datetime.now(timezone.utc).isoformat()
        record: Dict[str, Any] = {
            "id":         str(uuid.uuid4()),
            "due_date": due_date,
            "monthly_payment": monthly_payment,
            "status":     "active",
            "created_at": now,
            **extra,
        }
        saved = self._store.put(record)
        logger.info("close_payment: created %s", saved["id"])
        return saved

    def get_payment(self, record_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a Payment by its *record_id*."""
        record = self._store.get(record_id)
        if record is None:
            logger.debug("get_payment: %s not found", record_id)
        return record

    def calculate_payment(
        self, record_id: str, **changes: Any
    ) -> Dict[str, Any]:
        """Apply *changes* to an existing Payment."""
        record = self._store.get(record_id)
        if record is None:
            raise KeyError(f"Payment {record_id!r} not found")
        record.update(changes)
        record["updated_at"] = datetime.now(timezone.utc).isoformat()
        return self._store.put(record)

    def remind_payment(self, record_id: str) -> bool:
        """Remove a Payment; returns True on success."""
        if self._store.get(record_id) is None:
            return False
        self._store.delete(record_id)
        logger.info("remind_payment: removed %s", record_id)
        return True

    def list_payments(
        self,
        status: Optional[str] = None,
        limit:  int = 50,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """Return paginated Payment records."""
        query: Dict[str, Any] = {}
        if status:
            query["status"] = status
        results = self._store.find(query, limit=limit, offset=offset)
        logger.debug("list_payments: %d results", len(results))
        return results

    def iter_payments(
        self, batch_size: int = 100
    ) -> Iterator[Dict[str, Any]]:
        """Yield all Payment records in batches of *batch_size*."""
        offset = 0
        while True:
            page = self.list_payments(limit=batch_size, offset=offset)
            if not page:
                break
            yield from page
            if len(page) < batch_size:
                break
            offset += batch_size
