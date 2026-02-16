#!/usr/bin/env python3
"""
RHINOMETRIC Automated Backup Service
Runs scheduled backups using rmetricctl
"""
import os
import subprocess
import schedule
import time
import logging
from datetime import datetime, timedelta
from pathlib import Path

# Configuration from environment
BACKUP_SCHEDULE = os.getenv("BACKUP_SCHEDULE", "0 2 * * *")  # Default: 2 AM daily
RETENTION_DAYS = int(os.getenv("BACKUP_RETENTION_DAYS", "30"))
BACKUP_COMPONENTS = os.getenv("BACKUP_COMPONENTS", "prometheus,loki,tempo,grafana").split(",")
RMETRICCTL_PATH = "/usr/local/bin/rmetricctl"

# Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)


def run_backup():
    """Execute backup using rmetricctl"""
    logger.info(f"Starting scheduled backup: {', '.join(BACKUP_COMPONENTS)}")
    
    try:
        cmd = [RMETRICCTL_PATH, "backup", "--component"] + BACKUP_COMPONENTS
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        logger.info(f"Backup completed successfully")
        logger.info(result.stdout)
    except subprocess.CalledProcessError as e:
        logger.error(f"Backup failed: {e}")
        logger.error(e.stderr)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")


def run_cleanup():
    """Clean up old backups"""
    logger.info(f"Cleaning backups older than {RETENTION_DAYS} days")
    
    try:
        cmd = [RMETRICCTL_PATH, "clean", "--older-than", str(RETENTION_DAYS)]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        logger.info("Cleanup completed")
        logger.info(result.stdout)
    except subprocess.CalledProcessError as e:
        logger.error(f"Cleanup failed: {e}")
        logger.error(e.stderr)


def parse_cron_to_time(cron_expr: str) -> str:
    """Convert cron expression to schedule time (simplified)"""
    parts = cron_expr.split()
    if len(parts) >= 2:
        minute, hour = parts[0], parts[1]
        return f"{hour.zfill(2)}:{minute.zfill(2)}"
    return "02:00"  # Default fallback


def main():
    logger.info("=" * 60)
    logger.info("RHINOMETRIC Automated Backup Service v2.2.0")
    logger.info("=" * 60)
    logger.info(f"Schedule: {BACKUP_SCHEDULE}")
    logger.info(f"Retention: {RETENTION_DAYS} days")
    logger.info(f"Components: {', '.join(BACKUP_COMPONENTS)}")
    logger.info("=" * 60)
    
    # Parse schedule
    backup_time = parse_cron_to_time(BACKUP_SCHEDULE)
    logger.info(f"Daily backup scheduled at {backup_time}")
    
    # Schedule backup
    schedule.every().day.at(backup_time).do(run_backup)
    
    # Schedule weekly cleanup (Sunday at 3 AM)
    schedule.every().sunday.at("03:00").do(run_cleanup)
    
    logger.info("Service started. Waiting for scheduled tasks...")
    
    # Run once immediately in test mode
    if os.getenv("RUN_IMMEDIATE", "false").lower() == "true":
        logger.info("Running immediate test backup...")
        run_backup()
    
    # Main loop
    while True:
        schedule.run_pending()
        time.sleep(60)


if __name__ == "__main__":
    main()
