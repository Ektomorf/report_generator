#!/usr/bin/env python3
"""
Log to CSV converter and HTML viewer generator.
Converts test log files to CSV and creates an interactive HTML table with filtering and column controls.
"""

import json
import csv
import re
import os
import argparse
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

# Import presets configuration
try:
    from log_viewer_presets import get_presets_for_test_type, get_default_column_order
except ImportError:
    # Fallback if presets file doesn't exist
    def get_presets_for_test_type(test_name=None):
        return {
            'basic': ['timestamp', 'command_method', 'command_str'],
            'detailed': ['timestamp', 'command_method', 'command_str', 'raw_response', 'parsed_response'],
            'network': ['timestamp', 'command_method', 'raw_response'],
            'all': []
        }

    def get_default_column_order(available_columns):
        # Put timestamp first, then sort the rest
        if 'timestamp' in available_columns:
            ordered = ['timestamp'] + [col for col in sorted(available_columns) if col != 'timestamp']
        else:
            ordered = sorted(available_columns)
        return ordered

def parse_log_line(line: str) -> Optional[Dict[str, Any]]:
    """Parse a single log line into structured data."""
    import re

    # Pattern: timestamp - level - json_data
    # Support both formats: "HH:MM:SS" and "YYYY-MM-DD HH:MM:SS,mmm"
    patterns = [
        r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}) - (\w+) - (.+)$',  # Full timestamp with milliseconds
        r'^(\d{2}:\d{2}:\d{2}) - (\w+) - (.+)$'  # Time only
    ]

    match = None
    for pattern in patterns:
        match = re.match(pattern, line.strip())
        if match:
            break

    if not match:
        return None

    timestamp, level, json_str = match.groups()

    try:
        # Parse the JSON data - handle multiple formats
        data = None

        # Method 1: Try standard JSON parsing
        try:
            data = json.loads(json_str)
        except json.JSONDecodeError:
            pass

        # Method 2: Try with single quotes converted to double quotes
        if data is None:
            try:
                # Convert single quotes to double quotes for JSON compatibility
                json_fixed = json_str.replace("'", '"')
                data = json.loads(json_fixed)
            except json.JSONDecodeError:
                pass

        # Method 3: Try ast.literal_eval for Python dict format
        if data is None:
            try:
                # Clean up the JSON string to handle unparseable object representations
                cleaned_json_str = json_str

                # Replace object representations with empty strings to allow parsing
                import re
                cleaned_json_str = re.sub(r'<[^>]*object at 0x[0-9a-f]+>', '""', cleaned_json_str)

                # Try using literal_eval for single-quoted dictionaries
                import ast
                data = ast.literal_eval(cleaned_json_str)
            except (ValueError, SyntaxError):
                pass

        # Method 4: Last resort - try to extract key-value pairs manually
        if data is None:
            try:
                # Simple regex-based extraction for basic dict patterns
                import re
                # Look for key: value patterns
                pairs = re.findall(r"'([^']+)':\s*'([^']*)'", json_str)
                if pairs:
                    data = dict(pairs)
                else:
                    # If all parsing fails, create a minimal record
                    data = {'raw_log_data': json_str}
            except Exception:
                # Final fallback
                data = {'raw_log_data': json_str}

        if data is None:
            return None

        # Create flattened record
        record = {
            'timestamp': timestamp,
            'level': level,
        }

        # Flatten the JSON data
        def flatten_dict(d: Dict, prefix: str = '') -> Dict:
            items = []
            for k, v in d.items():
                new_key = f"{prefix}_{k}" if prefix else k
                if isinstance(v, dict):
                    items.extend(flatten_dict(v, new_key).items())
                elif isinstance(v, list):
                    # Convert lists to strings for CSV compatibility
                    items.append((new_key, json.dumps(v)))
                else:
                    items.append((new_key, str(v) if v is not None else ''))
            return dict(items)

        flattened = flatten_dict(data)
        record.update(flattened)

        return record

    except (json.JSONDecodeError, ValueError, SyntaxError):
        # If JSON parsing fails, store as raw text but also try to extract basic info
        record = {
            'timestamp': timestamp,
            'level': level,
            'raw_log': json_str
        }

        # Try to extract command_method if it appears in the raw string
        import re
        method_match = re.search(r"'command_method':\s*'([^']+)'", json_str)
        if method_match:
            record['command_method'] = method_match.group(1)

        # Try to extract log_type if it appears in the raw string
        type_match = re.search(r"'log_type':\s*'([^']+)'", json_str)
        if type_match:
            record['log_type'] = type_match.group(1)

        return record

def convert_log_to_csv(log_file: Path, csv_file: Path) -> List[str]:
    """Convert log file to CSV format and return column names."""
    records = []
    all_columns = set(['timestamp', 'level'])

    with open(log_file, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            record = parse_log_line(line)
            if record:
                records.append(record)
                all_columns.update(record.keys())

    # Use intelligent column ordering (timestamp first, then logical order)
    columns = get_default_column_order(list(all_columns))

    # Write CSV
    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        for record in records:
            # Fill missing columns with empty strings
            filled_record = {col: record.get(col, '') for col in columns}
            writer.writerow(filled_record)

    return columns

def generate_enhanced_html_viewer(log_csv_file: Path, results_csv_file: Path, html_file: Path, log_columns: List[str], results_columns: List[str]) -> None:
    """Generate interactive HTML viewer that includes both log and results CSV data."""

    # Read log CSV data
    log_csv_data = ""
    if log_csv_file and log_csv_file.exists():
        with open(log_csv_file, 'r', encoding='utf-8') as f:
            log_csv_data = f.read()

    # Read results CSV data
    results_csv_data = ""
    if results_csv_file and results_csv_file.exists():
        with open(results_csv_file, 'r', encoding='utf-8') as f:
            results_csv_data = f.read()

    # Escape CSV data for JavaScript
    log_csv_escaped = log_csv_data.replace('\\', '\\\\').replace('`', '\\`').replace('${', '\\${')
    results_csv_escaped = results_csv_data.replace('\\', '\\\\').replace('`', '\\`').replace('${', '\\${')

    # Get test name for presets
    test_name = log_csv_file.stem if log_csv_file else "unknown"
    presets = get_presets_for_test_type(test_name)
    presets['all_logs'] = log_columns
    presets['all_results'] = results_columns

    html_content = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Enhanced Log Viewer - {test_name}</title>
    <style>
        * {{
            box-sizing: border-box;
        }}

        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
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
            background: #2c3e50;
            color: white;
            padding: 20px;
        }}

        .header h1 {{
            margin: 0 0 10px 0;
            font-size: 24px;
        }}

        .tab-container {{
            background: #ecf0f1;
            display: flex;
            border-bottom: 1px solid #bdc3c7;
        }}

        .tab {{
            padding: 15px 20px;
            background: #ecf0f1;
            cursor: pointer;
            border: none;
            font-size: 16px;
            font-weight: 600;
            color: #2c3e50;
            transition: background-color 0.2s;
        }}

        .tab:hover {{
            background: #d5dbdb;
        }}

        .tab.active {{
            background: #3498db;
            color: white;
        }}

        .tab-content {{
            display: none;
            padding: 20px;
        }}

        .tab-content.active {{
            display: block;
        }}

        .controls {{
            background: #ecf0f1;
            padding: 20px;
            border-bottom: 1px solid #bdc3c7;
        }}

        .control-group {{
            margin-bottom: 15px;
        }}

        .control-group:last-child {{
            margin-bottom: 0;
        }}

        .control-group label {{
            display: block;
            margin-bottom: 5px;
            font-weight: 600;
            color: #2c3e50;
        }}

        .preset-buttons {{
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
            margin-bottom: 15px;
        }}

        .preset-btn {{
            padding: 8px 16px;
            background: #3498db;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 14px;
            transition: background-color 0.2s;
        }}

        .preset-btn:hover {{
            background: #2980b9;
        }}

        .preset-btn.active {{
            background: #27ae60;
        }}

        input[type="text"], input[type="number"], select {{
            width: 100%;
            padding: 8px;
            border: 1px solid #bdc3c7;
            border-radius: 4px;
            font-size: 14px;
        }}

        .checkbox-group {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
            gap: 10px;
            max-height: 200px;
            overflow-y: auto;
            padding: 10px;
            border: 1px solid #bdc3c7;
            border-radius: 4px;
            background: white;
        }}

        .checkbox-item {{
            display: flex;
            align-items: center;
            gap: 8px;
        }}

        .checkbox-item input[type="checkbox"] {{
            width: auto;
        }}

        .table-container {{
            overflow: auto;
            max-height: 80vh;
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 12px;
        }}

        th, td {{
            border: 1px solid #ddd;
            padding: 8px;
            text-align: left;
            white-space: nowrap;
        }}

        th {{
            background-color: #f8f9fa;
            font-weight: 600;
            position: sticky;
            top: 0;
            z-index: 10;
        }}

        tr:nth-child(even) {{
            background-color: #f8f9fa;
        }}

        tr:hover {{
            background-color: #e3f2fd;
        }}

        .expandable-cell {{
            max-width: 300px;
            overflow: hidden;
            text-overflow: ellipsis;
            cursor: pointer;
            position: relative;
        }}

        .expandable-cell.expanded {{
            white-space: normal;
            word-wrap: break-word;
            max-width: none;
        }}

        .expand-indicator {{
            color: #3498db;
            font-weight: bold;
            margin-left: 5px;
        }}

        .stats {{
            background: #e8f5e8;
            padding: 10px;
            margin-bottom: 20px;
            border-radius: 4px;
            border-left: 4px solid #27ae60;
        }}

        .summary-stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }}

        .stat-card {{
            background: #f8f9fa;
            padding: 15px;
            border-radius: 6px;
            text-align: center;
            border: 1px solid #e9ecef;
        }}

        .stat-number {{
            font-size: 24px;
            font-weight: bold;
            color: #2c3e50;
        }}

        .stat-label {{
            font-size: 14px;
            color: #6c757d;
            margin-top: 5px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Enhanced Log Viewer</h1>
            <p>Test: {test_name}</p>
        </div>

        <div class="tab-container">
            <button class="tab active" onclick="switchTab('logs')">Log Data</button>
            <button class="tab" onclick="switchTab('results')">Results Data</button>
        </div>

        <div id="logs-tab" class="tab-content active">
            <div class="controls">
                <div class="control-group">
                    <label>Quick Presets:</label>
                    <div class="preset-buttons" id="log-presets">
                        <!-- Preset buttons will be populated by JavaScript -->
                    </div>
                </div>

                <div class="control-group">
                    <label for="log-search">Search:</label>
                    <input type="text" id="log-search" placeholder="Search in any column...">
                </div>

                <div class="control-group">
                    <label for="log-column-filter">Show/Hide Columns:</label>
                    <div class="checkbox-group" id="log-column-checkboxes">
                        <!-- Column checkboxes will be populated by JavaScript -->
                    </div>
                </div>
            </div>

            <div class="stats" id="log-stats">
                <!-- Stats will be populated by JavaScript -->
            </div>

            <div class="table-container">
                <table id="log-table">
                    <thead id="log-table-head"></thead>
                    <tbody id="log-table-body"></tbody>
                </table>
            </div>
        </div>

        <div id="results-tab" class="tab-content">
            <div class="controls">
                <div class="control-group">
                    <label>Quick Presets:</label>
                    <div class="preset-buttons" id="results-presets">
                        <!-- Preset buttons will be populated by JavaScript -->
                    </div>
                </div>

                <div class="control-group">
                    <label for="results-search">Search:</label>
                    <input type="text" id="results-search" placeholder="Search in any column...">
                </div>

                <div class="control-group">
                    <label for="results-column-filter">Show/Hide Columns:</label>
                    <div class="checkbox-group" id="results-column-checkboxes">
                        <!-- Column checkboxes will be populated by JavaScript -->
                    </div>
                </div>
            </div>

            <div class="stats" id="results-stats">
                <!-- Stats will be populated by JavaScript -->
            </div>

            <div class="table-container">
                <table id="results-table">
                    <thead id="results-table-head"></thead>
                    <tbody id="results-table-body"></tbody>
                </table>
            </div>
        </div>
    </div>

    <script>
        // Embedded CSV data
        const logCsvData = `{log_csv_escaped}`;
        const resultsCsvData = `{results_csv_escaped}`;

        // Presets configuration
        const presets = {json.dumps(presets, indent=8)};

        let logData = [];
        let resultsData = [];
        let logColumns = [];
        let resultsColumns = [];
        let logVisibleColumns = [];
        let resultsVisibleColumns = [];

        // Parse CSV data
        function parseCSV(csvText) {{
            if (!csvText.trim()) return [[], []];

            const lines = csvText.trim().split('\\n');
            if (lines.length === 0) return [[], []];

            const headers = lines[0].split(',').map(h => h.replace(/^"|"$/g, ''));
            const data = [];

            for (let i = 1; i < lines.length; i++) {{
                const line = lines[i];
                if (line.trim()) {{
                    const values = parseCSVLine(line);
                    if (values.length === headers.length) {{
                        const row = {{}};
                        headers.forEach((header, index) => {{
                            row[header] = values[index] || '';
                        }});
                        data.push(row);
                    }}
                }}
            }}

            return [headers, data];
        }}

        function parseCSVLine(line) {{
            const result = [];
            let current = '';
            let inQuotes = false;

            for (let i = 0; i < line.length; i++) {{
                const char = line[i];

                if (char === '"') {{
                    if (inQuotes && line[i + 1] === '"') {{
                        current += '"';
                        i++; // Skip next quote
                    }} else {{
                        inQuotes = !inQuotes;
                    }}
                }} else if (char === ',' && !inQuotes) {{
                    result.push(current);
                    current = '';
                }} else {{
                    current += char;
                }}
            }}

            result.push(current);
            return result;
        }}

        // Initialize data
        [logColumns, logData] = parseCSV(logCsvData);
        [resultsColumns, resultsData] = parseCSV(resultsCsvData);
        logVisibleColumns = [...logColumns];
        resultsVisibleColumns = [...resultsColumns];

        // Tab switching
        function switchTab(tabName) {{
            document.querySelectorAll('.tab').forEach(tab => tab.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));

            document.querySelector(`[onclick="switchTab('${{tabName}}')"]`).classList.add('active');
            document.getElementById(`${{tabName}}-tab`).classList.add('active');

            if (tabName === 'logs') {{
                updateLogTable();
            }} else if (tabName === 'results') {{
                updateResultsTable();
            }}
        }}

        // Update tables
        function updateLogTable() {{
            updateTable('log', logData, logColumns, logVisibleColumns);
            updateStats('log', logData);
        }}

        function updateResultsTable() {{
            updateTable('results', resultsData, resultsColumns, resultsVisibleColumns);
            updateStats('results', resultsData);
        }}

        function updateTable(type, data, allColumns, visibleColumns) {{
            const searchTerm = document.getElementById(`${{type}}-search`).value.toLowerCase();
            const tableHead = document.getElementById(`${{type}}-table-head`);
            const tableBody = document.getElementById(`${{type}}-table-body`);

            // Filter data based on search
            const filteredData = data.filter(row => {{
                return Object.values(row).some(value =>
                    String(value).toLowerCase().includes(searchTerm)
                );
            }});

            // Create header
            tableHead.innerHTML = '';
            const headerRow = document.createElement('tr');
            visibleColumns.forEach(column => {{
                const th = document.createElement('th');
                th.textContent = column;
                headerRow.appendChild(th);
            }});
            tableHead.appendChild(headerRow);

            // Create body
            tableBody.innerHTML = '';
            filteredData.forEach(row => {{
                const tr = document.createElement('tr');
                visibleColumns.forEach(column => {{
                    const td = document.createElement('td');
                    const value = String(row[column] || '');

                    if (value.length > 100) {{
                        td.className = 'expandable-cell';
                        td.innerHTML = value.substring(0, 100) + '<span class="expand-indicator">...</span>';
                        td.onclick = () => toggleCellExpansion(td, value);
                    }} else {{
                        td.textContent = value;
                    }}

                    tr.appendChild(td);
                }});
                tableBody.appendChild(tr);
            }});
        }}

        function updateStats(type, data) {{
            const statsDiv = document.getElementById(`${{type}}-stats`);
            const searchTerm = document.getElementById(`${{type}}-search`).value.toLowerCase();

            const filteredData = data.filter(row => {{
                return Object.values(row).some(value =>
                    String(value).toLowerCase().includes(searchTerm)
                );
            }});

            statsDiv.innerHTML = `
                <div class="summary-stats">
                    <div class="stat-card">
                        <div class="stat-number">${{filteredData.length}}</div>
                        <div class="stat-label">Visible Rows</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">${{data.length}}</div>
                        <div class="stat-label">Total Rows</div>
                    </div>
                </div>
            `;
        }}

        function toggleCellExpansion(cell, fullValue) {{
            if (cell.classList.contains('expanded')) {{
                cell.innerHTML = fullValue.substring(0, 100) + '<span class="expand-indicator">...</span>';
                cell.classList.remove('expanded');
            }} else {{
                cell.textContent = fullValue;
                cell.classList.add('expanded');
            }}
        }}

        // Initialize page
        function init() {{
            // Setup log controls
            setupControls('log', logColumns, logVisibleColumns, presets);
            setupControls('results', resultsColumns, resultsVisibleColumns, presets);

            // Initial table render
            updateLogTable();
            updateResultsTable();

            // Setup search listeners
            document.getElementById('log-search').addEventListener('input', updateLogTable);
            document.getElementById('results-search').addEventListener('input', updateResultsTable);
        }}

        function setupControls(type, allColumns, visibleColumns, presets) {{
            // Setup presets
            const presetsDiv = document.getElementById(`${{type}}-presets`);
            Object.keys(presets).forEach(presetName => {{
                const button = document.createElement('button');
                button.className = 'preset-btn';
                button.textContent = presetName.charAt(0).toUpperCase() + presetName.slice(1);
                button.onclick = () => applyPreset(type, presetName, allColumns, visibleColumns);
                presetsDiv.appendChild(button);
            }});

            // Setup column checkboxes
            const checkboxDiv = document.getElementById(`${{type}}-column-checkboxes`);
            allColumns.forEach(column => {{
                const div = document.createElement('div');
                div.className = 'checkbox-item';

                const checkbox = document.createElement('input');
                checkbox.type = 'checkbox';
                checkbox.id = `${{type}}-col-${{column}}`;
                checkbox.checked = visibleColumns.includes(column);
                checkbox.onchange = () => toggleColumn(type, column);

                const label = document.createElement('label');
                label.htmlFor = `${{type}}-col-${{column}}`;
                label.textContent = column;

                div.appendChild(checkbox);
                div.appendChild(label);
                checkboxDiv.appendChild(div);
            }});
        }}

        function applyPreset(type, presetName, allColumns, visibleColumns) {{
            const presetColumns = presets[presetName] || allColumns;

            if (type === 'log') {{
                logVisibleColumns = presetColumns.length > 0 ? presetColumns : allColumns;
                updateColumnCheckboxes('log', logColumns, logVisibleColumns);
                updateLogTable();
            }} else if (type === 'results') {{
                resultsVisibleColumns = presetColumns.length > 0 ? presetColumns : allColumns;
                updateColumnCheckboxes('results', resultsColumns, resultsVisibleColumns);
                updateResultsTable();
            }}

            // Update active preset button
            document.querySelectorAll(`#${{type}}-presets .preset-btn`).forEach(btn => {{
                btn.classList.remove('active');
            }});
            event.target.classList.add('active');
        }}

        function toggleColumn(type, column) {{
            if (type === 'log') {{
                const index = logVisibleColumns.indexOf(column);
                if (index > -1) {{
                    logVisibleColumns.splice(index, 1);
                }} else {{
                    logVisibleColumns.push(column);
                }}
                updateLogTable();
            }} else if (type === 'results') {{
                const index = resultsVisibleColumns.indexOf(column);
                if (index > -1) {{
                    resultsVisibleColumns.splice(index, 1);
                }} else {{
                    resultsVisibleColumns.push(column);
                }}
                updateResultsTable();
            }}
        }}

        function updateColumnCheckboxes(type, allColumns, visibleColumns) {{
            allColumns.forEach(column => {{
                const checkbox = document.getElementById(`${{type}}-col-${{column}}`);
                if (checkbox) {{
                    checkbox.checked = visibleColumns.includes(column);
                }}
            }});
        }}

        // Initialize when page loads
        document.addEventListener('DOMContentLoaded', init);
    </script>
</body>
</html>'''

    # Write the HTML file
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(html_content)

def generate_html_viewer(csv_file: Path, html_file: Path, columns: List[str]) -> None:
    """Generate interactive HTML viewer for the CSV data."""

    # Check if there's a corresponding results file
    results_csv_file = csv_file.parent / f"{csv_file.stem}_results.csv"

    if results_csv_file.exists():
        # Use enhanced viewer with both log and results data
        try:
            import csv as csv_module
            with open(results_csv_file, 'r', encoding='utf-8') as f:
                reader = csv_module.reader(f)
                results_columns = next(reader, [])
            generate_enhanced_html_viewer(csv_file, results_csv_file, html_file, columns, results_columns)
            return
        except Exception as e:
            print(f"Warning: Could not read results file {results_csv_file}: {e}")
            # Fall back to standard viewer

    # Standard single-file viewer (existing code)
    # Read CSV data to embed directly in HTML
    with open(csv_file, 'r', encoding='utf-8') as f:
        csv_data = f.read()

    # Escape the CSV data for embedding in JavaScript template literal
    csv_data_escaped = csv_data.replace('\\', '\\\\').replace('`', '\\`').replace('${', '\\${')

    # Get presets from configuration, with fallback to 'all' preset
    test_name = csv_file.stem  # Extract test name from filename
    presets = get_presets_for_test_type(test_name)
    presets['all'] = columns  # Always include 'all' preset with current columns

    html_content = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Log Viewer - {csv_file.stem}</title>
    <style>
        * {{
            box-sizing: border-box;
        }}

        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
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
            background: #2c3e50;
            color: white;
            padding: 20px;
        }}

        .header h1 {{
            margin: 0 0 10px 0;
            font-size: 24px;
        }}

        .controls {{
            background: #ecf0f1;
            padding: 20px;
            border-bottom: 1px solid #bdc3c7;
        }}

        .control-group {{
            margin-bottom: 15px;
        }}

        .control-group:last-child {{
            margin-bottom: 0;
        }}

        .control-group label {{
            display: block;
            margin-bottom: 5px;
            font-weight: 600;
            color: #2c3e50;
        }}

        .preset-buttons {{
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
            margin-bottom: 15px;
        }}

        .preset-btn {{
            padding: 8px 16px;
            background: #3498db;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 14px;
            transition: background-color 0.2s;
        }}

        .preset-btn:hover {{
            background: #2980b9;
        }}

        .preset-btn.active {{
            background: #27ae60;
        }}

        .search-input {{
            width: 100%;
            padding: 10px;
            border: 1px solid #bdc3c7;
            border-radius: 4px;
            font-size: 14px;
        }}

        .filter-options {{
            margin-top: 10px;
            padding: 10px;
            background: #f8f9fa;
            border-radius: 4px;
            border: 1px solid #e9ecef;
        }}

        .filter-row {{
            display: flex;
            align-items: center;
            margin-bottom: 8px;
            gap: 10px;
            flex-wrap: wrap;
        }}

        .filter-row:last-child {{
            margin-bottom: 0;
        }}

        .filter-input {{
            padding: 5px 8px;
            border: 1px solid #ced4da;
            border-radius: 3px;
            font-size: 12px;
            width: 120px;
        }}

        .filter-select {{
            padding: 5px;
            border: 1px solid #ced4da;
            border-radius: 3px;
            font-size: 12px;
        }}

        .filter-label {{
            font-size: 12px;
            font-weight: 600;
            color: #495057;
            min-width: 80px;
        }}

        .filter-toggle {{
            display: flex;
            align-items: center;
            gap: 5px;
            font-size: 12px;
        }}

        .column-controls {{
            max-height: 300px;
            overflow-y: auto;
            border: 1px solid #bdc3c7;
            border-radius: 4px;
            padding: 10px;
            background: white;
        }}

        .column-item {{
            display: flex;
            align-items: center;
            padding: 8px 5px;
            border-bottom: 1px solid #ecf0f1;
            cursor: move;
            background: white;
            margin-bottom: 2px;
            border-radius: 3px;
            transition: all 0.2s ease;
        }}

        .column-item:last-child {{
            border-bottom: 1px solid #ecf0f1;
        }}

        .column-item:hover {{
            background: #f8f9fa;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}

        .column-item.dragging {{
            opacity: 0.5;
            transform: rotate(2deg);
        }}

        .column-item.drag-over {{
            border-top: 3px solid #3498db;
        }}

        .column-item input[type="checkbox"] {{
            margin-right: 10px;
        }}

        .column-item label {{
            flex: 1;
            margin: 0;
            cursor: pointer;
            font-weight: normal;
        }}

        .drag-handle {{
            margin-right: 8px;
            color: #95a5a6;
            cursor: move;
            font-size: 14px;
        }}

        .drag-handle:hover {{
            color: #3498db;
        }}

        .column-order-info {{
            background: #e8f5e8;
            padding: 8px;
            margin-bottom: 10px;
            border-radius: 4px;
            font-size: 12px;
            color: #2d5a2d;
        }}

        .table-info {{
            background: #e3f2fd;
            padding: 8px;
            margin-bottom: 10px;
            border-radius: 4px;
            font-size: 12px;
            color: #1565c0;
        }}

        .table-container {{
            overflow-x: auto;
            max-height: 80vh;
            overflow-y: auto;
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            background: white;
        }}

        th, td {{
            padding: 8px 6px;
            text-align: left;
            border-bottom: 1px solid #ecf0f1;
            font-size: 12px;
            position: relative;
        }}

        td {{
            max-width: 500px;
            overflow: hidden;
            cursor: pointer;
        }}

        td.collapsed {{
            white-space: nowrap;
            text-overflow: ellipsis;
        }}

        td.expanded {{
            white-space: pre-wrap;
            word-break: break-word;
            max-width: none;
            background-color: #f8f9fa;
            border: 2px solid #007bff;
            z-index: 5;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }}

        td:hover {{
            background-color: #f1f3f4;
        }}

        td.collapsed::after {{
            content: " 📄";
            color: #6c757d;
            font-size: 10px;
            opacity: 0.7;
        }}

        td.expanded::after {{
            content: " 📖";
            color: #007bff;
            font-size: 10px;
        }}

        /* Hide expand indicators for empty cells */
        td.collapsed:empty::after,
        td.expanded:empty::after {{
            display: none;
        }}

        th {{
            background: #34495e;
            color: white;
            position: sticky;
            top: 0;
            z-index: 10;
            font-weight: 600;
        }}

        tr:hover {{
            background-color: #f8f9fa;
        }}

        .timestamp {{
            font-family: 'Courier New', monospace;
            min-width: 100px;
        }}

        .level {{
            min-width: 60px;
        }}

        .level-INFO {{
            color: #27ae60;
        }}

        .level-WARN {{
            color: #f39c12;
        }}

        .level-ERROR {{
            color: #e74c3c;
        }}

        .level-DEBUG {{
            color: #9b59b6;
        }}

        .stats {{
            padding: 10px 20px;
            background: #f8f9fa;
            border-top: 1px solid #dee2e6;
            font-size: 14px;
            color: #6c757d;
        }}

        .hidden {{
            display: none;
        }}

        .filter-toggle {{
            background: #007bff;
            color: white;
            border: none;
            padding: 5px 10px;
            border-radius: 3px;
            cursor: pointer;
            font-size: 12px;
            margin-left: 10px;
        }}

        .filter-toggle:hover {{
            background: #0056b3;
        }}

        .advanced-filters {{
            margin-top: 10px;
            padding: 15px;
            background: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 4px;
        }}

        .filter-row {{
            display: flex;
            align-items: center;
            margin-bottom: 10px;
            gap: 10px;
        }}

        .filter-row label {{
            min-width: 120px;
            font-weight: 500;
        }}

        .filter-row input, .filter-row select {{
            flex: 1;
            padding: 4px 8px;
            border: 1px solid #ccc;
            border-radius: 3px;
            font-size: 14px;
        }}

        .advanced-filters button {{
            background: #6c757d;
            color: white;
            border: none;
            padding: 6px 12px;
            border-radius: 3px;
            cursor: pointer;
            font-size: 12px;
            margin-top: 10px;
        }}

        .advanced-filters button:hover {{
            background: #5a6268;
        }}

        .ai-filter-container {{
            display: flex;
            align-items: center;
            gap: 10px;
            flex-wrap: wrap;
        }}

        .ai-filter-btn {{
            padding: 10px 20px;
            background: #e74c3c;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 14px;
            transition: background-color 0.2s;
            white-space: nowrap;
        }}

        .ai-filter-btn:hover {{
            background: #c0392b;
        }}

        .ai-filter-btn:disabled {{
            background: #95a5a6;
            cursor: not-allowed;
        }}

        .ai-status {{
            font-size: 12px;
            color: #6c757d;
            flex: 1;
            min-width: 200px;
        }}

        .ai-status.loading {{
            color: #007bff;
        }}

        .ai-status.error {{
            color: #dc3545;
        }}

        .ai-status.success {{
            color: #28a745;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Log Viewer</h1>
            <p>File: {csv_file.name}</p>
        </div>

        <div class="controls">
            <div class="control-group">
                <label>Column Presets:</label>
                <div class="preset-buttons">
                    {''.join([f'<button class="preset-btn" onclick="applyPreset(\'{preset}\')">{preset.capitalize()}</button>' for preset in presets.keys()])}
                </div>
            </div>

            <div class="control-group">
                <label for="search">Search:</label>
                <input type="text" id="search" class="search-input" placeholder="Type to filter rows..." onkeyup="filterTable()">
            </div>

            <div class="control-group">
                <label for="aiPrompt">AI Smart Filter:</label>
                <div class="ai-filter-container">
                    <input type="text" id="aiPrompt" class="search-input" placeholder="Describe what you're looking for (e.g., 'errors in the last 5 minutes', 'responses with status codes')">
                    <button id="aiFilterBtn" class="ai-filter-btn" onclick="applyAIFilter()">Apply AI Filter</button>
                    <div id="aiStatus" class="ai-status"></div>
                </div>
            </div>

            <div class="control-group">
                <label>Row Filtering:</label>
                <div class="filter-options">
                    <label class="filter-label">
                        <input type="checkbox" id="hideEmptyRows" onchange="filterTable()" checked>
                        Hide rows with only timestamp data
                    </label>
                    <button class="filter-toggle" onclick="toggleAdvancedFilters()">Advanced Filters</button>
                </div>
                <div class="advanced-filters" id="advancedFilters" style="display: none;">
                    <div class="filter-row">
                        <label>Level:</label>
                        <select id="levelFilter" onchange="filterTable()">
                            <option value="">All</option>
                            <option value="DEBUG">DEBUG</option>
                            <option value="INFO">INFO</option>
                            <option value="WARN">WARN</option>
                            <option value="ERROR">ERROR</option>
                        </select>
                    </div>
                    <div class="filter-row">
                        <label>Command Method:</label>
                        <input type="text" id="commandMethodFilter" placeholder="Filter by command method..." onkeyup="filterTable()">
                    </div>
                    <div class="filter-row">
                        <label>Custom Column Filter:</label>
                        <select id="customColumnSelect" onchange="updateCustomFilter()">
                            <option value="">Choose column...</option>
                            {''.join([f'<option value="{col}">{col}</option>' for col in columns if col not in ['timestamp', 'send_timestamp', 'receive_timestamp']])}
                        </select>
                        <input type="text" id="customColumnFilter" placeholder="Filter value..." onkeyup="filterTable()" disabled>
                    </div>
                    <button onclick="clearAllFilters()">Clear All Filters</button>
                </div>
            </div>

            <div class="control-group">
                <label>Column Order & Visibility:</label>
                <div class="column-order-info">
                    💡 Drag columns to reorder • Check/uncheck to show/hide
                </div>
                <div class="column-controls" id="columnControls">
                    {''.join([f'<div class="column-item" draggable="true" data-column="{col}"><span class="drag-handle">⋮⋮</span><input type="checkbox" id="col_{i}" value="{col}" checked onchange="toggleColumn(\'{col}\')"><label for="col_{i}">{col}</label></div>' for i, col in enumerate(columns)])}
                </div>
            </div>
        </div>

        <div class="table-info">
            💡 Click any cell to expand and see full content • Click again to collapse • Expanded cells show with blue border
        </div>

        <div class="table-container">
            <table id="dataTable">
                <thead>
                    <tr>
                        {''.join([f'<th class="col-{col}" data-column="{col}">{col}</th>' for col in columns])}
                    </tr>
                </thead>
                <tbody id="tableBody">
                    <!-- Data will be loaded here -->
                </tbody>
            </table>
        </div>

        <div class="stats" id="stats">
            Loading...
        </div>
    </div>

    <script>
        let tableData = [];
        let filteredData = [];
        let visibleColumns = new Set({json.dumps(columns)});
        let columnOrder = {json.dumps(columns)};

        const presets = {json.dumps(presets)};

        // Embedded CSV data
        const csvData = `{csv_data_escaped}`;

        // Load CSV data
        function loadData() {{
            try {{
                tableData = parseCSV(csvData);
                filteredData = [...tableData];
                renderTable();
                updateStats();
            }} catch (error) {{
                console.error('Error parsing data:', error);
                document.getElementById('stats').textContent = 'Error parsing data';
            }}
        }}

        function parseCSV(text) {{
            const lines = text.split('\\n');
            const headers = lines[0].split(',').map(h => h.replace(/"/g, ''));
            const data = [];

            for (let i = 1; i < lines.length; i++) {{
                if (lines[i].trim()) {{
                    const values = parseCSVLine(lines[i]);
                    const row = {{}};
                    headers.forEach((header, index) => {{
                        row[header] = values[index] || '';
                    }});
                    data.push(row);
                }}
            }}

            return data;
        }}

        function parseCSVLine(line) {{
            const values = [];
            let current = '';
            let inQuotes = false;

            for (let i = 0; i < line.length; i++) {{
                const char = line[i];
                if (char === '"') {{
                    inQuotes = !inQuotes;
                }} else if (char === ',' && !inQuotes) {{
                    values.push(current.replace(/"/g, ''));
                    current = '';
                }} else {{
                    current += char;
                }}
            }}
            values.push(current.replace(/"/g, ''));
            return values;
        }}

        function renderTable() {{
            const tbody = document.getElementById('tableBody');
            tbody.innerHTML = '';

            // Clear existing table headers and rebuild based on current order
            const thead = document.querySelector('#dataTable thead tr');
            thead.innerHTML = '';

            // Add headers in current order
            columnOrder.forEach(col => {{
                const th = document.createElement('th');
                th.className = `col-${{col}}`;
                th.dataset.column = col;
                th.textContent = col;
                thead.appendChild(th);
            }});

            // Add data rows in current column order
            filteredData.forEach(row => {{
                const tr = document.createElement('tr');

                columnOrder.forEach(col => {{
                    const td = document.createElement('td');
                    td.className = `col-${{col}} collapsed` + (row.level ? ` level-${{row.level}}` : '');
                    td.textContent = row[col] || '';
                    td.title = 'Click to expand/collapse';
                    td.addEventListener('click', function() {{
                        toggleCellExpansion(this);
                    }});
                    tr.appendChild(td);
                }});

                tbody.appendChild(tr);
            }});

            // Update column visibility
            updateColumnVisibility();
        }}

        function filterTable() {{
            const searchTerm = document.getElementById('search').value.toLowerCase();
            const hideEmptyRows = document.getElementById('hideEmptyRows').checked;
            const levelFilter = document.getElementById('levelFilter').value;
            const commandMethodFilter = document.getElementById('commandMethodFilter').value.toLowerCase();
            const customColumnSelect = document.getElementById('customColumnSelect').value;
            const customColumnFilter = document.getElementById('customColumnFilter').value.toLowerCase();

            // Start with AI filtered data if available, otherwise use all data
            let filtered = aiFilteredData || tableData;

            // Filter by search term
            if (searchTerm) {{
                filtered = filtered.filter(row => {{
                    return Object.values(row).some(value =>
                        String(value).toLowerCase().includes(searchTerm)
                    );
                }});
            }}

            // Filter by level
            if (levelFilter) {{
                filtered = filtered.filter(row => row.level === levelFilter);
            }}

            // Filter by command method
            if (commandMethodFilter) {{
                filtered = filtered.filter(row => {{
                    const commandMethod = String(row.command_method || '').toLowerCase();
                    return commandMethod.includes(commandMethodFilter);
                }});
            }}

            // Filter by custom column
            if (customColumnSelect && customColumnFilter) {{
                filtered = filtered.filter(row => {{
                    const columnValue = String(row[customColumnSelect] || '').toLowerCase();
                    return columnValue.includes(customColumnFilter);
                }});
            }}

            // Filter empty rows if option is checked
            if (hideEmptyRows) {{
                filtered = filtered.filter(row => {{
                    // Check if row has meaningful data in visible columns (excluding timestamp columns)
                    const visibleNonTimestampCols = Array.from(visibleColumns).filter(col =>
                        !col.toLowerCase().includes('timestamp')
                    );

                    // If only timestamp columns are visible, don't filter any rows
                    if (visibleNonTimestampCols.length === 0) {{
                        return true;
                    }}

                    // Check if any visible non-timestamp column has non-empty data
                    return visibleNonTimestampCols.some(col => {{
                        const value = row[col];
                        return value && String(value).trim() !== '';
                    }});
                }});
            }}

            filteredData = filtered;
            renderTable();
            updateStats();
        }}

        function updateColumnVisibility() {{
            columnOrder.forEach(columnName => {{
                const elements = document.querySelectorAll(`.col-${{columnName}}`);
                if (visibleColumns.has(columnName)) {{
                    elements.forEach(el => el.classList.remove('hidden'));
                }} else {{
                    elements.forEach(el => el.classList.add('hidden'));
                }}
            }});
        }}

        function toggleCellExpansion(cell) {{
            if (cell.classList.contains('collapsed')) {{
                // Expand the cell
                cell.classList.remove('collapsed');
                cell.classList.add('expanded');
                cell.title = 'Click to collapse';

                // Close any other expanded cells in the same row
                const row = cell.parentElement;
                const otherCells = row.querySelectorAll('td.expanded');
                otherCells.forEach(otherCell => {{
                    if (otherCell !== cell) {{
                        otherCell.classList.remove('expanded');
                        otherCell.classList.add('collapsed');
                        otherCell.title = 'Click to expand/collapse';
                    }}
                }});
            }} else {{
                // Collapse the cell
                cell.classList.remove('expanded');
                cell.classList.add('collapsed');
                cell.title = 'Click to expand/collapse';
            }}
        }}

        function toggleColumn(columnName) {{
            const checkbox = document.querySelector(`input[value="${{columnName}}"]`);

            if (checkbox.checked) {{
                visibleColumns.add(columnName);
            }} else {{
                visibleColumns.delete(columnName);
            }}

            updateColumnVisibility();
            // Re-apply filters when column visibility changes
            filterTable();
        }}

        function applyPreset(presetName) {{
            const preset = presets[presetName];

            // Update active button
            document.querySelectorAll('.preset-btn').forEach(btn => btn.classList.remove('active'));
            event.target.classList.add('active');

            // Update column order and visibility based on preset
            if (preset && preset.length > 0) {{
                // Reorder columns according to preset, then add remaining columns
                const availablePresetCols = preset.filter(col => columnOrder.includes(col));
                const remainingCols = columnOrder.filter(col => !preset.includes(col));
                columnOrder = [...availablePresetCols, ...remainingCols];

                // Update visibility
                visibleColumns.clear();
                availablePresetCols.forEach(col => visibleColumns.add(col));
            }} else {{
                // 'all' preset - show all columns in current order
                columnOrder.forEach(col => visibleColumns.add(col));
            }}

            // Update checkboxes
            document.querySelectorAll('#columnControls input[type="checkbox"]').forEach(checkbox => {{
                checkbox.checked = visibleColumns.has(checkbox.value);
            }});

            // Update column order in UI
            updateColumnOrderUI();

            // Re-render table and apply filters
            filterTable();
        }}

        // Drag and Drop functionality
        let draggedElement = null;

        function setupDragAndDrop() {{
            const columnControls = document.getElementById('columnControls');

            columnControls.addEventListener('dragstart', (e) => {{
                draggedElement = e.target.closest('.column-item');
                draggedElement.classList.add('dragging');
                e.dataTransfer.effectAllowed = 'move';
                e.dataTransfer.setData('text/html', draggedElement.outerHTML);
            }});

            columnControls.addEventListener('dragend', (e) => {{
                if (draggedElement) {{
                    draggedElement.classList.remove('dragging');
                    draggedElement = null;
                }}
                document.querySelectorAll('.column-item').forEach(item => {{
                    item.classList.remove('drag-over');
                }});
            }});

            columnControls.addEventListener('dragover', (e) => {{
                e.preventDefault();
                e.dataTransfer.dropEffect = 'move';

                const afterElement = getDragAfterElement(columnControls, e.clientY);
                const dragging = document.querySelector('.dragging');

                if (afterElement == null) {{
                    columnControls.appendChild(dragging);
                }} else {{
                    columnControls.insertBefore(dragging, afterElement);
                }}
            }});

            columnControls.addEventListener('drop', (e) => {{
                e.preventDefault();
                updateColumnOrderFromUI();
                renderTable();
            }});
        }}

        function getDragAfterElement(container, y) {{
            const draggableElements = [...container.querySelectorAll('.column-item:not(.dragging)')];

            return draggableElements.reduce((closest, child) => {{
                const box = child.getBoundingClientRect();
                const offset = y - box.top - box.height / 2;

                if (offset < 0 && offset > closest.offset) {{
                    return {{ offset: offset, element: child }};
                }} else {{
                    return closest;
                }}
            }}, {{ offset: Number.NEGATIVE_INFINITY }}).element;
        }}

        function updateColumnOrderFromUI() {{
            const columnItems = document.querySelectorAll('.column-item');
            columnOrder = Array.from(columnItems).map(item => item.dataset.column);
        }}

        function updateColumnOrderUI() {{
            const columnControls = document.getElementById('columnControls');
            const items = Array.from(columnControls.querySelectorAll('.column-item'));

            // Sort items according to current columnOrder
            items.sort((a, b) => {{
                const aIndex = columnOrder.indexOf(a.dataset.column);
                const bIndex = columnOrder.indexOf(b.dataset.column);
                return aIndex - bIndex;
            }});

            // Re-append items in correct order
            items.forEach(item => columnControls.appendChild(item));
        }}

        function updateStats() {{
            const total = tableData.length;
            const filtered = filteredData.length;
            const visible = visibleColumns.size;

            document.getElementById('stats').textContent =
                `Showing ${{filtered}} of ${{total}} rows | ${{visible}} of {len(columns)} columns visible`;
        }}

        function toggleAdvancedFilters() {{
            const advancedFilters = document.getElementById('advancedFilters');
            const button = event.target;

            if (advancedFilters.style.display === 'none') {{
                advancedFilters.style.display = 'block';
                button.textContent = 'Hide Advanced Filters';
            }} else {{
                advancedFilters.style.display = 'none';
                button.textContent = 'Advanced Filters';
            }}
        }}

        function updateCustomFilter() {{
            const select = document.getElementById('customColumnSelect');
            const input = document.getElementById('customColumnFilter');

            if (select.value) {{
                input.disabled = false;
                input.placeholder = `Filter by ${{select.value}}...`;
            }} else {{
                input.disabled = true;
                input.value = '';
                input.placeholder = 'Filter value...';
                filterTable(); // Re-filter when custom filter is cleared
            }}
        }}

        function clearAllFilters() {{
            // Clear all filter inputs
            document.getElementById('search').value = '';
            document.getElementById('hideEmptyRows').checked = true;
            document.getElementById('levelFilter').value = '';
            document.getElementById('commandMethodFilter').value = '';
            document.getElementById('customColumnSelect').value = '';
            document.getElementById('customColumnFilter').value = '';
            document.getElementById('aiPrompt').value = '';

            // Clear AI filter state
            aiFilteredData = null;
            document.getElementById('aiStatus').textContent = '';
            document.getElementById('aiStatus').className = 'ai-status';

            // Update custom filter state
            updateCustomFilter();

            // Re-apply filters
            filterTable();
        }}

        // AI Filtering functionality
        let aiFilteredData = null;

        async function applyAIFilter() {{
            const prompt = document.getElementById('aiPrompt').value.trim();
            const statusEl = document.getElementById('aiStatus');
            const btnEl = document.getElementById('aiFilterBtn');

            if (!prompt) {{
                statusEl.textContent = 'Please enter a description of what you want to filter.';
                statusEl.className = 'ai-status error';
                return;
            }}

            // Show loading state
            statusEl.textContent = 'Processing with AI...';
            statusEl.className = 'ai-status loading';
            btnEl.disabled = true;

            try {{
                // Create a sample of the data for the AI to understand the structure
                const sampleData = tableData.slice(0, 5).map(row => {{
                    const sample = {{}};
                    Object.keys(row).forEach(key => {{
                        sample[key] = String(row[key]).length > 50 ?
                            String(row[key]).substring(0, 50) + '...' : row[key];
                    }});
                    return sample;
                }});

                // Prepare the AI prompt
                const aiPrompt = `
You are helping filter log data based on user requirements. Here's a sample of the data structure:

${{JSON.stringify(sampleData, null, 2)}}

The user wants to filter for: "${{prompt}}"

Please return a JavaScript function that takes a row object and returns true if the row should be included in the filtered results, false otherwise.

The function should be named 'filterFunction' and handle edge cases gracefully. Only return the function code, no explanation.

Example format:
function filterFunction(row) {{
    // Your filtering logic here
    return someCondition;
}}
`;

                // Call OpenAI API (you'll need to implement the actual API call)
                const response = await callOpenAI(aiPrompt);

                if (response && response.function) {{
                    // Execute the AI-generated filter function
                    const filterFunc = new Function('return ' + response.function)();
                    aiFilteredData = tableData.filter(filterFunc);

                    statusEl.textContent = `AI filter applied: ${{aiFilteredData.length}} of ${{tableData.length}} rows match`;
                    statusEl.className = 'ai-status success';

                    // Apply the filter
                    filterTable();
                }} else {{
                    throw new Error('Invalid response from AI');
                }}

            }} catch (error) {{
                console.error('AI Filter Error:', error);
                statusEl.textContent = 'AI filtering failed. Using keyword search instead.';
                statusEl.className = 'ai-status error';

                // Fallback to simple keyword search
                document.getElementById('search').value = prompt;
                filterTable();
            }} finally {{
                btnEl.disabled = false;
            }}
        }}

        async function callOpenAI(prompt) {{
            // This is a placeholder for the OpenAI API call
            // In a real implementation, you would need to:
            // 1. Set up a backend endpoint to handle the OpenAI API call
            // 2. Include your OpenAI API key securely
            // 3. Make the request through your backend

            return new Promise((resolve, reject) => {{
                // For now, we'll simulate the AI response with a simple keyword-based filter
                setTimeout(() => {{
                    try {{
                        const userPrompt = prompt.toLowerCase();
                        let filterCode = 'function filterFunction(row) {{ return true; }}';

                        // Simple pattern matching for common requests
                        if (userPrompt.includes('error')) {{
                            filterCode = `function filterFunction(row) {{
                                return String(row.level || '').toLowerCase().includes('error') ||
                                       Object.values(row).some(val => String(val).toLowerCase().includes('error'));
                            }}`;
                        }} else if (userPrompt.includes('warn')) {{
                            filterCode = `function filterFunction(row) {{
                                return String(row.level || '').toLowerCase().includes('warn') ||
                                       Object.values(row).some(val => String(val).toLowerCase().includes('warn'));
                            }}`;
                        }} else if (userPrompt.includes('info')) {{
                            filterCode = `function filterFunction(row) {{
                                return String(row.level || '').toLowerCase().includes('info') ||
                                       Object.values(row).some(val => String(val).toLowerCase().includes('info'));
                            }}`;
                        }} else if (userPrompt.includes('debug')) {{
                            filterCode = `function filterFunction(row) {{
                                return String(row.level || '').toLowerCase().includes('debug') ||
                                       Object.values(row).some(val => String(val).toLowerCase().includes('debug'));
                            }}`;
                        }} else {{
                            // Generic keyword search
                            const keywords = userPrompt.split(' ').filter(word => word.length > 2);
                            if (keywords.length > 0) {{
                                filterCode = `function filterFunction(row) {{
                                    const searchTerms = ${{JSON.stringify(keywords)}};
                                    return searchTerms.some(term =>
                                        Object.values(row).some(val =>
                                            String(val).toLowerCase().includes(term)
                                        )
                                    );
                                }}`;
                            }}
                        }}

                        resolve({{ function: filterCode }});
                    }} catch (error) {{
                        reject(error);
                    }}
                }}, 1000); // Simulate API delay
            }});
        }}

        // Initialize
        document.addEventListener('DOMContentLoaded', () => {{
            loadData();
            setupDragAndDrop();
            // Apply basic preset by default
            setTimeout(() => applyPreset('basic'), 100);
        }});
    </script>
</body>
</html>'''

    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(html_content)

def main():
    parser = argparse.ArgumentParser(description='Convert log files to CSV and generate HTML viewer')
    parser.add_argument('log_file', help='Path to the log file')
    parser.add_argument('--output-dir', default=None, help='Output directory (default: same as log file)')

    args = parser.parse_args()

    log_file = Path(args.log_file)
    if not log_file.exists():
        print(f"Error: Log file '{log_file}' does not exist")
        return 1

    # Determine output directory
    if args.output_dir:
        output_dir = Path(args.output_dir)
    else:
        output_dir = log_file.parent

    output_dir.mkdir(parents=True, exist_ok=True)

    # Generate output filenames
    base_name = log_file.stem
    csv_file = output_dir / f"{base_name}.csv"
    html_file = output_dir / f"{base_name}_viewer.html"

    print(f"Converting '{log_file}' to CSV...")
    columns = convert_log_to_csv(log_file, csv_file)
    print(f"CSV saved to: {csv_file}")

    print(f"Generating HTML viewer...")
    generate_html_viewer(csv_file, html_file, columns)
    print(f"HTML viewer saved to: {html_file}")

    print(f"\\nOpen {html_file} in your browser to view the interactive log data.")
    print(f"Found {len(columns)} columns: {', '.join(columns[:5])}{'...' if len(columns) > 5 else ''}")

    return 0

if __name__ == '__main__':
    exit(main())