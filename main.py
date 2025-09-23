#!/usr/bin/env python3
"""
Main entry point for the test report generator.
"""

import argparse
from pathlib import Path

from services.report_service import ReportService


def create_argument_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser"""
    parser = argparse.ArgumentParser(
        description='Generate HTML reports from RS ATS test results',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate reports for a specific test results folder
  python main.py /path/to/output/setups_180925_091733

  # Generate reports with custom output directory
  python main.py /path/to/output/setups_180925_091733 --output-dir ./reports

  # Generate reports with minimal columns only
  python main.py /path/to/output --column-config minimal

  # Generate reports showing only specific columns
  python main.py /path/to/output --visible-columns Timestamp channel frequency peak_frequency peak_amplitude

  # Generate reports hiding certain columns
  python main.py /path/to/output --hide-columns raw_socan_response raw_rf_matrix_response spectrum_frequencies

  # Use frequency analysis preset
  python main.py /path/to/output --column-config frequency_analysis
        """
    )

    parser.add_argument(
        'input_dir',
        type=Path,
        nargs='?',
        default=Path('output'),
        help='Input directory containing test result folders (default: output)'
    )

    parser.add_argument(
        '--output-dir', '-o',
        type=Path,
        default='processed_results',
        required=False,
        help='Output directory for HTML reports (default: processed_results)'
    )

    parser.add_argument(
        '--no-pdf',
        action='store_true',
        help='Skip PDF generation (generate HTML only)'
    )

    parser.add_argument(
        '--column-config',
        choices=['minimal', 'frequency_analysis', 'command_debugging', 'full_overview'],
        default='full_overview',
        help='Predefined column configuration (default: full_overview)'
    )

    parser.add_argument(
        '--visible-columns',
        nargs='*',
        help='Specify which columns to show (space-separated list)'
    )

    parser.add_argument(
        '--hide-columns',
        nargs='*',
        help='Specify which columns to hide (space-separated list)'
    )

    return parser


def apply_column_configuration(report_service, args):
    """Apply column configuration based on command line arguments"""

    # Predefined configurations
    configurations = {
        'minimal': {
            'visible_columns': [
                'Timestamp', 'channel', 'frequency', 'enabled', 'screenshot_filepath'
            ]
        },
        'frequency_analysis': {
            'visible_columns': [
                'Timestamp', 'channel', 'frequency', 'peak_frequency',
                'peak_amplitude', 'screenshot_filepath'
            ]
        },
        'command_debugging': {
            'visible_columns': [
                'Timestamp', 'channel', 'socan_command_method', 'socan_command_args',
                'socan_command', 'parsed_socan_response', 'raw_socan_response',
                'rf_matrix_command_method', 'rf_matrix_command_args', 'rf_matrix_command',
                'parsed_rf_matrix_response', 'raw_rf_matrix_response'
            ]
        },
        'full_overview': {
            'visible_columns': [
                'Timestamp', 'channel', 'frequency', 'enabled', 'gain',
                'peak_frequency', 'peak_amplitude', 'socan_command',
                'parsed_socan_response', 'rf_matrix_command', 'parsed_rf_matrix_response',
                'screenshot_filepath'
            ]
        }
    }

    # Apply predefined configuration
    if args.column_config in configurations:
        config = configurations[args.column_config]
        report_service.configure_columns(visible_columns=config['visible_columns'])
        print(f"Applied '{args.column_config}' column configuration")

    # Apply custom visible columns if specified
    if args.visible_columns:
        report_service.configure_columns(visible_columns=args.visible_columns)
        print(f"Set visible columns: {args.visible_columns}")

    # Hide specific columns if specified
    if args.hide_columns:
        report_service.hide_columns(args.hide_columns)
        print(f"Hidden columns: {args.hide_columns}")


def main() -> int:
    """Main entry point"""
    parser = create_argument_parser()
    args = parser.parse_args()

    input_dir = args.input_dir.resolve()
    output_dir = args.output_dir.resolve() if args.output_dir else input_dir

    try:
        report_service = ReportService()

        # Apply column configuration
        apply_column_configuration(report_service, args)

        generate_pdf = not args.no_pdf
        report_service.generate_reports(input_dir, output_dir, generate_pdf)
        return 0
    except Exception as e:
        print(f"Error: {str(e)}")
        return 1


if __name__ == '__main__':
    exit(main())