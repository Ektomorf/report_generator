#!/usr/bin/env python3
"""
Generate test campaign browser index.html
"""

import os
import re
import json
from pathlib import Path
from datetime import datetime
import pandas as pd

def get_test_start_time(output_dir, campaign, test_path, test_name):
    """Extract start time from test status JSON file"""
    try:
        status_file = output_dir / campaign / test_path / f'{test_name}_status.json'
        if status_file.exists():
            with open(status_file, 'r', encoding='utf-8') as f:
                status_data = json.load(f)
                start_time_str = status_data.get('start_time', '')
                if start_time_str:
                    # Parse ISO 8601 timestamp
                    return datetime.fromisoformat(start_time_str.replace('Z', '+00:00'))
    except Exception as e:
        print(f'Warning: Could not extract start time for {test_name}: {e}')
    return None

def get_test_status_from_csv(output_dir, campaign, test_path, test_name):
    """
    Determine test status by checking combined.csv for any Pass=False entries.
    Returns 'passed' if no False values in Pass column, 'failed' if any False, 'unknown' if file not found.
    """
    try:
        combined_csv = output_dir / campaign / test_path / f'{test_name}_combined.csv'
        if combined_csv.exists():
            df = pd.read_csv(combined_csv)
            if 'Pass' in df.columns:
                # Check if there's any False value in Pass column
                has_failure = (df['Pass'] == False).any()
                return 'failed' if has_failure else 'passed'
    except Exception as e:
        print(f'Warning: Could not determine status from CSV for {test_name}: {e}')
    return 'unknown'

def extract_campaign_info():
    output_dir = Path('output')
    report_files = list(output_dir.glob('**/report.json'))

    campaigns = {}

    for report_file in report_files:
        # Extract campaign name from path
        campaign = report_file.parent.name

        try:
            with open(report_file, 'r', encoding='utf-8') as f:
                report_data = json.load(f)

            # Extract date from campaign name
            date_match = re.search(r'(\d{6})_(\d{6})', campaign)
            if date_match:
                date_str = date_match.group(1) + date_match.group(2)
                formatted_date = f'20{date_str[4:6]}-{date_str[2:4]}-{date_str[0:2]} {date_str[6:8]}:{date_str[8:10]}:{date_str[10:12]}'
            else:
                formatted_date = 'Unknown'

            campaigns[campaign] = {
                'campaign': campaign,
                'date': formatted_date,
                'tests': []
            }

            # Extract test results from report.json
            if 'tests' in report_data:
                for test in report_data['tests']:
                    nodeid = test.get('nodeid', '')
                    # Remove leading :: from nodeid
                    test_name = nodeid.lstrip(':')

                    # Find the actual directory that contains this test
                    # Look for directories that contain the test name
                    matching_dirs = []
                    for item in report_file.parent.iterdir():
                        if item.is_dir() and item.name.startswith('test_') and test_name in item.name:
                            # More specific match - ensure it's the exact test name after the last __
                            if item.name.endswith(f'__{test_name}') or item.name == f'test_{test_name}':
                                matching_dirs.append(item)
                    
                    if matching_dirs:
                        test_dir = matching_dirs[0]  # Use the first matching directory
                        test_path = test_dir.name
                        
                        # Look for analyzer file in the test directory
                        analyzer_file = f'{test_name}_combined_analyzer.html'
                        analyzer_path = test_dir / analyzer_file
                        
                        if analyzer_path.exists():
                            # Get test start time for chronological ordering
                            start_time = get_test_start_time(output_dir, campaign, test_dir.name, test_name)
                            start_time_str = start_time.strftime('%H:%M:%S') if start_time else 'Unknown'
                            start_timestamp = start_time.timestamp() if start_time else float('inf')

                            # Determine status from combined.csv instead of report.json
                            status = get_test_status_from_csv(output_dir, campaign, test_dir.name, test_name)

                            campaigns[campaign]['tests'].append({
                                'name': test_name,
                                'path': test_path,
                                'file': analyzer_file,
                                'status': status,
                                'start_time': start_time_str,
                                'start_timestamp': start_timestamp
                            })
        except Exception as e:
            print(f'Warning: Could not process {report_file}: {e}')
            continue

    # Also check for analyzer files without corresponding report.json entries
    analyzer_files = list(output_dir.glob('**/*_analyzer.html'))

    for file_path in analyzer_files:
        parts = file_path.parts
        if len(parts) >= 3:
            campaign = parts[1]
            test_dir = parts[2]
            file_name = parts[3]
            test_name = file_name.replace('_combined_analyzer.html', '')

            if campaign not in campaigns:
                # Extract date from campaign name
                date_match = re.search(r'(\d{6})_(\d{6})', campaign)
                if date_match:
                    date_str = date_match.group(1) + date_match.group(2)
                    formatted_date = f'20{date_str[4:6]}-{date_str[2:4]}-{date_str[0:2]} {date_str[6:8]}:{date_str[8:10]}:{date_str[10:12]}'
                else:
                    formatted_date = 'Unknown'

                campaigns[campaign] = {
                    'campaign': campaign,
                    'date': formatted_date,
                    'tests': []
                }

            # Check if this test is already in the campaign
            existing_test = next((t for t in campaigns[campaign]['tests'] if t['name'] == test_name), None)
            if not existing_test:
                # Get test start time for chronological ordering
                start_time = get_test_start_time(output_dir, campaign, test_dir, test_name)
                start_time_str = start_time.strftime('%H:%M:%S') if start_time else 'Unknown'
                start_timestamp = start_time.timestamp() if start_time else float('inf')

                # Determine status from combined.csv
                status = get_test_status_from_csv(output_dir, campaign, test_dir, test_name)

                campaigns[campaign]['tests'].append({
                    'name': test_name,
                    'path': test_dir,
                    'file': file_name,
                    'status': status,
                    'start_time': start_time_str,
                    'start_timestamp': start_timestamp
                })

    # Sort tests within each campaign chronologically
    campaign_list = list(campaigns.values())
    for campaign in campaign_list:
        campaign['tests'].sort(key=lambda x: x['start_timestamp'])
    
    return campaign_list

def generate_index_html():
    # Generate the index.html
    campaign_data = extract_campaign_info()

    html_content = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Test Campaign Browser</title>
    <style>
        * { box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0; padding: 20px; background-color: #f5f5f5; color: #333;
        }
        .container {
            max-width: 1400px; margin: 0 auto; background: white;
            border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); overflow: hidden;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white; padding: 20px; text-align: center;
        }
        .header h1 { margin: 0; font-size: 2.5em; }
        .campaign-section { padding: 20px; border-bottom: 1px solid #dee2e6; }
        .campaign-header {
            background: #f8f9fa; padding: 15px; margin-bottom: 15px;
            border-radius: 8px; border-left: 4px solid #667eea;
        }
        .campaign-title { font-size: 1.5em; font-weight: bold; margin: 0 0 5px 0; color: #495057; }
        .campaign-date { color: #6c757d; font-size: 0.9em; }
        .tests-grid {
            display: grid; grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
            gap: 15px; margin-top: 15px;
        }
        .test-card {
            border: 1px solid #dee2e6; border-radius: 8px; padding: 15px;
            background: white; transition: box-shadow 0.2s;
        }
        .test-card:hover { box-shadow: 0 4px 12px rgba(0,0,0,0.15); }
        .test-card.failed { border-left: 4px solid #dc3545; background: #fff5f5; }
        .test-card.passed { border-left: 4px solid #28a745; background: #f8fff8; }
        .test-card.unknown { border-left: 4px solid #ffc107; background: #fffdf5; }
        .test-name { font-weight: bold; margin-bottom: 5px; color: #495057; }
        .test-path { font-size: 0.85em; color: #6c757d; margin-bottom: 5px; font-family: monospace; }
        .test-time { font-size: 0.9em; color: #28a745; margin-bottom: 10px; font-weight: bold; }
        .test-status {
            display: inline-block; padding: 4px 8px; border-radius: 4px;
            font-size: 0.8em; font-weight: bold; margin-bottom: 10px;
        }
        .status-failed { background: #f8d7da; color: #721c24; }
        .status-passed { background: #d4edda; color: #155724; }
        .status-unknown { background: #fff3cd; color: #856404; }
        .test-link {
            display: inline-block; background: #667eea; color: white;
            padding: 8px 12px; text-decoration: none; border-radius: 4px;
            font-size: 0.9em; transition: background 0.2s;
        }
        .test-link:hover { background: #5a67d8; text-decoration: none; color: white; }
        .summary { padding: 20px; background: #f8f9fa; border-top: 1px solid #dee2e6; }
        .summary-stats {
            display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px; margin-top: 15px;
        }
        .stat-card {
            background: white; padding: 15px; border-radius: 8px;
            text-align: center; border: 1px solid #dee2e6;
        }
        .stat-number { font-size: 2em; font-weight: bold; margin-bottom: 5px; }
        .stat-label { color: #6c757d; font-size: 0.9em; }
        .stat-failed .stat-number { color: #dc3545; }
        .stat-passed .stat-number { color: #28a745; }
        .stat-total .stat-number { color: #667eea; }
        .stat-campaigns .stat-number { color: #6f42c1; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Test Campaign Browser</h1>
            <p>Browse test campaigns and analyze test results</p>
        </div>
        <div id="campaigns-container"></div>
        <div class="summary">
            <h2>Summary Statistics</h2>
            <div class="summary-stats">
                <div class="stat-card stat-total">
                    <div class="stat-number" id="total-tests">0</div>
                    <div class="stat-label">Total Tests</div>
                </div>
                <div class="stat-card stat-passed">
                    <div class="stat-number" id="passed-tests">0</div>
                    <div class="stat-label">Passed Tests</div>
                </div>
                <div class="stat-card stat-failed">
                    <div class="stat-number" id="failed-tests">0</div>
                    <div class="stat-label">Failed Tests</div>
                </div>
                <div class="stat-card stat-campaigns">
                    <div class="stat-number" id="total-campaigns">0</div>
                    <div class="stat-label">Campaigns</div>
                </div>
            </div>
        </div>
    </div>
    <script>
        const testData = ''' + json.dumps(campaign_data) + ''';
        function renderCampaigns() {
            const container = document.getElementById('campaigns-container');
            let totalTests = 0, passedTests = 0, failedTests = 0;
            testData.forEach(campaign => {
                const campaignDiv = document.createElement('div');
                campaignDiv.className = 'campaign-section';
                const campaignHeader = document.createElement('div');
                campaignHeader.className = 'campaign-header';
                campaignHeader.innerHTML = `<div class="campaign-title">${campaign.campaign}</div><div class="campaign-date">Date: ${campaign.date} • Tests shown in chronological order</div>`;
                const testsGrid = document.createElement('div');
                testsGrid.className = 'tests-grid';
                campaign.tests.forEach(test => {
                    totalTests++;
                    const testCard = document.createElement('div');
                    testCard.className = `test-card ${test.status}`;
                    let statusClass = 'status-unknown', statusText = 'Unknown';
                    if (test.status === 'failed') { statusClass = 'status-failed'; statusText = 'FAILED'; failedTests++; }
                    else if (test.status === 'passed') { statusClass = 'status-passed'; statusText = 'PASSED'; passedTests++; }
                    testCard.innerHTML = `<div class="test-name">${test.name}</div><div class="test-path">${test.path}</div><div class="test-time">⏱️ Started: ${test.start_time}</div><div class="test-status ${statusClass}">${statusText}</div><a href="${campaign.campaign}/${test.path}/${test.file}" class="test-link" target="_blank">View Analysis →</a>`;
                    testsGrid.appendChild(testCard);
                });
                campaignDiv.appendChild(campaignHeader);
                campaignDiv.appendChild(testsGrid);
                container.appendChild(campaignDiv);
            });
            document.getElementById('total-tests').textContent = totalTests;
            document.getElementById('passed-tests').textContent = passedTests;
            document.getElementById('failed-tests').textContent = failedTests;
            document.getElementById('total-campaigns').textContent = testData.length;
        }
        document.addEventListener('DOMContentLoaded', renderCampaigns);
    </script>
</body>
</html>'''

    with open('output/index.html', 'w', encoding='utf-8') as f:
        f.write(html_content)

    print('Test campaign browser index.html generated successfully!')

if __name__ == '__main__':
    generate_index_html()