"""Centralized configuration for the sales data pipeline."""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger("sales_data_pipeline")


@dataclass
class PipelineConfig:
    """Pipeline configuration populated from environment variables.

    This replaces the scattered ``export`` statements in ``run_pipeline.sh``
    and the per-script defaults.  All directory paths are created automatically
    in ``__post_init__``.
    """

    api_url: str = field(default_factory=lambda: os.environ.get(
        "API_URL", "https://api.example.com/v1/sales"
    ))
    api_key: str = field(default_factory=lambda: os.environ.get(
        "DATA_PIPELINE_API_KEY", ""
    ))
    base_dir: Path = field(default=None)  # type: ignore[assignment]
    raw_dir: Path = field(init=False)
    processed_dir: Path = field(init=False)
    archive_dir: Path = field(default=None)  # type: ignore[assignment]
    log_dir: Path = field(default=None)  # type: ignore[assignment]
    region: str = field(default_factory=lambda: os.environ.get(
        "REGION", "northeast"
    ))
    max_age_days: int = field(default_factory=lambda: int(os.environ.get(
        "MAX_AGE_DAYS", "30"
    )))
    log_retention_days: int = field(default_factory=lambda: int(os.environ.get(
        "LOG_RETENTION_DAYS", "7"
    )))
    fetch_timeout: int = 30
    fetch_retries: int = 3

    def __post_init__(self) -> None:
        # --- base_dir ---
        if self.base_dir is None:
            self.base_dir = Path(os.environ.get("OUTPUT_DIR", "/tmp/data_pipeline"))
        else:
            self.base_dir = Path(self.base_dir)

        # --- computed dirs ---
        self.raw_dir = self.base_dir / "raw"
        self.processed_dir = self.base_dir / "processed"

        # --- archive_dir ---
        if self.archive_dir is None:
            env_val = os.environ.get("ARCHIVE_DIR")
            self.archive_dir = Path(env_val) if env_val else self.base_dir / "archive"
        else:
            self.archive_dir = Path(self.archive_dir)

        # --- log_dir ---
        if self.log_dir is None:
            env_val = os.environ.get("LOG_DIR")
            if env_val:
                self.log_dir = Path(env_val)
            else:
                self.log_dir = Path(__file__).resolve().parent.parent.parent / "logs"
        else:
            self.log_dir = Path(self.log_dir)

        # Create all directories
        for d in (self.raw_dir, self.processed_dir, self.archive_dir, self.log_dir):
            d.mkdir(parents=True, exist_ok=True)

        # Warn if API key is empty
        if not self.api_key:
            logger.warning("DATA_PIPELINE_API_KEY is not set — API calls will probably fail")
