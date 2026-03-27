"""Tests for sales_data_pipeline.fetch."""

from __future__ import annotations

from datetime import date
from pathlib import Path
from unittest.mock import patch

import pytest
import responses
from responses import matchers

from sales_data_pipeline.config import PipelineConfig
from sales_data_pipeline.fetch import FetchError, fetch_data


@pytest.fixture()
def config(tmp_path: Path) -> PipelineConfig:
    return PipelineConfig(
        base_dir=tmp_path / "pipeline",
        log_dir=tmp_path / "logs",
        api_key="test-key",
    )


class TestFetchData:
    """Tests for the fetch_data function."""

    @responses.activate
    def test_successful_download(self, config: PipelineConfig) -> None:
        csv_body = "date,region,product,units,revenue\n2024-01-01,northeast,Widget,10,100.00\n"
        today = date.today().isoformat()
        responses.add(
            responses.GET,
            f"{config.api_url}/daily",
            body=csv_body,
            status=200,
            content_type="text/csv",
        )

        result = fetch_data(config)
        assert result.exists()
        assert result.name == f"daily_sales_{today}.csv"
        assert result.read_text() == csv_body

    def test_skip_if_exists(self, config: PipelineConfig) -> None:
        today = date.today().isoformat()
        existing = config.raw_dir / f"daily_sales_{today}.csv"
        existing.write_text("existing data")

        result = fetch_data(config)
        assert result == existing
        assert result.read_text() == "existing data"

    @responses.activate
    def test_raises_fetch_error_on_failure(self, config: PipelineConfig) -> None:
        responses.add(
            responses.GET,
            f"{config.api_url}/daily",
            body="Internal Server Error",
            status=500,
        )

        with pytest.raises(FetchError, match="download attempts failed"):
            fetch_data(config)

    @responses.activate
    def test_partial_file_cleaned_on_failure(self, config: PipelineConfig) -> None:
        today = date.today().isoformat()
        output_file = config.raw_dir / f"daily_sales_{today}.csv"

        responses.add(
            responses.GET,
            f"{config.api_url}/daily",
            body="Internal Server Error",
            status=500,
        )

        with pytest.raises(FetchError):
            fetch_data(config)

        assert not output_file.exists()

    def test_warns_when_api_key_empty(self, tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
        cfg = PipelineConfig(
            base_dir=tmp_path / "pipeline",
            log_dir=tmp_path / "logs",
            api_key="",
        )
        today = date.today().isoformat()
        # Create the file so it short-circuits before making a request
        (cfg.raw_dir / f"daily_sales_{today}.csv").write_text("data")

        with caplog.at_level("WARNING", logger="sales_data_pipeline"):
            fetch_data(cfg)
        # The warning is emitted in PipelineConfig.__post_init__
        assert "DATA_PIPELINE_API_KEY" in caplog.text
