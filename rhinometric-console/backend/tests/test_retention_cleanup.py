"""
Tests for Data Retention & Cleanup module.
"""
import os
import pytest
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock


class TestGetRetentionDays:

    def test_default_value(self):
        from services.retention_cleanup import get_retention_days
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("EXTERNAL_SERVICE_CHECK_RETENTION_DAYS", None)
            assert get_retention_days() == 90

    def test_custom_value(self):
        from services.retention_cleanup import get_retention_days
        with patch.dict(os.environ, {"EXTERNAL_SERVICE_CHECK_RETENTION_DAYS": "30"}):
            assert get_retention_days() == 30

    def test_clamp_below_minimum(self):
        from services.retention_cleanup import get_retention_days
        with patch.dict(os.environ, {"EXTERNAL_SERVICE_CHECK_RETENTION_DAYS": "3"}):
            assert get_retention_days() == 7

    def test_clamp_above_maximum(self):
        from services.retention_cleanup import get_retention_days
        with patch.dict(os.environ, {"EXTERNAL_SERVICE_CHECK_RETENTION_DAYS": "999"}):
            assert get_retention_days() == 365

    def test_invalid_non_numeric(self):
        from services.retention_cleanup import get_retention_days
        with patch.dict(os.environ, {"EXTERNAL_SERVICE_CHECK_RETENTION_DAYS": "abc"}):
            assert get_retention_days() == 90

    def test_boundary_minimum(self):
        from services.retention_cleanup import get_retention_days
        with patch.dict(os.environ, {"EXTERNAL_SERVICE_CHECK_RETENTION_DAYS": "7"}):
            assert get_retention_days() == 7

    def test_boundary_maximum(self):
        from services.retention_cleanup import get_retention_days
        with patch.dict(os.environ, {"EXTERNAL_SERVICE_CHECK_RETENTION_DAYS": "365"}):
            assert get_retention_days() == 365


class TestRunCleanup:

    @patch("services.retention_cleanup.SessionLocal")
    def test_no_rows_to_delete(self, mock_session_cls):
        from services.retention_cleanup import run_cleanup
        mock_db = MagicMock()
        mock_session_cls.return_value = mock_db
        mock_result = MagicMock()
        mock_result.rowcount = 0
        mock_db.execute.return_value = mock_result

        deleted, duration = run_cleanup(retention_days=90)
        assert deleted == 0
        assert duration >= 0
        mock_db.close.assert_called_once()

    @patch("services.retention_cleanup.SessionLocal")
    def test_single_batch_deletion(self, mock_session_cls):
        from services.retention_cleanup import run_cleanup
        mock_db = MagicMock()
        mock_session_cls.return_value = mock_db
        result1 = MagicMock()
        result1.rowcount = 1234
        result2 = MagicMock()
        result2.rowcount = 0
        mock_db.execute.side_effect = [result1, result2]

        deleted, duration = run_cleanup(retention_days=90)
        assert deleted == 1234
        assert mock_db.commit.call_count == 2
        mock_db.close.assert_called_once()

    @patch("services.retention_cleanup.SessionLocal")
    def test_multi_batch_deletion(self, mock_session_cls):
        from services.retention_cleanup import run_cleanup, _BATCH_SIZE
        mock_db = MagicMock()
        mock_session_cls.return_value = mock_db
        results = []
        for _ in range(3):
            r = MagicMock()
            r.rowcount = _BATCH_SIZE
            results.append(r)
        partial = MagicMock()
        partial.rowcount = 42
        results.append(partial)
        done = MagicMock()
        done.rowcount = 0
        results.append(done)
        mock_db.execute.side_effect = results

        deleted, _ = run_cleanup(retention_days=30)
        assert deleted == (_BATCH_SIZE * 3) + 42

    @patch("services.retention_cleanup.SessionLocal")
    def test_db_error_handled(self, mock_session_cls):
        from services.retention_cleanup import run_cleanup
        mock_db = MagicMock()
        mock_session_cls.return_value = mock_db
        mock_db.execute.side_effect = Exception("connection lost")

        deleted, duration = run_cleanup(retention_days=90)
        assert deleted == 0
        mock_db.rollback.assert_called_once()
        mock_db.close.assert_called_once()


class TestGetStorageInfo:

    @patch("services.retention_cleanup.SessionLocal")
    def test_returns_expected_keys(self, mock_session_cls):
        from services.retention_cleanup import get_storage_info
        mock_db = MagicMock()
        mock_session_cls.return_value = mock_db
        mock_db.execute.side_effect = [
            MagicMock(fetchone=MagicMock(return_value=(5000,))),
            MagicMock(fetchone=MagicMock(return_value=(2097152,))),
            MagicMock(fetchone=MagicMock(return_value=(datetime(2026, 1, 1, tzinfo=timezone.utc),))),
            MagicMock(fetchone=MagicMock(return_value=(datetime(2026, 3, 10, tzinfo=timezone.utc),))),
        ]

        info = get_storage_info()
        assert info["table"] == "external_service_checks"
        assert info["row_count"] == 5000
        assert info["size_bytes"] == 2097152
        assert "MB" in info["size_human"]
        assert info["retention_days"] == 90
        mock_db.close.assert_called_once()

    @patch("services.retention_cleanup.SessionLocal")
    def test_handles_empty_table(self, mock_session_cls):
        from services.retention_cleanup import get_storage_info
        mock_db = MagicMock()
        mock_session_cls.return_value = mock_db
        mock_db.execute.side_effect = [
            MagicMock(fetchone=MagicMock(return_value=(0,))),
            MagicMock(fetchone=MagicMock(return_value=(8192,))),
            MagicMock(fetchone=MagicMock(return_value=(None,))),
            MagicMock(fetchone=MagicMock(return_value=(None,))),
        ]

        info = get_storage_info()
        assert info["row_count"] == 0
        assert info["oldest_check"] is None
        assert info["newest_check"] is None
