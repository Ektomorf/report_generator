#!/usr/bin/env python3
"""
Generate test campaign browser index.html
"""

import os
import re
import json
import hashlib
from pathlib import Path
from datetime import datetime
import pandas as pd

def generate_campaign_id(campaign_name, date_str):
    """Generate a unique campaign ID based on campaign name and date"""
    combined = f"{campaign_name}_{date_str}"
    hash_obj = hashlib.md5(combined.encode('utf-8'))
    hash_hex = hash_obj.hexdigest()[:8].upper()
    return f"CAMP-{hash_hex}"

def generate_test_id(campaign_name, test_name, test_path):
    """Generate a unique test ID based on campaign, test name, and path"""
    combined = f"{campaign_name}_{test_name}_{test_path}"
    hash_obj = hashlib.md5(combined.encode('utf-8'))
    hash_hex = hash_obj.hexdigest()[:8].upper()
    return f"TEST-{hash_hex}"

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

def get_failure_messages_from_csv(output_dir, campaign, test_path, test_name):
    """
    Extract all failure messages from combined.csv where Pass=False.
    Returns list of failure messages.
    """
    try:
        combined_csv = output_dir / campaign / test_path / f'{test_name}_combined.csv'
        if combined_csv.exists():
            df = pd.read_csv(combined_csv)
            if 'Pass' in df.columns and 'Failure_Messages' in df.columns:
                # Get rows where Pass is False
                failed_rows = df[df['Pass'] == False]
                # Extract non-null Failure_Messages
                messages = failed_rows['Failure_Messages'].dropna().tolist()
                return messages
    except Exception as e:
        print(f'Warning: Could not extract failure messages for {test_name}: {e}')
    return []

def get_commits_from_status(output_dir, campaign, test_path, test_name):
    """
    Extract git commit information from test status JSON file.
    Returns dict of {repo_name: commit_hash}.
    """
    try:
        status_file = output_dir / campaign / test_path / f'{test_name}_status.json'
        if status_file.exists():
            with open(status_file, 'r', encoding='utf-8') as f:
                status_data = json.load(f)
                if 'commits' in status_data:
                    return status_data['commits']
    except Exception as e:
        print(f'Warning: Could not extract commits for {test_name}: {e}')
    return {}

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

            campaign_id = generate_campaign_id(campaign, formatted_date)
            campaigns[campaign] = {
                'campaign': campaign,
                'campaign_id': campaign_id,
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

                            # Get failure messages
                            failure_messages = get_failure_messages_from_csv(output_dir, campaign, test_dir.name, test_name)

                            # Get commit information
                            commits = get_commits_from_status(output_dir, campaign, test_dir.name, test_name)

                            test_id = generate_test_id(campaign, test_name, test_path)
                            campaigns[campaign]['tests'].append({
                                'name': test_name,
                                'test_id': test_id,
                                'path': test_path,
                                'file': analyzer_file,
                                'status': status,
                                'start_time': start_time_str,
                                'start_timestamp': start_timestamp,
                                'failure_messages': failure_messages,
                                'commits': commits
                            })
        except Exception as e:
            print(f'Warning: Could not process {report_file}: {e}')
            continue

    # Also check for analyzer files without corresponding report.json entries
    analyzer_files = list(output_dir.glob('**/*_analyzer.html'))

    for file_path in analyzer_files:
        parts = file_path.parts

        # Skip campaign-level _all_logs_combined_analyzer.html files (these are aggregated logs, not individual tests)
        if '_all_logs_combined_analyzer.html' in str(file_path):
            continue

        if len(parts) >= 4:  # Need at least: output/campaign/test_dir/file_name
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

                campaign_id = generate_campaign_id(campaign, formatted_date)
                campaigns[campaign] = {
                    'campaign': campaign,
                    'campaign_id': campaign_id,
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

                # Get failure messages
                failure_messages = get_failure_messages_from_csv(output_dir, campaign, test_dir, test_name)

                # Get commit information
                commits = get_commits_from_status(output_dir, campaign, test_dir, test_name)

                test_id = generate_test_id(campaign, test_name, test_dir)
                campaigns[campaign]['tests'].append({
                    'name': test_name,
                    'test_id': test_id,
                    'path': test_dir,
                    'file': file_name,
                    'status': status,
                    'start_time': start_time_str,
                    'start_timestamp': start_timestamp,
                    'failure_messages': failure_messages,
                    'commits': commits
                })

    # Sort tests within each campaign chronologically
    campaign_list = list(campaigns.values())
    for campaign in campaign_list:
        campaign['tests'].sort(key=lambda x: x['start_timestamp'])

    # Sort campaigns chronologically by date (newest first)
    def get_campaign_timestamp(campaign):
        date_match = re.search(r'(\d{6})_(\d{6})', campaign['campaign'])
        if date_match:
            date_str = date_match.group(1) + date_match.group(2)
            # Parse: DDMMYY_HHMMSS -> timestamp
            try:
                dt = datetime.strptime(date_str, '%d%m%y%H%M%S')
                return dt.timestamp()
            except:
                pass
        return 0  # Unknown dates go to the end

    campaign_list.sort(key=get_campaign_timestamp, reverse=True)

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
        .filter-controls {
            padding: 15px 20px; background: #f8f9fa; border-bottom: 2px solid #dee2e6;
            display: flex; gap: 10px; align-items: center; flex-wrap: wrap;
        }
        .filter-input {
            flex: 1; min-width: 250px; padding: 8px 12px;
            border: 1px solid #ddd; border-radius: 4px; font-size: 14px;
        }
        .filter-btn {
            padding: 8px 16px; border: none; border-radius: 4px;
            cursor: pointer; font-size: 14px; font-weight: bold;
            transition: background-color 0.2s;
        }
        .filter-btn-primary {
            background: #dc3545; color: white;
        }
        .filter-btn-primary:hover { background: #c82333; }
        .filter-btn-secondary {
            background: #6c757d; color: white;
        }
        .filter-btn-secondary:hover { background: #545b62; }
        .filter-btn-export {
            background: #28a745; color: white;
        }
        .filter-btn-export:hover { background: #218838; }
        .filter-info {
            font-size: 0.9em; color: #6c757d; font-style: italic;
        }
        .campaign-section { padding: 20px; border-bottom: 1px solid #dee2e6; }
        .campaign-header {
            background: #f8f9fa; padding: 15px; margin-bottom: 0;
            border-radius: 8px; border-left: 4px solid #667eea;
            cursor: pointer; user-select: none;
            transition: background-color 0.2s;
            display: flex; justify-content: space-between; align-items: center;
        }
        .campaign-header:hover { background: #e9ecef; }
        .campaign-header-left { flex: 1; }
        .campaign-title { font-size: 1.5em; font-weight: bold; margin: 0 0 5px 0; color: #495057; }
        .campaign-toggle {
            font-size: 1.5em; color: #667eea; font-weight: bold;
            transition: transform 0.3s; margin-left: 15px;
        }
        .campaign-toggle.expanded { transform: rotate(90deg); }
        .campaign-date { color: #6c757d; font-size: 0.9em; }
        .campaign-commits {
            margin-top: 10px; padding: 10px; background: #e6f3ff;
            border-radius: 4px; border-left: 3px solid #2196F3;
        }
        .campaign-commits-title {
            font-size: 0.85em; font-weight: bold; color: #0d47a1;
            margin-bottom: 5px;
        }
        .campaign-commit {
            font-size: 0.75em; color: #495057; margin: 3px 0;
            font-family: monospace;
        }
        .campaign-commit-repo {
            font-weight: bold; color: #0d47a1; margin-right: 5px;
        }
        .campaign-commit-hash {
            color: #6c757d;
        }
        .campaign-content {
            max-height: 0; overflow: hidden;
            transition: max-height 0.3s ease-out;
        }
        .campaign-content.expanded {
            max-height: 10000px; transition: max-height 0.5s ease-in;
        }
        .tests-table-wrapper {
            margin-top: 15px; overflow-x: auto;
        }
        .tests-table {
            width: 100%; border-collapse: collapse; background: white;
            font-size: 0.9em;
        }
        .tests-table th {
            background: #f8f9fa; padding: 12px 10px; text-align: left;
            border-bottom: 2px solid #dee2e6; font-weight: bold;
            color: #495057; position: sticky; top: 0;
        }
        .tests-table td {
            padding: 10px; border-bottom: 1px solid #dee2e6;
            vertical-align: top;
        }
        .tests-table tr.hidden { display: none; }
        .tests-table tbody tr.failed { background: #fff5f5; border-left: 4px solid #dc3545; }
        .tests-table tbody tr.passed { background: #f8fff8; border-left: 4px solid #28a745; }
        .tests-table tbody tr.unknown { background: #fffdf5; border-left: 4px solid #ffc107; }
        .tests-table tbody tr:hover { background: #f1f3f5; }
        .test-name { font-weight: bold; color: #495057; }
        .test-path { font-size: 0.85em; color: #6c757d; font-family: monospace; }
        .test-time { font-size: 0.9em; color: #6c757d; }
        .test-status {
            display: inline-block; padding: 4px 8px; border-radius: 4px;
            font-size: 0.85em; font-weight: bold; white-space: nowrap;
        }
        .status-failed { background: #f8d7da; color: #721c24; }
        .status-passed { background: #d4edda; color: #155724; }
        .status-unknown { background: #fff3cd; color: #856404; }
        .test-link {
            display: inline-block; background: #667eea; color: white;
            padding: 6px 12px; text-decoration: none; border-radius: 4px;
            font-size: 0.85em; transition: background 0.2s; white-space: nowrap;
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
        .test-failures {
            margin-top: 8px; padding: 6px; background: #fff5f5;
            border-radius: 4px; border: 1px solid #f5c6cb;
            max-height: 100px; overflow-y: auto;
        }
        .test-failures-title {
            font-size: 0.65em; font-weight: bold; color: #dc3545;
            margin-bottom: 3px; text-transform: uppercase;
        }
        .test-failure-msg {
            font-size: 0.55em; color: #721c24; margin: 2px 0;
            padding: 2px 4px; background: white; border-radius: 2px;
            font-family: 'Courier New', monospace; line-height: 1.2;
            word-break: break-word;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Test Campaign Browser</h1>
            <p>Browse test campaigns and analyze test results</p>
        </div>
        <div class="filter-controls">
            <input type="text" id="general-filter" class="filter-input" placeholder="Filter by test name, failure message, test ID, or campaign ID..." onkeyup="applyGeneralFilter()">
            <input type="text" id="test-id-filter" class="filter-input" placeholder="Filter by Test ID (e.g., TEST-1234ABCD)..." onkeyup="applyTestIdFilter()" style="max-width: 200px;">
            <input type="text" id="campaign-id-filter" class="filter-input" placeholder="Filter by Campaign ID (e.g., CAMP-5678EFGH)..." onkeyup="applyCampaignIdFilter()" style="max-width: 200px;">
            <button class="filter-btn filter-btn-primary" onclick="showOnlyFailures()">Show Only Failed Tests</button>
            <button class="filter-btn filter-btn-secondary" onclick="clearAllFilters()">Clear All Filters</button>
            <button class="filter-btn filter-btn-export" onclick="exportFailuresToCSV()">📥 Export All Failures to CSV</button>
            <span id="filter-info" class="filter-info"></span>
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

        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }

        function toggleCampaign(campaignId) {
            const content = document.getElementById(`campaign-content-${campaignId}`);
            const toggle = document.getElementById(`campaign-toggle-${campaignId}`);
            content.classList.toggle('expanded');
            toggle.classList.toggle('expanded');
        }

        function renderCampaigns() {
            const container = document.getElementById('campaigns-container');
            let totalTests = 0, passedTests = 0, failedTests = 0;
            testData.forEach((campaign, index) => {
                const campaignDiv = document.createElement('div');
                campaignDiv.className = 'campaign-section';
                campaignDiv.dataset.campaignId = campaign.campaign_id;
                campaignDiv.dataset.campaignName = campaign.campaign;
                const campaignHeader = document.createElement('div');
                campaignHeader.className = 'campaign-header';
                campaignHeader.onclick = () => toggleCampaign(index);

                // Build commits HTML for campaign header
                let commitsHtml = '';
                if (campaign.tests && campaign.tests.length > 0 && campaign.tests[0].commits) {
                    const commits = campaign.tests[0].commits;
                    if (Object.keys(commits).length > 0) {
                        const commitItems = Object.entries(commits).map(([repo, hash]) =>
                            `<div class="campaign-commit"><span class="campaign-commit-repo">${repo}:</span><span class="campaign-commit-hash">${hash.substring(0, 8)} (${hash})</span></div>`
                        ).join('');
                        commitsHtml = `<div class="campaign-commits"><div class="campaign-commits-title">Git Commits:</div>${commitItems}</div>`;
                    }
                }

                campaignHeader.innerHTML = `
                    <div class="campaign-header-left">
                        <div class="campaign-title">${campaign.campaign} <span style="font-size: 0.8em; color: #6c757d; font-weight: normal;">[${campaign.campaign_id}]</span></div>
                        <div class="campaign-date">Date: ${campaign.date} • Tests shown in chronological order</div>
                        ${commitsHtml}
                    </div>
                    <div class="campaign-toggle" id="campaign-toggle-${index}">▶</div>
                `;

                const campaignContent = document.createElement('div');
                campaignContent.className = 'campaign-content';
                campaignContent.id = `campaign-content-${index}`;

                const tableWrapper = document.createElement('div');
                tableWrapper.className = 'tests-table-wrapper';

                const table = document.createElement('table');
                table.className = 'tests-table';

                // Create table header
                const thead = document.createElement('thead');
                thead.innerHTML = `
                    <tr>
                        <th>Test Name</th>
                        <th>Test ID</th>
                        <th>Status</th>
                        <th>Start Time</th>
                        <th>Failure Count</th>
                        <th>Action</th>
                    </tr>
                `;
                table.appendChild(thead);

                const tbody = document.createElement('tbody');
                campaign.tests.forEach(test => {
                    totalTests++;
                    const row = document.createElement('tr');
                    row.className = test.status;
                    row.dataset.testName = test.name;
                    row.dataset.testId = test.test_id;
                    row.dataset.testStatus = test.status;
                    row.dataset.campaignId = campaign.campaign_id;
                    row.dataset.campaignName = campaign.campaign;

                    let statusClass = 'status-unknown', statusText = 'Unknown';
                    if (test.status === 'failed') { statusClass = 'status-failed'; statusText = 'FAILED'; failedTests++; }
                    else if (test.status === 'passed') { statusClass = 'status-passed'; statusText = 'PASSED'; passedTests++; }

                    // Count failures
                    const failureCount = test.failure_messages ? test.failure_messages.length : 0;
                    const failureDisplay = failureCount > 0 ? failureCount : '-';

                    // Store failure messages in dataset for filtering
                    if (test.failure_messages && test.failure_messages.length > 0) {
                        row.dataset.failureMessages = test.failure_messages.join(' ');
                    }

                    row.innerHTML = `
                        <td><div class="test-name">${test.name}</div></td>
                        <td><div style="font-family: monospace; font-size: 0.9em; color: #6c757d;">${test.test_id}</div></td>
                        <td><div class="test-status ${statusClass}">${statusText}</div></td>
                        <td><div class="test-time">${test.start_time}</div></td>
                        <td>${failureDisplay}</td>
                        <td><a href="${campaign.campaign}/${test.path}/${test.file}" class="test-link" target="_blank">View →</a></td>
                    `;
                    tbody.appendChild(row);
                });
                table.appendChild(tbody);
                tableWrapper.appendChild(table);
                campaignContent.appendChild(tableWrapper);

                campaignDiv.appendChild(campaignHeader);
                campaignDiv.appendChild(campaignContent);
                container.appendChild(campaignDiv);
            });
            document.getElementById('total-tests').textContent = totalTests;
            document.getElementById('passed-tests').textContent = passedTests;
            document.getElementById('failed-tests').textContent = failedTests;
            document.getElementById('total-campaigns').textContent = testData.length;
        }

        function applyGeneralFilter() {
            applyAllFilters();
        }

        function applyTestIdFilter() {
            applyAllFilters();
        }

        function applyCampaignIdFilter() {
            applyAllFilters();
        }

        function applyAllFilters() {
            const generalFilter = document.getElementById('general-filter').value.toLowerCase();
            const testIdFilter = document.getElementById('test-id-filter').value.toLowerCase();
            const campaignIdFilter = document.getElementById('campaign-id-filter').value.toLowerCase();
            
            const testRows = document.querySelectorAll('.tests-table tbody tr');
            const campaigns = document.querySelectorAll('.campaign-section');
            let visibleTestCount = 0;
            let hiddenTestCount = 0;
            let activeCampaigns = new Set();

            testRows.forEach(row => {
                const testName = (row.dataset.testName || '').toLowerCase();
                const testId = (row.dataset.testId || '').toLowerCase();
                const campaignId = (row.dataset.campaignId || '').toLowerCase();
                const campaignName = (row.dataset.campaignName || '').toLowerCase();
                const failureMessages = (row.dataset.failureMessages || '').toLowerCase();

                let showTest = true;

                // Apply general filter (matches test name, failure messages, test ID, or campaign ID)
                if (generalFilter) {
                    showTest = showTest && (
                        testName.includes(generalFilter) ||
                        failureMessages.includes(generalFilter) ||
                        testId.includes(generalFilter) ||
                        campaignId.includes(generalFilter) ||
                        campaignName.includes(generalFilter)
                    );
                }

                // Apply test ID filter
                if (testIdFilter) {
                    showTest = showTest && testId.includes(testIdFilter);
                }

                // Apply campaign ID filter
                if (campaignIdFilter) {
                    showTest = showTest && campaignId.includes(campaignIdFilter);
                }

                if (showTest) {
                    row.classList.remove('hidden');
                    visibleTestCount++;
                    activeCampaigns.add(campaignId);
                } else {
                    row.classList.add('hidden');
                    hiddenTestCount++;
                }
            });

            // Hide/show campaigns based on whether they have visible tests
            campaigns.forEach(campaign => {
                const campaignId = campaign.dataset.campaignId.toLowerCase();
                if (activeCampaigns.has(campaignId) || (!generalFilter && !testIdFilter && !campaignIdFilter)) {
                    campaign.style.display = 'block';
                } else {
                    campaign.style.display = 'none';
                }
            });

            updateFilterInfo(visibleTestCount, hiddenTestCount);
        }

        function showOnlyFailures() {
            // First clear all filters
            clearAllFilters();
            
            const testRows = document.querySelectorAll('.tests-table tbody tr');
            const campaigns = document.querySelectorAll('.campaign-section');
            let visibleCount = 0;
            let hiddenCount = 0;
            let activeCampaigns = new Set();

            testRows.forEach(row => {
                if (row.dataset.testStatus === 'failed') {
                    row.classList.remove('hidden');
                    visibleCount++;
                    activeCampaigns.add(row.dataset.campaignId.toLowerCase());
                } else {
                    row.classList.add('hidden');
                    hiddenCount++;
                }
            });

            // Hide campaigns with no failed tests
            campaigns.forEach(campaign => {
                const campaignId = campaign.dataset.campaignId.toLowerCase();
                if (activeCampaigns.has(campaignId)) {
                    campaign.style.display = 'block';
                } else {
                    campaign.style.display = 'none';
                }
            });

            updateFilterInfo(visibleCount, hiddenCount, 'failed tests only');
        }

        function clearAllFilters() {
            document.getElementById('general-filter').value = '';
            document.getElementById('test-id-filter').value = '';
            document.getElementById('campaign-id-filter').value = '';
            
            const testRows = document.querySelectorAll('.tests-table tbody tr');
            const campaigns = document.querySelectorAll('.campaign-section');
            
            testRows.forEach(row => row.classList.remove('hidden'));
            campaigns.forEach(campaign => campaign.style.display = 'block');
            
            document.getElementById('filter-info').textContent = '';
        }

        function updateFilterInfo(visibleCount, hiddenCount, filterText) {
            const info = document.getElementById('filter-info');
            const generalFilter = document.getElementById('general-filter').value;
            const testIdFilter = document.getElementById('test-id-filter').value;
            const campaignIdFilter = document.getElementById('campaign-id-filter').value;
            
            let activeFilters = [];
            if (generalFilter) activeFilters.push(`general: "${generalFilter}"`);
            if (testIdFilter) activeFilters.push(`test ID: "${testIdFilter}"`);
            if (campaignIdFilter) activeFilters.push(`campaign ID: "${campaignIdFilter}"`);
            if (filterText) activeFilters.push(filterText);
            
            if (hiddenCount > 0 || activeFilters.length > 0) {
                const filterInfo = activeFilters.length > 0 ? ` (${activeFilters.join(', ')})` : '';
                info.textContent = `Showing ${visibleCount} test(s), hiding ${hiddenCount} test(s)${filterInfo}`;
            } else {
                info.textContent = visibleCount > 0 ? `Showing all ${visibleCount} test(s)` : '';
            }
        }

        function exportFailuresToCSV() {
            // Collect all failures across all campaigns in chronological order
            const failures = [];

            testData.forEach(campaign => {
                campaign.tests.forEach(test => {
                    if (test.status === 'failed' && test.failure_messages && test.failure_messages.length > 0) {
                        test.failure_messages.forEach(message => {
                            failures.push({
                                campaign: campaign.campaign,
                                campaign_id: campaign.campaign_id,
                                campaign_date: campaign.date,
                                test_name: test.name,
                                test_id: test.test_id,
                                test_path: test.path,
                                start_time: test.start_time,
                                start_timestamp: test.start_timestamp,
                                failure_message: message
                            });
                        });
                    }
                });
            });

            // Sort failures chronologically by start_timestamp
            failures.sort((a, b) => a.start_timestamp - b.start_timestamp);

            if (failures.length === 0) {
                alert('No failures found to export!');
                return;
            }

            // Helper function to escape CSV values
            function escapeCsvValue(value) {
                if (value === null || value === undefined) {
                    return '';
                }
                let strValue = String(value);
                // Escape double quotes by doubling them
                strValue = strValue.replace(/"/g, '""');
                // Always quote to handle newlines, commas, and quotes
                return `"${strValue}"`;
            }

            // Build CSV content
            const csvRows = [];

            // Add header
            csvRows.push([
                'Campaign',
                'Campaign ID',
                'Campaign Date',
                'Test Name',
                'Test ID',
                'Test Path',
                'Start Time',
                'Failure Message'
            ].map(h => escapeCsvValue(h)).join(','));

            // Add data rows
            failures.forEach(failure => {
                csvRows.push([
                    failure.campaign,
                    failure.campaign_id,
                    failure.campaign_date,
                    failure.test_name,
                    failure.test_id,
                    failure.test_path,
                    failure.start_time,
                    failure.failure_message
                ].map(v => escapeCsvValue(v)).join(','));
            });

            const csvContent = csvRows.join('\\n');

            // Create and download the file
            const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;

            // Generate filename with timestamp
            const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, -5);
            a.download = `all_failures_${failures.length}_items_${timestamp}.csv`;

            a.click();
            window.URL.revokeObjectURL(url);

            console.log(`Exported ${failures.length} failure(s) to CSV`);
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