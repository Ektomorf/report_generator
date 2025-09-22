#!/usr/bin/env python3
"""
Base parser interface for test result files.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, Optional
import json


class BaseParser(ABC):
    """Abstract base class for all parsers"""

    def __init__(self, folder_path: Path):
        self.folder_path = folder_path
        self.folder_name = folder_path.name

    @abstractmethod
    def parse(self) -> Dict[str, Any]:
        """Parse the data from the folder"""
        pass

    def _load_json_file(self, file_path: Path) -> Dict[str, Any]:
        """Safely load a JSON file"""
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            print(f"Warning: Invalid JSON in {file_path.name}: {str(e)}")
            return {}
        except FileNotFoundError:
            return {}

    def _find_file_with_suffix(self, suffix: str) -> Optional[Path]:
        """Find file with specific suffix in folder"""
        for file in self.folder_path.glob(f'*{suffix}'):
            return file
        return None