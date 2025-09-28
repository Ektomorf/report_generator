#!/usr/bin/env python3
"""
Data models and utilities for CSV analyzer
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum


class ColumnType(Enum):
    """Column data types"""
    TEXT = "text"
    NUMBER = "number"
    BOOLEAN = "boolean"
    CATEGORY = "category"
    TIMESTAMP = "timestamp"


class RowType(Enum):
    """Row classification types"""
    RESULT = "result"
    LOG = "log"


@dataclass
class AnalyzerConfig:
    """Configuration for the analyzer"""
    hide_empty_rows: bool = True
    default_visible_columns: List[str] = None

    def __post_init__(self):
        if self.default_visible_columns is None:
            self.default_visible_columns = ['Pass', 'timestamp', 'message', 'command_method']


@dataclass
class RowData:
    """Represents a single row of data with metadata"""
    data: Dict[str, Any]
    row_index: int
    row_type: RowType
    is_empty: bool = False
    css_class: str = ""

    def get_value(self, column: str) -> Any:
        """Get value for a specific column"""
        return self.data.get(column)

    def set_value(self, column: str, value: Any) -> None:
        """Set value for a specific column"""
        self.data[column] = value


@dataclass
class ColumnInfo:
    """Information about a column"""
    name: str
    column_type: ColumnType
    group: str = "Other"
    visible: bool = False


class AnalyzerData:
    """Container for all analyzer data"""

    def __init__(self):
        self.rows: List[RowData] = []
        self.columns: List[str] = []
        self.column_info: Dict[str, ColumnInfo] = {}
        self.config = AnalyzerConfig()

    def add_row(self, row_data: RowData) -> None:
        """Add a row to the dataset"""
        self.rows.append(row_data)

    def get_column_names(self) -> List[str]:
        """Get list of all column names"""
        return self.columns.copy()

    def get_visible_columns(self) -> List[str]:
        """Get list of visible column names"""
        return [col for col in self.columns if self.column_info[col].visible]

    def set_column_visibility(self, column: str, visible: bool) -> None:
        """Set visibility for a column"""
        if column in self.column_info:
            self.column_info[column].visible = visible

    def get_column_type(self, column: str) -> ColumnType:
        """Get the type of a column"""
        return self.column_info.get(column, ColumnInfo(column, ColumnType.TEXT)).column_type

    def get_row_count(self) -> int:
        """Get total number of rows"""
        return len(self.rows)

    def get_result_count(self) -> int:
        """Get number of result rows"""
        return sum(1 for row in self.rows if row.row_type == RowType.RESULT)

    def get_log_count(self) -> int:
        """Get number of log rows"""
        return sum(1 for row in self.rows if row.row_type == RowType.LOG)


def html_escape(text: str) -> str:
    """Escape HTML characters"""
    return (str(text)
            .replace('&', '&amp;')
            .replace('<', '&lt;')
            .replace('>', '&gt;')
            .replace('"', '&quot;')
            .replace("'", '&#x27;'))