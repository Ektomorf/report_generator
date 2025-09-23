#!/usr/bin/env python3
"""
Test Report Generator for RS ATS Test Results
Generates HTML reports from test result JSON files.
"""

import json
import os
import argparse
import shutil
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
import base64
import re


class TestResultParser:
    """Parser for test result files"""
    
    def __init__(self, test_folder: Path):
        self.test_folder = test_folder
        self.test_name = test_folder.name
        
    def parse_results(self) -> Dict[str, Any]:
        """Parse all result files for a test"""
        results = {
            'test_name': self.test_name,
            'test_folder': str(self.test_folder),
            'results_data': [],
            'params': {},
            'status': {},
            'screenshots': []
        }
        
        # Parse results JSON
        results_file = self._find_file_with_suffix('_results.json')
        if results_file:
            try:
                with open(results_file, 'r') as f:
                    results['results_data'] = json.load(f)
            except json.JSONDecodeError as e:
                print(f"Warning: Invalid JSON in {results_file.name}: {str(e)}")
                results['results_data'] = []
        
        # Parse params JSON  
        params_file = self._find_file_with_suffix('_params.json')
        if params_file:
            try:
                with open(params_file, 'r') as f:
                    results['params'] = json.load(f)
            except json.JSONDecodeError as e:
                print(f"Warning: Invalid JSON in {params_file.name}: {str(e)}")
                results['params'] = {}
                
        # Parse status JSON
        status_file = self._find_file_with_suffix('_status.json')
        if status_file:
            try:
                with open(status_file, 'r') as f:
                    results['status'] = json.load(f)
            except json.JSONDecodeError as e:
                print(f"Warning: Invalid JSON in {status_file.name}: {str(e)}")
                results['status'] = {}
                
        # Find screenshots
        for file in self.test_folder.glob('*.png'):
            results['screenshots'].append(str(file))
            
        return results
    
    def _find_file_with_suffix(self, suffix: str) -> Optional[Path]:
        """Find file with specific suffix in test folder"""
        for file in self.test_folder.glob(f'*{suffix}'):
            return file
        return None


class SetupReportParser:
    """Parser for setup report.json files"""
    
    def __init__(self, setup_folder: Path):
        self.setup_folder = setup_folder
        self.setup_name = setup_folder.name
        
    def parse_report(self) -> Dict[str, Any]:
        """Parse report.json and collect test logs"""
        report_data = {
            'setup_name': self.setup_name,
            'setup_folder': str(self.setup_folder),
            'test_summary': {},
            'tests': [],
            'logs': []
        }
        
        # Parse report.json
        report_file = self.setup_folder / 'report.json'
        if report_file.exists():
            try:
                with open(report_file, 'r') as f:
                    report_json = json.load(f)
                    
                # Extract summary information
                report_data['test_summary'] = {
                    'total': report_json.get('summary', {}).get('total', 0),
                    'passed': report_json.get('summary', {}).get('passed', 0),
                    'failed': report_json.get('summary', {}).get('failed', 0),
                    'error': report_json.get('summary', {}).get('error', 0),
                    'duration': report_json.get('duration', 0),
                    'created': report_json.get('created', 0)
                }
                
                # Extract test results
                for test in report_json.get('tests', []):
                    test_info = {
                        'name': test.get('nodeid', '').replace('::', ''),
                        'outcome': test.get('outcome', 'unknown'),
                        'duration': 0,
                        'error_message': ''
                    }
                    
                    # Calculate total test duration
                    if 'setup' in test:
                        test_info['duration'] += test['setup'].get('duration', 0)
                    if 'call' in test:
                        test_info['duration'] += test['call'].get('duration', 0)
                    if 'teardown' in test:
                        test_info['duration'] += test['teardown'].get('duration', 0)
                    
                    # Get error message if test failed
                    if test.get('outcome') in ['failed', 'error']:
                        if 'setup' in test and test['setup'].get('outcome') == 'failed':
                            crash = test['setup'].get('crash', {})
                            test_info['error_message'] = crash.get('message', test['setup'].get('longrepr', ''))
                        elif 'call' in test and test['call'].get('outcome') == 'failed':
                            crash = test['call'].get('crash', {})
                            test_info['error_message'] = crash.get('message', test['call'].get('longrepr', ''))
                    
                    report_data['tests'].append(test_info)
                    
            except json.JSONDecodeError as e:
                print(f"Warning: Invalid JSON in {report_file}: {str(e)}")
                
        # Collect logs from test subdirectories
        report_data['logs'] = self._collect_test_logs()
        
        return report_data
        
    def _collect_test_logs(self) -> List[Dict[str, Any]]:
        """Collect logs from all test subdirectories"""
        logs = []
        
        # Find all test subdirectories
        for test_dir in self.setup_folder.iterdir():
            if test_dir.is_dir() and test_dir.name.startswith('test_'):
                log_file = None
                # Look for .log files in the test directory
                for file in test_dir.glob('*.log'):
                    log_file = file
                    break
                    
                if log_file and log_file.exists():
                    try:
                        with open(log_file, 'r') as f:
                            content = f.read().strip()
                            if content:  # Only process non-empty logs
                                # Parse log lines with timestamp and level
                                for line in content.split('\n'):
                                    line = line.strip()
                                    if line:
                                        log_entry = self._parse_log_line(line)
                                        if log_entry:
                                            log_entry['test_name'] = test_dir.name
                                            logs.append(log_entry)
                    except Exception as e:
                        print(f"Warning: Could not read log file {log_file}: {str(e)}")
                        
        return sorted(logs, key=lambda x: x.get('timestamp', ''))
        
    def _parse_log_line(self, line: str) -> Optional[Dict[str, Any]]:
        """Parse a single log line to extract timestamp, level, and message"""
        # Expected format: HH:MM:SS - LEVEL - message
        log_pattern = r'^(\d{2}:\d{2}:\d{2})\s*-\s*(INFO|DEBUG|ERROR|WARNING|WARN)\s*-\s*(.+)$'
        match = re.match(log_pattern, line)
        
        if match:
            timestamp, level, message = match.groups()
            return {
                'timestamp': timestamp,
                'level': level.upper(),
                'message': message.strip()
            }
        
        return None


class HTMLReportGenerator:
    """Generator for HTML test reports"""
    
    def __init__(self):
        self.html_template = self._create_html_template()
    
    def generate_report(self, test_results: Dict[str, Any], output_file: Path) -> None:
        """Generate HTML report for a single test"""
        
        # Process results data for table
        table_headers = self._generate_table_headers(test_results['results_data'])
        table_rows = self._generate_table_rows(test_results['results_data'])
        
        # Process screenshots
        screenshot_html = self._generate_screenshot_html(test_results['screenshots'])
        
        # Generate status info
        status_info = self._generate_status_info(test_results['status'])
        
        # Generate test description info
        description_info = self._generate_description_info(test_results['params'], test_results['results_data'])
        
        # Generate params info
        params_info = self._generate_params_info(test_results['params'])
        
        # Fill in the template
        html_content = self.html_template.format(
            test_name=test_results['test_name'],
            status_info=status_info,
            description_info=description_info,
            params_info=params_info,
            table_headers=table_headers,
            table_rows=table_rows,
            screenshot_html=screenshot_html,
            generation_time=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        )
        
        # Write HTML file
        with open(output_file, 'w') as f:
            f.write(html_content)
            
        print(f"Generated report: {output_file}")
    
    def _get_all_unique_keys(self, results_data: List[Dict]) -> List[str]:
        """Get all unique keys from the results data in a consistent order"""
        if not results_data:
            return []
        
        # Collect all unique keys
        all_keys = set()
        for entry in results_data:
            all_keys.update(entry.keys())
        
        # Remove docstring-related fields as they should be in the description section, not table columns
        docstring_fields = {'docstring', 'test_description', 'description', 'Docstring', 'Test_Description', 'Description'}
        all_keys = all_keys - docstring_fields
        
        # Define a preferred order for common keys
        key_order = [
            'Timestamp',
            # Channel-related keys (dynamic - can be enabled_0, enabled_1, etc.)
            'channel', 'frequency', 'enabled', 'gain',  # Base names
            'spectrum_frequencies',
            'spectrum_amplitudes',
            'peak_frequency',
            'peak_amplitude',
            'screenshot_filepath',
            # SOCAN-related keys
            'socan_command_method',
            'socan_command_args', 
            'socan_command',
            'parsed_socan_response',
            'raw_socan_response',
            # RF Matrix-related keys
            'rf_matrix_command_method',
            'rf_matrix_command_args',
            'rf_matrix_command', 
            'parsed_rf_matrix_response',
            'raw_rf_matrix_response',
            # Keysight-related keys
            'keysight_xsan_command_method',
            'keysight_xsan_command_args',
            'keysight_xsan_command',
            # Measurement data
            'frequencies',
            'amplitudes',
        ]
        
        # Sort keys: preferred order first, then alphabetically for others
        ordered_keys = []
        remaining_keys = set(all_keys)
        
        # Add keys in preferred order if they exist
        for key in key_order:
            if key in remaining_keys:
                ordered_keys.append(key)
                remaining_keys.remove(key)
        
        # Add channel-specific keys (enabled_0, frequency_1, etc.) in order
        channel_keys = [k for k in remaining_keys if any(k.startswith(base) for base in ['enabled_', 'frequency_', 'gain_'])]
        for key in sorted(channel_keys):
            ordered_keys.append(key)
            remaining_keys.remove(key)
        
        # Add any remaining keys alphabetically
        ordered_keys.extend(sorted(remaining_keys))
        
        return ordered_keys

    def _generate_table_headers(self, results_data: List[Dict]) -> str:
        """Generate HTML table headers based on available data"""
        if not results_data:
            return "<tr><th>No Data</th></tr>"
        
        all_keys = self._get_all_unique_keys(results_data)
        
        # Generate headers
        headers = ["#"]  # Row number column
        
        for key in all_keys:
            # Format key names for display
            display_name = key.replace('_', ' ').title()
            # Special formatting for some keys
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
        
        # Handle different value types
        if isinstance(value, dict):
            content = str(value)
            # Wrap large dict content in scrollable div
            if len(content) > 100:
                return f'<div class="cell-content">{content}</div>'
            return content
        elif isinstance(value, list):
            # For lists, show count or full content if small
            if len(value) > 10:
                content = f"[{len(value)} items]"
            else:
                content = str(value)
                if len(content) > 100:
                    content = f'<div class="cell-content">{content}</div>'
            return content
        elif isinstance(value, str) and len(value) > 100:
            # Wrap long strings in scrollable div
            return f'<div class="cell-content">{value}</div>'
        
        # Special formatting for specific keys
        if 'peak_frequency' in key.lower() and isinstance(value, (int, float)):
            if 'ghz' not in key.lower():  # Convert Hz to GHz if not already in GHz
                return f"{value / 1e9:.3f} GHz"
            else:
                return f"{value:.3f} GHz"
        elif 'peak_amplitude' in key.lower() and isinstance(value, (int, float)):
            if 'dbm' not in key.lower():  # Add dBm unit if not already present
                return f"{value:.2f} dBm"
            else:
                return f"{value:.2f}"
        elif 'frequency' in key.lower() and isinstance(value, (int, float)):
            if value > 1000000:  # Likely in Hz, convert to more readable format
                return f"{value / 1e9:.3f} GHz"
            return str(value)
        elif 'screenshot_filepath' in key.lower() and value:
            # For screenshot filepaths, create a link
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
            
            # Row number
            row += f"<td>{i + 1}</td>"
            
            # Add data for each column
            for key in all_keys:
                value = entry.get(key, 'N/A')
                formatted_value = self._format_cell_value(key, value)
                
                # Apply appropriate CSS class based on content type
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
                # Encode image as base64 for embedding
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
        
        # Handle nested params structure
        params_data = params.get('params', params)
        
        for key, value in params_data.items():
            # Skip description fields as they're handled separately
            if key in ['test_description', 'description']:
                continue
            html += f"<li><strong>{key}:</strong> {value}</li>\n"
        html += "</ul>\n</div>\n"
        
        return html
    
    def _generate_description_info(self, params: Dict, results_data: List[Dict] = None) -> str:
        """Generate test description HTML from docstring in params or results data"""
        description = None
        
        # First, try to get description from params
        if params:
            # Handle nested params structure
            params_data = params.get('params', params)
            
            # Look for description in various possible keys
            description = (params_data.get('test_description') or 
                          params_data.get('description') or 
                          params.get('test_description') or 
                          params.get('description'))
        
        # If not found in params, try to get from results data
        if not description and results_data:
            for entry in results_data:
                # Look for docstring in results data (case-insensitive)
                for key in ['docstring', 'test_description', 'description', 'Docstring', 'Test_Description', 'Description']:
                    if key in entry and entry[key]:
                        description = entry[key]
                        break
                if description:
                    break
        
        if not description:
            return ""
        
        # Convert newlines to HTML line breaks for proper formatting
        formatted_description = description.replace('\n', '<br>')
        
        html = "<div class='description-info'>\n<h3>Test Description</h3>\n"
        html += f"<p class='test-description'>{formatted_description}</p>\n"
        html += "</div>\n"
        
        return html
    
    def _create_html_template(self) -> str:
        """Create the HTML template"""
        return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Test Report: {test_name}</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
            line-height: 1.6;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        
        h1 {{
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
            margin-bottom: 30px;
        }}
        
        h2 {{
            color: #34495e;
            margin-top: 40px;
            margin-bottom: 20px;
        }}
        
        .status-info {{
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 20px;
        }}
        
        .status-info.passed {{
            background-color: #d4edda;
            border: 1px solid #c3e6cb;
            color: #155724;
        }}
        
        .status-info.failed {{
            background-color: #f8d7da;
            border: 1px solid #f5c6cb;
            color: #721c24;
        }}
        
        .params-info {{
            background-color: #e9ecef;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 20px;
        }}
        
        .description-info {{
            background-color: #f8f9fa;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 20px;
            border-left: 4px solid #007bff;
        }}
        
        .test-description {{
            margin: 0;
            font-style: italic;
            line-height: 1.6;
            color: #495057;
        }}
        
        .table-container {{
            overflow-x: auto;
            margin: 20px 0;
            border: 1px solid #ddd;
            border-radius: 5px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        
        table {{
            width: 100%;
            min-width: 1500px;  /* Ensure minimum width for many columns */
            border-collapse: collapse;
            margin: 0;
            font-size: 13px;
        }}
        
        th, td {{
            padding: 8px 6px;
            text-align: left;
            border-bottom: 1px solid #ddd;
            border-right: 1px solid #eee;
            vertical-align: top;
            word-wrap: break-word;
            max-width: 200px;  /* Prevent columns from becoming too wide */
            max-height: 120px;  /* Limit cell height */
            overflow: auto;     /* Add scrolling for overflow content */
            position: relative;
        }}
        
        /* Scrollable content wrapper for cells with large data */
        .cell-content {{
            max-height: 100px;
            overflow-y: auto;
            overflow-x: hidden;
            word-wrap: break-word;
            white-space: pre-wrap;
        }}
        
        .cell-content::-webkit-scrollbar {{
            width: 6px;
        }}
        
        .cell-content::-webkit-scrollbar-track {{
            background: #f1f1f1;
            border-radius: 3px;
        }}
        
        .cell-content::-webkit-scrollbar-thumb {{
            background: #888;
            border-radius: 3px;
        }}
        
        .cell-content::-webkit-scrollbar-thumb:hover {{
            background: #555;
        }}
        
        th:last-child, td:last-child {{
            border-right: none;
        }}
        
        th {{
            background-color: #3498db;
            color: white;
            font-weight: bold;
            position: sticky;
            top: 0;
            font-size: 12px;
            white-space: nowrap;
        }}
        
        /* Specific column widths for better layout */
        th:first-child, td:first-child {{
            width: 40px;
            text-align: center;
        }}
        
        .command {{
            font-family: 'Courier New', monospace;
            font-size: 11px;
            max-width: 180px;
            word-wrap: break-word;
        }}
        
        .response {{
            font-family: 'Courier New', monospace;
            font-size: 10px;
            max-width: 200px;
            word-wrap: break-word;
        }}
        
        /* Special styling for parsed responses */
        .parsed-response {{
            font-family: 'Courier New', monospace;
            font-size: 11px;
            max-width: 300px;
            word-wrap: break-word;
        }}
        
        /* Override cell-content styles for specific cell types */
        .command .cell-content,
        .response .cell-content,
        .parsed-response .cell-content {{
            font-family: inherit;
            font-size: inherit;
        }}
        
        .numeric {{
            text-align: right;
            font-family: 'Courier New', monospace;
            white-space: nowrap;
        }}
        
        tr:nth-child(even) {{
            background-color: #f8f9fa;
        }}
        
        tr:hover {{
            background-color: #e3f2fd;
        }}
        
        .screenshot-link {{
            color: #3498db;
            text-decoration: none;
            font-weight: bold;
        }}
        
        .screenshot-link:hover {{
            text-decoration: underline;
        }}
        
        .screenshots {{
            margin-top: 40px;
        }}
        
        .screenshot {{
            margin-bottom: 30px;
            text-align: center;
        }}
        
        .screenshot img {{
            max-width: 100%;
            border: 2px solid #ddd;
            border-radius: 5px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        
        .footer {{
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            color: #666;
            font-size: 12px;
            text-align: center;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Test Report: {test_name}</h1>
        
        {status_info}
        
        {description_info}
        
        {params_info}
        
        <h2>Test Results</h2>
        <div class="table-container">
            <table>
                <thead>
                    {table_headers}
                </thead>
                <tbody>
                    {table_rows}
                </tbody>
            </table>
        </div>
        
        <h2>Screenshots</h2>
        {screenshot_html}
        
        <div class="footer">
            <p>Report generated on {generation_time}</p>
        </div>
    </div>
</body>
</html>"""


def main():
    parser = argparse.ArgumentParser(
        description='Generate HTML reports from RS ATS test results',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate reports for a specific test results folder
  python test_report_generator.py /path/to/output/setups_180925_091733
  
  # Generate reports with custom output directory
  python test_report_generator.py /path/to/output/setups_180925_091733 --output-dir ./reports
        """
    )
    
    parser.add_argument(
        'input_dir',
        type=Path,
        nargs='?',
        default=Path('output'),
        help='Input directory containing test result folders (default: output)'
    )
    
    parser.add_argument(
        '--output-dir', '-o',
        type=Path,
        default='processed_results',
        required=False,
        help='Output directory for HTML reports (default: same as input)'
    )
    
    args = parser.parse_args()
    
    input_dir = args.input_dir.resolve()
    if not input_dir.exists():
        print(f"Error: Input directory {input_dir} does not exist")
        return 1
    
    # Set output directory
    if args.output_dir:
        output_dir = args.output_dir.resolve()
        output_dir.mkdir(parents=True, exist_ok=True)
    else:
        output_dir = input_dir
    
    # Recursively find all subfolders containing *_results.json files OR report.json files
    valid_folders = []
    setup_folders = []
    
    for root, dirs, files in os.walk(input_dir):
        folder_path = Path(root)
        # Look for test result folders (existing logic)
        if any(f.endswith('_results.json') for f in files):
            valid_folders.append(folder_path)
        # Look for setup report folders (new logic)
        elif 'report.json' in files:
            setup_folders.append(folder_path)

    if not valid_folders and not setup_folders:
        print(f"No result folders found in {input_dir}")
        return 1

    print(f"Found {len(valid_folders)} result folders and {len(setup_folders)} setup folders")

    # Generate reports for each result folder
    report_generator = HTMLReportGenerator()
    generated_reports = []

    # Process regular test result folders
    for result_folder in sorted(valid_folders):
        print(f"Processing {result_folder.name}...")

        try:
            # Parse test results
            parser = TestResultParser(result_folder)
            test_results = parser.parse_results()

            # Create output directory for this test run (parent folder name)
            test_run_name = result_folder.parent.name if result_folder.parent != input_dir else result_folder.name
            test_run_output_dir = output_dir / test_run_name
            test_run_output_dir.mkdir(parents=True, exist_ok=True)

            # Generate HTML report in the test run folder
            output_file = test_run_output_dir / f"{result_folder.name}_report.html"
            report_generator.generate_report(test_results, output_file)
            generated_reports.append(output_file)

        except Exception as e:
            print(f"Error processing {result_folder.name}: {str(e)}")

    # Process setup folders with report.json
    setup_report_data = []
    for setup_folder in sorted(setup_folders):
        print(f"Processing setup {setup_folder.name}...")
        
        try:
            parser = SetupReportParser(setup_folder)
            setup_data = parser.parse_report()
            setup_report_data.append(setup_data)
        except Exception as e:
            print(f"Error processing setup {setup_folder.name}: {str(e)}")

    # Generate index page
    index_file = output_dir / "index.html"
    _generate_index_page(generated_reports, index_file, input_dir.name, setup_report_data)

    print(f"\nGenerated {len(generated_reports)} test reports in {output_dir}")
    print(f"Open {index_file} to view all reports")

    return 0


def _generate_index_page(report_files: List[Path], index_file: Path, test_session: str, setup_data: List[Dict[str, Any]] = None):
    """Generate an index page with links to all reports and setup test results"""
    
    if setup_data is None:
        setup_data = []
    
    # Group reports by test run (parent folder)
    test_runs = {}
    for report_file in report_files:
        test_run = report_file.parent.name
        if test_run not in test_runs:
            test_runs[test_run] = []
        test_runs[test_run].append(report_file)
    
    # Create comprehensive test results table data
    all_test_results = []
    all_logs = []
    
    for setup in setup_data:
        setup_name = setup['setup_name']
        setup_summary = setup['test_summary']
        
        # Add overall setup result
        setup_result = {
            'setup_name': setup_name,
            'test_name': 'Overall',
            'outcome': 'passed' if setup_summary.get('error', 0) == 0 and setup_summary.get('failed', 0) == 0 else 'failed',
            'duration': f"{setup_summary.get('duration', 0):.2f}s",
            'passed_tests': setup_summary.get('passed', 0),
            'failed_tests': setup_summary.get('failed', 0) + setup_summary.get('error', 0),
            'total_tests': setup_summary.get('total', 0),
            'created': setup_summary.get('created', 0)
        }
        all_test_results.append(setup_result)
        
        # Add individual test results
        for test in setup['tests']:
            test_result = {
                'setup_name': setup_name,
                'test_name': test['name'],
                'outcome': test['outcome'],
                'duration': f"{test['duration']:.2f}s",
                'error_message': test.get('error_message', ''),
                'created': setup_summary.get('created', 0)
            }
            all_test_results.append(test_result)
        
        # Add logs
        for log in setup['logs']:
            log['setup_name'] = setup_name
            all_logs.append(log)
    
    # Sort results by creation time and setup name
    all_test_results.sort(key=lambda x: (x['created'], x['setup_name'], x['test_name']))
    all_logs.sort(key=lambda x: (x.get('setup_name', ''), x.get('timestamp', '')))
    
    index_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Test Reports Index - {test_session}</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
            font-size: 14px;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1, h2 {{
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }}
        .section {{
            margin: 30px 0;
        }}
        .test-run {{
            margin: 30px 0;
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            overflow: hidden;
        }}
        .test-run-header {{
            background-color: #3498db;
            color: white;
            padding: 15px;
            font-weight: bold;
            font-size: 18px;
        }}
        .report-list {{
            list-style: none;
            padding: 0;
            margin: 0;
        }}
        .report-list li {{
            margin: 0;
            padding: 15px;
            background-color: #f8f9fa;
            border-bottom: 1px solid #e0e0e0;
        }}
        .report-list li:last-child {{
            border-bottom: none;
        }}
        .report-list a {{
            color: #2c3e50;
            text-decoration: none;
            font-weight: bold;
        }}
        .report-list a:hover {{
            color: #3498db;
        }}
        .results-table, .logs-table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            font-size: 12px;
        }}
        .results-table th, .results-table td,
        .logs-table th, .logs-table td {{
            padding: 8px;
            text-align: left;
            border: 1px solid #ddd;
        }}
        .results-table th, .logs-table th {{
            background-color: #3498db;
            color: white;
            font-weight: bold;
            position: sticky;
            top: 0;
        }}
        .results-table tr:nth-child(even), .logs-table tr:nth-child(even) {{
            background-color: #f2f2f2;
        }}
        .passed {{
            background-color: #d4edda !important;
            color: #155724;
        }}
        .failed, .error {{
            background-color: #f8d7da !important;
            color: #721c24;
        }}
        .log-info {{
            color: #0c5460;
        }}
        .log-debug {{
            color: #6c757d;
        }}
        .log-error {{
            color: #721c24;
            font-weight: bold;
        }}
        .log-warning {{
            color: #856404;
        }}
        .error-message {{
            font-family: monospace;
            font-size: 10px;
            max-width: 300px;
            word-wrap: break-word;
            color: #721c24;
        }}
        .footer {{
            margin-top: 30px;
            text-align: center;
            color: #666;
            font-size: 12px;
        }}
        .tabs {{
            display: flex;
            border-bottom: 1px solid #ddd;
            margin-bottom: 20px;
        }}
        .tab {{
            padding: 10px 20px;
            cursor: pointer;
            border: 1px solid #ddd;
            border-bottom: none;
            background-color: #f5f5f5;
            margin-right: 5px;
        }}
        .tab.active {{
            background-color: white;
            border-bottom: 1px solid white;
            margin-bottom: -1px;
        }}
        .tab-content {{
            display: none;
        }}
        .tab-content.active {{
            display: block;
        }}
    </style>
    <script>
        function showTab(tabName) {{
            // Hide all tab contents
            const contents = document.getElementsByClassName('tab-content');
            for (let content of contents) {{
                content.classList.remove('active');
            }}
            
            // Remove active class from all tabs
            const tabs = document.getElementsByClassName('tab');
            for (let tab of tabs) {{
                tab.classList.remove('active');
            }}
            
            // Show selected tab content and mark tab as active
            document.getElementById(tabName).classList.add('active');
            event.target.classList.add('active');
        }}
        
        function formatTimestamp(timestamp) {{
            const date = new Date(timestamp * 1000);
            return date.toLocaleString();
        }}
        
        window.onload = function() {{
            // Show first tab by default
            document.getElementById('detailed-reports').classList.add('active');
            document.getElementsByClassName('tab')[0].classList.add('active');
        }}
    </script>
</head>
<body>
    <div class="container">
        <h1>Test Reports Index</h1>
        <h2>Test Session: {test_session}</h2>
        
        <div class="tabs">
            <div class="tab" onclick="showTab('detailed-reports')">Detailed Reports</div>
            <div class="tab" onclick="showTab('test-logs')">Test Logs</div>
        </div>
        
        <!-- Test Logs Tab -->
        <div id="test-logs" class="tab-content">
            <h3>Test Execution Logs</h3>
"""
    
    if all_logs:
        index_html += """
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
            index_html += f"""
                    <tr>
                        <td>{log.get('setup_name', 'Unknown')}</td>
                        <td>{log.get('test_name', 'Unknown')}</td>
                        <td>{log.get('timestamp', 'N/A')}</td>
                        <td class="{level_class}">{log.get('level', 'INFO')}</td>
                        <td>{log.get('message', '')}</td>
                    </tr>
"""
        index_html += """
                </tbody>
            </table>
"""
    else:
        index_html += "<p>No logs available.</p>"
    
    index_html += """
        </div>
        
        <!-- Detailed Reports Tab -->
        <div id="detailed-reports" class="tab-content">
            <h3>Test Results and Detailed Reports</h3>
"""
    
    # Group setup data by setup name for easy lookup
    setup_results_map = {}
    for setup in setup_data:
        setup_results_map[setup['setup_name']] = setup
    
    # Create sections for each setup with test results and links to detailed reports
    processed_setups = set()
    
    # First, show setups that have both results and detailed reports
    for test_run_name in sorted(test_runs.keys()):
        if test_run_name in setup_results_map:
            setup = setup_results_map[test_run_name]
            reports = test_runs[test_run_name]
            processed_setups.add(test_run_name)
            
            # Get setup summary
            setup_summary = setup['test_summary']
            created_date = datetime.fromtimestamp(setup_summary.get('created', 0), tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC') if setup_summary.get('created') else 'Unknown'
            
            index_html += f"""
            <div class="test-run">
                <div class="test-run-header">
                    {test_run_name} 
                    <span style="float: right; font-size: 14px;">
                        {setup_summary.get('passed', 0)} Passed | {setup_summary.get('failed', 0) + setup_summary.get('error', 0)} Failed | 
                        Duration: {setup_summary.get('duration', 0):.1f}s | {created_date}
                    </span>
                </div>
                
                <!-- Test Results Table -->
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
            for test in setup['tests']:
                outcome_class = test['outcome'] if test['outcome'] in ['passed', 'failed', 'error'] else ''
                error_msg = test.get('error_message', '')[:80] + ('...' if len(test.get('error_message', '')) > 80 else '')
                
                index_html += f"""
                            <tr class="{outcome_class}">
                                <td>{test['name']}</td>
                                <td>{test['outcome'].upper()}</td>
                                <td>{test['duration']:.2f}s</td>
                                <td class="error-message">{error_msg}</td>
                            </tr>
"""
            index_html += """
                        </tbody>
                    </table>
                    
                    <h4>Detailed Reports</h4>
                    <ul class="report-list">
"""
            for report_file in sorted(reports):
                test_name = report_file.stem.replace('_report', '')
                relative_path = f"{test_run_name}/{report_file.name}"
                index_html += f'                        <li><a href="{relative_path}">{test_name}</a></li>\n'
            
            index_html += """                    </ul>
                </div>
            </div>
"""
    
    # Then, show setups that only have test results (no detailed reports)
    for setup in setup_data:
        setup_name = setup['setup_name']
        if setup_name not in processed_setups:
            setup_summary = setup['test_summary']
            created_date = datetime.fromtimestamp(setup_summary.get('created', 0), tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC') if setup_summary.get('created') else 'Unknown'
            
            index_html += f"""
            <div class="test-run">
                <div class="test-run-header">
                    {setup_name} 
                    <span style="float: right; font-size: 14px;">
                        {setup_summary.get('passed', 0)} Passed | {setup_summary.get('failed', 0) + setup_summary.get('error', 0)} Failed | 
                        Duration: {setup_summary.get('duration', 0):.1f}s | {created_date}
                    </span>
                </div>
                
                <!-- Test Results Table -->
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
            for test in setup['tests']:
                outcome_class = test['outcome'] if test['outcome'] in ['passed', 'failed', 'error'] else ''
                error_msg = test.get('error_message', '')[:80] + ('...' if len(test.get('error_message', '')) > 80 else '')
                
                index_html += f"""
                            <tr class="{outcome_class}">
                                <td>{test['name']}</td>
                                <td>{test['outcome'].upper()}</td>
                                <td>{test['duration']:.2f}s</td>
                                <td class="error-message">{error_msg}</td>
                            </tr>
"""
            index_html += """
                        </tbody>
                    </table>
                    <p><em>No detailed reports available for this setup.</em></p>
                </div>
            </div>
"""
    
    # Finally, show test runs that only have detailed reports (no setup results)
    for test_run_name in sorted(test_runs.keys()):
        if test_run_name not in setup_results_map:
            reports = test_runs[test_run_name]
            index_html += f"""
            <div class="test-run">
                <div class="test-run-header">{test_run_name}</div>
                <div style="padding: 15px;">
                    <h4>Detailed Reports</h4>
                    <ul class="report-list">
"""
            for report_file in sorted(reports):
                test_name = report_file.stem.replace('_report', '')
                relative_path = f"{test_run_name}/{report_file.name}"
                index_html += f'                        <li><a href="{relative_path}">{test_name}</a></li>\n'
            
            index_html += """                    </ul>
                    <p><em>No test results summary available for this setup.</em></p>
                </div>
            </div>
"""
        
    index_html += """
        </div>
"""
    
    total_reports = len(report_files)
    total_setups = len(setup_data)
    total_tests = sum(result.get('total_tests', 0) for result in all_test_results if result.get('total_tests'))
    total_passed = sum(result.get('passed_tests', 0) for result in all_test_results if result.get('passed_tests'))
    total_failed = sum(result.get('failed_tests', 0) for result in all_test_results if result.get('failed_tests'))
    
    index_html += f"""        
        <div class="footer">
            <p>Generated on {datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")}</p>
            <p>{total_setups} setup runs • {total_tests} tests • {total_passed} passed • {total_failed} failed • {len(all_logs)} log entries • {total_reports} detailed reports</p>
        </div>
    </div>
</body>
</html>"""
    
    with open(index_file, 'w') as f:
        f.write(index_html)


if __name__ == '__main__':
    exit(main())