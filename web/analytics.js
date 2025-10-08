// Analytics Dashboard - JavaScript

const API_BASE_URL = 'http://localhost:8000/api';

let campaignTrendChart = null;
let passFailChart = null;
let campaignComparisonChart = null;

// Initialize
document.addEventListener('DOMContentLoaded', async () => {
    await loadAllAnalytics();
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

async function loadAllAnalytics() {
    try {
        showLoading(true);

        // Load all data in parallel
        const [summary, campaigns, commonFailures, recentTests] = await Promise.all([
            apiCall('/stats/summary'),
            apiCall('/campaigns', { limit: 1000, order_by: 'date', direction: 'desc' }),
            apiCall('/failures/common', { limit: 10 }),
            apiCall('/tests', { limit: 20 })
        ]);

        // Update UI
        updateGlobalStats(summary);
        renderCampaignTrend(campaigns);
        renderPassFailChart(summary);
        renderCommonFailures(commonFailures);
        renderCampaignComparison(campaigns.slice(0, 10));
        renderRecentTests(recentTests);

    } catch (error) {
        console.error('Failed to load analytics:', error);
    } finally {
        showLoading(false);
    }
}

function updateGlobalStats(summary) {
    document.getElementById('total-tests').textContent = summary.total_tests || 0;
    document.getElementById('passed-tests').textContent = summary.passed_tests || 0;
    document.getElementById('failed-tests').textContent = summary.failed_tests || 0;
    document.getElementById('pass-rate').textContent = `${summary.pass_rate || 0}%`;
    document.getElementById('total-campaigns').textContent = summary.total_campaigns || 0;
}

function renderCampaignTrend(campaigns) {
    const ctx = document.getElementById('campaign-trend-chart');

    // Prepare data
    const labels = campaigns.slice(0, 20).reverse().map(c => c.campaign_name);
    const passedData = campaigns.slice(0, 20).reverse().map(c => c.passed_tests);
    const failedData = campaigns.slice(0, 20).reverse().map(c => c.failed_tests);

    // Destroy existing chart
    if (campaignTrendChart) {
        campaignTrendChart.destroy();
    }

    // Create chart
    campaignTrendChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Passed Tests',
                    data: passedData,
                    borderColor: '#28a745',
                    backgroundColor: 'rgba(40, 167, 69, 0.1)',
                    borderWidth: 2,
                    tension: 0.4
                },
                {
                    label: 'Failed Tests',
                    data: failedData,
                    borderColor: '#dc3545',
                    backgroundColor: 'rgba(220, 53, 69, 0.1)',
                    borderWidth: 2,
                    tension: 0.4
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                title: {
                    display: true,
                    text: 'Test Results Trend (Last 20 Campaigns)'
                },
                legend: {
                    position: 'top'
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Number of Tests'
                    }
                },
                x: {
                    ticks: {
                        maxRotation: 45,
                        minRotation: 45
                    }
                }
            }
        }
    });
}

function renderPassFailChart(summary) {
    const ctx = document.getElementById('pass-fail-chart');

    // Destroy existing chart
    if (passFailChart) {
        passFailChart.destroy();
    }

    // Create pie chart
    passFailChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Passed', 'Failed', 'Unknown'],
            datasets: [{
                data: [
                    summary.passed_tests || 0,
                    summary.failed_tests || 0,
                    summary.unknown_tests || 0
                ],
                backgroundColor: [
                    '#28a745',
                    '#dc3545',
                    '#ffc107'
                ],
                borderWidth: 2,
                borderColor: '#fff'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                title: {
                    display: true,
                    text: 'Overall Test Status Distribution'
                },
                legend: {
                    position: 'bottom'
                }
            }
        }
    });
}

function renderCommonFailures(failures) {
    const container = document.getElementById('common-failures-container');
    container.innerHTML = '';

    if (failures.length === 0) {
        container.innerHTML = '<p style="text-align: center; color: #6c757d;">No failure data available.</p>';
        return;
    }

    const table = document.createElement('table');
    table.className = 'analytics-table';

    // Header
    const thead = table.createTHead();
    const headerRow = thead.insertRow();
    ['Rank', 'Failure Message', 'Occurrences', 'Affected Tests'].forEach(header => {
        const th = document.createElement('th');
        th.textContent = header;
        headerRow.appendChild(th);
    });

    // Body
    const tbody = table.createTBody();
    failures.forEach((failure, index) => {
        const row = tbody.insertRow();

        // Rank
        const rankCell = row.insertCell(0);
        rankCell.textContent = `#${index + 1}`;
        rankCell.style.fontWeight = 'bold';
        rankCell.style.color = index < 3 ? '#dc3545' : '#6c757d';

        // Message
        const msgCell = row.insertCell(1);
        msgCell.textContent = failure.message;
        msgCell.style.fontFamily = 'monospace';
        msgCell.style.fontSize = '0.9em';

        // Count
        const countCell = row.insertCell(2);
        countCell.textContent = failure.count;
        countCell.style.fontWeight = 'bold';
        countCell.style.textAlign = 'center';

        // Test names
        const testsCell = row.insertCell(3);
        const testNames = failure.test_names.slice(0, 3).join(', ');
        const more = failure.test_names.length > 3 ? ` +${failure.test_names.length - 3} more` : '';
        testsCell.textContent = testNames + more;
        testsCell.style.fontSize = '0.85em';
        testsCell.style.color = '#6c757d';
    });

    container.appendChild(table);
}

function renderCampaignComparison(campaigns) {
    const ctx = document.getElementById('campaign-comparison-chart');

    // Prepare data
    const labels = campaigns.map(c => c.campaign_name);
    const totalData = campaigns.map(c => c.total_tests);
    const passedData = campaigns.map(c => c.passed_tests);
    const failedData = campaigns.map(c => c.failed_tests);

    // Destroy existing chart
    if (campaignComparisonChart) {
        campaignComparisonChart.destroy();
    }

    // Create stacked bar chart
    campaignComparisonChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Passed',
                    data: passedData,
                    backgroundColor: '#28a745',
                    borderWidth: 0
                },
                {
                    label: 'Failed',
                    data: failedData,
                    backgroundColor: '#dc3545',
                    borderWidth: 0
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                title: {
                    display: true,
                    text: 'Campaign Comparison (Latest 10)'
                },
                legend: {
                    position: 'top'
                }
            },
            scales: {
                x: {
                    stacked: true,
                    ticks: {
                        maxRotation: 45,
                        minRotation: 45
                    }
                },
                y: {
                    stacked: true,
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Number of Tests'
                    }
                }
            }
        }
    });
}

function renderRecentTests(tests) {
    const container = document.getElementById('recent-tests-container');
    container.innerHTML = '';

    if (tests.length === 0) {
        container.innerHTML = '<p style="text-align: center; color: #6c757d;">No recent tests found.</p>';
        return;
    }

    const table = document.createElement('table');
    table.className = 'analytics-table';

    // Header
    const thead = table.createTHead();
    const headerRow = thead.insertRow();
    ['Test Name', 'Campaign', 'Status', 'Time', 'Action'].forEach(header => {
        const th = document.createElement('th');
        th.textContent = header;
        headerRow.appendChild(th);
    });

    // Body
    const tbody = table.createTBody();
    tests.forEach(test => {
        const row = tbody.insertRow();

        // Test name
        const nameCell = row.insertCell(0);
        nameCell.textContent = test.test_name;
        nameCell.style.fontWeight = 'bold';

        // Campaign
        row.insertCell(1).textContent = test.campaign_name;

        // Status
        const statusCell = row.insertCell(2);
        const statusBadge = document.createElement('span');
        statusBadge.className = `test-status status-${test.status || 'unknown'}`;
        statusBadge.textContent = (test.status || 'unknown').toUpperCase();
        statusCell.appendChild(statusBadge);

        // Time
        const timeCell = row.insertCell(3);
        if (test.start_time) {
            const date = new Date(test.start_time);
            timeCell.textContent = date.toLocaleString();
        } else {
            timeCell.textContent = '-';
        }
        timeCell.style.fontSize = '0.85em';

        // Action
        const actionCell = row.insertCell(4);
        const detailsLink = document.createElement('a');
        detailsLink.href = `test.html?id=${test.test_id}`;
        detailsLink.className = 'btn-small btn-primary';
        detailsLink.textContent = 'Details';
        actionCell.appendChild(detailsLink);
    });

    container.appendChild(table);
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
