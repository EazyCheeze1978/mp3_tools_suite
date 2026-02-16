#!/bin/bash

###############################################################
# MP3 FULL AUDIT TOOL (Enhanced)
#
# - Scans ALL MP3 files (not just reducible ones)
# - Reports bitrate, size, duration
# - Extracts basic ID3 metadata (title, artist, album)
# - Indicates whether ID3 tags are present
# - Optionally cross-references Playnite game metadata CSV
#   (Name, Sources, Id) to map folder IDs to game titles/sources
# - Supports interactive/autonomous batching
# - CSV export with batch totals or final totals
# - Optional directory argument (defaults to current directory)
# - Color-coded output
#
# Usage:
#   ./mp3_full_audit.sh
#   ./mp3_full_audit.sh "/path/to/music"
#
###############################################################

########################
# Color Definitions
########################
RED="\033[0;31m"
GREEN="\033[0;32m"
YELLOW="\033[1;33m"
CYAN="\033[0;36m"
MAGENTA="\033[0;35m"
RESET="\033[0m"

########################
# Configuration
########################
BATCH_SIZE=50

# Default Playnite CSV filename (can be adjusted if needed)
PLAYNITE_CSV_DEFAULT="titles_sources_ids.csv"

########################
# Directory Handling
########################
# If a directory argument is provided, attempt to cd into it.
if [ -n "$1" ]; then
    if [ -d "$1" ]; then
        cd "$1" || { echo -e "${RED}Failed to enter directory: $1${RESET}"; exit 1; }
    else
        echo -e "${RED}Directory does not exist: $1${RESET}"
        exit 1
    fi
fi

########################
# Dependency Check
########################
for cmd in ffprobe stat bc; do
    if ! command -v "$cmd" >/dev/null 2>&1; then
        echo -e "${RED}Missing required command: $cmd${RESET}"
        exit 1
    fi
done

########################
# Global State Variables
########################
INTERACTIVE=0
CSV_BATCH_TOTALS=0
TOTAL_FILES=0

# Associative arrays for Playnite metadata (requires Bash 4+)
declare -A GAME_TITLE_BY_ID
declare -A GAME_SOURCE_BY_ID

########################
# Helper: Prompt for interactive vs autonomous mode
########################
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

########################
# Helper: Pause if interactive and at batch boundary
########################
pause_if_interactive() {
    local count="$1"
    if [ "$INTERACTIVE" -eq 1 ] && [ $((count % BATCH_SIZE)) -eq 0 ]; then
        read -p "Press Enter to continue..." _
    fi
}

########################
# Helper: Prompt for CSV totals mode
########################
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

########################
# Helper: Pre-scan to count total MP3 files
########################
prescan_total_files() {
    TOTAL_FILES=$(find . -type f -iname "*.mp3" | wc -l)
    if [ "$TOTAL_FILES" -eq 0 ]; then
        echo -e "${YELLOW}No MP3 files found in this directory.${RESET}"
    else
        echo -e "${CYAN}Found $TOTAL_FILES MP3 files to process.${RESET}"
    fi
}

########################
# Helper: Progress display
########################
show_progress() {
    local count="$1"
    if [ "$TOTAL_FILES" -gt 0 ]; then
        local percent=$((count * 100 / TOTAL_FILES))
        # Simple progress bar (width 20)
        local filled=$((percent / 5))
        local bar=""
        for ((i=0; i<filled; i++)); do bar+="#"; done
        for ((i=filled; i<20; i++)); do bar+="."; done
        echo -ne "${CYAN}[${bar}] ${percent}% (${count}/${TOTAL_FILES})\r${RESET}"
    fi
}

########################
# Forgiving CSV Loader for Playnite Metadata
########################
load_playnite_csv() {
    local csv_file=""

    # Auto-detect default CSV or ask user
    if [ -f "$PLAYNITE_CSV_DEFAULT" ]; then
        csv_file="$PLAYNITE_CSV_DEFAULT"
        echo -e "${GREEN}Found Playnite CSV:${RESET} $csv_file"
    else
        echo ""
        echo -e "${CYAN}Playnite CSV not found as '${PLAYNITE_CSV_DEFAULT}'.${RESET}"
        read -p "Enter Playnite CSV filename to use (or leave blank to skip): " user_csv
        if [ -n "$user_csv" ] && [ -f "$user_csv" ]; then
            csv_file="$user_csv"
            echo -e "${GREEN}Using Playnite CSV:${RESET} $csv_file"
        elif [ -n "$user_csv" ]; then
            echo -e "${YELLOW}File not found: $user_csv. Skipping Playnite metadata.${RESET}"
            return
        else
            echo -e "${YELLOW}No Playnite CSV specified. Skipping Playnite metadata.${RESET}"
            return
        fi
    fi

    # Forgiving CSV reader:
    # - Strips BOM
    # - Converts CRLF → LF
    # - Trims whitespace
    # - Skips blank/malformed lines
    local is_header=1
    local line

    while IFS= read -r line || [ -n "$line" ]; do

        # Strip BOM if present
        line="${line//$'\ufeff'/}"

        # Trim whitespace
        line="$(echo "$line" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"

        # Skip blank lines
        [ -z "$line" ] && continue

        # Skip header
        if [ $is_header -eq 1 ]; then
            is_header=0
            continue
        fi

        # Extract fields
        local name source id
        name=$(echo "$line"   | awk -F',' '{print $1}')
        source=$(echo "$line" | awk -F',' '{print $2}')
        id=$(echo "$line"     | awk -F',' '{print $3}')

        # Skip malformed lines
        [ -z "$id" ] && continue

        # Remove surrounding quotes
        name=$(echo "$name" | sed 's/^"//;s/"$//')
        source=$(echo "$source" | sed 's/^"//;s/"$//')
        id=$(echo "$id" | sed 's/^"//;s/"$//')

        # Store in associative arrays
        GAME_TITLE_BY_ID["$id"]="$name"
        GAME_SOURCE_BY_ID["$id"]="$source"

    done < <(sed 's/\r$//' "$csv_file")

    echo -e "${GREEN}Loaded Playnite metadata for ${#GAME_TITLE_BY_ID[@]} IDs.${RESET}"
}

########################
# Helper: Extract folder ID and map to Playnite metadata
########################
get_playnite_metadata_for_file() {
    local file="$1"
    local dir id game_title game_source

    dir=$(dirname "$file")
    # Assume the immediate folder name is the ID
    id=$(basename "$dir")

    game_title=""
    game_source=""

    if [ -n "${GAME_TITLE_BY_ID[$id]}" ]; then
        game_title="${GAME_TITLE_BY_ID[$id]}"
        game_source="${GAME_SOURCE_BY_ID[$id]}"
    fi

    echo "$id|$game_title|$game_source"
}

########################
# Helper: Extract ID3 metadata using ffprobe
########################
get_id3_metadata() {
    local file="$1"

    # Extract title, artist, album via ffprobe tags
    local title artist album
    title=$(ffprobe -v error -show_entries format_tags=title \
            -of default=noprint_wrappers=1:nokey=1 "$file" 2>/dev/null | head -n 1)
    artist=$(ffprobe -v error -show_entries format_tags=artist \
             -of default=noprint_wrappers=1:nokey=1 "$file" 2>/dev/null | head -n 1)
    album=$(ffprobe -v error -show_entries format_tags=album \
            -of default=noprint_wrappers=1:nokey=1 "$file" 2>/dev/null | head -n 1)

    # Determine if any ID3 tags are present
    local has_tags="no"
    if [ -n "$title" ] || [ -n "$artist" ] || [ -n "$album" ]; then
        has_tags="yes"
    fi

    # Return as pipe-separated string
    echo "$title|$artist|$album|$has_tags"
}

########################
# Core iterator: ALL MP3 files
#
# Calls a callback function with:
#   callback "$file" "$bitrate" "$filesize" "$duration" \
#             "$title" "$artist" "$album" "$has_tags" \
#             "$game_id" "$game_title" "$game_source"
########################
iterate_all_files() {
    local callback="$1"

    find . -type f -iname "*.mp3" | while read -r file; do
        # Bitrate
        local bitrate
        bitrate=$(ffprobe -v error -select_streams a:0 \
                  -show_entries stream=bit_rate \
                  -of default=noprint_wrappers=1:nokey=1 "$file")

        if [ -z "$bitrate" ]; then
            echo -e "${YELLOW}Skipping (no bitrate info):${RESET} $file"
            continue
        fi

        # Filesize
        local filesize
        filesize=$(stat -c%s "$file")

        # Duration
        local duration
        duration=$(ffprobe -v error -show_entries format=duration \
                   -of default=noprint_wrappers=1:nokey=1 "$file")

        if [ -z "$duration" ]; then
            echo -e "${YELLOW}Skipping (no duration info):${RESET} $file"
            continue
        fi

        # ID3 metadata
        local id3 title artist album has_tags
        id3=$(get_id3_metadata "$file")
        title=$(echo "$id3"    | awk -F'|' '{print $1}')
        artist=$(echo "$id3"   | awk -F'|' '{print $2}')
        album=$(echo "$id3"    | awk -F'|' '{print $3}')
        has_tags=$(echo "$id3" | awk -F'|' '{print $4}')

        # Playnite metadata
        local pm game_id game_title game_source
        pm=$(get_playnite_metadata_for_file "$file")
        game_id=$(echo "$pm"       | awk -F'|' '{print $1}')
        game_title=$(echo "$pm"    | awk -F'|' '{print $2}')
        game_source=$(echo "$pm"   | awk -F'|' '{print $3}')

        "$callback" "$file" "$bitrate" "$filesize" "$duration" \
                    "$title" "$artist" "$album" "$has_tags" \
                    "$game_id" "$game_title" "$game_source"
    done
}

########################
# AUDIT MODE
########################

# Callback for on-screen audit
audit_callback() {
    local file="$1"
    local bitrate="$2"
    local filesize="$3"
    local duration="$4"
    local title="$5"
    local artist="$6"
    local album="$7"
    local has_tags="$8"
    local game_id="$9"
    local game_title="${10}"
    local game_source="${11}"

    COUNT=$((COUNT + 1))
    BATCH_SIZE_SUM=$((BATCH_SIZE_SUM + filesize))
    TOTAL_SIZE_SUM=$((TOTAL_SIZE_SUM + filesize))

    # Progress bar in-place
    show_progress "$COUNT"

    echo ""
    echo -e "${MAGENTA}FILE:${RESET} $file"
    echo "  Bitrate:  $bitrate bps"
    echo "  Size:     $filesize bytes"
    echo "  Duration: ${duration}s"

    if [ "$has_tags" = "yes" ]; then
        echo -e "  ID3 Tags: ${GREEN}present${RESET}"
    else
        echo -e "  ID3 Tags: ${YELLOW}missing${RESET}"
    fi

    if [ -n "$title" ]; then
        echo "  Title:    $title"
    fi
    if [ -n "$artist" ]; then
        echo "  Artist:   $artist"
    fi
    if [ -n "$album" ]; then
        echo "  Album:    $album"
    fi

    if [ -n "$game_id" ] || [ -n "$game_title" ] || [ -n "$game_source" ]; then
        echo "  Game ID:      $game_id"
        echo "  Game Title:   $game_title"
        echo "  Game Source:  $game_source"
    fi

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
    load_playnite_csv
    prescan_total_files

    COUNT=0
    BATCH_SIZE_SUM=0
    TOTAL_SIZE_SUM=0

    iterate_all_files audit_callback

    # Clear progress line
    echo -ne "\r\033[K"

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

########################
# CSV EXPORT MODE
########################

# Callback for CSV export
csv_callback() {
    local file="$1"
    local bitrate="$2"
    local filesize="$3"
    local duration="$4"
    local title="$5"
    local artist="$6"
    local album="$7"
    local has_tags="$8"
    local game_id="$9"
    local game_title="${10}"
    local game_source="${11}"

    COUNT=$((COUNT + 1))
    BATCH_SIZE_SUM=$((BATCH_SIZE_SUM + filesize))
    TOTAL_SIZE_SUM=$((TOTAL_SIZE_SUM + filesize))

    # Progress bar in-place
    show_progress "$COUNT"

    # Escape double quotes in text fields for CSV safety
    local esc_file esc_title esc_artist esc_album esc_game_title esc_game_source
    esc_file=$(echo "$file" | sed 's/"/""/g')
    esc_title=$(echo "$title" | sed 's/"/""/g')
    esc_artist=$(echo "$artist" | sed 's/"/""/g')
    esc_album=$(echo "$album" | sed 's/"/""/g')
    esc_game_title=$(echo "$game_title" | sed 's/"/""/g')
    esc_game_source=$(echo "$game_source" | sed 's/"/""/g')

    # CSV columns:
    # file,bitrate,size,duration,title,artist,album,has_id3_tags,game_id,game_title,game_source
    echo "\"$esc_file\",$bitrate,$filesize,$duration,\"$esc_title\",\"$esc_artist\",\"$esc_album\",$has_tags,\"$game_id\",\"$esc_game_title\",\"$esc_game_source\"" >> "$CSV_FILE"

    if [ $((COUNT % BATCH_SIZE)) -eq 0 ] && [ "$CSV_BATCH_TOTALS" -eq 1 ]; then
        echo "\"BATCH_TOTAL_${COUNT}\",,$BATCH_SIZE_SUM,,,,,,,," >> "$CSV_FILE"
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
    load_playnite_csv
    prescan_total_files

    CSV_FILE="full_audit_$(date +%Y%m%d_%H%M%S).csv"
    echo "file,bitrate,size,duration,title,artist,album,has_id3_tags,game_id,game_title,game_source" > "$CSV_FILE"

    COUNT=0
    BATCH_SIZE_SUM=0
    TOTAL_SIZE_SUM=0

    iterate_all_files csv_callback

    # Clear progress line
    echo -ne "\r\033[K"

    # Final partial batch totals
    if [ "$CSV_BATCH_TOTALS" -eq 1 ] && [ $((COUNT % BATCH_SIZE)) -ne 0 ]; then
        echo "\"BATCH_TOTAL_${COUNT}\",,$BATCH_SIZE_SUM,,,,,,,," >> "$CSV_FILE"
    fi

    # Final totals row
    echo "\"GRAND_TOTAL\",,$TOTAL_SIZE_SUM,,,,,,,," >> "$CSV_FILE"

    echo -e "${GREEN}CSV export complete:${RESET} $CSV_FILE"
}

########################
# MAIN MENU
########################
while true; do
    echo ""
    echo -e "${MAGENTA}MP3 Full Audit Tool (Enhanced)${RESET}"
    echo "-------------------------------"
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
