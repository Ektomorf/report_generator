# Test Results API - Quick Reference Card

## Start Server
```bash
python api_server.py
# or
start_api.bat
```

## Interactive Documentation
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Common Endpoints

### Campaigns
```bash
GET /api/campaigns                    # List all campaigns
GET /api/campaigns/1                  # Get campaign details
GET /api/campaigns/1/tests            # List tests in campaign
```

### Tests
```bash
GET /api/tests?status=failed          # All failed tests
GET /api/tests?search=timeout         # Search tests
GET /api/tests/42                     # Test details
GET /api/tests/42/results             # Test results
GET /api/tests/42/logs                # Test logs
GET /api/tests/42/failures            # Failure messages
```

### Statistics
```bash
GET /api/stats/summary                # Global stats
GET /api/failures/common              # Top failures
```

### Export
```bash
GET /api/export/failures?format=csv   # Export failures CSV
GET /api/export/tests?status=failed   # Export failed tests
```

### Artefacts
```bash
GET /api/artefacts/42/analyzer        # View analyzer HTML
GET /api/artefacts/42/csv             # Download CSV
```

## Query Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| limit | int | Max results (default: 100) | `?limit=50` |
| offset | int | Pagination offset | `?offset=100` |
| status | str | Filter by status | `?status=failed` |
| search | str | Search keyword | `?search=timeout` |
| start_date | str | Filter by date | `?start_date=2025-10-01` |
| end_date | str | Filter by date | `?end_date=2025-10-31` |
| campaign_id | int | Filter by campaign | `?campaign_id=1` |
| format | str | Export format | `?format=csv` or `json` |

## Python Example
```python
import requests

# Get summary
r = requests.get("http://localhost:8000/api/stats/summary")
print(r.json())

# Search failed tests
r = requests.get("http://localhost:8000/api/tests",
                 params={"status": "failed", "limit": 10})
for test in r.json():
    print(f"{test['test_name']}: {test['status']}")
```

## cURL Examples
```bash
# Get campaigns
curl "http://localhost:8000/api/campaigns?limit=5"

# Search tests
curl "http://localhost:8000/api/tests?search=overdrive"

# Export failures
curl "http://localhost:8000/api/export/failures?format=csv" -o failures.csv
```

## Status Codes
- 200: Success
- 400: Bad request
- 404: Not found
- 500: Server error
