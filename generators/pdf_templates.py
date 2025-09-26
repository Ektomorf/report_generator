#!/usr/bin/env python3
"""
PDF-specific HTML templates for report generation.
"""


class PDFTemplates:
    """Container for PDF-optimized HTML templates"""

    @staticmethod
    def get_main_template() -> str:
        """Get the main PDF HTML report template with optimized styling"""
        return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Test Report: {test_name}</title>
    <style>
        @page {{
            size: A2 landscape;  /* Use A2 (420mm x 594mm) in landscape for extra width */
            margin: 15mm;
            @top-center {{
                content: "Test Report: {test_name}";
                font-family: 'Arial', sans-serif;
                font-size: 12pt;
                font-weight: bold;
            }}
            @bottom-center {{
                content: "Page " counter(page) " of " counter(pages);
                font-family: 'Arial', sans-serif;
                font-size: 10pt;
            }}
        }}

        body {{
            font-family: 'Arial', sans-serif;
            margin: 0;
            padding: 0;
            font-size: 9pt;
            line-height: 1.3;
            color: #333;
        }}

        .container {{
            width: 100%;
            padding: 0;
        }}

        h1 {{
            font-size: 18pt;
            color: #2c3e50;
            border-bottom: 2pt solid #3498db;
            padding-bottom: 5pt;
            margin-bottom: 15pt;
            page-break-after: avoid;
        }}

        h2 {{
            font-size: 14pt;
            color: #34495e;
            margin-top: 20pt;
            margin-bottom: 10pt;
            page-break-after: avoid;
        }}

        h3 {{
            font-size: 12pt;
            color: #34495e;
            margin-top: 15pt;
            margin-bottom: 8pt;
            page-break-after: avoid;
        }}

        .status-info {{
            padding: 8pt;
            border-radius: 3pt;
            margin-bottom: 10pt;
            page-break-inside: avoid;
        }}

        .status-info.passed {{
            background-color: #d4edda;
            border: 1pt solid #c3e6cb;
            color: #155724;
        }}

        .status-info.failed {{
            background-color: #f8d7da;
            border: 1pt solid #f5c6cb;
            color: #721c24;
        }}

        .params-info, .description-info {{
            background-color: #f8f9fa;
            padding: 8pt;
            border-radius: 3pt;
            margin-bottom: 10pt;
            page-break-inside: avoid;
            border-left: 3pt solid #007bff;
        }}

        .test-description {{
            margin: 0;
            font-style: italic;
            line-height: 1.4;
            color: #495057;
        }}

        /* Table styles optimized for wide tables */
        .table-container {{
            width: 100%;
            margin: 10pt 0;
            page-break-inside: avoid;
            overflow: visible;
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 0;
            font-size: 7pt;  /* Smaller font for more columns */
            table-layout: auto;
        }}

        th, td {{
            padding: 3pt 2pt;
            text-align: left;
            border: 0.5pt solid #ddd;
            vertical-align: top;
            word-wrap: break-word;
            word-break: break-word;
            hyphens: auto;
            max-width: 30mm;  /* Slightly increased column width */
            overflow-wrap: break-word;
            line-height: 1.2;
            white-space: normal;
        }}

        th {{
            background-color: #3498db;
            color: white;
            font-weight: bold;
            font-size: 7pt;
            white-space: nowrap;
            text-align: center;
        }}

        /* Row number column - keep narrow */
        th:first-child, td:first-child {{
            width: 8mm;
            text-align: center;
            max-width: 8mm;
        }}

        /* Special column types */
        .command {{
            font-family: 'Courier New', monospace;
            font-size: 6pt;
            max-width: 35mm;  /* Increased width */
            word-break: break-all;
            overflow-wrap: break-word;
            white-space: pre-wrap;  /* Preserve line breaks and wrap */
        }}

        .response {{
            font-family: 'Courier New', monospace;
            font-size: 6pt;
            max-width: 40mm;  /* Increased width */
            word-break: break-all;
            overflow-wrap: break-word;
            white-space: pre-wrap;
        }}

        .parsed-response {{
            font-family: 'Courier New', monospace;
            font-size: 6pt;
            max-width: 45mm;  /* Increased width */
            word-break: break-all;
            overflow-wrap: break-word;
            white-space: pre-wrap;
        }}

        .numeric {{
            text-align: right;
            font-family: 'Courier New', monospace;
            white-space: nowrap;
            font-size: 7pt;
        }}

        /* Zebra striping for readability */
        tr:nth-child(even) {{
            background-color: #f8f9fa;
        }}

        /* Long content handling */
        .cell-content {{
            max-height: 20mm;  /* Increased height */
            overflow: visible;  /* Allow content to be visible */
            word-wrap: break-word;
            word-break: break-word;
            overflow-wrap: break-word;
            display: block;
            hyphens: auto;
            line-height: 1.1;
        }}

        /* Screenshots section */
        .screenshots {{
            margin-top: 20pt;
        }}

        .screenshot {{
            margin-bottom: 15pt;
            text-align: center;
            page-break-inside: avoid;
        }}

        .screenshot img {{
            max-width: 100%;
            max-height: 200mm;  /* Limit image height */
            border: 1pt solid #ddd;
        }}

        .screenshot h4 {{
            font-size: 10pt;
            margin-bottom: 5pt;
        }}

        /* Footer */
        .footer {{
            margin-top: 20pt;
            padding-top: 10pt;
            border-top: 1pt solid #ddd;
            color: #666;
            font-size: 8pt;
            text-align: center;
        }}

        /* Page break controls */
        .page-break {{
            page-break-before: always;
        }}

        .no-break {{
            page-break-inside: avoid;
        }}

        /* List styles */
        ul {{
            margin: 5pt 0;
            padding-left: 15pt;
        }}

        li {{
            margin-bottom: 2pt;
            font-size: 8pt;
        }}

        /* Error message styling */
        .error-message {{
            font-family: 'Courier New', monospace;
            font-size: 6pt;
            color: #721c24;
            max-width: 30mm;
            word-break: break-all;
        }}

        .error-message.scrollable {{
            max-height: 15mm;
            overflow: hidden;
            border: 0.5pt solid #d6d8db;
            padding: 2pt;
            background-color: #f8f8f8;
            font-size: 5pt;
        }}

        .longrepr-section {{
            margin-top: 8pt;
            padding: 6pt;
            background-color: #fff3cd;
            border: 0.5pt solid #ffeaa7;
            border-radius: 2pt;
        }}

        .longrepr-section h4 {{
            margin-top: 0;
            color: #856404;
            font-size: 8pt;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Test Report: {test_name}</h1>

        <div class="no-break">
            {status_info}
        </div>

        <div class="no-break">
            {description_info}
        </div>

        <div class="no-break">
            {params_info}
        </div>

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

        <div class="page-break">
            <h2>Screenshots</h2>
            {screenshot_html}
        </div>

        <div class="footer">
            <p>Report generated on {generation_time}</p>
        </div>
    </div>
</body>
</html>"""

    @staticmethod
    def get_index_template() -> str:
        """Get the index page PDF template"""
        return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Test Reports Index - {test_session}</title>
    <style>
        @page {{
            size: A4 landscape;
            margin: 15mm;
            @top-center {{
                content: "Test Reports Index - {test_session}";
                font-family: 'Arial', sans-serif;
                font-size: 12pt;
                font-weight: bold;
            }}
            @bottom-center {{
                content: "Page " counter(page) " of " counter(pages);
                font-family: 'Arial', sans-serif;
                font-size: 10pt;
            }}
        }}

        body {{
            font-family: 'Arial', sans-serif;
            margin: 0;
            padding: 0;
            font-size: 9pt;
            line-height: 1.4;
            color: #333;
        }}

        .container {{
            width: 100%;
            padding: 0;
        }}

        h1, h2 {{
            color: #2c3e50;
            border-bottom: 2pt solid #3498db;
            padding-bottom: 5pt;
            page-break-after: avoid;
        }}

        h1 {{
            font-size: 18pt;
            margin-bottom: 15pt;
        }}

        h2 {{
            font-size: 14pt;
            margin-top: 20pt;
            margin-bottom: 10pt;
        }}

        h3, h4 {{
            color: #34495e;
            page-break-after: avoid;
        }}

        h3 {{
            font-size: 12pt;
            margin-top: 15pt;
            margin-bottom: 8pt;
        }}

        h4 {{
            font-size: 10pt;
            margin-top: 10pt;
            margin-bottom: 5pt;
        }}

        .test-run {{
            margin: 15pt 0;
            border: 1pt solid #e0e0e0;
            border-radius: 3pt;
            page-break-inside: avoid;
        }}

        .test-run-header {{
            background-color: #3498db;
            color: white;
            padding: 8pt;
            font-weight: bold;
            font-size: 11pt;
        }}

        .test-run-content {{
            padding: 8pt;
        }}

        .results-table {{
            width: 100%;
            border-collapse: collapse;
            margin: 8pt 0;
            font-size: 8pt;
        }}

        .results-table th, .results-table td {{
            padding: 4pt;
            text-align: left;
            border: 0.5pt solid #ddd;
        }}

        .results-table th {{
            background-color: #3498db;
            color: white;
            font-weight: bold;
            font-size: 8pt;
        }}

        .results-table tr:nth-child(even) {{
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

        .report-list {{
            list-style: none;
            padding: 0;
            margin: 8pt 0;
        }}

        .report-list li {{
            margin: 0;
            padding: 4pt;
            background-color: #f8f9fa;
            border-bottom: 0.5pt solid #e0e0e0;
            font-size: 8pt;
        }}

        .error-message {{
            font-family: 'Courier New', monospace;
            font-size: 7pt;
            max-width: 40mm;
            word-wrap: break-word;
            color: #721c24;
        }}

        .error-message.scrollable {{
            max-height: 20mm;
            overflow: hidden;
            border: 0.5pt solid #d6d8db;
            padding: 2pt;
            background-color: #f8f8f8;
            font-size: 6pt;
        }}

        .longrepr-section {{
            margin-top: 10pt;
            padding: 8pt;
            background-color: #fff3cd;
            border: 0.5pt solid #ffeaa7;
            border-radius: 3pt;
        }}

        .longrepr-section h4 {{
            margin-top: 0;
            color: #856404;
            font-size: 9pt;
        }}

        .footer {{
            margin-top: 20pt;
            text-align: center;
            color: #666;
            font-size: 8pt;
            border-top: 1pt solid #ddd;
            padding-top: 10pt;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Test Reports Index</h1>
        <h2>Test Session: {test_session}</h2>

        {content}

        <div class="footer">
            <p>Generated on {generation_time}</p>
            <p>{summary_stats}</p>
        </div>
    </div>
</body>
</html>"""