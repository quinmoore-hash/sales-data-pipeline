"""Data fetching module — replaces ``fetch_data.sh``.

Downloads the daily sales CSV from the API endpoint with retry logic.
"""

from __future__ import annotations

import logging
from datetime import date
from pathlib import Path

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from sales_data_pipeline.config import PipelineConfig

logger = logging.getLogger("sales_data_pipeline")


class FetchError(Exception):
    """Raised when data fetching fails after all retries."""


def fetch_data(config: PipelineConfig) -> Path:
    """Download today's sales CSV and return the path to the saved file.

    * Skips the download if the file already exists (like ``fetch_data.sh``
      lines 38-41).
    * Uses :mod:`urllib3` retry logic instead of a manual ``while`` loop.
    * Cleans up partial files on failure.

    Raises
    ------
    FetchError
        If the download fails after all retries.
    """
    today = date.today().isoformat()
    output_file = config.raw_dir / f"daily_sales_{today}.csv"

    # Already downloaded today
    if output_file.exists():
        logger.warning("File already exists: %s — skipping download", output_file)
        return output_file

    if not config.api_key:
        logger.warning("DATA_PIPELINE_API_KEY is not set, requests may fail")

    logger.info("Fetching data from %s/daily", config.api_url)

    # Build a session with automatic retries
    session = requests.Session()
    retry = Retry(
        total=config.fetch_retries,
        backoff_factor=1,
        status_forcelist=[500, 502, 503, 504],
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)

    try:
        response = session.get(
            f"{config.api_url}/daily",
            params={"date": today},
            headers={
                "Authorization": f"Bearer {config.api_key}",
                "Accept": "text/csv",
            },
            timeout=config.fetch_timeout,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        # Clean up any partial file
        output_file.unlink(missing_ok=True)
        raise FetchError(f"All {config.fetch_retries} download attempts failed") from exc

    # Write response content
    output_file.write_bytes(response.content)
    lines = len(response.text.splitlines())
    logger.info("API response: 200 OK")
    logger.info("Downloaded %d records to %s", lines, output_file)
    return output_file
