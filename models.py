#!/usr/bin/env python3
"""
Data models for the test report generator.
"""

from dataclasses import dataclass
from typing import Dict, List, Any, Optional
from pathlib import Path


@dataclass
class TestResult:
    """Represents a single test result"""
    test_name: str
    test_folder: str
    results_data: List[Dict[str, Any]]
    params: Dict[str, Any]
    status: Dict[str, Any]
    screenshots: List[str]
    longrepr: str = ""


@dataclass
class SetupReport:
    """Represents a setup report with test summaries"""
    setup_name: str
    setup_folder: str
    test_summary: Dict[str, Any]
    tests: List[Dict[str, Any]]
    logs: List[Dict[str, Any]]


@dataclass
class LogEntry:
    """Represents a single log entry"""
    timestamp: str
    level: str
    message: str
    test_name: str = ""
    setup_name: str = ""


@dataclass
class TestSummary:
    """Represents test execution summary"""
    total: int = 0
    passed: int = 0
    failed: int = 0
    error: int = 0
    duration: float = 0.0
    created: float = 0.0


@dataclass
class TestInfo:
    """Represents individual test information"""
    name: str
    outcome: str
    duration: float = 0.0
    error_message: str = ""