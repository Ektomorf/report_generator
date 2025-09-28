#!/usr/bin/env python3
"""
CSV data loading and parsing functionality
"""

import csv
from typing import Dict, List, Any
from pathlib import Path

from models import AnalyzerData, RowData, ColumnInfo, ColumnType, RowType


class CSVLoader:
    """Handles loading and parsing CSV files"""

    def __init__(self):
        self.data = AnalyzerData()

    def load_csv(self, csv_path: str) -> AnalyzerData:
        """Load CSV data and analyze column types"""
        print(f"Loading CSV: {csv_path}")

        with open(csv_path, 'r', encoding='utf-8', newline='') as f:
            # Try to detect dialect, fallback to standard CSV
            sample = f.read(8192)
            f.seek(0)

            try:
                dialect = csv.Sniffer().sniff(sample)
            except csv.Error:
                # Fallback to standard CSV format
                dialect = csv.excel

            reader = csv.DictReader(f, dialect=dialect)
            self.data.columns = reader.fieldnames or []

            # Load all data
            for row_idx, row in enumerate(reader):
                # Convert empty strings to None for cleaner display
                cleaned_row = {}
                for key, value in row.items():
                    if value == '':
                        cleaned_row[key] = None
                    else:
                        cleaned_row[key] = value

                # Create row data object
                row_data = RowData(
                    data=cleaned_row,
                    row_index=row_idx,
                    row_type=self._classify_row(cleaned_row)
                )

                # Set additional row metadata
                row_data.is_empty = self._is_empty_row(cleaned_row)
                row_data.css_class = self._get_row_class(cleaned_row, row_data.row_type)

                self.data.add_row(row_data)

        print(f"Loaded {self.data.get_row_count()} rows with {len(self.data.columns)} columns")
        self._analyze_columns()
        return self.data

    def _analyze_columns(self) -> None:
        """Analyze column types and groupings"""
        for col in self.data.columns:
            col_type = self._detect_column_type(col)
            group = self._determine_column_group(col)

            # Set default visibility
            is_visible = col in self.data.config.default_visible_columns

            self.data.column_info[col] = ColumnInfo(
                name=col,
                column_type=col_type,
                group=group,
                visible=is_visible
            )

    def _detect_column_type(self, column: str) -> ColumnType:
        """Detect column data type from column name and sample values"""
        # Check column name patterns
        col_lower = column.lower()

        if 'timestamp' in col_lower:
            return ColumnType.TIMESTAMP
        if col_lower in ['pass', 'socan_pass', 'rf_matrix_pass']:
            return ColumnType.BOOLEAN
        if col_lower in ['level', 'log_type']:
            return ColumnType.CATEGORY
        if 'frequency' in col_lower:
            return ColumnType.NUMBER
        if 'amplitude' in col_lower or 'dbm' in col_lower:
            return ColumnType.NUMBER
        if col_lower in ['message', 'docstring', 'command_str', 'data_str']:
            return ColumnType.TEXT

        # Analyze sample values
        sample_values = []
        for row in self.data.rows[:100]:  # Sample first 100 rows
            val = row.get_value(column)
            if val is not None:
                sample_values.append(val)

        if not sample_values:
            return ColumnType.TEXT

        # Try to detect numeric values
        numeric_count = 0
        for val in sample_values:
            try:
                float(val)
                numeric_count += 1
            except (ValueError, TypeError):
                pass

        if numeric_count > len(sample_values) * 0.7:
            return ColumnType.NUMBER

        # Check for boolean-like values
        bool_values = {'true', 'false', 'yes', 'no', '1', '0'}
        if all(str(val).lower() in bool_values for val in sample_values):
            return ColumnType.BOOLEAN

        return ColumnType.TEXT

    def _determine_column_group(self, column: str) -> str:
        """Determine which group a column belongs to"""
        col_lower = column.lower()

        if column in ['Pass', 'timestamp', 'Timestamp_original']:
            return 'Core'
        elif any(x in col_lower for x in ['pass', 'result', 'peak_', 'amplitude', 'frequency']):
            return 'Test Results'
        elif any(x in col_lower for x in ['command', 'method', 'response', 'parsed_']):
            return 'Commands'
        elif any(x in col_lower for x in ['peak_table', 'trace_', 'measurement', 'data_']):
            return 'Measurements'
        elif any(x in col_lower for x in ['timestamp', 'time', 'send_', 'receive_']):
            return 'Timing'
        elif any(x in col_lower for x in ['enabled_', 'frequency_', 'gain_', 'channel', 'address']):
            return 'Configuration'
        elif any(x in col_lower for x in ['log_', 'level', 'message', 'line_number']):
            return 'Logging'
        else:
            return 'Other'

    def _classify_row(self, row: Dict[str, Any]) -> RowType:
        """Determine if a row is a test result vs a log entry"""
        # Check for result indicators
        if row.get('Pass') is not None:
            return RowType.RESULT
        if row.get('log_type') or row.get('level'):
            return RowType.LOG
        if row.get('command_method') or row.get('keysight_xsan_command'):
            return RowType.RESULT
        if row.get('peak_amplitude') or row.get('frequencies'):
            return RowType.RESULT
        return RowType.LOG

    def _is_empty_row(self, row: Dict[str, Any]) -> bool:
        """Determine if a row only contains timestamp data and no other meaningful content"""
        # Get all columns except internal ones and common timestamp columns
        exclude_columns = {'_row_index', '_row_class', '_is_result', 'timestamp',
                          'Timestamp_original', 'timestamp_logs', 'timestamp_results'}
        data_columns = [col for col in self.data.columns if col not in exclude_columns]

        # Check if all data columns are empty/null
        non_empty_count = 0
        for col in data_columns:
            value = row.get(col)
            if value is not None and str(value).strip() != '':
                non_empty_count += 1

        return non_empty_count == 0

    def _get_row_class(self, row: Dict[str, Any], row_type: RowType) -> str:
        """Get CSS class for row styling"""
        if row_type == RowType.RESULT:
            if row.get('Pass') == 'True':
                return 'result-row result-pass'
            elif row.get('Pass') == 'False':
                return 'result-row result-fail'
            else:
                return 'result-row'
        else:
            log_level = row.get('level')
            if log_level:
                log_level = str(log_level).upper()
                if log_level in ['ERROR', 'CRITICAL']:
                    return 'log-row log-error'
                elif log_level == 'WARNING':
                    return 'log-row log-warning'
                elif log_level == 'INFO':
                    return 'log-row log-info'
                elif log_level == 'DEBUG':
                    return 'log-row log-debug'
            return 'log-row'