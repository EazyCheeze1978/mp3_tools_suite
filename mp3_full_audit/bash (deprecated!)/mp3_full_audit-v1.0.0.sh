#!/bin/bash

###############################################################
# MP3 FULL AUDIT TOOL
# - Scans ALL MP3 files (not just reducible ones)
# - Reports bitrate, size, duration
# - Supports interactive/autonomous batching
# - CSV export with batch totals or final totals
# - Optional directory argument
# - Color-coded output
###############################################################

# -------- Colors --------
RED="\033[0;31m"
GREEN="\033[0;32m"
YELLOW="\033[1;33m"
CYAN="\033[0;36m"
MAGENTA="\033[0;35m"
RESET="\033[0m"

# -------- Config --------
BATCH_SIZE=50

# -------- Directory Handling --------
if [ -n "$1" ]; then
    if [ -d "$1" ]; then
        cd "$1" || { echo -e "${RED}Failed to enter directory: $1${RESET}"; exit 1; }
    else
        echo -e "${RED}Directory does not exist: $1${RESET}"
        exit 1
    fi
fi

# -------- Dependency Check --------
for cmd in ffprobe stat bc; do
    if ! command -v "$cmd" >/dev/null 2>&1; then
        echo -e "${RED}Missing required command: $cmd${RESET}"
        exit 1
    fi
done

# -------- Helpers --------
prompt_interactive_mode() {
    echo ""
    echo -e "${CYAN}Display mode:${RESET}"
    echo "1) Interactive (pause every ${BATCH_SIZE} files)"
    echo "2) Autonomous (no pauses)"
    read -p "Choose display mode [1-2]: " mode
    case "$mode" in
        1) INTERACTIVE=1 ;;
        2) INTERACTIVE=0 ;;
        *) echo -e "${YELLOW}Invalid choice, defaulting to autonomous.${RESET}"; INTERACTIVE=0 ;;
    esac
}

pause_if_interactive() {
    local count="$1"
    if [ "$INTERACTIVE" -eq 1 ] && [ $((count % BATCH_SIZE)) -eq 0 ]; then
        read -p "Press Enter to continue..." _
    fi
}

prompt_csv_totals_mode() {
    echo ""
    echo -e "${CYAN}CSV totals mode:${RESET}"
    echo "1) Include batch totals every ${BATCH_SIZE} files"
    echo "2) Only final totals at the end"
    read -p "Choose CSV totals mode [1-2]: " mode
    case "$mode" in
        1) CSV_BATCH_TOTALS=1 ;;
        2) CSV_BATCH_TOTALS=0 ;;
        *) echo -e "${YELLOW}Invalid choice, defaulting to final totals only.${RESET}"; CSV_BATCH_TOTALS=0 ;;
    esac
}

# Iterate over ALL MP3 files and call a callback:
# callback "$file" "$bitrate" "$filesize" "$duration"
iterate_all_files() {
    local callback="$1"

    find . -type f -iname "*.mp3" | while read -r file; do
        local bitrate
        bitrate=$(ffprobe -v error -select_streams a:0 \
                  -show_entries stream=bit_rate \
                  -of default=noprint_wrappers=1:nokey=1 "$file")

        if [ -z "$bitrate" ]; then
            echo -e "${YELLOW}Skipping (no bitrate info):${RESET} $file"
            continue
        fi

        local filesize
        filesize=$(stat -c%s "$file")

        local duration
        duration=$(ffprobe -v error -show_entries format=duration \
                   -of default=noprint_wrappers=1:nokey=1 "$file")

        if [ -z "$duration" ]; then
            echo -e "${YELLOW}Skipping (no duration info):${RESET} $file"
            continue
        fi

        "$callback" "$file" "$bitrate" "$filesize" "$duration"
    done
}

# -------- Audit Mode --------
audit_callback() {
    local file="$1"
    local bitrate="$2"
    local filesize="$3"
    local duration="$4"

    COUNT=$((COUNT + 1))
    BATCH_SIZE_SUM=$((BATCH_SIZE_SUM + filesize))
    TOTAL_SIZE_SUM=$((TOTAL_SIZE_SUM + filesize))

    echo -e "${MAGENTA}FILE:${RESET} $file"
    echo "  Bitrate: $bitrate bps"
    echo "  Size:    $filesize bytes"
    echo "  Duration: ${duration}s"
    echo ""

    if [ $((COUNT % BATCH_SIZE)) -eq 0 ]; then
        echo -e "${CYAN}--- Batch of ${BATCH_SIZE} files ---${RESET}"
        echo "  Batch size: $BATCH_SIZE_SUM bytes"
        echo ""
        echo -e "${CYAN}Cumulative totals so far:${RESET}"
        echo "  Total size: $TOTAL_SIZE_SUM bytes"
        echo ""
        BATCH_SIZE_SUM=0
        pause_if_interactive "$COUNT"
    fi
}

audit_mode() {
    echo ""
    echo -e "${MAGENTA}Full Audit Mode (all MP3 files)${RESET}"
    prompt_interactive_mode

    COUNT=0
    BATCH_SIZE_SUM=0
    TOTAL_SIZE_SUM=0

    iterate_all_files audit_callback

    # Final partial batch
    if [ $((COUNT % BATCH_SIZE)) -ne 0 ]; then
        echo -e "${CYAN}--- Final partial batch (${COUNT % BATCH_SIZE} files) ---${RESET}"
        echo "  Batch size: $BATCH_SIZE_SUM bytes"
        echo ""
    fi

    echo -e "${GREEN}=== Audit Totals ===${RESET}"
    echo "Total files: $COUNT"
    echo "Total size:  $TOTAL_SIZE_SUM bytes"
    echo ""
}

# -------- CSV Export Mode --------
csv_callback() {
    local file="$1"
    local bitrate="$2"
    local filesize="$3"
    local duration="$4"

    COUNT=$((COUNT + 1))
    BATCH_SIZE_SUM=$((BATCH_SIZE_SUM + filesize))
    TOTAL_SIZE_SUM=$((TOTAL_SIZE_SUM + filesize))

    echo "\"$file\",$bitrate,$filesize,$duration" >> "$CSV_FILE"

    if [ $((COUNT % BATCH_SIZE)) -eq 0 ] && [ "$CSV_BATCH_TOTALS" -eq 1 ]; then
        echo "\"BATCH_TOTAL_${COUNT}\",,$BATCH_SIZE_SUM," >> "$CSV_FILE"
        BATCH_SIZE_SUM=0
    fi

    if [ "$INTERACTIVE" -eq 1 ] && [ $((COUNT % BATCH_SIZE)) -eq 0 ]; then
        echo -e "${CYAN}Processed $COUNT files so far...${RESET}"
        pause_if_interactive "$COUNT"
    fi
}

csv_mode() {
    echo ""
    echo -e "${MAGENTA}CSV Export (all MP3 files)${RESET}"
    prompt_interactive_mode
    prompt_csv_totals_mode

    CSV_FILE="full_audit_$(date +%Y%m%d_%H%M%S).csv"
    echo "file,bitrate,size,duration" > "$CSV_FILE"

    COUNT=0
    BATCH_SIZE_SUM=0
    TOTAL_SIZE_SUM=0

    iterate_all_files csv_callback

    # Final partial batch
    if [ "$CSV_BATCH_TOTALS" -eq 1 ] && [ $((COUNT % BATCH_SIZE)) -ne 0 ]; then
        echo "\"BATCH_TOTAL_${COUNT}\",,$BATCH_SIZE_SUM," >> "$CSV_FILE"
    fi

    # Final totals
    echo "\"GRAND_TOTAL\",,$TOTAL_SIZE_SUM," >> "$CSV_FILE"

    echo -e "${GREEN}CSV export complete:${RESET} $CSV_FILE"
}

# -------- Main Menu --------
while true; do
    echo ""
    echo -e "${MAGENTA}MP3 Full Audit Tool${RESET}"
    echo "-------------------"
    echo "1) Full audit (all MP3s)"
    echo "2) Export full CSV"
    echo "3) Exit"
    echo ""
    read -p "Choose an option [1-3]: " choice

    case "$choice" in
        1) audit_mode ;;
        2) csv_mode ;;
        3) echo "Goodbye."; exit 0 ;;
        *) echo -e "${YELLOW}Invalid choice.${RESET}" ;;
    esac
done
