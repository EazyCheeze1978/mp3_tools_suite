#!/bin/bash

#############################################
# MP3 Reduction Tool (Preview / Reduce / CSV / Safe Delete)
# v1.0.3 — Parallelized Reduction + Progress Monitor (Fixed)
#############################################

# -------- Colors --------
RED="\033[0;31m"
GREEN="\033[0;32m"
YELLOW="\033[1;33m"
CYAN="\033[0;36m"
MAGENTA="\033[0;35m"
RESET="\033[0m"

# -------- Config --------
TARGET_BITRATE=128000   # 128 kbps in bps
BATCH_SIZE=50
PARALLEL_JOBS=8

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
for cmd in ffprobe ffmpeg stat bc; do
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

# -------- Reducible File Iterator (unchanged) --------
iterate_reducible_files() {
    local callback="$1"

    find . -type f -iname "*.mp3" ! -iname "*_reduced.mp3" | while read -r file; do
        local bitrate
        bitrate=$(ffprobe -v error -select_streams a:0 \
                  -show_entries stream=bit_rate \
                  -of default=noprint_wrappers=1:nokey=1 "$file")

        if [ -z "$bitrate" ]; then
            echo -e "${YELLOW}Skipping (no bitrate info):${RESET} $file"
            continue
        fi

        if [ "$bitrate" -le "$TARGET_BITRATE" ]; then
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

        local estimated_size
        estimated_size=$(echo "$TARGET_BITRATE * $duration / 8" | bc)

        "$callback" "$file" "$bitrate" "$filesize" "$duration" "$estimated_size"
    done
}

# -------- Preview Mode (unchanged except pauses removed) --------
preview_callback() {
    local file="$1"
    local bitrate="$2"
    local filesize="$3"
    local duration="$4"
    local estimated_size="$5"

    COUNT=$((COUNT + 1))
    BATCH_CURRENT_SIZE=$((BATCH_CURRENT_SIZE + filesize))
    BATCH_EST_SIZE=$((BATCH_EST_SIZE + estimated_size))
    TOTAL_CURRENT_SIZE=$((TOTAL_CURRENT_SIZE + filesize))
    TOTAL_EST_SIZE=$((TOTAL_EST_SIZE + estimated_size))

    echo -e "${MAGENTA}FILE:${RESET} $file"
    echo "  Current bitrate: $bitrate bps"
    echo "  Current size:    $filesize bytes"
    echo "  Duration:        ${duration}s"
    echo "  Estimated new:   $estimated_size bytes"
    echo ""

    if [ $((COUNT % BATCH_SIZE)) -eq 0 ]; then
        echo -e "${CYAN}--- Batch of ${BATCH_SIZE} files ---${RESET}"
        echo "  Batch current size:  $BATCH_CURRENT_SIZE bytes"
        echo "  Batch estimated size: $BATCH_EST_SIZE bytes"
        echo "  Batch savings:        $((BATCH_CURRENT_SIZE - BATCH_EST_SIZE)) bytes"
        echo ""
        echo -e "${CYAN}Cumulative totals so far:${RESET}"
        echo "  Total current size:   $TOTAL_CURRENT_SIZE bytes"
        echo "  Total estimated size: $TOTAL_EST_SIZE bytes"
        echo "  Total savings:        $((TOTAL_CURRENT_SIZE - TOTAL_EST_SIZE)) bytes"
        echo ""
        BATCH_CURRENT_SIZE=0
        BATCH_EST_SIZE=0
    fi
}

preview_mode() {
    echo ""
    echo -e "${MAGENTA}Preview Mode (reducible files only)${RESET}"
    prompt_interactive_mode

    COUNT=0
    BATCH_CURRENT_SIZE=0
    BATCH_EST_SIZE=0
    TOTAL_CURRENT_SIZE=0
    TOTAL_EST_SIZE=0

    iterate_reducible_files preview_callback

    if [ $((COUNT % BATCH_SIZE)) -ne 0 ]; then
        echo -e "${CYAN}--- Final partial batch (${COUNT % BATCH_SIZE} files) ---${RESET}"
        echo "  Batch current size:  $BATCH_CURRENT_SIZE bytes"
        echo "  Batch estimated size: $BATCH_EST_SIZE bytes"
        echo "  Batch savings:        $((BATCH_CURRENT_SIZE - BATCH_EST_SIZE)) bytes"
        echo ""
    fi

    echo -e "${GREEN}=== Preview Totals ===${RESET}"
    echo "Total files considered: $COUNT"
    echo "Total current size:     $TOTAL_CURRENT_SIZE bytes"
    echo "Total estimated size:   $TOTAL_EST_SIZE bytes"
    echo "Total savings:          $((TOTAL_CURRENT_SIZE - TOTAL_EST_SIZE)) bytes"
    echo ""
}

# -------- NEW: Parallel Worker (exported for subshell visibility) --------
reduce_one_file() {
    local file="$1"
    local dir base
    dir=$(dirname "$file")
    base=$(basename "$file" .mp3)

    ffmpeg -loglevel error -y -i "$file" -b:a 128k "${dir}/${base}_reduced.mp3"

    echo 1 >> "$PROGRESS_FILE"
}
export -f reduce_one_file

# -------- NEW: Progress Monitor --------
progress_monitor() {
    local spinner='|/-\'
    local i=0

    while true; do
        DONE=$(wc -l < "$PROGRESS_FILE")
        PCT=$(( DONE * 100 / TOTAL ))

        ACTIVE=$(pgrep -fc "ffmpeg -loglevel error -y -i")

        printf "\rProcessed %d / %d (%d%%) | Active workers: %d | %c" \
            "$DONE" "$TOTAL" "$PCT" "$ACTIVE" "${spinner:i++%4:1}"

        sleep 1
    done
}

# -------- NEW: Parallelized Reduction Mode (fixed) --------
reduce_mode() {
    echo ""
    echo -e "${MAGENTA}Reduction Mode (128 kbps)${RESET}"
    echo -e "${YELLOW}Warning:${RESET} This will create new *_reduced.mp3 files."
    read -p "Proceed with reduction? [y/N]: " ans
    case "$ans" in
        y|Y) ;;
        *) echo -e "${YELLOW}Reduction cancelled.${RESET}"; return ;;
    esac

    FILE_LIST=$(mktemp)
    PROGRESS_FILE=$(mktemp)

    find . -type f -iname "*.mp3" ! -iname "*_reduced.mp3" | while read -r file; do
        bitrate=$(ffprobe -v error -select_streams a:0 \
                  -show_entries stream=bit_rate \
                  -of default=noprint_wrappers=1:nokey=1 "$file")

        if [ -n "$bitrate" ] && [ "$bitrate" -gt "$TARGET_BITRATE" ]; then
            echo "$file" >> "$FILE_LIST"
        fi
    done

    TOTAL=$(wc -l < "$FILE_LIST")
    echo -e "${CYAN}Reducing $TOTAL files...${RESET}"

    progress_monitor &
    MONITOR_PID=$!

    xargs -P "$PARALLEL_JOBS" -I {} bash -c 'reduce_one_file "$@"' _ {} < "$FILE_LIST"

    kill "$MONITOR_PID" 2>/dev/null
    echo ""

    echo -e "${GREEN}Reduction complete.${RESET}"
}

# -------- CSV Mode (unchanged) --------
csv_callback() {
    local file="$1"
    local bitrate="$2"
    local filesize="$3"
    local duration="$4"
    local estimated_size="$5"

    COUNT=$((COUNT + 1))
    BATCH_CURRENT_SIZE=$((BATCH_CURRENT_SIZE + filesize))
    BATCH_EST_SIZE=$((BATCH_EST_SIZE + estimated_size))
    TOTAL_CURRENT_SIZE=$((TOTAL_CURRENT_SIZE + filesize))
    TOTAL_EST_SIZE=$((TOTAL_EST_SIZE + estimated_size))

    echo "\"$file\",$bitrate,$filesize,$duration,$estimated_size,$((filesize - estimated_size))" >> "$CSV_FILE"

    if [ $((COUNT % BATCH_SIZE)) -eq 0 ] && [ "$CSV_BATCH_TOTALS" -eq 1 ]; then
        echo "\"BATCH_TOTAL_${COUNT}\",$TARGET_BITRATE,$BATCH_CURRENT_SIZE,,${BATCH_EST_SIZE},$((BATCH_CURRENT_SIZE - BATCH_EST_SIZE))" >> "$CSV_FILE"
        BATCH_CURRENT_SIZE=0
        BATCH_EST_SIZE=0
    fi
}

csv_mode() {
    echo ""
    echo -e "${MAGENTA}CSV Export (reducible files only)${RESET}"
    prompt_interactive_mode
    prompt_csv_totals_mode

    CSV_FILE="reduction_report_$(date +%Y%m%d_%H%M%S).csv"
    echo "file,bitrate,current_size,duration,estimated_new_size,savings" > "$CSV_FILE"

    COUNT=0
    BATCH_CURRENT_SIZE=0
    BATCH_EST_SIZE=0
    TOTAL_CURRENT_SIZE=0
    TOTAL_EST_SIZE=0

    iterate_reducible_files csv_callback

    if [ "$CSV_BATCH_TOTALS" -eq 1 ] && [ $((COUNT % BATCH_SIZE)) -ne 0 ]; then
        echo "\"BATCH_TOTAL_${COUNT}\",$TARGET_BITRATE,$BATCH_CURRENT_SIZE,,${BATCH_EST_SIZE},$((BATCH_CURRENT_SIZE - BATCH_EST_SIZE))" >> "$CSV_FILE"
    fi

    echo "\"GRAND_TOTAL\",$TARGET_BITRATE,$TOTAL_CURRENT_SIZE,,$TOTAL_EST_SIZE,$((TOTAL_CURRENT_SIZE - TOTAL_EST_SIZE))" >> "$CSV_FILE"

    echo -e "${GREEN}CSV export complete:${RESET} $CSV_FILE"
}

# -------- Safe Delete Mode (unchanged) --------
safe_delete_mode() {
    echo ""
    echo -e "${MAGENTA}Safe Delete Mode${RESET}"
    echo -e "${YELLOW}This will delete original MP3s that have verified *_reduced.mp3 counterparts.${RESET}"
    read -p "Scan and show summary first? [Y/n]: " ans
    case "$ans" in
        n|N) ;;
        *) ;;
    esac

    local candidates=0
    local total_reclaim=0

    while IFS= read -r file; do
        local dir base reduced
        dir=$(dirname "$file")
        base=$(basename "$file" .mp3)
        reduced="${dir}/${base}_reduced.mp3"

        if [ ! -f "$reduced" ]; then
            continue
        fi
        if [ ! -s "$reduced" ]; then
            continue
        fi
        if [ ! "$reduced" -nt "$file" ]; then
            continue
        fi

        ffprobe -v error -show_entries format=duration \
            -of default=noprint_wrappers=1:nokey=1 "$reduced" >/dev/null 2>&1 || continue

        local size
        size=$(stat -c%s "$file")
        total_reclaim=$((total_reclaim + size))
        candidates=$((candidates + 1))
    done < <(find . -type f -iname "*.mp3" ! -iname "*_reduced.mp3")

    if [ "$candidates" -eq 0 ]; then
        echo -e "${YELLOW}No safe delete candidates found.${RESET}"
        return
    fi

    echo -e "${CYAN}Safe delete candidates:${RESET}"
    echo "  Files:          $candidates"
    echo "  Space reclaim:  $total_reclaim bytes"
    echo ""
    read -p "Proceed with deletion? [y/N]: " confirm
    case "$confirm" in
        y|Y) ;;
        *) echo -e "${YELLOW}Deletion cancelled.${RESET}"; return ;;
    esac

    local delete_log="delete_log_$(date +%Y%m%d_%H%M%S).txt"
    echo "Delete log - $(date)" > "$delete_log"

    while IFS= read -r file; do
        local dir base reduced
        dir=$(dirname "$file")
        base=$(basename "$file" .mp3)
        reduced="${dir}/${base}_reduced.mp3"

        if [ ! -f "$reduced" ]; then
            continue
        fi
        if [ ! -s "$reduced" ]; then
            continue
        fi
        if [ ! "$reduced" -nt "$file" ]; then
            continue
        fi

        ffprobe -v error -show_entries format=duration \
            -of default=noprint_wrappers=1:nokey=1 "$reduced" >/dev/null 2>&1 || continue

        echo -e "${GREEN}Deleting original:${RESET} $file"
        echo "Deleted: $file" >> "$delete_log"
        rm -f "$file"
    done < <(find . -type f -iname "*.mp3" ! -iname "*_reduced.mp3")

    echo -e "${GREEN}Safe delete complete.${RESET}"
    echo "Details logged in: $delete_log"
}

# -------- Main Menu --------
while true; do
    echo ""
    echo -e "${MAGENTA}MP3 Reduction Tool${RESET}"
    echo "------------------"
    echo "1) Preview files that would be reduced"
    echo "2) Reduce files to 128 kbps"
    echo "3) Export CSV report (reducible files)"
    echo "4) Safe-delete originals (with verified reduced files)"
    echo "5) Exit"
    echo ""
    read -p "Choose an option [1-5]: "