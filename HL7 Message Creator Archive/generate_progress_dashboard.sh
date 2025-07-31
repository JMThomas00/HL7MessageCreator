#!/bin/bash

# Go to the script's directory
cd "$(dirname "$0")"

# Input files
SURGEON_FILE="surgeon_names.csv"
STAFF_FILE="names.csv"

# Folder-caseID map
declare -A CASE_ID_START=( ["PreviousDay"]=1000 ["CurrentDay"]=1100 ["NextDay"]=1300 )
declare -A CASE_ID_NEXT=( ["PreviousDay"]=1000 ["CurrentDay"]=1100 ["NextDay"]=1300 )
declare -A CASE_ID_COUNT=( ["PreviousDay"]=0 ["CurrentDay"]=0 ["NextDay"]=0 )

# Folder output map
declare -A OUTPUT_MAP=( ["PreviousDay"]="Yesterday" ["CurrentDay"]="Today" ["NextDay"]="Tomorrow" )

# Date values
TODAY=$(date +"%Y%m%d")
YESTERDAY=$(date -d "yesterday" +"%Y%m%d")
TOMORROW=$(date -d "tomorrow" +"%Y%m%d")

# Load name arrays
readarray -t SURGEON_NAMES < <(tail -n +2 "$SURGEON_FILE")
readarray -t STAFF_NAMES < <(tail -n +2 "$STAFF_FILE")

# Random name picker
get_random_name() {
    local names=("${!1}")
    local line="${names[RANDOM % ${#names[@]}]}"
    echo "$line"
}

# Process files in a folder
process_folder() {
    local input_folder=$1
    local output_folder=${OUTPUT_MAP[$input_folder]}
    local date_value

    echo "Processing $input_folder → $output_folder"

    case $input_folder in
        "PreviousDay") date_value=$YESTERDAY ;;
        "CurrentDay")  date_value=$TODAY ;;
        "NextDay")     date_value=$TOMORROW ;;
    esac

    mkdir -p "$output_folder"

    for file in "$input_folder"/*.hl7; do
        [[ -e "$file" ]] || continue  # skip if no files

        echo "Updating $file"
        echo "Original content:"
        cat "$file"

        filename=$(basename "$file")
        content=$(<"$file")

        # Select a random surgeon and staff members for other roles
        IFS=$'\t' read -r surgeon_first surgeon_last <<< "$(get_random_name SURGEON_NAMES[@])"
        IFS=$'\t' read -r staff_first staff_last <<< "$(get_random_name STAFF_NAMES[@])"

        # Case ID rules
        caseID=${CASE_ID_NEXT[$input_folder]}
        if [[ "$input_folder" == "NextDay" ]]; then
            ((CASE_ID_NEXT[$input_folder]++))
        else
            ((CASE_ID_COUNT[$input_folder]++))
            if (( CASE_ID_COUNT[$input_folder] % 15 == 0 )); then
                ((CASE_ID_NEXT[$input_folder]++))
            fi
        fi

        echo "Performing replacements..."

        # Updated sed command with specific placeholders
        updated_content=$(echo "$content" | sed \
            -e "s/{YYYYMMDD}/$date_value/g" \
            -e "s/{primaryFirstName}/$surgeon_first/g" \
            -e "s/{primaryLastName}/$surgeon_last/g" \
            -e "s/{staffFirstName}/$staff_first/g" \
            -e "s/{staffLastName}/$staff_last/g" \
            -e "s/{caseID}/$caseID/g" \
            -e "s/{lastName}/$staff_last/g" \
            -e "s/{firstName}/$staff_first/g")

        # Debug print of updated content
        echo "Updated content (debug):"
        echo "$updated_content"

        # Write to file with proper HL7 line endings (carriage return)
        printf "%s\r" "$updated_content" > "$output_folder/$filename"
    done
}

# Run processing for all three folders
process_folder "PreviousDay"
process_folder "CurrentDay"
process_folder "NextDay"

echo "✅ HL7 generation complete!"