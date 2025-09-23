#!/usr/bin/env python3
"""
HTML templates for report generation.
"""


class HTMLTemplates:
    """Container for all HTML templates"""

    @staticmethod
    def get_main_template() -> str:
        """Get the main HTML report template"""
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
            min-width: 1500px;
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
            max-width: 200px;
            max-height: 120px;
            overflow: auto;
            position: relative;
        }}

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

        .parsed-response {{
            font-family: 'Courier New', monospace;
            font-size: 11px;
            max-width: 300px;
            word-wrap: break-word;
        }}

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

        /* Column Control Panel Styles */
        .column-controls {{
            background: #f8f9fa;
            border: 1px solid #ddd;
            border-radius: 5px;
            padding: 15px;
            margin: 20px 0;
            position: relative;
        }}

        .column-controls h3 {{
            margin: 0 0 15px 0;
            color: #2c3e50;
            font-size: 16px;
        }}

        .column-controls-toggle {{
            background: #3498db;
            color: white;
            border: none;
            padding: 8px 15px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 14px;
            margin-bottom: 15px;
        }}

        .column-controls-toggle:hover {{
            background: #2980b9;
        }}

        .column-controls-content {{
            display: none;
        }}

        .column-controls-content.active {{
            display: block;
        }}

        .column-list {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 10px;
            margin: 15px 0;
        }}

        .column-item {{
            display: flex;
            align-items: center;
            padding: 5px;
            background: white;
            border: 1px solid #e0e0e0;
            border-radius: 3px;
            cursor: move;
            transition: all 0.2s;
        }}

        .column-item:hover {{
            background: #f0f7ff;
            border-color: #3498db;
        }}

        .column-item.dragging {{
            opacity: 0.5;
            transform: rotate(2deg);
        }}

        .column-checkbox {{
            margin-right: 10px;
        }}

        .column-type-icon {{
            margin-right: 8px;
            font-size: 12px;
        }}

        .column-label {{
            flex: 1;
            font-size: 13px;
            color: #333;
        }}

        .column-drag-handle {{
            color: #999;
            font-size: 14px;
            margin-left: 5px;
        }}

        .column-presets {{
            margin: 15px 0;
        }}

        .preset-button {{
            background: #ecf0f1;
            border: 1px solid #bdc3c7;
            color: #2c3e50;
            padding: 6px 12px;
            margin: 2px;
            border-radius: 3px;
            cursor: pointer;
            font-size: 12px;
            transition: all 0.2s;
        }}

        .preset-button:hover {{
            background: #d5dbdb;
        }}

        .preset-button.active {{
            background: #3498db;
            color: white;
            border-color: #2980b9;
        }}

        /* Hidden column styling */
        .column-hidden {{
            display: none !important;
        }}

        /* Drag and drop indicators */
        .drop-indicator {{
            height: 2px;
            background: #3498db;
            margin: 2px 0;
            opacity: 0;
            transition: opacity 0.2s;
        }}

        .drop-indicator.active {{
            opacity: 1;
        }}

        /* Responsive adjustments */
        @media (max-width: 768px) {{
            .column-list {{
                grid-template-columns: 1fr;
            }}
        }}
    </style>
    <script>
        // Column management functionality
        class ColumnManager {{
            constructor() {{
                this.columns = [];
                this.visibleColumns = new Set();
                this.columnOrder = [];
                this.draggedElement = null;
                this.init();
            }}

            init() {{
                this.loadColumnMetadata();
                this.loadSettings();
                this.setupEventListeners();
                this.createColumnControls();
                this.applyColumnVisibility();
            }}

            loadColumnMetadata() {{
                // Use provided metadata if available, otherwise extract from table
                if (window.columnMetadata && window.columnMetadata.length > 0) {{
                    this.columns = window.columnMetadata.map(col => ({{
                        key: col.key,
                        displayName: col.displayName,
                        index: col.index,
                        description: col.description || '',
                        type: col.type || 'text',
                        visible: col.visible !== false
                    }}));
                }} else {{
                    // Fallback: extract from table headers
                    const headerRow = document.querySelector('table thead tr');
                    if (!headerRow) return;

                    const headers = headerRow.querySelectorAll('th');
                    this.columns = Array.from(headers).slice(1).map((th, index) => ({{
                        key: this.generateColumnKey(th.textContent.trim()),
                        displayName: th.textContent.trim(),
                        index: index + 1, // +1 to account for row number column
                        description: '',
                        type: 'text',
                        visible: true
                    }}));
                }}

                this.columnOrder = this.columns.map(col => col.key);
                this.visibleColumns = new Set(this.columns.filter(col => col.visible).map(col => col.key));
            }}

            generateColumnKey(displayName) {{
                // Convert display name back to key format
                return displayName.toLowerCase()
                    .replace(/[^a-z0-9]/g, '_')
                    .replace(/_+/g, '_')
                    .replace(/^_|_$/g, '');
            }}

            loadSettings() {{
                try {{
                    const saved = localStorage.getItem('reportColumnSettings');
                    if (saved) {{
                        const settings = JSON.parse(saved);
                        this.visibleColumns = new Set(settings.visibleColumns || this.columnOrder);
                        this.columnOrder = settings.columnOrder || this.columnOrder;
                    }}
                }} catch (e) {{
                    console.log('Could not load column settings:', e);
                }}
            }}

            saveSettings() {{
                try {{
                    const settings = {{
                        visibleColumns: Array.from(this.visibleColumns),
                        columnOrder: this.columnOrder
                    }};
                    localStorage.setItem('reportColumnSettings', JSON.stringify(settings));
                }} catch (e) {{
                    console.log('Could not save column settings:', e);
                }}
            }}

            setupEventListeners() {{
                document.addEventListener('DOMContentLoaded', () => {{
                    this.applyColumnVisibility();
                }});
            }}

            createColumnControls() {{
                const container = document.querySelector('.container');
                const statusInfo = document.querySelector('.status-info');

                const controlsHtml = `
                    <div class="column-controls">
                        <button class="column-controls-toggle" onclick="columnManager.toggleControls()">
                            📊 Configure Columns
                        </button>
                        <div class="column-controls-content" id="column-controls-content">
                            <h3>Column Visibility & Order</h3>

                            <div class="column-presets">
                                <strong>Quick Presets:</strong><br>
                                <button class="preset-button" onclick="columnManager.applyPreset('minimal')">Minimal</button>
                                <button class="preset-button" onclick="columnManager.applyPreset('frequency')">Frequency Analysis</button>
                                <button class="preset-button" onclick="columnManager.applyPreset('commands')">Commands</button>
                                <button class="preset-button" onclick="columnManager.applyPreset('all')">Show All</button>
                                <button class="preset-button" onclick="columnManager.resetToDefault()">Reset</button>
                            </div>

                            <div class="column-list" id="column-list">
                                ${{this.generateColumnList()}}
                            </div>

                            <p style="font-size: 12px; color: #666; margin: 10px 0 0 0;">
                                💡 Drag items to reorder columns, use checkboxes to show/hide. Settings are saved automatically.
                            </p>
                        </div>
                    </div>
                `;

                if (statusInfo) {{
                    statusInfo.insertAdjacentHTML('afterend', controlsHtml);
                }} else {{
                    const h1 = container.querySelector('h1');
                    h1.insertAdjacentHTML('afterend', controlsHtml);
                }}

                this.setupDragAndDrop();
            }}

            generateColumnList() {{
                return this.columnOrder.map(key => {{
                    const column = this.columns.find(col => col.key === key);
                    if (!column) return '';

                    const checked = this.visibleColumns.has(key) ? 'checked' : '';
                    const title = column.description ? `title="${{column.description}}"` : '';
                    const typeIcon = this.getTypeIcon(column.type);

                    return `
                        <div class="column-item" draggable="true" data-column="${{key}}" ${{title}}>
                            <input type="checkbox" class="column-checkbox" ${{checked}}
                                   onchange="columnManager.toggleColumn('${{key}}', this.checked)">
                            <span class="column-type-icon">${{typeIcon}}</span>
                            <span class="column-label">${{column.displayName}}</span>
                            <span class="column-drag-handle">⋮⋮</span>
                        </div>
                    `;
                }}).join('');
            }}

            getTypeIcon(type) {{
                const icons = {{
                    'text': '📝',
                    'numeric': '🔢',
                    'frequency': '📊',
                    'amplitude': '📈',
                    'command': '⌨️',
                    'response': '💬',
                    'parsed_response': '🔍',
                    'screenshot': '📷'
                }};
                return icons[type] || '📝';
            }}

            toggleControls() {{
                const content = document.getElementById('column-controls-content');
                content.classList.toggle('active');

                if (content.classList.contains('active')) {{
                    this.refreshColumnList();
                }}
            }}

            refreshColumnList() {{
                const columnList = document.getElementById('column-list');
                if (columnList) {{
                    columnList.innerHTML = this.generateColumnList();
                    this.setupDragAndDrop();
                }}
            }}

            toggleColumn(key, visible) {{
                if (visible) {{
                    this.visibleColumns.add(key);
                }} else {{
                    this.visibleColumns.delete(key);
                }}
                this.applyColumnVisibility();
                this.saveSettings();
            }}

            applyColumnVisibility() {{
                const table = document.querySelector('table');
                if (!table) return;

                this.columns.forEach(column => {{
                    const isVisible = this.visibleColumns.has(column.key);
                    const columnIndex = column.index;

                    // Hide/show header
                    const headerCell = table.querySelector(`thead tr th:nth-child(${{columnIndex + 1}})`);
                    if (headerCell) {{
                        headerCell.classList.toggle('column-hidden', !isVisible);
                    }}

                    // Hide/show data cells
                    const dataCells = table.querySelectorAll(`tbody tr td:nth-child(${{columnIndex + 1}})`);
                    dataCells.forEach(cell => {{
                        cell.classList.toggle('column-hidden', !isVisible);
                    }});
                }});
            }}

            setupDragAndDrop() {{
                const items = document.querySelectorAll('.column-item');

                items.forEach(item => {{
                    item.addEventListener('dragstart', (e) => {{
                        this.draggedElement = item;
                        item.classList.add('dragging');
                        e.dataTransfer.effectAllowed = 'move';
                    }});

                    item.addEventListener('dragend', () => {{
                        item.classList.remove('dragging');
                        this.draggedElement = null;
                    }});

                    item.addEventListener('dragover', (e) => {{
                        e.preventDefault();
                        e.dataTransfer.dropEffect = 'move';
                    }});

                    item.addEventListener('drop', (e) => {{
                        e.preventDefault();
                        if (this.draggedElement && this.draggedElement !== item) {{
                            this.reorderColumns(this.draggedElement, item);
                        }}
                    }});
                }});
            }}

            reorderColumns(draggedItem, targetItem) {{
                const draggedKey = draggedItem.dataset.column;
                const targetKey = targetItem.dataset.column;

                const draggedIndex = this.columnOrder.indexOf(draggedKey);
                const targetIndex = this.columnOrder.indexOf(targetKey);

                if (draggedIndex !== -1 && targetIndex !== -1) {{
                    // Remove dragged item and insert at target position
                    this.columnOrder.splice(draggedIndex, 1);
                    const newTargetIndex = draggedIndex < targetIndex ? targetIndex - 1 : targetIndex;
                    this.columnOrder.splice(newTargetIndex, 0, draggedKey);

                    this.refreshColumnList();
                    this.reorderTableColumns();
                    this.saveSettings();
                }}
            }}

            reorderTableColumns() {{
                const table = document.querySelector('table');
                if (!table) return;

                // Get current column order based on this.columnOrder
                const headerRow = table.querySelector('thead tr');
                const bodyRows = table.querySelectorAll('tbody tr');

                if (!headerRow) return;

                // Create mapping of current positions
                const currentHeaders = Array.from(headerRow.children);
                const rowNumberHeader = currentHeaders[0]; // Keep row number column first

                // Reorder headers (excluding row number column)
                const newHeaderOrder = [rowNumberHeader];
                this.columnOrder.forEach(key => {{
                    const column = this.columns.find(col => col.key === key);
                    if (column && column.index < currentHeaders.length) {{
                        newHeaderOrder.push(currentHeaders[column.index]);
                    }}
                }});

                // Clear and rebuild header row
                headerRow.innerHTML = '';
                newHeaderOrder.forEach(header => headerRow.appendChild(header));

                // Reorder each data row
                bodyRows.forEach(row => {{
                    const cells = Array.from(row.children);
                    const rowNumberCell = cells[0]; // Keep row number cell first

                    const newCellOrder = [rowNumberCell];
                    this.columnOrder.forEach(key => {{
                        const column = this.columns.find(col => col.key === key);
                        if (column && column.index < cells.length) {{
                            newCellOrder.push(cells[column.index]);
                        }}
                    }});

                    // Clear and rebuild row
                    row.innerHTML = '';
                    newCellOrder.forEach(cell => row.appendChild(cell));
                }});

                // Update column indices to match new positions
                this.columns.forEach((column, index) => {{
                    column.index = index + 1; // +1 for row number column
                }});

                // Reapply visibility after reordering
                this.applyColumnVisibility();
            }}

            applyPreset(presetName) {{
                const presets = {{
                    minimal: ['timestamp', 'channel', 'frequency', 'enabled', 'screenshot_filepath'],
                    frequency: ['timestamp', 'channel', 'frequency', 'peak_frequency', 'peak_amplitude', 'screenshot_filepath'],
                    commands: ['timestamp', 'channel', 'socan_command', 'parsed_socan_response', 'rf_matrix_command', 'parsed_rf_matrix_response'],
                    all: this.columnOrder
                }};

                if (presets[presetName]) {{
                    this.visibleColumns = new Set(presets[presetName]);
                    this.applyColumnVisibility();
                    this.refreshColumnList();
                    this.saveSettings();

                    // Update preset button styling
                    document.querySelectorAll('.preset-button').forEach(btn => btn.classList.remove('active'));
                    event.target.classList.add('active');
                }}
            }}

            resetToDefault() {{
                this.visibleColumns = new Set(this.columnOrder);
                this.applyColumnVisibility();
                this.refreshColumnList();
                this.saveSettings();

                document.querySelectorAll('.preset-button').forEach(btn => btn.classList.remove('active'));
            }}
        }}

        // Initialize column manager when page loads
        let columnManager;
        document.addEventListener('DOMContentLoaded', () => {{
            columnManager = new ColumnManager();
        }});
    </script>
</head>
<body>
    <div class="container">
        <h1>Test Report: {test_name}</h1>

        {column_metadata}

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

    @staticmethod
    def get_index_template() -> str:
        """Get the index page HTML template"""
        return """<!DOCTYPE html>
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
            const contents = document.getElementsByClassName('tab-content');
            for (let content of contents) {{
                content.classList.remove('active');
            }}

            const tabs = document.getElementsByClassName('tab');
            for (let tab of tabs) {{
                tab.classList.remove('active');
            }}

            document.getElementById(tabName).classList.add('active');
            event.target.classList.add('active');
        }}

        window.onload = function() {{
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

        {content}

        <div class="footer">
            <p>Generated on {generation_time}</p>
            <p>{summary_stats}</p>
        </div>
    </div>
</body>
</html>"""