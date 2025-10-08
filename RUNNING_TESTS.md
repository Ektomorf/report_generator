# Running PyTests in rs_ats

## Prerequisites

- Python with `debugpy` extension for VSCode debugging
- Required Python packages installed in your environment

## Project Structure

- **Test runner**: [rs_ats_sw/run_tests.py](rs_ats_sw/run_tests.py)
- **Test configurations**: `nucom_gen1/general/setups/groups/*.json`
- **Working directory**: `/mnt/devel/george/work/rs_ats` (project root)

## Environment Setup

### Required PYTHONPATH
```bash
export PYTHONPATH="${workspaceFolder}/rs_ats_sw/tests_automation:${workspaceFolder}/rs_ats_sw"
```

## Running Tests

### Command Line Usage

```bash
python rs_ats_sw/run_tests.py <test_group_file> -s <setup_name> -l <log_level> -o <output_folder>
```

### Parameters

- **test_group_file**: Path to JSON test group file (relative to `rs_ats_sw/tests_automation/`)
- **-s, --setup_name**: Name of test setup (e.g., `UK_ATS_NUCOM_LAB2`) - **REQUIRED**
- **-l, --log_level**: Logging level (default: `WARNING`, options: `DEBUG`, `INFO`, `WARNING`, `ERROR`)
- **-o, --output_folder**: Optional output directory for test reports

### Example Commands

**Basic test run:**
```bash
python rs_ats_sw/run_tests.py nucom_gen1/general/setups/groups/test_versal_commands.json -s UK_ATS_NUCOM_LAB2
```

**With logging and output:**
```bash
python rs_ats_sw/run_tests.py nucom_gen1/general/setups/groups/test_versal_commands.json \
  -s UK_ATS_NUCOM_LAB2 \
  -l INFO \
  -o report_generator/output/versal
```

## Available Test Suites

From [.vscode/launch.json](.vscode/launch.json):

| Suite Name | Test Group File | Output Directory |
|------------|----------------|------------------|
| Versal Tests | `test_versal_commands.json` | `report_generator/output/versal` |
| Screenshot and Peak Table | `screenshot_and_peak_table.json` | `report_generator/output/upconvertor_sweep` |
| Sweep LO Upconvertor | `test_upconvert_sweep.json` | `report_generator/output/upconvertor_sweep` |
| v1_1_tests_fwd | `v1_1_tests_fwd.json` | `report_generator/output/v1_1_tests_fwd` |
| v1_1_tests_rtn | `v1_1_tests_rtn.json` | `report_generator/output/v1_1_tests_rtn` |
| RF Matrix Timeout | `rf_matrix_timeout.json` | *(none)* |
| RF Matrix TCP | `rf_matrix_tcp_suite.json` | *(none)* |
| ATMega normalMode | `atmega_group_normal_mode.json` | `report_generator/output/atmega_normal_mode` |
| ATMega Cyclic Commands | `atmega_group_cyclic_commands.json` | `report_generator/output/atmega_cyclic_commands` |
| ATMega serviceMode | `atmega_group_normal_mode.json` | `report_generator/output/atmega_service_mode` |
| GPP 4323 Power Supply | `gp4323_suite.json` | *(none)* |

## VSCode Debugging

All configurations use `debugpy` for interactive debugging. To debug:

1. Open [.vscode/launch.json](.vscode/launch.json)
2. Select desired configuration from debug dropdown
3. Press F5 or click "Start Debugging"

Breakpoints and variable inspection work as expected during debug sessions.

## Environment Variables (Alternative)

Instead of command-line arguments, you can set:

```bash
export TEST_LIST_FILE="nucom_gen1/general/setups/groups/test_versal_commands.json"
export SETUP_NAME="UK_ATS_NUCOM_LAB2"
python rs_ats_sw/run_tests.py
```

## Report Generator

### Overview

The report generator automates the process of running all test suites sequentially and generating consolidated HTML reports with test results and diagnostic information.

### How It Works

1. **Test Execution**: Run test suites with specified parameters (test group file, setup name, output directory)
2. **Report Generation**: [generate_report.py](generate_report.py) processes the test output:
   - Scans the output directory for test results
   - Converts CSV test results to HTML tables
   - Extracts test parameters from JSON files
   - Creates combined analyzer reports with embedded diagnostics
   - Generates an index page linking all test results
3. **Index Creation**: A master [index.html](output/index.html) provides navigation to all test reports

### Usage

**Generate reports from test output:**
```batch
python generate_report.py
```

**Process CSV files (alternative workflow):**
```batch
process_all.bat
```

### Output Structure

```
report_generator/output/
├── index.html                          # Master index of all test runs
├── <test_suite>_<timestamp>/           # Individual test run directory
│   ├── test_<module>__<test_name>/     # Per-test results
│   │   ├── *_combined_analyzer*.html   # Main test report with diagnostics
│   │   ├── *.csv                       # Raw test data
│   │   └── *.json                      # Test parameters
│   └── ...
└── ...
```

### Key Features

- **Automated sequential execution** of all test suites
- **HTML reports** with sortable, filterable tables
- **Test parameter extraction** from JSON configuration
- **Failure message export** to CSV for analysis
- **Clickable file links** in the index for easy navigation
- **Timestamp-based organization** to preserve test history
