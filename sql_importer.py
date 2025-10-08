#!/usr/bin/env python3
"""
SQL Test Results Importer

Scans test output directory and imports test results, logs, and metadata
into an SQLite database for efficient querying and archival.
"""

import os
import sys
import json
import csv
import hashlib
import sqlite3
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass


@dataclass
class ArtefactInfo:
    """Information about a discovered artefact file"""
    file_path: Path
    artefact_type: str
    file_hash: str
    campaign_name: str
    test_name: Optional[str] = None
    test_path: Optional[str] = None


class SQLImporter:
    """Import test results into SQL database"""

    def __init__(self, db_path: str = "test_results.db"):
        self.db_path = db_path
        self.conn: Optional[sqlite3.Connection] = None
        self.base_dir: Optional[Path] = None

    def connect(self):
        """Connect to database and create schema if needed"""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row

        # Enable foreign keys
        self.conn.execute("PRAGMA foreign_keys = ON")

        # Read and execute schema
        schema_path = Path(__file__).parent / "schema.sql"
        if schema_path.exists():
            with open(schema_path, 'r', encoding='utf-8') as f:
                schema_sql = f.read()
                self.conn.executescript(schema_sql)
        else:
            print(f"Warning: schema.sql not found at {schema_path}")

        self.conn.commit()

    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()

    def calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA256 hash of file"""
        sha256_hash = hashlib.sha256()

        try:
            with open(file_path, "rb") as f:
                # Read file in chunks to handle large files
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            return sha256_hash.hexdigest()
        except Exception as e:
            print(f"Error calculating hash for {file_path}: {e}")
            return ""

    def is_artefact_processed(self, file_hash: str) -> bool:
        """Check if artefact with this hash has been processed"""
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM artefacts WHERE file_hash = ? AND processed = 1",
            (file_hash,)
        )
        count = cursor.fetchone()[0]
        return count > 0

    def scan_artefacts(self, base_dir: Path) -> List[ArtefactInfo]:
        """Scan directory for test artefacts"""
        print(f"Scanning for artefacts in: {base_dir}")
        artefacts = []

        # Find all campaign directories (contain report.json or have test subdirs)
        for campaign_dir in base_dir.iterdir():
            if not campaign_dir.is_dir():
                continue

            campaign_name = campaign_dir.name

            # Look for test directories
            for test_dir in campaign_dir.iterdir():
                if not test_dir.is_dir() or not test_dir.name.startswith('test_'):
                    continue

                test_path = test_dir.name

                # Find test name from directory structure
                # Format: test_<module>__<test_name> or test_<test_name>
                test_name_match = re.search(r'__([^_].+)$', test_path)
                if test_name_match:
                    test_name = test_name_match.group(1)
                else:
                    test_name = test_path.replace('test_', '', 1)

                # Scan for artefact files in test directory
                for file_path in test_dir.iterdir():
                    if not file_path.is_file():
                        continue

                    file_name = file_path.name
                    artefact_type = None

                    # Determine artefact type
                    if file_name.endswith('_combined.csv'):
                        artefact_type = 'csv'
                    elif file_name.endswith('_analyzer.html'):
                        artefact_type = 'analyzer_html'
                    elif file_name.endswith('_params.json'):
                        artefact_type = 'json'
                    elif file_name.endswith('_status.json'):
                        artefact_type = 'json'
                    elif file_name.endswith('.png') or file_name.endswith('.jpg'):
                        artefact_type = 'screenshot'
                    elif file_name.endswith('.log'):
                        artefact_type = 'log'

                    if artefact_type:
                        file_hash = self.calculate_file_hash(file_path)
                        artefacts.append(ArtefactInfo(
                            file_path=file_path,
                            artefact_type=artefact_type,
                            file_hash=file_hash,
                            campaign_name=campaign_name,
                            test_name=test_name,
                            test_path=test_path
                        ))

        print(f"Found {len(artefacts)} artefacts")
        return artefacts

    def parse_campaign_date(self, campaign_name: str) -> Optional[datetime]:
        """Parse date from campaign name (format: name_DDMMYY_HHMMSS)"""
        date_match = re.search(r'(\d{6})_(\d{6})', campaign_name)
        if date_match:
            date_str = date_match.group(1)
            time_str = date_match.group(2)
            try:
                # Format: DDMMYY_HHMMSS
                day = int(date_str[0:2])
                month = int(date_str[2:4])
                year = 2000 + int(date_str[4:6])
                hour = int(time_str[0:2])
                minute = int(time_str[2:4])
                second = int(time_str[4:6])
                return datetime(year, month, day, hour, minute, second)
            except ValueError as e:
                print(f"Warning: Could not parse date from {campaign_name}: {e}")
        return None

    def get_or_create_campaign(self, campaign_name: str) -> int:
        """Get existing campaign or create new one, return campaign_id"""
        cursor = self.conn.cursor()

        # Check if campaign exists
        cursor.execute(
            "SELECT campaign_id FROM campaigns WHERE campaign_name = ?",
            (campaign_name,)
        )
        row = cursor.fetchone()

        if row:
            return row[0]

        # Create new campaign
        campaign_date = self.parse_campaign_date(campaign_name)
        cursor.execute(
            "INSERT INTO campaigns (campaign_name, campaign_date) VALUES (?, ?)",
            (campaign_name, campaign_date)
        )
        self.conn.commit()
        return cursor.lastrowid

    def get_or_create_test(
        self,
        campaign_id: int,
        test_name: str,
        test_path: str
    ) -> int:
        """Get existing test or create new one, return test_id"""
        cursor = self.conn.cursor()

        # Check if test exists
        cursor.execute(
            "SELECT test_id FROM tests WHERE campaign_id = ? AND test_name = ? AND test_path = ?",
            (campaign_id, test_name, test_path)
        )
        row = cursor.fetchone()

        if row:
            return row[0]

        # Create new test
        cursor.execute(
            "INSERT INTO tests (campaign_id, test_name, test_path, status) VALUES (?, ?, ?, ?)",
            (campaign_id, test_name, test_path, 'unknown')
        )
        self.conn.commit()
        return cursor.lastrowid

    def import_test_params(self, test_id: int, params_json_path: Path):
        """Import test parameters from params JSON file"""
        try:
            with open(params_json_path, 'r', encoding='utf-8') as f:
                params_data = json.load(f)

            if 'params' not in params_data:
                return

            cursor = self.conn.cursor()

            # Delete existing params for this test
            cursor.execute("DELETE FROM test_params WHERE test_id = ?", (test_id,))

            # Insert new params
            for param_name, param_value in params_data['params'].items():
                cursor.execute(
                    "INSERT INTO test_params (test_id, param_name, param_value) VALUES (?, ?, ?)",
                    (test_id, param_name, json.dumps(param_value) if isinstance(param_value, (dict, list)) else str(param_value))
                )

            self.conn.commit()

        except Exception as e:
            print(f"Error importing params from {params_json_path}: {e}")

    def import_test_status(self, test_id: int, status_json_path: Path):
        """Import test status from status JSON file"""
        try:
            with open(status_json_path, 'r', encoding='utf-8') as f:
                status_data = json.load(f)

            cursor = self.conn.cursor()

            # Update test with status information
            start_time = status_data.get('start_time')
            if start_time:
                try:
                    start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                    start_timestamp = int(start_dt.timestamp() * 1000)

                    cursor.execute(
                        "UPDATE tests SET start_time = ?, start_timestamp = ? WHERE test_id = ?",
                        (start_dt, start_timestamp, test_id)
                    )
                    self.conn.commit()
                except Exception as e:
                    print(f"Warning: Could not parse start_time: {e}")

        except Exception as e:
            print(f"Error importing status from {status_json_path}: {e}")

    def import_csv_data(self, test_id: int, csv_path: Path):
        """Import test results and logs from combined CSV file"""
        try:
            cursor = self.conn.cursor()

            # Delete existing results/logs for this test
            cursor.execute("DELETE FROM test_results WHERE test_id = ?", (test_id,))
            cursor.execute("DELETE FROM test_logs WHERE test_id = ?", (test_id,))
            cursor.execute("DELETE FROM failure_messages WHERE test_id = ?", (test_id,))

            with open(csv_path, 'r', encoding='utf-8', newline='') as f:
                reader = csv.DictReader(f)

                docstring = None
                has_failure = False
                failure_messages_set = set()

                for row_index, row in enumerate(reader):
                    # Extract docstring from first row
                    if row_index == 0 and 'docstring' in row and row['docstring']:
                        docstring = row['docstring'].strip()
                        if docstring:
                            cursor.execute(
                                "UPDATE tests SET docstring = ? WHERE test_id = ?",
                                (docstring, test_id)
                            )

                    # Convert row to JSON for storage
                    full_data_json = json.dumps(row)

                    # Determine if this is a result row or log row
                    is_result_row = self._is_result_row(row)

                    # Extract common fields
                    timestamp = row.get('timestamp', '') or row.get('Timestamp_original', '')
                    timestamp_int = int(timestamp) if timestamp and timestamp.isdigit() else None

                    if is_result_row:
                        # Import as test result
                        pass_value = row.get('Pass', '')
                        pass_bool = None
                        if pass_value == 'True':
                            pass_bool = 1
                        elif pass_value == 'False':
                            pass_bool = 0
                            has_failure = True

                        # Extract failure messages
                        failure_msg = row.get('Failure_Messages', '')
                        if failure_msg and pass_bool == 0:
                            failure_messages_set.add(failure_msg)

                        cursor.execute("""
                            INSERT INTO test_results (
                                test_id, row_index, timestamp, pass,
                                command_method, command_str, raw_response,
                                peak_frequency, peak_amplitude, failure_messages,
                                full_data_json
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            test_id, row_index, timestamp_int, pass_bool,
                            row.get('command_method'), row.get('command_str'), row.get('raw_response'),
                            self._parse_float(row.get('peak_frequency')),
                            self._parse_float(row.get('peak_amplitude')),
                            failure_msg,
                            full_data_json
                        ))
                    else:
                        # Import as log entry
                        cursor.execute("""
                            INSERT INTO test_logs (
                                test_id, row_index, timestamp, level, message,
                                log_type, line_number, full_data_json
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            test_id, row_index, timestamp_int,
                            row.get('level'), row.get('message'),
                            row.get('log_type'),
                            self._parse_int(row.get('line_number')),
                            full_data_json
                        ))

                # Update test status based on results
                test_status = 'failed' if has_failure else 'passed'
                cursor.execute(
                    "UPDATE tests SET status = ? WHERE test_id = ?",
                    (test_status, test_id)
                )

                # Insert failure messages
                for msg in failure_messages_set:
                    cursor.execute(
                        "INSERT INTO failure_messages (test_id, message) VALUES (?, ?)",
                        (test_id, msg)
                    )

                self.conn.commit()
                print(f"  Imported {row_index + 1} rows from CSV")

        except Exception as e:
            print(f"Error importing CSV {csv_path}: {e}")
            import traceback
            traceback.print_exc()

    def _is_result_row(self, row: Dict[str, str]) -> bool:
        """Determine if row is a test result vs log entry"""
        # Check for result indicators
        if row.get('Pass') in ('True', 'False'):
            return True
        if row.get('command_method') or row.get('keysight_xsan_command'):
            return True
        if row.get('peak_amplitude') or row.get('peak_frequency'):
            return True
        # If has log indicators, it's a log row
        if row.get('log_type') or row.get('level'):
            return False
        return False

    def _parse_float(self, value: Optional[str]) -> Optional[float]:
        """Parse float value from string"""
        if not value or value.strip() == '':
            return None
        try:
            return float(value)
        except ValueError:
            return None

    def _parse_int(self, value: Optional[str]) -> Optional[int]:
        """Parse int value from string"""
        if not value or value.strip() == '':
            return None
        try:
            return int(value)
        except ValueError:
            return None

    def register_artefact(
        self,
        test_id: Optional[int],
        artefact: ArtefactInfo,
        processed: bool = False
    ) -> int:
        """Register an artefact in the database"""
        cursor = self.conn.cursor()

        # Check if artefact already exists
        cursor.execute(
            "SELECT artefact_id FROM artefacts WHERE file_path = ?",
            (str(artefact.file_path),)
        )
        row = cursor.fetchone()

        if row:
            artefact_id = row[0]
            # Update processed status if needed
            if processed:
                cursor.execute(
                    "UPDATE artefacts SET processed = 1, processed_at = ? WHERE artefact_id = ?",
                    (datetime.now(), artefact_id)
                )
                self.conn.commit()
            return artefact_id

        # Insert new artefact
        cursor.execute("""
            INSERT INTO artefacts (
                test_id, artefact_type, file_path, file_hash, processed, processed_at
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, (
            test_id,
            artefact.artefact_type,
            str(artefact.file_path),
            artefact.file_hash,
            1 if processed else 0,
            datetime.now() if processed else None
        ))
        self.conn.commit()
        return cursor.lastrowid

    def import_test_artefacts(self, artefacts: List[ArtefactInfo]):
        """Import all artefacts for tests"""
        # Group artefacts by campaign and test
        tests_by_campaign = {}

        for artefact in artefacts:
            campaign_name = artefact.campaign_name
            test_key = (artefact.test_name, artefact.test_path)

            if campaign_name not in tests_by_campaign:
                tests_by_campaign[campaign_name] = {}
            if test_key not in tests_by_campaign[campaign_name]:
                tests_by_campaign[campaign_name][test_key] = []

            tests_by_campaign[campaign_name][test_key].append(artefact)

        # Process each campaign
        total_campaigns = len(tests_by_campaign)
        for campaign_idx, (campaign_name, tests) in enumerate(tests_by_campaign.items(), 1):
            print(f"\nProcessing campaign {campaign_idx}/{total_campaigns}: {campaign_name}")
            campaign_id = self.get_or_create_campaign(campaign_name)

            # Process each test in campaign
            total_tests = len(tests)
            for test_idx, ((test_name, test_path), test_artefacts) in enumerate(tests.items(), 1):
                print(f"  Test {test_idx}/{total_tests}: {test_name}")

                # Get or create test
                test_id = self.get_or_create_test(campaign_id, test_name, test_path)

                # Process artefacts for this test
                csv_artefact = None
                params_artefact = None
                status_artefact = None
                analyzer_artefact = None

                for artefact in test_artefacts:
                    # Check if already processed (skip if hash matches and processed)
                    if self.is_artefact_processed(artefact.file_hash):
                        print(f"    Skipping already processed: {artefact.file_path.name}")
                        self.register_artefact(test_id, artefact, processed=True)
                        continue

                    # Categorize artefacts
                    if artefact.artefact_type == 'csv' and '_combined.csv' in artefact.file_path.name:
                        csv_artefact = artefact
                    elif artefact.artefact_type == 'json':
                        if '_params.json' in artefact.file_path.name:
                            params_artefact = artefact
                        elif '_status.json' in artefact.file_path.name:
                            status_artefact = artefact
                    elif artefact.artefact_type == 'analyzer_html':
                        analyzer_artefact = artefact

                    # Register artefact
                    self.register_artefact(test_id, artefact, processed=False)

                # Import data in order
                if params_artefact:
                    print(f"    Importing params: {params_artefact.file_path.name}")
                    self.import_test_params(test_id, params_artefact.file_path)
                    self.register_artefact(test_id, params_artefact, processed=True)

                if status_artefact:
                    print(f"    Importing status: {status_artefact.file_path.name}")
                    self.import_test_status(test_id, status_artefact.file_path)
                    self.register_artefact(test_id, status_artefact, processed=True)

                if csv_artefact:
                    print(f"    Importing CSV: {csv_artefact.file_path.name}")
                    self.import_csv_data(test_id, csv_artefact.file_path)
                    self.register_artefact(test_id, csv_artefact, processed=True)

                if analyzer_artefact:
                    # Store path to analyzer HTML
                    cursor = self.conn.cursor()
                    cursor.execute(
                        "UPDATE tests SET analyzer_html_path = ? WHERE test_id = ?",
                        (str(analyzer_artefact.file_path), test_id)
                    )
                    self.conn.commit()
                    self.register_artefact(test_id, analyzer_artefact, processed=True)

    def import_directory(self, base_dir: str, incremental: bool = True):
        """Import all test results from directory"""
        self.base_dir = Path(base_dir)

        if not self.base_dir.exists():
            print(f"Error: Directory not found: {base_dir}")
            return

        print(f"Starting import from: {base_dir}")
        print(f"Incremental mode: {incremental}")

        # Scan for artefacts
        artefacts = self.scan_artefacts(self.base_dir)

        if not artefacts:
            print("No artefacts found!")
            return

        # Import artefacts
        self.import_test_artefacts(artefacts)

        print("\nImport complete!")

        # Print summary
        self.print_summary()

    def print_summary(self):
        """Print database summary statistics"""
        cursor = self.conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM campaigns")
        total_campaigns = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM tests")
        total_tests = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM tests WHERE status = 'passed'")
        passed_tests = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM tests WHERE status = 'failed'")
        failed_tests = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM test_results")
        total_results = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM test_logs")
        total_logs = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM artefacts")
        total_artefacts = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM artefacts WHERE processed = 1")
        processed_artefacts = cursor.fetchone()[0]

        print("\n" + "="*60)
        print("DATABASE SUMMARY")
        print("="*60)
        print(f"Campaigns:          {total_campaigns}")
        print(f"Tests:              {total_tests}")
        print(f"  - Passed:         {passed_tests}")
        print(f"  - Failed:         {failed_tests}")
        print(f"Test Results:       {total_results}")
        print(f"Test Logs:          {total_logs}")
        print(f"Artefacts:          {total_artefacts}")
        print(f"  - Processed:      {processed_artefacts}")
        print("="*60)


def main():
    """Main CLI function"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Import test results into SQL database"
    )
    parser.add_argument(
        'directory',
        help='Directory containing test output (usually "output")'
    )
    parser.add_argument(
        '--db',
        default='test_results.db',
        help='SQLite database path (default: test_results.db)'
    )
    parser.add_argument(
        '--full',
        action='store_true',
        help='Full import (re-process all files, ignore hash checks)'
    )
    parser.add_argument(
        '--summary',
        action='store_true',
        help='Print database summary only (do not import)'
    )

    args = parser.parse_args()

    # Create importer
    importer = SQLImporter(db_path=args.db)
    importer.connect()

    try:
        if args.summary:
            importer.print_summary()
        else:
            # Import directory
            incremental = not args.full
            importer.import_directory(args.directory, incremental=incremental)
    finally:
        importer.close()


if __name__ == "__main__":
    main()
