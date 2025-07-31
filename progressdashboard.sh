#!/bin/bash

# Set base directory and log file
BASE_DIR="."
PROCESSED_DIR="$BASE_DIR/Processed"
LOG_FILE="$BASE_DIR/update_log.txt"

# Define folder mappings (source -> destination folder)
declare -A FOLDERS=(["PreviousDay"]="Yesterday" ["CurrentDay"]="Today" ["NextDay"]="Tomorrow")
DATE_FORMAT="%Y%m%d"

# Get dates
TODAY=$(date +"$DATE_FORMAT")
YESTERDAY=$(date -d "yesterday" +"$DATE_FORMAT")
TOMORROW=$(date -d "tomorrow" +"$DATE_FORMAT")

# Set initial case IDs per folder
declare -A CASE_ID_START=(["PreviousDay"]=1000 ["CurrentDay"]=1100 ["NextDay"]=1300)

# Draw progress bar
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

# Process each folder
process_folder() {
    local src_folder="$1"
    local dst_folder="$2"
    local date_val="$3"
    local case_id_start="$4"
    local is_block="$5"

    # Color output
    case "$src_folder" in
        "PreviousDay") color="\033[1;33m" ;;  # Yellow
        "CurrentDay")  color="\033[1;32m" ;;  # Green
        "NextDay")     color="\033[1;34m" ;;  # Blue
        *)             color="\033[0m"   ;;  # Default
    esac

    echo -e "${color}Processing folder: $src_folder → Processed/$dst_folder\033[0m"

    mkdir -p "$PROCESSED_DIR/$dst_folder"
    rm -f "$PROCESSED_DIR/$dst_folder"/*.hl7 2>/dev/null  # Clear old files

    local files=("$BASE_DIR/$src_folder"/*.hl7)
    local total_files=${#files[@]}
    local patient_index=0
    local case_id=$case_id_start

    for i in "${!files[@]}"; do
        local file="${files[$i]}"
        local out_file="$PROCESSED_DIR/$dst_folder/$(basename "$file")"

        # Determine if we're starting a new patient block
        if [[ "$is_block" == "true" ]]; then
            if (( i % 15 == 0 )); then
                case_id=$((case_id_start + patient_index))
                patient_index=$((patient_index + 1))
            fi
        else
            # One message per patient in NextDay
            case_id=$((case_id_start + patient_index))
            patient_index=$((patient_index + 1))
        fi

        # Replace variables
        sed -e "s/{YYYYMMDD}/$date_val/g" \
            -e "s/{caseID}/$case_id/g" \
            -e "s/{patientMRN}/$case_id/g" \
            "$file" > "$out_file"

        draw_progress_bar $((i + 1)) "$total_files"
    done
    echo    # newline after progress bar
}

# Log start time
echo "Script run at $(date)" >> "$LOG_FILE"

# Execute processing for each folder
if process_folder "PreviousDay" "Yesterday" "$YESTERDAY" ${CASE_ID_START["PreviousDay"]} true &&
   process_folder "CurrentDay" "Today" "$TODAY" ${CASE_ID_START["CurrentDay"]} true &&
   process_folder "NextDay" "Tomorrow" "$TOMORROW" ${CASE_ID_START["NextDay"]} false; then
    echo "✅ Successfully updated HL7 messages." >> "$LOG_FILE"
else
    echo "❌ Error occurred while updating messages." >> "$LOG_FILE"
    echo "Error occurred while updating messages."
fi
