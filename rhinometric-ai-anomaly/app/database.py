"""
SQLite Database Manager for AI Anomaly Detection
Handles baselines, incidents, and related data persistence

Version: 2.6.0
Thread-safe for async FastAPI usage
"""
import sqlite3
import logging
import asyncio
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime
from contextlib import contextmanager
import threading
import os

logger = logging.getLogger(__name__)


# Database schema version for migrations
SCHEMA_VERSION = 1


class DatabaseManager:
    """Thread-safe SQLite database manager"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls, db_path: str = "/app/data/ai_anomaly.db"):
        """Singleton pattern to ensure single DB connection"""
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance
    
    def __init__(self, db_path: str = "/app/data/ai_anomaly.db"):
        """Initialize database manager"""
        if self._initialized:
            return
        
        self.db_path = Path(db_path)
        self._local = threading.local()
        
        # Ensure data directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize schema
        self._initialize_schema()
        self._initialized = True
        
        logger.info(f"DatabaseManager initialized: {self.db_path}")
    
    @property
    def conn(self) -> sqlite3.Connection:
        """Get thread-local connection"""
        if not hasattr(self._local, 'connection') or self._local.connection is None:
            self._local.connection = sqlite3.connect(
                str(self.db_path),
                check_same_thread=False,
                isolation_level="DEFERRED"  # Use DEFERRED transactions
            )
            self._local.connection.row_factory = sqlite3.Row
            # Enable WAL mode for better concurrency
            self._local.connection.execute("PRAGMA journal_mode=WAL")
            self._local.connection.execute("PRAGMA synchronous=NORMAL")
        return self._local.connection
    
    @contextmanager
    def transaction(self):
        """Context manager for transactions"""
        conn = self.conn
        try:
            conn.execute("BEGIN")
            yield conn
            conn.execute("COMMIT")
        except Exception as e:
            conn.execute("ROLLBACK")
            logger.error(f"Transaction rolled back: {e}")
            raise
    
    def _initialize_schema(self):
        """Create database schema if not exists"""
        schema_sql = """
        -- Schema version tracking
        CREATE TABLE IF NOT EXISTS schema_version (
            version INTEGER PRIMARY KEY,
            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        -- Baseline storage: metric baselines by time context
        CREATE TABLE IF NOT EXISTS baselines (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            metric_name TEXT NOT NULL,
            metric_labels TEXT NOT NULL,
            hour_of_day INTEGER NOT NULL CHECK(hour_of_day >= 0 AND hour_of_day <= 23),
            day_of_week INTEGER NOT NULL CHECK(day_of_week >= 0 AND day_of_week <= 6),
            mean_value REAL NOT NULL,
            std_dev REAL NOT NULL,
            p10 REAL NOT NULL,
            p50 REAL NOT NULL,
            p90 REAL NOT NULL,
            min_value REAL NOT NULL,
            max_value REAL NOT NULL,
            sample_count INTEGER NOT NULL DEFAULT 0,
            last_updated TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(metric_name, metric_labels, hour_of_day, day_of_week)
        );
        
        CREATE INDEX IF NOT EXISTS idx_baselines_metric 
            ON baselines(metric_name, hour_of_day, day_of_week);
        CREATE INDEX IF NOT EXISTS idx_baselines_updated 
            ON baselines(last_updated);
        
        -- Incidents: grouped anomalies
        CREATE TABLE IF NOT EXISTS incidents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            incident_id TEXT UNIQUE NOT NULL,
            status TEXT NOT NULL CHECK(status IN ('new', 'ongoing', 'resolved')),
            severity TEXT NOT NULL CHECK(severity IN ('info', 'warning', 'critical')),
            start_time TIMESTAMP NOT NULL,
            end_time TIMESTAMP,
            last_updated TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            affected_services TEXT,
            affected_hosts TEXT,
            root_cause_metric TEXT,
            rca_suggestion TEXT,
            correlation_data TEXT,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE INDEX IF NOT EXISTS idx_incidents_status 
            ON incidents(status, start_time DESC);
        CREATE INDEX IF NOT EXISTS idx_incidents_severity 
            ON incidents(severity);
        CREATE INDEX IF NOT EXISTS idx_incidents_time 
            ON incidents(start_time DESC);
        
        -- Incident metrics
        CREATE TABLE IF NOT EXISTS incident_metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            incident_id INTEGER NOT NULL,
            metric_name TEXT NOT NULL,
            timestamp TIMESTAMP NOT NULL,
            current_value REAL NOT NULL,
            expected_value REAL NOT NULL,
            anomaly_score REAL NOT NULL,
            confidence REAL NOT NULL,
            severity TEXT NOT NULL,
            models_used TEXT NOT NULL,
            model_scores TEXT NOT NULL,
            metadata TEXT,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (incident_id) REFERENCES incidents(id) ON DELETE CASCADE
        );
        
        CREATE INDEX IF NOT EXISTS idx_incident_metrics_incident 
            ON incident_metrics(incident_id);
        CREATE INDEX IF NOT EXISTS idx_incident_metrics_metric 
            ON incident_metrics(metric_name, timestamp);
        
        -- Baseline history
        CREATE TABLE IF NOT EXISTS baseline_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            metric_name TEXT NOT NULL,
            metric_labels TEXT NOT NULL,
            timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            mean_value REAL NOT NULL,
            std_dev REAL NOT NULL,
            sample_count INTEGER NOT NULL
        );
        
        CREATE INDEX IF NOT EXISTS idx_baseline_history_metric 
            ON baseline_history(metric_name, timestamp DESC);
        """
        
        try:
            # Execute schema SQL directly (without explicit transaction context manager)
            conn = self.conn
            conn.executescript(schema_sql)
            conn.commit()
            
            # Check and insert schema version
            cursor = conn.execute("SELECT version FROM schema_version WHERE version = ?", (SCHEMA_VERSION,))
            if cursor.fetchone() is None:
                conn.execute("INSERT INTO schema_version (version) VALUES (?)", (SCHEMA_VERSION,))
                conn.commit()
                logger.info(f"Database schema v{SCHEMA_VERSION} initialized")
            else:
                logger.info(f"Database schema v{SCHEMA_VERSION} already exists")
        
        except Exception as e:
            logger.error(f"Failed to initialize schema: {e}")
            raise
    
    # ========== BASELINE OPERATIONS ==========
    
    def upsert_baseline(
        self,
        metric_name: str,
        metric_labels: str,
        hour_of_day: int,
        day_of_week: int,
        mean_value: float,
        std_dev: float,
        p10: float,
        p50: float,
        p90: float,
        min_value: float,
        max_value: float,
        sample_count: int
    ) -> int:
        """
        Insert or update baseline data
        
        Returns:
            Row ID of inserted/updated baseline
        """
        sql = """
        INSERT INTO baselines (
            metric_name, metric_labels, hour_of_day, day_of_week,
            mean_value, std_dev, p10, p50, p90, min_value, max_value,
            sample_count, last_updated
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(metric_name, metric_labels, hour_of_day, day_of_week) 
        DO UPDATE SET
            mean_value = excluded.mean_value,
            std_dev = excluded.std_dev,
            p10 = excluded.p10,
            p50 = excluded.p50,
            p90 = excluded.p90,
            min_value = excluded.min_value,
            max_value = excluded.max_value,
            sample_count = excluded.sample_count,
            last_updated = CURRENT_TIMESTAMP
        """
        
        try:
            cursor = self.conn.execute(
                sql,
                (metric_name, metric_labels, hour_of_day, day_of_week,
                 mean_value, std_dev, p10, p50, p90, min_value, max_value, sample_count)
            )
            self.conn.commit()  # ✅ CRITICAL: WAL mode requires explicit commit
            logger.info(f"✅ DATABASE_COMMIT: Baseline for {metric_name} committed (rowid={cursor.lastrowid})")
            return cursor.lastrowid
        except Exception as e:
            logger.error(f"Failed to upsert baseline for {metric_name}: {e}")
            self.conn.rollback()  # ✅ Rollback on error
            raise
    
    def get_baseline(
        self,
        metric_name: str,
        metric_labels: str,
        hour_of_day: int,
        day_of_week: int
    ) -> Optional[Dict[str, Any]]:
        """
        Get baseline for specific metric and time context
        
        Returns:
            Dict with baseline data or None if not found
        """
        sql = """
        SELECT * FROM baselines
        WHERE metric_name = ? AND metric_labels = ?
          AND hour_of_day = ? AND day_of_week = ?
        """
        
        try:
            cursor = self.conn.execute(sql, (metric_name, metric_labels, hour_of_day, day_of_week))
            row = cursor.fetchone()
            return dict(row) if row else None
        except Exception as e:
            logger.error(f"Failed to get baseline for {metric_name}: {e}")
            return None
    
    def get_all_baselines(self, metric_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get all baselines, optionally filtered by metric name
        
        Returns:
            List of baseline dictionaries
        """
        if metric_name:
            sql = "SELECT * FROM baselines WHERE metric_name = ? ORDER BY last_updated DESC"
            params = (metric_name,)
        else:
            sql = "SELECT * FROM baselines ORDER BY last_updated DESC"
            params = ()
        
        try:
            cursor = self.conn.execute(sql, params)
            return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Failed to get baselines: {e}")
            return []
    
    def delete_old_baselines(self, days: int = 30) -> int:
        """
        Delete baselines older than specified days
        
        Returns:
            Number of deleted rows
        """
        sql = """
        DELETE FROM baselines
        WHERE last_updated < datetime('now', ?)
        """
        
        try:
            cursor = self.conn.execute(sql, (f'-{days} days',))
            deleted = cursor.rowcount
            logger.info(f"Deleted {deleted} old baselines (>{days} days)")
            return deleted
        except Exception as e:
            logger.error(f"Failed to delete old baselines: {e}")
            return 0
    
    # ========== INCIDENT OPERATIONS ==========
    
    def create_incident(
        self,
        incident_id: str,
        status: str,
        severity: str,
        start_time: datetime,
        affected_services: Optional[str] = None,
        affected_hosts: Optional[str] = None
    ) -> int:
        """
        Create new incident
        
        Returns:
            Row ID of created incident
        """
        sql = """
        INSERT INTO incidents (
            incident_id, status, severity, start_time,
            affected_services, affected_hosts
        ) VALUES (?, ?, ?, ?, ?, ?)
        """
        
        try:
            cursor = self.conn.execute(
                sql,
                (incident_id, status, severity, start_time.isoformat(),
                 affected_services, affected_hosts)
            )
            logger.info(f"Created incident {incident_id}")
            return cursor.lastrowid
        except Exception as e:
            logger.error(f"Failed to create incident {incident_id}: {e}")
            raise
    
    def update_incident(
        self,
        incident_id: str,
        status: Optional[str] = None,
        severity: Optional[str] = None,
        end_time: Optional[datetime] = None,
        root_cause_metric: Optional[str] = None,
        rca_suggestion: Optional[str] = None,
        correlation_data: Optional[str] = None,
        affected_services: Optional[str] = None,
        affected_hosts: Optional[str] = None
    ) -> bool:
        """
        Update existing incident
        
        Returns:
            True if updated, False otherwise
        """
        # Build dynamic UPDATE query
        updates = []
        params = []
        
        if status:
            updates.append("status = ?")
            params.append(status)
        if severity:
            updates.append("severity = ?")
            params.append(severity)
        if end_time:
            updates.append("end_time = ?")
            params.append(end_time.isoformat())
        if root_cause_metric:
            updates.append("root_cause_metric = ?")
            params.append(root_cause_metric)
        if rca_suggestion:
            updates.append("rca_suggestion = ?")
            params.append(rca_suggestion)
        if correlation_data:
            updates.append("correlation_data = ?")
            params.append(correlation_data)
        if affected_services:
            updates.append("affected_services = ?")
            params.append(affected_services)
        if affected_hosts:
            updates.append("affected_hosts = ?")
            params.append(affected_hosts)
        
        if not updates:
            return False
        
        updates.append("last_updated = CURRENT_TIMESTAMP")
        params.append(incident_id)
        
        sql = f"UPDATE incidents SET {', '.join(updates)} WHERE incident_id = ?"
        
        try:
            cursor = self.conn.execute(sql, tuple(params))
            updated = cursor.rowcount > 0
            if updated:
                logger.debug(f"Updated incident {incident_id}")
            return updated
        except Exception as e:
            logger.error(f"Failed to update incident {incident_id}: {e}")
            return False
    
    def get_incident(self, incident_id: str) -> Optional[Dict[str, Any]]:
        """Get incident by ID"""
        sql = "SELECT * FROM incidents WHERE incident_id = ?"
        
        try:
            cursor = self.conn.execute(sql, (incident_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
        except Exception as e:
            logger.error(f"Failed to get incident {incident_id}: {e}")
            return None
    
    def get_incidents(
        self,
        status: Optional[str] = None,
        severity: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get incidents with optional filters
        
        Returns:
            List of incident dictionaries
        """
        sql = "SELECT * FROM incidents WHERE 1=1"
        params = []
        
        if status:
            sql += " AND status = ?"
            params.append(status)
        if severity:
            sql += " AND severity = ?"
            params.append(severity)
        
        sql += " ORDER BY start_time DESC LIMIT ?"
        params.append(limit)
        
        try:
            cursor = self.conn.execute(sql, tuple(params))
            return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Failed to get incidents: {e}")
            return []
    
    def add_incident_metric(
        self,
        incident_id: str,
        metric_name: str,
        timestamp: datetime,
        current_value: float,
        expected_value: float,
        anomaly_score: float,
        confidence: float,
        severity: str,
        models_used: str,
        model_scores: str,
        metadata: Optional[str] = None
    ) -> int:
        """
        Add anomaly metric to incident
        
        Returns:
            Row ID of added metric
        """
        # Get incident row ID
        incident = self.get_incident(incident_id)
        if not incident:
            raise ValueError(f"Incident {incident_id} not found")
        
        sql = """
        INSERT INTO incident_metrics (
            incident_id, metric_name, timestamp, current_value, expected_value,
            anomaly_score, confidence, severity, models_used, model_scores, metadata
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        try:
            cursor = self.conn.execute(
                sql,
                (incident['id'], metric_name, timestamp.isoformat(), current_value, expected_value,
                 anomaly_score, confidence, severity, models_used, model_scores, metadata)
            )
            return cursor.lastrowid
        except Exception as e:
            logger.error(f"Failed to add metric to incident {incident_id}: {e}")
            raise
    
    def get_incident_metrics(self, incident_id: str) -> List[Dict[str, Any]]:
        """Get all metrics for an incident"""
        sql = """
        SELECT im.* FROM incident_metrics im
        JOIN incidents i ON im.incident_id = i.id
        WHERE i.incident_id = ?
        ORDER BY im.timestamp
        """
        
        try:
            cursor = self.conn.execute(sql, (incident_id,))
            return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Failed to get metrics for incident {incident_id}: {e}")
            return []
    
    # ========== STATISTICS ==========
    
    def get_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        stats = {}
        
        try:
            # Baseline stats
            cursor = self.conn.execute("SELECT COUNT(*) as count FROM baselines")
            stats['baseline_count'] = cursor.fetchone()['count']
            
            cursor = self.conn.execute("SELECT COUNT(DISTINCT metric_name) as count FROM baselines")
            stats['unique_metrics'] = cursor.fetchone()['count']
            
            # Incident stats
            cursor = self.conn.execute("SELECT COUNT(*) as count FROM incidents")
            stats['total_incidents'] = cursor.fetchone()['count']
            
            cursor = self.conn.execute("SELECT COUNT(*) as count FROM incidents WHERE status = 'ongoing'")
            stats['active_incidents'] = cursor.fetchone()['count']
            
            cursor = self.conn.execute("SELECT COUNT(*) as count FROM incident_metrics")
            stats['total_anomalies'] = cursor.fetchone()['count']
            
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
        
        return stats
    
    def close(self):
        """Close database connection"""
        if hasattr(self._local, 'connection') and self._local.connection:
            self._local.connection.close()
            self._local.connection = None
            logger.info("Database connection closed")


# Global database instance
db = DatabaseManager(
    db_path=os.getenv("DB_PATH", "/app/data/ai_anomaly.db")
)
