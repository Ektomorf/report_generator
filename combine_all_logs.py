#!/usr/bin/env python3
"""
Combine all _logs.csv files from test campaigns into sequential log files.
This creates:
1. A master log file combining ALL logs from ALL campaigns (excludes journalctl_logs.csv)
2. Individual combined log files for each test campaign (excludes journalctl_logs.csv)

Note: journalctl_logs.csv files are excluded from the combination to keep only test logs.
"""

import csv
import os
import glob
import argparse
from pathlib import Path
import logging


def combine_logs_for_campaign(campaign_dir, output_path):
    """
    Combine all _logs.csv files in a test campaign directory into a single file.
    Excludes journalctl_logs.csv files from the combination.

    Args:
        campaign_dir: Path to test campaign directory
        output_path: Path to output directory (for relative path calculation)

    Returns:
        tuple: (output_file_path, all_rows, all_fieldnames) or (None, [], set()) if failed
    """
    campaign_path = Path(campaign_dir)
    campaign_name = campaign_path.name

    # Find all _logs.csv files in this campaign (excluding journalctl logs)
    all_log_files = glob.glob(os.path.join(campaign_dir, "**/*_logs.csv"), recursive=True)

    # Filter out journalctl_logs.csv files
    log_files = [f for f in all_log_files if not f.endswith('journalctl_logs.csv')]

    if not log_files:
        logging.info(f"No _logs.csv files found in {campaign_name} (excluding journalctl)")
        return None, [], set()

    logging.info(f"Found {len(log_files)} log CSV files in {campaign_name} (excluding journalctl)")

    # Output file path
    output_file = os.path.join(campaign_dir, f"{campaign_name}_all_logs_combined.csv")

    # Skip if output already exists
    if os.path.exists(output_file):
        logging.info(f"Skipping {campaign_name} - combined log already exists: {output_file}")
        # Still need to read the data for the master log
        # Return the path but we'll re-read it later if needed
        return output_file, [], set()

    all_rows = []
    all_fieldnames = set()

    # Read all log CSV files
    for log_file in log_files:
        try:
            # Get relative path for source tracking
            rel_path = os.path.relpath(log_file, campaign_dir)
            test_name = os.path.dirname(rel_path)

            logging.debug(f"  Reading {rel_path}")

            with open(log_file, 'r', encoding='utf-8', newline='') as f:
                reader = csv.DictReader(f)

                if not reader.fieldnames:
                    logging.warning(f"  No fieldnames in {rel_path}, skipping")
                    continue

                # Track all fieldnames
                all_fieldnames.update(reader.fieldnames)
                all_fieldnames.add('test_name')  # Add test_name column
                all_fieldnames.add('campaign_name')  # Add campaign_name column

                for row in reader:
                    # Add test name and campaign name to each row
                    row['test_name'] = test_name
                    row['campaign_name'] = campaign_name
                    all_rows.append(row)

        except Exception as e:
            logging.error(f"  Error reading {log_file}: {e}")
            continue

    if not all_rows:
        logging.warning(f"No log data found in {campaign_name}")
        return None, [], set()

    # Sort by timestamp (handle missing/invalid timestamps)
    def get_timestamp(row):
        try:
            ts = row.get('timestamp', '')
            if ts:
                return int(float(ts))
            return 0
        except (ValueError, TypeError):
            return 0

    all_rows.sort(key=get_timestamp)

    # Ensure consistent field order: timestamp first, then campaign/test names, then alphabetically
    fieldnames = ['timestamp']
    if 'Timestamp_original' in all_fieldnames:
        fieldnames.append('Timestamp_original')
    fieldnames.append('campaign_name')
    fieldnames.append('test_name')

    # Add remaining fields alphabetically
    remaining_fields = sorted([f for f in all_fieldnames
                              if f not in ['timestamp', 'Timestamp_original', 'campaign_name', 'test_name']])
    fieldnames.extend(remaining_fields)

    # Write combined CSV
    try:
        with open(output_file, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for row in all_rows:
                # Fill missing fields with empty values
                complete_row = {field: row.get(field, '') for field in fieldnames}
                writer.writerow(complete_row)

        print(f"✓ Created campaign log: {output_file}")
        print(f"  Total log entries: {len(all_rows)}")
        print(f"  Source files: {len(log_files)}")
        print(f"  Columns: {len(fieldnames)}")

        return output_file, all_rows, all_fieldnames

    except Exception as e:
        logging.error(f"Error writing combined log for {campaign_name}: {e}")
        return None, [], set()


def process_output_directory(output_dir):
    """
    Process all test campaign directories in the output folder.
    Creates both per-campaign combined logs and a master log across all campaigns.

    Args:
        output_dir: Path to output directory containing test campaigns
    """
    output_path = Path(output_dir)

    if not output_path.exists():
        print(f"Error: Output directory does not exist: {output_dir}")
        return 1

    # Find all test campaign directories (they contain test subdirectories)
    # Look for directories that contain _logs.csv files (excluding journalctl)
    campaign_dirs = set()

    all_logs_csv = glob.glob(os.path.join(output_dir, "**/*_logs.csv"), recursive=True)
    # Filter out journalctl_logs.csv files
    filtered_logs_csv = [f for f in all_logs_csv if not f.endswith('journalctl_logs.csv')]

    for logs_csv in filtered_logs_csv:
        # Campaign dir is typically 2 levels up from the _logs.csv file
        # e.g., output/campaign_name/test_name/test_logs.csv
        logs_path = Path(logs_csv)

        # Find the campaign directory (immediate child of output_dir)
        for parent in logs_path.parents:
            if parent.parent == output_path:
                campaign_dirs.add(str(parent))
                break

    if not campaign_dirs:
        print(f"No test campaigns with _logs.csv files found in {output_dir} (excluding journalctl)")
        return 0

    campaign_dirs = sorted(list(campaign_dirs))
    print(f"Found {len(campaign_dirs)} test campaign(s) to process...")
    print()

    # Process each campaign and collect all rows for master log
    master_rows = []
    master_fieldnames = set()
    success_count = 0

    for campaign_dir in campaign_dirs:
        output_file, rows, fieldnames = combine_logs_for_campaign(campaign_dir, output_path)
        if output_file:
            success_count += 1
            # Add rows to master collection
            master_rows.extend(rows)
            master_fieldnames.update(fieldnames)
        print()

    print(f"Successfully combined logs for {success_count}/{len(campaign_dirs)} campaign(s)")
    print()

    # Create master log file combining ALL campaigns
    if master_rows:
        print("=" * 72)
        print("Creating master log file combining ALL campaigns...")
        print("=" * 72)

        master_output_file = os.path.join(output_dir, "ALL_CAMPAIGNS_master_log.csv")

        # Sort all rows by timestamp
        def get_timestamp(row):
            try:
                ts = row.get('timestamp', '')
                if ts:
                    return int(float(ts))
                return 0
            except (ValueError, TypeError):
                return 0

        master_rows.sort(key=get_timestamp)

        # Ensure consistent field order
        fieldnames = ['timestamp']
        if 'Timestamp_original' in master_fieldnames:
            fieldnames.append('Timestamp_original')
        fieldnames.append('campaign_name')
        fieldnames.append('test_name')

        remaining_fields = sorted([f for f in master_fieldnames
                                  if f not in ['timestamp', 'Timestamp_original', 'campaign_name', 'test_name']])
        fieldnames.extend(remaining_fields)

        # Write master log
        try:
            with open(master_output_file, 'w', encoding='utf-8', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()

                for row in master_rows:
                    complete_row = {field: row.get(field, '') for field in fieldnames}
                    writer.writerow(complete_row)

            print(f"✓ Created MASTER log: {master_output_file}")
            print(f"  Total campaigns: {len(campaign_dirs)}")
            print(f"  Total log entries: {len(master_rows)}")
            print(f"  Columns: {len(fieldnames)}")
            print()

        except Exception as e:
            logging.error(f"Error writing master log file: {e}")
            return 1
    else:
        print("No log data collected for master log file")
        print()

    return 0


def main():
    parser = argparse.ArgumentParser(
        description='Combine all _logs.csv files from test campaigns into sequential master logs. '
                   'Excludes journalctl_logs.csv files to keep only test logs.'
    )
    parser.add_argument('output_dir',
                       help='Output directory containing test campaign folders')
    parser.add_argument('-v', '--verbose', action='store_true',
                       help='Enable verbose logging')

    args = parser.parse_args()

    # Set up logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=log_level, format='%(levelname)s: %(message)s')

    return process_output_directory(args.output_dir)


if __name__ == "__main__":
    exit(main())
