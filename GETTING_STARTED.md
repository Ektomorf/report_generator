# Getting Started - SQL Test Results System

Complete guide to set up and use the SQL-based test results archival system.

## System Overview

```
┌─────────────────┐
│  Test Output    │  (PyTest generates CSV/JSON files)
│  Directory      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ sql_importer.py │  (Scans and imports to database)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  test_results   │  (SQLite database)
│      .db        │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  api_server.py  │  (REST API on :8000)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Web Frontend   │  (Browser UI on :8080)
│  (index.html)   │
└─────────────────┘
```

## Quick Start (5 Minutes)

### Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

This installs:
- FastAPI (REST API framework)
- Uvicorn (ASGI server)
- SQLAlchemy (Database ORM)
- Pydantic (Data validation)

### Step 2: Import Test Results

```bash
python sql_importer.py output
```

This will:
- Scan `output/` directory for test results
- Create `test_results.db` SQLite database
- Import campaigns, tests, results, and logs
- Track file hashes for incremental updates

**Example output:**
```
Starting import from: output
Incremental mode: True
Scanning for artefacts in: output
Found 245 artefacts

Processing campaign 1/5: socan_061025_103235
  Test 1/15: test_rtn_defaults
    Importing CSV: test_rtn_defaults_combined.csv
    Imported 234 rows from CSV
...

============================================================
DATABASE SUMMARY
============================================================
Campaigns:          5
Tests:              75
  - Passed:         62
  - Failed:         13
Test Results:       5432
Test Logs:          12890
Artefacts:          245
  - Processed:      245
============================================================
```

### Step 3: Start API Server

```bash
python api_server.py
```

**Or use the batch file:**
```bash
start_api.bat
```

The API server starts on http://localhost:8000

**Verify it's working:**
- Open http://localhost:8000/docs (Swagger UI)
- Open http://localhost:8000/health (Health check)

### Step 4: Start Web Frontend

In a **new terminal**:

```bash
start_web.bat
```

**Or manually:**
```bash
cd web
python -m http.server 8080
```

The web server starts on http://localhost:8080

### Step 5: Open in Browser

Open http://localhost:8080 in your web browser.

You should see:
- Campaign browser with test cards
- Filter controls
- Summary statistics

## Complete Workflow

### 1. Run Tests (Already Done)

Your PyTest framework generates:
```
output/
├── campaign_name_061025_115459/
│   ├── test_module__test_name/
│   │   ├── test_name_combined.csv
│   │   ├── test_name_analyzer.html
│   │   ├── test_name_params.json
│   │   ├── test_name_status.json
│   └── report.json
```

### 2. Import to Database

**Initial import:**
```bash
python sql_importer.py output
```

**Incremental import** (after new tests):
```bash
python sql_importer.py output
```

Only new/modified files are processed (via file hashing).

**Force re-import everything:**
```bash
python sql_importer.py output --full
```

**View database summary:**
```bash
python sql_importer.py output --summary
```

### 3. Query the API

You can use the API directly without the web UI:

**Using cURL:**
```bash
# Get all campaigns
curl http://localhost:8000/api/campaigns

# Get failed tests
curl http://localhost:8000/api/tests?status=failed

# Get global summary
curl http://localhost:8000/api/stats/summary

# Export failures
curl "http://localhost:8000/api/export/failures?format=csv" -o failures.csv
```

**Using Python:**
```python
import requests

# Get summary
response = requests.get("http://localhost:8000/api/stats/summary")
print(response.json())

# Search for failed tests
response = requests.get(
    "http://localhost:8000/api/tests",
    params={"status": "failed", "limit": 10}
)
for test in response.json():
    print(f"{test['test_name']}: {test['status']}")
```

**Interactive API docs:**
- http://localhost:8000/docs (Swagger UI)
- http://localhost:8000/redoc (ReDoc)

### 4. Browse in Web UI

Open http://localhost:8080

**Filter tests:**
- Select "Failed Tests Only" from status dropdown
- Type keywords in search box
- Select specific campaign

**View test details:**
- Click "View Analysis →" to open analyzer HTML
- Failure messages shown inline on failed tests

**Export data:**
- Click "📥 Export All Failures to CSV"
- Downloads CSV with all failure information

## Daily Usage

### Adding New Test Results

After running new tests:

```bash
# 1. Import new results (incremental - fast)
python sql_importer.py output

# 2. API server picks up changes automatically
# (no restart needed - just refresh browser)
```

### Querying Test History

**Find tests with specific failure:**
```bash
curl "http://localhost:8000/api/tests?search=timeout"
```

**Get all failures from last campaign:**
```bash
# Get latest campaign ID
curl "http://localhost:8000/api/campaigns?limit=1" | jq '.[0].campaign_id'

# Export its failures
curl "http://localhost:8000/api/export/failures?campaign_id=5&format=csv" -o latest_failures.csv
```

**Find common failure patterns:**
```bash
curl "http://localhost:8000/api/failures/common?limit=10"
```

### Analyzing Trends

Use the API to track test history:

```python
import requests
import pandas as pd

# Get all tests
response = requests.get("http://localhost:8000/api/tests?limit=1000")
tests = pd.DataFrame(response.json())

# Group by campaign
summary = tests.groupby('campaign_name').agg({
    'test_id': 'count',
    'status': lambda x: (x == 'passed').sum()
})
summary.columns = ['total', 'passed']
summary['pass_rate'] = (summary['passed'] / summary['total'] * 100).round(2)

print(summary)
```

## Architecture Details

### Database Schema

9 tables:
- `campaigns` - Test campaigns
- `tests` - Individual tests
- `test_params` - Test parameters
- `test_results` - Result rows (Pass/Fail)
- `test_logs` - Log entries
- `failure_messages` - Extracted failures
- `artefacts` - File tracking
- `processing_log` - Import history

**View schema:**
```bash
sqlite3 test_results.db ".schema"
```

### API Endpoints

**Campaigns:**
- `GET /api/campaigns` - List all campaigns
- `GET /api/campaigns/{id}` - Campaign details
- `GET /api/campaigns/{id}/tests` - Tests in campaign

**Tests:**
- `GET /api/tests` - Search/filter tests
- `GET /api/tests/{id}` - Test details
- `GET /api/tests/{id}/results` - Test results
- `GET /api/tests/{id}/logs` - Test logs
- `GET /api/tests/{id}/failures` - Failure messages

**Statistics:**
- `GET /api/stats/summary` - Global summary
- `GET /api/failures/common` - Common failures

**Export:**
- `GET /api/export/failures` - Export failures CSV/JSON
- `GET /api/export/tests` - Export tests CSV/JSON

**Artefacts:**
- `GET /api/artefacts/{id}/analyzer` - Serve analyzer HTML
- `GET /api/artefacts/{id}/csv` - Download CSV

### Web Frontend

3 files:
- `web/index.html` - Page structure
- `web/styles.css` - Styling (matches original index.html)
- `web/app.js` - Application logic

**Features:**
- Campaign browser
- Test cards with color coding
- Filtering (status, search, campaign)
- Pagination (100 tests/page)
- Summary statistics
- CSV export
- Direct links to analyzer HTMLs

## Advanced Usage

### Custom Queries

Use SQLite directly for custom analysis:

```bash
sqlite3 test_results.db
```

**Example queries:**

```sql
-- Find flaky tests (passed and failed across campaigns)
SELECT test_name, COUNT(DISTINCT status) as status_count
FROM tests
GROUP BY test_name
HAVING status_count > 1;

-- Average test execution by campaign
SELECT
    c.campaign_name,
    AVG(julianday(t.start_time) - julianday(c.campaign_date)) * 24 * 60 as avg_duration_minutes
FROM tests t
JOIN campaigns c ON t.campaign_id = c.campaign_id
GROUP BY c.campaign_id;

-- Most common failure messages
SELECT message, COUNT(*) as count
FROM failure_messages
GROUP BY message
ORDER BY count DESC
LIMIT 10;
```

### Automation

**Daily import script:**
```bash
# daily_import.bat
@echo off
echo Running daily test import...
python sql_importer.py output
echo Done! Check database for updates.
```

**Schedule with Task Scheduler** (Windows):
```powershell
schtasks /create /sc daily /tn "Import Test Results" /tr "C:\path\to\daily_import.bat" /st 09:00
```

### Integration with CI/CD

Add to your CI pipeline:

```yaml
# .github/workflows/tests.yml
- name: Run Tests
  run: pytest

- name: Import Results to SQL
  run: python sql_importer.py output

- name: Check Pass Rate
  run: |
    curl http://api-server/api/stats/summary | jq -r '.pass_rate' | awk '$1 < 95 {exit 1}'
```

## Troubleshooting

### Database Issues

**Error: "database is locked"**

SQLite doesn't handle concurrent writes well.

**Solution:**
```bash
# Stop all processes accessing database
# Re-run import
python sql_importer.py output
```

**Corrupted database:**
```bash
# Backup
copy test_results.db test_results.db.backup

# Re-import from scratch
del test_results.db
python sql_importer.py output --full
```

### API Issues

**Error: "Failed to fetch data"**

Check API server is running:
```bash
curl http://localhost:8000/health
```

**Port 8000 already in use:**
```bash
# Change port
uvicorn api_server:app --port 8001
```

Then update `web/app.js`:
```javascript
const API_BASE_URL = 'http://localhost:8001/api';
```

### Import Issues

**No artefacts found:**

Check directory structure:
```bash
dir output /s | findstr "combined.csv"
```

Expected structure:
```
output/campaign_name_DDMMYY_HHMMSS/test_*/test_name_combined.csv
```

**Import fails on specific test:**

Check CSV file is valid:
```bash
python -c "import csv; csv.DictReader(open('path/to/file.csv'))"
```

## Performance Tips

### For Large Databases (1000+ tests)

1. **Use PostgreSQL instead of SQLite:**
   - Update `api_server.py` DATABASE_URL
   - Better concurrency and performance

2. **Add indexes:**
   ```sql
   CREATE INDEX idx_custom ON tests(field_name);
   ```

3. **Increase pagination:**
   ```javascript
   // web/app.js
   const TESTS_PER_PAGE = 200;
   ```

4. **Use filters:**
   - Don't load all tests at once
   - Filter by campaign or date range

## File Locations

```
report_generator/
├── schema.sql                  # Database schema
├── sql_importer.py            # Import tool
├── api_server.py              # REST API server
├── models.py                  # SQLAlchemy models
├── requirements.txt           # Python dependencies
├── test_results.db           # SQLite database (created)
├── start_api.bat             # Start API server
├── start_web.bat             # Start web server
├── web/
│   ├── index.html            # Main page
│   ├── styles.css            # Styling
│   └── app.js                # Frontend logic
├── output/                   # Test results directory
│   └── campaign_*/
│       └── test_*/
│           ├── *_combined.csv
│           ├── *_analyzer.html
│           ├── *_params.json
│           └── *_status.json
└── README_*.md               # Documentation
```

## Next Steps

Now that you have the basic system running:

### Phase 4: Advanced Features (Optional)

See `SQL_IMPLEMENTATION_TODO.md` for:
- Campaign detail page
- Test detail modal
- Advanced search page
- Analytics dashboard with charts

### Phase 5: Analytics & Optimization (Optional)

- Add Redis caching
- Implement static HTML generation
- Performance testing

### Phase 6: Production Deployment (Optional)

- Docker containerization
- Nginx reverse proxy
- HTTPS setup
- Backups and monitoring

## Resources

- **SQL Importer**: [README_SQL_IMPORTER.md](README_SQL_IMPORTER.md)
- **API Server**: [README_API_SERVER.md](README_API_SERVER.md)
- **Web Frontend**: [README_WEB_FRONTEND.md](README_WEB_FRONTEND.md)
- **API Reference**: [API_QUICK_REFERENCE.md](API_QUICK_REFERENCE.md)
- **Full Plan**: [SQL_IMPLEMENTATION_TODO.md](SQL_IMPLEMENTATION_TODO.md)

## Support

Common issues:
1. Check each component separately (importer → API → web)
2. Review logs/console for errors
3. Verify database has data
4. Test API endpoints directly
5. Check browser console for frontend errors

## Success Checklist

✅ Dependencies installed (`pip install -r requirements.txt`)
✅ Database created and populated (`python sql_importer.py output`)
✅ API server running (`python api_server.py` → http://localhost:8000)
✅ Web server running (`start_web.bat` → http://localhost:8080)
✅ Can view tests in browser
✅ Filters working
✅ Export working
✅ Analyzer links opening

**You're all set!** 🎉
