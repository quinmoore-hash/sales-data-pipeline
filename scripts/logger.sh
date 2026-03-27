#!/bin/bash
#
# logger.sh - Simple logging utility
# Source this from other scripts, or run standalone to write a message
#

LOG_DIR="${LOG_DIR:-$(cd "$(dirname "$0")/../logs" && pwd)}"
LOG_FILE="${LOG_FILE:-$LOG_DIR/pipeline_$(date '+%Y-%m-%d').log}"

# create log dir — probably already exists but just in case
mkdir -p "$LOG_DIR" 2>/dev/null

log_msg() {
    local level="$1"
    local message="$2"
    local timestamp
    timestamp=$(date '+%Y-%m-%d %H:%M:%S')

    local entry="[${timestamp}] ${level}: ${message}"

    # always print to stdout
    echo "$entry"

    # also append to log file
    echo "$entry" >> "$LOG_FILE" 2>/dev/null
    if [ $? -ne 0 ]; then
        echo "[${timestamp}] WARN: Could not write to log file ${LOG_FILE}" >&2
    fi
}

# if someone runs this script directly with arguments, log the message
# usage: ./logger.sh INFO "something happened"
if [ "${BASH_SOURCE[0]}" = "$0" ]; then
    if [ $# -lt 2 ]; then
        echo "Usage: $0 <LEVEL> <MESSAGE>"
        echo "  Levels: INFO, WARN, ERROR"
        echo "  Example: $0 INFO \"Pipeline started\""
        exit 1
    fi

    LEVEL="$1"
    shift
    MESSAGE="$*"

    log_msg "$LEVEL" "$MESSAGE"
fi
