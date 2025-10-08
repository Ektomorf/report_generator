# Test Results REST API Server

FastAPI-based REST API for querying test results, campaigns, and analytics from the SQL database.

## Features

✅ **Campaign Management** - List and search campaigns
✅ **Test Queries** - Advanced search and filtering
✅ **Statistics** - Global summaries and analytics
✅ **Failure Analysis** - Common failures and trends
✅ **Export** - CSV/JSON export capabilities
✅ **Artefact Access** - Serve analyzer HTML and CSV files
✅ **Auto-documentation** - Swagger UI and ReDoc
✅ **CORS enabled** - Cross-origin requests supported

## Installation

### Install Dependencies

```bash
pip install -r requirements.txt
```

Requirements:
- fastapi >= 0.104.1
- uvicorn >= 0.24.0
- sqlalchemy >= 2.0.23
- pydantic >= 2.5.0

### Database Setup

Ensure you have imported data into the database:

```bash
# Import test results first
python sql_importer.py output

# Verify database
python sql_importer.py output --summary
```

## Running the Server

### Development Mode (with auto-reload)

```bash
python api_server.py
```

### Production Mode

```bash
uvicorn api_server:app --host 0.0.0.0 --port 8000 --workers 4
```

### Custom Database Path

```bash
DB_PATH=/path/to/custom.db python api_server.py
```

## API Documentation

Once the server is running, visit:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

## API Endpoints

### Campaign Endpoints

#### GET /api/campaigns
List all campaigns with summary statistics.

**Query Parameters:**
- `limit` (int, default=100): Maximum results
- `offset` (int, default=0): Pagination offset
- `order_by` (str): Sort by "date" or "name"
- `direction` (str): "asc" or "desc"

**Example:**
```bash
curl "http://localhost:8000/api/campaigns?limit=10&order_by=date&direction=desc"
```

**Response:**
```json
[
  {
    "campaign_id": 1,
    "campaign_name": "socan_061025_103235",
    "campaign_date": "2025-10-06T10:32:35",
    "total_tests": 15,
    "passed_tests": 12,
    "failed_tests": 3,
    "unknown_tests": 0
  }
]
```

#### GET /api/campaigns/{campaign_id}
Get campaign details.

**Example:**
```bash
curl "http://localhost:8000/api/campaigns/1"
```

#### GET /api/campaigns/{campaign_id}/tests
List all tests in a campaign.

**Query Parameters:**
- `status` (str, optional): Filter by "passed", "failed", or "unknown"
- `limit` (int)
- `offset` (int)

**Example:**
```bash
curl "http://localhost:8000/api/campaigns/1/tests?status=failed"
```

### Test Endpoints

#### GET /api/tests
Search and filter tests across all campaigns.

**Query Parameters:**
- `status` (str): Filter by status
- `campaign_id` (int): Filter by campaign
- `start_date` (str): ISO format date (e.g., "2025-10-01")
- `end_date` (str): ISO format date
- `search` (str): Search in test names and failure messages
- `limit` (int)
- `offset` (int)

**Example:**
```bash
# Get all failed tests
curl "http://localhost:8000/api/tests?status=failed&limit=20"

# Search for tests with "timeout" in name or failures
curl "http://localhost:8000/api/tests?search=timeout"

# Get tests from date range
curl "http://localhost:8000/api/tests?start_date=2025-10-01&end_date=2025-10-31"
```

**Response:**
```json
[
  {
    "test_id": 42,
    "test_name": "test_rtn_defaults",
    "test_path": "test_v1_1_rtn__test_rtn_defaults",
    "status": "failed",
    "start_time": "2025-10-06T12:30:45",
    "campaign_id": 1,
    "campaign_name": "socan_061025_103235",
    "failure_count": 2
  }
]
```

#### GET /api/tests/{test_id}
Get complete test details including params and failure messages.

**Example:**
```bash
curl "http://localhost:8000/api/tests/42"
```

**Response:**
```json
{
  "test_id": 42,
  "test_name": "test_rtn_defaults",
  "test_path": "test_v1_1_rtn__test_rtn_defaults",
  "status": "failed",
  "start_time": "2025-10-06T12:30:45",
  "start_timestamp": 1728217845000,
  "docstring": "Test RTN with default parameters",
  "analyzer_html_path": "output/socan_061025_103235/test_v1_1_rtn__test_rtn_defaults/test_rtn_defaults_combined_analyzer.html",
  "campaign_id": 1,
  "campaign_name": "socan_061025_103235",
  "params": {
    "frequency": "2400",
    "threshold": "10"
  },
  "failure_messages": [
    "Peak amplitude below threshold",
    "Timeout waiting for response"
  ]
}
```

#### GET /api/tests/{test_id}/results
Get test result rows from the CSV.

**Query Parameters:**
- `limit` (int, default=1000)
- `offset` (int)

**Example:**
```bash
curl "http://localhost:8000/api/tests/42/results"
```

#### GET /api/tests/{test_id}/logs
Get test log entries.

**Query Parameters:**
- `level` (str, optional): Filter by log level (DEBUG, INFO, WARNING, ERROR)
- `limit` (int)
- `offset` (int)

**Example:**
```bash
curl "http://localhost:8000/api/tests/42/logs?level=ERROR"
```

#### GET /api/tests/{test_id}/failures
Get failure messages for a test.

**Example:**
```bash
curl "http://localhost:8000/api/tests/42/failures"
```

### Statistics & Analytics Endpoints

#### GET /api/stats/summary
Get global summary statistics.

**Example:**
```bash
curl "http://localhost:8000/api/stats/summary"
```

**Response:**
```json
{
  "total_campaigns": 25,
  "total_tests": 543,
  "passed_tests": 478,
  "failed_tests": 65,
  "unknown_tests": 0,
  "pass_rate": 88.03,
  "total_results": 12543,
  "total_logs": 45678
}
```

#### GET /api/failures/common
Get most common failure messages across all tests.

**Query Parameters:**
- `limit` (int, default=10): Number of top failures

**Example:**
```bash
curl "http://localhost:8000/api/failures/common?limit=5"
```

**Response:**
```json
[
  {
    "message": "Peak amplitude below threshold",
    "count": 23,
    "test_names": ["test_rtn_defaults", "test_fwd_defaults", "..."]
  },
  {
    "message": "Timeout waiting for response",
    "count": 15,
    "test_names": ["test_memory_patch", "..."]
  }
]
```

### Export Endpoints

#### GET /api/export/failures
Export all failures to CSV or JSON.

**Query Parameters:**
- `campaign_id` (int, optional): Filter by campaign
- `format` (str): "csv" or "json" (default: csv)

**Example:**
```bash
# Download CSV of all failures
curl "http://localhost:8000/api/export/failures?format=csv" -o failures.csv

# Download JSON
curl "http://localhost:8000/api/export/failures?format=json" -o failures.json
```

#### GET /api/export/tests
Export test results based on filters.

**Query Parameters:**
- `status` (str, optional)
- `campaign_id` (int, optional)
- `format` (str): "csv" or "json"

**Example:**
```bash
# Export all failed tests as CSV
curl "http://localhost:8000/api/export/tests?status=failed&format=csv" -o failed_tests.csv
```

### Artefact Access Endpoints

#### GET /api/artefacts/{test_id}/analyzer
Serve the analyzer HTML file for a test.

**Example:**
```bash
# Open in browser
open "http://localhost:8000/api/artefacts/42/analyzer"
```

#### GET /api/artefacts/{test_id}/csv
Download the raw combined CSV file.

**Example:**
```bash
curl "http://localhost:8000/api/artefacts/42/csv" -o test_data.csv
```

## Usage Examples

### Python

```python
import requests

# Get all campaigns
response = requests.get("http://localhost:8000/api/campaigns")
campaigns = response.json()

for campaign in campaigns:
    print(f"{campaign['campaign_name']}: {campaign['total_tests']} tests")

# Search for failed tests
response = requests.get(
    "http://localhost:8000/api/tests",
    params={"status": "failed", "limit": 10}
)
failed_tests = response.json()

# Get test details
test_id = failed_tests[0]['test_id']
response = requests.get(f"http://localhost:8000/api/tests/{test_id}")
test_detail = response.json()

print(f"Test: {test_detail['test_name']}")
print(f"Status: {test_detail['status']}")
print(f"Failures: {test_detail['failure_messages']}")

# Export failures to CSV
response = requests.get(
    "http://localhost:8000/api/export/failures",
    params={"format": "csv"}
)
with open("failures.csv", "wb") as f:
    f.write(response.content)
```

### JavaScript (Browser)

```javascript
// Get global summary
fetch('http://localhost:8000/api/stats/summary')
  .then(response => response.json())
  .then(data => {
    console.log(`Total Tests: ${data.total_tests}`);
    console.log(`Pass Rate: ${data.pass_rate}%`);
  });

// Search tests
fetch('http://localhost:8000/api/tests?search=timeout&limit=20')
  .then(response => response.json())
  .then(tests => {
    tests.forEach(test => {
      console.log(`${test.test_name}: ${test.status}`);
    });
  });

// Get common failures
fetch('http://localhost:8000/api/failures/common?limit=10')
  .then(response => response.json())
  .then(failures => {
    failures.forEach(f => {
      console.log(`${f.message}: ${f.count} occurrences`);
    });
  });
```

### cURL Examples

```bash
# Health check
curl http://localhost:8000/health

# List campaigns
curl "http://localhost:8000/api/campaigns?limit=5"

# Get failed tests from specific campaign
curl "http://localhost:8000/api/campaigns/1/tests?status=failed"

# Search for tests with keyword
curl "http://localhost:8000/api/tests?search=overdrive"

# Get test details
curl "http://localhost:8000/api/tests/42"

# Get global summary
curl "http://localhost:8000/api/stats/summary"

# Get top 10 common failures
curl "http://localhost:8000/api/failures/common?limit=10"

# Export failures as JSON
curl "http://localhost:8000/api/export/failures?format=json" > failures.json
```

## CORS Configuration

CORS is enabled for all origins by default. For production, update the `allow_origins` in `api_server.py`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],  # Specific domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Error Handling

The API returns standard HTTP status codes:

- **200 OK**: Success
- **400 Bad Request**: Invalid parameters
- **404 Not Found**: Resource not found
- **500 Internal Server Error**: Server error

Error response format:
```json
{
  "detail": "Error message here"
}
```

## Performance

- **Pagination**: All list endpoints support `limit` and `offset`
- **Indexes**: Database has indexes on commonly queried fields
- **Connection pooling**: SQLAlchemy manages DB connections efficiently
- **Response streaming**: Large exports use streaming responses

### Recommended Limits

- List endpoints: 100-1000 results per page
- Result/log queries: 1000-10000 rows per request
- Export operations: No limits (streams data)

## Production Deployment

### Using Gunicorn

```bash
pip install gunicorn
gunicorn -w 4 -k uvicorn.workers.UvicornWorker api_server:app --bind 0.0.0.0:8000
```

### Using Docker

```dockerfile
FROM python:3.10-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000
CMD ["uvicorn", "api_server:app", "--host", "0.0.0.0", "--port", "8000"]
```

Build and run:
```bash
docker build -t test-results-api .
docker run -p 8000:8000 -v $(pwd)/test_results.db:/app/test_results.db test-results-api
```

## Troubleshooting

### Database locked error
SQLite doesn't handle high concurrency well. For production with multiple workers, use PostgreSQL.

### Port already in use
```bash
# Change port
uvicorn api_server:app --port 8001
```

### CORS errors
Ensure CORS middleware is configured for your frontend domain.

## Next Steps

After setting up the API:
1. Test endpoints using Swagger UI at http://localhost:8000/docs
2. Build frontend UI (Phase 3) that consumes this API
3. Add authentication/authorization if needed
4. Set up monitoring and logging
5. Consider PostgreSQL for production

## API Versioning

Current version: **v1.0.0**

All endpoints are prefixed with `/api/` for future versioning support.
