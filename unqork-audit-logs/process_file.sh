#!/bin/bash

# --- Configuration Variables ---
TARGET_DIR="./2025-november-december"       # <--- SET YOUR SPECIFIC DIRECTORY PATH HERE
OUTPUT_CSV_FILE="2025-november-december-output.csv"
# -------------------------------

echo "Starting batch processing for all files in directory: $TARGET_DIR"

# Ensure the target directory exists
if [ ! -d "$TARGET_DIR" ]; then
    echo "Error: Target directory '$TARGET_DIR' not found."
    exit 1
fi

# Remove the output file if it already exists before we start
if [ -f "$OUTPUT_CSV_FILE" ]; then
    rm "$OUTPUT_CSV_FILE"
    echo "Removed previous $OUTPUT_CSV_FILE"
fi

# 1. Print the CSV Header ONCE at the beginning of the combined file
echo '"userid","ipaddress","timestamp"' > "$OUTPUT_CSV_FILE"
echo "Header written."

# 2. Loop through every item in the target directory
# We use find/while loop for robust handling of generic filenames and potential spaces
find "$TARGET_DIR" -maxdepth 1 -type f | while IFS= read -r INPUT_FILE; do

    echo "--> Processing file: $INPUT_FILE"

    # Use jq to process the current file (NDJSON format expected)
    # The '>>' appends the data to the existing combined CSV file
    # We rely on jq to silently fail/ignore non-JSON data if it encounters non-compliant files
    jq -r '
      select(.actor.identifier.value | startswith("ngl")) |
      [
    .actor.identifier.value,
    .context.clientIp,
    .timestamp
      ] | @csv
    ' "$INPUT_FILE" >> "$OUTPUT_CSV_FILE"

done

echo "Batch processing complete."
echo "All data combined into: $OUTPUT_CSV_FILE"
