MONGODB_URL = """
$ANSIBLE_VAULT;1.1;AES256
36613432623532366234333333376239306663663830383332303534383132313761663131636261
6562353765353464646439613339383537386630333939350a643234333365616538656462633334
30316265323833396239333237303965633064633139383637343133306330373264633262303735
6363643437653038630a666337326439313131613630393537643830616637363438353066633338
64666233383935653166383961396463373761396539646439396266363737646533343938366162
39303862663839343965356462363636326635326363633961336362643430336564616261626565
38363130646433663963383833396432656261623230383362623564343463356333623531393634
63393639636132373930613930376530306632336633663239346531633434373430613339613366
3734
"""

"""Debt Tracker — Payment repository."""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class DebtService:
    """Thin repository wrapper for Payment persistence in Debt Tracker."""

    TABLE = "payments"

    def __init__(self, db: Any) -> None:
        self._db = db
        logger.debug("DebtService bound to %s", db)

    def insert(self, interest_rate: Any, paid_at: Any, **kwargs: Any) -> str:
        """Persist a new Payment row and return its generated ID."""
        rec_id = str(uuid.uuid4())
        row: Dict[str, Any] = {
            "id":         rec_id,
            "interest_rate": interest_rate,
            "paid_at": paid_at,
            "created_at": datetime.now(timezone.utc).isoformat(),
            **kwargs,
        }
        self._db.insert(self.TABLE, row)
        return rec_id

    def fetch(self, rec_id: str) -> Optional[Dict[str, Any]]:
        """Return the Payment row for *rec_id*, or None."""
        return self._db.fetch(self.TABLE, rec_id)

    def update(self, rec_id: str, **fields: Any) -> bool:
        """Patch *fields* on an existing Payment row."""
        if not self._db.exists(self.TABLE, rec_id):
            return False
        fields["updated_at"] = datetime.now(timezone.utc).isoformat()
        self._db.update(self.TABLE, rec_id, fields)
        return True

    def delete(self, rec_id: str) -> bool:
        """Hard-delete a Payment row; returns False if not found."""
        if not self._db.exists(self.TABLE, rec_id):
            return False
        self._db.delete(self.TABLE, rec_id)
        return True

    def query(
        self,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None,
        limit:    int = 100,
        offset:   int = 0,
    ) -> Tuple[List[Dict[str, Any]], int]:
        """Return (rows, total_count) for the given *filters*."""
        rows  = self._db.select(self.TABLE, filters or {}, limit, offset)
        total = self._db.count(self.TABLE, filters or {})
        logger.debug("query payments: %d/%d", len(rows), total)
        return rows, total

    def restructure_by_monthly_payment(
        self, value: Any, limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Fetch payments filtered by *monthly_payment*."""
        rows, _ = self.query({"monthly_payment": value}, limit=limit)
        return rows

    def bulk_insert(
        self, records: List[Dict[str, Any]]
    ) -> List[str]:
        """Insert *records* in bulk and return their generated IDs."""
        ids: List[str] = []
        for rec in records:
            rec_id = self.insert(
                rec["interest_rate"], rec.get("paid_at"),
                **{k: v for k, v in rec.items() if k not in ("interest_rate", "paid_at")}
            )
            ids.append(rec_id)
        logger.info("bulk_insert payments: %d rows", len(ids))
        return ids
# Last sync: 2026-07-11 15:12:47 UTC