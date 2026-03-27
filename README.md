# Sales Data Pipeline

Internal tool for pulling daily sales data from the API, filtering by region, and archiving results.

## Python Package (recommended)

The pipeline has been rewritten as a proper Python package in `src/sales_data_pipeline/`. The original Bash scripts are preserved in `scripts/` for reference.

### Installation

```bash
# Install the package (editable / development mode)
pip install -e .

# Include dev dependencies (pytest, responses) for testing
pip install -e ".[dev]"
```

### Usage

```bash
# Run the full pipeline
export DATA_PIPELINE_API_KEY="your-key-here"
sales-pipeline

# Or run as a module
python -m sales_data_pipeline

# Use the standalone logger
python -m sales_data_pipeline.logger INFO "something happened"
```

### Running Tests

```bash
pip install -e ".[dev]"
pytest
```

## How It Works

1. **Fetch** (`fetch.py`) — Downloads the daily sales CSV from the API endpoint. Supports retries via `urllib3` and skips if today's file already exists.
2. **Process** (`process.py`) — Filters the CSV by region using `csv.DictReader` (correctly handles quoted commas), calculates revenue totals, and writes a summary report.
3. **Organize** (`organize.py`) — Moves processed files to the archive directory and renames raw files with a `.done` suffix.
4. **Cleanup** (`cleanup.py`) — Deletes files older than their retention period from archive, processed, and log directories.
5. **Logger** (`logger.py`) — Shared logging utility with dual stdout + file output.
6. **Orchestrator** (`__main__.py`) — Main entry point that calls everything in order with file locking.

## Directory Structure

```
├── src/sales_data_pipeline/
│   ├── __init__.py
│   ├── __main__.py        # pipeline orchestrator (replaces run_pipeline.sh)
│   ├── config.py          # centralized configuration
│   ├── logger.py          # logging setup
│   ├── fetch.py           # API data download
│   ├── process.py         # CSV filtering & summarization
│   ├── organize.py        # file move/rename/archive
│   └── cleanup.py         # old file removal
├── tests/
│   ├── test_config.py
│   ├── test_fetch.py
│   ├── test_process.py
│   ├── test_organize.py
│   └── test_cleanup.py
├── scripts/               # original bash scripts (kept for reference)
│   ├── run_pipeline.sh
│   ├── fetch_data.sh
│   ├── process_csv.sh
│   ├── organize_files.sh
│   ├── cleanup.sh
│   └── logger.sh
├── data/
│   ├── sales_q1.csv       # sample sales data
│   └── api_config.json    # API configuration
├── logs/
│   └── pipeline_2024-03-29.log   # sample log output
├── pyproject.toml
└── README.md
```

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `API_URL` | `https://api.example.com/v1/sales` | Base URL for the sales API |
| `DATA_PIPELINE_API_KEY` | *(none)* | Bearer token for API auth (warns if empty) |
| `OUTPUT_DIR` | `/tmp/data_pipeline` | Base output directory |
| `REGION` | `northeast` | Region to filter by |
| `ARCHIVE_DIR` | `$OUTPUT_DIR/archive` | Where processed files end up |
| `MAX_AGE_DAYS` | `30` | Days before cleanup removes archive/processed files |
| `LOG_RETENTION_DAYS` | `7` | Days before cleanup removes log files |
| `LOG_DIR` | `<project>/logs` | Where log files are written |

## Usage

```bash
# Run the full pipeline (Python)
export DATA_PIPELINE_API_KEY="your-key-here"
sales-pipeline

# Or run as a module
python -m sales_data_pipeline

# Run the original bash pipeline (kept for reference)
bash scripts/run_pipeline.sh
```

## Bug Fixes (vs. original Bash scripts)

- **`OUTPUT_DIR` no longer mutated:** `run_pipeline.sh` used to overwrite `OUTPUT_DIR` (lines 34, 50, 63) causing `organize_files.sh` to use the same directory for both `RAW_DIR` and `PROCESSED_DIR`. The Python version uses a `PipelineConfig` dataclass with separate, immutable `raw_dir` and `processed_dir` fields.
- **Organize uses `move` instead of `copy`:** `organize_files.sh` used `cp` (line 38) so files would pile up indefinitely. Now uses `shutil.move`.
- **File locking added:** A new `fcntl.flock`-based lock prevents concurrent pipeline runs (addresses the known concurrency issue).
- **Log retention is now configurable:** `cleanup.sh` hardcoded `OLD_LOG_DAYS=7` (line 50) but reported all removals as "older than MAX_AGE_DAYS". The Python version uses a separate `LOG_RETENTION_DAYS` env var and reports correct thresholds.
- **CSV parsing handles quoted commas:** `process_csv.sh` used `awk -F','` which breaks on quoted commas. The Python version uses `csv.DictReader`.
- **Process output is a return value:** `process_csv.sh` printed the output path to stdout (line 68) which got mixed with log messages. The Python version returns it as a function return value.
