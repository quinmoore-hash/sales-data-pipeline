"""Tests for sales_data_pipeline.cleanup."""

from __future__ import annotations

import os
import time
from pathlib import Path

import pytest

from sales_data_pipeline.cleanup import cleanup_old_files
from sales_data_pipeline.config import PipelineConfig


def _set_mtime_days_ago(path: Path, days: int) -> None:
    """Set the mtime of *path* to *days* days in the past."""
    old_time = time.time() - (days * 86400) - 60  # extra 60s buffer
    os.utime(path, (old_time, old_time))


@pytest.fixture()
def config(tmp_path: Path) -> PipelineConfig:
    return PipelineConfig(
        base_dir=tmp_path / "pipeline",
        log_dir=tmp_path / "logs",
        max_age_days=30,
        log_retention_days=7,
    )


class TestCleanupOldFiles:
    def test_removes_old_archive_csv(self, config: PipelineConfig) -> None:
        old_file = config.archive_dir / "sales_old.csv"
        old_file.write_text("old")
        _set_mtime_days_ago(old_file, 31)

        removed = cleanup_old_files(config)
        assert removed >= 1
        assert not old_file.exists()

    def test_keeps_recent_archive_csv(self, config: PipelineConfig) -> None:
        recent = config.archive_dir / "sales_recent.csv"
        recent.write_text("recent")
        _set_mtime_days_ago(recent, 5)

        removed = cleanup_old_files(config)
        assert recent.exists()

    def test_removes_old_processed_csv(self, config: PipelineConfig) -> None:
        old_csv = config.processed_dir / "sales_northeast_old.csv"
        old_csv.write_text("old")
        _set_mtime_days_ago(old_csv, 31)

        old_summary = config.processed_dir / "summary_northeast_old.txt"
        old_summary.write_text("summary")
        _set_mtime_days_ago(old_summary, 31)

        removed = cleanup_old_files(config)
        assert removed >= 2
        assert not old_csv.exists()
        assert not old_summary.exists()

    def test_log_files_use_log_retention_days(self, config: PipelineConfig) -> None:
        """Log files should use log_retention_days=7, not max_age_days=30."""
        # File 8 days old should be removed (> 7)
        old_log = config.log_dir / "pipeline_2024-01-01.log"
        old_log.write_text("old log")
        _set_mtime_days_ago(old_log, 8)

        # File 5 days old should be kept (< 7)
        recent_log = config.log_dir / "pipeline_2024-03-20.log"
        recent_log.write_text("recent log")
        _set_mtime_days_ago(recent_log, 5)

        removed = cleanup_old_files(config)
        assert not old_log.exists(), "Log older than log_retention_days should be removed"
        assert recent_log.exists(), "Log within log_retention_days should be kept"

    def test_log_retention_independent_of_max_age(self, config: PipelineConfig) -> None:
        """Verify a log file at 20 days old IS removed even though max_age is 30.

        This is the bug fix: cleanup.sh used hardcoded 7 days for logs but
        reported all removals as 'older than MAX_AGE_DAYS'.
        """
        mid_age_log = config.log_dir / "pipeline_mid.log"
        mid_age_log.write_text("mid age")
        _set_mtime_days_ago(mid_age_log, 20)

        cleanup_old_files(config)
        # 20 > 7 (log_retention_days) so it should be gone
        assert not mid_age_log.exists()

    def test_removes_csv_done_files(self, config: PipelineConfig) -> None:
        old = config.archive_dir / "data.csv.done"
        old.write_text("done")
        _set_mtime_days_ago(old, 31)

        removed = cleanup_old_files(config)
        assert not old.exists()

    def test_empty_dirs_no_error(self, config: PipelineConfig) -> None:
        removed = cleanup_old_files(config)
        assert removed == 0
