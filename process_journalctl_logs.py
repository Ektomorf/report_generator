#!/usr/bin/env python3
"""
Journal Log to CSV Converter

This script converts journalctl.log files into CSV format.
It parses the standard journalctl format:
  Timestamp Hostname Program[PID]: Message
  
Example input:
  Sep 26 18:08:02 digichan-devel mcu-comms[297]: SOCAN ->  x01,x00,x00,x00,x00,x00,x0a,x0a,x0a,x0a,x0a,x0a,x0a,x08,x80
  
Example output CSV:
  timestamp,hostname,program,pid,message
  "Sep 26 18:08:02","digichan-devel","mcu-comms","297","SOCAN ->  x01,x00,x00,x00,x00,x00,x0a,x0a,x0a,x0a,x0a,x0a,x0a,x08,x80"
"""

import re
import csv
import argparse
import sys
from pathlib import Path
import logging
from datetime import datetime, timezone
import time

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def convert_journalctl_timestamp_to_unix_ms(timestamp_str, year=None):
    """
    Convert journalctl timestamp to Unix milliseconds (UTC).
    
    Args:
        timestamp_str (str): Timestamp in format "Sep 26 18:08:02"
        year (int): Year to use (if None, infer from current year)
        
    Returns:
        int: Unix timestamp in milliseconds (UTC), or 0 if conversion fails
    """
    try:
        if year is None:
            year = datetime.now().year

        # Format: "Sep 26 18:08:02" -> "2025 Sep 26 18:08:02"
        full_timestamp_str = f"{year} {timestamp_str}"

        # Parse as naive datetime, then set as UTC
        dt = datetime.strptime(full_timestamp_str, "%Y %b %d %H:%M:%S")
        dt_utc = dt.replace(tzinfo=timezone.utc)

        unix_timestamp_ms = int(dt_utc.timestamp() * 1000)
        return unix_timestamp_ms

    except Exception as e:
        logger.warning(f"Failed to convert timestamp '{timestamp_str}': {str(e)}")
        return 0

def infer_year_from_log_context(input_file):
    """
    Try to infer the year from the log file context.
    
    This function looks for clues in the log file such as:
    - File modification time
    - Any explicit year references in log messages
    - Fall back to current year
    
    Args:
        input_file (Path): Path to the log file
        
    Returns:
        int: Inferred year
    """
    try:
        # First, try to use file modification time as a hint
        file_mtime = input_file.stat().st_mtime
        file_year = datetime.fromtimestamp(file_mtime).year
        
        # If the file is very recent (modified this year), use current year
        current_year = datetime.now().year
        if file_year == current_year or file_year == current_year - 1:
            return file_year
            
        # Look for year references in the first few hundred lines
        try:
            with open(input_file, 'r', encoding='utf-8', errors='ignore') as f:
                for line_num, line in enumerate(f):
                    if line_num > 500:  # Don't read too much
                        break
                    
                    # Look for 4-digit years in log messages
                    year_matches = re.findall(r'\b(20\d{2})\b', line)
                    if year_matches:
                        # Use the most recent reasonable year found
                        for year_str in year_matches:
                            year = int(year_str)
                            if 2020 <= year <= current_year + 1:
                                logger.info(f"Inferred year {year} from log content")
                                return year
        except:
            pass
        
        # Fall back to file modification year or current year
        logger.info(f"Using file modification year: {file_year}")
        return file_year
        
    except Exception as e:
        logger.warning(f"Could not infer year from file context: {str(e)}, using current year")
        return datetime.now().year

def parse_journalctl_line(line, year=None):
    """
    Parse a journalctl log line into components.
    
    Expected format:
    Timestamp Hostname Program[PID]: Message
    or
    Timestamp Hostname Program: Message
    or 
    Timestamp Hostname kernel: Message
    
    Args:
        line (str): The log line to parse
        year (int): Year to use for timestamp conversion
        
    Returns:
        dict: Dictionary with parsed components or None if parsing fails
    """
    # Remove any leading/trailing whitespace
    line = line.strip()
    
    if not line:
        return None
    
    # Regular expression to match journalctl format
    # Pattern explanation:
    # ^(\w+\s+\d+\s+\d+:\d+:\d+) - timestamp (e.g., "Sep 26 18:08:02")
    # \s+                         - one or more spaces
    # ([^\s]+)                    - hostname (non-space characters)
    # \s+                         - one or more spaces
    # ([^:\[\s]+)                 - program name (characters before : or [)
    # (?:\[(\d+)\])?             - optional PID in brackets
    # :\s*                        - colon followed by optional spaces
    # (.*)                        - message (rest of the line)
    
    pattern = r'^(\w+\s+\d+\s+\d+:\d+:\d+)\s+([^\s]+)\s+([^:\[\s]+)(?:\[(\d+)\])?:\s*(.*)'
    
    match = re.match(pattern, line)
    
    if match:
        timestamp_str = match.group(1)
        hostname = match.group(2)
        program = match.group(3)
        pid = match.group(4) if match.group(4) else ""
        message = match.group(5)
        
        # Convert timestamp to Unix milliseconds
        unix_timestamp_ms = convert_journalctl_timestamp_to_unix_ms(timestamp_str, year)
        
        return {
            'timestamp': unix_timestamp_ms,
            'hostname': hostname,
            'program': program,
            'pid': pid,
            'message': message
        }
    else:
        logger.warning(f"Could not parse line: {line[:100]}...")
        return None

def convert_journalctl_to_csv(input_file, output_file, start_time_ms=None, end_time_ms=None):
    """
    Convert a journalctl.log file to CSV format.

    Args:
        input_file (Path): Path to the input journalctl.log file
        output_file (Path): Path to the output CSV file
        start_time_ms (int): Optional start time in Unix milliseconds (inclusive)
        end_time_ms (int): Optional end time in Unix milliseconds (inclusive)

    Returns:
        tuple: (success_count, error_count, total_lines, filtered_count)
    """
    success_count = 0
    error_count = 0
    total_lines = 0
    filtered_count = 0

    # Infer the year for timestamp conversion
    inferred_year = infer_year_from_log_context(input_file)
    logger.info(f"Using year {inferred_year} for timestamp conversion")

    if start_time_ms or end_time_ms:
        time_range_str = f"Filtering to time range: "
        if start_time_ms:
            time_range_str += f"from {datetime.fromtimestamp(start_time_ms/1000).strftime('%Y-%m-%d %H:%M:%S')}"
        if end_time_ms:
            if start_time_ms:
                time_range_str += f" to {datetime.fromtimestamp(end_time_ms/1000).strftime('%Y-%m-%d %H:%M:%S')}"
            else:
                time_range_str += f"until {datetime.fromtimestamp(end_time_ms/1000).strftime('%Y-%m-%d %H:%M:%S')}"
        logger.info(time_range_str)
    
    try:
        with open(input_file, 'r', encoding='utf-8', errors='ignore') as infile, \
             open(output_file, 'w', newline='', encoding='utf-8') as outfile:
            
            # Create CSV writer with proper quoting
            writer = csv.writer(outfile, quoting=csv.QUOTE_ALL)
            
            # Write header
            writer.writerow(['timestamp', 'hostname', 'program', 'pid', 'message'])
            
            for line_num, line in enumerate(infile, 1):
                total_lines += 1

                parsed = parse_journalctl_line(line, inferred_year)

                if parsed:
                    # Apply time range filter if specified
                    timestamp = parsed['timestamp']

                    # Skip if before start_time
                    if start_time_ms is not None and timestamp < start_time_ms:
                        filtered_count += 1
                        continue

                    # Skip if after end_time
                    if end_time_ms is not None and timestamp > end_time_ms:
                        filtered_count += 1
                        continue

                    writer.writerow([
                        parsed['timestamp'],
                        parsed['hostname'],
                        parsed['program'],
                        parsed['pid'],
                        parsed['message']
                    ])
                    success_count += 1
                else:
                    error_count += 1
                    if error_count <= 5:  # Show first 5 parsing errors
                        logger.warning(f"Line {line_num}: Failed to parse: {line.strip()[:100]}...")

                # Progress indicator for large files
                if total_lines % 10000 == 0:
                    logger.info(f"Processed {total_lines} lines...")
                    
    except Exception as e:
        logger.error(f"Error processing file {input_file}: {str(e)}")
        return 0, 0, 0, 0

    return success_count, error_count, total_lines, filtered_count

def find_campaign_timespan(campaign_dir):
    """
    Find the earliest and latest timestamps from test log files in a campaign directory.

    Args:
        campaign_dir (Path): Path to the campaign directory

    Returns:
        tuple: (min_timestamp_ms, max_timestamp_ms) or (None, None) if no timestamps found
    """
    min_timestamp = None
    max_timestamp = None

    # Pattern to match timestamps in log files: "2025-09-29 16:48:29,238"
    timestamp_pattern = re.compile(r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3})')

    # Find all .log files in the campaign directory (not journalctl.log)
    log_files = [f for f in campaign_dir.rglob('*.log') if f.name != 'journalctl.log']

    for log_file in log_files:
        try:
            with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                # Check first line for start timestamp
                first_line = f.readline()
                match = timestamp_pattern.match(first_line.strip())
                if match:
                    timestamp_str = match.group(1)
                    # Convert to Unix ms
                    try:
                        dt = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S,%f')
                        timestamp_ms = int(dt.timestamp() * 1000)

                        if min_timestamp is None or timestamp_ms < min_timestamp:
                            min_timestamp = timestamp_ms
                    except:
                        pass

                # Check last non-empty line for end timestamp
                # Read file backwards to find last timestamp
                f.seek(0, 2)  # Go to end
                file_size = f.tell()
                if file_size > 0:
                    # Read last few KB to find last timestamp
                    read_size = min(8192, file_size)
                    f.seek(max(0, file_size - read_size))
                    lines = f.readlines()

                    # Find last line with timestamp
                    for line in reversed(lines):
                        match = timestamp_pattern.match(line.strip())
                        if match:
                            timestamp_str = match.group(1)
                            try:
                                dt = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S,%f')
                                timestamp_ms = int(dt.timestamp() * 1000)

                                if max_timestamp is None or timestamp_ms > max_timestamp:
                                    max_timestamp = timestamp_ms
                                break
                            except:
                                pass
        except Exception as e:
            logger.debug(f"Error reading {log_file}: {str(e)}")
            continue

    return min_timestamp, max_timestamp

def find_journalctl_logs(directory):
    """
    Find all journalctl.log files in the given directory and subdirectories.

    Args:
        directory (Path): Directory to search

    Returns:
        list: List of Path objects for found journalctl.log files
    """
    log_files = []

    for file_path in directory.rglob('journalctl.log'):
        log_files.append(file_path)

    return log_files

def main():
    parser = argparse.ArgumentParser(
        description='Convert journalctl.log files to CSV format',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Convert a single file
  python process_journalctl_logs.py /path/to/journalctl.log
  
  # Process all journalctl.log files in a directory
  python process_journalctl_logs.py /path/to/output/dir --batch
  
  # Specify custom output file
  python process_journalctl_logs.py /path/to/journalctl.log --output /path/to/output.csv
        """
    )
    
    parser.add_argument('input', 
                       help='Input journalctl.log file or directory containing log files')
    parser.add_argument('--output', '-o', 
                       help='Output CSV file path (default: same name with .csv extension)')
    parser.add_argument('--batch', '-b', action='store_true',
                       help='Process all journalctl.log files found in the input directory')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose output')
    
    args = parser.parse_args()
    
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    
    input_path = Path(args.input)
    
    if not input_path.exists():
        logger.error(f"Input path does not exist: {input_path}")
        return 1
    
    files_to_process = []
    
    if args.batch or input_path.is_dir():
        # Process all journalctl.log files in directory
        if not input_path.is_dir():
            logger.error(f"--batch specified but input is not a directory: {input_path}")
            return 1
            
        files_to_process = find_journalctl_logs(input_path)
        if not files_to_process:
            logger.warning(f"No journalctl.log files found in {input_path}")
            return 0
            
        logger.info(f"Found {len(files_to_process)} journalctl.log files to process")
        
    else:
        # Process single file
        if not input_path.is_file():
            logger.error(f"Input file does not exist: {input_path}")
            return 1
        files_to_process = [input_path]
    
    total_success = 0
    total_errors = 0
    total_processed = 0
    total_filtered = 0

    for log_file in files_to_process:
        logger.info(f"Processing: {log_file}")

        # Determine output file path
        if args.output and len(files_to_process) == 1:
            output_file = Path(args.output)
        else:
            # Create CSV file in the same directory as the log file
            # For journalctl.log, create journalctl_logs.csv instead of journalctl_journalctl.csv
            if log_file.stem == "journalctl":
                output_file = log_file.parent / "journalctl_logs.csv"
            else:
                output_file = log_file.parent / f"{log_file.stem}_journalctl.csv"

        # Find campaign timespan for filtering (when processing in batch mode)
        start_time_ms = None
        end_time_ms = None

        if args.batch:
            # The journalctl.log file is in the campaign directory
            campaign_dir = log_file.parent
            logger.info(f"Finding campaign timespan for: {campaign_dir.name}")
            start_time_ms, end_time_ms = find_campaign_timespan(campaign_dir)

            if start_time_ms and end_time_ms:
                logger.info(f"Campaign timespan: {datetime.fromtimestamp(start_time_ms/1000).strftime('%Y-%m-%d %H:%M:%S')} to {datetime.fromtimestamp(end_time_ms/1000).strftime('%Y-%m-%d %H:%M:%S')}")
            else:
                logger.warning(f"Could not determine campaign timespan for {campaign_dir.name}, processing all logs")

        # Convert the file with time filtering
        success, errors, total, filtered = convert_journalctl_to_csv(log_file, output_file, start_time_ms, end_time_ms)

        if total > 0:
            logger.info(f"✓ Converted {log_file} -> {output_file}")
            logger.info(f"  Successfully parsed: {success}/{total} lines ({success/total*100:.1f}%)")
            if filtered > 0:
                logger.info(f"  Filtered out (outside campaign timespan): {filtered} lines ({filtered/total*100:.1f}%)")
            if errors > 0:
                logger.warning(f"  Parsing errors: {errors} lines ({errors/total*100:.1f}%)")
        else:
            logger.error(f"✗ Failed to process {log_file}")

        total_success += success
        total_errors += errors
        total_processed += total
        total_filtered += filtered
    
    # Summary
    logger.info("=" * 60)
    logger.info("PROCESSING COMPLETE")
    logger.info(f"Files processed: {len(files_to_process)}")
    logger.info(f"Total lines: {total_processed}")
    if total_processed > 0:
        logger.info(f"Successfully parsed: {total_success} ({total_success/total_processed*100:.1f}%)")
        if total_filtered > 0:
            logger.info(f"Filtered (outside timespan): {total_filtered} ({total_filtered/total_processed*100:.1f}%)")
        if total_errors > 0:
            logger.warning(f"Parsing errors: {total_errors} ({total_errors/total_processed*100:.1f}%)")
    else:
        logger.warning("No lines were processed successfully.")

    return 0

if __name__ == '__main__':
    sys.exit(main())