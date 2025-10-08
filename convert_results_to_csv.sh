#!/bin/bash

# Change to the script's directory
cd "$(dirname "$0")"

echo "Converting all JSON result files to CSV format..."
echo ""

python3 process_result_csv.py output/ --pattern "**/*_results.json" --verbose

echo ""
echo "Done! CSV files have been created alongside each JSON result file."
echo "You can now open the CSV files in Excel or other spreadsheet applications."
