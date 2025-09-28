#!/usr/bin/env python3
"""
HTML template generation functionality
"""

import json
from typing import Dict, List, Any
from pathlib import Path

from models import AnalyzerData, ColumnType, html_escape
from data_processor import DataProcessor


class HTMLGenerator:
    """Generates interactive HTML analyzer from data"""

    def __init__(self, data: AnalyzerData, processor: DataProcessor):
        self.data = data
        self.processor = processor

    def generate_html(self, output_path: str, title: str = None) -> None:
        """Generate interactive HTML analyzer"""
        if title is None:
            title = f"Test Analysis - {Path(output_path).stem}"

        # Prepare data for JavaScript
        js_data = []
        for row in self.data.rows:
            js_row = {
                '_row_class': row.css_class,
                '_is_result': row.row_type.value == 'result'
            }
            for col in self.data.columns:
                value = row.get_value(col)
                # Format timestamp values for JavaScript
                if self.data.get_column_type(col) == ColumnType.TIMESTAMP and value:
                    formatted_value = self.processor.format_timestamp(str(value))
                    js_row[col] = formatted_value if formatted_value != str(value) else value
                else:
                    js_row[col] = value
            js_data.append(js_row)

        # Group columns by category
        column_groups = self.processor.get_column_groups()

        html_content = self._generate_html_template(title, js_data, column_groups)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

        print(f"Generated HTML analyzer: {output_path}")

    def _generate_html_template(self, title: str, js_data: List[Dict], column_groups: Dict[str, List[str]]) -> str:
        """Generate the complete HTML template"""

        # Column visibility checkboxes HTML
        column_controls = []
        for group_name, cols in column_groups.items():
            column_controls.append(f'<div class="column-group">')
            column_controls.append(f'<h4>{group_name} <button class="group-toggle" onclick="toggleGroup(\'{group_name}\')">'
                                 f'Toggle All</button></h4>')
            for col in cols:
                col_id = col.replace(' ', '_').replace('.', '_')
                checked = 'checked' if self.data.column_info[col].visible else ''
                col_type = self.data.get_column_type(col).value
                column_controls.append(f'''
                    <label class="column-checkbox">
                        <input type="checkbox" {checked} data-column="{col}" data-group="{group_name}"
                               onchange="toggleColumn('{col}')">
                        <span class="column-name">{html_escape(col)}</span>
                        <span class="column-type">({col_type})</span>
                    </label>
                ''')
            column_controls.append('</div>')

        column_controls_html = '\n'.join(column_controls)

        # Filter controls HTML
        filter_controls = []
        for col in self.data.columns:
            col_type = self.data.get_column_type(col)
            if col_type == ColumnType.NUMBER:
                filter_controls.append(f'''
                    <div class="filter-control" data-column="{col}" style="display: none;">
                        <label>{html_escape(col)} (number)</label>
                        <input type="number" placeholder="Min" onchange="applyFilters()" data-filter-type="min" data-filter-column="{col}">
                        <input type="number" placeholder="Max" onchange="applyFilters()" data-filter-type="max" data-filter-column="{col}">
                    </div>
                ''')
            elif col_type == ColumnType.CATEGORY:
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

        # Convert column types to JSON-serializable format
        column_types_js = {col: col_info.column_type.value for col, col_info in self.data.column_info.items()}

        return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{html_escape(title)}</title>
    {self._get_css_styles()}
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
                        <option value="test-overview">Test Overview</option>
                        <option value="results-only">Results Only</option>
                        <option value="failures-only">Failures Only</option>
                        <option value="logs-only">Logs Only</option>
                        <option value="errors-warnings">Errors & Warnings</option>
                        <option value="debug-view">Debug View</option>
                        <option value="commands-only">Commands Only</option>
                        <option value="measurements">Measurements</option>
                        <option value="timing-analysis">Timing Analysis</option>
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
    </div>

    <!-- Modal for expanded content -->
    <div id="contentModal" class="modal">
        <div class="modal-content">
            <span class="close" onclick="closeModal()">&times;</span>
            <h3>Content Detail</h3>
            <pre id="modal-content"></pre>
        </div>
    </div>

    {self._get_javascript(js_data, column_types_js)}
</body>
</html>'''

    def _get_css_styles(self) -> str:
        """Get the CSS styles for the HTML template"""
        return '''<style>
        * {
            box-sizing: border-box;
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
            color: #333;
        }

        .container {
            max-width: 100%;
            margin: 0 auto;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            overflow: hidden;
        }

        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            text-align: center;
        }

        .header h1 {
            margin: 0;
            font-size: 2em;
        }

        .controls {
            display: flex;
            flex-wrap: wrap;
            gap: 20px;
            padding: 20px;
            background: #f8f9fa;
            border-bottom: 1px solid #dee2e6;
        }

        .control-section {
            flex: 1;
            min-width: 300px;
        }

        .control-section h3 {
            margin: 0 0 15px 0;
            color: #495057;
        }

        .global-controls {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            margin-bottom: 15px;
        }

        .global-search {
            flex: 1;
            min-width: 200px;
            padding: 8px 12px;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-size: 14px;
        }

        .btn {
            padding: 8px 16px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 14px;
            background: #007bff;
            color: white;
            transition: background-color 0.2s;
        }

        .btn:hover {
            background: #0056b3;
        }

        .btn-secondary {
            background: #6c757d;
        }

        .btn-secondary:hover {
            background: #545b62;
        }

        .presets {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            align-items: center;
        }

        .preset-select {
            min-width: 150px;
            padding: 6px;
            border: 1px solid #ddd;
            border-radius: 4px;
        }

        .column-controls {
            max-height: 300px;
            overflow-y: auto;
            border: 1px solid #ddd;
            border-radius: 4px;
            padding: 10px;
            background: white;
        }

        .column-group {
            margin-bottom: 15px;
        }

        .column-group h4 {
            margin: 0 0 8px 0;
            color: #495057;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .group-toggle {
            background: #28a745;
            color: white;
            border: none;
            padding: 4px 8px;
            border-radius: 3px;
            cursor: pointer;
            font-size: 12px;
        }

        .column-checkbox {
            display: block;
            padding: 4px 0;
            cursor: pointer;
        }

        .column-checkbox input {
            margin-right: 8px;
        }

        .column-name {
            font-weight: 500;
        }

        .column-type {
            color: #6c757d;
            font-size: 12px;
            margin-left: 8px;
        }

        .toggle-checkbox {
            display: flex;
            align-items: center;
            gap: 8px;
            cursor: pointer;
            font-size: 14px;
            color: #495057;
        }

        .toggle-checkbox input {
            margin: 0;
        }

        .filter-controls {
            max-height: 300px;
            overflow-y: auto;
            border: 1px solid #ddd;
            border-radius: 4px;
            padding: 10px;
            background: white;
        }

        .filter-control {
            margin-bottom: 10px;
        }

        .filter-control label {
            display: block;
            margin-bottom: 4px;
            font-weight: 500;
            color: #495057;
        }

        .filter-control input,
        .filter-control select {
            width: 100%;
            padding: 6px;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-size: 14px;
        }

        .filter-control input[type="number"] {
            width: 48%;
            margin-right: 4%;
        }

        .filter-control input[type="number"]:last-child {
            margin-right: 0;
        }

        .stats {
            text-align: center;
            padding: 10px;
            background: #e9ecef;
            font-size: 14px;
            color: #6c757d;
        }

        .table-container {
            overflow: auto;
            max-height: 70vh;
        }

        table {
            width: 100%;
            border-collapse: collapse;
            font-size: 13px;
        }

        th, td {
            padding: 8px;
            text-align: left;
            border: 1px solid #ddd;
            word-wrap: break-word;
            max-width: 300px;
            position: relative;
        }

        th {
            background: #f8f9fa;
            font-weight: 600;
            position: sticky;
            top: 0;
            z-index: 100;
        }

        .sortable {
            cursor: pointer;
            user-select: none;
            position: relative;
        }

        .sortable:hover {
            background: #e9ecef;
        }

        .draggable {
            cursor: grab;
            transition: background-color 0.2s;
        }

        .draggable:active {
            cursor: grabbing;
        }

        .draggable.dragging {
            opacity: 0.5;
            background: #007bff;
            color: white;
        }

        .drop-zone {
            position: relative;
        }

        .drop-indicator {
            position: absolute;
            top: 0;
            bottom: 0;
            width: 3px;
            background: #007bff;
            z-index: 1000;
            display: none;
        }

        .drop-indicator.left {
            left: -2px;
        }

        .drop-indicator.right {
            right: -2px;
        }

        .drop-indicator.show {
            display: block;
        }

        .sort-indicator {
            float: right;
            opacity: 0.5;
        }

        .result-row {
            background: #f8fff8;
        }

        .result-pass {
            border-left: 4px solid #28a745;
        }

        .result-fail {
            border-left: 4px solid #dc3545;
            background: #fff5f5;
        }

        .log-row {
            background: #fafafa;
        }

        .log-error {
            border-left: 4px solid #dc3545;
            background: #fff5f5;
        }

        .log-warning {
            border-left: 4px solid #ffc107;
            background: #fffbf0;
        }

        .log-info {
            border-left: 4px solid #17a2b8;
        }

        .log-debug {
            border-left: 4px solid #6c757d;
        }

        .cell-content.expandable {
            cursor: pointer;
            color: #007bff;
            text-decoration: underline;
        }

        .expanded {
            white-space: pre-wrap;
            max-width: none !important;
            word-break: break-all;
        }

        .hidden {
            display: none !important;
        }

        .modal {
            display: none;
            position: fixed;
            z-index: 1000;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0,0,0,0.5);
        }

        .modal-content {
            background-color: #fff;
            margin: 5% auto;
            padding: 20px;
            border-radius: 8px;
            width: 80%;
            max-width: 800px;
            max-height: 80%;
            overflow-y: auto;
        }

        .close {
            color: #aaa;
            float: right;
            font-size: 28px;
            font-weight: bold;
            cursor: pointer;
        }

        .close:hover {
            color: #000;
        }

        @media (max-width: 768px) {
            .controls {
                flex-direction: column;
            }

            .control-section {
                min-width: auto;
            }

            th, td {
                padding: 4px;
                font-size: 12px;
            }
        }
    </style>'''

    def _get_javascript(self, js_data: List[Dict], column_types: Dict[str, str]) -> str:
        """Get the JavaScript code for the HTML template"""
        return f'''<script>
        // Data and state
        const data = {json.dumps(js_data, indent=2)};
        const columns = {json.dumps(self.data.columns)};
        const columnTypes = {json.dumps(column_types)};

        let filteredData = [...data];
        let visibleColumns = new Set({json.dumps(self.data.config.default_visible_columns)});
        let columnOrder = [...columns]; // Track the order of columns
        let sortColumn = null;
        let sortDirection = 'asc';
        let filters = {{}};

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
                if (/^\\\\d+$/.test(timestampStr.trim())) {{
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

                columnOrder.forEach(col => {{
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
                    columns: ['Pass', 'timestamp', 'command_method', 'command_str', 'raw_response'],
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
                }},
                'test-overview': {{
                    columns: ['Pass', 'timestamp', 'command_method', 'peak_amplitude', 'peak_frequency', 'level', 'message'],
                    filters: {{}}
                }},
                'commands-only': {{
                    columns: ['timestamp', 'command_method', 'keysight_xsan_command', 'command_str', 'response_str'],
                    filters: {{}}
                }},
                'measurements': {{
                    columns: ['timestamp', 'peak_amplitude', 'peak_frequency', 'frequencies', 'peak_table', 'trace_name'],
                    filters: {{}}
                }},
                'timing-analysis': {{
                    columns: ['timestamp', 'send_time_str', 'receive_time_str', 'command_method', 'level'],
                    filters: {{}}
                }},
                'failures-only': {{
                    columns: ['Pass', 'timestamp', 'command_method', 'level', 'message', 'peak_amplitude'],
                    filters: {{ 'Pass': ['False'] }}
                }},
                'debug-view': {{
                    columns: ['timestamp', 'level', 'message', 'line_number', 'command_method', 'docstring'],
                    filters: {{ 'level': ['DEBUG', 'INFO', 'WARNING', 'ERROR'] }}
                }}
            }};

            preset = presets[presetName];

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
            const fullContent = element.dataset.full || element.textContent;
            document.getElementById('modal-content').textContent = fullContent;
            document.getElementById('contentModal').style.display = 'block';
        }}

        function closeModal() {{
            document.getElementById('contentModal').style.display = 'none';
        }}

        function exportData() {{
            const csvContent = [
                columnOrder.filter(col => visibleColumns.has(col)).join(','),
                ...filteredData.map(row =>
                    columnOrder.filter(col => visibleColumns.has(col))
                             .map(col => `"${{String(row[col] || '').replace(/"/g, '""')}}"`)
                             .join(',')
                )
            ].join('\\\\n');

            const blob = new Blob([csvContent], {{ type: 'text/csv' }});
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'filtered_data.csv';
            a.click();
            window.URL.revokeObjectURL(url);
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
    </script>'''