#!/bin/bash
#
# fetch_data.sh - Download daily sales data from the API
# Usually run by the pipeline, but can be called standalone too
#

API_URL="${API_URL:-https://api.example.com/v1/sales}"
API_KEY="${DATA_PIPELINE_API_KEY:-}"
OUTPUT_DIR="${OUTPUT_DIR:-/tmp/data_pipeline/raw}"
TIMEOUT=30
RETRIES=3

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# source the logger if it exists
if [ -f "$SCRIPT_DIR/logger.sh" ]; then
    source "$SCRIPT_DIR/logger.sh"
else
    # fallback if logger isn't found
    log_msg() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1: $2"; }
fi

if [ -z "$API_KEY" ]; then
    log_msg "WARN" "DATA_PIPELINE_API_KEY is not set, requests may fail"
fi

# make output dir if needed
mkdir -p "$OUTPUT_DIR" 2>/dev/null
if [ $? -ne 0 ]; then
    log_msg "ERROR" "Could not create output directory: $OUTPUT_DIR"
    exit 1
fi

TODAY=$(date '+%Y-%m-%d')
OUTPUT_FILE="$OUTPUT_DIR/daily_sales_${TODAY}.csv"

# check if we already downloaded today
if [ -f "$OUTPUT_FILE" ]; then
    log_msg "WARN" "File already exists: $OUTPUT_FILE — skipping download"
    exit 0
fi

log_msg "INFO" "Fetching data from ${API_URL}/daily"

# do the actual download with retries
ATTEMPT=0
while [ $ATTEMPT -lt $RETRIES ]; do
    ATTEMPT=$((ATTEMPT + 1))

    HTTP_CODE=$(curl -s -o "$OUTPUT_FILE" -w "%{http_code}" \
        -H "Authorization: Bearer ${API_KEY}" \
        -H "Accept: text/csv" \
        --max-time $TIMEOUT \
        "${API_URL}/daily?date=${TODAY}" 2>/dev/null)

    if [ "$HTTP_CODE" = "200" ]; then
        log_msg "INFO" "API response: ${HTTP_CODE} OK"
        LINES=$(wc -l < "$OUTPUT_FILE" | tr -d ' ')
        log_msg "INFO" "Downloaded ${LINES} records to ${OUTPUT_FILE}"
        exit 0
    else
        log_msg "WARN" "Attempt ${ATTEMPT}/${RETRIES} failed (HTTP ${HTTP_CODE})"
        sleep 2
    fi
done

log_msg "ERROR" "All ${RETRIES} download attempts failed"
rm -f "$OUTPUT_FILE"  # cleanup partial file
exit 1
