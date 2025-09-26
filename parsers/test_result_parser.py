#!/usr/bin/env python3
"""
Parser for individual test result files.
"""

from pathlib import Path
from typing import Dict, Any
from parsers.base_parser import BaseParser
from models import TestResult


class TestResultParser(BaseParser):
    """Parser for test result files"""

    def parse(self) -> TestResult:
        """Parse all result files for a test"""
        results_data = self._parse_results_json()
        params = self._parse_params_json()
        status = self._parse_status_json()
        screenshots = self._find_screenshots()
        longrepr = self._extract_longrepr()

        return TestResult(
            test_name=self.folder_name,
            test_folder=str(self.folder_path),
            results_data=results_data,
            params=params,
            status=status,
            screenshots=screenshots,
            longrepr=longrepr
        )

    def _parse_results_json(self) -> list:
        """Parse results JSON file"""
        results_file = self._find_file_with_suffix('_results.json')
        if results_file:
            data = self._load_json_file(results_file)
            return data if isinstance(data, list) else []
        return []

    def _parse_params_json(self) -> Dict[str, Any]:
        """Parse params JSON file"""
        params_file = self._find_file_with_suffix('_params.json')
        if params_file:
            return self._load_json_file(params_file)
        return {}

    def _parse_status_json(self) -> Dict[str, Any]:
        """Parse status JSON file"""
        status_file = self._find_file_with_suffix('_status.json')
        if status_file:
            return self._load_json_file(status_file)
        return {}

    def _find_screenshots(self) -> list:
        """Find all screenshot files"""
        screenshots = []
        for file in self.folder_path.glob('*.png'):
            screenshots.append(str(file))
        return screenshots

    def _extract_longrepr(self) -> str:
        """Extract longrepr from parent setup report.json"""
        try:
            # Look for report.json in the parent directory
            parent_dir = self.folder_path.parent
            report_file = parent_dir / 'report.json'

            if not report_file.exists():
                return ''

            report_data = self._load_json_file(report_file)
            if not report_data or 'tests' not in report_data:
                return ''

            # Find the test by matching the folder name to the test nodeid
            test_name_parts = self.folder_name.split('__')
            if len(test_name_parts) < 2:
                return ''

            # The actual test function name is usually the last part
            test_func_name = test_name_parts[-1]

            # Look for the test in the report data
            for test in report_data['tests']:
                nodeid = test.get('nodeid', '')
                if test_func_name in nodeid or nodeid.endswith(f'::{test_func_name}'):
                    # Check both setup and call phases for longrepr
                    for phase in ['setup', 'call']:
                        if phase in test and test[phase].get('outcome') == 'failed':
                            longrepr = test[phase].get('longrepr', '')
                            if longrepr:
                                return longrepr
                    break

            return ''
        except Exception:
            # If there's any error reading the report, just return empty string
            return ''