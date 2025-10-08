// Campaign Detail View - JavaScript

const API_BASE_URL = 'http://localhost:8000/api';
const TESTS_PER_PAGE = 50;

let campaignId = null;
let currentPage = 0;
let allTests = [];
let currentFilters = {
    status: '',
    search: ''
};

// Get campaign ID from URL
function getCampaignIdFromURL() {
    const params = new URLSearchParams(window.location.search);
    return params.get('id');
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    campaignId = getCampaignIdFromURL();

    if (!campaignId) {
        showError('No campaign ID provided');
        return;
    }

    // Set up event listeners
    document.getElementById('search-input').addEventListener('input', debounce(applyFilters, 500));
    document.getElementById('status-filter').addEventListener('change', applyFilters);

    // Load data
    loadCampaignDetails();
    loadCampaignTests();
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

async function loadCampaignDetails() {
    try {
        showLoading(true);
        const campaign = await apiCall(`/campaigns/${campaignId}`);

        document.getElementById('campaign-name').textContent = campaign.campaign_name;
        document.getElementById('campaign-id').textContent = campaign.campaign_id;

        if (campaign.campaign_date) {
            const date = new Date(campaign.campaign_date);
            document.getElementById('campaign-date').textContent = date.toLocaleString();
        } else {
            document.getElementById('campaign-date').textContent = 'Unknown';
        }

        document.title = `${campaign.campaign_name} - Campaign Details`;
    } catch (error) {
        console.error('Failed to load campaign details:', error);
    } finally {
        showLoading(false);
    }
}

async function loadCampaignTests() {
    try {
        showLoading(true);

        const params = {
            limit: TESTS_PER_PAGE,
            offset: currentPage * TESTS_PER_PAGE
        };

        if (currentFilters.status) {
            params.status = currentFilters.status;
        }

        // Get tests from campaign endpoint
        allTests = await apiCall(`/campaigns/${campaignId}/tests`, params);

        // Load failure messages for failed tests
        await loadFailureMessages(allTests);

        renderTests();
        updateStatistics();
        updatePagination();
    } catch (error) {
        console.error('Failed to load tests:', error);
    } finally {
        showLoading(false);
    }
}

async function loadFailureMessages(tests) {
    const failedTests = tests.filter(t => t.status === 'failed');

    for (const test of failedTests) {
        try {
            const failures = await apiCall(`/tests/${test.test_id}/failures`);
            test.failure_messages = failures;
        } catch (error) {
            console.error(`Failed to load failures for test ${test.test_id}:`, error);
            test.failure_messages = [];
        }
    }
}

// Rendering
function renderTests() {
    const container = document.getElementById('tests-container');
    container.innerHTML = '';

    if (allTests.length === 0) {
        container.innerHTML = '<div style="padding: 40px; text-align: center; color: #6c757d;">No tests found.</div>';
        return;
    }

    // Apply client-side search filter
    let filteredTests = allTests;
    if (currentFilters.search) {
        const searchLower = currentFilters.search.toLowerCase();
        filteredTests = allTests.filter(test =>
            test.test_name.toLowerCase().includes(searchLower) ||
            (test.test_path && test.test_path.toLowerCase().includes(searchLower))
        );
    }

    filteredTests.forEach(test => {
        const testRow = createTestRow(test);
        container.appendChild(testRow);
    });
}

function createTestRow(test) {
    const row = document.createElement('div');
    row.className = `test-row ${test.status || 'unknown'}`;

    // Test info column
    const infoCol = document.createElement('div');
    infoCol.className = 'test-row-info';

    const name = document.createElement('div');
    name.className = 'test-row-name';
    name.textContent = test.test_name;

    const path = document.createElement('div');
    path.className = 'test-row-path';
    path.textContent = test.test_path || '';

    const time = document.createElement('div');
    time.className = 'test-row-time';
    if (test.start_time) {
        const timeObj = new Date(test.start_time);
        time.textContent = `⏱️ ${timeObj.toLocaleString()}`;
    }

    infoCol.appendChild(name);
    infoCol.appendChild(path);
    infoCol.appendChild(time);

    // Status column
    const statusCol = document.createElement('div');
    statusCol.className = 'test-row-status';

    const statusBadge = document.createElement('div');
    statusBadge.className = `test-status status-${test.status || 'unknown'}`;
    statusBadge.textContent = (test.status || 'unknown').toUpperCase();
    statusCol.appendChild(statusBadge);

    // Failures column
    const failuresCol = document.createElement('div');
    failuresCol.className = 'test-row-failures';

    if (test.failure_messages && test.failure_messages.length > 0) {
        const failuresTitle = document.createElement('div');
        failuresTitle.className = 'failures-title';
        failuresTitle.textContent = `${test.failure_messages.length} failure(s)`;
        failuresCol.appendChild(failuresTitle);

        test.failure_messages.forEach(msg => {
            const msgDiv = document.createElement('div');
            msgDiv.className = 'failure-msg-item';
            msgDiv.textContent = msg;
            failuresCol.appendChild(msgDiv);
        });
    } else if (test.status === 'failed') {
        failuresCol.textContent = 'No failure messages recorded';
        failuresCol.style.color = '#6c757d';
        failuresCol.style.fontSize = '0.85em';
    }

    // Actions column
    const actionsCol = document.createElement('div');
    actionsCol.className = 'test-row-actions';

    const detailsBtn = document.createElement('a');
    detailsBtn.className = 'btn-small btn-primary';
    detailsBtn.href = `test.html?id=${test.test_id}`;
    detailsBtn.textContent = 'Details';

    const analyzerBtn = document.createElement('a');
    analyzerBtn.className = 'btn-small btn-secondary';
    analyzerBtn.href = `${API_BASE_URL}/artefacts/${test.test_id}/analyzer`;
    analyzerBtn.target = '_blank';
    analyzerBtn.textContent = 'Analyzer';

    actionsCol.appendChild(detailsBtn);
    actionsCol.appendChild(analyzerBtn);

    // Assemble row
    row.appendChild(infoCol);
    row.appendChild(statusCol);
    row.appendChild(failuresCol);
    row.appendChild(actionsCol);

    return row;
}

function updateStatistics() {
    const total = allTests.length;
    const passed = allTests.filter(t => t.status === 'passed').length;
    const failed = allTests.filter(t => t.status === 'failed').length;
    const passRate = total > 0 ? ((passed / total) * 100).toFixed(1) : 0;

    document.getElementById('total-tests').textContent = total;
    document.getElementById('passed-tests').textContent = passed;
    document.getElementById('failed-tests').textContent = failed;
    document.getElementById('pass-rate').textContent = `${passRate}%`;
}

// Filtering
function applyFilters() {
    const searchInput = document.getElementById('search-input').value;
    const statusFilter = document.getElementById('status-filter').value;

    currentFilters.search = searchInput;
    currentFilters.status = statusFilter;

    // Reset to first page
    currentPage = 0;

    // Reload tests
    loadCampaignTests();
}

function clearFilters() {
    document.getElementById('search-input').value = '';
    document.getElementById('status-filter').value = '';

    currentFilters = {
        status: '',
        search: ''
    };

    currentPage = 0;
    loadCampaignTests();
}

// Pagination
function updatePagination() {
    const pagination = document.getElementById('pagination');
    const prevBtn = document.getElementById('prev-page');
    const nextBtn = document.getElementById('next-page');
    const pageInfo = document.getElementById('page-info');

    if (allTests.length > 0) {
        pagination.style.display = 'block';

        const start = currentPage * TESTS_PER_PAGE + 1;
        const end = Math.min((currentPage + 1) * TESTS_PER_PAGE, start + allTests.length - 1);

        pageInfo.textContent = `Page ${currentPage + 1} (${start}-${end})`;

        prevBtn.disabled = currentPage === 0;
        nextBtn.disabled = allTests.length < TESTS_PER_PAGE;
    } else {
        pagination.style.display = 'none';
    }
}

function nextPage() {
    if (allTests.length >= TESTS_PER_PAGE) {
        currentPage++;
        loadCampaignTests();
        window.scrollTo(0, 0);
    }
}

function prevPage() {
    if (currentPage > 0) {
        currentPage--;
        loadCampaignTests();
        window.scrollTo(0, 0);
    }
}

// Export
async function exportCampaignTests() {
    try {
        showLoading(true);

        const params = new URLSearchParams({
            campaign_id: campaignId,
            format: 'csv'
        });

        if (currentFilters.status) {
            params.append('status', currentFilters.status);
        }

        const url = `${API_BASE_URL}/export/tests?${params.toString()}`;

        const a = document.createElement('a');
        a.href = url;
        a.download = `campaign_${campaignId}_tests.csv`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
    } catch (error) {
        console.error('Export failed:', error);
        showError('Failed to export tests');
    } finally {
        showLoading(false);
    }
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

function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}
