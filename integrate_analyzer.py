#!/usr/bin/env python3
"""
CSV Analyzer Integration Script

This script demonstrates how to integrate the CSV analyzer into your existing
report generator workflow. It provides batch processing and individual test
analysis capabilities.

Usage Examples:
    # Generate analyzer for a single test
    python integrate_analyzer.py --single output/test_dir/test_name_combined.csv
    
    # Generate analyzers for all tests
    python integrate_analyzer.py --batch output/
    
    # Generate analyzers for tests matching pattern
    python integrate_analyzer.py --pattern "*fwd*"
    
    # Generate and open in browser
    python integrate_analyzer.py --single test.csv --open
"""

import os
import sys
import webbrowser
import argparse
from pathlib import Path
from csv_analyzer import CSVToHTMLAnalyzer, process_batch, process_single_file


def main():
    parser = argparse.ArgumentParser(description='CSV Test Results Analyzer')
    parser.add_argument('--single', help='Process single CSV file')
    parser.add_argument('--batch', help='Process all combined CSV files in directory')
    parser.add_argument('--pattern', help='Process files matching glob pattern')
    parser.add_argument('--open', action='store_true', help='Open result in browser')
    parser.add_argument('--output-dir', help='Output directory for HTML files')
    
    args = parser.parse_args()
    
    if args.single:
        process_single_test(args.single, args.output_dir, args.open)
    elif args.batch:
        process_batch_tests(args.batch, args.output_dir, args.open)
    elif args.pattern:
        process_pattern_tests(args.pattern, args.output_dir, args.open)
    else:
        parser.print_help()


def process_single_test(csv_file, output_dir=None, open_browser=False):
    """Process a single CSV file"""
    csv_path = Path(csv_file)
    
    if not csv_path.exists():
        print(f"❌ Error: CSV file not found: {csv_file}")
        return False
        
    if output_dir:
        output_path = Path(output_dir) / f"{csv_path.stem}_analyzer.html"
        output_path.parent.mkdir(parents=True, exist_ok=True)
    else:
        output_path = csv_path.with_name(f"{csv_path.stem}_analyzer.html")
    
    try:
        process_single_file(str(csv_path), str(output_path))
        
        if open_browser:
            webbrowser.open(f"file://{output_path.absolute()}")
            print(f"🌐 Opened in browser: {output_path}")
            
        return True
        
    except Exception as e:
        print(f"❌ Error processing {csv_file}: {e}")
        return False


def process_batch_tests(directory, output_dir=None, open_browser=False):
    """Process all combined CSV files in directory"""
    base_path = Path(directory)
    
    if not base_path.exists():
        print(f"❌ Error: Directory not found: {directory}")
        return False
        
    # Find all combined CSV files
    csv_files = list(base_path.rglob("*combined.csv"))
    
    if not csv_files:
        print(f"ℹ️  No *combined.csv files found in {directory}")
        return False
        
    print(f"📊 Found {len(csv_files)} combined CSV files")
    
    success_count = 0
    generated_files = []
    
    for csv_file in csv_files:
        if output_dir:
            # Maintain directory structure in output
            rel_path = csv_file.relative_to(base_path)
            output_path = Path(output_dir) / rel_path.with_name(f"{rel_path.stem}_analyzer.html")
            output_path.parent.mkdir(parents=True, exist_ok=True)
        else:
            output_path = csv_file.with_name(f"{csv_file.stem}_analyzer.html")
            
        try:
            analyzer = CSVToHTMLAnalyzer()
            analyzer.load_csv(str(csv_file))
            
            # Generate descriptive title
            parts = csv_file.parts
            if len(parts) >= 3:
                test_suite = parts[-3]
                test_name = parts[-2]
                title = f"Test Analysis - {test_suite} - {test_name.replace('_', ' ').title()}"
            else:
                title = f"Test Analysis - {csv_file.stem.replace('_', ' ').title()}"
                
            analyzer.generate_html(str(output_path), title)
            print(f"✅ Generated: {output_path}")
            
            generated_files.append(output_path)
            success_count += 1
            
        except Exception as e:
            print(f"❌ Error processing {csv_file}: {e}")
            continue
    
    print(f"\n📈 Batch processing complete: {success_count}/{len(csv_files)} successful")
    
    if open_browser and generated_files:
        # Open the first generated file as an example
        webbrowser.open(f"file://{generated_files[0].absolute()}")
        print(f"🌐 Opened example in browser: {generated_files[0]}")
        
    return success_count > 0


def process_pattern_tests(pattern, output_dir=None, open_browser=False):
    """Process files matching glob pattern"""
    files = list(Path().glob(pattern))
    csv_files = [f for f in files if f.suffix == '.csv' and 'combined' in f.name]
    
    if not csv_files:
        print(f"ℹ️  No combined CSV files found matching pattern: {pattern}")
        return False
        
    print(f"📊 Found {len(csv_files)} files matching pattern")
    
    success_count = 0
    generated_files = []
    
    for csv_file in csv_files:
        if process_single_test(str(csv_file), output_dir, False):
            success_count += 1
            if output_dir:
                output_path = Path(output_dir) / f"{csv_file.stem}_analyzer.html"
            else:
                output_path = csv_file.with_name(f"{csv_file.stem}_analyzer.html")
            generated_files.append(output_path)
            
    print(f"\n📈 Pattern processing complete: {success_count}/{len(csv_files)} successful")
    
    if open_browser and generated_files:
        webbrowser.open(f"file://{generated_files[0].absolute()}")
        print(f"🌐 Opened example in browser: {generated_files[0]}")
        
    return success_count > 0


def generate_index_page(output_dir):
    """Generate an index page linking to all generated analyzers"""
    output_path = Path(output_dir)
    html_files = list(output_path.rglob("*_analyzer.html"))
    
    if not html_files:
        return None
        
    # Group by test suite
    test_suites = {}
    for html_file in html_files:
        parts = html_file.parts
        suite_name = parts[-3] if len(parts) >= 3 else "Other"
        if suite_name not in test_suites:
            test_suites[suite_name] = []
        test_suites[suite_name].append(html_file)
        
    index_html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Test Analysis Dashboard</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            min-height: 100vh;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}
        
        .header {{
            text-align: center;
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            margin-bottom: 30px;
        }}
        
        .header h1 {{
            margin: 0;
            color: #2c3e50;
            font-size: 2.5em;
        }}
        
        .header p {{
            color: #7f8c8d;
            margin-top: 10px;
            font-size: 1.2em;
        }}
        
        .test-suite {{
            background: white;
            margin-bottom: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        
        .suite-header {{
            background: #3498db;
            color: white;
            padding: 20px;
            font-size: 1.3em;
            font-weight: bold;
        }}
        
        .test-links {{
            padding: 20px;
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 15px;
        }}
        
        .test-link {{
            display: block;
            padding: 15px;
            background: #f8f9fa;
            border: 1px solid #e9ecef;
            border-radius: 8px;
            text-decoration: none;
            color: #495057;
            transition: all 0.2s ease;
        }}
        
        .test-link:hover {{
            background: #e3f2fd;
            border-color: #2196f3;
            transform: translateY(-2px);
        }}
        
        .test-name {{
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 5px;
        }}
        
        .test-description {{
            font-size: 0.9em;
            color: #6c757d;
        }}
        
        .stats {{
            text-align: center;
            margin-top: 30px;
            color: #7f8c8d;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🧪 Test Analysis Dashboard</h1>
            <p>Interactive analysis of test results and logs</p>
        </div>
'''
    
    for suite_name, files in sorted(test_suites.items()):
        index_html += f'''
        <div class="test-suite">
            <div class="suite-header">
                📋 {suite_name.replace('_', ' ').title()} ({len(files)} tests)
            </div>
            <div class="test-links">
'''
        
        for html_file in sorted(files):
            test_name = html_file.stem.replace('_combined_analyzer', '').replace('_', ' ').title()
            rel_path = html_file.relative_to(output_path)
            
            index_html += f'''
                <a href="{rel_path}" class="test-link">
                    <div class="test-name">{test_name}</div>
                    <div class="test-description">Interactive analysis with filtering and column management</div>
                </a>
'''
        
        index_html += '''
            </div>
        </div>
'''
    
    index_html += f'''
        <div class="stats">
            <p>Generated {len(html_files)} test analyzers across {len(test_suites)} test suites</p>
        </div>
    </div>
</body>
</html>'''
    
    index_path = output_path / 'index.html'
    with open(index_path, 'w', encoding='utf-8') as f:
        f.write(index_html)
        
    print(f"📄 Generated index page: {index_path}")
    return index_path


if __name__ == "__main__":
    main()