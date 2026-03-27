#!/bin/bash
#
# process_csv.sh - Filter and summarize sales CSV data
# Filters by region, calculates totals, writes output
#

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
DATA_DIR="${DATA_DIR:-$SCRIPT_DIR/../data}"
OUTPUT_DIR="${OUTPUT_DIR:-/tmp/data_pipeline/processed}"
REGION="${REGION:-northeast}"

source "$SCRIPT_DIR/logger.sh"

INPUT_FILE="${1:-$DATA_DIR/sales_q1.csv}"

if [ ! -f "$INPUT_FILE" ]; then
    log_msg "ERROR" "Input file not found: $INPUT_FILE"
    exit 1
fi

mkdir -p "$OUTPUT_DIR" 2>/dev/null

log_msg "INFO" "Processing CSV file: $(basename $INPUT_FILE)"

# count total data rows (skip header)
TOTAL_ROWS=$(tail -n +2 "$INPUT_FILE" | wc -l | tr -d ' ')

# filter by region using awk
TODAY=$(date '+%Y-%m-%d')
FILTERED_FILE="$OUTPUT_DIR/sales_${REGION}_${TODAY}.csv"

# write header first
head -1 "$INPUT_FILE" > "$FILTERED_FILE"

# filter rows — match region column (column 2)
awk -F',' -v region="$REGION" 'NR > 1 && $2 == region { print }' "$INPUT_FILE" >> "$FILTERED_FILE"

MATCHED=$(tail -n +2 "$FILTERED_FILE" | wc -l | tr -d ' ')
log_msg "INFO" "Filtered ${TOTAL_ROWS} rows, ${MATCHED} matched region=${REGION}"

if [ "$MATCHED" -eq 0 ]; then
    log_msg "WARN" "No data found for region: $REGION"
    rm -f "$FILTERED_FILE"
    exit 0
fi

# calculate total revenue for the region
TOTAL_REV=$(awk -F',' 'NR > 1 { sum += $5 } END { printf "%.2f", sum }' "$FILTERED_FILE")
log_msg "INFO" "Summary — Total revenue for ${REGION}: \$${TOTAL_REV}"

# generate a quick summary file too
SUMMARY_FILE="$OUTPUT_DIR/summary_${REGION}_${TODAY}.txt"
echo "=== Sales Summary ===" > "$SUMMARY_FILE"
echo "Region: $REGION" >> "$SUMMARY_FILE"
echo "Date: $TODAY" >> "$SUMMARY_FILE"
echo "Records: $MATCHED" >> "$SUMMARY_FILE"
echo "Total Revenue: \$${TOTAL_REV}" >> "$SUMMARY_FILE"
echo "" >> "$SUMMARY_FILE"

# breakdown by product
echo "Revenue by Product:" >> "$SUMMARY_FILE"
awk -F',' 'NR > 1 { rev[$3] += $5; count[$3]++ }
    END { for (p in rev) printf "  %-12s %d units  $%.2f\n", p, count[p], rev[p] }' \
    "$FILTERED_FILE" >> "$SUMMARY_FILE"

log_msg "INFO" "Summary written to $SUMMARY_FILE"

echo "$FILTERED_FILE"
