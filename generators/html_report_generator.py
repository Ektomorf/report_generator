#!/usr/bin/env python3
"""
HTML report generator for individual test results.
"""

import base64
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

from models import TestResult
from generators.html_templates import HTMLTemplates


class HTMLReportGenerator:
    """Generator for HTML test reports"""

    def __init__(self):
        self.template = HTMLTemplates.get_main_template()

    def generate_report(self, test_result: TestResult, output_file: Path) -> None:
        """Generate HTML report for a single test"""
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

        with open(output_file, 'w') as f:
            f.write(html_content)

        print(f"Generated report: {output_file}")

    def _get_all_unique_keys(self, results_data: List[Dict]) -> List[str]:
        """Get all unique keys from the results data in a consistent order"""
        if not results_data:
            return []

        all_keys = set()
        for entry in results_data:
            all_keys.update(entry.keys())

        docstring_fields = {'docstring', 'test_description', 'description', 'Docstring', 'Test_Description', 'Description'}
        all_keys = all_keys - docstring_fields

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

        for key in key_order:
            if key in remaining_keys:
                ordered_keys.append(key)
                remaining_keys.remove(key)

        channel_keys = [k for k in remaining_keys if any(k.startswith(base) for base in ['enabled_', 'frequency_', 'gain_'])]
        for key in sorted(channel_keys):
            ordered_keys.append(key)
            remaining_keys.remove(key)

        ordered_keys.extend(sorted(remaining_keys))
        return ordered_keys

    def _generate_table_headers(self, results_data: List[Dict]) -> str:
        """Generate HTML table headers based on available data"""
        if not results_data:
            return "<tr><th>No Data</th></tr>"

        all_keys = self._get_all_unique_keys(results_data)
        headers = ["#"]

        for key in all_keys:
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