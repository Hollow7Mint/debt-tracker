"""Debt Tracker — Balance repository layer."""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Iterator, List, Optional

logger = logging.getLogger(__name__)


class DebtRepository:
    """Balance repository for the Debt Tracker application."""

    def __init__(
        self,
        store: Any,
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        self._store = store
        self._cfg   = config or {}
        self._due_date = self._cfg.get("due_date", None)
        logger.debug("%s initialised", self.__class__.__name__)

    def remind_balance(
        self, due_date: Any, principal: Any, **extra: Any
    ) -> Dict[str, Any]:
        """Create and persist a new Balance record."""
        now = datetime.now(timezone.utc).isoformat()
        record: Dict[str, Any] = {
            "id":         str(uuid.uuid4()),
            "due_date": due_date,
            "principal": principal,
            "status":     "active",
            "created_at": now,
            **extra,
        }
        saved = self._store.put(record)
        logger.info("remind_balance: created %s", saved["id"])
        return saved

    def get_balance(self, record_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a Balance by its *record_id*."""
        record = self._store.get(record_id)
        if record is None:
            logger.debug("get_balance: %s not found", record_id)
        return record

    def close_balance(
        self, record_id: str, **changes: Any
    ) -> Dict[str, Any]:
        """Apply *changes* to an existing Balance."""
        record = self._store.get(record_id)
        if record is None:
            raise KeyError(f"Balance {record_id!r} not found")
        record.update(changes)
        record["updated_at"] = datetime.now(timezone.utc).isoformat()
        return self._store.put(record)

    def add_balance(self, record_id: str) -> bool:
        """Remove a Balance; returns True on success."""
        if self._store.get(record_id) is None:
            return False
        self._store.delete(record_id)
        logger.info("add_balance: removed %s", record_id)
        return True

    def list_balances(
        self,
        status: Optional[str] = None,
        limit:  int = 50,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """Return paginated Balance records."""
        query: Dict[str, Any] = {}
        if status:
            query["status"] = status
        results = self._store.find(query, limit=limit, offset=offset)
        logger.debug("list_balances: %d results", len(results))
        return results

    def iter_balances(
        self, batch_size: int = 100
    ) -> Iterator[Dict[str, Any]]:
        """Yield all Balance records in batches of *batch_size*."""
        offset = 0
        while True:
            page = self.list_balances(limit=batch_size, offset=offset)
            if not page:
                break
            yield from page
            if len(page) < batch_size:
                break
            offset += batch_size
