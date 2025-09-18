# RS ATS Test Report Generator

A Python script to generate professional HTML reports from RS ATS test results.

## Features

- **Comprehensive Test Reports**: Parses JSON result files and generates detailed HTML reports
- **Visual Screenshots**: Embeds test screenshots directly in the reports
- **Professional Styling**: Clean, responsive HTML design with CSS styling
- **Batch Processing**: Processes multiple test runs automatically
- **Index Page**: Creates a master index linking all test reports
- **Command Line Interface**: Easy to use with flexible options

## File Structure

The script expects test result directories with the following structure:
```
output/setups_YYYYMMDD_HHMMSS/
├── test_name_1/
│   ├── test_name_1_results.json    # Test measurement data
│   ├── test_name_1_params.json     # Test parameters
│   ├── test_name_1_status.json     # Test status (PASSED/FAILED)
│   └── screenshot.png              # Screenshots
├── test_name_2/
│   └── ...
└── ...
```

## Usage

### Basic Usage
Generate reports for a test session:
```bash
python3 test_report_generator.py output/setups_180925_091733
```

### Custom Output Directory
Save reports to a specific directory:
```bash
python3 test_report_generator.py output/setups_180925_091733 --output-dir reports
```

### Batch Processing
Process multiple test sessions:
```bash
# Process all setup directories
for dir in output/setups_*/; do
    echo "Processing $dir..."
    python3 test_report_generator.py "$dir" --output-dir "reports/$(basename "$dir")"
done
```

### Help
```bash
python3 test_report_generator.py --help
```

## Output

The script generates:

1. **Individual Test Reports**: One HTML file per test run (`test_name_report.html`)
2. **Index Page**: Master index with links to all reports (`index.html`)

### Report Contents

Each test report includes:

- **Test Status**: PASSED/FAILED status with timing information
- **Test Parameters**: Configuration parameters used for the test
- **Results Table**: Detailed measurement data with:
  - Timestamps
  - SOCAN commands and responses
  - RF Matrix commands
  - Keysight instrument commands
  - Peak frequency and amplitude measurements
  - Screenshot references
- **Screenshots**: Embedded images for visual verification

## Requirements

- Python 3.6+
- Standard library modules only (json, os, argparse, pathlib, datetime, base64)

## Example

```bash
# Test the script with example data
python3 test_report_generator.py output/setups_180925_091733 --output-dir reports_test

# View results
firefox reports_test/index.html
```

## File Descriptions

- `test_report_generator.py` - Main script for generating HTML reports
- `example_usage.py` - Examples and usage demonstrations
- `README.md` - This documentation file

## Notes

- Screenshots are embedded as base64-encoded images in the HTML
- The script handles missing files gracefully and shows appropriate messages
- Reports are responsive and work well on both desktop and mobile devices
- Large data sets are automatically truncated for better readability