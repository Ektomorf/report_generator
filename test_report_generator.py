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
            with open(results_file, 'r') as f:
                results['results_data'] = json.load(f)
        
        # Parse params JSON  
        params_file = self._find_file_with_suffix('_params.json')
        if params_file:
            with open(params_file, 'r') as f:
                results['params'] = json.load(f)
                
        # Parse status JSON
        status_file = self._find_file_with_suffix('_status.json')
        if status_file:
            with open(status_file, 'r') as f:
                results['status'] = json.load(f)
                
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
            table_rows=table_rows,
            screenshot_html=screenshot_html,
            generation_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
        
        # Write HTML file
        with open(output_file, 'w') as f:
            f.write(html_content)
            
        print(f"Generated report: {output_file}")
    
    def _generate_table_rows(self, results_data: List[Dict]) -> str:
        """Generate HTML table rows from results data"""
        if not results_data:
            return "<tr><td colspan='100%'>No test data available</td></tr>"
            
        rows = []
        for i, entry in enumerate(results_data):
            row = f"<tr class='{'even' if i % 2 == 0 else 'odd'}'>"
            
            # Row number
            row += f"<td>{i + 1}</td>"
            
            # Timestamp
            timestamp = entry.get('Timestamp', 'N/A')
            row += f"<td>{timestamp}</td>"
            
            # SOCAN Command
            socan_cmd = entry.get('socan_command', 'N/A')
            row += f"<td class='command'>{socan_cmd}</td>"
            
            # SOCAN Response
            socan_response = entry.get('raw_socan_response', 'N/A')
            if len(str(socan_response)) > 100:
                socan_response = str(socan_response)[:100] + "..."
            row += f"<td class='response'>{socan_response}</td>"
            
            # RF Matrix Command
            rf_cmd = entry.get('rf_matrix_command', 'N/A')
            row += f"<td class='command'>{rf_cmd}</td>"
            
            # Keysight Command
            keysight_cmd = entry.get('keysight_xsan_command', 'N/A')
            row += f"<td class='command'>{keysight_cmd}</td>"
            
            # Peak Frequency
            peak_freq = entry.get('peak_frequency', 'N/A')
            if isinstance(peak_freq, (int, float)):
                peak_freq = f"{peak_freq / 1e9:.3f} GHz"
            row += f"<td class='numeric'>{peak_freq}</td>"
            
            # Peak Amplitude
            peak_amp = entry.get('peak_amplitude', 'N/A')
            if isinstance(peak_amp, (int, float)):
                peak_amp = f"{peak_amp:.2f} dBm"
            row += f"<td class='numeric'>{peak_amp}</td>"
            
            # Screenshot
            screenshot = entry.get('screenshot_filepath', '')
            if screenshot:
                row += f"<td><a href='#{screenshot}' class='screenshot-link'>View</a></td>"
            else:
                row += f"<td>N/A</td>"
                
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
        
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            font-size: 14px;
        }}
        
        th, td {{
            padding: 12px 8px;
            text-align: left;
            border-bottom: 1px solid #ddd;
            vertical-align: top;
        }}
        
        th {{
            background-color: #3498db;
            color: white;
            font-weight: bold;
            position: sticky;
            top: 0;
        }}
        
        tr:nth-child(even) {{
            background-color: #f8f9fa;
        }}
        
        tr:hover {{
            background-color: #e3f2fd;
        }}
        
        .command {{
            font-family: 'Courier New', monospace;
            font-size: 12px;
            max-width: 200px;
            word-wrap: break-word;
        }}
        
        .response {{
            font-family: 'Courier New', monospace;
            font-size: 11px;
            max-width: 250px;
            word-wrap: break-word;
        }}
        
        .numeric {{
            text-align: right;
            font-family: 'Courier New', monospace;
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
        
        .table-container {{
            overflow-x: auto;
            margin: 20px 0;
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
                    <tr>
                        <th>#</th>
                        <th>Timestamp</th>
                        <th>SOCAN Command</th>
                        <th>SOCAN Response</th>
                        <th>RF Matrix Command</th>
                        <th>Keysight Command</th>
                        <th>Peak Frequency</th>
                        <th>Peak Amplitude</th>
                        <th>Screenshot</th>
                    </tr>
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
        help='Input directory containing test result folders'
    )
    
    parser.add_argument(
        '--output-dir', '-o',
        type=Path,
        default=None,
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
    
    # Find all test folders (those starting with "test_")
    test_folders = [d for d in input_dir.iterdir() 
                   if d.is_dir() and d.name.startswith('test_')]
    
    if not test_folders:
        print(f"No test folders found in {input_dir}")
        return 1
    
    print(f"Found {len(test_folders)} test folders")
    
    # Generate reports for each test
    report_generator = HTMLReportGenerator()
    generated_reports = []
    
    for test_folder in sorted(test_folders):
        print(f"Processing {test_folder.name}...")
        
        try:
            # Parse test results
            parser = TestResultParser(test_folder)
            test_results = parser.parse_results()
            
            # Generate HTML report
            output_file = output_dir / f"{test_folder.name}_report.html"
            report_generator.generate_report(test_results, output_file)
            generated_reports.append(output_file)
            
        except Exception as e:
            print(f"Error processing {test_folder.name}: {str(e)}")
    
    # Generate index page
    index_file = output_dir / "index.html"
    _generate_index_page(generated_reports, index_file, input_dir.name)
    
    print(f"\nGenerated {len(generated_reports)} test reports in {output_dir}")
    print(f"Open {index_file} to view all reports")
    
    return 0


def _generate_index_page(report_files: List[Path], index_file: Path, test_session: str):
    """Generate an index page with links to all reports"""
    
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
            max-width: 800px;
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
        .report-list {{
            list-style: none;
            padding: 0;
        }}
        .report-list li {{
            margin: 10px 0;
            padding: 15px;
            background-color: #f8f9fa;
            border-left: 4px solid #3498db;
            border-radius: 4px;
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
        
        <ul class="report-list">
"""
    
    for report_file in sorted(report_files):
        test_name = report_file.stem.replace('_report', '')
        index_html += f'            <li><a href="{report_file.name}">{test_name}</a></li>\n'
    
    index_html += f"""        </ul>
        
        <div class="footer">
            <p>Generated on {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
            <p>{len(report_files)} test reports available</p>
        </div>
    </div>
</body>
</html>"""
    
    with open(index_file, 'w') as f:
        f.write(index_html)


if __name__ == '__main__':
    exit(main())