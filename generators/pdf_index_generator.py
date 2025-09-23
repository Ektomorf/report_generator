#!/usr/bin/env python3
"""
PDF index page generator for test reports.
"""

from datetime import datetime
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

            # Add Test Logs section
            if all_logs:
                story.append(Spacer(1, 12))
                story.append(Paragraph("Test Logs", styles['Heading2']))
                story.append(Spacer(1, 6))

                logs_table = self._create_logs_table(all_logs)
                if logs_table:
                    story.append(logs_table)

            # Add summary statistics
            summary_stats = self._generate_summary_stats(all_test_results, all_logs, len(report_files))
            story.append(Spacer(1, 12))
            story.append(Paragraph(summary_stats, styles['Normal']))
            story.append(Spacer(1, 6))
            story.append(Paragraph(f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))

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
        # Sort logs by setup_name first, then by timestamp (HH:MM:SS format)
        def parse_timestamp(log):
            timestamp = log.get('timestamp', '00:00:00')
            try:
                # Convert HH:MM:SS to seconds for proper chronological ordering
                parts = timestamp.split(':')
                if len(parts) == 3:
                    hours, minutes, seconds = map(int, parts)
                    return hours * 3600 + minutes * 60 + seconds
                return 0
            except (ValueError, AttributeError):
                return 0

        all_logs.sort(key=lambda x: (x.get('setup_name', ''), parse_timestamp(x)))

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
        created_date = datetime.fromtimestamp(setup_summary.get('created', 0)).strftime('%Y-%m-%d %H:%M:%S') if setup_summary.get('created') else 'Unknown'

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
            error_msg = test.get('error_message', '')[:60] + ('...' if len(test.get('error_message', '')) > 60 else '')

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

    def _create_logs_table(self, all_logs: List[Dict]) -> Table:
        """Create a logs table for PDF display"""
        if not all_logs:
            return None

        styles = getSampleStyleSheet()
        cell_style = ParagraphStyle(
            'LogCellStyle',
            parent=styles['Normal'],
            fontSize=7,
            leading=9,
            leftIndent=0,
            rightIndent=0,
            spaceAfter=0,
            spaceBefore=0,
            wordWrap='LTR',
            splitLongWords=True,
            allowOrphans=0,
            allowWidows=0,
        )

        # Create header row
        headers = ["Setup", "Test", "Time", "Level", "Message"]
        table_data = [headers]

        # Add log entries (limit to avoid extremely large PDFs)
        max_logs = 100  # Limit to first 100 logs for PDF readability
        for log in all_logs[:max_logs]:
            setup_name = log.get('setup_name', 'Unknown')
            test_name = log.get('test_name', 'Unknown')
            timestamp = log.get('timestamp', 'N/A')
            level = log.get('level', 'INFO')
            message = log.get('message', '')

            # Keep full message text - Paragraph will handle wrapping
            row = [
                Paragraph(setup_name, cell_style),
                Paragraph(test_name, cell_style),
                Paragraph(timestamp, cell_style),
                Paragraph(level, cell_style),
                Paragraph(message, cell_style)
            ]
            table_data.append(row)

        # Add truncation notice if logs were limited
        if len(all_logs) > max_logs:
            truncation_msg = f"Showing first {max_logs} of {len(all_logs)} log entries"
            table_data.append([
                Paragraph(truncation_msg, cell_style),
                "", "", "", ""
            ])

        # Calculate column widths
        available_width = landscape(A4)[0] - 1*inch
        col_widths = [
            available_width * 0.15,  # Setup
            available_width * 0.15,  # Test
            available_width * 0.15,  # Time
            available_width * 0.10,  # Level
            available_width * 0.45   # Message
        ]

        table = Table(table_data, colWidths=col_widths, repeatRows=1)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.Color(52/255, 152/255, 219/255)),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 8),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 7),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
            ('TOPPADDING', (0, 1), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
            ('LEFTPADDING', (0, 0), (-1, -1), 4),
            ('RIGHTPADDING', (0, 0), (-1, -1), 4),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.Color(248/255, 249/255, 250/255)]),
            ('WORDWRAP', (0, 0), (-1, -1), 'LTR'),
            ('SHRINKTOFIT', (0, 0), (-1, -1), 0),  # Disable shrink to fit to allow full expansion
        ]))

        return table