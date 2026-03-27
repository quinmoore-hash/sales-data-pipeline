"""Old file removal module — replaces ``cleanup.sh``.

Scans archive, processed, and log directories and removes files that exceed
their respective retention periods.

Bug fix: log files now use ``config.log_retention_days`` instead of a
hardcoded 7, and the summary message reports the correct threshold for each
category (see ``cleanup.sh`` line 57).
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from pathlib import Path

from sales_data_pipeline.config import PipelineConfig

logger = logging.getLogger("sales_data_pipeline")


def _remove_old(directory: Path, pattern: str, max_days: int) -> int:
    """Delete files in *directory* matching *pattern* older than *max_days*.

    Uses ``>`` (strictly older), matching the behaviour of ``find -mtime +N``.

    Returns the number of files removed.
    """
    if not directory.is_dir():
        logger.warning("Directory does not exist, skipping: %s", directory)
        return 0

    cutoff = datetime.now() - timedelta(days=max_days)
    removed = 0

    for f in sorted(directory.glob(pattern)):
        if not f.is_file():
            continue
        mtime = datetime.fromtimestamp(f.stat().st_mtime)
        if mtime < cutoff:  # strictly older than cutoff
            try:
                f.unlink()
                logger.info("Removed: %s", f)
                removed += 1
            except OSError as exc:
                logger.error("Failed to remove %s: %s", f, exc)

    return removed


def cleanup_old_files(config: PipelineConfig) -> int:
    """Remove stale files from archive, processed, and log directories.

    Returns the total number of files removed.
    """
    logger.info(
        "Cleanup started — removing archive/processed files older than %d days, "
        "log files older than %d days",
        config.max_age_days,
        config.log_retention_days,
    )

    removed = 0

    # Archive CSVs
    removed += _remove_old(config.archive_dir, "*.csv", config.max_age_days)
    removed += _remove_old(config.archive_dir, "*.csv.done", config.max_age_days)

    # Processed outputs
    removed += _remove_old(config.processed_dir, "sales_*.csv", config.max_age_days)
    removed += _remove_old(config.processed_dir, "summary_*.txt", config.max_age_days)

    # Log files — use log_retention_days (not max_age_days)
    removed += _remove_old(config.log_dir, "pipeline_*.log", config.log_retention_days)

    logger.info("Cleanup complete — removed %d files", removed)
    return removed
