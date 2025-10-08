## Test Campaign Browser - Web Frontend

Modern web interface for browsing and analyzing test results, powered by the SQL backend API.

## Features

✅ **Campaign Browser** - View all test campaigns organized by date
✅ **Test Cards** - Visual test result cards with color-coded status
✅ **Advanced Filtering** - Filter by status, campaign, and search text
✅ **Live Search** - Search across test names and failure messages
✅ **Failure Analysis** - View failure messages inline
✅ **Pagination** - Handle thousands of tests efficiently
✅ **Summary Statistics** - Global test statistics dashboard
✅ **Export** - Export failures to CSV
✅ **Direct Links** - Open analyzer HTML files directly
✅ **Responsive Design** - Works on desktop and mobile

## Architecture

```
Web Frontend (Static HTML/CSS/JS)
         ↓ (REST API calls)
API Server (FastAPI on :8000)
         ↓ (SQL queries)
SQLite Database (test_results.db)
```

## File Structure

```
web/
├── index.html      - Main HTML page
├── styles.css      - Styling (matches current index.html)
├── app.js          - Application logic and API integration
```

## Quick Start

### 1. Start API Server

The web frontend requires the API server to be running.

```bash
# In terminal 1
python api_server.py
```

API server will start on http://localhost:8000

### 2. Start Web Server

```bash
# In terminal 2
start_web.bat
```

Web server will start on http://localhost:8080

### 3. Open Browser

Open http://localhost:8080 in your web browser.

## Usage

### Main Dashboard

The main dashboard shows:
- **Filter Controls** at the top
  - Text search (searches test names and failure messages)
  - Status dropdown (All/Failed/Passed/Unknown)
  - Campaign dropdown (filter by specific campaign)
  - Clear filters button
  - Export failures button

- **Campaign Sections**
  - Each campaign shown in a separate section
  - Campaign name and date
  - Grid of test cards

- **Summary Statistics**
  - Total tests
  - Passed tests
  - Failed tests
  - Total campaigns
  - Pass rate percentage

### Test Cards

Each test card displays:
- Test name
- Test path (directory)
- Start time
- Status badge (color-coded)
- Failure messages (for failed tests)
- "View Analysis" link to analyzer HTML

**Color Coding:**
- 🟢 **Green border** - Passed tests
- 🔴 **Red border** - Failed tests
- 🟡 **Yellow border** - Unknown status

### Filtering

**By Status:**
Select from dropdown:
- All Tests
- Failed Tests Only
- Passed Tests Only
- Unknown Status

**By Campaign:**
Select specific campaign from dropdown

**By Text Search:**
Type in search box to filter by:
- Test names
- Failure message text

Filters combine (AND logic) - all active filters must match.

### Pagination

- Shows 100 tests per page
- Navigate with Previous/Next buttons
- Page info shows current range

### Export

Click "📥 Export All Failures to CSV" to download:
- All failure messages
- Campaign info
- Test names and paths
- Timestamps
- Formatted as CSV file

## Configuration

### API Endpoint

Edit `web/app.js` to change API URL:

```javascript
const API_BASE_URL = 'http://localhost:8000/api';
```

For production, update to your server URL:

```javascript
const API_BASE_URL = 'https://yourserver.com/api';
```

### Tests Per Page

Edit `web/app.js`:

```javascript
const TESTS_PER_PAGE = 100;  // Change to desired number
```

## Development

### Running Locally

For development with auto-reload:

```bash
# Use any static file server
cd web
python -m http.server 8080

# Or use Node.js
npx http-server -p 8080

# Or use Live Server (VS Code extension)
```

### Debugging

Open browser developer console (F12) to view:
- API calls and responses
- Error messages
- Application logs

### Making Changes

1. Edit HTML/CSS/JS files in `web/` directory
2. Refresh browser to see changes
3. No build step required (vanilla JS)

## API Integration

The frontend makes REST API calls to:

### On Page Load
```javascript
GET /api/stats/summary       // Global statistics
GET /api/campaigns           // All campaigns
GET /api/tests              // Tests (paginated)
GET /api/tests/{id}/failures // Failure messages (for failed tests)
```

### On Filter Change
```javascript
GET /api/tests?status=failed&search=keyword  // Filtered tests
```

### On Export
```javascript
GET /api/export/failures?format=csv  // Download CSV
```

### On View Analysis Click
```javascript
GET /api/artefacts/{test_id}/analyzer  // Serve analyzer HTML
```

## Comparison to Original index.html

### Preserved Features ✅
- Campaign browser layout
- Test cards with color coding
- Failure message display
- Status filtering
- Text search
- Summary statistics
- CSV export
- Links to analyzer HTMLs
- Responsive design

### New Features 🆕
- **Live data from SQL** - No static JSON, queries database
- **Better filtering** - Combine multiple filters
- **Campaign dropdown** - Filter by specific campaign
- **Pagination** - Handle thousands of tests
- **Real-time search** - Debounced search as you type
- **API-powered** - All data from REST API
- **Scalable** - Works with any number of tests

### Differences
- **Data source**: API calls instead of embedded JSON
- **Performance**: Paginated loading (faster for large datasets)
- **Statefulness**: Uses API for state, not local variables
- **Export**: API-generated CSV (more flexible)

## Performance

### Optimizations Implemented
- **Debounced search** - Wait for typing to stop before searching
- **Pagination** - Load 100 tests at a time
- **Lazy loading** - Failure messages loaded on-demand
- **Client-side caching** - Campaigns cached after first load

### Recommended Limits
- 100 tests per page (adjustable)
- 1000 campaigns max in dropdown
- Debounce delay: 500ms for search

### Handling Large Datasets
For thousands of tests:
1. Use pagination (already implemented)
2. Use filters to narrow results
3. Consider adding date range filter
4. Use export for bulk analysis

## Browser Compatibility

Tested on:
- Chrome 90+
- Firefox 88+
- Edge 90+
- Safari 14+

Requires:
- ES6 JavaScript support
- Fetch API
- CSS Grid

## Troubleshooting

### "Failed to fetch data" error

**Cause**: API server not running or CORS issue

**Solution**:
```bash
# Check API server is running
curl http://localhost:8000/health

# Restart API server
python api_server.py
```

### Tests not loading

**Cause**: Database empty or API error

**Solution**:
```bash
# Check database has data
python sql_importer.py output --summary

# Import test results
python sql_importer.py output
```

### Filters not working

**Solution**:
- Clear browser cache and reload
- Check browser console for errors
- Verify API responses in Network tab

### Export not downloading

**Cause**: Pop-up blocker or CORS

**Solution**:
- Allow pop-ups for localhost
- Check API CORS settings
- Try right-click → Save As on export link

## Production Deployment

### 1. Build for Production

No build step needed (vanilla JS), but consider:
- Minify CSS/JS for performance
- Use CDN for static assets
- Enable gzip compression

### 2. Serve with Nginx

```nginx
server {
    listen 80;
    server_name yourdomain.com;

    # Serve static frontend
    location / {
        root /path/to/web;
        try_files $uri $uri/ /index.html;
    }

    # Proxy API requests
    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 3. Update API URL

Edit `web/app.js`:
```javascript
const API_BASE_URL = 'https://yourdomain.com/api';
```

### 4. Enable HTTPS

Use Let's Encrypt or similar:
```bash
certbot --nginx -d yourdomain.com
```

## Security

### CORS
API server has CORS enabled for all origins (development).

For production, update `api_server.py`:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Authentication
Currently no authentication. To add:
1. Implement JWT or session-based auth in API
2. Add login page to frontend
3. Include auth token in API calls

## Future Enhancements

Potential additions:
- **Date range filter** - Filter tests by date
- **Test comparison** - Compare two test runs
- **Charts/graphs** - Visualize pass/fail trends
- **Test details modal** - Quick view without opening analyzer
- **Keyboard shortcuts** - Navigate with keyboard
- **Dark mode** - Toggle dark/light theme
- **Saved filters** - Bookmark common filter combinations
- **Real-time updates** - WebSocket for live test results

## Support

For issues:
1. Check browser console for errors
2. Verify API server is running
3. Check database has data
4. Review API documentation at http://localhost:8000/docs

## Files Reference

- **index.html** (93 lines) - Main page structure
- **styles.css** (358 lines) - Complete styling
- **app.js** (422 lines) - Application logic
- Total: ~870 lines of clean, documented code

## Next Steps

After setting up the web frontend:
1. Test with real data
2. Customize styling/branding
3. Add authentication if needed
4. Deploy to production
5. Consider Phase 4 features (advanced views)
