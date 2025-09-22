#!/usr/bin/env python3
"""
Test Report Generator for RS ATS Test Results

A modular Python package for generating HTML reports from test result JSON files.
"""

__version__ = "2.0.0"
__author__ = "Test Report Generator"
__description__ = "Generate HTML reports from RS ATS test results"

from .services import ReportService
from .models import TestResult, SetupReport
from .parsers import TestResultParser, SetupReportParser
from .generators import HTMLReportGenerator, IndexGenerator

__all__ = [
    'ReportService',
    'TestResult', 'SetupReport',
    'TestResultParser', 'SetupReportParser',
    'HTMLReportGenerator', 'IndexGenerator'
]