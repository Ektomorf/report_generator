#!/usr/bin/env python3
"""
PDF report generator for individual test results.
"""

import base64
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

try:
    import pdfkit
    HAS_PDFKIT = True
except ImportError:
    HAS_PDFKIT = False

try:
    from reportlab.lib.pagesizes import A2, landscape
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
    from reportlab.lib.units import inch
    HAS_REPORTLAB = True
except ImportError:
    HAS_REPORTLAB = False

from models import TestResult
from generators.pdf_templates import PDFTemplates


class PDFReportGenerator:
    """Generator for PDF test reports"""

    def __init__(self):
        self.template = PDFTemplates.get_main_template()

    def generate_report(self, test_result: TestResult, output_file: Path) -> None:
        """Generate PDF report for a single test"""
        if HAS_REPORTLAB:
            self._generate_reportlab_pdf(test_result, output_file)
        elif HAS_PDFKIT:
            self._generate_pdfkit_pdf(test_result, output_file)
        else:
            print(f"Warning: No PDF generation library available. Skipping PDF generation for {test_result.test_name}")

    def _generate_reportlab_pdf(self, test_result: TestResult, output_file: Path) -> None:
        """Generate PDF using ReportLab (native PDF generation)"""
        try:
            # Use A2 landscape for very wide tables
            doc = SimpleDocTemplate(
                str(output_file),
                pagesize=landscape(A2),
                leftMargin=0.5*inch,
                rightMargin=0.5*inch,
                topMargin=0.75*inch,
                bottomMargin=0.75*inch
            )

            # Create story (content) list
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
            story.append(Paragraph(f"Test Report: {test_result.test_name}", title_style))
            story.append(Spacer(1, 12))

            # Add status info
            if test_result.status:
                status_text = f"Status: {test_result.status.get('status', 'UNKNOWN')}"
                if test_result.status.get('duration'):
                    status_text += f" | Duration: {test_result.status.get('duration')}"
                story.append(Paragraph(status_text, styles['Normal']))
                story.append(Spacer(1, 6))

            # Add test description if available
            description = self._extract_description(test_result.params, test_result.results_data)
            if description:
                story.append(Paragraph(f"<b>Description:</b> {description}", styles['Normal']))
                story.append(Spacer(1, 12))

            # Add test results table
            if test_result.results_data:
                story.append(Paragraph("Test Results", styles['Heading2']))
                story.append(Spacer(1, 6))

                table_data = self._create_table_data(test_result.results_data)
                if table_data:
                    # Create table with appropriate column widths
                    col_count = len(table_data[0]) if table_data else 0
                    # Calculate column widths - distribute evenly but with constraints
                    available_width = landscape(A2)[0] - 1*inch  # Page width minus margins
                    col_width = min(available_width / col_count, 1.5*inch)  # Max 1.5 inches per column
                    col_widths = [col_width] * col_count

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
                        ('TOPPADDING', (0, 1), (-1, -1), 6),  # Increased top padding
                        ('BOTTOMPADDING', (0, 1), (-1, -1), 6),  # Increased bottom padding
                        ('LEFTPADDING', (0, 0), (-1, -1), 4),  # Increased left padding
                        ('RIGHTPADDING', (0, 0), (-1, -1), 4),  # Increased right padding
                        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.Color(248/255, 249/255, 250/255)]),
                        ('WORDWRAP', (0, 0), (-1, -1), 'LTR'),  # Enable word wrapping
                        ('SHRINKTOFIT', (0, 0), (-1, -1), 1),  # Allow text to shrink to fit
                    ]))
                    story.append(table)

            # Add screenshots section
            if test_result.screenshots:
                story.append(PageBreak())  # Start screenshots on new page
                story.append(Paragraph("Screenshots", styles['Heading2']))
                story.append(Spacer(1, 12))

                for screenshot_path in test_result.screenshots:
                    screenshot_name = Path(screenshot_path).name
                    try:
                        # Add screenshot title
                        story.append(Paragraph(screenshot_name, styles['Heading3']))
                        story.append(Spacer(1, 6))

                        # Add the image
                        img = Image(screenshot_path)
                        # Scale image to fit page width while maintaining aspect ratio
                        img_width, img_height = img.drawWidth, img.drawHeight
                        max_width = landscape(A2)[0] - 1*inch  # Available width
                        max_height = 6*inch  # Maximum height for images

                        # Calculate scaling
                        width_scale = max_width / img_width
                        height_scale = max_height / img_height
                        scale = min(width_scale, height_scale, 1.0)  # Don't upscale

                        img.drawWidth = img_width * scale
                        img.drawHeight = img_height * scale

                        story.append(img)
                        story.append(Spacer(1, 12))

                    except Exception as e:
                        # If image can't be loaded, show error message
                        error_msg = f"Error loading image {screenshot_name}: {str(e)}"
                        story.append(Paragraph(error_msg, styles['Normal']))
                        story.append(Spacer(1, 12))

            # Add generation timestamp
            story.append(Spacer(1, 24))
            story.append(Paragraph(f"Report generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                                  styles['Normal']))

            # Build PDF
            doc.build(story)
            print(f"Generated PDF report: {output_file}")

        except Exception as e:
            print(f"Error generating PDF report {output_file}: {str(e)}")

    def _generate_pdfkit_pdf(self, test_result: TestResult, output_file: Path) -> None:
        """Generate PDF using pdfkit (requires wkhtmltopdf)"""
        try:
            table_headers = self._generate_table_headers(test_result.results_data)
            table_rows = self._generate_table_rows(test_result.results_data)
            screenshot_html = self._generate_screenshot_html(test_result.screenshots)
            status_info = self._generate_status_info(test_result.status)
            description_info = self._generate_description_info(test_result.params, test_result.results_data)
            params_info = self._generate_params_info(test_result.params)

            html_content = self.template.format(
                test_name=test_result.test_name,
                status_info=status_info,
                description_info=description_info,
                params_info=params_info,
                table_headers=table_headers,
                table_rows=table_rows,
                screenshot_html=screenshot_html,
                generation_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            )

            # Configure pdfkit options for landscape and large page
            options = {
                'page-size': 'A2',
                'orientation': 'Landscape',
                'margin-top': '0.5in',
                'margin-right': '0.5in',
                'margin-bottom': '0.5in',
                'margin-left': '0.5in',
                'encoding': "UTF-8",
                'no-outline': None
            }

            pdfkit.from_string(html_content, str(output_file), options=options)
            print(f"Generated PDF report: {output_file}")

        except Exception as e:
            print(f"Error generating PDF report {output_file}: {str(e)}")

    def _get_all_unique_keys(self, results_data: List[Dict]) -> List[str]:
        """Get all unique keys from the results data in a consistent order"""
        if not results_data:
            return []

        all_keys = set()
        for entry in results_data:
            all_keys.update(entry.keys())

        # Remove docstring fields for table display
        docstring_fields = {'docstring', 'test_description', 'description', 'Docstring', 'Test_Description', 'Description'}
        all_keys = all_keys - docstring_fields

        # Define preferred order for common keys
        key_order = [
            'Timestamp',
            'channel', 'frequency', 'enabled', 'gain',
            'spectrum_frequencies', 'spectrum_amplitudes',
            'peak_frequency', 'peak_amplitude', 'screenshot_filepath',
            'socan_command_method', 'socan_command_args', 'socan_command',
            'parsed_socan_response', 'raw_socan_response',
            'rf_matrix_command_method', 'rf_matrix_command_args', 'rf_matrix_command',
            'parsed_rf_matrix_response', 'raw_rf_matrix_response',
            'keysight_xsan_command_method', 'keysight_xsan_command_args', 'keysight_xsan_command',
            'frequencies', 'amplitudes',
        ]

        ordered_keys = []
        remaining_keys = set(all_keys)

        # Add keys in preferred order
        for key in key_order:
            if key in remaining_keys:
                ordered_keys.append(key)
                remaining_keys.remove(key)

        # Add channel-specific keys
        channel_keys = [k for k in remaining_keys if any(k.startswith(base) for base in ['enabled_', 'frequency_', 'gain_'])]
        for key in sorted(channel_keys):
            ordered_keys.append(key)
            remaining_keys.remove(key)

        # Add remaining keys alphabetically
        ordered_keys.extend(sorted(remaining_keys))
        return ordered_keys

    def _generate_table_headers(self, results_data: List[Dict]) -> str:
        """Generate HTML table headers optimized for PDF"""
        if not results_data:
            return "<tr><th>No Data</th></tr>"

        all_keys = self._get_all_unique_keys(results_data)
        headers = ["#"]  # Row number column

        for key in all_keys:
            # Format key names for display
            display_name = key.replace('_', ' ').title()

            # Special formatting for readability in PDF
            if 'socan' in key.lower():
                display_name = display_name.replace('Socan', 'SOCAN')
            elif 'rf' in key.lower() and 'matrix' in key.lower():
                display_name = display_name.replace('Rf Matrix', 'RF Matrix')
            elif 'xsan' in key.lower():
                display_name = display_name.replace('Xsan', 'XSAN')
            elif 'ghz' in key.lower():
                display_name = display_name.replace('Ghz', 'GHz')
            elif 'dbm' in key.lower():
                display_name = display_name.replace('Dbm', 'dBm')

            # Truncate very long header names for PDF
            if len(display_name) > 15:
                display_name = display_name[:12] + "..."

            headers.append(display_name)

        header_row = "<tr>" + "".join(f"<th>{header}</th>" for header in headers) + "</tr>"
        return header_row

    def _format_cell_value_for_pdf(self, key: str, value: Any) -> str:
        """Format cell value specifically for PDF output"""
        if value is None:
            return 'N/A'

        # Handle different value types with PDF-specific limits
        if isinstance(value, dict):
            content = str(value)
            # Truncate very long dict content for PDF
            if len(content) > 200:
                return f'<div class="cell-content">{content[:197]}...</div>'
            return content
        elif isinstance(value, list):
            if len(value) > 10:
                content = f"[{len(value)} items]"
            else:
                content = str(value)
                if len(content) > 150:
                    content = f'<div class="cell-content">{content[:147]}...</div>'
            return content
        elif isinstance(value, str):
            # Truncate very long strings for PDF readability
            if len(value) > 200:
                return f'<div class="cell-content">{value[:197]}...</div>'
            return value

        # Special formatting for specific keys
        if 'peak_frequency' in key.lower() and isinstance(value, (int, float)):
            if 'ghz' not in key.lower():
                return f"{value / 1e9:.3f} GHz"
            else:
                return f"{value:.3f} GHz"
        elif 'peak_amplitude' in key.lower() and isinstance(value, (int, float)):
            if 'dbm' not in key.lower():
                return f"{value:.2f} dBm"
            else:
                return f"{value:.2f}"
        elif 'frequency' in key.lower() and isinstance(value, (int, float)):
            if value > 1000000:
                return f"{value / 1e9:.3f} GHz"
            return str(value)
        elif 'screenshot_filepath' in key.lower() and value:
            screenshot_filename = Path(str(value)).name
            return f"📷 {screenshot_filename}"  # Use emoji for PDF since links don't work

        return str(value)

    def _generate_table_rows(self, results_data: List[Dict]) -> str:
        """Generate HTML table rows optimized for PDF"""
        if not results_data:
            return "<tr><td colspan='100%'>No test data available</td></tr>"

        all_keys = self._get_all_unique_keys(results_data)
        rows = []

        for i, entry in enumerate(results_data):
            row = f"<tr class='{'even' if i % 2 == 0 else 'odd'}'>"
            row += f"<td>{i + 1}</td>"

            for key in all_keys:
                value = entry.get(key, 'N/A')
                formatted_value = self._format_cell_value_for_pdf(key, value)

                # Apply CSS classes for styling
                css_class = ''
                if 'command' in key.lower():
                    css_class = 'command'
                elif 'parsed' in key.lower() and 'response' in key.lower():
                    css_class = 'parsed-response'
                elif 'response' in key.lower():
                    css_class = 'response'
                elif any(word in key.lower() for word in ['frequency', 'amplitude', 'peak']):
                    css_class = 'numeric'

                if css_class:
                    row += f"<td class='{css_class}'>{formatted_value}</td>"
                else:
                    row += f"<td>{formatted_value}</td>"

            row += "</tr>"
            rows.append(row)

        return '\n'.join(rows)

    def _generate_screenshot_html(self, screenshots: List[str]) -> str:
        """Generate HTML for screenshots section optimized for PDF"""
        if not screenshots:
            return "<p>No screenshots available</p>"

        html = "<div class='screenshots'>\n"
        for screenshot_path in screenshots:
            screenshot_name = Path(screenshot_path).name
            try:
                # Convert path to absolute path to ensure it exists
                abs_screenshot_path = Path(screenshot_path).resolve()
                if not abs_screenshot_path.exists():
                    # Try relative to current directory
                    abs_screenshot_path = Path.cwd() / screenshot_path

                if abs_screenshot_path.exists():
                    # Embed images as base64 for PDF
                    with open(abs_screenshot_path, 'rb') as f:
                        img_data = base64.b64encode(f.read()).decode('utf-8')

                    # Determine image format from file extension
                    ext = abs_screenshot_path.suffix.lower()
                    if ext in ['.jpg', '.jpeg']:
                        img_format = 'jpeg'
                    elif ext == '.png':
                        img_format = 'png'
                    elif ext == '.gif':
                        img_format = 'gif'
                    elif ext in ['.bmp', '.bitmap']:
                        img_format = 'bmp'
                    else:
                        img_format = 'png'  # Default to png

                    html += f"""
                <div class='screenshot'>
                    <h4>{screenshot_name}</h4>
                    <img src='data:image/{img_format};base64,{img_data}' alt='{screenshot_name}' style='max-width: 100%; height: auto;' />
                </div>
                """
                else:
                    html += f"""
                <div class='screenshot'>
                    <h4>{screenshot_name}</h4>
                    <p>Image file not found: {screenshot_path}</p>
                </div>
                """
            except Exception as e:
                html += f"""
                <div class='screenshot'>
                    <h4>{screenshot_name}</h4>
                    <p>Error loading image: {str(e)}</p>
                </div>
                """
        html += "</div>\n"
        return html

    def _extract_description(self, params: Dict, results_data: List[Dict] = None) -> str:
        """Extract test description from params or results data"""
        description = None

        if params:
            params_data = params.get('params', params)
            description = (params_data.get('test_description') or
                          params_data.get('description') or
                          params.get('test_description') or
                          params.get('description'))

        if not description and results_data:
            for entry in results_data:
                for key in ['docstring', 'test_description', 'description', 'Docstring', 'Test_Description', 'Description']:
                    if key in entry and entry[key]:
                        description = entry[key]
                        break
                if description:
                    break

        return description or ""

    def _create_table_data(self, results_data: List[Dict]) -> List[List]:
        """Create table data for ReportLab Table using Paragraph objects for proper text wrapping"""
        if not results_data:
            return []

        all_keys = self._get_all_unique_keys(results_data)
        if not all_keys:
            return []

        # Get styles for table cells
        styles = getSampleStyleSheet()
        cell_style = ParagraphStyle(
            'CellStyle',
            parent=styles['Normal'],
            fontSize=7,
            leading=9,  # Increased line spacing for better readability
            leftIndent=0,
            rightIndent=0,
            spaceAfter=0,
            spaceBefore=0,
            wordWrap='LTR',
            hyphenationLang='en_US',  # Enable hyphenation
            allowOrphans=0,  # Prevent orphan lines
            allowWidows=0,   # Prevent widow lines
        )

        # Create header row (plain strings for headers)
        headers = ["#"] + [self._format_header_name(key) for key in all_keys]
        table_data = [headers]

        # Create data rows with Paragraph objects for text wrapping
        for i, entry in enumerate(results_data):
            row = [Paragraph(str(i + 1), cell_style)]
            for key in all_keys:
                value = entry.get(key, 'N/A')
                formatted_value = self._format_cell_value_for_reportlab(key, value)
                # Use Paragraph for automatic text wrapping
                row.append(Paragraph(formatted_value, cell_style))
            table_data.append(row)

        return table_data

    def _format_header_name(self, key: str) -> str:
        """Format header name for display"""
        display_name = key.replace('_', ' ').title()

        # Special formatting
        if 'socan' in key.lower():
            display_name = display_name.replace('Socan', 'SOCAN')
        elif 'rf' in key.lower() and 'matrix' in key.lower():
            display_name = display_name.replace('Rf Matrix', 'RF Matrix')
        elif 'xsan' in key.lower():
            display_name = display_name.replace('Xsan', 'XSAN')
        elif 'ghz' in key.lower():
            display_name = display_name.replace('Ghz', 'GHz')
        elif 'dbm' in key.lower():
            display_name = display_name.replace('Dbm', 'dBm')

        # Truncate very long header names
        if len(display_name) > 12:
            display_name = display_name[:9] + "..."

        return display_name

    def _format_cell_value_for_reportlab(self, key: str, value: Any) -> str:
        """Format cell value for ReportLab table with automatic text wrapping via Paragraph"""
        if value is None:
            return 'N/A'

        # Determine max length based on key type - more generous since Paragraph handles wrapping
        if 'command' in key.lower():
            max_length = 200  # Commands can be longer
        elif 'response' in key.lower():
            max_length = 300  # Responses can be longer
        elif 'message' in key.lower() or 'description' in key.lower():
            max_length = 400  # Messages can be longer
        else:
            max_length = 150  # Default length increased

        # Handle different value types
        if isinstance(value, dict):
            content = str(value)
            if len(content) > max_length:
                return content[:max_length-3] + "..."
            return content
        elif isinstance(value, list):
            if len(value) > 10:
                return f"[{len(value)} items]"
            else:
                content = str(value)
                if len(content) > max_length:
                    return content[:max_length-3] + "..."
                return content
        elif isinstance(value, str):
            if len(value) > max_length:
                return value[:max_length-3] + "..."
            return value

        # Special formatting for specific keys
        if 'peak_frequency' in key.lower() and isinstance(value, (int, float)):
            if 'ghz' not in key.lower():
                return f"{value / 1e9:.3f} GHz"
            else:
                return f"{value:.3f} GHz"
        elif 'peak_amplitude' in key.lower() and isinstance(value, (int, float)):
            if 'dbm' not in key.lower():
                return f"{value:.2f} dBm"
            else:
                return f"{value:.2f}"
        elif 'frequency' in key.lower() and isinstance(value, (int, float)):
            if value > 1000000:
                return f"{value / 1e9:.3f} GHz"
            return str(value)
        elif 'screenshot_filepath' in key.lower() and value:
            screenshot_filename = Path(str(value)).name
            return f"📷 {screenshot_filename}"

        return str(value)

    def _generate_status_info(self, status: Dict) -> str:
        """Generate status information HTML"""
        if not status:
            return "<p>No status information available</p>"

        status_class = "passed" if status.get('status') == 'PASSED' else "failed"

        return f"""
        <div class='status-info {status_class}'>
            <h3>Test Status: {status.get('status', 'UNKNOWN')}</h3>
            <p><strong>Duration:</strong> {status.get('duration', 'N/A')}</p>
            <p><strong>Start Time:</strong> {status.get('start_time', 'N/A')}</p>
            <p><strong>End Time:</strong> {status.get('end_time', 'N/A')}</p>
        </div>
        """

    def _generate_params_info(self, params: Dict) -> str:
        """Generate parameters information HTML"""
        if not params:
            return "<p>No parameter information available</p>"

        html = "<div class='params-info'>\n<h3>Test Parameters</h3>\n<ul>\n"
        params_data = params.get('params', params)

        for key, value in params_data.items():
            if key in ['test_description', 'description']:
                continue
            html += f"<li><strong>{key}:</strong> {value}</li>\n"
        html += "</ul>\n</div>\n"

        return html

    def _generate_description_info(self, params: Dict, results_data: List[Dict] = None) -> str:
        """Generate test description HTML"""
        description = None

        if params:
            params_data = params.get('params', params)
            description = (params_data.get('test_description') or
                          params_data.get('description') or
                          params.get('test_description') or
                          params.get('description'))

        if not description and results_data:
            for entry in results_data:
                for key in ['docstring', 'test_description', 'description', 'Docstring', 'Test_Description', 'Description']:
                    if key in entry and entry[key]:
                        description = entry[key]
                        break
                if description:
                    break

        if not description:
            return ""

        formatted_description = description.replace('\n', '<br>')

        html = "<div class='description-info'>\n<h3>Test Description</h3>\n"
        html += f"<p class='test-description'>{formatted_description}</p>\n"
        html += "</div>\n"

        return html