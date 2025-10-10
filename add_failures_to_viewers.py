#!/usr/bin/env python3
"""
Script to add failure information to viewer and analyzer HTML files.
Reads report.json, extracts failure data, and updates viewer/analyzer HTML files.
"""

import json
import os
import re
from pathlib import Path


def clean_ansi_escapes(text):
    """Remove ANSI escape sequences from text."""
    if not text:
        return ""
    # Remove ANSI escape sequences like \u001b[31m, \u001b[0m, etc.
    ansi_escape = re.compile(r'\x1b\[[0-9;]*[mK]')
    return ansi_escape.sub('', text)


def extract_test_failures(report_json_path):
    """Extract failure information from report.json."""
    try:
        with open(report_json_path, 'r', encoding='utf-8') as f:
            report_data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"  WARNING: Failed to parse JSON file: {e}")
        print(f"  Skipping malformed report.json at line {e.lineno}, column {e.colno}")
        return {}
    except Exception as e:
        print(f"  WARNING: Error reading report.json: {e}")
        return {}

    failures = {}

    # Look through all tests
    for test in report_data.get('tests', []):
        nodeid = test.get('nodeid', '')
        outcome = test.get('outcome', '')
        longrepr = test.get('call', {}).get('longrepr', '')

        # Only process failed tests that have longrepr
        if outcome == 'failed' and longrepr:
            # Clean the nodeid to match directory names
            test_name = nodeid.lstrip('::')

            # Clean ANSI escape sequences
            clean_longrepr = clean_ansi_escapes(longrepr)

            failures[test_name] = {
                'nodeid': nodeid,
                'outcome': outcome,
                'longrepr': clean_longrepr
            }

    return failures


def find_viewer_html_files(base_dir):
    """Find all *_viewer.html and *_analyzer.html files in test directories."""
    viewer_files = []
    base_path = Path(base_dir)
    
    # Look for test directories and viewer files
    for item in base_path.iterdir():
        if item.is_dir() and item.name.startswith('test_'):
            # Look for viewer and analyzer HTML files in this directory
            for html_file in item.glob('*_viewer.html'):
                viewer_files.append(html_file)
            for html_file in item.glob('*_analyzer.html'):
                viewer_files.append(html_file)
    
    return viewer_files


def extract_test_name_from_path(html_path):
    """Extract the test name from the HTML file path."""
    # Example: test_v1_1_fwd__test_fwd_enable_all/test_fwd_enable_all_viewer.html
    # Example: test_v1_1_fwd__test_fwd_freq_sweep/test_fwd_freq_sweep_combined_analyzer.html
    # Should extract: test_fwd_enable_all or test_fwd_freq_sweep
    parent_dir = html_path.parent.name
    
    # Parse the directory name to get the test function name
    # Format: test_module__test_function -> test_function
    if '__' in parent_dir:
        return parent_dir.split('__', 1)[1]
    
    return parent_dir


def add_failure_section_to_html(html_path, failure_info):
    """Add failure section to viewer HTML file."""
    with open(html_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check if failure section already exists
    if 'class="failure-section"' in content:
        print(f"  Failure section already exists in {html_path}, skipping...")
        return False
    
    # Find the header section and add failure info after it
    header_pattern = r'(<div class="header">.*?</div>)'
    
    # Create the failure section HTML
    failure_html = f'''
    <div class="failure-section" style="background: #f8d7da; border: 1px solid #f5c6cb; color: #721c24; padding: 15px; margin: 15px 20px; border-radius: 8px;">
        <h3 style="margin: 0 0 10px 0; color: #721c24;">Test Failure Details</h3>
        <pre style="white-space: pre-wrap; font-family: 'Courier New', monospace; font-size: 12px; margin: 0; background: #fff; padding: 10px; border-radius: 4px; overflow-x: auto;">{failure_info['longrepr']}</pre>
    </div>'''
    
    # Replace the header section with header + failure section
    def replace_header(match):
        return match.group(1) + failure_html
    
    modified_content = re.sub(header_pattern, replace_header, content, flags=re.DOTALL)
    
    # Write the modified content back
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(modified_content)
    
    return True


def main():
    """Main function to process all viewer files."""
    # Set up paths
    base_dir = Path(__file__).parent
    
    # Look for report.json files in output directories
    output_dirs = []
    for item in base_dir.iterdir():
        if item.is_dir() and item.name == 'output':
            for subdir in item.iterdir():
                if subdir.is_dir():
                    report_json = subdir / 'report.json'
                    if report_json.exists():
                        output_dirs.append(subdir)
    
    if not output_dirs:
        print("No output directories with report.json found")
        return
    
    total_processed = 0
    total_skipped = 0
    total_errors = 0

    for output_dir in output_dirs:
        print(f"\nProcessing directory: {output_dir}")

        # Extract failures from report.json
        report_json_path = output_dir / 'report.json'
        failures = extract_test_failures(report_json_path)

        if not failures and report_json_path.exists():
            print(f"  No failed tests found (or JSON parse error)")
            total_skipped += 1
            continue

        print(f"  Found {len(failures)} failed tests")

        # Find viewer and analyzer HTML files
        viewer_files = find_viewer_html_files(output_dir)
        print(f"  Found {len(viewer_files)} viewer/analyzer files")

        # Process each viewer file
        processed_count = 0
        for html_path in viewer_files:
            test_name = extract_test_name_from_path(html_path)

            # Check if this test has failure information
            if test_name in failures:
                print(f"  Adding failure info to: {html_path.name}")
                try:
                    if add_failure_section_to_html(html_path, failures[test_name]):
                        processed_count += 1
                except Exception as e:
                    print(f"  ERROR processing {html_path.name}: {e}")
                    total_errors += 1

        print(f"  ✓ Successfully processed {processed_count} viewer/analyzer files")
        total_processed += processed_count

    print(f"\n{'='*60}")
    print(f"SUMMARY:")
    print(f"  Total campaigns processed: {len(output_dirs)}")
    print(f"  Total HTML files updated: {total_processed}")
    print(f"  Campaigns skipped: {total_skipped}")
    print(f"  Errors encountered: {total_errors}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()