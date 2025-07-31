#!/bin/bash

# Use current directory
BASE_DIR="."
LOG_FILE="$BASE_DIR/script_log.txt"

# Create log file if it doesn’t exist
touch "$LOG_FILE"

# Function to log messages
log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> "$LOG_FILE"
}

# Get dates
TODAY=$(date '+%Y%m%d')
YESTERDAY=$(date -d "yesterday" '+%Y%m%d')
TOMORROW=$(date -d "tomorrow" '+%Y%m%d')

# Create output directories if they don’t exist
mkdir -p Yesterday Today Tomorrow

# Load names into arrays (handling tabs and trimming spaces)
mapfile -t STAFF_FIRST_NAMES < <(tail -n +2 "$BASE_DIR/names.csv" | cut -f1 | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
mapfile -t STAFF_LAST_NAMES  < <(tail -n +2 "$BASE_DIR/names.csv" | cut -f2 | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
mapfile -t SURGEON_FIRST_NAMES < <(tail -n +2 "$BASE_DIR/surgeon_names.csv" | cut -f1 | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
mapfile -t SURGEON_LAST_NAMES  < <(tail -n +2 "$BASE_DIR/surgeon_names.csv" | cut -f2 | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')

# Function to process files
process_folder() {
    local src_folder="$1"
    local dst_folder="$2"
    local date_val="$3"
    local case_start="$4"
    local is_block="$5"  # true for 16-message blocks, false for per-message increment

    # Clear destination folder
    rm -f "$dst_folder"/*.hl7
    mkdir -p "$dst_folder"

    local files=("$BASE_DIR/$src_folder"/*.hl7)
    local case_id=$case_start
    local msg_count=0

    for file in "${files[@]}"; do
        if [ -f "$file" ]; then
            local out_file="$dst_folder/$(basename "$file")"
            local temp_file=$(mktemp)

            # Update case_id based on rules
            if [ "$is_block" = "true" ]; then
                if [ $((msg_count % 16)) -eq 0 ]; then
                    ((case_id++))
                fi
            else
                ((case_id++))
            fi
            ((msg_count++))

            # Select a primary surgeon for this message
            surgeon_idx=$((RANDOM % ${#SURGEON_FIRST_NAMES[@]}))
            primary_fname="${SURGEON_FIRST_NAMES[$surgeon_idx]}"
            primary_lname="${SURGEON_LAST_NAMES[$surgeon_idx]}"

            # Process line by line
            while IFS= read -r line || [ -n "$line" ]; do
                # Replace date and caseID globally
                line=$(echo "$line" | sed "s/{YYYYMMDD}/$date_val/g; s/{caseID}/$case_id/g")

                # Skip if line doesn’t contain placeholders we’re targeting
                if [[ ! "$line" =~ \{[p]rimaryLastName\}|\{lastName\}|\{firstName\} ]]; then
                    echo "$line" >> "$temp_file"
                    continue
                fi

                # Split line into fields based on HL7 separator
                IFS='|' read -r -a fields <<< "$line"

                # Process specific segments
                case "${fields[0]}" in
                    "PV1"|"AIP")
                        # For PV1 (field 17, index 17) or AIP (field 2, index 2)
                        target_field_idx=$([[ "${fields[0]}" == "PV1" ]] && echo 17 || echo 2)
                        if [ ${#fields[@]} -gt "$target_field_idx" ]; then
                            field="${fields[$target_field_idx]}"
                            # Split field into components
                            IFS='^' read -r -a components <<< "$field"

                            # Replace placeholders in name components
                            for i in "${!components[@]}"; do
                                if [[ "${components[$i]}" == "{primaryLastName}" ]]; then
                                    components[$i]="$primary_lname"
                                elif [[ "${components[$i]}" == "{primaryFirstName}" ]]; then
                                    components[$i]="$primary_fname"
                                elif [[ "${components[$i]}" == "{lastName}" ]]; then
                                    staff_idx=$((RANDOM % ${#STAFF_LAST_NAMES[@]}))
                                    components[$i]="${STAFF_LAST_NAMES[$staff_idx]}"
                                elif [[ "${components[$i]}" == "{firstName}" ]]; then
                                    staff_idx=$((RANDOM % ${#STAFF_FIRST_NAMES[@]}))
                                    components[$i]="${STAFF_FIRST_NAMES[$staff_idx]}"
                                fi
                            done

                            # Rebuild the field
                            fields[$target_field_idx]=$(IFS='^'; echo "${components[*]}")
                        fi
                        ;;
                    "NTE")
                        # Check comment field (field 3, index 3) for {firstName}
                        if [ ${#fields[@]} -gt 3 ] && [[ "${fields[3]}" =~ \{firstName\} ]]; then
                            staff_idx=$((RANDOM % ${#STAFF_FIRST_NAMES[@]}))
                            fields[3]="${fields[3]//\{firstName\}/${STAFF_FIRST_NAMES[$staff_idx]}}"
                        fi
                        ;;
                esac

                # Rebuild the line
                IFS='|'; echo "${fields[*]}" >> "$temp_file"
            done < "$file"

            # Move temp file to output
            mv "$temp_file" "$out_file"
        fi
    done
}

# Process all folders
process_folder "PreviousDay" "Yesterday" "$YESTERDAY" "1000" "true" && \
process_folder "CurrentDay" "Today" "$TODAY" "1100" "true" && \
process_folder "NextDay" "Tomorrow" "$TOMORROW" "1300" "false"

# Check if processing was successful
if [ $? -eq 0 ]; then
    log_message "Script ran successfully"
    echo "Processing completed successfully"
else
    log_message "Script failed"
    echo "Processing failed"
    exit 1
fi

exit 0