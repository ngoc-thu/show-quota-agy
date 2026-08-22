"""Unit tests for QuotaService."""

import unittest
from pathlib import Path
from unittest.mock import MagicMock
from src.core.service import QuotaService
from src.core.models import QuotaSnapshot, QuotaInfo, QuotaStatus, ConnectionState, AppSettings
from src.storage.db import DatabaseManager
from tests.mock_data import MOCK_FETCH_MODELS_RESPONSE, MOCK_QUOTA_SUMMARY_RESPONSE


class TestService(unittest.TestCase):
    def setUp(self):
        self.db = DatabaseManager(Path(":memory:"))
        self.mock_client = MagicMock()
        self.mock_client.fetch_available_models.return_value = MOCK_FETCH_MODELS_RESPONSE
        self.mock_client.fetch_quota_summary.return_value = MOCK_QUOTA_SUMMARY_RESPONSE

        self.service = QuotaService(
            db_manager=self.db,
            client=self.mock_client,
        )

    def test_service_refresh_success(self):
        snapshot = self.service.refresh(force=True)
        self.assertEqual(snapshot.connection_state, ConnectionState.CONNECTED)
        self.assertFalse(snapshot.is_stale)
        self.assertIn("gemini-3.6-flash-high", snapshot.models)
        self.assertEqual(len(snapshot.groups), 2)

    def test_service_listener_notification(self):
        received = []
        self.service.add_listener(lambda s: received.append(s))

        self.service.refresh(force=True)
        self.assertEqual(len(received), 1)
        self.assertEqual(received[0].connection_state, ConnectionState.CONNECTED)


if __name__ == "__main__":
    unittest.main()
