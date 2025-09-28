#!/usr/bin/env python3
"""
Main analyzer class that coordinates all components
"""

import os
import sys
from pathlib import Path
from typing import Optional

from models import AnalyzerData
from csv_loader import CSVLoader
from data_processor import DataProcessor
from html_generator import HTMLGenerator


class CSVAnalyzer:
    """Main analyzer class that orchestrates CSV loading, processing, and HTML generation"""

    def __init__(self):
        self.data: Optional[AnalyzerData] = None
        self.loader = CSVLoader()
        self.processor: Optional[DataProcessor] = None
        self.html_generator: Optional[HTMLGenerator] = None

    def load_csv(self, csv_path: str) -> None:
        """Load CSV data using the CSV loader"""
        self.data = self.loader.load_csv(csv_path)
        self.processor = DataProcessor(self.data)
        self.html_generator = HTMLGenerator(self.data, self.processor)

    def generate_html(self, output_path: str, title: str = None) -> None:
        """Generate interactive HTML analyzer"""
        if not self.html_generator:
            raise ValueError("No data loaded. Call load_csv() first.")

        self.html_generator.generate_html(output_path, title)

    def process_single_file(self, csv_file: str, output_html: str = None) -> None:
        """Process a single CSV file and generate HTML output"""
        if not os.path.exists(csv_file):
            print(f"Error: CSV file not found: {csv_file}")
            sys.exit(1)

        if not output_html:
            output_html = str(Path(csv_file).with_suffix('.html'))

        try:
            self.load_csv(csv_file)

            # Generate title from path
            csv_path = Path(csv_file)
            title = f"Test Analysis - {csv_path.parent.name} - {csv_path.stem}"

            self.generate_html(output_html, title)
            print(f"Generated: {output_html}")

        except Exception as e:
            print(f"Error processing {csv_file}: {e}")
            import traceback
            traceback.print_exc()

    def process_batch(self, directory: str) -> None:
        """Process all *combined.csv files in directory recursively"""
        base_path = Path(directory)
        if not base_path.exists():
            print(f"Error: Directory not found: {directory}")
            sys.exit(1)

        # Find all combined CSV files
        csv_files = list(base_path.rglob("*combined.csv"))

        if not csv_files:
            print(f"No *combined.csv files found in {directory}")
            return

        print(f"Found {len(csv_files)} combined CSV files")

        for csv_file in csv_files:
            try:
                # Generate HTML in same directory as CSV
                output_html = csv_file.with_name(f"{csv_file.stem}_analyzer.html")

                self.load_csv(str(csv_file))

                # Generate title from path structure
                parts = csv_file.parts
                if len(parts) >= 2:
                    title = f"Test Analysis - {parts[-2]} - {csv_file.stem}"
                else:
                    title = f"Test Analysis - {csv_file.stem}"

                self.generate_html(str(output_html), title)
                print(f"Generated: {output_html}")

            except Exception as e:
                print(f"Error processing {csv_file}: {e}")
                continue

        print(f"\nBatch processing complete!")

    def get_data_statistics(self) -> dict:
        """Get statistics about the loaded data"""
        if not self.data or not self.processor:
            return {}

        filtered_rows = self.processor.filter_data()
        return self.processor.get_statistics(filtered_rows)

    def get_column_info(self) -> dict:
        """Get information about columns"""
        if not self.data:
            return {}

        return {
            'columns': self.data.get_column_names(),
            'visible_columns': self.data.get_visible_columns(),
            'column_groups': self.processor.get_column_groups() if self.processor else {}
        }