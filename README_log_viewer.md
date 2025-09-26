# Log Viewer Tool

A Python tool to convert test log files to CSV and generate interactive HTML viewers with advanced filtering and column management capabilities.

## Features

- **Log to CSV Conversion**: Parses structured log files with JSON data and converts them to CSV format
- **Interactive HTML Viewer**: Web-based interface for viewing and analyzing log data
- **Column Management**: Show/hide columns with CSS controls
- **Text Search Filtering**: Real-time search across all log data
- **Column Presets**: Pre-defined column sets for different viewing needs
- **Responsive Design**: Works on different screen sizes
- **Timestamp Support**: Handles millisecond-resolution timestamps

## Usage

### Basic Usage

```bash
python log_viewer.py path/to/logfile.log
```

### Specify Output Directory

```bash
python log_viewer.py path/to/logfile.log --output-dir /custom/output/path
```

### Example

```bash
# Convert a test log file
python log_viewer.py "output/rtn_v1_1_default/test_v1_1_rtn__test_rtn_defaults/test_rtn_defaults.log"

# This creates:
# - test_rtn_defaults.csv (CSV data)
# - test_rtn_defaults_viewer.html (Interactive HTML viewer)
```

## Log File Format

The tool expects log files with the following format and supports multiple timestamp formats:

**Format 1 - Time only:**
```
HH:MM:SS - LEVEL - {JSON_DATA}
```

**Format 2 - Full timestamp with milliseconds:**
```
YYYY-MM-DD HH:MM:SS,mmm - LEVEL - {JSON_DATA}
```

Examples:
```
14:41:48 - INFO - {'command_method': 'get_channel', 'command_str': 'sendACQ $03 $00 13', 'raw_response': 'OK'}
2025-09-26 15:08:15,575 - INFO - {'send_timestamp': '2025-09-26 15:08:15,564', 'receive_timestamp': '2025-09-26 15:08:15,575', 'command_method': 'get_channel'}
```

## HTML Viewer Features

### Column Presets

- **Basic**: `timestamp`, `level`, `command_method`, `command_str`
- **Detailed**: Basic + `raw_response`, `parsed_response`
- **Network**: `timestamp`, `level`, `command_method`, `raw_response`
- **All**: All available columns

### Search Functionality

- Real-time text search across all columns
- Case-insensitive matching
- Searches through all data including JSON content

### Column Controls

- Individual column visibility toggles
- Checkbox controls for each column
- Scrollable column list for many columns
- Column ordering preserved from CSV

### Navigation

- Sticky table headers
- Horizontal and vertical scrolling
- Row highlighting on hover
- Status bar showing filtered/total rows and visible columns

## Output Files

### CSV File (`{logname}.csv`)
- Flattened JSON data as columns
- Nested objects become prefixed columns (e.g., `parsed_response_frequency`)
- Arrays converted to JSON strings for CSV compatibility
- All data preserved for analysis

### HTML Viewer (`{logname}_viewer.html`)
- Self-contained HTML file with embedded CSS and JavaScript
- No external dependencies
- Can be opened in any modern web browser
- Responsive design for different screen sizes

## Column Naming

The tool automatically flattens nested JSON structures:
- `command_method` → `command_method`
- `parsed_response.frequency` → `parsed_response_frequency`
- `**kwargs.address` → `**kwargs_address`

## Requirements

- Python 3.6+
- No external dependencies (uses only standard library)

## File Structure

When processing test suites, the tool works with:
```
output/
├── test_suite_name/
│   ├── test_run_1/
│   │   ├── test_file.log          # Input log file
│   │   ├── test_file.csv          # Generated CSV
│   │   └── test_file_viewer.html  # Generated HTML viewer
│   └── test_run_2/
│       └── ...
```

## Browser Compatibility

The HTML viewer works with:
- Chrome/Edge (recommended)
- Firefox
- Safari
- Any modern browser with JavaScript enabled

## Performance

- Handles log files with thousands of entries
- Client-side filtering for responsive search
- Efficient CSV parsing and rendering
- Minimal memory footprint