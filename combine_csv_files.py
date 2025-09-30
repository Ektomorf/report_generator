#!/usr/bin/env python3
"""
Combine results and logs CSV files based on timestamp.
Merges CSV files from process_result_csv.py and process_log_csv.py using timestamp as index.
"""

import pandas as pd
import os
import glob
import argparse
from pathlib import Path
import logging
from datetime import datetime

def setup_logging(verbose=False):
    """Setup logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

def find_csv_pairs(root_dir, pattern="**/*"):
    """
    Find pairs of _results.csv and _logs.csv files.
    
    Args:
        root_dir: Root directory to search in
        pattern: Glob pattern for searching
        
    Returns:
        List of tuples (results_csv_path, logs_csv_path, base_name)
    """
    pairs = []
    results_pattern = os.path.join(root_dir, pattern + "_results.csv")
    results_files = glob.glob(results_pattern, recursive=True)
    
    for results_file in results_files:
        # Derive the corresponding logs file path
        base_name = results_file.replace("_results.csv", "")
        logs_file = base_name + "_logs.csv"
        
        if os.path.exists(logs_file):
            pairs.append((results_file, logs_file, base_name))
            logging.info(f"Found pair: {os.path.basename(results_file)} + {os.path.basename(logs_file)}")
        else:
            logging.warning(f"No corresponding logs file found for {results_file}")
    
    return pairs

def combine_csv_files(results_csv, logs_csv, output_csv):
    """
    Combine results and logs CSV files using timestamp as index.
    
    Args:
        results_csv: Path to results CSV file
        logs_csv: Path to logs CSV file
        output_csv: Path for output combined CSV file
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Read CSV files
        logging.debug(f"Reading results CSV: {results_csv}")
        results_df = pd.read_csv(results_csv)
        
        logging.debug(f"Reading logs CSV: {logs_csv}")
        logs_df = pd.read_csv(logs_csv)
        
        # Check if timestamp columns exist
        if 'timestamp' not in results_df.columns:
            logging.error(f"No 'timestamp' column found in results CSV: {results_csv}")
            return False
            
        if 'timestamp' not in logs_df.columns:
            logging.error(f"No 'timestamp' column found in logs CSV: {logs_csv}")
            return False
        
        # Remove rows where timestamp is NaN or empty
        results_df = results_df.dropna(subset=['timestamp'])
        logs_df = logs_df.dropna(subset=['timestamp'])
        
        if results_df.empty:
            logging.warning(f"No valid timestamp data in results CSV: {results_csv}")
            return False
            
        if logs_df.empty:
            logging.warning(f"No valid timestamp data in logs CSV: {logs_csv}")
            return False
        
        # Convert timestamp to integer (Unix ms) if it's not already
        try:
            results_df['timestamp'] = pd.to_numeric(results_df['timestamp'], errors='coerce').astype('Int64')
            logs_df['timestamp'] = pd.to_numeric(logs_df['timestamp'], errors='coerce').astype('Int64')
        except Exception as e:
            logging.error(f"Error converting timestamps to numeric: {e}")
            return False
        
        # Remove rows where timestamp conversion failed
        results_df = results_df.dropna(subset=['timestamp'])
        logs_df = logs_df.dropna(subset=['timestamp'])
        
        logging.info(f"Results data: {len(results_df)} rows with valid timestamps")
        logging.info(f"Logs data: {len(logs_df)} rows with valid timestamps")
        
        # Handle column name conflicts by adding suffixes first
        common_columns = set(results_df.columns).intersection(set(logs_df.columns))
        common_columns.discard('timestamp')  # Don't suffix the timestamp column
        
        if common_columns:
            logging.info(f"Found {len(common_columns)} common columns: {list(common_columns)[:5]}...")
            
            # Rename common columns to avoid conflicts
            for col in common_columns:
                results_df.rename(columns={col: f"{col}_results"}, inplace=True)
                logs_df.rename(columns={col: f"{col}_logs"}, inplace=True)
        
        # Set timestamp as index for both dataframes to handle duplicates properly
        results_df.set_index('timestamp', inplace=True)
        logs_df.set_index('timestamp', inplace=True)
        
        # Use outer join to preserve ALL rows from both dataframes
        logging.info("Merging dataframes using outer join to preserve all rows...")
        combined_df = pd.concat([results_df, logs_df], axis=0, join='outer', sort=True)
        
        # Reset index to make timestamp a column again
        combined_df.reset_index(inplace=True)
        
        # Sort by timestamp (already sorted but ensure it)
        combined_df.sort_values('timestamp', inplace=True)
        
        logging.info(f"Combined data: {len(combined_df)} rows")
        
        # Save combined CSV
        os.makedirs(os.path.dirname(output_csv), exist_ok=True)
        combined_df.to_csv(output_csv, index=False)
        logging.info(f"Saved combined CSV: {output_csv}")
        
        return True
        
    except Exception as e:
        logging.error(f"Error combining CSV files: {e}")
        return False

def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Combine results and logs CSV files based on timestamp",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s output/ --verbose
  %(prog)s output/test_dir/ --pattern "**/*test*" --output combined_output/
        """
    )
    
    parser.add_argument(
        'input_directory',
        help='Root directory to search for CSV files'
    )
    
    parser.add_argument(
        '--pattern',
        default='**/*',
        help='Glob pattern for finding CSV files (default: **/*)'
    )
    
    parser.add_argument(
        '--output',
        default=None,
        help='Output directory for combined CSV files (default: same as input with _combined suffix)'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    setup_logging(args.verbose)
    
    if not os.path.exists(args.input_directory):
        logging.error(f"Input directory does not exist: {args.input_directory}")
        return 1
    
    # Find CSV pairs
    logging.info(f"Searching for CSV pairs in: {args.input_directory}")
    pairs = find_csv_pairs(args.input_directory, args.pattern)
    
    if not pairs:
        logging.warning("No CSV pairs found!")
        return 0
    
    logging.info(f"Found {len(pairs)} CSV pairs to process")
    
    # Process each pair
    success_count = 0
    for results_csv, logs_csv, base_name in pairs:
        logging.info(f"Processing: {os.path.basename(base_name)}")
        
        # Determine output path
        if args.output:
            # Use specified output directory
            rel_path = os.path.relpath(base_name, args.input_directory)
            output_csv = os.path.join(args.output, rel_path + "_combined.csv")
        else:
            # Use same directory as input
            output_csv = base_name + "_combined.csv"
        
        # Combine the files
        if combine_csv_files(results_csv, logs_csv, output_csv):
            success_count += 1
        else:
            logging.error(f"Failed to process pair: {base_name}")
    
    logging.info(f"Successfully processed {success_count}/{len(pairs)} CSV pairs")
    
    if success_count > 0:
        logging.info("Combined CSV files have been created with _combined.csv suffix")
        logging.info("The files include all columns from both results and logs CSVs, indexed by timestamp")
    
    return 0 if success_count > 0 else 1

if __name__ == "__main__":
    exit(main())