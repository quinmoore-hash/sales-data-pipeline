# Sales Data Pipeline

Internal tool for pulling daily sales data from the API, filtering by region, and archiving results.

**⚠️ This is a collection of Bash scripts that has grown organically. It works, but could really use a rewrite in Python.**

## How It Works

1. **`fetch_data.sh`** — Downloads the daily sales CSV from the API endpoint using `curl`. Supports retries and basic auth via env vars.
2. **`process_csv.sh`** — Filters the CSV by region (default: `northeast`) and generates a summary with revenue totals per product. Uses `awk` and `grep`.
3. **`organize_files.sh`** — Copies processed files to the archive directory and renames raw files with a `.done` suffix so they don't get re-processed.
4. **`cleanup.sh`** — Deletes files older than 30 days from archive, processed, and log directories.
5. **`logger.sh`** — Shared logging utility. Sourced by all other scripts. Can also be called standalone.
6. **`run_pipeline.sh`** — Main entry point that calls everything in order. This is what cron runs.

## Directory Structure

```
├── scripts/
│   ├── run_pipeline.sh      # main pipeline (calls the others)
│   ├── fetch_data.sh        # API data download
│   ├── process_csv.sh       # CSV filtering & summarization
│   ├── organize_files.sh    # file move/rename/archive
│   ├── cleanup.sh           # old file removal
│   └── logger.sh            # logging utility
├── data/
│   ├── sales_q1.csv         # sample sales data
│   └── api_config.json      # API configuration
├── logs/
│   └── pipeline_2024-03-29.log   # sample log output
└── README.md
```

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `API_URL` | `https://api.example.com/v1/sales` | Base URL for the sales API |
| `DATA_PIPELINE_API_KEY` | *(none)* | Bearer token for API auth |
| `OUTPUT_DIR` | `/tmp/data_pipeline` | Base output directory |
| `REGION` | `northeast` | Region to filter by |
| `ARCHIVE_DIR` | `$OUTPUT_DIR/archive` | Where processed files end up |
| `MAX_AGE_DAYS` | `30` | Days before cleanup removes files |
| `LOG_DIR` | `./logs` | Where log files are written |

## Usage

```bash
# Run the full pipeline
export DATA_PIPELINE_API_KEY="your-key-here"
bash scripts/run_pipeline.sh

# Or run individual steps
REGION=midwest bash scripts/process_csv.sh data/sales_q1.csv

# Check logs
cat logs/pipeline_$(date '+%Y-%m-%d').log
```

## Known Issues

- The `OUTPUT_DIR` variable gets overwritten by `run_pipeline.sh` which is confusing
- Error handling is inconsistent between scripts
- `organize_files.sh` uses `cp` instead of `mv` so files can pile up
- No locking mechanism — if two pipelines run at once, things will break
- The cleanup script hardcodes 7 days for logs but uses `MAX_AGE_DAYS` for everything else
- No unit tests (obviously)
