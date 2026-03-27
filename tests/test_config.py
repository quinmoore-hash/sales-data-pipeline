"""Tests for sales_data_pipeline.config."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from sales_data_pipeline.config import PipelineConfig


@pytest.fixture()
def tmp_base(tmp_path: Path) -> Path:
    return tmp_path / "pipeline"


class TestPipelineConfigDefaults:
    """Verify that defaults are applied when env vars are absent."""

    def test_default_api_url(self, tmp_base: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("API_URL", raising=False)
        monkeypatch.delenv("DATA_PIPELINE_API_KEY", raising=False)
        monkeypatch.delenv("OUTPUT_DIR", raising=False)
        monkeypatch.delenv("ARCHIVE_DIR", raising=False)
        monkeypatch.delenv("LOG_DIR", raising=False)
        monkeypatch.delenv("REGION", raising=False)
        monkeypatch.delenv("MAX_AGE_DAYS", raising=False)
        monkeypatch.delenv("LOG_RETENTION_DAYS", raising=False)
        cfg = PipelineConfig(base_dir=tmp_base, log_dir=tmp_base / "logs")
        assert cfg.api_url == "https://api.example.com/v1/sales"

    def test_default_region(self, tmp_base: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("REGION", raising=False)
        cfg = PipelineConfig(base_dir=tmp_base, log_dir=tmp_base / "logs")
        assert cfg.region == "northeast"

    def test_default_max_age_days(self, tmp_base: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("MAX_AGE_DAYS", raising=False)
        cfg = PipelineConfig(base_dir=tmp_base, log_dir=tmp_base / "logs")
        assert cfg.max_age_days == 30

    def test_default_log_retention_days(self, tmp_base: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("LOG_RETENTION_DAYS", raising=False)
        cfg = PipelineConfig(base_dir=tmp_base, log_dir=tmp_base / "logs")
        assert cfg.log_retention_days == 7

    def test_default_fetch_timeout_and_retries(self, tmp_base: Path) -> None:
        cfg = PipelineConfig(base_dir=tmp_base, log_dir=tmp_base / "logs")
        assert cfg.fetch_timeout == 30
        assert cfg.fetch_retries == 3


class TestPipelineConfigEnvVars:
    """Verify that environment variables override defaults."""

    def test_api_url_from_env(self, tmp_base: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("API_URL", "https://custom.api/v2")
        cfg = PipelineConfig(base_dir=tmp_base, log_dir=tmp_base / "logs")
        assert cfg.api_url == "https://custom.api/v2"

    def test_region_from_env(self, tmp_base: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("REGION", "midwest")
        cfg = PipelineConfig(base_dir=tmp_base, log_dir=tmp_base / "logs")
        assert cfg.region == "midwest"

    def test_max_age_from_env(self, tmp_base: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("MAX_AGE_DAYS", "60")
        cfg = PipelineConfig(base_dir=tmp_base, log_dir=tmp_base / "logs")
        assert cfg.max_age_days == 60

    def test_log_retention_from_env(self, tmp_base: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("LOG_RETENTION_DAYS", "14")
        cfg = PipelineConfig(base_dir=tmp_base, log_dir=tmp_base / "logs")
        assert cfg.log_retention_days == 14

    def test_api_key_from_env(self, tmp_base: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("DATA_PIPELINE_API_KEY", "secret123")
        cfg = PipelineConfig(base_dir=tmp_base, log_dir=tmp_base / "logs")
        assert cfg.api_key == "secret123"


class TestPipelineConfigDirectories:
    """Verify directory creation and computed paths."""

    def test_computed_dirs(self, tmp_base: Path) -> None:
        cfg = PipelineConfig(base_dir=tmp_base, log_dir=tmp_base / "logs")
        assert cfg.raw_dir == tmp_base / "raw"
        assert cfg.processed_dir == tmp_base / "processed"

    def test_dirs_created(self, tmp_base: Path) -> None:
        cfg = PipelineConfig(base_dir=tmp_base, log_dir=tmp_base / "logs")
        assert cfg.raw_dir.is_dir()
        assert cfg.processed_dir.is_dir()
        assert cfg.archive_dir.is_dir()
        assert cfg.log_dir.is_dir()

    def test_archive_dir_defaults_to_base(self, tmp_base: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("ARCHIVE_DIR", raising=False)
        cfg = PipelineConfig(base_dir=tmp_base, log_dir=tmp_base / "logs")
        assert cfg.archive_dir == tmp_base / "archive"

    def test_archive_dir_from_env(self, tmp_base: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        custom = tmp_base / "custom_archive"
        monkeypatch.setenv("ARCHIVE_DIR", str(custom))
        cfg = PipelineConfig(base_dir=tmp_base, log_dir=tmp_base / "logs")
        assert cfg.archive_dir == custom
        assert custom.is_dir()

    def test_empty_api_key_warns(self, tmp_base: Path, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture) -> None:
        monkeypatch.delenv("DATA_PIPELINE_API_KEY", raising=False)
        with caplog.at_level("WARNING", logger="sales_data_pipeline"):
            PipelineConfig(base_dir=tmp_base, log_dir=tmp_base / "logs")
        assert "DATA_PIPELINE_API_KEY" in caplog.text
