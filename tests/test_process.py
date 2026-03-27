"""Tests for sales_data_pipeline.process."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from sales_data_pipeline.config import PipelineConfig
from sales_data_pipeline.process import process_csv

SAMPLE_CSV = """\
date,region,product,units_sold,revenue
2024-01-05,northeast,Widget A,150,4500.00
2024-01-05,southeast,Widget B,89,2670.00
2024-01-12,northeast,Widget B,175,5250.00
2024-02-02,northeast,Widget C,300,12000.00
"""

QUOTED_COMMAS_CSV = """\
date,region,product,units_sold,revenue
2024-01-05,northeast,"Widget, Deluxe A",150,4500.00
2024-01-05,southeast,Widget B,89,2670.00
2024-01-12,northeast,"Widget, Deluxe B",175,5250.00
"""


@pytest.fixture()
def config(tmp_path: Path) -> PipelineConfig:
    return PipelineConfig(
        base_dir=tmp_path / "pipeline",
        log_dir=tmp_path / "logs",
        region="northeast",
    )


@pytest.fixture()
def input_csv(config: PipelineConfig) -> Path:
    p = config.raw_dir / "sample.csv"
    p.write_text(SAMPLE_CSV)
    return p


class TestProcessCsv:
    def test_filters_by_region(self, config: PipelineConfig, input_csv: Path) -> None:
        result = process_csv(config, input_csv)
        assert result is not None
        assert result.exists()

        lines = result.read_text().strip().splitlines()
        # header + 3 northeast rows
        assert len(lines) == 4
        for line in lines[1:]:
            assert "northeast" in line

    def test_summary_file_created(self, config: PipelineConfig, input_csv: Path) -> None:
        process_csv(config, input_csv)
        today = date.today().isoformat()
        summary = config.processed_dir / f"summary_northeast_{today}.txt"
        assert summary.exists()

        text = summary.read_text()
        assert "=== Sales Summary ===" in text
        assert "Region: northeast" in text
        assert "Records: 3" in text
        assert "Total Revenue: $21750.00" in text
        assert "Revenue by Product:" in text

    def test_zero_match_returns_none(self, config: PipelineConfig, input_csv: Path) -> None:
        config_west = PipelineConfig(
            base_dir=config.base_dir,
            log_dir=config.log_dir,
            region="west",
        )
        result = process_csv(config_west, input_csv)
        assert result is None

    def test_zero_match_removes_filtered_file(self, config: PipelineConfig, input_csv: Path) -> None:
        config_west = PipelineConfig(
            base_dir=config.base_dir,
            log_dir=config.log_dir,
            region="west",
        )
        today = date.today().isoformat()
        process_csv(config_west, input_csv)
        filtered = config_west.processed_dir / f"sales_west_{today}.csv"
        assert not filtered.exists()

    def test_quoted_commas_handled(self, config: PipelineConfig) -> None:
        """csv.DictReader should handle quoted commas — unlike awk -F','."""
        p = config.raw_dir / "quoted.csv"
        p.write_text(QUOTED_COMMAS_CSV)

        result = process_csv(config, p)
        assert result is not None

        lines = result.read_text().strip().splitlines()
        # header + 2 northeast rows
        assert len(lines) == 3

    def test_returns_path_not_printed(self, config: PipelineConfig, input_csv: Path, capsys: pytest.CaptureFixture[str]) -> None:
        """Verify result is returned, not printed to stdout (bug fix)."""
        result = process_csv(config, input_csv)
        captured = capsys.readouterr()
        # The path should NOT appear in stdout — it's a return value
        assert result is not None
        assert str(result) not in captured.out

    def test_file_not_found_raises(self, config: PipelineConfig) -> None:
        with pytest.raises(FileNotFoundError):
            process_csv(config, Path("/nonexistent/file.csv"))
