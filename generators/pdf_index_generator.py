#!/usr/bin/env python3
"""
PDF index page generator for test reports.
"""

from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any

try:
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
    from reportlab.lib.units import inch
    HAS_REPORTLAB = True
except ImportError:
    HAS_REPORTLAB = False

from models import SetupReport
from generators.pdf_templates import PDFTemplates


class PDFIndexGenerator:
    """Generator for PDF index pages"""

    def __init__(self):
        self.template = PDFTemplates.get_index_template()

    def generate_index(self, report_files: List[Path], index_file: Path,
                      test_session: str, setup_data: List[SetupReport] = None) -> None:
        """Generate a PDF index page with test results summary"""

        if not HAS_REPORTLAB:
            print(f"Warning: ReportLab not available. Skipping PDF index generation.")
            return

        if setup_data is None:
            setup_data = []

        try:
            # Use A4 landscape for index
            doc = SimpleDocTemplate(
                str(index_file),
                pagesize=landscape(A4),
                leftMargin=0.5*inch,
                rightMargin=0.5*inch,
                topMargin=0.75*inch,
                bottomMargin=0.75*inch
            )

            story = []
            styles = getSampleStyleSheet()

            # Add title
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=16,
                spaceAfter=12,
                textColor=colors.Color(44/255, 62/255, 80/255),
            )
            story.append(Paragraph(f"Test Reports Index - {test_session}", title_style))
            story.append(Spacer(1, 12))

            # Process and display setup data
            test_runs = self._group_reports_by_test_run(report_files)
            all_test_results, all_logs = self._process_setup_data(setup_data)

            if setup_data:
                story.append(Paragraph("Test Results Summary", styles['Heading2']))
                story.append(Spacer(1, 6))

                # Create summary table
                summary_data = [['Setup', 'Total Tests', 'Passed', 'Failed', 'Duration']]
                for setup in setup_data:
                    summary = setup.test_summary
                    summary_data.append([
                        setup.setup_name,
                        str(summary.get('total', 0)),
                        str(summary.get('passed', 0)),
                        str(summary.get('failed', 0) + summary.get('error', 0)),
                        f"{summary.get('duration', 0):.1f}s"
                    ])

                summary_table = Table(summary_data)
                summary_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.Color(52/255, 152/255, 219/255)),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 1), (-1, -1), 9),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.Color(248/255, 249/255, 250/255)]),
                ]))
                story.append(summary_table)
                story.append(Spacer(1, 12))

            # Add available reports
            if report_files:
                story.append(Paragraph("Available PDF Reports", styles['Heading2']))
                story.append(Spacer(1, 6))

                grouped_reports = self._group_reports_by_test_run(report_files)
                for test_run, reports in sorted(grouped_reports.items()):
                    story.append(Paragraph(f"• {test_run}:", styles['Normal']))
                    for report in sorted(reports):
                        report_name = report.stem.replace('_report', '')
                        story.append(Paragraph(f"  - {report_name}.pdf", styles['Normal']))
                    story.append(Spacer(1, 6))

            # Add summary statistics
            summary_stats = self._generate_summary_stats(all_test_results, all_logs, len(report_files))
            story.append(Spacer(1, 12))
            story.append(Paragraph(summary_stats, styles['Normal']))
            story.append(Spacer(1, 6))
            story.append(Paragraph(f"Generated on {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}", styles['Normal']))

            # Build PDF
            doc.build(story)
            print(f"Generated PDF index: {index_file}")

        except Exception as e:
            print(f"Error generating PDF index {index_file}: {str(e)}")

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

    def _generate_content(self, test_runs: Dict[str, List[Path]], setup_data: List[SetupReport]) -> str:
        """Generate the main content for the PDF index"""
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
                    <span style="float: right; font-size: 9pt;">
                        {setup_summary.get('passed', 0)} Passed | {setup_summary.get('failed', 0) + setup_summary.get('error', 0)} Failed |
                        Duration: {setup_summary.get('duration', 0):.1f}s | {created_date}
                    </span>
                </div>

                <div class="test-run-content">
                    <h4>Test Results</h4>
                    <table class="results-table">
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
            full_error_msg = test.get('error_message', '')

            # For PDF, we show full message if it's scrollable, otherwise truncate
            error_class = "error-message"
            if len(full_error_msg) > 200:
                error_class += " scrollable"
                error_msg = full_error_msg  # Show full message in scrollable container
            else:
                error_msg = full_error_msg[:60] + ('...' if len(full_error_msg) > 60 else '')

            # HTML escape the error message and process newlines to prevent HTML injection
            import html
            escaped_error_msg = html.escape(error_msg)
            # Convert newlines to <br> tags for proper display
            formatted_error_msg = escaped_error_msg.replace('\n', '<br>')

            content += f"""
                            <tr class="{outcome_class}">
                                <td>{html.escape(test['name'])}</td>
                                <td>{html.escape(test['outcome'].upper())}</td>
                                <td>{test['duration']:.2f}s</td>
                                <td class="{error_class}">{formatted_error_msg}</td>
                            </tr>
            """

        content += """
                        </tbody>
                    </table>
        """

        if reports:
            content += """
                    <h4>Available PDF Reports</h4>
                    <ul class="report-list">
            """
            for report_file in sorted(reports):
                test_name = report_file.stem.replace('_report', '')
                # For PDF, just list the report names since links don't work
                content += f'                        <li>📄 {test_name}_report.pdf</li>\n'

            content += "                    </ul>"
        else:
            content += "                    <p><em>No detailed PDF reports generated for this setup.</em></p>"

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
                <div class="test-run-content">
                    <h4>Available PDF Reports</h4>
                    <ul class="report-list">
        """

        for report_file in sorted(reports):
            test_name = report_file.stem.replace('_report', '')
            content += f'                        <li>📄 {test_name}_report.pdf</li>\n'

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

        return f"{total_setups} setup runs • {total_tests} tests • {total_passed} passed • {total_failed} failed • {len(all_logs)} log entries • {total_reports} PDF reports"