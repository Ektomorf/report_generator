#!/usr/bin/env python3
"""
Parser for setup report.json files.
"""

import re
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from parsers.base_parser import BaseParser
from models import SetupReport, TestSummary, TestInfo, LogEntry


class SetupReportParser(BaseParser):
    """Parser for setup report.json files"""

    def parse(self) -> SetupReport:
        """Parse report.json and collect test logs"""
        report_file = self.folder_path / 'report.json'
        report_data = self._load_json_file(report_file) if report_file.exists() else {}

        test_summary = self._extract_test_summary(report_data)
        tests = self._extract_test_results(report_data)
        logs = self._collect_test_logs()

        return SetupReport(
            setup_name=self.folder_name,
            setup_folder=str(self.folder_path),
            test_summary=test_summary,
            tests=tests,
            logs=logs
        )

    def _extract_test_summary(self, report_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract summary information from report"""
        summary = report_data.get('summary', {})
        return {
            'total': summary.get('total', 0),
            'passed': summary.get('passed', 0),
            'failed': summary.get('failed', 0),
            'error': summary.get('error', 0),
            'duration': report_data.get('duration', 0),
            'created': report_data.get('created', 0)
        }

    def _extract_test_results(self, report_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract individual test results"""
        tests = []
        for test in report_data.get('tests', []):
            test_info = {
                'name': test.get('nodeid', '').replace('::', ''),
                'outcome': test.get('outcome', 'unknown'),
                'duration': self._calculate_test_duration(test),
                'error_message': self._extract_error_message(test)
            }
            tests.append(test_info)
        return tests

    def _calculate_test_duration(self, test: Dict[str, Any]) -> float:
        """Calculate total test duration from all phases"""
        duration = 0.0
        for phase in ['setup', 'call', 'teardown']:
            if phase in test:
                duration += test[phase].get('duration', 0)
        return duration

    def _extract_error_message(self, test: Dict[str, Any]) -> str:
        """Extract error message from failed test"""
        if test.get('outcome') not in ['failed', 'error']:
            return ''

        for phase in ['setup', 'call']:
            if phase in test and test[phase].get('outcome') == 'failed':
                # Use longrepr as the primary source for error messages
                longrepr = test[phase].get('longrepr', '')
                if longrepr:
                    return longrepr
                # Fallback to crash message if longrepr is empty
                crash = test[phase].get('crash', {})
                return crash.get('message', '')

        return ''

    def _collect_test_logs(self) -> List[Dict[str, Any]]:
        """Collect logs from all test subdirectories"""
        logs = []

        # Get the setup creation date to combine with log times
        report_file = self.folder_path / 'report.json'
        report_data = self._load_json_file(report_file) if report_file.exists() else {}
        setup_created = report_data.get('created', 0)
        setup_date = None
        if setup_created:
            setup_date = datetime.fromtimestamp(setup_created, tz=timezone.utc).date()

        for test_dir in self.folder_path.iterdir():
            if test_dir.is_dir() and test_dir.name.startswith('test_'):
                logs.extend(self._parse_test_logs(test_dir, setup_date))

        return sorted(logs, key=lambda x: x.get('timestamp', ''))

    def _parse_test_logs(self, test_dir: Path, setup_date=None) -> List[Dict[str, Any]]:
        """Parse logs from a single test directory"""
        logs = []
        log_file = self._find_log_file(test_dir)

        if not log_file or not log_file.exists():
            return logs

        try:
            with open(log_file, 'r') as f:
                content = f.read().strip()
                if content:
                    for line in content.split('\n'):
                        log_entry = self._parse_log_line(line.strip(), setup_date)
                        if log_entry:
                            log_entry['test_name'] = test_dir.name
                            logs.append(log_entry)
        except Exception as e:
            print(f"Warning: Could not read log file {log_file}: {str(e)}")

        return logs

    def _find_log_file(self, test_dir: Path) -> Optional[Path]:
        """Find the log file in a test directory"""
        for file in test_dir.glob('*.log'):
            return file
        return None

    def _parse_log_line(self, line: str, setup_date=None) -> Optional[Dict[str, Any]]:
        """Parse a single log line to extract timestamp, level, and message"""
        if not line:
            return None

        log_pattern = r'^(\d{2}:\d{2}:\d{2})\s*-\s*(INFO|DEBUG|ERROR|WARNING|WARN)\s*-\s*(.+)$'
        match = re.match(log_pattern, line)

        if match:
            time_str, level, message = match.groups()

            # Combine setup date with log time to create full timestamp
            if setup_date:
                full_timestamp = f"{setup_date.strftime('%Y-%m-%d')} {time_str}"
            else:
                # Fallback to just the time if no date available
                full_timestamp = time_str

            return {
                'timestamp': full_timestamp,
                'level': level.upper(),
                'message': message.strip()
            }

        return None