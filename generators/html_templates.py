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