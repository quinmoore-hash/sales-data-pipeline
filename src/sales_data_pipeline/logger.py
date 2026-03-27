"""Logging setup for the sales data pipeline.

Provides dual output to stdout and a daily rotating log file, mirroring the
behaviour of ``logger.sh``.
"""

from __future__ import annotations

import logging
import sys
from datetime import date
from pathlib import Path

from sales_data_pipeline.config import PipelineConfig

LOG_FORMAT = "[%(asctime)s] %(levelname)s: %(message)s"
LOG_DATEFMT = "%Y-%m-%d %H:%M:%S"


def setup_logging(config: PipelineConfig) -> logging.Logger:
    """Configure and return the ``sales_data_pipeline`` logger.

    Adds a :class:`~logging.StreamHandler` (stdout) and a
    :class:`~logging.FileHandler` that writes to
    ``config.log_dir / pipeline_<date>.log``.

    Returns the configured logger and the path to today's log file.
    """
    logger = logging.getLogger("sales_data_pipeline")
    logger.setLevel(logging.DEBUG)

    # Avoid adding duplicate handlers on repeated calls
    if logger.handlers:
        return logger

    formatter = logging.Formatter(LOG_FORMAT, datefmt=LOG_DATEFMT)

    # Stdout handler
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setLevel(logging.DEBUG)
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    # File handler
    log_file = config.log_dir / f"pipeline_{date.today().isoformat()}.log"
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger


def get_log_file_path(config: PipelineConfig) -> Path:
    """Return the path to today's log file."""
    return config.log_dir / f"pipeline_{date.today().isoformat()}.log"


# ---------------------------------------------------------------------------
# Standalone CLI entry-point  (mirrors ``logger.sh`` lines 33-45)
# ---------------------------------------------------------------------------

def _cli() -> None:
    """``python -m sales_data_pipeline.logger LEVEL message ...``"""
    if len(sys.argv) < 3:
        print("Usage: python -m sales_data_pipeline.logger <LEVEL> <MESSAGE>")
        print("  Levels: INFO, WARN, ERROR")
        print('  Example: python -m sales_data_pipeline.logger INFO "Pipeline started"')
        sys.exit(1)

    level_name = sys.argv[1].upper()
    message = " ".join(sys.argv[2:])

    config = PipelineConfig()
    logger = setup_logging(config)

    level = getattr(logging, level_name, None)
    if level is None:
        # Treat WARN as WARNING
        if level_name == "WARN":
            level = logging.WARNING
        else:
            print(f"Unknown log level: {level_name}")
            sys.exit(1)

    logger.log(level, message)


if __name__ == "__main__":
    _cli()
