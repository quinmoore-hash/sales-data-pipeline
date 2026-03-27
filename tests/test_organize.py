"""Tests for sales_data_pipeline.organize."""

from __future__ import annotations

from pathlib import Path

import pytest

from sales_data_pipeline.config import PipelineConfig
from sales_data_pipeline.organize import organize_files


@pytest.fixture()
def config(tmp_path: Path) -> PipelineConfig:
    return PipelineConfig(
        base_dir=tmp_path / "pipeline",
        log_dir=tmp_path / "logs",
    )


class TestOrganizeFiles:
    def test_move_to_archive(self, config: PipelineConfig) -> None:
        # Create a processed file
        src = config.processed_dir / "sales_northeast_2024-01-05.csv"
        src.write_text("data")

        moved, errors = organize_files(config)
        assert moved == 1
        assert errors == 0

        dest = config.archive_dir / "sales_northeast_2024-01-05.csv"
        assert dest.exists()
        # Source should be gone (shutil.move, not copy)
        assert not src.exists()

    def test_skip_if_archive_exists(self, config: PipelineConfig) -> None:
        src = config.processed_dir / "sales_northeast_2024-01-05.csv"
        src.write_text("new data")
        dest = config.archive_dir / "sales_northeast_2024-01-05.csv"
        dest.write_text("old data")

        moved, errors = organize_files(config)
        assert moved == 0
        assert errors == 0
        # Original archive content preserved
        assert dest.read_text() == "old data"

    def test_rename_raw_to_done(self, config: PipelineConfig) -> None:
        raw = config.raw_dir / "daily_sales_2024-01-05.csv"
        raw.write_text("raw data")

        organize_files(config)

        assert not raw.exists()
        done = config.raw_dir / "daily_sales_2024-01-05.csv.done"
        assert done.exists()
        assert done.read_text() == "raw data"

    def test_multiple_files(self, config: PipelineConfig) -> None:
        for i in range(3):
            f = config.processed_dir / f"sales_northeast_2024-01-0{i+1}.csv"
            f.write_text(f"data {i}")

        moved, errors = organize_files(config)
        assert moved == 3
        assert errors == 0

    def test_no_files_is_ok(self, config: PipelineConfig) -> None:
        moved, errors = organize_files(config)
        assert moved == 0
        assert errors == 0
