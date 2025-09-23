#!/usr/bin/env python3
"""
Main service for orchestrating report generation.
"""

import os
from pathlib import Path
from typing import List

from models import TestResult, SetupReport
from parsers import TestResultParser, SetupReportParser
from generators import HTMLReportGenerator, IndexGenerator, PDFReportGenerator, PDFIndexGenerator
from config import ColumnConfigManager


class ReportService:
    """Main service for generating test reports"""

    def __init__(self, column_config: ColumnConfigManager = None):
        self.column_config = column_config or ColumnConfigManager()
        self.html_generator = HTMLReportGenerator(self.column_config)
        self.index_generator = IndexGenerator()
        self.pdf_generator = PDFReportGenerator()
        self.pdf_index_generator = PDFIndexGenerator()

    def configure_columns(self, visible_columns: List[str] = None, column_order: List[str] = None) -> None:
        """Configure which columns to display and in what order"""
        if visible_columns is not None:
            self.column_config.set_visible_columns(visible_columns)
        if column_order is not None:
            self.column_config.set_column_order(column_order)

    def hide_columns(self, column_keys: List[str]) -> None:
        """Hide specific columns"""
        for key in column_keys:
            self.column_config.hide_column(key)

    def show_columns(self, column_keys: List[str]) -> None:
        """Show specific columns"""
        for key in column_keys:
            self.column_config.show_column(key)

    def get_available_columns(self) -> List[str]:
        """Get list of all available column definitions"""
        return [col.key for col in self.column_config.get_all_available_columns()]

    def get_visible_columns(self) -> List[str]:
        """Get list of currently visible columns"""
        return self.column_config.get_visible_columns()

    def generate_reports(self, input_dir: Path, output_dir: Path, generate_pdf: bool = True) -> None:
        """Generate all reports for the given input directory"""
        if not input_dir.exists():
            raise FileNotFoundError(f"Input directory {input_dir} does not exist")

        output_dir.mkdir(parents=True, exist_ok=True)

        result_folders, setup_folders = self._find_folders(input_dir)

        if not result_folders and not setup_folders:
            print(f"No result folders found in {input_dir}")
            return

        print(f"Found {len(result_folders)} result folders and {len(setup_folders)} setup folders")

        generated_reports = self._process_result_folders(result_folders, input_dir, output_dir, generate_pdf)
        setup_data = self._process_setup_folders(setup_folders)

        self._generate_index_page(generated_reports, output_dir, input_dir.name, setup_data, generate_pdf)

        report_count = len([r for r in generated_reports if r.suffix == '.html'])
        pdf_count = len([r for r in generated_reports if r.suffix == '.pdf'])

        print(f"\nGenerated {report_count} HTML reports" + (f" and {pdf_count} PDF reports" if generate_pdf else "") + f" in {output_dir}")
        print(f"Open {output_dir / 'index.html'} to view all reports")

    def _find_folders(self, input_dir: Path) -> tuple:
        """Find all valid result and setup folders"""
        result_folders = []
        setup_folders = []

        for root, dirs, files in os.walk(input_dir):
            folder_path = Path(root)
            if any(f.endswith('_results.json') for f in files):
                result_folders.append(folder_path)
            elif 'report.json' in files:
                setup_folders.append(folder_path)

        return result_folders, setup_folders

    def _process_result_folders(self, result_folders: List[Path],
                               input_dir: Path, output_dir: Path, generate_pdf: bool = True) -> List[Path]:
        """Process all result folders and generate HTML and PDF reports"""
        generated_reports = []

        for result_folder in sorted(result_folders):
            print(f"Processing {result_folder.name}...")

            try:
                parser = TestResultParser(result_folder)
                test_result = parser.parse()

                test_run_name = (result_folder.parent.name
                               if result_folder.parent != input_dir
                               else result_folder.name)
                test_run_output_dir = output_dir / test_run_name
                test_run_output_dir.mkdir(parents=True, exist_ok=True)

                # Generate HTML report
                html_output_file = test_run_output_dir / f"{result_folder.name}_report.html"
                self.html_generator.generate_report(test_result, html_output_file)
                generated_reports.append(html_output_file)

                # Generate PDF report if requested
                if generate_pdf:
                    pdf_output_file = test_run_output_dir / f"{result_folder.name}_report.pdf"
                    self.pdf_generator.generate_report(test_result, pdf_output_file)
                    generated_reports.append(pdf_output_file)

            except Exception as e:
                print(f"Error processing {result_folder.name}: {str(e)}")

        return generated_reports

    def _process_setup_folders(self, setup_folders: List[Path]) -> List[SetupReport]:
        """Process all setup folders and extract data"""
        setup_data = []

        for setup_folder in sorted(setup_folders):
            print(f"Processing setup {setup_folder.name}...")

            try:
                parser = SetupReportParser(setup_folder)
                setup_report = parser.parse()
                setup_data.append(setup_report)
            except Exception as e:
                print(f"Error processing setup {setup_folder.name}: {str(e)}")

        return setup_data

    def _generate_index_page(self, report_files: List[Path], output_dir: Path,
                           test_session: str, setup_data: List[SetupReport], generate_pdf: bool = True) -> None:
        """Generate the index pages"""
        # Generate HTML index
        html_index_file = output_dir / "index.html"
        html_reports = [f for f in report_files if f.suffix == '.html']
        self.index_generator.generate_index(html_reports, html_index_file, test_session, setup_data)

        # Generate PDF index if requested
        if generate_pdf:
            pdf_index_file = output_dir / "index.pdf"
            pdf_reports = [f for f in report_files if f.suffix == '.pdf']
            self.pdf_index_generator.generate_index(pdf_reports, pdf_index_file, test_session, setup_data)