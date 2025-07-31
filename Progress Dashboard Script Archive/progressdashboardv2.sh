#!/bin/bash

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

# Load names into arrays (correctly handling tabs and trimming spaces)
readarray -t STAFF_FIRST_NAMES < <(tail -n +2 "$BASE_DIR/names.csv" | cut -f1 | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
readarray -t STAFF_LAST_NAMES  < <(tail -n +2 "$BASE_DIR/names.csv" | cut -f2 | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')

readarray -t SURGEON_FIRST_NAMES < <(tail -n +2 "$BASE_DIR/surgeon_names.csv" | cut -f1 | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
readarray -t SURGEON_LAST_NAMES  < <(tail -n +2 "$BASE_DIR/surgeon_names.csv" | cut -f2 | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')


get_random_name() {
    local first_names=("${!1}")
    local last_names=("${!2}")
    local idx=$((RANDOM % ${#first_names[@]}))
    local first="${first_names[$idx]}"
    local last="${last_names[$idx]}"

    # Sanitize the names to ensure HL7 compatibility (trim spaces, no special chars)
    first=$(echo "$first" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
    last=$(echo "$last" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')

    # Ensure no extra spaces in names
    first=$(echo "$first" | tr -s ' ')
    last=$(echo "$last" | tr -s ' ')

    # Return in correct HL7 format: LastName^FirstName
    echo "$last^$first"
}


# Function to process files
process_folder() {
    local src_folder="$1"
    local dst_folder="$2"
    local date_val="$3"
    local case_start="$4"
    local case_step="$5"
    local is_block="$6"

    mkdir -p "$BASE_DIR/$dst_folder"

    local files=("$BASE_DIR/$src_folder"/*.hl7)
    local case_id=$case_start
    local case_count=0
    local current_surgeon=""

    # Process files in the folder
    for i in "${!files[@]}"; do
        local file="${files[$i]}"
        local out_file="$BASE_DIR/$dst_folder/$(basename "$file")"

        # For block folders (PreviousDay/CurrentDay), refresh names every 16 files
        if [[ "$is_block" == "true" && $((i % 16)) -eq 0 ]]; then
            surgeon=$(get_random_name SURGEON_FIRST_NAMES[@] SURGEON_LAST_NAMES[@])
            current_surgeon=(${surgeon//^/ })

            current_staff=()
            for _ in {1..4}; do
                staff=$(get_random_name STAFF_FIRST_NAMES[@] STAFF_LAST_NAMES[@])
                current_staff+=("${staff//^/ }")
            done
            case_id=$((case_start + case_count))
            case_count=$((case_count + 1))
        elif [[ "$is_block" == "false" ]]; then
            surgeon=$(get_random_name SURGEON_FIRST_NAMES[@] SURGEON_LAST_NAMES[@])
            current_surgeon=(${surgeon//^/ })

            current_staff=()
            for _ in {1..4}; do
                staff=$(get_random_name STAFF_FIRST_NAMES[@] STAFF_LAST_NAMES[@])
                current_staff+=("${staff//^/ }")
            done
            case_id=$((case_id + 1))
        fi


        # Now we replace variables in the file and ensure staff and surgeon names are handled properly
        sed -e "s/{YYYYMMDD}/$date_val/g" \
            -e "s/{primaryFirstName}/${current_surgeon[1]}/g" \
            -e "s/{primaryLastName}/${current_surgeon[0]}/g" \
            -e "s/{firstName}/${current_staff[1]}/g" \
            -e "s/{lastName}/${current_staff[0]}/g" \
            -e "s/{caseID}/$case_id/g" \
            "$file" > "$out_file"
    done
}



# Run processing for each folder
{
    echo "Script run at $(date)"

    # Run the process_folder functions and check for success
    if process_folder "PreviousDay" "Yesterday" "$YESTERDAY" 1000 1 true &&
       process_folder "CurrentDay"  "Today"     "$TODAY"     1100 1 true &&
       process_folder "NextDay"     "Tomorrow"  "$TOMORROW"  1300 1 false; then
        echo "✅ Successfully updated messages."
    else
        echo "❌ Error occurred while updating messages."
    fi

    echo
} >> "$LOG_FILE" 2>&1
