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
from datetime import datetime
from typing import Dict, List, Any, Optional
import base64


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
        
        # Generate params info
        params_info = self._generate_params_info(test_results['params'])
        
        # Fill in the template
        html_content = self.html_template.format(
            test_name=test_results['test_name'],
            status_info=status_info,
            params_info=params_info,
            table_headers=table_headers,
            table_rows=table_rows,
            screenshot_html=screenshot_html,
            generation_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
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
            return str(value)
        elif isinstance(value, list):
            # For lists, show count or truncated content
            if len(value) > 10:
                return f"[{len(value)} items]"
            elif len(str(value)) > 100:
                return f"{str(value)[:100]}..."
            return str(value)
        elif isinstance(value, str) and len(value) > 150:
            # Truncate long strings
            return f"{value[:150]}..."
        
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
            html += f"<li><strong>{key}:</strong> {value}</li>\n"
        html += "</ul>\n</div>\n"
        
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
            white-space: pre-wrap;
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
    
    # Recursively find all subfolders containing *_results.json files
    valid_folders = []
    for root, dirs, files in os.walk(input_dir):
        folder_path = Path(root)
        if any(f.endswith('_results.json') for f in files):
            valid_folders.append(folder_path)

    if not valid_folders:
        print(f"No result folders found in {input_dir}")
        return 1

    print(f"Found {len(valid_folders)} result folders")

    # Generate reports for each result folder
    report_generator = HTMLReportGenerator()
    generated_reports = []

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

    # Generate index page
    index_file = output_dir / "index.html"
    _generate_index_page(generated_reports, index_file, input_dir.name)

    print(f"\nGenerated {len(generated_reports)} test reports in {output_dir}")
    print(f"Open {index_file} to view all reports")

    return 0


def _generate_index_page(report_files: List[Path], index_file: Path, test_session: str):
    """Generate an index page with links to all reports"""
    
    # Group reports by test run (parent folder)
    test_runs = {}
    for report_file in report_files:
        test_run = report_file.parent.name
        if test_run not in test_runs:
            test_runs[test_run] = []
        test_runs[test_run].append(report_file)
    
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
        }}
        .container {{
            max-width: 1000px;
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
        .footer {{
            margin-top: 30px;
            text-align: center;
            color: #666;
            font-size: 12px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Test Reports Index</h1>
        <h2>Test Session: {test_session}</h2>
        
"""
    
    for test_run_name in sorted(test_runs.keys()):
        reports = test_runs[test_run_name]
        index_html += f"""
        <div class="test-run">
            <div class="test-run-header">{test_run_name}</div>
            <ul class="report-list">
"""
        for report_file in sorted(reports):
            test_name = report_file.stem.replace('_report', '')
            relative_path = f"{test_run_name}/{report_file.name}"
            index_html += f'                <li><a href="{relative_path}">{test_name}</a></li>\n'
        
        index_html += """            </ul>
        </div>
"""
    
    index_html += f"""        
        <div class="footer">
            <p>Generated on {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
            <p>{len(report_files)} test reports available across {len(test_runs)} test runs</p>
        </div>
    </div>
</body>
</html>"""
    
    with open(index_file, 'w') as f:
        f.write(index_html)


if __name__ == '__main__':
    exit(main())