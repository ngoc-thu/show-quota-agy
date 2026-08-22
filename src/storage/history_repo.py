"""Repository for storing and querying historical quota snapshots."""

from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional
from .db import DatabaseManager
from ..core.models import QuotaSnapshot, QuotaInfo


class HistoryRepository:
    """Stores historical quota samples in SQLite for timeline analytics."""

    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

    def record_snapshot(self, snapshot: QuotaSnapshot):
        """Inserts quota data points from a snapshot."""
        if not snapshot.models:
            return

        ts_iso = snapshot.timestamp.isoformat()
        records = []
        for mid, minfo in snapshot.models.items():
            records.append(
                (
                    ts_iso,
                    minfo.model_id,
                    minfo.model_name,
                    minfo.percentage,
                    minfo.remaining_fraction,
                    minfo.reset_time_iso,
                    minfo.category,
                )
            )

        with self.db_manager.get_connection() as conn:
            conn.executemany(
                """
                INSERT INTO quota_history (
                    timestamp, model_id, model_name, percentage, remaining_fraction, reset_at, group_name
                ) VALUES (?, ?, ?, ?, ?, ?, ?);
                """,
                records,
            )
            conn.commit()

    def get_history(
        self,
        hours: float = 24.0,
        model_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Returns historical entries recorded within the last N hours."""
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
        cutoff_iso = cutoff.isoformat()

        query = "SELECT * FROM quota_history WHERE timestamp >= ?"
        params: List[Any] = [cutoff_iso]

        if model_id:
            query += " AND model_id = ?"
            params.append(model_id)

        query += " ORDER BY timestamp ASC;"

        with self.db_manager.get_connection() as conn:
            cursor = conn.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    def get_distinct_models(self) -> List[Dict[str, str]]:
        """Returns distinct model_ids and their latest model_name."""
        with self.db_manager.get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT model_id, model_name, MAX(timestamp) as last_seen 
                FROM quota_history 
                GROUP BY model_id 
                ORDER BY last_seen DESC;
                """
            )
            return [{"model_id": row["model_id"], "model_name": row["model_name"]} for row in cursor.fetchall()]

    def purge_older_than(self, days: int = 30) -> int:
        """Removes historical data points older than specified days."""
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        cutoff_iso = cutoff.isoformat()

        with self.db_manager.get_connection() as conn:
            cursor = conn.execute("DELETE FROM quota_history WHERE timestamp < ?;", [cutoff_iso])
            conn.commit()
            return cursor.rowcount
