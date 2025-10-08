#!/usr/bin/env python3
"""
CSV to Interactive HTML Analyzer Generator

Converts combined CSV test results into interactive HTML analyzers with:
- Column visibility controls and reordering
- Global and per-column filtering
- Preset management
- Cell expansion for large content
- Row highlighting for results vs logs
- Responsive design
"""

import csv
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional


class CSVToHTMLAnalyzer:
    """Convert CSV data to interactive HTML analyzer"""
    
    def __init__(self):
        self.data: List[Dict[str, Any]] = []
        self.columns: List[str] = []
        self.column_types: Dict[str, str] = {}
        self.csv_path: Optional[str] = None

    def load_csv(self, csv_path: str) -> None:
        """Load CSV data and analyze column types"""
        print(f"Loading CSV: {csv_path}")
        self.csv_path = csv_path

        with open(csv_path, 'r', encoding='utf-8', newline='') as f:
            # Just use standard CSV format - no need to detect dialect
            reader = csv.DictReader(f)
            self.columns = reader.fieldnames or []
            
            # Load all data
            for row_idx, row in enumerate(reader):
                # Convert empty strings to None for cleaner display
                cleaned_row = {}
                for key, value in row.items():
                    if value == '':
                        cleaned_row[key] = None
                    else:
                        # Try to parse string representations of lists
                        if value.startswith('[') and value.endswith(']'):
                            try:
                                import ast
                                parsed_value = ast.literal_eval(value)
                                if isinstance(parsed_value, list):
                                    cleaned_row[key] = parsed_value
                                else:
                                    cleaned_row[key] = value
                            except (ValueError, SyntaxError):
                                cleaned_row[key] = value
                        else:
                            cleaned_row[key] = value

                cleaned_row['_row_index'] = row_idx
                self.data.append(cleaned_row)
        
        print(f"Loaded {len(self.data)} rows with {len(self.columns)} columns")
        self._analyze_column_types()
        
    def _analyze_column_types(self) -> None:
        """Analyze column types for better filtering and display"""
        for col in self.columns:
            col_type = self._detect_column_type(col)
            self.column_types[col] = col_type
            
    def _detect_column_type(self, column: str) -> str:
        """Detect column data type from column name and sample values"""
        # Check column name patterns
        if 'timestamp' in column.lower():
            return 'timestamp'
        if column.lower() in ['pass', 'socan_pass', 'rf_matrix_pass']:
            return 'boolean'
        if column.lower() in ['level', 'log_type']:
            return 'category'
        if 'frequency' in column.lower():
            return 'number'
        if 'amplitude' in column.lower() or 'dbm' in column.lower():
            return 'number'
        if column.lower() in ['message', 'docstring', 'command_str', 'data_str']:
            return 'text'
            
        # Analyze sample values
        sample_values = []
        for row in self.data[:100]:  # Sample first 100 rows
            val = row.get(column)
            if val is not None:
                sample_values.append(val)
        
        if not sample_values:
            return 'text'
            
        # Try to detect numeric values
        numeric_count = 0
        for val in sample_values:
            try:
                float(val)
                numeric_count += 1
            except (ValueError, TypeError):
                pass
                
        if numeric_count > len(sample_values) * 0.7:
            return 'number'
            
        # Check for boolean-like values
        bool_values = {'true', 'false', 'yes', 'no', '1', '0'}
        if all(str(val).lower() in bool_values for val in sample_values):
            return 'boolean'
            
        return 'text'
        
    def _is_result_row(self, row: Dict[str, Any]) -> bool:
        """Determine if a row is a test result vs a log entry"""
        # Check for result indicators
        if row.get('Pass') is not None:
            return True
        if row.get('log_type') or row.get('level'):
            return False
        if row.get('command_method') or row.get('keysight_xsan_command'):
            return True
        if row.get('peak_amplitude') or row.get('frequencies'):
            return True
        return False

    def _is_empty_row(self, row: Dict[str, Any]) -> bool:
        """Determine if a row only contains timestamp data and no other meaningful content"""
        # Get all columns except internal ones and common timestamp columns
        exclude_columns = {'_row_index', '_row_class', '_is_result', 'timestamp', 'Timestamp_original', 'timestamp_logs', 'timestamp_results'}
        data_columns = [col for col in self.columns if col not in exclude_columns]

        # Check if all data columns are empty/null
        non_empty_count = 0
        for col in data_columns:
            value = row.get(col)
            if value is not None and str(value).strip() != '':
                non_empty_count += 1

        return non_empty_count == 0

    def _get_row_class(self, row: Dict[str, Any]) -> str:
        """Get CSS class for row styling"""
        if self._is_result_row(row):
            if row.get('Pass') == 'True':
                return 'result-row result-pass'
            elif row.get('Pass') == 'False':
                return 'result-row result-fail'
            else:
                return 'result-row'
        else:
            log_level = row.get('level')
            if log_level:
                log_level = str(log_level).upper()
                if log_level in ['ERROR', 'CRITICAL']:
                    return 'log-row log-error'
                elif log_level == 'WARNING':
                    return 'log-row log-warning'
                elif log_level == 'INFO':
                    return 'log-row log-info'
                elif log_level == 'DEBUG':
                    return 'log-row log-debug'
            else:
                return 'log-row'
        
    def _extract_test_params(self, csv_path: str = None) -> Dict[str, Any]:
        """Extract test parameters from params JSON file"""
        test_params = {}

        if not csv_path:
            return test_params

        # Find the params.json file in the same directory as the CSV
        csv_path_obj = Path(csv_path)
        params_json_path = csv_path_obj.parent / f"{csv_path_obj.stem}_params.json"

        if not params_json_path.exists():
            # Fallback: try without _combined suffix
            params_json_path = csv_path_obj.parent / f"{csv_path_obj.stem.replace('_combined', '')}_params.json"

        if params_json_path.exists():
            try:
                with open(params_json_path, 'r', encoding='utf-8') as f:
                    params_data = json.load(f)
                    # The JSON has a "params" key containing the actual parameters
                    if 'params' in params_data:
                        test_params = params_data['params']
            except Exception as e:
                print(f"Warning: Could not load params from {params_json_path}: {e}")

        return test_params

    def _format_timestamp(self, timestamp_str: str) -> str:
        """Convert Unix timestamp (ms) to readable format yyyy-mm-dd hh:mm:ss,ms UTC"""
        if not timestamp_str or timestamp_str.strip() == '':
            return ''
            
        try:
            # First, try to parse as Unix timestamp in milliseconds (e.g., 1758902529684)
            if timestamp_str.strip().isdigit():
                timestamp_ms = int(timestamp_str.strip())
                # Convert from milliseconds to seconds for datetime
                dt = datetime.fromtimestamp(timestamp_ms / 1000.0)
                # Format to requested format: yyyy-mm-dd hh:mm:ss,ms
                ms = timestamp_ms % 1000  # Extract milliseconds
                formatted = dt.strftime('%Y-%m-%d %H:%M:%S') + f',{ms:03d}'
                return formatted
            
            # If not a Unix timestamp, try to parse as ISO format: "2025-09-26 17:01:59,358"
            if ',' in timestamp_str:
                # Replace comma with dot for milliseconds
                timestamp_str = timestamp_str.replace(',', '.')
                
            # Parse the timestamp (assuming it's already in UTC)
            dt = datetime.fromisoformat(timestamp_str)
            
            # Format to requested format: yyyy-mm-dd hh:mm:ss,ms
            formatted = dt.strftime('%Y-%m-%d %H:%M:%S')
            
            # Add milliseconds if present
            if dt.microsecond:
                ms = dt.microsecond // 1000  # Convert microseconds to milliseconds
                formatted += f',{ms:03d}'
                
            return formatted
            
        except (ValueError, AttributeError, OSError) as e:
            # If parsing fails, return original value
            return timestamp_str
    
    def _format_cell_value(self, value: Any, column: str) -> str:
        """Format cell value for display"""
        if value is None:
            return ''

        value_str = str(value)

        # Handle timestamp columns
        if self.column_types.get(column) == 'timestamp':
            # Skip formatting if the value is "None" or empty
            if value_str and value_str != 'None':
                formatted_ts = self._format_timestamp(value_str)
                if formatted_ts != value_str:  # Only show formatted if different
                    value_str = formatted_ts
            else:
                value_str = ''
        
        # Handle very long values
        if len(value_str) > 200:
            truncated = value_str[:197] + '...'
            escaped_full = html_escape(value_str)
            escaped_truncated = html_escape(truncated)
            return f'<span class="cell-content expandable" title="Click to expand" data-full="{escaped_full}">{escaped_truncated}</span>'
        else:
            return html_escape(value_str)
            
    def generate_html(self, output_path: str, title: str = None) -> None:
        """Generate interactive HTML analyzer"""
        if title is None:
            title = f"Test Analysis - {Path(output_path).stem}"

        # Extract docstring if available in the data
        docstring = None
        if 'docstring' in self.columns and self.data:
            # Get docstring from first row that has a non-empty value
            for row in self.data:
                doc_value = row.get('docstring', '')
                if doc_value and doc_value is not None:
                    doc_value = doc_value.strip()
                    if doc_value:
                        docstring = doc_value
                        break

        # Extract test parameters from params JSON file
        test_params = self._extract_test_params(self.csv_path)

        # Prepare data for JavaScript
        js_data = []
        for row in self.data:
            js_row = {
                '_row_class': self._get_row_class(row),
                '_is_result': self._is_result_row(row)
            }
            for col in self.columns:
                value = row.get(col)
                # Format timestamp values for JavaScript
                if self.column_types.get(col) == 'timestamp' and value:
                    formatted_value = self._format_timestamp(str(value))
                    js_row[col] = formatted_value if formatted_value != str(value) else value
                else:
                    js_row[col] = value
            js_data.append(js_row)

        # Group columns by category
        column_groups = self._group_columns()

        html_content = self._generate_html_template(title, js_data, column_groups, docstring, test_params)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

        print(f"Generated HTML analyzer: {output_path}")
        
    def _group_columns(self) -> Dict[str, List[str]]:
        """Group columns by category for better organization"""
        groups = {
            'Core': [],
            'Test Results': [],
            'Commands': [],
            'Measurements': [],
            'Timing': [],
            'Configuration': [],
            'Logging': [],
            'Other': []
        }
        
        for col in self.columns:
            col_lower = col.lower()
            
            if col in ['Pass', 'timestamp', 'Timestamp_original']:
                groups['Core'].append(col)
            elif any(x in col_lower for x in ['pass', 'result', 'peak_', 'amplitude', 'frequency']):
                groups['Test Results'].append(col)
            elif any(x in col_lower for x in ['command', 'method', 'response', 'parsed_']):
                groups['Commands'].append(col)
            elif any(x in col_lower for x in ['peak_table', 'trace_', 'measurement', 'data_']):
                groups['Measurements'].append(col)
            elif any(x in col_lower for x in ['timestamp', 'time', 'send_', 'receive_']):
                groups['Timing'].append(col)
            elif any(x in col_lower for x in ['enabled_', 'frequency_', 'gain_', 'channel', 'address']):
                groups['Configuration'].append(col)
            elif any(x in col_lower for x in ['log_', 'level', 'message', 'line_number']):
                groups['Logging'].append(col)
            else:
                groups['Other'].append(col)
                
        # Remove empty groups
        return {k: v for k, v in groups.items() if v}
        
    def _generate_html_template(self, title: str, js_data: List[Dict], column_groups: Dict[str, List[str]], docstring: str = None, test_params: Dict[str, Any] = None) -> str:
        """Generate the complete HTML template"""
        
        # Column visibility checkboxes HTML
        column_controls = []
        for group_name, cols in column_groups.items():
            column_controls.append(f'<div class="column-group">')
            column_controls.append(f'<h4>{group_name} <button class="group-toggle" onclick="toggleGroup(\'{group_name}\')">Toggle All</button></h4>')
            for col in cols:
                col_id = col.replace(' ', '_').replace('.', '_')
                checked = 'checked' if col in ['Pass', 'timestamp', 'message', 'command_method'] else ''
                column_controls.append(f'''
                    <label class="column-checkbox">
                        <input type="checkbox" {checked} data-column="{col}" data-group="{group_name}" 
                               onchange="toggleColumn('{col}')">
                        <span class="column-name">{html_escape(col)}</span>
                        <span class="column-type">({self.column_types.get(col, 'text')})</span>
                    </label>
                ''')
            column_controls.append('</div>')
            
        column_controls_html = '\n'.join(column_controls)
        
        # Filter controls HTML
        filter_controls = []
        for col in self.columns:
            col_type = self.column_types.get(col, 'text')
            if col_type == 'number':
                filter_controls.append(f'''
                    <div class="filter-control" data-column="{col}" style="display: none;">
                        <label>{html_escape(col)} (number)</label>
                        <input type="number" placeholder="Min" onchange="applyFilters()" data-filter-type="min" data-filter-column="{col}">
                        <input type="number" placeholder="Max" onchange="applyFilters()" data-filter-type="max" data-filter-column="{col}">
                    </div>
                ''')
            elif col_type == 'category':
                filter_controls.append(f'''
                    <div class="filter-control" data-column="{col}" style="display: none;">
                        <label>{html_escape(col)} (category)</label>
                        <select multiple onchange="applyFilters()" data-filter-column="{col}">
                            <!-- Options will be populated by JavaScript -->
                        </select>
                    </div>
                ''')
            else:
                filter_controls.append(f'''
                    <div class="filter-control" data-column="{col}" style="display: none;">
                        <label>{html_escape(col)} (text)</label>
                        <input type="text" placeholder="Filter..." onchange="applyFilters()" data-filter-column="{col}">
                    </div>
                ''')
                
        filter_controls_html = '\n'.join(filter_controls)
        
        return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{html_escape(title)}</title>
    <script>
        // Journalctl data will be loaded from parent directory
        var journalctlData = [];
    </script>
    <script src="../journalctl_data.js" onerror="console.warn('journalctl_data.js not found - double-click feature will not work')"></script>
    <style>
        * {{
            box-sizing: border-box;
        }}

        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
            color: #333;
        }}

        .container {{
            max-width: 100%;
            margin: 0 auto;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            overflow: hidden;
        }}

        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            text-align: center;
        }}

        .header h1 {{
            margin: 0;
            font-size: 2em;
        }}
        
        .controls {{
            display: flex;
            flex-wrap: wrap;
            gap: 20px;
            padding: 20px;
            background: #f8f9fa;
            border-bottom: 1px solid #dee2e6;
        }}
        
        .control-section {{
            flex: 1;
            min-width: 300px;
        }}
        
        .control-section h3 {{
            margin: 0 0 15px 0;
            color: #495057;
        }}
        
        .global-controls {{
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            margin-bottom: 15px;
        }}
        
        .global-search {{
            flex: 1;
            min-width: 200px;
            padding: 8px 12px;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-size: 14px;
        }}
        
        .btn {{
            padding: 8px 16px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 14px;
            background: #007bff;
            color: white;
            transition: background-color 0.2s;
        }}
        
        .btn:hover {{
            background: #0056b3;
        }}
        
        .btn-secondary {{
            background: #6c757d;
        }}
        
        .btn-secondary:hover {{
            background: #545b62;
        }}
        
        .presets {{
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            align-items: center;
        }}
        
        .preset-select {{
            min-width: 150px;
            padding: 6px;
            border: 1px solid #ddd;
            border-radius: 4px;
        }}
        
        .column-controls {{
            max-height: 300px;
            overflow-y: auto;
            border: 1px solid #ddd;
            border-radius: 4px;
            padding: 10px;
            background: white;
        }}
        
        .column-group {{
            margin-bottom: 15px;
        }}
        
        .column-group h4 {{
            margin: 0 0 8px 0;
            color: #495057;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        
        .group-toggle {{
            background: #28a745;
            color: white;
            border: none;
            padding: 4px 8px;
            border-radius: 3px;
            cursor: pointer;
            font-size: 12px;
        }}
        
        .column-checkbox {{
            display: block;
            padding: 4px 0;
            cursor: pointer;
        }}
        
        .column-checkbox input {{
            margin-right: 8px;
        }}
        
        .column-name {{
            font-weight: 500;
        }}
        
        .column-type {{
            color: #6c757d;
            font-size: 12px;
            margin-left: 8px;
        }}

        .toggle-checkbox {{
            display: flex;
            align-items: center;
            gap: 8px;
            cursor: pointer;
            font-size: 14px;
            color: #495057;
        }}

        .toggle-checkbox input {{
            margin: 0;
        }}
        
        .filter-controls {{
            max-height: 300px;
            overflow-y: auto;
            border: 1px solid #ddd;
            border-radius: 4px;
            padding: 10px;
            background: white;
        }}
        
        .filter-control {{
            margin-bottom: 10px;
        }}
        
        .filter-control label {{
            display: block;
            margin-bottom: 4px;
            font-weight: 500;
            color: #495057;
        }}
        
        .filter-control input,
        .filter-control select {{
            width: 100%;
            padding: 6px;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-size: 14px;
        }}
        
        .filter-control input[type="number"] {{
            width: 48%;
            margin-right: 4%;
        }}
        
        .filter-control input[type="number"]:last-child {{
            margin-right: 0;
        }}
        
        .stats {{
            text-align: center;
            padding: 10px;
            background: #e9ecef;
            font-size: 14px;
            color: #6c757d;
        }}
        
        .table-container {{
            overflow: auto;
            max-height: 70vh;
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 13px;
        }}
        
        th, td {{
            padding: 8px;
            text-align: left;
            border: 1px solid #ddd;
            word-wrap: break-word;
            max-width: 300px;
            position: relative;
        }}
        
        th {{
            background: #f8f9fa;
            font-weight: 600;
            position: sticky;
            top: 0;
            z-index: 100;
        }}
        
        .sortable {{
            cursor: pointer;
            user-select: none;
            position: relative;
        }}

        .sortable:hover {{
            background: #e9ecef;
        }}

        .draggable {{
            cursor: grab;
            transition: background-color 0.2s;
        }}

        .draggable:active {{
            cursor: grabbing;
        }}

        .draggable.dragging {{
            opacity: 0.5;
            background: #007bff;
            color: white;
        }}

        .drop-zone {{
            position: relative;
        }}

        .drop-indicator {{
            position: absolute;
            top: 0;
            bottom: 0;
            width: 3px;
            background: #007bff;
            z-index: 1000;
            display: none;
        }}

        .drop-indicator.left {{
            left: -2px;
        }}

        .drop-indicator.right {{
            right: -2px;
        }}

        .drop-indicator.show {{
            display: block;
        }}
        
        .sort-indicator {{
            float: right;
            opacity: 0.5;
        }}
        
        .result-row {{
            background: #f8fff8;
        }}
        
        .result-pass {{
            border-left: 4px solid #28a745;
        }}
        
        .result-fail {{
            border-left: 4px solid #dc3545;
            background: #fff5f5;
        }}
        
        .log-row {{
            background: #fafafa;
        }}
        
        .log-error {{
            border-left: 4px solid #dc3545;
            background: #fff5f5;
        }}
        
        .log-warning {{
            border-left: 4px solid #ffc107;
            background: #fffbf0;
        }}
        
        .log-info {{
            border-left: 4px solid #17a2b8;
        }}
        
        .log-debug {{
            border-left: 4px solid #6c757d;
        }}
        
        .cell-content.expandable {{
            cursor: pointer;
            color: #007bff;
            text-decoration: underline;
        }}
        
        .expanded {{
            white-space: pre-wrap;
            max-width: none !important;
            word-break: break-all;
        }}
        
        .hidden {{
            display: none !important;
        }}
        
        .modal {{
            display: none;
            position: fixed;
            z-index: 1000;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0,0,0,0.5);
        }}

        .modal-content {{
            background-color: #fff;
            margin: 5% auto;
            padding: 20px;
            border-radius: 8px;
            width: 80%;
            max-width: 800px;
            max-height: 80%;
            overflow-y: auto;
        }}

        .image-modal {{
            display: none;
            position: fixed;
            z-index: 1001;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0,0,0,0.8);
            cursor: pointer;
        }}

        .image-modal-content {{
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            max-width: 95vw;
            max-height: 95vh;
            width: auto;
            height: auto;
            background: white;
            border-radius: 8px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.3);
            overflow: hidden;
        }}

        .image-modal img {{
            max-width: 100%;
            max-height: calc(95vh - 60px);
            width: auto;
            height: auto;
            display: block;
            object-fit: contain;
        }}

        .image-modal-caption {{
            padding: 15px;
            background: white;
            text-align: center;
            color: #333;
            font-size: 14px;
            border-top: 1px solid #eee;
        }}

        .image-modal-close {{
            position: absolute;
            top: 15px;
            right: 20px;
            color: white;
            font-size: 35px;
            font-weight: bold;
            cursor: pointer;
            background: rgba(0,0,0,0.5);
            border-radius: 50%;
            width: 45px;
            height: 45px;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: background-color 0.2s;
        }}

        .image-modal-close:hover {{
            background: rgba(0,0,0,0.7);
        }}
        
        .close {{
            color: #aaa;
            float: right;
            font-size: 28px;
            font-weight: bold;
            cursor: pointer;
        }}
        
        .close:hover {{
            color: #000;
        }}

        .image-gallery {{
            padding: 20px;
            background: #f8f9fa;
            border-top: 1px solid #dee2e6;
        }}

        .image-gallery h3 {{
            margin: 0 0 20px 0;
            color: #495057;
            text-align: center;
        }}

        .gallery-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 20px;
            max-height: 600px;
            overflow-y: auto;
        }}

        .gallery-item {{
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            overflow: hidden;
            transition: transform 0.2s;
        }}

        .gallery-item:hover {{
            transform: translateY(-2px);
            box-shadow: 0 4px 10px rgba(0,0,0,0.15);
        }}

        .gallery-item img {{
            width: 100%;
            height: 200px;
            object-fit: contain;
            background: #f8f9fa;
            border-bottom: 1px solid #dee2e6;
        }}

        .gallery-item .filename {{
            padding: 10px;
            font-size: 12px;
            color: #6c757d;
            text-align: center;
            word-break: break-all;
        }}

        .filename-link {{
            color: #007bff;
            text-decoration: underline;
            cursor: pointer;
        }}

        .filename-link:hover {{
            color: #0056b3;
        }}

        .gallery-empty {{
            text-align: center;
            color: #6c757d;
            font-style: italic;
            padding: 40px;
        }}

        @media (max-width: 768px) {{
            .controls {{
                flex-direction: column;
            }}

            .control-section {{
                min-width: auto;
            }}

            th, td {{
                padding: 4px;
                font-size: 12px;
            }}

            .gallery-grid {{
                grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
                gap: 10px;
            }}

            .gallery-item img {{
                height: 150px;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{html_escape(title)}</h1>
        </div>
        {f'''
        <div class="docstring-section" style="background: #e7f3ff; border-left: 4px solid #2196F3; color: #1565C0; padding: 15px 20px; margin: 15px 20px; border-radius: 4px;">
            <h3 style="margin: 0 0 10px 0; color: #1565C0; font-size: 1.1em;">Test Description</h3>
            <p style="margin: 0; white-space: pre-wrap; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6;">{html_escape(docstring)}</p>
        </div>
        ''' if docstring else ''}
        {f'''
        <div class="test-params-section" style="background: #f0f8f0; border-left: 4px solid #4CAF50; color: #2e7d32; padding: 15px 20px; margin: 15px 20px; border-radius: 4px;">
            <h3 style="margin: 0 0 10px 0; color: #2e7d32; font-size: 1.1em;">Test Parameters</h3>
            <table style="width: 100%; border-collapse: collapse; font-size: 0.95em;">
                {''.join([f'<tr><td style="padding: 5px 10px; border: 1px solid #c8e6c9; font-weight: 500; background: #e8f5e9; width: 40%;">{html_escape(key)}</td><td style="padding: 5px 10px; border: 1px solid #c8e6c9; background: white;">{html_escape(str(value))}</td></tr>' for key, value in test_params.items()])}
            </table>
        </div>
        ''' if test_params else ''}
        <div class="controls">
            <div class="control-section">
                <h3>Global Controls</h3>
                <div class="global-controls">
                    <input type="text" class="global-search" placeholder="Global search..." onkeyup="applyFilters()">
                    <label class="toggle-checkbox">
                        <input type="checkbox" id="hide-empty-rows" checked onchange="applyFilters()">
                        <span>Hide empty rows</span>
                    </label>
                    <button class="btn" onclick="clearAllFilters()">Clear Filters</button>
                    <button class="btn btn-secondary" onclick="exportData()">Export Data</button>
                </div>
                
                <div class="presets">
                    <select class="preset-select" onchange="loadPreset(this.value)">
                        <option value="">Select Preset...</option>
                        <option value="default">Default View</option>
                        <option value="results-only">Results Only</option>
                    </select>
                </div>
            </div>
            
            <div class="control-section">
                <h3>Column Visibility</h3>
                <div class="column-controls">
                    {column_controls_html}
                </div>
            </div>
            
            <div class="control-section">
                <h3>Column Filters</h3>
                <div class="filter-controls">
                    {filter_controls_html}
                </div>
            </div>
        </div>
        
        <div class="stats">
            <span id="row-count">Loading...</span> | 
            <span id="result-count">Results: 0</span> | 
            <span id="log-count">Logs: 0</span>
        </div>
        
        <div class="table-container">
            <table id="data-table">
                <thead id="table-header">
                    <!-- Headers will be generated by JavaScript -->
                </thead>
                <tbody id="table-body">
                    <!-- Data will be populated by JavaScript -->
                </tbody>
            </table>
        </div>

        <div class="image-gallery">
            <h3>Image Gallery</h3>
            <div id="gallery-grid" class="gallery-grid">
                <div class="gallery-empty">
                    No images found in the current data
                </div>
            </div>
        </div>
    </div>
    
    <!-- Modal for expanded content -->
    <div id="contentModal" class="modal">
        <div class="modal-content">
            <span class="close" onclick="closeModal()">&times;</span>
            <h3>Content Detail</h3>
            <pre id="modal-content"></pre>
        </div>
    </div>

    <!-- Modal for expanded images -->
    <div id="imageModal" class="image-modal" onclick="closeImageModal()">
        <div class="image-modal-close" onclick="closeImageModal()">&times;</div>
        <div class="image-modal-content" onclick="event.stopPropagation()">
            <img id="modal-image" src="" alt="">
            <div class="image-modal-caption" id="modal-caption"></div>
        </div>
    </div>
    
    <script>
        // Data and state
        const data = {json.dumps(js_data, indent=2)};
        const columns = {json.dumps(self.columns)};
        const columnTypes = {json.dumps(self.column_types)};
        
        let filteredData = [...data];
        let visibleColumns = new Set(['Pass', 'timestamp', 'message', 'command_method']);
        let columnOrder = [...columns]; // Track the order of columns
        let sortColumn = null;
        let sortDirection = 'asc';
        let filters = {{}};

        // Escape HTML attribute values
        function escapeHtmlAttr(str) {{
            return String(str)
                .replace(/&/g, '&amp;')
                .replace(/"/g, '&quot;')
                .replace(/'/g, '&#39;')
                .replace(/</g, '&lt;')
                .replace(/>/g, '&gt;');
        }}

        // Check if a row is empty based on currently visible columns
        function isRowEmpty(row) {{
            const timestampColumns = ['timestamp', 'Timestamp_original', 'timestamp_logs', 'timestamp_results'];
            const visibleDataColumns = Array.from(visibleColumns).filter(col => !timestampColumns.includes(col));

            for (const col of visibleDataColumns) {{
                const value = row[col];
                if (value !== null && value !== undefined && String(value).trim() !== '') {{
                    return false;
                }}
            }}

            return visibleDataColumns.length > 0; // Only consider empty if there are non-timestamp columns visible
        }}

        // Format timestamp from Unix ms or "2025-09-26 17:01:59,358" to "2025-09-26 17:01:59,358"
        function formatTimestamp(timestampStr) {{
            if (!timestampStr || timestampStr.trim() === '') {{
                return '';
            }}
            
            try {{
                // First, check if it's a Unix timestamp (all digits)
                if (/^\\d+$/.test(timestampStr.trim())) {{
                    const timestampMs = parseInt(timestampStr.trim());
                    const date = new Date(timestampMs);
                    
                    if (isNaN(date.getTime())) {{
                        return timestampStr; // Return original if parsing fails
                    }}
                    
                    const year = date.getFullYear();
                    const month = String(date.getMonth() + 1).padStart(2, '0');
                    const day = String(date.getDate()).padStart(2, '0');
                    const hours = String(date.getHours()).padStart(2, '0');
                    const minutes = String(date.getMinutes()).padStart(2, '0');
                    const seconds = String(date.getSeconds()).padStart(2, '0');
                    const ms = String(date.getMilliseconds()).padStart(3, '0');
                    
                    return `${{year}}-${{month}}-${{day}} ${{hours}}:${{minutes}}:${{seconds}},${{ms}}`;
                }}
                
                // If not Unix timestamp, handle ISO format: "2025-09-26 17:01:59,358"
                let formattedStr = timestampStr.replace(',', '.');
                const date = new Date(formattedStr);
                
                if (isNaN(date.getTime())) {{
                    return timestampStr; // Return original if parsing fails
                }}
                
                const year = date.getFullYear();
                const month = String(date.getMonth() + 1).padStart(2, '0');
                const day = String(date.getDate()).padStart(2, '0');
                const hours = String(date.getHours()).padStart(2, '0');
                const minutes = String(date.getMinutes()).padStart(2, '0');
                const seconds = String(date.getSeconds()).padStart(2, '0');
                const ms = String(date.getMilliseconds()).padStart(3, '0');
                
                return `${{year}}-${{month}}-${{day}} ${{hours}}:${{minutes}}:${{seconds}},${{ms}}`;
                
            }} catch (e) {{
                return timestampStr; // Return original if error
            }}
        }}
        
        // Initialize
        document.addEventListener('DOMContentLoaded', function() {{
            initializeTable();
            populateFilterOptions();
            loadSavedPresets();
            populateImageGallery();
            updateDisplay();
        }});
        
        function initializeTable() {{
            updateTableHeaders();
        }}
        
        function updateTableHeaders() {{
            const headerRow = document.getElementById('table-header');
            headerRow.innerHTML = '';

            columnOrder.forEach(col => {{
                if (visibleColumns.has(col)) {{
                    const th = document.createElement('th');
                    th.className = 'sortable draggable drop-zone';
                    th.draggable = true;
                    th.dataset.column = col;
                    th.onclick = (e) => {{
                        if (!e.target.closest('.dragging')) {{
                            sortBy(col);
                        }}
                    }};

                    const sortIndicator = sortColumn === col ?
                        (sortDirection === 'asc' ? '↑' : '↓') : '↕';

                    th.innerHTML = `
                        <div class="drop-indicator left"></div>
                        <span style="opacity: 0.5; margin-right: 5px;">⋮⋮</span>${{col}} <span class="sort-indicator">${{sortIndicator}}</span>
                        <div class="drop-indicator right"></div>
                    `;

                    // Add drag event listeners
                    th.addEventListener('dragstart', handleDragStart);
                    th.addEventListener('dragover', handleDragOver);
                    th.addEventListener('dragenter', handleDragEnter);
                    th.addEventListener('dragleave', handleDragLeave);
                    th.addEventListener('drop', handleDrop);
                    th.addEventListener('dragend', handleDragEnd);

                    headerRow.appendChild(th);
                }}
            }});
        }}
        
        function updateTableBody() {{
            const tbody = document.getElementById('table-body');
            tbody.innerHTML = '';

            filteredData.forEach(row => {{
                const tr = document.createElement('tr');
                tr.className = row._row_class || '';

                // Add double-click handler to open journalctl view
                tr.ondblclick = function() {{
                    openJournalctlView(row);
                }};
                tr.style.cursor = 'pointer';
                tr.title = 'Double-click to view journalctl logs (configurable time window)';

                columnOrder.forEach(col => {{
                    if (visibleColumns.has(col)) {{
                        const td = document.createElement('td');
                        let value = row[col];

                        if (value !== null && value !== undefined) {{
                            let valueStr;

                            // Handle arrays and objects
                            if (Array.isArray(value)) {{
                                // Check if array contains objects
                                if (value.length > 0 && typeof value[0] === 'object') {{
                                    valueStr = value.map(item => JSON.stringify(item)).join('\\n');
                                }} else {{
                                    valueStr = value.join('\\n');
                                }}
                            }} else if (typeof value === 'object') {{
                                // Handle objects by JSON stringifying them
                                valueStr = JSON.stringify(value, null, 2);
                            }} else {{
                                valueStr = String(value);
                            }}

                            // Format timestamp columns
                            if (columnTypes[col] === 'timestamp') {{
                                const formatted = formatTimestamp(valueStr);
                                if (formatted !== valueStr) {{
                                    valueStr = formatted;
                                }}
                            }}

                            // Handle filename column specially
                            if (col.toLowerCase() === 'filename' && isImageFile(valueStr)) {{
                                const imageId = generateImageId(valueStr);
                                td.innerHTML = `<span class="filename-link" onclick="scrollToImage('${{imageId}}')">${{valueStr}}</span>`;
                            }} else if (valueStr.length > 200) {{
                                const escapedValue = escapeHtmlAttr(valueStr);
                                td.innerHTML = `<span class="cell-content expandable" onclick="showModal('${{col}}', this)" data-full="${{escapedValue}}">${{valueStr.substring(0, 197)}}...</span>`;
                            }} else {{
                                // Use pre-wrap to preserve newlines in arrays
                                if (Array.isArray(value)) {{
                                    td.style.whiteSpace = 'pre-wrap';
                                }}
                                td.textContent = valueStr;
                            }}
                        }} else {{
                            td.textContent = '';
                        }}

                        tr.appendChild(td);
                    }}
                }});

                tbody.appendChild(tr);
            }});
        }}
        
        function updateDisplay() {{
            updateTableHeaders();
            updateTableBody();
            updateStats();
            updateFilterVisibility();
        }}
        
        function updateStats() {{
            const totalRows = filteredData.length;
            const resultRows = filteredData.filter(row => row._is_result).length;
            const logRows = totalRows - resultRows;
            const hideEmptyRows = document.getElementById('hide-empty-rows').checked;
            const hiddenEmptyRows = hideEmptyRows ? data.filter(row => isRowEmpty(row)).length : 0;

            let statsText = `Showing ${{totalRows}} of ${{data.length}} rows`;
            if (hideEmptyRows && hiddenEmptyRows > 0) {{
                statsText += ` (${{hiddenEmptyRows}} empty rows hidden)`;
            }}

            document.getElementById('row-count').textContent = statsText;
            document.getElementById('result-count').textContent = `Results: ${{resultRows}}`;
            document.getElementById('log-count').textContent = `Logs: ${{logRows}}`;
        }}
        
        function updateFilterVisibility() {{
            document.querySelectorAll('.filter-control').forEach(control => {{
                const column = control.dataset.column;
                control.style.display = visibleColumns.has(column) ? 'block' : 'none';
            }});
        }}
        
        function toggleColumn(column) {{
            if (visibleColumns.has(column)) {{
                visibleColumns.delete(column);
            }} else {{
                visibleColumns.add(column);
            }}
            applyFilters(); // Recalculate empty rows based on new visible columns
        }}
        
        function toggleGroup(groupName) {{
            const checkboxes = document.querySelectorAll(`input[data-group="${{groupName}}"]`);
            const anyChecked = Array.from(checkboxes).some(cb => cb.checked);
            
            checkboxes.forEach(cb => {{
                cb.checked = !anyChecked;
                const column = cb.dataset.column;
                if (!anyChecked) {{
                    visibleColumns.add(column);
                }} else {{
                    visibleColumns.delete(column);
                }}
            }});

            applyFilters(); // Recalculate empty rows based on new visible columns
        }}
        
        function sortBy(column) {{
            if (sortColumn === column) {{
                sortDirection = sortDirection === 'asc' ? 'desc' : 'asc';
            }} else {{
                sortColumn = column;
                sortDirection = 'asc';
            }}
            
            filteredData.sort((a, b) => {{
                let valA = a[column];
                let valB = b[column];
                
                // Handle null/undefined values
                if (valA === null || valA === undefined) valA = '';
                if (valB === null || valB === undefined) valB = '';
                
                // Try numeric comparison
                const numA = parseFloat(valA);
                const numB = parseFloat(valB);
                if (!isNaN(numA) && !isNaN(numB)) {{
                    return sortDirection === 'asc' ? numA - numB : numB - numA;
                }}
                
                // String comparison
                const strA = String(valA).toLowerCase();
                const strB = String(valB).toLowerCase();
                if (sortDirection === 'asc') {{
                    return strA < strB ? -1 : strA > strB ? 1 : 0;
                }} else {{
                    return strA > strB ? -1 : strA < strB ? 1 : 0;
                }}
            }});
            
            updateDisplay();
        }}
        
        function applyFilters() {{
            const globalSearch = document.querySelector('.global-search').value.toLowerCase();
            const hideEmptyRows = document.getElementById('hide-empty-rows').checked;

            // Collect all filter values
            filters = {{}};
            document.querySelectorAll('[data-filter-column]').forEach(input => {{
                const column = input.dataset.filterColumn;
                const filterType = input.dataset.filterType;
                
                if (input.tagName === 'SELECT') {{
                    const selected = Array.from(input.selectedOptions).map(opt => opt.value);
                    if (selected.length > 0) {{
                        filters[column] = {{ type: 'select', values: selected }};
                    }}
                }} else if (filterType === 'min' || filterType === 'max') {{
                    if (!filters[column]) filters[column] = {{ type: 'range' }};
                    if (input.value) {{
                        filters[column][filterType] = parseFloat(input.value);
                    }}
                }} else if (input.value) {{
                    filters[column] = {{ type: 'text', value: input.value.toLowerCase() }};
                }}
            }});
            
            // Apply filters
            filteredData = data.filter(row => {{
                // Hide empty rows filter (dynamic based on visible columns)
                if (hideEmptyRows && isRowEmpty(row)) {{
                    return false;
                }}

                // Global search
                if (globalSearch) {{
                    const rowText = columns.map(col => String(row[col] || '')).join(' ').toLowerCase();
                    if (!rowText.includes(globalSearch)) {{
                        return false;
                    }}
                }}
                
                // Column filters
                for (const [column, filter] of Object.entries(filters)) {{
                    const value = row[column];
                    
                    if (filter.type === 'text') {{
                        if (!String(value || '').toLowerCase().includes(filter.value)) {{
                            return false;
                        }}
                    }} else if (filter.type === 'select') {{
                        if (!filter.values.includes(String(value || ''))) {{
                            return false;
                        }}
                    }} else if (filter.type === 'range') {{
                        const numValue = parseFloat(value);
                        if (isNaN(numValue)) continue;
                        
                        if (filter.min !== undefined && numValue < filter.min) {{
                            return false;
                        }}
                        if (filter.max !== undefined && numValue > filter.max) {{
                            return false;
                        }}
                    }}
                }}
                
                return true;
            }});
            
            updateDisplay();
        }}
        
        function clearAllFilters() {{
            document.querySelector('.global-search').value = '';
            document.getElementById('hide-empty-rows').checked = true; // Keep hide empty rows on by default
            document.querySelectorAll('[data-filter-column]').forEach(input => {{
                if (input.tagName === 'SELECT') {{
                    input.selectedIndex = -1;
                }} else {{
                    input.value = '';
                }}
            }});

            filters = {{}};
            applyFilters(); // Use applyFilters to respect the hide empty rows setting
        }}
        
        function populateFilterOptions() {{
            // Populate select options for category columns
            columns.forEach(column => {{
                if (columnTypes[column] === 'category') {{
                    const select = document.querySelector(`select[data-filter-column="${{column}}"]`);
                    if (select) {{
                        const uniqueValues = [...new Set(data.map(row => row[column]).filter(v => v !== null && v !== undefined))];
                        uniqueValues.sort();

                        uniqueValues.forEach(value => {{
                            const option = document.createElement('option');
                            option.value = value;
                            option.textContent = value;
                            select.appendChild(option);
                        }});
                    }}
                }}
            }});
        }}

        function loadSavedPresets() {{
            // No longer needed - presets are now built-in
        }}
        
        function loadPreset(presetName) {{
            if (!presetName) return;

            let preset = null;

            // All presets are now built-in
            const presets = {{
                'default': {{
                    columns: ['timestamp', 'Pass', 'command_method', 'command_str', 'raw_response', 'peak_frequency', 'peak_amplitude', 'log_type'],
                    filters: {{}}
                }},
                'results-only': {{
                    columns: ['timestamp', 'rf_matrix_command_str', 'rf_matrix_raw_response', 'socan_command_str', 'socan_raw_response', 'peak_amplitude', 'peak_frequency', 'Pass', 'Failure_Messages'],
                    filters: {{ '_is_result': true }}
                }},
            }};

            preset = presets[presetName];

            if (preset) {{
                // Set visible columns and update column order to match preset
                visibleColumns.clear();
                const newColumnOrder = [];
                preset.columns.forEach(col => {{
                    if (columns.includes(col)) {{
                        visibleColumns.add(col);
                        newColumnOrder.push(col);
                    }}
                }});
                // Add remaining columns that aren't in the preset
                columns.forEach(col => {{
                    if (!newColumnOrder.includes(col)) {{
                        newColumnOrder.push(col);
                    }}
                }});
                columnOrder = newColumnOrder;

                // Update checkboxes
                document.querySelectorAll('input[data-column]').forEach(cb => {{
                    cb.checked = visibleColumns.has(cb.dataset.column);
                }});

                // Clear all filters first
                clearAllFilters();

                // Apply saved filters
                if (preset.filters) {{
                    Object.entries(preset.filters).forEach(([column, filter]) => {{
                        if (filter.type === 'text') {{
                            const input = document.querySelector(`input[data-filter-column="${{column}}"]`);
                            if (input && input.type === 'text') {{
                                input.value = filter.value;
                            }}
                        }} else if (filter.type === 'select') {{
                            const select = document.querySelector(`select[data-filter-column="${{column}}"]`);
                            if (select) {{
                                filter.values.forEach(value => {{
                                    const option = select.querySelector(`option[value="${{value}}"]`);
                                    if (option) option.selected = true;
                                }});
                            }}
                        }} else if (filter.type === 'range') {{
                            if (filter.min !== undefined) {{
                                const minInput = document.querySelector(`input[data-filter-column="${{column}}"][data-filter-type="min"]`);
                                if (minInput) minInput.value = filter.min;
                            }}
                            if (filter.max !== undefined) {{
                                const maxInput = document.querySelector(`input[data-filter-column="${{column}}"][data-filter-type="max"]`);
                                if (maxInput) maxInput.value = filter.max;
                            }}
                        }}
                    }});
                }}

                // Apply special preset filters
                if (preset.filters) {{
                    // Handle result filtering
                    if (preset.filters._is_result !== undefined) {{
                        filteredData = data.filter(row => row._is_result === preset.filters._is_result);
                    }}

                    // Handle Pass filter for failures-only
                    if (preset.filters.Pass) {{
                        const passValues = preset.filters.Pass;
                        filteredData = filteredData.filter(row => passValues.includes(String(row.Pass || '')));
                    }}

                    // Handle level filter
                    if (preset.filters.level) {{
                        const levelSelect = document.querySelector('select[data-filter-column="level"]');
                        if (levelSelect) {{
                            preset.filters.level.forEach(level => {{
                                const option = levelSelect.querySelector(`option[value="${{level}}"]`);
                                if (option) option.selected = true;
                            }});
                        }}
                    }}
                }}

                applyFilters();
            }}
        }}
        
        
        function showModal(column, element) {{
            let fullContent = element.dataset.full || element.textContent;
            // Unescape HTML entities from the data attribute
            const textarea = document.createElement('textarea');
            textarea.innerHTML = fullContent;
            fullContent = textarea.value;
            document.getElementById('modal-content').textContent = fullContent;
            document.getElementById('contentModal').style.display = 'block';
        }}
        
        function closeModal() {{
            document.getElementById('contentModal').style.display = 'none';
        }}

        function openImageModal(imageSrc, filename) {{
            const modal = document.getElementById('imageModal');
            const modalImage = document.getElementById('modal-image');
            const modalCaption = document.getElementById('modal-caption');

            modalImage.src = imageSrc;
            modalImage.alt = filename;
            modalCaption.textContent = filename;
            modal.style.display = 'block';
        }}

        function closeImageModal() {{
            document.getElementById('imageModal').style.display = 'none';
        }}
        
        function exportData() {{
            // Get visible columns in current order
            const visibleCols = columnOrder.filter(col => visibleColumns.has(col));

            // Helper function to properly escape CSV values
            function escapeCsvValue(value) {{
                if (value === null || value === undefined) {{
                    return '';
                }}

                // Convert to string
                let strValue = String(value);

                // Handle arrays by joining with newlines
                if (Array.isArray(value)) {{
                    strValue = value.join('\\n');
                }}

                // Handle objects by stringifying
                if (typeof value === 'object' && !Array.isArray(value)) {{
                    strValue = JSON.stringify(value);
                }}

                // Escape double quotes by doubling them
                strValue = strValue.replace(/"/g, '""');

                // Always quote the value to handle newlines, commas, and quotes properly
                return `"${{strValue}}"`;
            }}

            // Build CSV content
            const csvRows = [];

            // Add header row
            csvRows.push(visibleCols.map(col => escapeCsvValue(col)).join(','));

            // Add data rows from filtered data
            filteredData.forEach(row => {{
                const rowValues = visibleCols.map(col => {{
                    // Get the original full value (not truncated)
                    let value = row[col];

                    // Format timestamps for better readability
                    if (columnTypes[col] === 'timestamp' && value) {{
                        const formatted = formatTimestamp(String(value));
                        if (formatted !== String(value)) {{
                            value = formatted;
                        }}
                    }}

                    return escapeCsvValue(value);
                }});

                csvRows.push(rowValues.join(','));
            }});

            const csvContent = csvRows.join('\\n');

            // Create and download the file
            const blob = new Blob([csvContent], {{ type: 'text/csv;charset=utf-8;' }});
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;

            // Generate filename based on current filters
            const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, -5);
            const rowCount = filteredData.length;
            a.download = `export_${{rowCount}}_rows_${{timestamp}}.csv`;

            a.click();
            window.URL.revokeObjectURL(url);

            console.log(`Exported ${{rowCount}} rows with ${{visibleCols.length}} columns`);
        }}

        // Image gallery functions
        function isImageFile(filename) {{
            if (!filename) return false;
            const imageExtensions = ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.svg', '.webp'];
            const lowerFilename = filename.toLowerCase();
            return imageExtensions.some(ext => lowerFilename.endsWith(ext));
        }}

        function generateImageId(filename) {{
            // Create a unique ID from filename by replacing problematic characters
            return 'img_' + filename.replace(/[^a-zA-Z0-9_-]/g, '_');
        }}

        function populateImageGallery() {{
            const galleryGrid = document.getElementById('gallery-grid');
            const imageFiles = new Set();

            // Find all image files in the filename column
            data.forEach(row => {{
                const filename = row.filename;
                if (filename && isImageFile(filename)) {{
                    imageFiles.add(filename);
                }}
            }});

            if (imageFiles.size === 0) {{
                galleryGrid.innerHTML = '<div class="gallery-empty">No images found in the current data</div>';
                return;
            }}

            // Create gallery items
            galleryGrid.innerHTML = '';
            imageFiles.forEach(filename => {{
                const imageId = generateImageId(filename);
                const galleryItem = document.createElement('div');
                galleryItem.className = 'gallery-item';
                galleryItem.id = imageId;

                // Extract just the filename from the path for the image src
                // If filename contains path separators, use only the filename part
                const imageSrc = filename.includes('/') ? filename.split('/').pop() : filename;

                galleryItem.innerHTML = `
                    <img src="${{imageSrc}}" alt="${{filename}}" onclick="openImageModal('${{imageSrc}}', '${{filename}}')" style="cursor: pointer;" onerror="this.src='data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAwIiBoZWlnaHQ9IjEwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWxsPSIjZjhmOWZhIi8+PHRleHQgeD0iNTAlIiB5PSI1MCUiIGZvbnQtZmFtaWx5PSJBcmlhbCwgc2Fucy1zZXJpZiIgZm9udC1zaXplPSIxNCIgZmlsbD0iIzZjNzU3ZCIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZHk9Ii4zZW0iPkltYWdlIG5vdCBmb3VuZDwvdGV4dD48L3N2Zz4='; this.alt='Image not found'; this.onclick=null; this.style.cursor='default';">
                    <div class="filename">${{filename}}</div>
                `;

                galleryGrid.appendChild(galleryItem);
            }});
        }}

        function scrollToImage(imageId) {{
            const imageElement = document.getElementById(imageId);
            if (imageElement) {{
                imageElement.scrollIntoView({{
                    behavior: 'smooth',
                    block: 'center'
                }});

                // Add highlight effect
                imageElement.style.boxShadow = '0 4px 20px rgba(0,123,255,0.5)';
                setTimeout(() => {{
                    imageElement.style.boxShadow = '0 2px 5px rgba(0,0,0,0.1)';
                }}, 2000);
            }}
        }}
        
        // Drag and Drop functionality for column reordering
        let draggedColumn = null;
        let draggedElement = null;

        function handleDragStart(e) {{
            draggedColumn = e.target.dataset.column;
            draggedElement = e.target;
            e.target.classList.add('dragging');
            e.dataTransfer.effectAllowed = 'move';
            e.dataTransfer.setData('text/html', e.target.outerHTML);
        }}

        function handleDragOver(e) {{
            if (e.preventDefault) {{
                e.preventDefault();
            }}
            e.dataTransfer.dropEffect = 'move';
            return false;
        }}

        function handleDragEnter(e) {{
            if (e.target.classList.contains('drop-zone') && e.target !== draggedElement) {{
                const rect = e.target.getBoundingClientRect();
                const midPoint = rect.left + rect.width / 2;
                const isLeft = e.clientX < midPoint;

                // Clear all indicators
                document.querySelectorAll('.drop-indicator').forEach(indicator => {{
                    indicator.classList.remove('show');
                }});

                // Show appropriate indicator
                const indicator = e.target.querySelector(isLeft ? '.drop-indicator.left' : '.drop-indicator.right');
                if (indicator) {{
                    indicator.classList.add('show');
                }}
            }}
        }}

        function handleDragLeave(e) {{
            // Only hide indicators if we're leaving the drop zone entirely
            if (!e.target.closest('.drop-zone')) {{
                document.querySelectorAll('.drop-indicator').forEach(indicator => {{
                    indicator.classList.remove('show');
                }});
            }}
        }}

        function handleDrop(e) {{
            if (e.stopPropagation) {{
                e.stopPropagation();
            }}

            if (draggedColumn && e.target.classList.contains('drop-zone') && e.target !== draggedElement) {{
                const targetColumn = e.target.dataset.column;
                const rect = e.target.getBoundingClientRect();
                const midPoint = rect.left + rect.width / 2;
                const isLeft = e.clientX < midPoint;

                reorderColumns(draggedColumn, targetColumn, isLeft);
            }}

            // Clear all indicators
            document.querySelectorAll('.drop-indicator').forEach(indicator => {{
                indicator.classList.remove('show');
            }});

            return false;
        }}

        function handleDragEnd(e) {{
            e.target.classList.remove('dragging');
            draggedColumn = null;
            draggedElement = null;

            // Clear all indicators
            document.querySelectorAll('.drop-indicator').forEach(indicator => {{
                indicator.classList.remove('show');
            }});
        }}

        function reorderColumns(draggedCol, targetCol, insertLeft) {{
            const draggedIndex = columnOrder.indexOf(draggedCol);
            const targetIndex = columnOrder.indexOf(targetCol);

            if (draggedIndex === -1 || targetIndex === -1) return;

            // Remove dragged column from its current position
            columnOrder.splice(draggedIndex, 1);

            // Calculate new insertion position
            let newTargetIndex = columnOrder.indexOf(targetCol);
            const insertIndex = insertLeft ? newTargetIndex : newTargetIndex + 1;

            // Insert at new position
            columnOrder.splice(insertIndex, 0, draggedCol);

            // Update display
            updateDisplay();
        }}

        // Close modal when clicking outside
        window.onclick = function(event) {{
            const modal = document.getElementById('contentModal');
            if (event.target === modal) {{
                closeModal();
            }}
        }}

        // Close image modal with Escape key
        document.addEventListener('keydown', function(event) {{
            if (event.key === 'Escape') {{
                const imageModal = document.getElementById('imageModal');
                const contentModal = document.getElementById('contentModal');
                if (imageModal.style.display === 'block') {{
                    closeImageModal();
                }} else if (contentModal.style.display === 'block') {{
                    closeModal();
                }}
            }}
        }});

        // Open journalctl view with configurable time window
        function openJournalctlView(row) {{
            // Find the timestamp column - try multiple common names
            const timestampColumns = ['timestamp', 'Timestamp_original', 'timestamp_results', 'timestamp_logs'];
            let timestamp = null;
            let timestampCol = null;

            for (const col of timestampColumns) {{
                if (row[col] !== null && row[col] !== undefined) {{
                    timestamp = row[col];
                    timestampCol = col;
                    break;
                }}
            }}

            if (!timestamp) {{
                alert('No timestamp found in this row');
                return;
            }}

            // Convert to Unix milliseconds if needed
            let timestampMs = null;
            // Check if it's a number (integer or float) - handles both "1759230172236" and "1759230172236.0"
            if (/^\\d+(\\.\\d+)?$/.test(String(timestamp).trim())) {{
                timestampMs = parseInt(parseFloat(String(timestamp).trim()));
            }} else if (typeof timestamp === 'number') {{
                // Already a number
                timestampMs = parseInt(timestamp);
            }} else {{
                // Try to parse as date string
                const dateStr = String(timestamp).replace(',', '.');
                const date = new Date(dateStr);
                if (!isNaN(date.getTime())) {{
                    timestampMs = date.getTime();
                }} else {{
                    alert('Could not parse timestamp: ' + timestamp);
                    return;
                }}
            }}

            // Prompt user for time window (default 5 seconds)
            const timeWindowInput = prompt('Enter time window in seconds (e.g., 5, 10, 60, or 0 for no filter):', '5');
            if (timeWindowInput === null) {{
                return; // User cancelled
            }}

            const timeWindowSeconds = parseFloat(timeWindowInput);
            if (isNaN(timeWindowSeconds) || timeWindowSeconds < 0) {{
                alert('Invalid time window. Please enter a positive number or 0.');
                return;
            }}

            // Calculate time window (convert seconds to milliseconds)
            const timeWindowMs = timeWindowSeconds * 1000;
            const startTime = timeWindowSeconds === 0 ? 0 : timestampMs - timeWindowMs;
            const endTime = timeWindowSeconds === 0 ? Number.MAX_SAFE_INTEGER : timestampMs + timeWindowMs;

            // Show loading message
            const loadingWindow = window.open('', '_blank', 'width=1200,height=800');
            loadingWindow.document.write('<html><body style="font-family: Arial; padding: 50px; text-align: center;"><h2>Loading journalctl logs...</h2><p>Please wait while we fetch the data.</p></body></html>');

            // Load and filter journalctl data
            // We'll use the journalctl_data variable that should be loaded separately
            if (typeof journalctlData === 'undefined') {{
                loadingWindow.document.write('<html><body style="font-family: Arial; padding: 50px;"><h2>Error</h2><p>Journalctl data not loaded. Please ensure journalctl_data.js exists in the parent directory.</p><p>Run process_all.bat to generate this file.</p></body></html>');
                return;
            }}

            // Filter rows by timestamp (or show all if time window is 0)
            const filteredRows = timeWindowSeconds === 0
                ? journalctlData
                : journalctlData.filter(row => {{
                    const rowTimestamp = parseInt(row.timestamp || '0');
                    return rowTimestamp >= startTime && rowTimestamp <= endTime;
                }});

            // Generate HTML for viewer
            const viewerHTML = generateJournalctlHTML(filteredRows, ['timestamp', 'hostname', 'program', 'pid', 'message'], timestampMs, startTime, endTime, timeWindowSeconds);

            // Write to the window
            loadingWindow.document.open();
            loadingWindow.document.write(viewerHTML);
            loadingWindow.document.close();
        }}


        // Generate HTML for journalctl viewer
        function generateJournalctlHTML(rows, headers, centerTime, startTime, endTime, timeWindowSeconds) {{
            const centerFormatted = formatTimestamp(String(centerTime));
            const startFormatted = timeWindowSeconds === 0 ? 'All logs' : formatTimestamp(String(startTime));
            const endFormatted = timeWindowSeconds === 0 ? 'All logs' : formatTimestamp(String(endTime));
            const titleTimeWindow = timeWindowSeconds === 0 ? 'All Logs' : `±${{timeWindowSeconds}}s`;

            let tableRows = '';
            rows.forEach(row => {{
                const isCenterRow = Math.abs(parseInt(row.timestamp) - centerTime) < 500;
                const rowClass = isCenterRow ? 'class="center-row"' : '';

                tableRows += '<tr ' + rowClass + '>';
                headers.forEach(header => {{
                    const value = row[header] || '';
                    const displayValue = header === 'timestamp' ? formatTimestamp(value) : escapeHtml(value);
                    tableRows += '<td>' + displayValue + '</td>';
                }});
                tableRows += '</tr>';
            }});

            return `<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Journalctl Logs ${{titleTimeWindow}}</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
        }}
        .header h1 {{
            margin: 0 0 10px 0;
        }}
        .time-range {{
            font-size: 14px;
            opacity: 0.9;
        }}
        .container {{
            background: white;
            border-radius: 8px;
            padding: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 13px;
        }}
        th, td {{
            padding: 8px;
            text-align: left;
            border: 1px solid #ddd;
            word-wrap: break-word;
        }}
        th {{
            background: #f8f9fa;
            font-weight: 600;
            position: sticky;
            top: 0;
            z-index: 100;
        }}
        tr:hover {{
            background: #f8f9fa;
        }}
        .center-row {{
            background: #fff3cd;
            border-left: 4px solid #ffc107;
            font-weight: bold;
        }}
        .stats {{
            margin-bottom: 15px;
            padding: 10px;
            background: #e9ecef;
            border-radius: 4px;
            font-size: 14px;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Journalctl System Logs</h1>
        <div class="time-range">
            <strong>Center Time:</strong> ${{centerFormatted}}<br>
            <strong>Time Range:</strong> ${{startFormatted}} to ${{endFormatted}} ${{timeWindowSeconds === 0 ? '' : `(±${{timeWindowSeconds}} seconds)`}}
        </div>
    </div>
    <div class="container">
        <div class="stats">
            Showing <strong>${{rows.length}}</strong> log entries
        </div>
        <table>
            <thead>
                <tr>
                    ${{headers.map(h => '<th>' + escapeHtml(h) + '</th>').join('')}}
                </tr>
            </thead>
            <tbody>
                ${{tableRows}}
            </tbody>
        </table>
    </div>
</body>
</html>`;
        }}

        function escapeHtml(text) {{
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }}
    </script>
</body>
</html>'''


def html_escape(text: str) -> str:
    """Escape HTML characters"""
    return (str(text)
            .replace('&', '&amp;')
            .replace('<', '&lt;')
            .replace('>', '&gt;')
            .replace('"', '&quot;')
            .replace("'", '&#x27;'))


def main():
    """Main function to process CSV files"""
    if len(sys.argv) < 2:
        print("Usage: python csv_analyzer.py <csv_file> [output_html]")
        print("   or: python csv_analyzer.py --batch <directory>")
        sys.exit(1)
        
    if sys.argv[1] == '--batch':
        # Batch process all combined CSV files
        if len(sys.argv) < 3:
            print("Usage: python csv_analyzer.py --batch <directory>")
            sys.exit(1)
            
        batch_directory = sys.argv[2]
        process_batch(batch_directory)
    else:
        # Single file processing
        csv_file = sys.argv[1]
        output_html = sys.argv[2] if len(sys.argv) > 2 else None
        
        if not output_html:
            output_html = str(Path(csv_file).with_suffix('.html'))
            
        process_single_file(csv_file, output_html)


def process_single_file(csv_file: str, output_html: str):
    """Process a single CSV file"""
    if not os.path.exists(csv_file):
        print(f"Error: CSV file not found: {csv_file}")
        sys.exit(1)
        
    try:
        analyzer = CSVToHTMLAnalyzer()
        analyzer.load_csv(csv_file)
        
        # Generate title from path
        csv_path = Path(csv_file)
        title = f"Test Analysis - {csv_path.parent.name} - {csv_path.stem}"
        
        analyzer.generate_html(output_html, title)
        print(f"Generated: {output_html}")
        
    except Exception as e:
        print(f"Error processing {csv_file}: {e}")
        import traceback
        traceback.print_exc()


def generate_journalctl_js(csv_file: str, output_js: str):
    """Convert journalctl CSV to JavaScript data file"""
    print(f"Generating journalctl data file: {output_js}")

    try:
        with open(csv_file, 'r', encoding='utf-8', newline='') as f:
            reader = csv.DictReader(f)
            rows = []

            for row in reader:
                # Only keep essential columns and convert to minimal format
                rows.append({
                    'timestamp': row.get('timestamp', ''),
                    'hostname': row.get('hostname', ''),
                    'program': row.get('program', ''),
                    'pid': row.get('pid', ''),
                    'message': row.get('message', '')
                })

        # Write as JavaScript file
        with open(output_js, 'w', encoding='utf-8') as f:
            f.write('// Journalctl data for test campaign\n')
            f.write('// Auto-generated by csv_analyzer.py\n')
            f.write('var journalctlData = ')
            json.dump(rows, f, indent=2)
            f.write(';\n')

        print(f"Generated journalctl_data.js with {len(rows)} entries")

    except Exception as e:
        print(f"Error generating journalctl data: {e}")
        import traceback
        traceback.print_exc()


def process_batch(directory: str):
    """Process all *combined.csv files in directory recursively"""
    base_path = Path(directory)
    if not base_path.exists():
        print(f"Error: Directory not found: {directory}")
        sys.exit(1)

    # Find all combined CSV files
    csv_files = list(base_path.rglob("*combined.csv"))

    if not csv_files:
        print(f"No *combined.csv files found in {directory}")
        return

    print(f"Found {len(csv_files)} combined CSV files")

    # Find and generate journalctl_data.js for each test campaign
    test_campaigns = set()
    for csv_file in csv_files:
        # Find the test campaign root (contains system_status folder)
        for parent in csv_file.parents:
            system_status = parent / 'system_status'
            if system_status.exists():
                test_campaigns.add(parent)
                break

    # Generate journalctl_data.js for each campaign
    for campaign_dir in test_campaigns:
        # Try both naming patterns
        journalctl_csv = campaign_dir / 'system_status' / 'journalctl_logs.csv'
        if not journalctl_csv.exists():
            journalctl_csv = campaign_dir / 'system_status' / 'journalctl_journalctl.csv'

        if journalctl_csv.exists():
            output_js = campaign_dir / 'journalctl_data.js'
            generate_journalctl_js(str(journalctl_csv), str(output_js))

    for csv_file in csv_files:
        try:
            # Generate HTML in same directory as CSV
            output_html = csv_file.with_name(f"{csv_file.stem}_analyzer.html")

            analyzer = CSVToHTMLAnalyzer()
            analyzer.load_csv(str(csv_file))

            # Generate title from path structure
            parts = csv_file.parts
            if len(parts) >= 2:
                title = f"Test Analysis - {parts[-2]} - {csv_file.stem}"
            else:
                title = f"Test Analysis - {csv_file.stem}"

            analyzer.generate_html(str(output_html), title)
            print(f"Generated: {output_html}")

        except Exception as e:
            print(f"Error processing {csv_file}: {e}")
            continue

    print(f"\\nBatch processing complete!")


if __name__ == "__main__":
    main()