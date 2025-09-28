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
        
    def load_csv(self, csv_path: str) -> None:
        """Load CSV data and analyze column types"""
        print(f"Loading CSV: {csv_path}")
        
        with open(csv_path, 'r', encoding='utf-8', newline='') as f:
            # Try to detect dialect, fallback to standard CSV
            sample = f.read(8192)
            f.seek(0)
            
            try:
                dialect = csv.Sniffer().sniff(sample)
            except csv.Error:
                # Fallback to standard CSV format
                dialect = csv.excel
            
            reader = csv.DictReader(f, dialect=dialect)
            self.columns = reader.fieldnames or []
            
            # Load all data
            for row_idx, row in enumerate(reader):
                # Convert empty strings to None for cleaner display
                cleaned_row = {}
                for key, value in row.items():
                    if value == '':
                        cleaned_row[key] = None
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
            formatted_ts = self._format_timestamp(value_str)
            if formatted_ts != value_str:  # Only show formatted if different
                value_str = formatted_ts
        
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
        
        html_content = self._generate_html_template(title, js_data, column_groups)
        
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
        
    def _generate_html_template(self, title: str, js_data: List[Dict], column_groups: Dict[str, List[str]]) -> str:
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
        }}
        
        .sortable:hover {{
            background: #e9ecef;
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
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{html_escape(title)}</h1>
        </div>
        
        <div class="controls">
            <div class="control-section">
                <h3>Global Controls</h3>
                <div class="global-controls">
                    <input type="text" class="global-search" placeholder="Global search..." onkeyup="applyFilters()">
                    <button class="btn" onclick="clearAllFilters()">Clear Filters</button>
                    <button class="btn btn-secondary" onclick="exportData()">Export Data</button>
                </div>
                
                <div class="presets">
                    <select class="preset-select" onchange="loadPreset(this.value)">
                        <option value="">Select Preset...</option>
                        <option value="default">Default View</option>
                        <option value="results-only">Results Only</option>
                        <option value="logs-only">Logs Only</option>
                        <option value="errors-warnings">Errors & Warnings</option>
                    </select>
                    <button class="btn btn-secondary" onclick="savePreset()">Save Preset</button>
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
    </div>
    
    <!-- Modal for expanded content -->
    <div id="contentModal" class="modal">
        <div class="modal-content">
            <span class="close" onclick="closeModal()">&times;</span>
            <h3>Content Detail</h3>
            <pre id="modal-content"></pre>
        </div>
    </div>
    
    <script>
        // Data and state
        const data = {json.dumps(js_data, indent=2)};
        const columns = {json.dumps(self.columns)};
        const columnTypes = {json.dumps(self.column_types)};
        
        let filteredData = [...data];
        let visibleColumns = new Set(['Pass', 'timestamp', 'message', 'command_method']);
        let sortColumn = null;
        let sortDirection = 'asc';
        let filters = {{}};
        
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
            updateDisplay();
        }});
        
        function initializeTable() {{
            updateTableHeaders();
        }}
        
        function updateTableHeaders() {{
            const headerRow = document.getElementById('table-header');
            headerRow.innerHTML = '';
            
            columns.forEach(col => {{
                if (visibleColumns.has(col)) {{
                    const th = document.createElement('th');
                    th.className = 'sortable';
                    th.onclick = () => sortBy(col);
                    
                    const sortIndicator = sortColumn === col ? 
                        (sortDirection === 'asc' ? '↑' : '↓') : '↕';
                    
                    th.innerHTML = `${{col}} <span class="sort-indicator">${{sortIndicator}}</span>`;
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
                
                columns.forEach(col => {{
                    if (visibleColumns.has(col)) {{
                        const td = document.createElement('td');
                        let value = row[col];
                        
                        if (value !== null && value !== undefined) {{
                            let valueStr = String(value);
                            
                            // Format timestamp columns
                            if (columnTypes[col] === 'timestamp') {{
                                const formatted = formatTimestamp(valueStr);
                                if (formatted !== valueStr) {{
                                    valueStr = formatted;
                                }}
                            }}
                            
                            if (valueStr.length > 200) {{
                                td.innerHTML = `<span class="cell-content expandable" onclick="showModal('${{col}}', this)" data-full="${{valueStr}}">${{valueStr.substring(0, 197)}}...</span>`;
                            }} else {{
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
            
            document.getElementById('row-count').textContent = `Showing ${{totalRows}} of ${{data.length}} rows`;
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
            updateDisplay();
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
            
            updateDisplay();
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
            document.querySelectorAll('[data-filter-column]').forEach(input => {{
                if (input.tagName === 'SELECT') {{
                    input.selectedIndex = -1;
                }} else {{
                    input.value = '';
                }}
            }});
            
            filters = {{}};
            filteredData = [...data];
            updateDisplay();
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
        
        function loadPreset(presetName) {{
            if (!presetName) return;
            
            const presets = {{
                'default': {{
                    columns: ['Pass', 'timestamp', 'message', 'command_method', 'level'],
                    filters: {{}}
                }},
                'results-only': {{
                    columns: ['Pass', 'timestamp', 'command_method', 'peak_amplitude', 'peak_frequency'],
                    filters: {{ '_is_result': true }}
                }},
                'logs-only': {{
                    columns: ['timestamp', 'level', 'message', 'line_number'],
                    filters: {{ '_is_result': false }}
                }},
                'errors-warnings': {{
                    columns: ['timestamp', 'level', 'message', 'line_number'],
                    filters: {{ 'level': ['ERROR', 'WARNING'] }}
                }}
            }};
            
            const preset = presets[presetName];
            if (preset) {{
                // Set visible columns
                visibleColumns.clear();
                preset.columns.forEach(col => {{
                    if (columns.includes(col)) {{
                        visibleColumns.add(col);
                    }}
                }});
                
                // Update checkboxes
                document.querySelectorAll('input[data-column]').forEach(cb => {{
                    cb.checked = visibleColumns.has(cb.dataset.column);
                }});
                
                // Apply preset filters
                clearAllFilters();
                if (preset.filters._is_result !== undefined) {{
                    filteredData = data.filter(row => row._is_result === preset.filters._is_result);
                }}
                if (preset.filters.level) {{
                    const levelSelect = document.querySelector('select[data-filter-column="level"]');
                    if (levelSelect) {{
                        preset.filters.level.forEach(level => {{
                            const option = levelSelect.querySelector(`option[value="${{level}}"]`);
                            if (option) option.selected = true;
                        }});
                    }}
                }}
                
                updateDisplay();
            }}
        }}
        
        function savePreset() {{
            const presetName = prompt('Enter preset name:');
            if (presetName) {{
                const preset = {{
                    columns: Array.from(visibleColumns),
                    filters: filters
                }};
                localStorage.setItem(`preset_${{presetName}}`, JSON.stringify(preset));
                alert('Preset saved!');
            }}
        }}
        
        function showModal(column, element) {{
            const fullContent = element.dataset.full || element.textContent;
            document.getElementById('modal-content').textContent = fullContent;
            document.getElementById('contentModal').style.display = 'block';
        }}
        
        function closeModal() {{
            document.getElementById('contentModal').style.display = 'none';
        }}
        
        function exportData() {{
            const csvContent = [
                columns.filter(col => visibleColumns.has(col)).join(','),
                ...filteredData.map(row => 
                    columns.filter(col => visibleColumns.has(col))
                           .map(col => `"${{String(row[col] || '').replace(/"/g, '""')}}"`)
                           .join(',')
                )
            ].join('\\n');
            
            const blob = new Blob([csvContent], {{ type: 'text/csv' }});
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'filtered_data.csv';
            a.click();
            window.URL.revokeObjectURL(url);
        }}
        
        // Close modal when clicking outside
        window.onclick = function(event) {{
            const modal = document.getElementById('contentModal');
            if (event.target === modal) {{
                closeModal();
            }}
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
        print(f"✓ Generated: {output_html}")
        
    except Exception as e:
        print(f"Error processing {csv_file}: {e}")
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
            print(f"✓ Generated: {output_html}")
            
        except Exception as e:
            print(f"✗ Error processing {csv_file}: {e}")
            continue
            
    print(f"\\n✓ Batch processing complete!")


if __name__ == "__main__":
    main()