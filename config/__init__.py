#!/usr/bin/env python3
"""
Configuration package for the report generator.
"""

from .column_config import ColumnConfigManager, ColumnDefinition, ColumnType

__all__ = ['ColumnConfigManager', 'ColumnDefinition', 'ColumnType']