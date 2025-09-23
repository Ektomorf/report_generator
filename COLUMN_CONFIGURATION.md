# Column Configuration Guide

The test report generator now supports configurable columns, allowing you to customize which columns are displayed in your reports and in what order they appear.

## Features

- **Column Selection**: Choose which columns to show or hide
- **Column Ordering**: Control the order in which columns appear
- **Predefined Configurations**: Use preset column configurations for common use cases
- **Custom Columns**: Add your own column definitions with custom formatting
- **Command Line Support**: Configure columns directly from the command line

## Quick Start

### Using Predefined Configurations

The easiest way to configure columns is using the predefined configurations:

```bash
# Minimal columns for basic overview
python main.py /path/to/output --column-config minimal

# Focus on frequency analysis
python main.py /path/to/output --column-config frequency_analysis

# Show command debugging information
python main.py /path/to/output --column-config command_debugging

# Full overview (default)
python main.py /path/to/output --column-config full_overview
```

### Custom Column Selection

```bash
# Show only specific columns
python main.py /path/to/output --visible-columns Timestamp channel frequency peak_frequency peak_amplitude

# Hide specific columns from the default set
python main.py /path/to/output --hide-columns raw_socan_response raw_rf_matrix_response spectrum_frequencies
```

## Predefined Configurations

### Minimal
Shows only essential information:
- Timestamp, channel, frequency, enabled, screenshot_filepath

### Frequency Analysis
Focused on frequency-related measurements:
- Timestamp, channel, frequency, peak_frequency, peak_amplitude, screenshot_filepath

### Command Debugging
Shows all command and response information:
- All SOCAN and RF Matrix commands, arguments, and responses

### Full Overview (Default)
Comprehensive view with the most important columns:
- Timestamp, channel, frequency, enabled, gain, peak_frequency, peak_amplitude, commands, responses, screenshots

## Programmatic Configuration

You can also configure columns programmatically in your Python code:

### Basic Usage

```python
from services.report_service import ReportService

# Create report service
report_service = ReportService()

# Hide specific columns
report_service.hide_columns(['raw_socan_response', 'raw_rf_matrix_response'])

# Show only essential columns
essential_columns = [
    'Timestamp', 'channel', 'frequency', 'peak_frequency',
    'peak_amplitude', 'screenshot_filepath'
]
report_service.configure_columns(visible_columns=essential_columns)

# Generate reports with this configuration
report_service.generate_reports(input_dir, output_dir)
```

### Advanced Configuration with Custom Columns

```python
from config import ColumnConfigManager, ColumnDefinition, ColumnType

# Create custom column configuration
column_config = ColumnConfigManager()

# Add a custom column
custom_column = ColumnDefinition(
    key='custom_metric',
    display_name='Custom Metric',
    column_type=ColumnType.NUMERIC,
    order=500,
    description='A custom calculated metric'
)
column_config.add_custom_column(custom_column)

# Create report service with custom configuration
report_service = ReportService(column_config)

# Configure columns
report_service.configure_columns(
    visible_columns=['Timestamp', 'channel', 'custom_metric'],
    column_order=['Timestamp', 'channel', 'custom_metric']
)
```

## Available Columns

### Basic Measurement Columns
- `Timestamp` - Test execution timestamp
- `channel` - Channel identifier
- `frequency` - Operating frequency
- `enabled` - Channel enabled status
- `gain` - Signal gain

### Frequency Analysis Columns
- `peak_frequency` - Peak frequency detected
- `peak_amplitude` - Peak amplitude measured
- `spectrum_frequencies` - Spectrum frequency data (hidden by default)
- `spectrum_amplitudes` - Spectrum amplitude data (hidden by default)
- `frequencies` - Frequency data array (hidden by default)
- `amplitudes` - Amplitude data array (hidden by default)

### SOCAN Command Columns
- `socan_command_method` - SOCAN command method
- `socan_command_args` - SOCAN command arguments
- `socan_command` - Full SOCAN command
- `parsed_socan_response` - Parsed SOCAN response
- `raw_socan_response` - Raw SOCAN response

### RF Matrix Command Columns
- `rf_matrix_command_method` - RF Matrix command method
- `rf_matrix_command_args` - RF Matrix command arguments
- `rf_matrix_command` - Full RF Matrix command
- `parsed_rf_matrix_response` - Parsed RF Matrix response
- `raw_rf_matrix_response` - Raw RF Matrix response

### Keysight XSAN Command Columns
- `keysight_xsan_command_method` - Keysight XSAN command method
- `keysight_xsan_command_args` - Keysight XSAN command arguments
- `keysight_xsan_command` - Full Keysight XSAN command

### Other Columns
- `screenshot_filepath` - Link to screenshot

## Column Types and Formatting

Columns are automatically formatted based on their type:

- **TEXT**: Standard text formatting
- **NUMERIC**: Right-aligned with monospace font
- **FREQUENCY**: Formatted as GHz with appropriate precision
- **AMPLITUDE**: Formatted as dBm with appropriate precision
- **COMMAND**: Monospace font, smaller text
- **RESPONSE**: Monospace font, smaller text, limited width
- **PARSED_RESPONSE**: Monospace font, larger width for structured data
- **SCREENSHOT**: Formatted as clickable link

## Examples

See the `examples/column_configuration_example.py` file for complete working examples of:

- Basic column configuration
- Advanced configuration with custom columns
- Different configurations for different test types
- Applying configurations and generating reports

## API Reference

### ReportService Methods

- `configure_columns(visible_columns=None, column_order=None)` - Set visible columns and order
- `hide_columns(column_keys)` - Hide specific columns
- `show_columns(column_keys)` - Show specific columns
- `get_available_columns()` - Get list of all available columns
- `get_visible_columns()` - Get list of currently visible columns

### ColumnConfigManager Methods

- `get_column_definition(key)` - Get column definition for a key
- `add_custom_column(column_def)` - Add a custom column definition
- `set_visible_columns(column_keys)` - Set which columns are visible
- `set_column_order(ordered_keys)` - Set the order of columns
- `hide_column(key)` / `show_column(key)` - Hide/show individual columns

This configuration system gives you complete control over how your test data is presented in the generated reports.