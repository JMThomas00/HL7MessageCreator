#!/bin/bash

# Note: If this script isn't running correctly, 
# first run the following command:
# tr -d '\r' < progressdashboard.sh > progressdashboard_temp.sh && mv progressdashboard_temp.sh progressdashboard.sh

# Set base directory
BASE_DIR="."
LOG_FILE="$BASE_DIR/update_log.txt"

# Define folders
declare -A FOLDERS=(["PreviousDay"]="Yesterday" ["CurrentDay"]="Today" ["NextDay"]="Tomorrow")
DATE_FORMAT="%Y%m%d"

# Get dates
TODAY=$(date +"$DATE_FORMAT")
YESTERDAY=$(date -d "yesterday" +"$DATE_FORMAT")
TOMORROW=$(date -d "tomorrow" +"$DATE_FORMAT")

# Function to draw progress bar
draw_progress_bar() {
    local progress=$1
    local total=$2
    local width=40

    local percent=$((progress * 100 / total))
    local filled=$((progress * width / total))
    local empty=$((width - filled))

    local bar=$(printf "%${filled}s" | tr ' ' '#')
    bar+=$(printf "%${empty}s" | tr ' ' '-')

    printf "\r[%s] %d%% (%d/%d)" "$bar" "$percent" "$progress" "$total"
}

# Function to process files with progress bar
process_folder() {
    local src_folder="$1"
    local dst_folder="$2"
    local date_val="$3"
    local case_start="$4"
    local case_step="$5"
    local is_block="$6"

    # Color-coding folder names
    case "$src_folder" in
        "PreviousDay") color="\033[1;33m" ;;  # Yellow
        "CurrentDay")  color="\033[1;32m" ;;  # Green
        "NextDay")     color="\033[1;34m" ;;  # Blue
        *)             color="\033[0m"   ;;  # Default
    esac

    echo -e "${color}Processing folder: $src_folder\033[0m"

    mkdir -p "$BASE_DIR/$dst_folder"

    local files=("$BASE_DIR/$src_folder"/*.hl7)
    local total_files=${#files[@]}
    local case_id=$case_start
    local case_count=0

    for i in "${!files[@]}"; do
        local file="${files[$i]}"
        local out_file="$BASE_DIR/$dst_folder/$(basename "$file")"

        # For block folders, step through case IDs per 16 files
        if [[ "$is_block" == "true" && $((i % 16)) -eq 0 ]]; then
            case_id=$((case_start + case_count))
            case_count=$((case_count + 1))
        elif [[ "$is_block" == "false" ]]; then
            case_id=$((case_id + 1))
        fi

        # Replace only the date and caseID; leave names for other scripts to handle
        sed -e "s/{YYYYMMDD}/$date_val/g" \
            -e "s/{caseID}/$case_id/g" \
            "$file" > "$out_file"

        # Update progress bar
        draw_progress_bar $((i + 1)) "$total_files"
    done
    echo    # newline after progress bar
}

# Log start time
echo "Script run at $(date)" >> "$LOG_FILE"

# Run processing and capture success/failure
if process_folder "PreviousDay" "Yesterday" "$YESTERDAY" 1000 1 true &&
   process_folder "CurrentDay"  "Today"     "$TODAY"     1100 1 true &&
   process_folder "NextDay"     "Tomorrow"  "$TOMORROW"  1300 1 false; then
    echo "✅ Successfully updated messages." >> "$LOG_FILE"
else
    echo "❌ Error occurred while updating messages." >> "$LOG_FILE"
    echo "Error occurred while updating messages."
fi
