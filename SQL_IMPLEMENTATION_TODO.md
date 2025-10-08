# SQL-Based Test Results Archive System - Implementation Plan

## Project Overview
Create an SQL-based web server to manage and query test results from thousands of tests, replacing the current file-based index.html approach for scalable, shareable test result archival.

---

## 1. Summary of index.html Features

### Current Features
- **Campaign Browser**: Displays test campaigns organized by date/time
- **Test Cards**: Shows individual test results with:
  - Test name, path, start time
  - Pass/fail status with color coding
  - Failure messages (expandable)
  - Links to individual analyzer HTMLs
- **Filtering**:
  - Text filter for failure messages
  - "Show Only Failed Tests" button
  - Global search across all fields
- **Summary Statistics**:
  - Total tests
  - Passed tests
  - Failed tests
  - Total campaigns
- **Export**: CSV export of all failures with chronological ordering
- **Data Source**: Reads from:
  - `report.json` files
  - `*_combined.csv` for test status
  - `*_status.json` for timing
  - `*_analyzer.html` files (links only)

### Data Model (Current)
```
Campaign:
  - name (derived from directory)
  - date (parsed from campaign name)
  - tests[]

Test:
  - name
  - path (directory)
  - file (analyzer.html)
  - status (passed/failed/unknown)
  - start_time
  - start_timestamp
  - failure_messages[]
```

---

## 2. Review of _analyzer.html Structure

### Data Sources for Analyzer HTML
- **Primary**: `*_combined.csv` files containing:
  - Test results (Pass/Fail, commands, measurements)
  - Log entries (level, message, timestamp)
  - Merged timestamp columns
  - Failure messages

- **Metadata**:
  - `*_params.json` - Test parameters
  - Docstring from first row of CSV
  - `*_status.json` - Test execution metadata

### Features in Analyzer HTML
1. **Interactive Table**:
   - Column visibility controls
   - Column reordering (drag & drop)
   - Sorting
   - Row highlighting (results vs logs)
   - Cell expansion for long content

2. **Filtering**:
   - Global search
   - Per-column filters (text, numeric ranges, categories)
   - Hide empty rows
   - Presets (default, results-only)

3. **Data Export**: CSV export with visible columns

4. **Image Gallery**: For screenshot files

5. **Journalctl Integration**: Double-click rows to view system logs

### Processing Pipeline
```
PyTest → CSV files → csv_analyzer.py → analyzer.html
       → JSON files
```

---

## 3. SQL Database Design

### Schema

#### Tables

**campaigns**
```sql
campaign_id         INTEGER PRIMARY KEY
campaign_name       VARCHAR(255) UNIQUE NOT NULL
campaign_date       DATETIME
created_at          DATETIME DEFAULT CURRENT_TIMESTAMP
INDEX idx_campaign_date (campaign_date)
```

**tests**
```sql
test_id             INTEGER PRIMARY KEY
campaign_id         INTEGER REFERENCES campaigns(campaign_id)
test_name           VARCHAR(255) NOT NULL
test_path           VARCHAR(500)
status              ENUM('passed', 'failed', 'unknown')
start_time          DATETIME
start_timestamp     BIGINT
docstring           TEXT
analyzer_html_path  VARCHAR(500)
created_at          DATETIME DEFAULT CURRENT_TIMESTAMP
INDEX idx_campaign_test (campaign_id, test_name)
INDEX idx_status (status)
INDEX idx_start_time (start_time)
```

**test_params**
```sql
param_id            INTEGER PRIMARY KEY
test_id             INTEGER REFERENCES tests(test_id)
param_name          VARCHAR(255)
param_value         TEXT
INDEX idx_test_params (test_id)
```

**test_results**
```sql
result_id           INTEGER PRIMARY KEY
test_id             INTEGER REFERENCES tests(test_id)
row_index           INTEGER
timestamp           BIGINT
timestamp_formatted VARCHAR(50)
pass                BOOLEAN
command_method      VARCHAR(255)
command_str         TEXT
raw_response        TEXT
peak_frequency      FLOAT
peak_amplitude      FLOAT
failure_messages    TEXT
is_result_row       BOOLEAN DEFAULT TRUE
row_class           VARCHAR(50)
full_data_json      TEXT -- Store complete row as JSON for flexibility
INDEX idx_test_results (test_id, row_index)
INDEX idx_pass (pass)
INDEX idx_timestamp (timestamp)
```

**test_logs**
```sql
log_id              INTEGER PRIMARY KEY
test_id             INTEGER REFERENCES tests(test_id)
row_index           INTEGER
timestamp           BIGINT
timestamp_formatted VARCHAR(50)
level               VARCHAR(20)
message             TEXT
log_type            VARCHAR(50)
line_number         INTEGER
full_data_json      TEXT
INDEX idx_test_logs (test_id, row_index)
INDEX idx_level (level)
INDEX idx_timestamp (timestamp)
```

**failure_messages**
```sql
failure_id          INTEGER PRIMARY KEY
test_id             INTEGER REFERENCES tests(test_id)
message             TEXT
created_at          DATETIME DEFAULT CURRENT_TIMESTAMP
INDEX idx_test_failures (test_id)
INDEX idx_message_search (message(255)) -- For text search
```

**artefacts**
```sql
artefact_id         INTEGER PRIMARY KEY
test_id             INTEGER REFERENCES tests(test_id)
artefact_type       ENUM('csv', 'analyzer_html', 'log', 'json', 'screenshot')
file_path           VARCHAR(500) NOT NULL
file_hash           VARCHAR(64) -- SHA256 for deduplication
processed           BOOLEAN DEFAULT FALSE
processed_at        DATETIME
created_at          DATETIME DEFAULT CURRENT_TIMESTAMP
INDEX idx_test_artefacts (test_id, artefact_type)
INDEX idx_processed (processed)
INDEX idx_file_hash (file_hash)
```

**processing_log**
```sql
log_id              INTEGER PRIMARY KEY
artefact_id         INTEGER REFERENCES artefacts(artefact_id)
processing_status   ENUM('pending', 'processing', 'completed', 'failed')
error_message       TEXT
started_at          DATETIME
completed_at        DATETIME
```

---

## 4. Data Processing Script

### Processing Strategy
1. **Scan for artefacts**: Find all `*_analyzer.html`, `*.csv`, `*.json` files
2. **Check if processed**: Use `file_hash` to avoid re-processing
3. **Extract data**:
   - Parse CSV files directly (more reliable than parsing HTML)
   - Extract metadata from JSON files
   - Store analyzer HTML paths as references
4. **Incremental updates**: Only process new/modified artefacts

### Implementation: `sql_importer.py`
```python
Key Functions:
- scan_artefacts(base_dir) -> List[ArtefactInfo]
- calculate_file_hash(file_path) -> str
- is_artefact_processed(file_hash) -> bool
- process_campaign(campaign_dir) -> CampaignData
- import_test_data(test_dir, campaign_id) -> None
- import_csv_data(csv_path, test_id) -> None
- import_test_params(params_json, test_id) -> None
```

---

## 5. SQL Backend API Design

### Technology Stack
- **Framework**: Flask or FastAPI (Python)
- **Database**: PostgreSQL (production) / SQLite (development)
- **ORM**: SQLAlchemy

### API Endpoints

#### Campaign Queries
```
GET /api/campaigns
  - List all campaigns with summary stats
  - Query params: ?limit=N&offset=N&order_by=date&direction=desc

GET /api/campaigns/{campaign_id}
  - Get campaign details with all tests

GET /api/campaigns/{campaign_id}/tests
  - List tests in campaign
  - Query params: ?status=failed&limit=N&offset=N
```

#### Test Queries
```
GET /api/tests
  - Search/filter tests across all campaigns
  - Query params:
    - ?status=failed
    - ?campaign_id=123
    - ?start_date=2025-01-01
    - ?end_date=2025-12-31
    - ?search=keyword (searches test_name, failure_messages)
    - ?limit=N&offset=N

GET /api/tests/{test_id}
  - Get complete test details including results and logs

GET /api/tests/{test_id}/results
  - Get test results (from test_results table)

GET /api/tests/{test_id}/logs
  - Get test logs (from test_logs table)

GET /api/tests/{test_id}/failures
  - Get failure messages for test
```

#### Statistics & Analytics
```
GET /api/stats/summary
  - Global summary: total tests, pass rate, campaigns

GET /api/stats/trends
  - Time-series data for pass/fail trends
  - Query params: ?start_date=&end_date=&granularity=day

GET /api/failures/common
  - Most common failure messages across all tests
  - Query params: ?limit=10
```

#### Export & Downloads
```
GET /api/export/failures
  - Export failures to CSV (same as current index.html)
  - Query params: ?campaign_id=&status=&format=csv|json

GET /api/export/tests
  - Export test results based on filters
```

#### Artefact Access
```
GET /api/artefacts/{test_id}/analyzer
  - Serve the analyzer.html file for a test

GET /api/artefacts/{test_id}/csv
  - Serve the raw CSV data
```

---

## 6. Web Frontend Design

### Architecture
- **Base Template**: Adapt current `index.html` structure
- **Technology**: Vanilla JS + modern CSS (or Vue.js for reactivity)
- **Communication**: REST API calls to backend

### Pages/Views

#### 1. Main Dashboard (index.html equivalent)
```
Components:
- Campaign browser (paginated, server-side)
- Filter panel:
  - Date range picker
  - Status filter (passed/failed/unknown)
  - Campaign name search
  - Failure message text search
- Summary statistics (total, passed, failed, campaigns)
- Test cards grid (lazy loaded)
- Export button → triggers API call
```

#### 2. Campaign Detail View
```
URL: /campaigns/{campaign_id}
- Campaign metadata
- List of all tests in campaign
- Campaign-level statistics
- Filtering within campaign
```

#### 3. Test Detail View
```
URL: /tests/{test_id}
- Embedded analyzer.html (iframe or direct link)
- Test metadata sidebar
- Quick stats
- Link to download raw CSV/JSON
```

#### 4. Advanced Search View
```
URL: /search
- Multi-field search form:
  - Test name
  - Campaign name
  - Date range
  - Status
  - Failure message keywords
  - Test parameter filters
- Results table with pagination
- Export filtered results
```

#### 5. Analytics Dashboard
```
URL: /analytics
- Pass/fail trends over time (charts)
- Most common failures
- Test execution time trends
- Campaign comparison
```

### Key Features to Preserve from Current index.html
- ✅ Campaign browser with test cards
- ✅ Color-coded status (green/red/yellow)
- ✅ Failure message display
- ✅ Filter by failure message text
- ✅ Show only failures toggle
- ✅ CSV export
- ✅ Summary statistics
- ✅ Links to analyzer HTMLs

### New Features Enabled by SQL
- 🆕 Advanced search across all tests ever run
- 🆕 Date range filtering
- 🆕 Pagination for thousands of tests
- 🆕 Test parameter filtering
- 🆕 Failure message aggregation/analytics
- 🆕 Trend visualization
- 🆕 Bookmarkable filtered views (URL parameters)

---

## 7. Query Result Caching & Index.html Generation

### Strategy
For common queries (e.g., "last 7 days failures"), generate static HTML files to reduce server load.

### Implementation
```python
# Cached Query Manager
- Store query hash → generated HTML mapping
- TTL-based cache expiration (e.g., 1 hour)
- Background job to pre-generate common queries:
  - Last 24 hours
  - Last 7 days
  - Latest 100 tests
  - All failures from last campaign

# Static HTML Generation
- Use Jinja2 templates
- Generate mini-index.html files for specific queries
- Store in /cache/{query_hash}.html
- Serve directly via nginx (fast static file serving)
```

### Cache Invalidation
- On new data import, invalidate affected caches
- Use message queue (e.g., Redis pub/sub) to notify web servers

---

## 8. Performance Optimizations for Thousands of Tests

### Database Optimizations
1. **Indexing** (already in schema):
   - Campaign date, test status, timestamps
   - Failure message full-text search index

2. **Partitioning**:
   - Partition `test_results` and `test_logs` by `campaign_id` or date range

3. **Query Optimization**:
   - Use `LIMIT` and `OFFSET` for pagination
   - Avoid `SELECT *`, fetch only needed columns
   - Use `COUNT(*)` with covering indexes

4. **Connection Pooling**: SQLAlchemy pool for efficient DB connections

### Application Optimizations
1. **Pagination**:
   - Server-side pagination (100 tests per page)
   - Infinite scroll or numbered pages

2. **Lazy Loading**:
   - Load test cards on scroll
   - Defer loading of failure messages until expanded

3. **API Response Caching**:
   - Use Redis for caching API responses
   - Cache key: query parameters hash
   - TTL: 5-15 minutes

4. **Compression**:
   - Enable gzip compression for JSON responses
   - Compress large analyzer.html files

5. **CDN**:
   - Serve static assets (CSS, JS, images) via CDN
   - Cache analyzer.html files

### Frontend Optimizations
1. **Virtual Scrolling**: For large lists of tests
2. **Debounced Search**: Wait for user to stop typing before searching
3. **Progressive Loading**: Show summary first, load details on demand

---

## 9. Implementation Roadmap

### Phase 1: Database & Import (Week 1)
- [ ] Set up PostgreSQL database
- [ ] Create schema with migrations
- [ ] Implement `sql_importer.py`:
  - Scan artefacts
  - Import campaigns, tests, CSV data
  - Handle incremental processing
- [ ] Test with existing output directory

### Phase 2: Backend API (Week 2)
- [ ] Set up Flask/FastAPI project
- [ ] Implement core API endpoints:
  - Campaigns list & detail
  - Tests search & filter
  - Failures export
- [ ] Add authentication (optional)
- [ ] Write API tests

### Phase 3: Frontend - Basic (Week 3)
- [ ] Port `index.html` to template system
- [ ] Implement main dashboard with API integration
- [ ] Add pagination and filtering
- [ ] Test with real data

### Phase 4: Frontend - Advanced (Week 4)
- [ ] Create campaign detail view
- [ ] Create test detail view (embed analyzer.html)
- [ ] Create advanced search page
- [ ] Add export functionality

### Phase 5: Analytics & Optimization (Week 5)
- [ ] Implement analytics dashboard
- [ ] Add caching layer (Redis)
- [ ] Generate static HTML for common queries
- [ ] Performance testing with 1000+ tests

### Phase 6: Deployment (Week 6)
- [ ] Docker containerization
- [ ] Set up nginx reverse proxy
- [ ] Deploy to server
- [ ] Configure backups
- [ ] Write user documentation

---

## 10. Technology Recommendations

### Backend
- **Language**: Python 3.10+
- **Framework**: FastAPI (async, fast, modern) or Flask (simpler, well-known)
- **Database**: PostgreSQL 14+ (production), SQLite (development/testing)
- **ORM**: SQLAlchemy 2.0
- **Cache**: Redis 7+
- **Task Queue**: Celery (for background import jobs)

### Frontend
- **Framework**: Vue.js 3 or React (for complex UI) OR Vanilla JS + Alpine.js (simpler)
- **Charts**: Chart.js or Plotly.js
- **CSS**: Tailwind CSS or Bootstrap 5
- **Build Tool**: Vite

### Deployment
- **Containerization**: Docker + Docker Compose
- **Web Server**: Nginx (reverse proxy, static file serving)
- **WSGI**: Gunicorn or Uvicorn (FastAPI)
- **Monitoring**: Prometheus + Grafana
- **Logging**: ELK stack or simple file-based

---

## 11. Future Enhancements

1. **Real-time Updates**: WebSocket for live test result streaming
2. **Test Comparison**: Side-by-side comparison of two test runs
3. **Alerts**: Email/Slack notifications for test failures
4. **Test History**: Track same test across multiple campaigns
5. **Custom Dashboards**: User-configurable dashboard widgets
6. **API Keys**: Generate API keys for external integrations
7. **Regression Detection**: ML-based failure pattern analysis
8. **Multi-tenant**: Support multiple projects/teams

---

## Notes
- All analyzer.html files remain as artefacts and are served via links (not re-created)
- Raw CSV/JSON files are preserved for audit trail
- SQL database is the source of truth for querying; files are the backup
- Consider data retention policies (archive old campaigns after N months)
