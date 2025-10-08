# SQL Test Results Importer - Quick Start Guide

## Overview
The SQL Importer scans your test output directory and imports all test results, logs, and metadata into a SQLite database for efficient querying and long-term archival.

## Installation

No additional dependencies required - uses Python standard library only.

## Database Setup

The importer automatically creates the database schema on first run. The schema is defined in `schema.sql`.

## Usage

### Basic Import

Import all test results from the `output` directory:

```bash
python sql_importer.py output
```

This creates a `test_results.db` file in the current directory.

### Custom Database Location

```bash
python sql_importer.py output --db /path/to/custom.db
```

### Full Re-import

By default, the importer runs in incremental mode (skips already-processed files). To re-process everything:

```bash
python sql_importer.py output --full
```

### View Database Summary

```bash
python sql_importer.py output --summary
```

Example output:
```
============================================================
DATABASE SUMMARY
============================================================
Campaigns:          15
Tests:              243
  - Passed:         198
  - Failed:         45
Test Results:       5432
Test Logs:          12890
Artefacts:          1215
  - Processed:      1215
============================================================
```

## How It Works

### 1. Directory Scanning

The importer scans the output directory structure:

```
output/
├── campaign_name_061025_115459/
│   ├── test_module__test_name/
│   │   ├── test_name_combined.csv          ← Test results & logs
│   │   ├── test_name_analyzer.html         ← Interactive viewer
│   │   ├── test_name_params.json           ← Test parameters
│   │   ├── test_name_status.json           ← Test metadata
│   │   └── screenshot_001.png              ← Screenshots
│   └── report.json
└── another_campaign_021025_130502/
    └── ...
```

### 2. File Hash Tracking

Each file is hashed (SHA256) to detect changes. Only new or modified files are processed in incremental mode.

### 3. Data Import

For each test:
- **Campaign** is extracted from directory name
- **Test metadata** from `*_status.json`
- **Test parameters** from `*_params.json`
- **Results & logs** from `*_combined.csv`
- **Analyzer HTML path** stored as reference

### 4. Database Schema

Key tables:
- `campaigns` - Test campaigns
- `tests` - Individual tests
- `test_params` - Test parameters
- `test_results` - Test result rows (Pass/Fail)
- `test_logs` - Log entries
- `failure_messages` - Extracted failure messages
- `artefacts` - File tracking with hashes

## Querying the Database

### Using SQLite CLI

```bash
sqlite3 test_results.db
```

Example queries:

```sql
-- Count tests by status
SELECT status, COUNT(*) FROM tests GROUP BY status;

-- Get all failed tests with failure messages
SELECT
    c.campaign_name,
    t.test_name,
    t.start_time,
    f.message
FROM tests t
JOIN campaigns c ON t.campaign_id = c.campaign_id
JOIN failure_messages f ON t.test_id = f.test_id
WHERE t.status = 'failed'
ORDER BY t.start_time DESC;

-- Find tests with specific failure message
SELECT
    c.campaign_name,
    t.test_name,
    t.start_time
FROM tests t
JOIN campaigns c ON t.campaign_id = c.campaign_id
JOIN failure_messages f ON t.test_id = f.test_id
WHERE f.message LIKE '%timeout%'
ORDER BY t.start_time DESC;

-- Get test results for a specific test
SELECT
    r.row_index,
    r.pass,
    r.command_method,
    r.failure_messages
FROM test_results r
JOIN tests t ON r.test_id = t.test_id
WHERE t.test_name = 'test_rtn_defaults'
ORDER BY r.row_index;

-- Campaign summary statistics
SELECT
    c.campaign_name,
    c.campaign_date,
    COUNT(*) as total_tests,
    SUM(CASE WHEN t.status = 'passed' THEN 1 ELSE 0 END) as passed,
    SUM(CASE WHEN t.status = 'failed' THEN 1 ELSE 0 END) as failed
FROM campaigns c
LEFT JOIN tests t ON c.campaign_id = t.campaign_id
GROUP BY c.campaign_id
ORDER BY c.campaign_date DESC;
```

### Using Python

```python
import sqlite3

conn = sqlite3.connect('test_results.db')
conn.row_factory = sqlite3.Row

cursor = conn.cursor()
cursor.execute("""
    SELECT campaign_name, test_name, status
    FROM tests t
    JOIN campaigns c ON t.campaign_id = c.campaign_id
    WHERE status = 'failed'
""")

for row in cursor.fetchall():
    print(f"{row['campaign_name']}: {row['test_name']} - {row['status']}")

conn.close()
```

## Incremental Updates

To add new test results without re-processing old ones:

1. Run your tests (new results go to `output/`)
2. Run the importer: `python sql_importer.py output`
3. Only new/changed files are processed

The importer tracks file hashes in the `artefacts` table to skip already-processed files.

## Performance

- **Initial import**: ~1-2 seconds per test (depends on CSV size)
- **Incremental import**: Only processes new files
- **Database size**: ~1-5 MB per 100 tests (varies with log volume)

## Troubleshooting

### Import Errors

If import fails on a specific test:
- Check CSV file is valid (not corrupted)
- Ensure JSON files are valid JSON
- Look for error messages in console output

### Missing Data

If tests are missing:
- Ensure directory structure matches expected format
- Check that `*_combined.csv` files exist
- Run with `--full` flag to re-process everything

### Database Corruption

If database appears corrupted:
```bash
# Backup old database
mv test_results.db test_results.db.backup

# Create fresh database
python sql_importer.py output --full
```

## Next Steps

After importing data:
1. Query the database directly with SQL
2. Use the REST API (Phase 2 - see `SQL_IMPLEMENTATION_TODO.md`)
3. View results in web UI (Phase 3 - see `SQL_IMPLEMENTATION_TODO.md`)

## File Locations

- **Database**: `test_results.db` (or custom path via `--db`)
- **Schema**: `schema.sql`
- **Importer**: `sql_importer.py`
- **Test Data**: `output/` directory
- **Analyzer HTMLs**: Preserved in original locations (referenced via `analyzer_html_path`)

## Notes

- Analyzer HTML files are NOT imported into the database - only their paths are stored
- Raw CSV/JSON files remain in the output directory (database is for querying)
- File hashes ensure idempotent imports (safe to run multiple times)
- Foreign key constraints maintain referential integrity
