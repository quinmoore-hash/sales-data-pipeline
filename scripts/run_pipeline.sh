#!/bin/bash
#
# run_pipeline.sh - Main entry point for the data pipeline
# Calls the other scripts in order. This is what cron runs.
#

set -e  # exit on first error... mostly

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/logger.sh"

# --- Config ---
export API_URL="${API_URL:-https://api.example.com/v1/sales}"
export OUTPUT_DIR="${OUTPUT_DIR:-/tmp/data_pipeline}"
export REGION="${REGION:-northeast}"
export ARCHIVE_DIR="${ARCHIVE_DIR:-$OUTPUT_DIR/archive}"

# override OUTPUT_DIR for sub-scripts that expect specific subdirs
RAW_DIR="$OUTPUT_DIR/raw"
PROC_DIR="$OUTPUT_DIR/processed"

log_msg "INFO" "Pipeline started"

# quick env check
if [ -z "$DATA_PIPELINE_API_KEY" ]; then
    log_msg "WARN" "DATA_PIPELINE_API_KEY not set — API calls will probably fail"
    # don't exit, let fetch_data.sh handle it
fi

log_msg "INFO" "Environment check passed"

# --- Step 1: Fetch data ---
log_msg "INFO" "Step 1: Fetching data..."
export OUTPUT_DIR="$RAW_DIR"
bash "$SCRIPT_DIR/fetch_data.sh"
FETCH_STATUS=$?

if [ $FETCH_STATUS -ne 0 ]; then
    log_msg "ERROR" "Data fetch failed (exit code $FETCH_STATUS)"
    # try to continue with existing data if we have it
    if [ -z "$(ls -A $RAW_DIR/*.csv 2>/dev/null)" ]; then
        log_msg "ERROR" "No existing data to fall back on, aborting"
        exit 1
    fi
    log_msg "WARN" "Using existing data files instead"
fi

# --- Step 2: Process CSV ---
log_msg "INFO" "Step 2: Processing data..."
export OUTPUT_DIR="$PROC_DIR"

# process the main data file
PROCESSED_FILE=$(bash "$SCRIPT_DIR/process_csv.sh")
PROC_STATUS=$?

if [ $PROC_STATUS -ne 0 ]; then
    log_msg "ERROR" "CSV processing failed (exit code $PROC_STATUS)"
    exit 1
fi

# --- Step 3: Organize files ---
log_msg "INFO" "Step 3: Organizing files..."
export OUTPUT_DIR="$PROC_DIR"
bash "$SCRIPT_DIR/organize_files.sh"
ORG_STATUS=$?

if [ $ORG_STATUS -ne 0 ]; then
    log_msg "WARN" "File organization had errors (exit code $ORG_STATUS)"
    # not fatal, continue
fi

# --- Step 4: Cleanup old stuff ---
log_msg "INFO" "Step 4: Running cleanup..."
bash "$SCRIPT_DIR/cleanup.sh"
# don't really care if cleanup fails
CLEAN_STATUS=$?

log_msg "INFO" "Pipeline finished successfully (exit code 0)"
echo ""
echo "Done. Check logs at: $LOG_FILE"
