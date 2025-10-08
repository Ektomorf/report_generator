// Test Campaign Browser - Main Application Logic

// Configuration
const API_BASE_URL = 'http://localhost:8000/api';
const TESTS_PER_PAGE = 100;

// State
let currentPage = 0;
let totalTests = 0;
let currentFilters = {
    status: '',
    search: '',
    campaign_id: ''
};
let allCampaigns = [];
let allTests = [];

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    initializeApp();
});

async function initializeApp() {
    console.log('Initializing Test Campaign Browser...');

    // Set up event listeners
    document.getElementById('failure-filter').addEventListener('input', debounce(applyFilters, 500));
    document.getElementById('status-filter').addEventListener('change', applyFilters);
    document.getElementById('campaign-filter').addEventListener('change', applyFilters);

    // Load data
    await loadGlobalSummary();
    await loadCampaigns();
    await loadTests();
}

// ============================================================================
// API Calls
// ============================================================================

async function apiCall(endpoint, params = {}) {
    const queryString = new URLSearchParams(params).toString();
    const url = `${API_BASE_URL}${endpoint}${queryString ? '?' + queryString : ''}`;

    try {
        const response = await fetch(url);
        if (!response.ok) {
            throw new Error(`API error: ${response.status} ${response.statusText}`);
        }
        return await response.json();
    } catch (error) {
        console.error('API call failed:', error);
        showError(`Failed to fetch data: ${error.message}`);
        throw error;
    }
}

async function loadGlobalSummary() {
    try {
        const summary = await apiCall('/stats/summary');
        updateSummaryStats(summary);
    } catch (error) {
        console.error('Failed to load summary:', error);
    }
}

async function loadCampaigns() {
    try {
        showLoading(true);
        allCampaigns = await apiCall('/campaigns', {
            limit: 1000,
            order_by: 'date',
            direction: 'desc'
        });

        // Populate campaign filter dropdown
        const campaignFilter = document.getElementById('campaign-filter');
        campaignFilter.innerHTML = '<option value="">All Campaigns</option>';
        allCampaigns.forEach(campaign => {
            const option = document.createElement('option');
            option.value = campaign.campaign_id;
            option.textContent = campaign.campaign_name;
            campaignFilter.appendChild(option);
        });

        console.log(`Loaded ${allCampaigns.length} campaigns`);
    } catch (error) {
        console.error('Failed to load campaigns:', error);
    } finally {
        showLoading(false);
    }
}

async function loadTests() {
    try {
        showLoading(true);

        const params = {
            limit: TESTS_PER_PAGE,
            offset: currentPage * TESTS_PER_PAGE
        };

        // Apply filters
        if (currentFilters.status) {
            params.status = currentFilters.status;
        }
        if (currentFilters.search) {
            params.search = currentFilters.search;
        }
        if (currentFilters.campaign_id) {
            params.campaign_id = currentFilters.campaign_id;
        }

        allTests = await apiCall('/tests', params);

        // Load failure messages for failed tests
        await loadFailureMessages(allTests);

        renderTests();
        updateFilterInfo();

        console.log(`Loaded ${allTests.length} tests`);
    } catch (error) {
        console.error('Failed to load tests:', error);
    } finally {
        showLoading(false);
    }
}

async function loadFailureMessages(tests) {
    // Load failure messages for failed tests
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

// ============================================================================
// Rendering
// ============================================================================

function renderTests() {
    const container = document.getElementById('campaigns-container');
    container.innerHTML = '';

    if (allTests.length === 0) {
        container.innerHTML = '<div style="padding: 40px; text-align: center; color: #6c757d;">No tests found matching your filters.</div>';
        return;
    }

    // Group tests by campaign
    const testsByCampaign = {};
    allTests.forEach(test => {
        if (!testsByCampaign[test.campaign_id]) {
            testsByCampaign[test.campaign_id] = {
                campaign: allCampaigns.find(c => c.campaign_id === test.campaign_id) || {
                    campaign_name: test.campaign_name,
                    campaign_id: test.campaign_id
                },
                tests: []
            };
        }
        testsByCampaign[test.campaign_id].tests.push(test);
    });

    // Render each campaign section
    Object.values(testsByCampaign).forEach(({ campaign, tests }) => {
        const campaignSection = createCampaignSection(campaign, tests);
        container.appendChild(campaignSection);
    });

    // Update pagination
    updatePagination();
}

function createCampaignSection(campaign, tests) {
    const section = document.createElement('div');
    section.className = 'campaign-section';

    // Campaign header
    const header = document.createElement('div');
    header.className = 'campaign-header';

    const title = document.createElement('div');
    title.className = 'campaign-title';

    // Make campaign title a clickable link
    const titleLink = document.createElement('a');
    titleLink.href = `campaign.html?id=${campaign.campaign_id}`;
    titleLink.textContent = campaign.campaign_name;
    titleLink.style.color = 'inherit';
    titleLink.style.textDecoration = 'none';
    titleLink.addEventListener('mouseenter', () => {
        titleLink.style.textDecoration = 'underline';
    });
    titleLink.addEventListener('mouseleave', () => {
        titleLink.style.textDecoration = 'none';
    });
    title.appendChild(titleLink);

    const date = document.createElement('div');
    date.className = 'campaign-date';
    if (campaign.campaign_date) {
        const dateObj = new Date(campaign.campaign_date);
        date.textContent = `Date: ${dateObj.toLocaleString()} • ${tests.length} test(s) shown`;
    } else {
        date.textContent = `${tests.length} test(s) shown`;
    }

    header.appendChild(title);
    header.appendChild(date);

    // Campaign stats (if available)
    if (campaign.total_tests !== undefined) {
        const stats = document.createElement('div');
        stats.className = 'campaign-stats';
        stats.textContent = `Total: ${campaign.total_tests} | Passed: ${campaign.passed_tests} | Failed: ${campaign.failed_tests}`;
        header.appendChild(stats);
    }

    // Tests grid
    const grid = document.createElement('div');
    grid.className = 'tests-grid';

    tests.forEach(test => {
        const card = createTestCard(test);
        grid.appendChild(card);
    });

    section.appendChild(header);
    section.appendChild(grid);

    return section;
}

function createTestCard(test) {
    const card = document.createElement('div');
    card.className = `test-card ${test.status || 'unknown'}`;
    card.dataset.testId = test.test_id;
    card.dataset.testStatus = test.status;

    // Test name
    const name = document.createElement('div');
    name.className = 'test-name';
    name.textContent = test.test_name;

    // Test path
    const path = document.createElement('div');
    path.className = 'test-path';
    path.textContent = test.test_path || '';

    // Start time
    const time = document.createElement('div');
    time.className = 'test-time';
    if (test.start_time) {
        const timeObj = new Date(test.start_time);
        time.textContent = `⏱️ Started: ${timeObj.toLocaleTimeString()}`;
    } else {
        time.textContent = '⏱️ Start time unknown';
    }

    // Status badge
    const status = document.createElement('div');
    status.className = `test-status status-${test.status || 'unknown'}`;
    status.textContent = (test.status || 'unknown').toUpperCase();

    // Failure messages
    let failuresDiv = null;
    if (test.failure_messages && test.failure_messages.length > 0) {
        failuresDiv = document.createElement('div');
        failuresDiv.className = 'test-failures';

        const failuresTitle = document.createElement('div');
        failuresTitle.className = 'test-failures-title';
        failuresTitle.textContent = 'Failure Messages:';
        failuresDiv.appendChild(failuresTitle);

        test.failure_messages.forEach(msg => {
            const msgDiv = document.createElement('div');
            msgDiv.className = 'test-failure-msg';
            msgDiv.textContent = msg;
            failuresDiv.appendChild(msgDiv);
        });

        // Store for filtering
        card.dataset.failureMessages = test.failure_messages.join(' ');
    }

    // Link to analyzer
    const link = document.createElement('a');
    link.className = 'test-link';
    link.href = `${API_BASE_URL}/artefacts/${test.test_id}/analyzer`;
    link.target = '_blank';
    link.textContent = 'View Analysis →';

    // Assemble card
    card.appendChild(name);
    card.appendChild(path);
    card.appendChild(time);
    card.appendChild(status);
    if (failuresDiv) {
        card.appendChild(failuresDiv);
    }
    card.appendChild(link);

    return card;
}

function updateSummaryStats(summary) {
    document.getElementById('total-tests').textContent = summary.total_tests || 0;
    document.getElementById('passed-tests').textContent = summary.passed_tests || 0;
    document.getElementById('failed-tests').textContent = summary.failed_tests || 0;
    document.getElementById('total-campaigns').textContent = summary.total_campaigns || 0;
    document.getElementById('pass-rate').textContent = `${summary.pass_rate || 0}%`;
}

// ============================================================================
// Filtering
// ============================================================================

function applyFilters() {
    const searchInput = document.getElementById('failure-filter').value;
    const statusFilter = document.getElementById('status-filter').value;
    const campaignFilter = document.getElementById('campaign-filter').value;

    // Update filter state
    currentFilters.search = searchInput;
    currentFilters.status = statusFilter;
    currentFilters.campaign_id = campaignFilter;

    // Reset to first page
    currentPage = 0;

    // Reload tests with filters
    loadTests();
}

function clearFilters() {
    document.getElementById('failure-filter').value = '';
    document.getElementById('status-filter').value = '';
    document.getElementById('campaign-filter').value = '';

    currentFilters = {
        status: '',
        search: '',
        campaign_id: ''
    };

    currentPage = 0;
    loadTests();
}

function updateFilterInfo() {
    const info = document.getElementById('filter-info');
    const hasFilters = currentFilters.status || currentFilters.search || currentFilters.campaign_id;

    if (hasFilters) {
        const parts = [];
        if (currentFilters.status) parts.push(`status: ${currentFilters.status}`);
        if (currentFilters.search) parts.push(`search: "${currentFilters.search}"`);
        if (currentFilters.campaign_id) {
            const campaign = allCampaigns.find(c => c.campaign_id == currentFilters.campaign_id);
            if (campaign) parts.push(`campaign: ${campaign.campaign_name}`);
        }
        info.textContent = `Showing ${allTests.length} test(s) (${parts.join(', ')})`;
    } else {
        info.textContent = `Showing ${allTests.length} test(s)`;
    }
}

// ============================================================================
// Pagination
// ============================================================================

function updatePagination() {
    const pagination = document.getElementById('pagination');
    const prevBtn = document.getElementById('prev-page');
    const nextBtn = document.getElementById('next-page');
    const pageInfo = document.getElementById('page-info');

    // Show pagination if we have tests
    if (allTests.length > 0) {
        pagination.style.display = 'block';

        const start = currentPage * TESTS_PER_PAGE + 1;
        const end = Math.min((currentPage + 1) * TESTS_PER_PAGE, start + allTests.length - 1);

        pageInfo.textContent = `Showing ${start}-${end} (Page ${currentPage + 1})`;

        prevBtn.disabled = currentPage === 0;
        nextBtn.disabled = allTests.length < TESTS_PER_PAGE;
    } else {
        pagination.style.display = 'none';
    }
}

function nextPage() {
    if (allTests.length >= TESTS_PER_PAGE) {
        currentPage++;
        loadTests();
    }
}

function prevPage() {
    if (currentPage > 0) {
        currentPage--;
        loadTests();
    }
}

// ============================================================================
// Export
// ============================================================================

async function exportFailures() {
    try {
        showLoading(true);

        const params = new URLSearchParams({
            format: 'csv'
        });

        if (currentFilters.campaign_id) {
            params.append('campaign_id', currentFilters.campaign_id);
        }

        const url = `${API_BASE_URL}/export/failures?${params.toString()}`;

        // Trigger download
        const a = document.createElement('a');
        a.href = url;
        a.download = `failures_${new Date().toISOString().slice(0, 10)}.csv`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);

        console.log('Export initiated');
    } catch (error) {
        console.error('Export failed:', error);
        showError('Failed to export failures');
    } finally {
        showLoading(false);
    }
}

// ============================================================================
// UI Helpers
// ============================================================================

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

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
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
