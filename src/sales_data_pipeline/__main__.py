"""Pipeline orchestrator — replaces ``run_pipeline.sh``.

Run with::

    python -m sales_data_pipeline
    # or, after ``pip install -e .``:
    sales-pipeline
"""

from __future__ import annotations

import fcntl
import logging
import sys
from pathlib import Path

from sales_data_pipeline.cleanup import cleanup_old_files
from sales_data_pipeline.config import PipelineConfig
from sales_data_pipeline.fetch import FetchError, fetch_data
from sales_data_pipeline.logger import get_log_file_path, setup_logging
from sales_data_pipeline.organize import organize_files
from sales_data_pipeline.process import process_csv


def main() -> None:  # noqa: C901
    """Entry point for the pipeline."""
    config = PipelineConfig()
    logger = setup_logging(config)
    log_file = get_log_file_path(config)

    # --- File lock (addresses concurrency issue noted in README) ---
    lock_path = config.base_dir / ".pipeline.lock"
    try:
        lock_fh = open(lock_path, "w")  # noqa: SIM115
        fcntl.flock(lock_fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        logger.error(
            "Could not acquire lock — another pipeline instance may be running (%s)",
            lock_path,
        )
        sys.exit(1)

    logger.info("Pipeline started")

    # Warn (don't abort) if API key is missing
    if not config.api_key:
        logger.warning("DATA_PIPELINE_API_KEY not set — API calls will probably fail")

    logger.info("Environment check passed")

    # --- Step 1: Fetch ---
    logger.info("Step 1: Fetching data...")
    input_file: Path | None = None
    try:
        input_file = fetch_data(config)
    except FetchError as exc:
        logger.error("Data fetch failed: %s", exc)
        # Fall back to the most recent existing CSV in raw_dir
        existing = sorted(config.raw_dir.glob("*.csv"))
        if not existing:
            logger.error("No existing data to fall back on, aborting")
            sys.exit(1)
        input_file = existing[-1]
        logger.warning("Using existing data file: %s", input_file)

    # --- Step 2: Process ---
    logger.info("Step 2: Processing data...")
    try:
        result = process_csv(config, input_file)
        if result is None:
            logger.warning("Processing produced no output (0 rows matched)")
    except Exception as exc:
        logger.error("CSV processing failed: %s", exc)
        sys.exit(1)

    # --- Step 3: Organize ---
    logger.info("Step 3: Organizing files...")
    try:
        moved, errs = organize_files(config)
        if errs > 0:
            logger.warning("File organization had %d errors", errs)
    except Exception as exc:
        logger.warning("File organization failed: %s", exc)

    # --- Step 4: Cleanup ---
    logger.info("Step 4: Running cleanup...")
    try:
        cleanup_old_files(config)
    except Exception as exc:
        logger.warning("Cleanup failed (non-fatal): %s", exc)

    logger.info("Pipeline finished successfully")
    print(f"\nDone. Check logs at: {log_file}")

    # Release lock
    fcntl.flock(lock_fh, fcntl.LOCK_UN)
    lock_fh.close()

    sys.exit(0)


if __name__ == "__main__":
    main()
