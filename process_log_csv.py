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
from datetime import datetime

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

    # If all parsing attempts fail, treat as plain text message
    # Don't log warning - this is expected for plain text messages
    return None

def convert_timestamp_to_unix_ms(timestamp_str):
    """
    Convert timestamp string to Unix milliseconds.
    
    Args:
        timestamp_str: String containing timestamp in various formats
        
    Returns:
        int: Unix timestamp in milliseconds, or None if parsing fails
    """
    if not timestamp_str or not isinstance(timestamp_str, str):
        return None
    
    # List of common timestamp formats to try
    formats = [
        '%Y-%m-%d %H:%M:%S,%f',      # 2025-09-26 17:01:59,383 (with comma for milliseconds)
        '%Y-%m-%d %H:%M:%S.%f',      # 2023-09-28 10:30:45.123456
        '%Y-%m-%d %H:%M:%S',         # 2023-09-28 10:30:45
        '%Y-%m-%dT%H:%M:%S.%fZ',     # 2023-09-28T10:30:45.123456Z (ISO format)
        '%Y-%m-%dT%H:%M:%SZ',        # 2023-09-28T10:30:45Z (ISO format)
        '%Y-%m-%dT%H:%M:%S.%f',      # 2023-09-28T10:30:45.123456 (ISO without Z)
        '%Y-%m-%dT%H:%M:%S',         # 2023-09-28T10:30:45 (ISO without Z)
        '%m/%d/%Y %H:%M:%S',         # 09/28/2023 10:30:45
        '%d/%m/%Y %H:%M:%S',         # 28/09/2023 10:30:45
        '%Y%m%d_%H%M%S',             # 20230928_103045
        '%Y%m%d%H%M%S',              # 20230928103045
        '%Y-%d-%m %H:%M:%S,%f'       # 2025-26-09 15:08:15,575 (day-month swapped with comma)
    ]
    
    # Clean up the timestamp string
    timestamp_str = timestamp_str.strip()
    
    # Try parsing with each format
    for fmt in formats:
        try:
            # Handle comma separator for milliseconds by converting to format Python expects
            if ',%f' in fmt and ',' in timestamp_str:
                # Python's %f expects dot separator, but we have comma
                # Convert comma to dot for parsing
                test_str = timestamp_str.replace(',', '.')
                test_fmt = fmt.replace(',%f', '.%f')
                dt = datetime.strptime(test_str, test_fmt)
            else:
                dt = datetime.strptime(timestamp_str, fmt)
            # Convert to Unix timestamp in milliseconds
            return int(dt.timestamp() * 1000)
        except ValueError:
            continue
    
    # Try parsing as Unix timestamp (seconds or milliseconds)
    try:
        # Check if it's already a numeric timestamp
        timestamp_num = float(timestamp_str)
        
        # If it looks like seconds (reasonable range), convert to milliseconds
        if 1000000000 <= timestamp_num <= 9999999999:  # Years 2001-2286 in seconds
            return int(timestamp_num * 1000)
        # If it looks like milliseconds (reasonable range), return as-is
        elif 1000000000000 <= timestamp_num <= 9999999999999:  # Years 2001-2286 in milliseconds
            return int(timestamp_num)
    except (ValueError, OverflowError):
        pass
    
    # If all parsing attempts fail, log and return None
    logging.warning(f"Failed to parse timestamp: {timestamp_str}")
    return None

def parse_plain_text_log_line(line):
    """
    Parse a plain text log line in format: TIMESTAMP - UNIX_MS - LEVEL - JSON_DATA

    Args:
        line: Log line string

    Returns:
        dict: Parsed log entry with timestamp, level, and message
    """
    import re

    # Pattern to match: TIMESTAMP - UNIX_MS - LEVEL - MESSAGE
    # Example: 2025-09-30 11:48:54,787 - 1759229334787 - INFO - {'log_type': 'VersalCommand', ...}
    pattern = r'^(\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}:\d{2},\d{3})\s*-\s*(\d+)\s*-\s*(\w+)\s*-\s*(.+)$'

    match = re.match(pattern, line.strip())
    if match:
        timestamp_str, unix_ms, level, message = match.groups()
        return {
            'Timestamp_original': timestamp_str,
            'timestamp': int(unix_ms),  # Use Unix ms directly
            'level': level,
            'message': message.strip()
        }

    # If pattern doesn't match, return the line as a message
    return {
        'timestamp': '',
        'level': '',
        'message': line.strip()
    }

def is_plain_text_log_file(file_path):
    """
    Determine if a file is a plain text log file or CSV file.

    Args:
        file_path: Path to the file

    Returns:
        bool: True if it's a plain text log file, False if CSV
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            first_line = f.readline().strip()

            # Check if first line looks like a plain text log entry
            # Format: TIMESTAMP - UNIX_MS - LEVEL - MESSAGE
            import re
            log_pattern = r'^\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}:\d{2},\d{3}\s*-\s*\d+\s*-\s*\w+\s*-\s*.+'

            if re.match(log_pattern, first_line):
                return True

            # Check if it looks like CSV (has comma-separated headers)
            if ',' in first_line and not first_line.startswith('{'):
                return False

            # Default to plain text log if uncertain
            return True

    except Exception:
        return True

def process_log_csv(input_file_path, output_file_path=None):
    """
    Process a log file (either plain text or CSV) and flatten JSON data.

    Args:
        input_file_path: Path to input log file
        output_file_path: Path to output CSV file (optional)
    """
    if output_file_path is None:
        # Create output filename with _logs.csv suffix
        base_name = os.path.splitext(input_file_path)[0]
        output_file_path = f"{base_name}_logs.csv"

    # Skip if output file already exists
    if os.path.exists(output_file_path):
        logging.info(f"Skipping {input_file_path} - output already exists: {output_file_path}")
        return

    logging.info(f"Processing {input_file_path} -> {output_file_path}")

    try:
        # Determine if input is plain text log or CSV
        is_plain_text = is_plain_text_log_file(input_file_path)

        rows = []
        fieldnames = set()

        if is_plain_text:
            # Process plain text log file
            logging.debug(f"Processing as plain text log file")

            with open(input_file_path, 'r', encoding='utf-8') as infile:
                for line_num, line in enumerate(infile, 1):
                    if not line.strip():
                        continue

                    # Parse the plain text log line
                    parsed_line = parse_plain_text_log_line(line)

                    new_row = {}

                    # Add basic fields - timestamp is already in Unix ms from parse_plain_text_log_line
                    timestamp = parsed_line.get('timestamp', '')
                    timestamp_original = parsed_line.get('Timestamp_original', '')
                    level = parsed_line.get('level', '')
                    message = parsed_line.get('message', '')

                    # Add timestamp (already in Unix ms)
                    if timestamp:
                        new_row['timestamp'] = timestamp
                        fieldnames.add('timestamp')

                    # Add original timestamp string
                    if timestamp_original:
                        new_row['Timestamp_original'] = timestamp_original
                        fieldnames.add('Timestamp_original')

                    if level:
                        new_row['level'] = level
                        fieldnames.add('level')

                    # Parse JSON from message
                    if message:
                        parsed_json = safe_json_parse(message)

                        if parsed_json is not None:
                            for key, value in parsed_json.items():
                                # Handle nested dictionaries by flattening them
                                if isinstance(value, dict):
                                    for nested_key, nested_value in value.items():
                                        flat_key = f"{key}_{nested_key}"
                                        # Keep values as-is (timestamps already in Unix ms)
                                        new_row[flat_key] = nested_value
                                        fieldnames.add(flat_key)
                                elif isinstance(value, list):
                                    # Convert lists to comma-separated strings
                                    new_row[key] = ','.join(str(item) for item in value)
                                    fieldnames.add(key)
                                else:
                                    # Keep values as-is (timestamps already in Unix ms)
                                    new_row[key] = value
                                    fieldnames.add(key)
                        else:
                            # If JSON parsing failed, treat as plain text message
                            new_row['message'] = message
                            fieldnames.add('message')

                    rows.append(new_row)
        else:
            # Process CSV file (existing logic)
            logging.debug(f"Processing as CSV file")

            with open(input_file_path, 'r', encoding='utf-8', newline='') as infile:
                reader = csv.DictReader(infile)
                original_fieldnames = reader.fieldnames or []

                for row in reader:
                    new_row = {}

                    # Copy all original columns except message, raw_line, and source_file
                    for field in original_fieldnames:
                        if field not in ['message', 'raw_line', 'source_file']:
                            # Keep values as-is (timestamps already in Unix ms)
                            new_row[field] = row.get(field, '')
                            fieldnames.add(field)

                    # Parse JSON from message column
                    message = row.get('message', '')
                    if message:
                        parsed_json = safe_json_parse(message)

                        # If JSON was successfully parsed, add parsed fields to the row
                        if parsed_json is not None:
                            for key, value in parsed_json.items():
                                # Handle nested dictionaries by flattening them
                                if isinstance(value, dict):
                                    for nested_key, nested_value in value.items():
                                        flat_key = f"{key}_{nested_key}"
                                        # Keep values as-is (timestamps already in Unix ms)
                                        new_row[flat_key] = nested_value
                                        fieldnames.add(flat_key)
                                elif isinstance(value, list):
                                    # Convert lists to comma-separated strings
                                    new_row[key] = ','.join(str(item) for item in value)
                                    fieldnames.add(key)
                                else:
                                    # Keep values as-is (timestamps already in Unix ms)
                                    new_row[key] = value
                                    fieldnames.add(key)
                        else:
                            # If JSON parsing failed, treat as plain text message
                            new_row['message'] = message
                            fieldnames.add('message')

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
        if not is_plain_text:
            print(f"  Original columns: {len(original_fieldnames)}, New columns: {len(fieldnames)}")
        else:
            print(f"  New columns: {len(fieldnames)}")

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