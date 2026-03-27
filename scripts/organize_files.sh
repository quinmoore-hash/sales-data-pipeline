#!/bin/bash
#
# organize_files.sh - Move and rename processed files
# Moves raw files to archive, renames with status suffix
#

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/logger.sh"

RAW_DIR="${OUTPUT_DIR:-/tmp/data_pipeline/raw}"
PROCESSED_DIR="${OUTPUT_DIR:-/tmp/data_pipeline/processed}"
ARCHIVE_DIR="${ARCHIVE_DIR:-/tmp/data_pipeline/archive}"

# create archive dir
mkdir -p "$ARCHIVE_DIR" 2>/dev/null
if [ $? -ne 0 ]; then
    log_msg "ERROR" "Cannot create archive directory: $ARCHIVE_DIR"
    exit 1
fi

# Move processed files to their final location
# (in a real setup this might be an S3 upload or network share copy)
MOVED=0
ERRORS=0

for f in "$PROCESSED_DIR"/sales_*.csv; do
    [ -f "$f" ] || continue

    BASENAME=$(basename "$f")
    DEST="$ARCHIVE_DIR/$BASENAME"

    # don't overwrite existing archived files
    if [ -f "$DEST" ]; then
        log_msg "WARN" "Archive file already exists, skipping: $DEST"
        continue
    fi

    cp "$f" "$DEST"
    if [ $? -eq 0 ]; then
        log_msg "INFO" "Moved processed file to $DEST"
        MOVED=$((MOVED + 1))
    else
        log_msg "ERROR" "Failed to copy $f to $DEST"
        ERRORS=$((ERRORS + 1))
    fi
done

# Rename raw files to mark them as done
for f in "$RAW_DIR"/daily_sales_*.csv; do
    [ -f "$f" ] || continue

    NEWNAME="${f}.done"
    mv "$f" "$NEWNAME" 2>/dev/null

    if [ $? -eq 0 ]; then
        log_msg "INFO" "Renamed raw file to $NEWNAME"
    else
        log_msg "ERROR" "Could not rename $f"
        ERRORS=$((ERRORS + 1))
    fi
done

log_msg "INFO" "Organize complete — moved ${MOVED} files, ${ERRORS} errors"

if [ $ERRORS -gt 0 ]; then
    exit 1
fi
exit 0
