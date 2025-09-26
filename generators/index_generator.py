#!/usr/bin/env python3
"""
Index page generator for test reports.
"""

from datetime import datetime, timezone
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
            generation_time=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
            summary_stats=summary_stats
        )

        with open(index_file, 'w', encoding='utf-8') as f:
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
        """Generate content for the logs tab with navigation"""
        if not all_logs:
            return "<p>No logs available.</p>"

        # Group logs by setup and test for navigation
        logs_by_setup = {}
        for log in all_logs:
            setup_name = log.get('setup_name', 'Unknown')
            test_name = log.get('test_name', 'Unknown')

            if setup_name not in logs_by_setup:
                logs_by_setup[setup_name] = {}
            if test_name not in logs_by_setup[setup_name]:
                logs_by_setup[setup_name][test_name] = []

            logs_by_setup[setup_name][test_name].append(log)

        # Generate navigation sidebar and content
        content = """
            <div style="display: flex; gap: 20px;">
                <div style="flex: 0 0 300px; background: #f8f9fa; padding: 15px; border-radius: 8px; border: 1px solid #ddd; max-height: 600px; overflow-y: auto;">
                    <h4 style="margin-top: 0; color: #2c3e50;">Log Navigation</h4>
                    <div class="log-navigation">
        """

        # Build navigation tree
        for setup_name in sorted(logs_by_setup.keys()):
            setup_id = setup_name.replace(' ', '_').replace('/', '_')
            content += f"""
                        <div class="nav-setup">
                            <div class="nav-setup-header" onclick="toggleNavSection('{setup_id}')" style="cursor: pointer; padding: 8px; background: #e9ecef; border-radius: 4px; margin: 5px 0; font-weight: bold; border: 1px solid #ced4da;">
                                📁 {setup_name} ({sum(len(tests) for tests in logs_by_setup[setup_name].values())} logs)
                                <span id="arrow_{setup_id}" style="float: right;">▼</span>
                            </div>
                            <div id="nav_{setup_id}" class="nav-tests" style="margin-left: 15px; display: block;">
            """

            for test_name in sorted(logs_by_setup[setup_name].keys()):
                test_id = f"{setup_id}_{test_name.replace(' ', '_').replace('/', '_')}"
                log_count = len(logs_by_setup[setup_name][test_name])
                content += f"""
                                <div class="nav-test" onclick="jumpToLogs('{test_id}')" style="cursor: pointer; padding: 6px; margin: 2px 0; background: white; border-radius: 3px; border: 1px solid #e0e0e0; font-size: 12px;">
                                    📄 {test_name} ({log_count} logs)
                                </div>
                """

            content += """
                            </div>
                        </div>
            """

        content += """
                    </div>
                </div>
                <div style="flex: 1;">
                    <div style="margin-bottom: 15px;">
                        <input type="text" id="logFilter" placeholder="Filter logs by message..." style="width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px;" onkeyup="filterLogs()">
                    </div>
        """

        # Generate main log content organized by setup and test
        for setup_name in sorted(logs_by_setup.keys()):
            setup_id = setup_name.replace(' ', '_').replace('/', '_')
            content += f"""
                    <div class="log-setup-section" id="logs_{setup_id}" style="margin-bottom: 30px; border: 1px solid #ddd; border-radius: 8px; overflow: hidden;">
                        <div style="background: #3498db; color: white; padding: 10px; font-weight: bold;">
                            {setup_name}
                        </div>
            """

            for test_name in sorted(logs_by_setup[setup_name].keys()):
                test_id = f"{setup_id}_{test_name.replace(' ', '_').replace('/', '_')}"
                test_logs = logs_by_setup[setup_name][test_name]

                content += f"""
                        <div class="log-test-section" id="logs_{test_id}" style="margin: 15px; border: 1px solid #e0e0e0; border-radius: 5px;">
                            <div style="background: #f8f9fa; padding: 8px; font-weight: bold; border-bottom: 1px solid #e0e0e0;">
                                📄 {test_name} ({len(test_logs)} log entries)
                            </div>
                            <table class="logs-table" style="width: 100%; border-collapse: collapse; margin: 0;">
                                <thead>
                                    <tr>
                                        <th style="background: #34495e; color: white; padding: 6px; border: 1px solid #ddd;">Time</th>
                                        <th style="background: #34495e; color: white; padding: 6px; border: 1px solid #ddd;">Level</th>
                                        <th style="background: #34495e; color: white; padding: 6px; border: 1px solid #ddd;">Message</th>
                                    </tr>
                                </thead>
                                <tbody>
                """

                for log in test_logs:
                    level_class = f"log-{log.get('level', 'info').lower()}"

                    # Format timestamp to show full UTC date/time
                    timestamp = log.get('timestamp', 'N/A')
                    if timestamp != 'N/A':
                        # If it's already a full date/time format from enhanced parsing
                        if len(timestamp) > 8:  # More than just HH:MM:SS
                            if 'UTC' not in timestamp.upper() and '+' not in timestamp and 'Z' not in timestamp:
                                timestamp = f"{timestamp} UTC"
                        else:
                            # Legacy format - just time, so indicate this is time-only
                            timestamp = f"{timestamp} (time only) UTC"

                    content += f"""
                                    <tr class="log-row" data-message="{log.get('message', '').lower()}">
                                        <td style="padding: 4px 6px; border: 1px solid #ddd; font-family: monospace; font-size: 11px; white-space: nowrap;">{timestamp}</td>
                                        <td class="{level_class}" style="padding: 4px 6px; border: 1px solid #ddd; font-weight: bold; text-align: center; width: 80px;">{log.get('level', 'INFO')}</td>
                                        <td style="padding: 4px 6px; border: 1px solid #ddd; font-family: monospace; font-size: 11px; word-break: break-word;">{log.get('message', '')}</td>
                                    </tr>
                    """

                content += """
                                </tbody>
                            </table>
                        </div>
                """

            content += """
                    </div>
            """

        content += """
                </div>
            </div>

            <script>
                function toggleNavSection(setupId) {
                    const section = document.getElementById('nav_' + setupId);
                    const arrow = document.getElementById('arrow_' + setupId);
                    if (section.style.display === 'none') {
                        section.style.display = 'block';
                        arrow.textContent = '▼';
                    } else {
                        section.style.display = 'none';
                        arrow.textContent = '▶';
                    }
                }

                function jumpToLogs(testId) {
                    const element = document.getElementById('logs_' + testId);
                    if (element) {
                        element.scrollIntoView({behavior: 'smooth', block: 'start'});
                        element.style.boxShadow = '0 0 10px #3498db';
                        setTimeout(() => {
                            element.style.boxShadow = '';
                        }, 2000);
                    }
                }

                function filterLogs() {
                    const filter = document.getElementById('logFilter').value.toLowerCase();
                    const rows = document.querySelectorAll('.log-row');

                    rows.forEach(row => {
                        const message = row.getAttribute('data-message');
                        if (message.includes(filter)) {
                            row.style.display = '';
                        } else {
                            row.style.display = 'none';
                        }
                    });
                }
            </script>
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
        created_date = datetime.fromtimestamp(setup_summary.get('created', 0), tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC') if setup_summary.get('created') else 'Unknown'

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