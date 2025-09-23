#!/usr/bin/env python3
"""
Example demonstrating how to configure columns in test reports.
"""

from pathlib import Path
from services.report_service import ReportService
from config import ColumnConfigManager, ColumnDefinition, ColumnType


def example_basic_column_configuration():
    """Example of basic column configuration"""

    # Create a report service
    report_service = ReportService()

    # Example 1: Hide specific columns
    columns_to_hide = [
        'spectrum_frequencies',
        'spectrum_amplitudes',
        'raw_socan_response',
        'raw_rf_matrix_response'
    ]
    report_service.hide_columns(columns_to_hide)

    # Example 2: Show only specific columns
    essential_columns = [
        'Timestamp',
        'channel',
        'frequency',
        'enabled',
        'peak_frequency',
        'peak_amplitude',
        'screenshot_filepath'
    ]
    report_service.configure_columns(visible_columns=essential_columns)

    # Example 3: Set custom column order
    custom_order = [
        'Timestamp',
        'channel',
        'frequency',
        'peak_frequency',
        'peak_amplitude',
        'enabled',
        'gain',
        'screenshot_filepath',
        'socan_command',
        'parsed_socan_response'
    ]
    report_service.configure_columns(column_order=custom_order)

    print("Basic configuration applied:")
    print(f"Visible columns: {report_service.get_visible_columns()}")
    print(f"Available columns: {report_service.get_available_columns()}")


def example_advanced_column_configuration():
    """Example of advanced column configuration with custom columns"""

    # Create custom column configuration manager
    column_config = ColumnConfigManager()

    # Add a custom column definition
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

    # Configure for RF testing focus
    rf_focused_columns = [
        'Timestamp',
        'channel',
        'frequency',
        'peak_frequency',
        'peak_amplitude',
        'rf_matrix_command_method',
        'rf_matrix_command_args',
        'parsed_rf_matrix_response',
        'screenshot_filepath'
    ]

    rf_column_order = [
        'Timestamp',
        'channel',
        'frequency',
        'rf_matrix_command_method',
        'rf_matrix_command_args',
        'peak_frequency',
        'peak_amplitude',
        'parsed_rf_matrix_response',
        'screenshot_filepath'
    ]

    report_service.configure_columns(
        visible_columns=rf_focused_columns,
        column_order=rf_column_order
    )

    print("\nAdvanced RF-focused configuration applied:")
    print(f"Visible columns: {report_service.get_visible_columns()}")


def example_different_test_configurations():
    """Example showing different configurations for different test types"""

    configurations = {
        'minimal': [
            'Timestamp', 'channel', 'frequency', 'enabled', 'screenshot_filepath'
        ],

        'frequency_analysis': [
            'Timestamp', 'channel', 'frequency', 'peak_frequency',
            'peak_amplitude', 'spectrum_frequencies', 'spectrum_amplitudes',
            'screenshot_filepath'
        ],

        'command_debugging': [
            'Timestamp', 'channel', 'socan_command_method', 'socan_command_args',
            'socan_command', 'parsed_socan_response', 'raw_socan_response',
            'rf_matrix_command_method', 'rf_matrix_command_args', 'rf_matrix_command',
            'parsed_rf_matrix_response', 'raw_rf_matrix_response'
        ],

        'full_overview': [
            'Timestamp', 'channel', 'frequency', 'enabled', 'gain',
            'peak_frequency', 'peak_amplitude', 'socan_command',
            'parsed_socan_response', 'rf_matrix_command', 'parsed_rf_matrix_response',
            'screenshot_filepath'
        ]
    }

    print("\nPredefined configurations:")
    for config_name, columns in configurations.items():
        print(f"\n{config_name.upper()} configuration:")
        print(f"Columns: {', '.join(columns)}")


def apply_configuration_and_generate_reports(config_name: str = 'full_overview'):
    """Apply a specific configuration and generate reports"""

    # Configuration presets
    configurations = {
        'minimal': {
            'visible_columns': [
                'Timestamp', 'channel', 'frequency', 'enabled', 'screenshot_filepath'
            ],
            'column_order': [
                'Timestamp', 'channel', 'frequency', 'enabled', 'screenshot_filepath'
            ]
        },

        'frequency_analysis': {
            'visible_columns': [
                'Timestamp', 'channel', 'frequency', 'peak_frequency',
                'peak_amplitude', 'screenshot_filepath'
            ],
            'column_order': [
                'Timestamp', 'channel', 'frequency', 'peak_frequency',
                'peak_amplitude', 'screenshot_filepath'
            ]
        },

        'full_overview': {
            'visible_columns': [
                'Timestamp', 'channel', 'frequency', 'enabled', 'gain',
                'peak_frequency', 'peak_amplitude', 'socan_command',
                'parsed_socan_response', 'rf_matrix_command', 'parsed_rf_matrix_response',
                'screenshot_filepath'
            ],
            'column_order': [
                'Timestamp', 'channel', 'frequency', 'enabled', 'gain',
                'peak_frequency', 'peak_amplitude', 'socan_command',
                'parsed_socan_response', 'rf_matrix_command', 'parsed_rf_matrix_response',
                'screenshot_filepath'
            ]
        }
    }

    if config_name not in configurations:
        print(f"Unknown configuration: {config_name}")
        print(f"Available configurations: {list(configurations.keys())}")
        return

    # Create report service and apply configuration
    report_service = ReportService()
    config = configurations[config_name]

    report_service.configure_columns(
        visible_columns=config['visible_columns'],
        column_order=config['column_order']
    )

    print(f"\nApplied {config_name} configuration")
    print(f"Visible columns: {report_service.get_visible_columns()}")

    # Now you can generate reports with this configuration
    # input_dir = Path('output')  # Your input directory
    # output_dir = Path('processed_results')  # Your output directory
    # report_service.generate_reports(input_dir, output_dir)

    return report_service


if __name__ == '__main__':
    print("Column Configuration Examples")
    print("=" * 50)

    example_basic_column_configuration()
    example_advanced_column_configuration()
    example_different_test_configurations()

    # Demonstrate applying a configuration
    print("\n" + "=" * 50)
    print("Applying 'frequency_analysis' configuration:")
    service = apply_configuration_and_generate_reports('frequency_analysis')