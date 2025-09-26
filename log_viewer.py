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

def parse_log_line(line: str) -> Optional[Dict[str, Any]]:
    """Parse a single log line into structured data."""
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
        # Parse the JSON data - handle single quotes by using eval (safe for log parsing)
        try:
            data = json.loads(json_str)
        except json.JSONDecodeError:
            # Try using eval for single-quoted dictionaries (safer than literal_eval for this format)
            import ast
            data = ast.literal_eval(json_str)

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
        # If JSON parsing fails, store as raw text
        return {
            'timestamp': timestamp,
            'level': level,
            'raw_data': json_str
        }

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

    # Sort columns for consistent ordering
    columns = sorted(all_columns)

    # Write CSV
    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        for record in records:
            # Fill missing columns with empty strings
            filled_record = {col: record.get(col, '') for col in columns}
            writer.writerow(filled_record)

    return columns

def generate_html_viewer(csv_file: Path, html_file: Path, columns: List[str]) -> None:
    """Generate interactive HTML viewer for the CSV data."""

    # Define column presets
    presets = {
        'basic': ['timestamp', 'level', 'command_method', 'command_str'],
        'detailed': ['timestamp', 'level', 'command_method', 'command_str', 'raw_response', 'parsed_response'],
        'network': ['timestamp', 'level', 'command_method', 'raw_response'],
        'all': columns
    }

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

        .column-controls {{
            max-height: 200px;
            overflow-y: auto;
            border: 1px solid #bdc3c7;
            border-radius: 4px;
            padding: 10px;
            background: white;
        }}

        .column-item {{
            display: flex;
            align-items: center;
            padding: 5px 0;
            border-bottom: 1px solid #ecf0f1;
        }}

        .column-item:last-child {{
            border-bottom: none;
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

        .table-container {{
            overflow-x: auto;
            max-height: 70vh;
            overflow-y: auto;
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            background: white;
        }}

        th, td {{
            padding: 12px 8px;
            text-align: left;
            border-bottom: 1px solid #ecf0f1;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            max-width: 300px;
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
                <label>Visible Columns:</label>
                <div class="column-controls" id="columnControls">
                    {''.join([f'<div class="column-item"><input type="checkbox" id="col_{i}" value="{col}" checked onchange="toggleColumn(\'{col}\')"><label for="col_{i}">{col}</label></div>' for i, col in enumerate(columns)])}
                </div>
            </div>
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

        const presets = {json.dumps(presets)};

        // Load CSV data
        async function loadData() {{
            try {{
                const response = await fetch('{csv_file.name}');
                const csvText = await response.text();
                tableData = parseCSV(csvText);
                filteredData = [...tableData];
                renderTable();
                updateStats();
            }} catch (error) {{
                console.error('Error loading data:', error);
                document.getElementById('stats').textContent = 'Error loading data';
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

            filteredData.forEach(row => {{
                const tr = document.createElement('tr');

                {''.join([f'''const td{i} = document.createElement('td');
                td{i}.className = 'col-{col}' + (row.level ? ' level-' + row.level : '');
                td{i}.textContent = row['{col}'] || '';
                td{i}.title = row['{col}'] || '';
                tr.appendChild(td{i});
                ''' for i, col in enumerate(columns)])}

                tbody.appendChild(tr);
            }});
        }}

        function filterTable() {{
            const searchTerm = document.getElementById('search').value.toLowerCase();

            if (!searchTerm) {{
                filteredData = [...tableData];
            }} else {{
                filteredData = tableData.filter(row => {{
                    return Object.values(row).some(value =>
                        String(value).toLowerCase().includes(searchTerm)
                    );
                }});
            }}

            renderTable();
            updateStats();
        }}

        function toggleColumn(columnName) {{
            const elements = document.querySelectorAll(`.col-${{columnName}}`);
            const checkbox = document.querySelector(`input[value="${{columnName}}"]`);

            if (checkbox.checked) {{
                visibleColumns.add(columnName);
                elements.forEach(el => el.classList.remove('hidden'));
            }} else {{
                visibleColumns.delete(columnName);
                elements.forEach(el => el.classList.add('hidden'));
            }}
        }}

        function applyPreset(presetName) {{
            const preset = presets[presetName];

            // Update active button
            document.querySelectorAll('.preset-btn').forEach(btn => btn.classList.remove('active'));
            event.target.classList.add('active');

            // Update checkboxes and visibility
            document.querySelectorAll('#columnControls input[type="checkbox"]').forEach(checkbox => {{
                const columnName = checkbox.value;
                const shouldShow = preset.includes(columnName);

                checkbox.checked = shouldShow;

                const elements = document.querySelectorAll(`.col-${{columnName}}`);
                if (shouldShow) {{
                    visibleColumns.add(columnName);
                    elements.forEach(el => el.classList.remove('hidden'));
                }} else {{
                    visibleColumns.delete(columnName);
                    elements.forEach(el => el.classList.add('hidden'));
                }}
            }});
        }}

        function updateStats() {{
            const total = tableData.length;
            const filtered = filteredData.length;
            const visible = visibleColumns.size;

            document.getElementById('stats').textContent =
                `Showing ${{filtered}} of ${{total}} rows | ${{visible}} of {len(columns)} columns visible`;
        }}

        // Initialize
        document.addEventListener('DOMContentLoaded', () => {{
            loadData();
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