#!/usr/bin/env python3
"""
Data processing, filtering, and formatting functionality
"""

from datetime import datetime
from typing import Dict, List, Any, Optional, Callable
from models import AnalyzerData, RowData, ColumnType, RowType, html_escape


class DataProcessor:
    """Handles data processing, filtering, and formatting"""

    def __init__(self, data: AnalyzerData):
        self.data = data

    def filter_data(self, filters: Dict[str, Any] = None,
                   global_search: str = "",
                   hide_empty_rows: bool = True) -> List[RowData]:
        """Apply filters to the data and return filtered rows"""
        if filters is None:
            filters = {}

        filtered_rows = []

        for row in self.data.rows:
            # Hide empty rows filter (dynamic based on visible columns)
            if hide_empty_rows and self._is_row_empty_based_on_visible_columns(row):
                continue

            # Global search
            if global_search:
                row_text = ' '.join(str(row.get_value(col) or '') for col in self.data.columns).lower()
                if global_search.lower() not in row_text:
                    continue

            # Column filters
            if not self._apply_column_filters(row, filters):
                continue

            filtered_rows.append(row)

        return filtered_rows

    def _is_row_empty_based_on_visible_columns(self, row: RowData) -> bool:
        """Check if a row is empty based on currently visible columns"""
        timestamp_columns = {'timestamp', 'Timestamp_original', 'timestamp_logs', 'timestamp_results'}
        visible_data_columns = [col for col in self.data.get_visible_columns()
                               if col not in timestamp_columns]

        for col in visible_data_columns:
            value = row.get_value(col)
            if value is not None and str(value).strip() != '':
                return False

        return len(visible_data_columns) > 0

    def _apply_column_filters(self, row: RowData, filters: Dict[str, Any]) -> bool:
        """Apply column-specific filters to a row"""
        for column, filter_config in filters.items():
            value = row.get_value(column)

            if filter_config.get('type') == 'text':
                filter_value = filter_config.get('value', '').lower()
                if filter_value and filter_value not in str(value or '').lower():
                    return False

            elif filter_config.get('type') == 'select':
                allowed_values = filter_config.get('values', [])
                if allowed_values and str(value or '') not in allowed_values:
                    return False

            elif filter_config.get('type') == 'range':
                try:
                    num_value = float(value or 0)
                    min_val = filter_config.get('min')
                    max_val = filter_config.get('max')

                    if min_val is not None and num_value < min_val:
                        return False
                    if max_val is not None and num_value > max_val:
                        return False
                except (ValueError, TypeError):
                    continue

        return True

    def sort_data(self, rows: List[RowData], column: str, direction: str = 'asc') -> List[RowData]:
        """Sort rows by a specific column"""
        def sort_key(row: RowData) -> Any:
            value = row.get_value(column)

            # Handle null/undefined values
            if value is None:
                return '' if direction == 'asc' else 'zzz'

            # Try numeric comparison first
            try:
                return float(value)
            except (ValueError, TypeError):
                # Fall back to string comparison
                return str(value).lower()

        return sorted(rows, key=sort_key, reverse=(direction == 'desc'))

    def format_cell_value(self, value: Any, column: str) -> str:
        """Format cell value for display"""
        if value is None:
            return ''

        value_str = str(value)

        # Handle timestamp columns
        if self.data.get_column_type(column) == ColumnType.TIMESTAMP:
            formatted_ts = self.format_timestamp(value_str)
            if formatted_ts != value_str:  # Only show formatted if different
                value_str = formatted_ts

        # Handle very long values
        if len(value_str) > 200:
            truncated = value_str[:197] + '...'
            escaped_full = html_escape(value_str)
            escaped_truncated = html_escape(truncated)
            return f'<span class="cell-content expandable" title="Click to expand" data-full="{escaped_full}">{escaped_truncated}</span>'
        else:
            return html_escape(value_str)

    def format_timestamp(self, timestamp_str: str) -> str:
        """Convert Unix timestamp (ms) to readable format yyyy-mm-dd hh:mm:ss,ms UTC"""
        if not timestamp_str or timestamp_str.strip() == '':
            return ''

        try:
            # First, try to parse as Unix timestamp in milliseconds (e.g., 1758902529684)
            if timestamp_str.strip().isdigit():
                timestamp_ms = int(timestamp_str.strip())
                # Convert from milliseconds to seconds for datetime
                dt = datetime.fromtimestamp(timestamp_ms / 1000.0)
                # Format to requested format: yyyy-mm-dd hh:mm:ss,ms
                ms = timestamp_ms % 1000  # Extract milliseconds
                formatted = dt.strftime('%Y-%m-%d %H:%M:%S') + f',{ms:03d}'
                return formatted

            # If not a Unix timestamp, try to parse as ISO format: "2025-09-26 17:01:59,358"
            if ',' in timestamp_str:
                # Replace comma with dot for milliseconds
                timestamp_str = timestamp_str.replace(',', '.')

            # Parse the timestamp (assuming it's already in UTC)
            dt = datetime.fromisoformat(timestamp_str)

            # Format to requested format: yyyy-mm-dd hh:mm:ss,ms
            formatted = dt.strftime('%Y-%m-%d %H:%M:%S')

            # Add milliseconds if present
            if dt.microsecond:
                ms = dt.microsecond // 1000  # Convert microseconds to milliseconds
                formatted += f',{ms:03d}'

            return formatted

        except (ValueError, AttributeError, OSError):
            # If parsing fails, return original value
            return timestamp_str

    def get_column_groups(self) -> Dict[str, List[str]]:
        """Group columns by category for better organization"""
        groups = {}

        for col in self.data.columns:
            group = self.data.column_info[col].group
            if group not in groups:
                groups[group] = []
            groups[group].append(col)

        # Remove empty groups and return in a specific order
        ordered_groups = ['Core', 'Test Results', 'Commands', 'Measurements',
                         'Timing', 'Configuration', 'Logging', 'Other']

        result = {}
        for group in ordered_groups:
            if group in groups and groups[group]:
                result[group] = groups[group]

        # Add any remaining groups
        for group, cols in groups.items():
            if group not in result and cols:
                result[group] = cols

        return result

    def get_unique_values(self, column: str) -> List[str]:
        """Get unique values for a column (useful for category filters)"""
        values = set()
        for row in self.data.rows:
            value = row.get_value(column)
            if value is not None:
                values.add(str(value))
        return sorted(list(values))

    def get_statistics(self, filtered_rows: List[RowData]) -> Dict[str, int]:
        """Get statistics about the current data"""
        total_rows = len(filtered_rows)
        result_rows = sum(1 for row in filtered_rows if row.row_type == RowType.RESULT)
        log_rows = total_rows - result_rows

        return {
            'total_rows': total_rows,
            'total_data_rows': self.data.get_row_count(),
            'result_rows': result_rows,
            'log_rows': log_rows
        }