#!/usr/bin/env python3
"""
HTML report generator for individual test results.
"""

import base64
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any

from models import TestResult
from generators.html_templates import HTMLTemplates
from config import ColumnConfigManager


class HTMLReportGenerator:
    """Generator for HTML test reports"""

    def __init__(self, column_config: ColumnConfigManager = None):
        self.template = HTMLTemplates.get_main_template()
        self.column_config = column_config or ColumnConfigManager()

    def generate_report(self, test_result: TestResult, output_file: Path) -> None:
        """Generate HTML report for a single test"""
        table_headers = self._generate_table_headers(test_result.results_data)
        table_rows = self._generate_table_rows(test_result.results_data)
        screenshot_html = self._generate_screenshot_html(test_result.screenshots)
        status_info = self._generate_status_info(test_result.status)
        description_info = self._generate_description_info(test_result.params, test_result.results_data)
        params_info = self._generate_params_info(test_result.params, test_result.longrepr)

        column_metadata = self._generate_column_metadata(test_result.results_data)

        html_content = self.template.format(
            test_name=test_result.test_name,
            status_info=status_info,
            description_info=description_info,
            params_info=params_info,
            table_headers=table_headers,
            table_rows=table_rows,
            screenshot_html=screenshot_html,
            column_metadata=column_metadata,
            generation_time=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        )

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)

        print(f"Generated report: {output_file}")

    def _get_all_unique_keys(self, results_data: List[Dict]) -> List[str]:
        """Get all unique keys from the results data using column configuration"""
        if not results_data:
            return []

        # Get all available keys from the data
        all_keys = set()
        data_samples = {}
        for entry in results_data:
            for key, value in entry.items():
                all_keys.add(key)
                # Keep a sample of data for better type inference (use the first non-None, non-empty value)
                if key not in data_samples and value is not None and value != '':
                    data_samples[key] = value

        # Remove docstring fields as they're handled separately
        docstring_fields = {'docstring', 'test_description', 'description', 'Docstring', 'Test_Description', 'Description'}
        all_keys = all_keys - docstring_fields

        # Update column configuration with any new dynamic columns
        self.column_config.update_from_data_keys(all_keys, data_samples)

        # Use column configuration to get ordered, visible keys
        return self.column_config.get_ordered_visible_keys(all_keys)

    def _generate_table_headers(self, results_data: List[Dict]) -> str:
        """Generate HTML table headers based on available data and column configuration"""
        if not results_data:
            return "<tr><th>No Data</th></tr>"

        all_keys = self._get_all_unique_keys(results_data)
        headers = ["#"]

        for key in all_keys:
            column_def = self.column_config.get_column_definition(key)
            if column_def and column_def.display_name:
                display_name = column_def.display_name
            else:
                # Fallback to the old logic for unknown columns
                display_name = key.replace('_', ' ').title()
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

            headers.append(display_name)

        header_row = "<tr>" + "".join(f"<th>{header}</th>" for header in headers) + "</tr>"
        return header_row

    def _format_cell_value(self, key: str, value: Any) -> str:
        """Format cell value based on the key type"""
        if value is None:
            return 'N/A'

        if isinstance(value, dict):
            content = str(value)
            if len(content) > 100:
                return f'<div class="cell-content">{content}</div>'
            return content
        elif isinstance(value, list):
            if len(value) > 10:
                content = f"[{len(value)} items]"
            else:
                content = str(value)
                if len(content) > 100:
                    content = f'<div class="cell-content">{content}</div>'
            return content
        elif isinstance(value, str) and len(value) > 100:
            return f'<div class="cell-content">{value}</div>'

        # Handle timestamp formatting to show UTC
        if 'timestamp' in key.lower() and isinstance(value, str):
            # If the timestamp doesn't already have UTC indicator, add it
            if 'UTC' not in value.upper() and '+' not in value and 'Z' not in value:
                return f"{value} UTC"
            return value
        elif 'peak_frequency' in key.lower() and isinstance(value, (int, float)):
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
            return f"<a href='#{screenshot_filename}' class='screenshot-link'>View</a>"

        return str(value)

    def _generate_table_rows(self, results_data: List[Dict]) -> str:
        """Generate HTML table rows from results data"""
        if not results_data:
            return "<tr><td colspan='100%'>No test data available</td></tr>"

        all_keys = self._get_all_unique_keys(results_data)
        rows = []

        for i, entry in enumerate(results_data):
            row = f"<tr class='{'even' if i % 2 == 0 else 'odd'}'>"
            row += f"<td>{i + 1}</td>"

            for key in all_keys:
                value = entry.get(key, 'N/A')
                formatted_value = self._format_cell_value(key, value)

                css_class = self.column_config.get_column_css_class(key)

                if css_class:
                    row += f"<td class='{css_class}'>{formatted_value}</td>"
                else:
                    row += f"<td>{formatted_value}</td>"

            row += "</tr>"
            rows.append(row)

        return '\n'.join(rows)

    def _generate_screenshot_html(self, screenshots: List[str]) -> str:
        """Generate HTML for screenshots section"""
        if not screenshots:
            return "<p>No screenshots available</p>"

        html = "<div class='screenshots'>\n"
        for screenshot_path in screenshots:
            screenshot_name = Path(screenshot_path).name
            try:
                with open(screenshot_path, 'rb') as f:
                    img_data = base64.b64encode(f.read()).decode('utf-8')
                html += f"""
                <div class='screenshot' id='{screenshot_name}'>
                    <h4>{screenshot_name}</h4>
                    <img src='data:image/png;base64,{img_data}' alt='{screenshot_name}' />
                </div>
                """
            except Exception as e:
                html += f"""
                <div class='screenshot' id='{screenshot_name}'>
                    <h4>{screenshot_name}</h4>
                    <p>Error loading image: {str(e)}</p>
                </div>
                """
        html += "</div>\n"
        return html

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

    def _generate_params_info(self, params: Dict, longrepr: str = "") -> str:
        """Generate parameters information HTML"""
        html = "<div class='params-info'>\n<h3>Test Parameters</h3>\n"

        if not params and not longrepr:
            html += "<p>No parameter information available</p>"
        else:
            html += "<ul>\n"
            if params:
                params_data = params.get('params', params)
                for key, value in params_data.items():
                    if key in ['test_description', 'description']:
                        continue
                    import html as html_escape
                    escaped_key = html_escape.escape(str(key))
                    escaped_value = html_escape.escape(str(value))
                    html += f"<li><strong>{escaped_key}:</strong> {escaped_value}</li>\n"
            html += "</ul>\n"

        # Add longrepr section if available
        if longrepr:
            import html as html_escape
            # First escape HTML, then replace newlines with <br> tags
            escaped_longrepr = html_escape.escape(longrepr)
            formatted_longrepr = escaped_longrepr.replace('\n', '<br>')

            # Apply scrollable class if longrepr is longer than 500 characters
            error_class = "error-message"
            if len(longrepr) > 500:
                error_class += " scrollable"

            html += f"""
            <div class="longrepr-section">
                <h4>Error Details</h4>
                <div class="{error_class}">{formatted_longrepr}</div>
            </div>
            """

        html += "</div>\n"
        return html

    def _generate_description_info(self, params: Dict, results_data: List[Dict] = None) -> str:
        """Generate test description HTML from docstring in params or results data"""
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

    def _generate_column_metadata(self, results_data: List[Dict]) -> str:
        """Generate JavaScript column metadata for the interactive controls"""
        if not results_data:
            return "<script>window.columnMetadata = [];</script>"

        all_keys = self._get_all_unique_keys(results_data)
        metadata = []

        for i, key in enumerate(all_keys):
            column_def = self.column_config.get_column_definition(key)
            if column_def and column_def.display_name:
                display_name = column_def.display_name
                description = column_def.description or ""
                column_type = column_def.column_type.value if column_def.column_type else "text"
            else:
                # Fallback to the old logic for unknown columns
                display_name = key.replace('_', ' ').title()
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
                description = ""
                column_type = "text"

            metadata.append({
                'key': key,
                'displayName': display_name,
                'index': i + 1,  # +1 for row number column
                'description': description,
                'type': column_type,
                'visible': self.column_config.is_column_visible(key)
            })

        metadata_json = str(metadata).replace("'", '"').replace('True', 'true').replace('False', 'false')

        return f"""
        <script>
            window.columnMetadata = {metadata_json};
        </script>
        """