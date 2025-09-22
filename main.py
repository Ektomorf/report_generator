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

    return parser


def main() -> int:
    """Main entry point"""
    parser = create_argument_parser()
    args = parser.parse_args()

    input_dir = args.input_dir.resolve()
    output_dir = args.output_dir.resolve() if args.output_dir else input_dir

    try:
        report_service = ReportService()
        generate_pdf = not args.no_pdf
        report_service.generate_reports(input_dir, output_dir, generate_pdf)
        return 0
    except Exception as e:
        print(f"Error: {str(e)}")
        return 1


if __name__ == '__main__':
    exit(main())