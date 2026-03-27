"""File organization module — replaces ``organize_files.sh``.

Moves processed CSVs to the archive directory and renames raw files with a
``.done`` suffix so they are not re-processed.

Bug fix: uses :func:`shutil.move` instead of ``cp`` so files don't pile up
(see ``organize_files.sh`` line 38, README.md line 65).
"""

from __future__ import annotations

import logging
import shutil
from pathlib import Path

from sales_data_pipeline.config import PipelineConfig

logger = logging.getLogger("sales_data_pipeline")


def organize_files(config: PipelineConfig) -> tuple[int, int]:
    """Organize pipeline output files.

    Returns ``(moved_count, error_count)``.  Never raises — the organize
    step is non-fatal (see ``run_pipeline.sh`` lines 67-70).
    """
    moved = 0
    errors = 0

    # Move processed sales CSVs to archive
    for f in sorted(config.processed_dir.glob("sales_*.csv")):
        dest = config.archive_dir / f.name
        if dest.exists():
            logger.warning("Archive file already exists, skipping: %s", dest)
            continue
        try:
            shutil.move(str(f), str(dest))
            logger.info("Moved processed file to %s", dest)
            moved += 1
        except OSError as exc:
            logger.error("Failed to move %s to %s: %s", f, dest, exc)
            errors += 1

    # Rename raw files to mark them as done
    for f in sorted(config.raw_dir.glob("daily_sales_*.csv")):
        new_name = f.with_name(f"{f.name}.done")
        try:
            f.rename(new_name)
            logger.info("Renamed raw file to %s", new_name)
        except OSError as exc:
            logger.error("Could not rename %s: %s", f, exc)
            errors += 1

    logger.info("Organize complete — moved %d files, %d errors", moved, errors)
    return moved, errors
