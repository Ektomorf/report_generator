# CSV Test Results Interactive Analyzer

An advanced interactive HTML analyzer for combined CSV test results that provides powerful filtering, column management, and data exploration capabilities.

## 🌟 Features

### **Interactive Data Exploration**
- **Column Visibility Controls**: Show/hide columns by category (Core, Test Results, Commands, Measurements, etc.)
- **Advanced Filtering**: Global search + per-column filters (text, numeric ranges, category selection)
- **Smart Row Highlighting**: Automatically distinguishes between test results and log entries
- **Cell Expansion**: Click to expand large cell content in modal popups
- **Sortable Columns**: Click headers to sort by any column (numeric or alphabetic)

### **Preset Management**
- **Built-in Presets**: Default View, Results Only, Logs Only, Errors & Warnings
- **Custom Presets**: Save your own column/filter combinations
- **Local Storage**: Presets persist across browser sessions

### **Data Export**
- Export filtered data as CSV
- Maintains current column visibility and filter settings

### **Responsive Design**
- Works on desktop, tablet, and mobile devices
- Sticky headers for large datasets
- Optimized for performance with thousands of rows

## 🚀 Quick Start

### Generate Analyzer for Single Test
```bash
python csv_analyzer.py path/to/test_combined.csv
```

### Batch Process All Tests
```bash
python csv_analyzer.py --batch output/
```

### Integration Script (Advanced)
```bash
# Single test with browser opening
python integrate_analyzer.py --single test_combined.csv --open

# Batch process with custom output directory
python integrate_analyzer.py --batch output/ --output-dir analyzers/

# Process files matching pattern
python integrate_analyzer.py --pattern "*fwd*combined.csv"
```

## 📊 Understanding Your Data

### Row Types and Highlighting

| Row Type | Appearance | Identification |
|----------|------------|----------------|
| **Test Results** | Green background, left border | Contains `Pass` column or measurement data |
| **Passed Tests** | Green left border | `Pass` = True |
| **Failed Tests** | Red left border, pink background | `Pass` = False |
| **Log Entries** | Gray background | Contains `log_type`, `level`, `message` |
| **Error Logs** | Red left border, pink background | `level` = ERROR/CRITICAL |
| **Warning Logs** | Yellow left border, light yellow background | `level` = WARNING |
| **Info Logs** | Blue left border | `level` = INFO |
| **Debug Logs** | Gray left border | `level` = DEBUG |

### Column Categories

The analyzer automatically groups columns for easier management:

- **Core**: Essential columns like Pass, timestamp
- **Test Results**: Peak data, amplitudes, frequencies, pass/fail status
- **Commands**: SoCAN commands, RF matrix commands, parsed responses
- **Measurements**: Peak tables, trace data, measurement metadata
- **Timing**: Timestamps, send/receive times
- **Configuration**: Channel settings, frequencies, gain values
- **Logging**: Log levels, messages, line numbers
- **Other**: Miscellaneous columns

## 🎯 Usage Examples

### Analyze Test Failures
1. Load a test analyzer HTML file
2. Select "Errors & Warnings" preset
3. Use Pass column filter to show only failed tests
4. Examine error messages and surrounding log context

### Investigate Performance Issues
1. Select "Results Only" preset
2. Filter by measurement columns (peak_amplitude, frequencies)
3. Sort by timing columns to find slow operations
4. Use cell expansion to examine detailed measurement data

### Debug Command Sequences
1. Show command-related columns (command_method, parsed_response)
2. Sort by timestamp to see command sequence
3. Filter by specific command types
4. Cross-reference with log entries for detailed context

### Export Filtered Data
1. Apply desired filters and column visibility
2. Click "Export Data" button
3. Filtered CSV will download with current view settings

## 🔧 Advanced Features

### Custom Filters

**Text Filters**: 
- Case-insensitive substring matching
- Use multiple terms: "error timeout" matches rows containing both words

**Numeric Filters**:
- Range filtering: set min/max values
- Works with frequencies, amplitudes, timing data

**Category Filters**:
- Multi-select dropdowns for log levels, commands, etc.
- Hold Ctrl/Cmd to select multiple values

### Global Search
- Searches across all visible columns
- Useful for finding specific test conditions or error messages
- Combines with column filters (AND logic)

### Preset Management
1. Configure your preferred columns and filters
2. Click "Save Preset"
3. Enter a descriptive name
4. Presets are saved in browser local storage
5. Access via dropdown in future sessions

## 📁 File Structure

```
report_generator/
├── csv_analyzer.py          # Main analyzer generator
├── integrate_analyzer.py    # Integration script with advanced options
├── output/                  # Test output directory
│   └── test_suite_name/
│       └── test_name/
│           ├── test_name_combined.csv         # Input CSV
│           └── test_name_combined_analyzer.html # Generated analyzer
└── analyzers/              # Optional custom output directory
```

## 🔍 Troubleshooting

### Large Files
- Analyzers handle thousands of rows efficiently
- Browser may be slow with 10,000+ rows
- Consider filtering data before analysis for very large files

### Missing Data
- Empty cells are shown as blank (not "null" or "undefined")
- Use column type indicators to understand expected data formats

### Browser Compatibility
- Works in all modern browsers (Chrome, Firefox, Safari, Edge)
- Requires JavaScript enabled
- Uses modern CSS Grid and Flexbox

### Performance Tips
- Hide unused columns to improve rendering speed
- Use presets to quickly switch between analysis views
- Export filtered data for further analysis in external tools

## 🎨 Customization

### Styling
The analyzer uses CSS custom properties for easy theming:
- Modify colors in the `<style>` section of generated HTML
- Row highlighting colors can be customized per row type

### Column Detection
The analyzer automatically detects column types based on:
- Column names (timestamp, frequency, amplitude, etc.)
- Data patterns (numeric, boolean, text)
- Special indicators (Pass column, log_type column)

### Adding New Row Types
Modify the `_is_result_row()` and `_get_row_class()` methods in `csv_analyzer.py` to add custom row highlighting logic.

## 📚 API Reference

### CSVToHTMLAnalyzer Class

```python
from csv_analyzer import CSVToHTMLAnalyzer

analyzer = CSVToHTMLAnalyzer()
analyzer.load_csv('test_data.csv')
analyzer.generate_html('output.html', 'My Test Analysis')
```

### Command Line Options

```bash
# Single file
python csv_analyzer.py input.csv [output.html]

# Batch processing
python csv_analyzer.py --batch input_directory/

# Integration script
python integrate_analyzer.py --help
```

## 🚀 Integration with Existing Workflow

### Automatic Generation
Add to your test pipeline:
```bash
# After generating combined CSV
python csv_analyzer.py --batch output/
```

### Custom Processing
```python
# In your Python test scripts
from csv_analyzer import CSVToHTMLAnalyzer

def generate_test_analyzer(csv_path, test_name):
    analyzer = CSVToHTMLAnalyzer()
    analyzer.load_csv(csv_path)
    html_path = csv_path.replace('.csv', '_analyzer.html')
    analyzer.generate_html(html_path, f"Analysis - {test_name}")
    return html_path
```

## 🔄 Updates and Maintenance

The analyzer is designed to be self-contained - each HTML file includes all necessary CSS and JavaScript. This ensures:
- **Portability**: Files can be shared without dependencies
- **Archival**: Historical analyses remain functional
- **Offline Use**: No internet connection required after generation

## 📄 License

This tool is part of your report generator project. Modify and distribute as needed for your testing requirements.

---

**Need Help?** Check the console (F12) for JavaScript errors, or examine the CSV structure if data doesn't appear as expected.