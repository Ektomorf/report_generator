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

def find_csv_sets(root_dir, pattern="**/*"):
    """
    Find sets of _results.csv, _logs.csv, and journalctl_logs.csv files.
    
    Args:
        root_dir: Root directory to search in
        pattern: Glob pattern for searching
        
    Returns:
        List of tuples (results_csv_path, logs_csv_path, journalctl_logs_path, base_name)
        where any of the CSV paths can be None if the file doesn't exist
    """
    sets = []
    results_pattern = os.path.join(root_dir, pattern + "_results.csv")
    results_files = glob.glob(results_pattern, recursive=True)
    
    for results_file in results_files:
        # Derive the corresponding logs file paths
        base_name = results_file.replace("_results.csv", "")
        logs_file = base_name + "_logs.csv"
        
        # Look for journalctl_logs.csv in the campaign directory (system_status folder)
        results_dir = os.path.dirname(results_file)
        # Go up to campaign level and look for system_status/journalctl_logs.csv
        campaign_dir = os.path.dirname(results_dir)
        journalctl_logs_file = os.path.join(campaign_dir, "system_status", "journalctl_logs.csv")
        
        # Check which files exist
        logs_exists = os.path.exists(logs_file)
        journalctl_exists = os.path.exists(journalctl_logs_file)
        
        if logs_exists or journalctl_exists:
            file_list = []
            if logs_exists:
                file_list.append(f"{os.path.basename(logs_file)}")
            if journalctl_exists:
                file_list.append("journalctl_logs.csv")
            
            sets.append((
                results_file,
                logs_file if logs_exists else None,
                journalctl_logs_file if journalctl_exists else None,
                base_name
            ))
            logging.info(f"Found set: {os.path.basename(results_file)} + {' + '.join(file_list)}")
        else:
            logging.warning(f"No corresponding logs files found for {results_file}")
    
    return sets

def combine_csv_files(results_csv, logs_csv, journalctl_csv, output_csv):
    """
    Combine results, logs, and journalctl CSV files using timestamp as index.
    
    Args:
        results_csv: Path to results CSV file
        logs_csv: Path to logs CSV file (can be None)
        journalctl_csv: Path to journalctl logs CSV file (can be None)
        output_csv: Path for output combined CSV file
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        dataframes = []
        
        # Read results CSV (required)
        logging.debug(f"Reading results CSV: {results_csv}")
        results_df = pd.read_csv(results_csv)
        
        if 'timestamp' not in results_df.columns:
            logging.error(f"No 'timestamp' column found in results CSV: {results_csv}")
            return False
            
        results_df = results_df.dropna(subset=['timestamp'])
        if results_df.empty:
            logging.warning(f"No valid timestamp data in results CSV: {results_csv}")
            return False
        
        # Convert timestamp to numeric
        try:
            results_df['timestamp'] = pd.to_numeric(results_df['timestamp'], errors='coerce')
            results_df = results_df.dropna(subset=['timestamp'])
        except Exception as e:
            logging.error(f"Error converting timestamps to numeric in results: {e}")
            return False
        
        dataframes.append(('results', results_df))
        logging.info(f"Results data: {len(results_df)} rows with valid timestamps")
        
        # Read logs CSV (optional)
        if logs_csv and os.path.exists(logs_csv):
            logging.debug(f"Reading logs CSV: {logs_csv}")
            logs_df = pd.read_csv(logs_csv)
            
            if 'timestamp' in logs_df.columns:
                logs_df = logs_df.dropna(subset=['timestamp'])
                if not logs_df.empty:
                    try:
                        logs_df['timestamp'] = pd.to_numeric(logs_df['timestamp'], errors='coerce')
                        logs_df = logs_df.dropna(subset=['timestamp'])
                        dataframes.append(('logs', logs_df))
                        logging.info(f"Logs data: {len(logs_df)} rows with valid timestamps")
                    except Exception as e:
                        logging.error(f"Error converting timestamps to numeric in logs: {e}")
            else:
                logging.warning(f"No 'timestamp' column found in logs CSV: {logs_csv}")
        
        # Read journalctl CSV (optional)  
        if journalctl_csv and os.path.exists(journalctl_csv):
            logging.debug(f"Reading journalctl CSV: {journalctl_csv}")
            journalctl_df = pd.read_csv(journalctl_csv)
            
            if 'timestamp' in journalctl_df.columns:
                journalctl_df = journalctl_df.dropna(subset=['timestamp'])
                if not journalctl_df.empty:
                    try:
                        journalctl_df['timestamp'] = pd.to_numeric(journalctl_df['timestamp'], errors='coerce')
                        journalctl_df = journalctl_df.dropna(subset=['timestamp'])
                        dataframes.append(('journalctl', journalctl_df))
                        logging.info(f"Journalctl data: {len(journalctl_df)} rows with valid timestamps")
                    except Exception as e:
                        logging.error(f"Error converting timestamps to numeric in journalctl: {e}")
            else:
                logging.warning(f"No 'timestamp' column found in journalctl CSV: {journalctl_csv}")
        
        if len(dataframes) == 0:
            logging.error("No valid dataframes to combine")
            return False
        
        # Handle column name conflicts by adding suffixes
        all_columns = set()
        for _, df in dataframes:
            all_columns.update(df.columns)
        all_columns.discard('timestamp')
        
        # Find common columns across dataframes
        common_columns = set(dataframes[0][1].columns)
        for _, df in dataframes[1:]:
            common_columns = common_columns.intersection(set(df.columns))
        common_columns.discard('timestamp')
        
        if common_columns:
            logging.info(f"Found {len(common_columns)} common columns: {list(common_columns)[:5]}...")
        
        # Rename columns to avoid conflicts and set index
        processed_dfs = []
        for suffix, df in dataframes:
            df_copy = df.copy()
            
            # Rename common columns (except timestamp)
            for col in common_columns:
                if col in df_copy.columns:
                    df_copy.rename(columns={col: f"{col}_{suffix}"}, inplace=True)
            
            df_copy.set_index('timestamp', inplace=True)
            processed_dfs.append(df_copy)
        
        # Combine all dataframes
        logging.info(f"Merging {len(processed_dfs)} dataframes using outer join to preserve all rows...")
        combined_df = pd.concat(processed_dfs, axis=0, join='outer', sort=True)
        
        # Reset index to make timestamp a column again
        combined_df.reset_index(inplace=True)
        
        # Sort by timestamp
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
    
    # Find CSV sets
    logging.info(f"Searching for CSV sets in: {args.input_directory}")
    sets = find_csv_sets(args.input_directory, args.pattern)
    
    if not sets:
        logging.warning("No CSV sets found!")
        return 0
    
    logging.info(f"Found {len(sets)} CSV sets to process")
    
    # Process each set
    success_count = 0
    for results_csv, logs_csv, journalctl_csv, base_name in sets:
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
        if combine_csv_files(results_csv, logs_csv, journalctl_csv, output_csv):
            success_count += 1
        else:
            logging.error(f"Failed to process set: {base_name}")
    
    logging.info(f"Successfully processed {success_count}/{len(sets)} CSV sets")
    
    if success_count > 0:
        logging.info("Combined CSV files have been created with _combined.csv suffix")
        logging.info("The files include all columns from results, logs, and journalctl CSVs, indexed by timestamp")
    
    return 0 if success_count > 0 else 1

if __name__ == "__main__":
    exit(main())