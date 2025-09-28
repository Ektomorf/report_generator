#!/usr/bin/env python3
"""
Main entry point for the CSV analyzer application
"""

import sys
from pathlib import Path

from analyzer import CSVAnalyzer


def main():
    """Main function to process CSV files"""
    if len(sys.argv) < 2:
        print("Usage: python main.py <csv_file> [output_html]")
        print("   or: python main.py --batch <directory>")
        sys.exit(1)

    analyzer = CSVAnalyzer()

    if sys.argv[1] == '--batch':
        # Batch process all combined CSV files
        if len(sys.argv) < 3:
            print("Usage: python main.py --batch <directory>")
            sys.exit(1)

        batch_directory = sys.argv[2]
        analyzer.process_batch(batch_directory)
    else:
        # Single file processing
        csv_file = sys.argv[1]
        output_html = sys.argv[2] if len(sys.argv) > 2 else None

        analyzer.process_single_file(csv_file, output_html)


if __name__ == "__main__":
    main()