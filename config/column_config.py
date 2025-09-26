#!/usr/bin/env python3
"""
Column configuration for test reports.
"""

from dataclasses import dataclass
from typing import List, Dict, Set, Optional
from enum import Enum


class ColumnType(Enum):
    """Types of columns for different formatting"""
    TEXT = "text"
    NUMERIC = "numeric"
    COMMAND = "command"
    RESPONSE = "response"
    PARSED_RESPONSE = "parsed_response"
    SCREENSHOT = "screenshot"
    FREQUENCY = "frequency"
    AMPLITUDE = "amplitude"


@dataclass
class ColumnDefinition:
    """Definition for a single column"""
    key: str
    display_name: str
    column_type: ColumnType = ColumnType.TEXT
    visible: bool = True
    order: int = 999
    width: Optional[str] = None
    description: Optional[str] = None


class ColumnConfigManager:
    """Manager for column configuration"""

    def __init__(self):
        self._default_columns = self._create_default_columns()
        self._custom_columns = {}
        self._column_order = []
        self._visible_columns = set()
        self._load_default_configuration()

    def _create_default_columns(self) -> Dict[str, ColumnDefinition]:
        """Create default column definitions"""
        return {
            'Timestamp': ColumnDefinition(
                key='Timestamp',
                display_name='Timestamp',
                column_type=ColumnType.TEXT,
                order=1,
                description='Test execution timestamp'
            ),
            'channel': ColumnDefinition(
                key='channel',
                display_name='Channel',
                column_type=ColumnType.TEXT,
                order=10,
                description='Channel identifier'
            ),
            'frequency': ColumnDefinition(
                key='frequency',
                display_name='Frequency',
                column_type=ColumnType.FREQUENCY,
                order=20,
                description='Operating frequency'
            ),
            'enabled': ColumnDefinition(
                key='enabled',
                display_name='Enabled',
                column_type=ColumnType.TEXT,
                order=30,
                description='Channel enabled status'
            ),
            'gain': ColumnDefinition(
                key='gain',
                display_name='Gain',
                column_type=ColumnType.NUMERIC,
                order=40,
                description='Signal gain'
            ),
            'peak_frequency': ColumnDefinition(
                key='peak_frequency',
                display_name='Peak Frequency',
                column_type=ColumnType.FREQUENCY,
                order=50,
                description='Peak frequency detected'
            ),
            'peak_amplitude': ColumnDefinition(
                key='peak_amplitude',
                display_name='Peak Amplitude',
                column_type=ColumnType.AMPLITUDE,
                order=60,
                description='Peak amplitude measured'
            ),
            'screenshot_filepath': ColumnDefinition(
                key='screenshot_filepath',
                display_name='Screenshot',
                column_type=ColumnType.SCREENSHOT,
                order=70,
                description='Link to screenshot'
            ),
            'socan_command_method': ColumnDefinition(
                key='socan_command_method',
                display_name='SOCAN Method',
                column_type=ColumnType.COMMAND,
                order=100,
                description='SOCAN command method'
            ),
            'socan_command_args': ColumnDefinition(
                key='socan_command_args',
                display_name='SOCAN Args',
                column_type=ColumnType.COMMAND,
                order=110,
                description='SOCAN command arguments'
            ),
            'socan_command': ColumnDefinition(
                key='socan_command',
                display_name='SOCAN Command',
                column_type=ColumnType.COMMAND,
                order=120,
                description='Full SOCAN command'
            ),
            'parsed_socan_response': ColumnDefinition(
                key='parsed_socan_response',
                display_name='SOCAN Parsed Response',
                column_type=ColumnType.PARSED_RESPONSE,
                order=130,
                description='Parsed SOCAN response'
            ),
            'raw_socan_response': ColumnDefinition(
                key='raw_socan_response',
                display_name='SOCAN Raw Response',
                column_type=ColumnType.RESPONSE,
                order=140,
                description='Raw SOCAN response'
            ),
            'rf_matrix_command_method': ColumnDefinition(
                key='rf_matrix_command_method',
                display_name='RF Matrix Method',
                column_type=ColumnType.COMMAND,
                order=200,
                description='RF Matrix command method'
            ),
            'rf_matrix_command_args': ColumnDefinition(
                key='rf_matrix_command_args',
                display_name='RF Matrix Args',
                column_type=ColumnType.COMMAND,
                order=210,
                description='RF Matrix command arguments'
            ),
            'rf_matrix_command': ColumnDefinition(
                key='rf_matrix_command',
                display_name='RF Matrix Command',
                column_type=ColumnType.COMMAND,
                order=220,
                description='Full RF Matrix command'
            ),
            'parsed_rf_matrix_response': ColumnDefinition(
                key='parsed_rf_matrix_response',
                display_name='RF Matrix Parsed Response',
                column_type=ColumnType.PARSED_RESPONSE,
                order=230,
                description='Parsed RF Matrix response'
            ),
            'raw_rf_matrix_response': ColumnDefinition(
                key='raw_rf_matrix_response',
                display_name='RF Matrix Raw Response',
                column_type=ColumnType.RESPONSE,
                order=240,
                description='Raw RF Matrix response'
            ),
            'keysight_xsan_command_method': ColumnDefinition(
                key='keysight_xsan_command_method',
                display_name='Keysight XSAN Method',
                column_type=ColumnType.COMMAND,
                order=300,
                description='Keysight XSAN command method'
            ),
            'keysight_xsan_command_args': ColumnDefinition(
                key='keysight_xsan_command_args',
                display_name='Keysight XSAN Args',
                column_type=ColumnType.COMMAND,
                order=310,
                description='Keysight XSAN command arguments'
            ),
            'keysight_xsan_command': ColumnDefinition(
                key='keysight_xsan_command',
                display_name='Keysight XSAN Command',
                column_type=ColumnType.COMMAND,
                order=320,
                description='Full Keysight XSAN command'
            ),
            'spectrum_frequencies': ColumnDefinition(
                key='spectrum_frequencies',
                display_name='Spectrum Frequencies',
                column_type=ColumnType.TEXT,
                order=400,
                visible=False,
                description='Spectrum frequency data'
            ),
            'spectrum_amplitudes': ColumnDefinition(
                key='spectrum_amplitudes',
                display_name='Spectrum Amplitudes',
                column_type=ColumnType.TEXT,
                order=410,
                visible=False,
                description='Spectrum amplitude data'
            ),
            'frequencies': ColumnDefinition(
                key='frequencies',
                display_name='Frequencies',
                column_type=ColumnType.TEXT,
                order=420,
                visible=False,
                description='Frequency data array'
            ),
            'amplitudes': ColumnDefinition(
                key='amplitudes',
                display_name='Amplitudes',
                column_type=ColumnType.TEXT,
                order=430,
                visible=False,
                description='Amplitude data array'
            ),
        }

    def _load_default_configuration(self):
        """Load the default column configuration"""
        # Set visible columns (the ones that are visible by default)
        visible_keys = [
            'Timestamp', 'channel', 'frequency', 'enabled', 'gain',
            'peak_frequency', 'peak_amplitude', 'screenshot_filepath',
            'socan_command_method', 'socan_command_args', 'socan_command',
            'parsed_socan_response',
            'rf_matrix_command_method', 'rf_matrix_command_args', 'rf_matrix_command',
            'parsed_rf_matrix_response',
            'keysight_xsan_command_method', 'keysight_xsan_command_args', 'keysight_xsan_command'
        ]

        self._visible_columns = set(visible_keys)

        # Set column order
        self._column_order = sorted(
            self._default_columns.keys(),
            key=lambda k: self._default_columns[k].order
        )

    def get_column_definition(self, key: str) -> Optional[ColumnDefinition]:
        """Get column definition for a key"""
        return self._custom_columns.get(key) or self._default_columns.get(key)

    def get_all_available_columns(self) -> List[ColumnDefinition]:
        """Get all available column definitions"""
        all_columns = {}
        all_columns.update(self._default_columns)
        all_columns.update(self._custom_columns)
        return list(all_columns.values())

    def get_visible_columns(self) -> List[str]:
        """Get list of visible column keys in order"""
        return [key for key in self._column_order if key in self._visible_columns]

    def set_visible_columns(self, column_keys: List[str]):
        """Set which columns are visible"""
        self._visible_columns = set(column_keys)

    def set_column_order(self, ordered_keys: List[str]):
        """Set the order of columns"""
        self._column_order = ordered_keys

    def add_custom_column(self, column_def: ColumnDefinition):
        """Add a custom column definition"""
        self._custom_columns[column_def.key] = column_def
        if column_def.key not in self._column_order:
            self._column_order.append(column_def.key)

    def hide_column(self, key: str):
        """Hide a specific column"""
        self._visible_columns.discard(key)

    def show_column(self, key: str):
        """Show a specific column"""
        if key in self._default_columns or key in self._custom_columns:
            self._visible_columns.add(key)

    def is_column_visible(self, key: str) -> bool:
        """Check if a column is visible"""
        return key in self._visible_columns

    def get_ordered_visible_keys(self, available_keys: Set[str]) -> List[str]:
        """Get ordered list of visible keys that are actually available in the data"""
        # Start with configured order
        ordered_keys = []
        remaining_keys = set(available_keys)

        # Add keys in configured order if they're visible and available
        for key in self._column_order:
            if key in self._visible_columns and key in remaining_keys:
                ordered_keys.append(key)
                remaining_keys.remove(key)

        # Add any remaining keys that are visible but not in configured order
        for key in remaining_keys:
            if key in self._visible_columns:
                ordered_keys.append(key)
                remaining_keys.remove(key)

        # Handle dynamic channel columns (enabled_*, frequency_*, gain_*)
        channel_keys = [k for k in remaining_keys if any(k.startswith(base) for base in ['enabled_', 'frequency_', 'gain_'])]
        for key in sorted(channel_keys):
            if self.should_show_dynamic_column(key):
                ordered_keys.append(key)
                remaining_keys.remove(key)

        # Add any other remaining keys if they would be visible by default
        for key in sorted(remaining_keys):
            if self.should_show_dynamic_column(key):
                ordered_keys.append(key)

        return ordered_keys

    def should_show_dynamic_column(self, key: str) -> bool:
        """Determine if a dynamic column should be shown"""
        # For now, show all dynamic columns that aren't explicitly hidden
        # This can be enhanced later with more sophisticated rules
        return True

    def get_column_css_class(self, key: str) -> str:
        """Get CSS class for a column based on its type"""
        column_def = self.get_column_definition(key)
        if not column_def:
            # Fallback logic for unknown columns
            if 'command' in key.lower():
                return 'command'
            elif 'parsed' in key.lower() and 'response' in key.lower():
                return 'parsed-response'
            elif 'response' in key.lower():
                return 'response'
            elif any(word in key.lower() for word in ['frequency', 'amplitude', 'peak']):
                return 'numeric'
            return ''

        type_to_class = {
            ColumnType.COMMAND: 'command',
            ColumnType.RESPONSE: 'response',
            ColumnType.PARSED_RESPONSE: 'parsed-response',
            ColumnType.NUMERIC: 'numeric',
            ColumnType.FREQUENCY: 'numeric',
            ColumnType.AMPLITUDE: 'numeric',
            ColumnType.SCREENSHOT: '',
            ColumnType.TEXT: ''
        }

        return type_to_class.get(column_def.column_type, '')