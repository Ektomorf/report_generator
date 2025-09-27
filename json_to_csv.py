#!/usr/bin/env python3
"""
Convert JSON results files to CSV format with flattened nested objects.
Similar to process_all_logs.bat but for CSV export.
"""

import json
import csv
import os
import glob
import argparse
from pathlib import Path
import pandas as pd
from collections import defaultdict
import logging

def flatten_dict(d, parent_key='', sep='_'):
    """
    Flatten a nested dictionary.

    Args:
        d: Dictionary to flatten
        parent_key: Parent key prefix
        sep: Separator for nested keys

    Returns:
        Flattened dictionary
    """
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        elif isinstance(v, list):
            # Check if all items in list are simple types (not dicts)
            if v and all(not isinstance(item, dict) for item in v):
                # Convert list to comma-separated string
                list_str = ','.join(str(item) for item in v)
                items.append((new_key, list_str))
            else:
                # Handle lists with dict items by creating indexed entries
                for i, item in enumerate(v):
                    if isinstance(item, dict):
                        items.extend(flatten_dict(item, f"{new_key}_{i}", sep=sep).items())
                    else:
                        items.append((f"{new_key}_{i}", item))
        else:
            items.append((new_key, v))
    return dict(items)

def process_json_file(json_file_path):
    """
    Process a single JSON file and return flattened data.

    Args:
        json_file_path: Path to JSON file

    Returns:
        List of flattened dictionaries
    """
    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Handle both single objects and arrays
        if isinstance(data, list):
            flattened_data = [flatten_dict(item) for item in data]
        else:
            flattened_data = [flatten_dict(data)]

        return flattened_data

    except Exception as e:
        logging.error(f"Error processing {json_file_path}: {e}")
        return []

def json_to_csv(json_file_path, csv_file_path=None):
    """
    Convert a JSON file to CSV format.

    Args:
        json_file_path: Path to input JSON file
        csv_file_path: Path to output CSV file (optional)
    """
    if csv_file_path is None:
        csv_file_path = json_file_path.replace('.json', '.csv')

    flattened_data = process_json_file(json_file_path)

    if not flattened_data:
        logging.warning(f"No data to process in {json_file_path}")
        return

    # Get all unique keys across all records
    all_keys = set()
    for record in flattened_data:
        all_keys.update(record.keys())

    all_keys = sorted(list(all_keys))

    # Write CSV file
    try:
        with open(csv_file_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=all_keys)
            writer.writeheader()

            for record in flattened_data:
                # Fill missing keys with empty values
                complete_record = {key: record.get(key, '') for key in all_keys}
                writer.writerow(complete_record)

        print(f"Successfully converted {json_file_path} to {csv_file_path}")

    except Exception as e:
        logging.error(f"Error writing CSV file {csv_file_path}: {e}")

def process_directory(directory_path, pattern="**/*_results.json"):
    """
    Process all JSON result files in a directory.

    Args:
        directory_path: Path to directory containing JSON files
        pattern: Glob pattern to match JSON files
    """
    json_files = glob.glob(os.path.join(directory_path, pattern), recursive=True)

    if not json_files:
        print(f"No JSON files found matching pattern: {pattern}")
        return

    print(f"Found {len(json_files)} JSON files to process...")

    for json_file in json_files:
        json_to_csv(json_file)

    print("Done! CSV files have been created alongside the JSON files.")

def main():
    parser = argparse.ArgumentParser(description='Convert JSON results to CSV format')
    parser.add_argument('input', help='Input JSON file or directory path')
    parser.add_argument('-o', '--output', help='Output CSV file path (for single file mode)')
    parser.add_argument('-p', '--pattern', default='**/*_results.json',
                       help='Glob pattern for JSON files (default: **/*_results.json)')
    parser.add_argument('-v', '--verbose', action='store_true',
                       help='Enable verbose logging')

    args = parser.parse_args()

    # Set up logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=log_level, format='%(levelname)s: %(message)s')

    input_path = Path(args.input)

    if input_path.is_file():
        # Process single file
        json_to_csv(str(input_path), args.output)
    elif input_path.is_dir():
        # Process directory
        process_directory(str(input_path), args.pattern)
    else:
        print(f"Error: {input_path} is not a valid file or directory")
        return 1

    return 0

if __name__ == "__main__":
    exit(main())