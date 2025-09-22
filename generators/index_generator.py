#!/usr/bin/env python3
"""
Index page generator for test reports.
"""

from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

from models import SetupReport
from generators.html_templates import HTMLTemplates


class IndexGenerator:
    """Generator for index pages with links to all reports"""

    def __init__(self):
        self.template = HTMLTemplates.get_index_template()

    def generate_index(self, report_files: List[Path], index_file: Path,
                      test_session: str, setup_data: List[SetupReport] = None) -> None:
        """Generate an index page with links to all reports and setup test results"""

        if setup_data is None:
            setup_data = []

        test_runs = self._group_reports_by_test_run(report_files)
        all_test_results, all_logs = self._process_setup_data(setup_data)
        content = self._generate_content(test_runs, setup_data, all_logs)
        summary_stats = self._generate_summary_stats(all_test_results, all_logs, len(report_files))

        html_content = self.template.format(
            test_session=test_session,
            content=content,
            generation_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            summary_stats=summary_stats
        )

        with open(index_file, 'w') as f:
            f.write(html_content)

        print(f"Generated index: {index_file}")

    def _group_reports_by_test_run(self, report_files: List[Path]) -> Dict[str, List[Path]]:
        """Group reports by test run (parent folder)"""
        test_runs = {}
        for report_file in report_files:
            test_run = report_file.parent.name
            if test_run not in test_runs:
                test_runs[test_run] = []
            test_runs[test_run].append(report_file)
        return test_runs

    def _process_setup_data(self, setup_data: List[SetupReport]) -> tuple:
        """Process setup data to extract test results and logs"""
        all_test_results = []
        all_logs = []

        for setup in setup_data:
            setup_summary = setup.test_summary

            setup_result = {
                'setup_name': setup.setup_name,
                'test_name': 'Overall',
                'outcome': 'passed' if setup_summary.get('error', 0) == 0 and setup_summary.get('failed', 0) == 0 else 'failed',
                'duration': f"{setup_summary.get('duration', 0):.2f}s",
                'passed_tests': setup_summary.get('passed', 0),
                'failed_tests': setup_summary.get('failed', 0) + setup_summary.get('error', 0),
                'total_tests': setup_summary.get('total', 0),
                'created': setup_summary.get('created', 0)
            }
            all_test_results.append(setup_result)

            for test in setup.tests:
                test_result = {
                    'setup_name': setup.setup_name,
                    'test_name': test['name'],
                    'outcome': test['outcome'],
                    'duration': f"{test['duration']:.2f}s",
                    'error_message': test.get('error_message', ''),
                    'created': setup_summary.get('created', 0)
                }
                all_test_results.append(test_result)

            for log in setup.logs:
                log['setup_name'] = setup.setup_name
                all_logs.append(log)

        all_test_results.sort(key=lambda x: (x['created'], x['setup_name'], x['test_name']))
        all_logs.sort(key=lambda x: (x.get('setup_name', ''), x.get('timestamp', '')))

        return all_test_results, all_logs

    def _generate_content(self, test_runs: Dict[str, List[Path]],
                         setup_data: List[SetupReport], all_logs: List[Dict]) -> str:
        """Generate the main content for both tabs"""
        logs_content = self._generate_logs_content(all_logs)
        reports_content = self._generate_reports_content(test_runs, setup_data)

        return f"""
        <!-- Test Logs Tab -->
        <div id="test-logs" class="tab-content">
            <h3>Test Execution Logs</h3>
            {logs_content}
        </div>

        <!-- Detailed Reports Tab -->
        <div id="detailed-reports" class="tab-content">
            <h3>Test Results and Detailed Reports</h3>
            {reports_content}
        </div>
        """

    def _generate_logs_content(self, all_logs: List[Dict]) -> str:
        """Generate content for the logs tab"""
        if not all_logs:
            return "<p>No logs available.</p>"

        content = """
            <table class="logs-table">
                <thead>
                    <tr>
                        <th>Setup</th>
                        <th>Test</th>
                        <th>Time</th>
                        <th>Level</th>
                        <th>Message</th>
                    </tr>
                </thead>
                <tbody>
        """

        for log in all_logs:
            level_class = f"log-{log.get('level', 'info').lower()}"
            content += f"""
                    <tr>
                        <td>{log.get('setup_name', 'Unknown')}</td>
                        <td>{log.get('test_name', 'Unknown')}</td>
                        <td>{log.get('timestamp', 'N/A')}</td>
                        <td class="{level_class}">{log.get('level', 'INFO')}</td>
                        <td>{log.get('message', '')}</td>
                    </tr>
            """

        content += """
                </tbody>
            </table>
        """
        return content

    def _generate_reports_content(self, test_runs: Dict[str, List[Path]],
                                 setup_data: List[SetupReport]) -> str:
        """Generate content for the detailed reports tab"""
        setup_results_map = {setup.setup_name: setup for setup in setup_data}
        processed_setups = set()
        content = ""

        # Process setups with both results and detailed reports
        for test_run_name in sorted(test_runs.keys()):
            if test_run_name in setup_results_map:
                setup = setup_results_map[test_run_name]
                reports = test_runs[test_run_name]
                processed_setups.add(test_run_name)
                content += self._generate_setup_section(setup, reports)

        # Process setups with only test results
        for setup in setup_data:
            if setup.setup_name not in processed_setups:
                content += self._generate_setup_section(setup, [])

        # Process test runs with only detailed reports
        for test_run_name in sorted(test_runs.keys()):
            if test_run_name not in setup_results_map:
                reports = test_runs[test_run_name]
                content += self._generate_reports_only_section(test_run_name, reports)

        return content

    def _generate_setup_section(self, setup: SetupReport, reports: List[Path]) -> str:
        """Generate a section for a setup with test results and optional reports"""
        setup_summary = setup.test_summary
        created_date = datetime.fromtimestamp(setup_summary.get('created', 0)).strftime('%Y-%m-%d %H:%M:%S') if setup_summary.get('created') else 'Unknown'

        content = f"""
            <div class="test-run">
                <div class="test-run-header">
                    {setup.setup_name}
                    <span style="float: right; font-size: 14px;">
                        {setup_summary.get('passed', 0)} Passed | {setup_summary.get('failed', 0) + setup_summary.get('error', 0)} Failed |
                        Duration: {setup_summary.get('duration', 0):.1f}s | {created_date}
                    </span>
                </div>

                <div style="padding: 15px;">
                    <h4>Test Results</h4>
                    <table class="results-table" style="margin: 10px 0;">
                        <thead>
                            <tr>
                                <th>Test Name</th>
                                <th>Result</th>
                                <th>Duration</th>
                                <th>Error Message</th>
                            </tr>
                        </thead>
                        <tbody>
        """

        for test in setup.tests:
            outcome_class = test['outcome'] if test['outcome'] in ['passed', 'failed', 'error'] else ''
            error_msg = test.get('error_message', '')[:80] + ('...' if len(test.get('error_message', '')) > 80 else '')

            content += f"""
                            <tr class="{outcome_class}">
                                <td>{test['name']}</td>
                                <td>{test['outcome'].upper()}</td>
                                <td>{test['duration']:.2f}s</td>
                                <td class="error-message">{error_msg}</td>
                            </tr>
            """

        content += """
                        </tbody>
                    </table>
        """

        if reports:
            content += """
                    <h4>Detailed Reports</h4>
                    <ul class="report-list">
            """
            for report_file in sorted(reports):
                test_name = report_file.stem.replace('_report', '')
                relative_path = f"{setup.setup_name}/{report_file.name}"
                content += f'                        <li><a href="{relative_path}">{test_name}</a></li>\n'

            content += "                    </ul>"
        else:
            content += "                    <p><em>No detailed reports available for this setup.</em></p>"

        content += """
                </div>
            </div>
        """
        return content

    def _generate_reports_only_section(self, test_run_name: str, reports: List[Path]) -> str:
        """Generate a section for test runs with only detailed reports"""
        content = f"""
            <div class="test-run">
                <div class="test-run-header">{test_run_name}</div>
                <div style="padding: 15px;">
                    <h4>Detailed Reports</h4>
                    <ul class="report-list">
        """

        for report_file in sorted(reports):
            test_name = report_file.stem.replace('_report', '')
            relative_path = f"{test_run_name}/{report_file.name}"
            content += f'                        <li><a href="{relative_path}">{test_name}</a></li>\n'

        content += """                    </ul>
                    <p><em>No test results summary available for this setup.</em></p>
                </div>
            </div>
        """
        return content

    def _generate_summary_stats(self, all_test_results: List[Dict],
                               all_logs: List[Dict], total_reports: int) -> str:
        """Generate summary statistics for the footer"""
        total_setups = len(set(result.get('setup_name') for result in all_test_results if result.get('setup_name')))
        total_tests = sum(result.get('total_tests', 0) for result in all_test_results if result.get('total_tests'))
        total_passed = sum(result.get('passed_tests', 0) for result in all_test_results if result.get('passed_tests'))
        total_failed = sum(result.get('failed_tests', 0) for result in all_test_results if result.get('failed_tests'))

        return f"{total_setups} setup runs • {total_tests} tests • {total_passed} passed • {total_failed} failed • {len(all_logs)} log entries • {total_reports} detailed reports"