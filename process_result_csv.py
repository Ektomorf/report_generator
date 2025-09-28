#!/usr/bin/env python3
"""
Convert JSON results files to CSV format with flattened nested objects.
Used by convert_logs_to_csv.bat and convert_results_to_csv.bat for CSV export.
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
from datetime import datetime
import re

def convert_timestamp_to_unix_ms(value):
    """
    Convert timestamp string to unix milliseconds.
    
    Args:
        value: Timestamp string in various formats
        
    Returns:
        int: Unix timestamp in milliseconds, or original value if not a timestamp
    """
    if not isinstance(value, str):
        return value
    
    # Common timestamp patterns
    timestamp_patterns = [
        # 2025-09-26 15:08:15,575 (with comma for milliseconds)
        (r'^\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}:\d{2},\d{3}$', '%Y-%m-%d %H:%M:%S,%f'),
        # 2025-09-26 15:08:15.575 (with dot for milliseconds)
        (r'^\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}:\d{2}\.\d{3}$', '%Y-%m-%d %H:%M:%S.%f'),
        # 2025-09-26 15:08:15 (without milliseconds)
        (r'^\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}:\d{2}$', '%Y-%m-%d %H:%M:%S'),
        # ISO format: 2025-09-26T15:08:15.575Z
        (r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z?$', '%Y-%m-%dT%H:%M:%S.%f'),
        # ISO format without milliseconds: 2025-09-26T15:08:15Z
        (r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z?$', '%Y-%m-%dT%H:%M:%S'),
        # 2025-26-09 15:08:15,575 (day swapped with month)
        (r'^\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}:\d{2},\d{3}$', '%Y-%d-%m %H:%M:%S,%f'),
        # 2025-26-09 15:08:15 (day swapped with month)
        (r'^\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}:\d{2}$', '%Y-%d-%m %H:%M:%S'),
    ]
    
    for pattern, format_str in timestamp_patterns:
        if re.match(pattern, value.strip()):
            try:
                # Handle comma separator for milliseconds by replacing with dot
                normalized_value = value.strip().replace(',', '.')
                # Remove Z suffix if present
                if normalized_value.endswith('Z'):
                    normalized_value = normalized_value[:-1]
                
                dt = datetime.strptime(normalized_value, format_str.replace(',%f', '.%f'))
                # Convert to unix timestamp in milliseconds
                return int(dt.timestamp() * 1000)
            except (ValueError, OSError) as e:
                # If parsing fails, return original value
                continue
    
    return value

def is_timestamp_field(key):
    """
    Check if a field key indicates it contains timestamp data.
    
    Args:
        key: Field name/key
        
    Returns:
        bool: True if key indicates timestamp field
    """
    timestamp_keywords = [
        'timestamp', 'Timestamp'
    ]
    
    key_lower = key.lower()
    # Only match exact 'timestamp' or other keywords, but exclude send_timestamp and receive_timestamp
    if key_lower == 'timestamp':
        return True
    
    # Check other keywords but exclude send/receive specific timestamps
    for keyword in timestamp_keywords[1:]:  # Skip 'timestamp' since we handled it above
        if keyword in key_lower and 'send' not in key_lower and 'receive' not in key_lower:
            return True
    
    return False

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
                        indexed_key = f"{new_key}_{i}"
                        # Check if this is a timestamp field and convert if needed
                        if is_timestamp_field(indexed_key):
                            # Keep original timestamp with '_original' suffix
                            original_field = f"{indexed_key}_original"
                            items.append((original_field, item))
                            # Add converted timestamp in 'timestamp' column
                            converted_item = convert_timestamp_to_unix_ms(item)
                            if converted_item != item:  # Only add if conversion was successful
                                items.append(('timestamp', converted_item))
                        else:
                            items.append((indexed_key, item))
        else:
            # Check if this is a timestamp field and convert if needed
            if is_timestamp_field(new_key):
                # Keep original timestamp with '_original' suffix
                original_field = f"{new_key}_original"
                items.append((original_field, v))
                # Add converted timestamp in 'timestamp' column
                converted_value = convert_timestamp_to_unix_ms(v)
                if converted_value != v:  # Only add if conversion was successful
                    items.append(('timestamp', converted_value))
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

def json_to_csv(json_file_path, csv_file_path=None, suffix=''):
    """
    Convert a JSON file to CSV format.

    Args:
        json_file_path: Path to input JSON file
        csv_file_path: Path to output CSV file (optional)
        suffix: Optional suffix to add before .csv extension
    """
    if csv_file_path is None:
        if suffix:
            csv_file_path = json_file_path.replace('.json', f'{suffix}.csv')
        else:
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

def process_directory(directory_path, pattern="**/*_results.json", suffix=''):
    """
    Process all JSON result files in a directory.

    Args:
        directory_path: Path to directory containing JSON files
        pattern: Glob pattern to match JSON files
        suffix: Optional suffix to add before .csv extension
    """
    json_files = glob.glob(os.path.join(directory_path, pattern), recursive=True)

    if not json_files:
        print(f"No JSON files found matching pattern: {pattern}")
        return

    print(f"Found {len(json_files)} JSON files to process...")

    for json_file in json_files:
        json_to_csv(json_file, suffix=suffix)

    print("Done! CSV files have been created alongside the JSON files.")

def main():
    parser = argparse.ArgumentParser(description='Convert JSON results to CSV format')
    parser.add_argument('input', help='Input JSON file or directory path')
    parser.add_argument('-o', '--output', help='Output CSV file path (for single file mode)')
    parser.add_argument('-p', '--pattern', default='**/*_results.json',
                       help='Glob pattern for JSON files (default: **/*_results.json)')
    parser.add_argument('-s', '--suffix', default='',
                       help='Suffix to add before .csv extension (e.g., "_logs")')
    parser.add_argument('-v', '--verbose', action='store_true',
                       help='Enable verbose logging')

    args = parser.parse_args()

    # Set up logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=log_level, format='%(levelname)s: %(message)s')

    input_path = Path(args.input)

    if input_path.is_file():
        # Process single file
        json_to_csv(str(input_path), args.output, args.suffix)
    elif input_path.is_dir():
        # Process directory
        process_directory(str(input_path), args.pattern, args.suffix)
    else:
        print(f"Error: {input_path} is not a valid file or directory")
        return 1

    return 0

if __name__ == "__main__":
    exit(main())