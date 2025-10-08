#!/bin/bash

# Change to the script's directory
cd "$(dirname "$0")"

echo "Combining CSV files from results and logs based on timestamp..."
echo ""

python3 combine_csv_files.py output/ --verbose

echo ""
echo "Done! Combined CSV files have been created with _combined.csv suffix."
echo "These files include all columns from both results and logs CSVs, indexed by timestamp."
echo "You can now open the combined CSV files in Excel or other spreadsheet applications."
