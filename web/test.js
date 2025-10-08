// Test Detail View - JavaScript

const API_BASE_URL = 'http://localhost:8000/api';

let testId = null;
let testData = null;
let allLogs = [];

// Get test ID from URL
function getTestIdFromURL() {
    const params = new URLSearchParams(window.location.search);
    return params.get('id');
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    testId = getTestIdFromURL();

    if (!testId) {
        showError('No test ID provided');
        return;
    }

    loadTestDetails();
});

// API Calls
async function apiCall(endpoint, params = {}) {
    const queryString = new URLSearchParams(params).toString();
    const url = `${API_BASE_URL}${endpoint}${queryString ? '?' + queryString : ''}`;

    try {
        const response = await fetch(url);
        if (!response.ok) {
            throw new Error(`API error: ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error('API call failed:', error);
        showError(`Failed to fetch data: ${error.message}`);
        throw error;
    }
}

async function loadTestDetails() {
    try {
        showLoading(true);
        testData = await apiCall(`/tests/${testId}`);

        renderTestInfo();
        updateBreadcrumb();
    } catch (error) {
        console.error('Failed to load test details:', error);
    } finally {
        showLoading(false);
    }
}

function renderTestInfo() {
    // Test name and status
    document.getElementById('test-name').textContent = testData.test_name;
    document.title = `${testData.test_name} - Test Details`;

    const statusBadge = document.getElementById('test-status-badge');
    statusBadge.textContent = (testData.status || 'unknown').toUpperCase();
    statusBadge.className = `test-status status-${testData.status || 'unknown'}`;

    // Metadata
    document.getElementById('test-id').textContent = testData.test_id;
    document.getElementById('campaign-name').textContent = testData.campaign_name || 'Unknown';
    document.getElementById('test-path').textContent = testData.test_path || 'N/A';

    if (testData.start_time) {
        const date = new Date(testData.start_time);
        document.getElementById('start-time').textContent = date.toLocaleString();
    } else {
        document.getElementById('start-time').textContent = 'Unknown';
    }

    // Docstring
    if (testData.docstring) {
        document.getElementById('docstring-section').style.display = 'block';
        document.getElementById('docstring-text').textContent = testData.docstring;
    }

    // Parameters
    if (testData.params && Object.keys(testData.params).length > 0) {
        document.getElementById('params-section').style.display = 'block';
        renderParameters(testData.params);
    }

    // Failure messages
    if (testData.failure_messages && testData.failure_messages.length > 0) {
        document.getElementById('failures-section').style.display = 'block';
        renderFailures(testData.failure_messages);
    }
}

function renderParameters(params) {
    const table = document.getElementById('params-table');
    table.innerHTML = '';

    Object.entries(params).forEach(([key, value]) => {
        const row = table.insertRow();
        const keyCell = row.insertCell(0);
        const valueCell = row.insertCell(1);

        keyCell.textContent = key;
        keyCell.style.fontWeight = 'bold';
        valueCell.textContent = value;
    });
}

function renderFailures(failures) {
    const container = document.getElementById('failures-list');
    container.innerHTML = '';

    failures.forEach((msg, index) => {
        const msgDiv = document.createElement('div');
        msgDiv.className = 'failure-item';
        msgDiv.textContent = `${index + 1}. ${msg}`;
        container.appendChild(msgDiv);
    });
}

function updateBreadcrumb() {
    const campaignLink = document.getElementById('campaign-link');
    if (testData && testData.campaign_id) {
        campaignLink.href = `campaign.html?id=${testData.campaign_id}`;
        campaignLink.textContent = testData.campaign_name || 'Campaign';
    }
}

// Action Buttons
function openAnalyzer() {
    if (!testData || !testData.analyzer_html_path) {
        showError('Analyzer HTML not available for this test');
        return;
    }

    const url = `${API_BASE_URL}/artefacts/${testId}/analyzer`;
    window.open(url, '_blank');
}

function downloadCSV() {
    const url = `${API_BASE_URL}/artefacts/${testId}/csv`;

    const a = document.createElement('a');
    a.href = url;
    a.download = `test_${testId}_data.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
}

async function viewResults() {
    const section = document.getElementById('results-section');

    if (section.style.display === 'block') {
        section.style.display = 'none';
        return;
    }

    try {
        showLoading(true);
        const results = await apiCall(`/tests/${testId}/results`, { limit: 1000 });

        renderResults(results);
        section.style.display = 'block';

        // Scroll to section
        section.scrollIntoView({ behavior: 'smooth' });
    } catch (error) {
        console.error('Failed to load results:', error);
    } finally {
        showLoading(false);
    }
}

function renderResults(results) {
    const container = document.getElementById('results-container');
    container.innerHTML = '';

    if (results.length === 0) {
        container.innerHTML = '<p>No results found.</p>';
        return;
    }

    const table = document.createElement('table');
    table.className = 'data-table';

    // Header
    const thead = table.createTHead();
    const headerRow = thead.insertRow();
    ['Row', 'Pass', 'Command Method', 'Command', 'Response', 'Failures'].forEach(header => {
        const th = document.createElement('th');
        th.textContent = header;
        headerRow.appendChild(th);
    });

    // Body
    const tbody = table.createTBody();
    results.forEach(result => {
        const row = tbody.insertRow();
        row.className = result.pass ? 'result-pass' : 'result-fail';

        row.insertCell(0).textContent = result.row_index ?? '-';

        const passCell = row.insertCell(1);
        if (result.pass !== null && result.pass !== undefined) {
            passCell.textContent = result.pass ? '✓ PASS' : '✗ FAIL';
            passCell.style.fontWeight = 'bold';
            passCell.style.color = result.pass ? '#28a745' : '#dc3545';
        } else {
            passCell.textContent = '-';
        }

        row.insertCell(2).textContent = result.command_method || '-';
        row.insertCell(3).textContent = truncate(result.command_str, 50);
        row.insertCell(4).textContent = truncate(result.raw_response, 50);
        row.insertCell(5).textContent = result.failure_messages || '-';
    });

    container.appendChild(table);
}

function hideResults() {
    document.getElementById('results-section').style.display = 'none';
}

async function viewLogs() {
    const section = document.getElementById('logs-section');

    if (section.style.display === 'block') {
        section.style.display = 'none';
        return;
    }

    try {
        showLoading(true);
        allLogs = await apiCall(`/tests/${testId}/logs`, { limit: 5000 });

        renderLogs(allLogs);
        section.style.display = 'block';

        // Scroll to section
        section.scrollIntoView({ behavior: 'smooth' });
    } catch (error) {
        console.error('Failed to load logs:', error);
    } finally {
        showLoading(false);
    }
}

function renderLogs(logs) {
    const container = document.getElementById('logs-container');
    container.innerHTML = '';

    if (logs.length === 0) {
        container.innerHTML = '<p>No logs found.</p>';
        return;
    }

    const table = document.createElement('table');
    table.className = 'data-table';

    // Header
    const thead = table.createTHead();
    const headerRow = thead.insertRow();
    ['Row', 'Level', 'Message'].forEach(header => {
        const th = document.createElement('th');
        th.textContent = header;
        headerRow.appendChild(th);
    });

    // Body
    const tbody = table.createTBody();
    logs.forEach(log => {
        const row = tbody.insertRow();

        // Add level-based styling
        if (log.level) {
            const levelLower = log.level.toLowerCase();
            if (levelLower === 'error' || levelLower === 'critical') {
                row.className = 'log-error';
            } else if (levelLower === 'warning') {
                row.className = 'log-warning';
            }
        }

        row.insertCell(0).textContent = log.row_index ?? '-';

        const levelCell = row.insertCell(1);
        levelCell.textContent = log.level || '-';
        levelCell.style.fontWeight = 'bold';

        const msgCell = row.insertCell(2);
        msgCell.textContent = log.message || '-';
        msgCell.style.fontFamily = 'monospace';
        msgCell.style.fontSize = '0.9em';
    });

    container.appendChild(table);
}

function hideLogs() {
    document.getElementById('logs-section').style.display = 'none';
}

function filterLogs() {
    const level = document.getElementById('log-level-filter').value;

    let filteredLogs = allLogs;
    if (level) {
        filteredLogs = allLogs.filter(log => log.level && log.level.toUpperCase() === level);
    }

    renderLogs(filteredLogs);
}

// UI Helpers
function showLoading(show) {
    document.getElementById('loading').style.display = show ? 'block' : 'none';
}

function showError(message) {
    const errorDiv = document.getElementById('error-message');
    errorDiv.textContent = message;
    errorDiv.style.display = 'block';

    setTimeout(() => {
        errorDiv.style.display = 'none';
    }, 5000);
}

function truncate(str, maxLen) {
    if (!str) return '-';
    if (str.length <= maxLen) return str;
    return str.substring(0, maxLen) + '...';
}
