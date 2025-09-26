#!/usr/bin/env python3
"""
Batch Log Viewer - Process all log files in a directory structure.
Finds all .log files recursively and converts them to CSV + HTML viewers.
"""

import os
import sys
import argparse
import time
from pathlib import Path
from typing import List, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

# Import from the main log_viewer module
from log_viewer import convert_log_to_csv, generate_html_viewer

class BatchProcessor:
    def __init__(self, base_dir: Path, max_workers: int = 4):
        self.base_dir = base_dir
        self.max_workers = max_workers
        self.stats = {
            'total_files': 0,
            'processed': 0,
            'errors': 0,
            'skipped': 0
        }
        self.lock = threading.Lock()

    def find_log_files(self) -> List[Path]:
        """Recursively find all .log files in the directory structure."""
        log_files = []
        print(f"Scanning for log files in: {self.base_dir}")

        for root, dirs, files in os.walk(self.base_dir):
            for file in files:
                if file.endswith('.log'):
                    log_path = Path(root) / file
                    log_files.append(log_path)

        print(f"Found {len(log_files)} log files")
        return log_files

    def process_single_file(self, log_file: Path) -> Tuple[bool, str, Path]:
        """Process a single log file. Returns (success, message, log_file)."""
        try:
            # Generate output filenames
            base_name = log_file.stem
            output_dir = log_file.parent
            csv_file = output_dir / f"{base_name}.csv"
            html_file = output_dir / f"{base_name}_viewer.html"

            # Skip if outputs already exist and are newer than source
            # if (csv_file.exists() and html_file.exists() and
            #     csv_file.stat().st_mtime > log_file.stat().st_mtime and
            #     html_file.stat().st_mtime > log_file.stat().st_mtime):
            #     return True, "Skipped (up to date)", log_file

            # Convert log to CSV
            columns = convert_log_to_csv(log_file, csv_file)

            # Generate HTML viewer
            generate_html_viewer(csv_file, html_file, columns)

            return True, f"Processed ({len(columns)} columns)", log_file

        except Exception as e:
            return False, f"Error: {str(e)}", log_file

    def update_progress(self, success: bool, message: str, log_file: Path):
        """Thread-safe progress update."""
        with self.lock:
            if success:
                if "Skipped" in message:
                    self.stats['skipped'] += 1
                else:
                    self.stats['processed'] += 1
            else:
                self.stats['errors'] += 1

            completed = self.stats['processed'] + self.stats['errors'] + self.stats['skipped']

            # Print progress
            relative_path = log_file.relative_to(self.base_dir)
            status = "OK" if success else "ERROR"
            print(f"[{completed:3d}/{self.stats['total_files']:3d}] {status} {relative_path} - {message}")

    def process_all(self, parallel: bool = True) -> dict:
        """Process all log files, optionally in parallel."""
        log_files = self.find_log_files()
        self.stats['total_files'] = len(log_files)

        if not log_files:
            print("No log files found!")
            return self.stats

        print(f"\nProcessing {len(log_files)} files {'in parallel' if parallel else 'sequentially'}...")
        print("-" * 80)

        start_time = time.time()

        if parallel and len(log_files) > 1:
            # Process in parallel
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                # Submit all tasks
                future_to_file = {
                    executor.submit(self.process_single_file, log_file): log_file
                    for log_file in log_files
                }

                # Process completed tasks
                for future in as_completed(future_to_file):
                    success, message, log_file = future.result()
                    self.update_progress(success, message, log_file)
        else:
            # Process sequentially
            for log_file in log_files:
                success, message, _ = self.process_single_file(log_file)
                self.update_progress(success, message, log_file)

        elapsed = time.time() - start_time

        print("-" * 80)
        print(f"Completed in {elapsed:.1f} seconds")
        print(f"Processed: {self.stats['processed']}")
        print(f"Skipped: {self.stats['skipped']}")
        print(f"Errors: {self.stats['errors']}")

        return self.stats

def main():
    parser = argparse.ArgumentParser(
        description='Batch process all log files in a directory structure',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process all logs in output/ folder
  python batch_log_viewer.py output/

  # Process with more parallel workers
  python batch_log_viewer.py output/ --workers 8

  # Process sequentially (no parallelism)
  python batch_log_viewer.py output/ --sequential

  # Force reprocessing of all files
  python batch_log_viewer.py output/ --force
        """
    )

    parser.add_argument('directory', help='Directory to scan for log files')
    parser.add_argument('--workers', '-w', type=int, default=4,
                       help='Number of parallel workers (default: 4)')
    parser.add_argument('--sequential', '-s', action='store_true',
                       help='Process files sequentially instead of in parallel')
    parser.add_argument('--force', '-f', action='store_true',
                       help='Force reprocessing even if outputs exist and are up to date')

    args = parser.parse_args()

    # Validate directory
    base_dir = Path(args.directory)
    if not base_dir.exists():
        print(f"Error: Directory '{base_dir}' does not exist")
        return 1

    if not base_dir.is_dir():
        print(f"Error: '{base_dir}' is not a directory")
        return 1

    # Create processor
    processor = BatchProcessor(base_dir, max_workers=args.workers)

    # Temporarily modify the process_single_file method if force is enabled
    if args.force:
        original_process = processor.process_single_file
        def force_process(log_file):
            try:
                base_name = log_file.stem
                output_dir = log_file.parent
                csv_file = output_dir / f"{base_name}.csv"
                html_file = output_dir / f"{base_name}_viewer.html"

                columns = convert_log_to_csv(log_file, csv_file)
                generate_html_viewer(csv_file, html_file, columns)

                return True, f"Processed ({len(columns)} columns)", log_file
            except Exception as e:
                return False, f"Error: {str(e)}", log_file

        processor.process_single_file = force_process

    # Process all files
    try:
        stats = processor.process_all(parallel=not args.sequential)

        if stats['errors'] > 0:
            print(f"\nWarning: {stats['errors']} files had errors")
            return 1
        else:
            print(f"\nSuccess: All files processed successfully!")
            return 0

    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        return 1
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        return 1

if __name__ == '__main__':
    exit(main())