#!/bin/bash
#
# cleanup.sh - Remove old files from pipeline directories
# Run this periodically (cron?) to keep disk usage in check
#

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/logger.sh"

ARCHIVE_DIR="${ARCHIVE_DIR:-/tmp/data_pipeline/archive}"
PROCESSED_DIR="${OUTPUT_DIR:-/tmp/data_pipeline/processed}"
LOG_DIR="${LOG_DIR:-$SCRIPT_DIR/../logs}"
MAX_AGE_DAYS="${MAX_AGE_DAYS:-30}"

log_msg "INFO" "Cleanup started — removing files older than ${MAX_AGE_DAYS} days"

REMOVED=0

cleanup_dir() {
    local dir="$1"
    local pattern="$2"

    if [ ! -d "$dir" ]; then
        log_msg "WARN" "Directory does not exist, skipping: $dir"
        return
    fi

    # find old files and delete them
    while IFS= read -r file; do
        [ -z "$file" ] && continue
        rm -f "$file"
        if [ $? -eq 0 ]; then
            log_msg "INFO" "Removed: $file"
            REMOVED=$((REMOVED + 1))
        else
            log_msg "ERROR" "Failed to remove: $file"
        fi
    done < <(find "$dir" -name "$pattern" -type f -mtime +${MAX_AGE_DAYS} 2>/dev/null)
}

# clean up archived csv files
cleanup_dir "$ARCHIVE_DIR" "*.csv"
cleanup_dir "$ARCHIVE_DIR" "*.csv.done"

# clean up old processed outputs
cleanup_dir "$PROCESSED_DIR" "sales_*.csv"
cleanup_dir "$PROCESSED_DIR" "summary_*.txt"

# clean old log files but keep last 7 days worth regardless of MAX_AGE
OLD_LOG_DAYS=7
while IFS= read -r logfile; do
    [ -z "$logfile" ] && continue
    rm -f "$logfile"
    REMOVED=$((REMOVED + 1))
done < <(find "$LOG_DIR" -name "pipeline_*.log" -type f -mtime +${OLD_LOG_DAYS} 2>/dev/null)

log_msg "INFO" "Cleanup complete — removed ${REMOVED} files older than ${MAX_AGE_DAYS} days"
