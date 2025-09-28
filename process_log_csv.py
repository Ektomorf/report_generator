#!/usr/bin/env python3
"""
Process log CSV files and flatten JSON data in the message column.
Creates new CSV files with JSON keys as individual columns.
"""

import csv
import json
import os
import glob
import argparse
from pathlib import Path
import logging

def safe_json_parse(json_string):
    """
    Safely parse JSON string, handling malformed JSON.

    Args:
        json_string: String that should contain JSON

    Returns:
        dict: Parsed JSON or empty dict if parsing fails
    """
    if not json_string or not isinstance(json_string, str):
        return {}

    # Clean up Python object representations first
    import re

    # Remove Python object references like <sdk.keysight_xsan_sdk.utils.commands.peak_detection.PeakDetectionCommandBuilder object at 0x729cef1a8af0>
    cleaned_string = re.sub(r"<[^>]*>", "null", json_string)

    # Remove module references like <module 'time' (built-in)>
    cleaned_string = re.sub(r"<module '[^']*' \([^)]*\)>", "null", cleaned_string)

    try:
        # First try parsing as-is (in case it's already valid JSON)
        return json.loads(cleaned_string)
    except (json.JSONDecodeError, ValueError):
        pass

    try:
        # Handle Python dict string representation
        if cleaned_string.startswith("{'") or cleaned_string.startswith("{\""):
            # Use ast.literal_eval for safe evaluation of Python literals
            import ast
            return ast.literal_eval(cleaned_string)
    except (ValueError, SyntaxError):
        pass

    try:
        # Try converting single quotes to double quotes and parse
        if "'" in cleaned_string:
            # More sophisticated quote replacement
            # Replace single quotes with double quotes, but be careful about apostrophes
            fixed_string = re.sub(r"'([^']*)':", r'"\1":', cleaned_string)  # Keys
            fixed_string = re.sub(r": '([^']*)'", r': "\1"', fixed_string)  # Values
            fixed_string = fixed_string.replace("{'", '{"').replace("'}", '"}')
            return json.loads(fixed_string)
    except (json.JSONDecodeError, ValueError):
        pass

    # Final attempt: try to extract key-value pairs manually from the string
    try:
        # Extract basic key-value pairs using regex
        basic_data = {}
        # Find simple key-value patterns like 'key': 'value' or 'key': number
        simple_patterns = re.findall(r"'([^']+)':\s*'([^']*)'", cleaned_string)
        for key, value in simple_patterns:
            basic_data[key] = value

        # Find numeric patterns like 'key': 123.45
        numeric_patterns = re.findall(r"'([^']+)':\s*([+-]?\d*\.?\d+)", cleaned_string)
        for key, value in numeric_patterns:
            try:
                # Try to convert to appropriate numeric type
                if '.' in value:
                    basic_data[key] = float(value)
                else:
                    basic_data[key] = int(value)
            except ValueError:
                basic_data[key] = value

        if basic_data:
            return basic_data

    except Exception:
        pass

    # If all parsing attempts fail, log and return empty dict
    logging.warning(f"Failed to parse JSON after all attempts: {cleaned_string[:200]}...")
    return {}

def process_log_csv(input_file_path, output_file_path=None):
    """
    Process a log CSV file and flatten JSON in the message column.

    Args:
        input_file_path: Path to input CSV file
        output_file_path: Path to output CSV file (optional)
    """
    if output_file_path is None:
        # Create output filename with _logs.csv suffix
        base_name = os.path.splitext(input_file_path)[0]
        output_file_path = f"{base_name}_logs.csv"

    logging.info(f"Processing {input_file_path} -> {output_file_path}")

    try:
        # Read the input CSV
        rows = []
        fieldnames = set()

        with open(input_file_path, 'r', encoding='utf-8', newline='') as infile:
            reader = csv.DictReader(infile)
            original_fieldnames = reader.fieldnames or []

            for row in reader:
                new_row = {}

                # Copy all original columns except message
                for field in original_fieldnames:
                    if field != 'message':
                        new_row[field] = row.get(field, '')
                        fieldnames.add(field)

                # Parse JSON from message column
                message = row.get('message', '')
                if message:
                    parsed_json = safe_json_parse(message)

                    # Add parsed JSON fields to the row
                    for key, value in parsed_json.items():
                        # Handle nested dictionaries by flattening them
                        if isinstance(value, dict):
                            for nested_key, nested_value in value.items():
                                flat_key = f"{key}_{nested_key}"
                                new_row[flat_key] = str(nested_value)
                                fieldnames.add(flat_key)
                        elif isinstance(value, list):
                            # Convert lists to comma-separated strings
                            new_row[key] = ','.join(str(item) for item in value)
                            fieldnames.add(key)
                        else:
                            new_row[key] = str(value)
                            fieldnames.add(key)

                    # If no fields were parsed but message exists, mark as parse_failed
                    if not parsed_json and message.strip():
                        new_row['parse_failed'] = 'true'
                        new_row['parse_failed_reason'] = 'JSON parsing failed'
                        fieldnames.add('parse_failed')
                        fieldnames.add('parse_failed_reason')

                # Keep original message for reference
                new_row['original_message'] = message
                fieldnames.add('original_message')

                rows.append(new_row)

        # Sort fieldnames for consistent output
        fieldnames = sorted(list(fieldnames))

        # Write the output CSV
        with open(output_file_path, 'w', encoding='utf-8', newline='') as outfile:
            writer = csv.DictWriter(outfile, fieldnames=fieldnames)
            writer.writeheader()

            for row in rows:
                # Fill missing fields with empty values
                complete_row = {field: row.get(field, '') for field in fieldnames}
                writer.writerow(complete_row)

        print(f"Successfully processed {input_file_path} -> {output_file_path}")
        print(f"  Original columns: {len(original_fieldnames)}, New columns: {len(fieldnames)}")

    except Exception as e:
        logging.error(f"Error processing {input_file_path}: {e}")

def process_directory(directory_path, pattern="**/*.log"):
    """
    Process all log files in a directory.

    Args:
        directory_path: Path to directory containing log files
        pattern: Glob pattern to match log files
    """
    log_files = glob.glob(os.path.join(directory_path, pattern), recursive=True)

    if not log_files:
        print(f"No log files found matching pattern: {pattern}")
        return

    print(f"Found {len(log_files)} log files to process...")

    for log_file in log_files:
        process_log_csv(log_file)

    print("Done! Processed CSV files have been created with _logs.csv suffix.")

def main():
    parser = argparse.ArgumentParser(description='Process log CSV files and flatten JSON in message column')
    parser.add_argument('input', help='Input log file or directory path')
    parser.add_argument('-o', '--output', help='Output CSV file path (for single file mode)')
    parser.add_argument('-p', '--pattern', default='**/*.log',
                       help='Glob pattern for log files (default: **/*.log)')
    parser.add_argument('-v', '--verbose', action='store_true',
                       help='Enable verbose logging')

    args = parser.parse_args()

    # Set up logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=log_level, format='%(levelname)s: %(message)s')

    input_path = Path(args.input)

    if input_path.is_file():
        # Process single file
        process_log_csv(str(input_path), args.output)
    elif input_path.is_dir():
        # Process directory
        process_directory(str(input_path), args.pattern)
    else:
        print(f"Error: {input_path} is not a valid file or directory")
        return 1

    return 0

if __name__ == "__main__":
    exit(main())