// Advanced Search - JavaScript

const API_BASE_URL = 'http://localhost:8000/api';
const RESULTS_PER_PAGE = 50;

let currentPage = 0;
let searchResults = [];
let searchParams = {};

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    loadCampaigns();
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

async function loadCampaigns() {
    try {
        const campaigns = await apiCall('/campaigns', { limit: 1000 });

        const select = document.getElementById('campaign-search');
        campaigns.forEach(campaign => {
            const option = document.createElement('option');
            option.value = campaign.campaign_id;
            option.textContent = campaign.campaign_name;
            select.appendChild(option);
        });
    } catch (error) {
        console.error('Failed to load campaigns:', error);
    }
}

async function performSearch() {
    try {
        showLoading(true);
        currentPage = 0;

        // Build search parameters
        searchParams = {
            limit: RESULTS_PER_PAGE,
            offset: 0
        };

        const testName = document.getElementById('test-name-search').value.trim();
        const status = document.getElementById('status-search').value;
        const campaignId = document.getElementById('campaign-search').value;
        const startDate = document.getElementById('start-date-search').value;
        const endDate = document.getElementById('end-date-search').value;
        const keyword = document.getElementById('keyword-search').value.trim();

        if (status) searchParams.status = status;
        if (campaignId) searchParams.campaign_id = campaignId;
        if (startDate) searchParams.start_date = startDate;
        if (endDate) searchParams.end_date = endDate;
        if (keyword) searchParams.search = keyword;

        // Perform search
        searchResults = await apiCall('/tests', searchParams);

        // Filter by test name on client side if needed
        if (testName) {
            const testNameLower = testName.toLowerCase();
            searchResults = searchResults.filter(test =>
                test.test_name.toLowerCase().includes(testNameLower)
            );
        }

        renderResults();
        updateResultsInfo();
        updatePagination();

        document.getElementById('results-section').style.display = 'block';
        document.getElementById('results-info').style.display = 'block';

        // Scroll to results
        document.getElementById('results-section').scrollIntoView({ behavior: 'smooth' });
    } catch (error) {
        console.error('Search failed:', error);
    } finally {
        showLoading(false);
    }
}

function renderResults() {
    const container = document.getElementById('results-container');
    container.innerHTML = '';

    if (searchResults.length === 0) {
        container.innerHTML = '<div class="no-results">No tests found matching your search criteria.</div>';
        return;
    }

    const table = document.createElement('table');
    table.className = 'search-results-table';

    // Header
    const thead = table.createTHead();
    const headerRow = thead.insertRow();
    ['Test Name', 'Campaign', 'Status', 'Start Time', 'Actions'].forEach(header => {
        const th = document.createElement('th');
        th.textContent = header;
        headerRow.appendChild(th);
    });

    // Body
    const tbody = table.createTBody();
    searchResults.forEach(test => {
        const row = tbody.insertRow();

        // Test name
        const nameCell = row.insertCell(0);
        nameCell.textContent = test.test_name;
        nameCell.style.fontWeight = 'bold';

        // Campaign
        row.insertCell(1).textContent = test.campaign_name || 'Unknown';

        // Status
        const statusCell = row.insertCell(2);
        const statusSpan = document.createElement('span');
        statusSpan.className = `test-status status-${test.status || 'unknown'}`;
        statusSpan.textContent = (test.status || 'unknown').toUpperCase();
        statusCell.appendChild(statusSpan);

        // Start time
        const timeCell = row.insertCell(3);
        if (test.start_time) {
            const date = new Date(test.start_time);
            timeCell.textContent = date.toLocaleString();
        } else {
            timeCell.textContent = '-';
        }

        // Actions
        const actionsCell = row.insertCell(4);
        const detailsBtn = document.createElement('a');
        detailsBtn.className = 'btn-small btn-primary';
        detailsBtn.href = `test.html?id=${test.test_id}`;
        detailsBtn.textContent = 'Details';

        const analyzerBtn = document.createElement('a');
        analyzerBtn.className = 'btn-small btn-secondary';
        analyzerBtn.href = `${API_BASE_URL}/artefacts/${test.test_id}/analyzer`;
        analyzerBtn.target = '_blank';
        analyzerBtn.textContent = 'Analyzer';
        analyzerBtn.style.marginLeft = '5px';

        actionsCell.appendChild(detailsBtn);
        actionsCell.appendChild(analyzerBtn);
    });

    container.appendChild(table);
}

function updateResultsInfo() {
    document.getElementById('results-count').textContent = searchResults.length;
}

function clearSearch() {
    document.getElementById('test-name-search').value = '';
    document.getElementById('status-search').value = '';
    document.getElementById('campaign-search').value = '';
    document.getElementById('start-date-search').value = '';
    document.getElementById('end-date-search').value = '';
    document.getElementById('keyword-search').value = '';

    document.getElementById('results-section').style.display = 'none';
    document.getElementById('results-info').style.display = 'none';
    searchResults = [];
    searchParams = {};
}

async function exportResults() {
    if (searchResults.length === 0) {
        showError('No results to export. Perform a search first.');
        return;
    }

    try {
        showLoading(true);

        const params = new URLSearchParams({
            format: 'csv',
            ...searchParams
        });

        const url = `${API_BASE_URL}/export/tests?${params.toString()}`;

        const a = document.createElement('a');
        a.href = url;
        a.download = `search_results_${new Date().toISOString().slice(0, 10)}.csv`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
    } catch (error) {
        console.error('Export failed:', error);
        showError('Failed to export results');
    } finally {
        showLoading(false);
    }
}

// Pagination
function updatePagination() {
    const pagination = document.getElementById('pagination');
    const prevBtn = document.getElementById('prev-page');
    const nextBtn = document.getElementById('next-page');
    const pageInfo = document.getElementById('page-info');

    if (searchResults.length > 0) {
        pagination.style.display = 'block';

        pageInfo.textContent = `Page ${currentPage + 1}`;

        prevBtn.disabled = currentPage === 0;
        nextBtn.disabled = searchResults.length < RESULTS_PER_PAGE;
    } else {
        pagination.style.display = 'none';
    }
}

async function nextPage() {
    if (searchResults.length >= RESULTS_PER_PAGE) {
        currentPage++;
        searchParams.offset = currentPage * RESULTS_PER_PAGE;

        try {
            showLoading(true);
            searchResults = await apiCall('/tests', searchParams);
            renderResults();
            updatePagination();
            window.scrollTo(0, 0);
        } catch (error) {
            console.error('Failed to load next page:', error);
        } finally {
            showLoading(false);
        }
    }
}

async function prevPage() {
    if (currentPage > 0) {
        currentPage--;
        searchParams.offset = currentPage * RESULTS_PER_PAGE;

        try {
            showLoading(true);
            searchResults = await apiCall('/tests', searchParams);
            renderResults();
            updatePagination();
            window.scrollTo(0, 0);
        } catch (error) {
            console.error('Failed to load previous page:', error);
        } finally {
            showLoading(false);
        }
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
