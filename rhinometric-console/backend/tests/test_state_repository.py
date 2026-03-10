"""
Unit tests for health checker state persistence.
"""
import pytest
from unittest.mock import patch, MagicMock, call
from datetime import datetime, timezone


class TestEnsureSchema:
    """Tests for schema migration."""

    @patch("services.state_repository.SessionLocal")
    def test_migration_adds_columns(self, mock_session_cls):
        from services.state_repository import ensure_schema, _MIGRATION_COLUMNS
        mock_db = MagicMock()
        mock_session_cls.return_value = mock_db

        ensure_schema()

        # Should execute one ALTER TABLE per column
        assert mock_db.execute.call_count == len(_MIGRATION_COLUMNS)
        mock_db.commit.assert_called_once()
        mock_db.close.assert_called_once()

    @patch("services.state_repository.SessionLocal")
    def test_migration_rollback_on_error(self, mock_session_cls):
        from services.state_repository import ensure_schema
        mock_db = MagicMock()
        mock_session_cls.return_value = mock_db
        mock_db.execute.side_effect = Exception("DB error")

        with pytest.raises(Exception):
            ensure_schema()

        mock_db.rollback.assert_called_once()
        mock_db.close.assert_called_once()


class TestLoadAllStates:
    """Tests for loading persisted state."""

    @patch("services.state_repository.SessionLocal")
    def test_loads_all_enabled_services(self, mock_session_cls):
        from services.state_repository import load_all_states
        mock_db = MagicMock()
        mock_session_cls.return_value = mock_db

        now = datetime.now(timezone.utc)
        mock_db.execute.return_value.fetchall.return_value = [
            (1, "svc-a", "up", 0, now, None, now),
            (2, "svc-b", "down", 3, None, now, now),
        ]

        result = load_all_states()

        assert len(result) == 2
        assert result[0]["id"] == 1
        assert result[0]["status"] == "up"
        assert result[0]["consecutive_failures"] == 0
        assert result[1]["id"] == 2
        assert result[1]["consecutive_failures"] == 3
        mock_db.close.assert_called_once()

    @patch("services.state_repository.SessionLocal")
    def test_returns_empty_on_error(self, mock_session_cls):
        from services.state_repository import load_all_states
        mock_db = MagicMock()
        mock_session_cls.return_value = mock_db
        mock_db.execute.side_effect = Exception("fail")

        result = load_all_states()
        assert result == []
        mock_db.close.assert_called_once()


class TestPersistState:
    """Tests for per-service state persistence."""

    @patch("services.state_repository.SessionLocal")
    def test_persist_success_state(self, mock_session_cls):
        from services.state_repository import persist_state
        mock_db = MagicMock()
        mock_session_cls.return_value = mock_db

        persist_state(1, status="up", consecutive_failures=0, is_success=True)

        mock_db.execute.assert_called_once()
        sql_text = str(mock_db.execute.call_args[0][0].text)
        assert "last_success_at" in sql_text
        assert "last_failure_at" not in sql_text
        mock_db.commit.assert_called_once()
        mock_db.close.assert_called_once()

    @patch("services.state_repository.SessionLocal")
    def test_persist_failure_state(self, mock_session_cls):
        from services.state_repository import persist_state
        mock_db = MagicMock()
        mock_session_cls.return_value = mock_db

        persist_state(1, status="down", consecutive_failures=3, is_success=False)

        mock_db.execute.assert_called_once()
        sql_text = str(mock_db.execute.call_args[0][0].text)
        assert "last_failure_at" in sql_text
        assert "last_success_at" not in sql_text
        mock_db.commit.assert_called_once()

    @patch("services.state_repository.SessionLocal")
    def test_persist_rollback_on_error(self, mock_session_cls):
        from services.state_repository import persist_state
        mock_db = MagicMock()
        mock_session_cls.return_value = mock_db
        mock_db.execute.side_effect = Exception("DB error")

        # Should NOT raise — just log warning
        persist_state(1, status="down", consecutive_failures=1, is_success=False)

        mock_db.rollback.assert_called_once()
        mock_db.close.assert_called_once()


class TestClearInMemoryState:
    """Tests for clearing state on service deletion."""

    def test_clears_all_dicts(self):
        import services.health_checker as hc
        hc._previous_status[99] = "up"
        hc._consecutive_failures[99] = 5
        hc._recent_checks[99] = [(1, True, 100)]

        from services.state_repository import clear_in_memory_state
        clear_in_memory_state(99)

        assert 99 not in hc._previous_status
        assert 99 not in hc._consecutive_failures
        assert 99 not in hc._recent_checks

    def test_no_error_if_service_not_in_dicts(self):
        from services.state_repository import clear_in_memory_state
        # Should not raise even if service_id not present
        clear_in_memory_state(99999)
