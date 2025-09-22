"""
Parser modules for different types of test result files.
"""

from parsers.base_parser import BaseParser
from parsers.test_result_parser import TestResultParser
from parsers.setup_report_parser import SetupReportParser

__all__ = ['BaseParser', 'TestResultParser', 'SetupReportParser']