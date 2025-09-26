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

    def generate_display_name(self, key: str) -> str:
        """Generate a human-readable display name for a column key"""
        # Handle common patterns first
        if key == 'Timestamp':
            return 'Timestamp'

        # Convert snake_case and camelCase to Title Case
        # Replace underscores with spaces and capitalize words
        display_name = key.replace('_', ' ')

        # Handle common abbreviations and technical terms
        word_replacements = {
            'rf': 'RF',
            'socan': 'SOCAN',
            'xsan': 'XSAN',
            'keysight': 'Keysight',
            'command': 'Command',
            'response': 'Response',
            'parsed': 'Parsed',
            'raw': 'Raw',
            'method': 'Method',
            'args': 'Args',
            'filepath': 'File Path',
            'screenshot': 'Screenshot',
            'frequency': 'Frequency',
            'amplitude': 'Amplitude',
            'channel': 'Channel',
            'enabled': 'Enabled',
            'gain': 'Gain',
            'peak': 'Peak',
            'spectrum': 'Spectrum',
            'frequencies': 'Frequencies',
            'amplitudes': 'Amplitudes'
        }

        # Split into words and apply replacements
        words = display_name.split()
        formatted_words = []

        for word in words:
            word_lower = word.lower()
            if word_lower in word_replacements:
                formatted_words.append(word_replacements[word_lower])
            else:
                # Capitalize first letter of each word
                formatted_words.append(word.capitalize())

        return ' '.join(formatted_words)

    def register_dynamic_column(self, key: str, data_sample=None) -> ColumnDefinition:
        """Register a new dynamic column based on the key and optional data sample"""
        # Check if already registered
        if key in self._default_columns or key in self._custom_columns:
            return self.get_column_definition(key)

        # Generate display name
        display_name = self.generate_display_name(key)

        # Determine column type based on key patterns and data sample
        column_type = self._infer_column_type(key, data_sample)

        # Determine default visibility
        visible = self._should_be_visible_by_default(key)

        # Create new column definition
        column_def = ColumnDefinition(
            key=key,
            display_name=display_name,
            column_type=column_type,
            visible=visible,
            order=self._get_dynamic_column_order(key),
            description=f'Dynamically detected column: {display_name}'
        )

        # Register as custom column
        self._custom_columns[key] = column_def

        # Add to column order if not already present
        if key not in self._column_order:
            # Insert in appropriate position based on order
            insert_pos = len(self._column_order)
            for i, existing_key in enumerate(self._column_order):
                existing_def = self.get_column_definition(existing_key)
                if existing_def and existing_def.order > column_def.order:
                    insert_pos = i
                    break
            self._column_order.insert(insert_pos, key)

        # Add to visible columns if it should be visible by default
        if visible:
            self._visible_columns.add(key)

        return column_def

    def _infer_column_type(self, key: str, data_sample=None) -> ColumnType:
        """Infer the column type based on key patterns and data sample"""
        key_lower = key.lower()

        # Check data sample first if available
        if data_sample is not None:
            if isinstance(data_sample, (int, float)):
                if any(term in key_lower for term in ['frequency', 'freq']):
                    return ColumnType.FREQUENCY
                elif any(term in key_lower for term in ['amplitude', 'amp', 'gain', 'power']):
                    return ColumnType.AMPLITUDE
                else:
                    return ColumnType.NUMERIC
            elif isinstance(data_sample, str):
                if 'screenshot' in key_lower or 'filepath' in key_lower:
                    return ColumnType.SCREENSHOT
                elif len(data_sample) > 100:  # Long strings might be responses
                    if 'parsed' in key_lower:
                        return ColumnType.PARSED_RESPONSE
                    elif 'response' in key_lower:
                        return ColumnType.RESPONSE
                    elif 'command' in key_lower:
                        return ColumnType.COMMAND

        # Fallback to pattern matching
        if 'command' in key_lower:
            return ColumnType.COMMAND
        elif 'parsed' in key_lower and 'response' in key_lower:
            return ColumnType.PARSED_RESPONSE
        elif 'response' in key_lower:
            return ColumnType.RESPONSE
        elif 'screenshot' in key_lower or 'filepath' in key_lower:
            return ColumnType.SCREENSHOT
        elif any(term in key_lower for term in ['frequency', 'freq']):
            return ColumnType.FREQUENCY
        elif any(term in key_lower for term in ['amplitude', 'amp', 'gain', 'power']):
            return ColumnType.AMPLITUDE
        elif any(term in key_lower for term in ['time', 'timestamp', 'date']):
            return ColumnType.TEXT

        return ColumnType.TEXT

    def _should_be_visible_by_default(self, key: str) -> bool:
        """Determine if a dynamic column should be visible by default"""
        key_lower = key.lower()

        # Always show important status/result columns
        important_patterns = [
            'pass', 'fail', 'status', 'result', 'error', 'success'
        ]

        for pattern in important_patterns:
            if pattern in key_lower:
                return True

        # Hide very technical or verbose columns by default
        hidden_patterns = [
            'raw_response', 'spectrum_frequencies', 'spectrum_amplitudes',
            'frequencies', 'amplitudes', 'debug', 'internal', 'temp'
        ]

        for pattern in hidden_patterns:
            if pattern in key_lower:
                return False

        # Show most other columns by default
        return True

    def _get_dynamic_column_order(self, key: str) -> int:
        """Get appropriate order number for a dynamic column"""
        key_lower = key.lower()

        # Order by category
        if 'timestamp' in key_lower or 'time' in key_lower:
            return 5
        elif 'channel' in key_lower:
            return 15
        elif 'frequency' in key_lower:
            return 25
        elif 'enabled' in key_lower:
            return 35
        elif 'gain' in key_lower:
            return 45
        elif 'amplitude' in key_lower or 'peak' in key_lower:
            return 55
        elif 'pass' in key_lower or 'fail' in key_lower or 'status' in key_lower:
            return 65  # Place pass/fail columns after measurements but before screenshots
        elif 'screenshot' in key_lower:
            return 75
        elif 'socan' in key_lower:
            if 'method' in key_lower:
                return 105
            elif 'args' in key_lower:
                return 115
            elif 'command' in key_lower:
                return 125
            elif 'parsed' in key_lower:
                return 135
            else:
                return 145
        elif 'rf' in key_lower and 'matrix' in key_lower:
            if 'method' in key_lower:
                return 205
            elif 'args' in key_lower:
                return 215
            elif 'command' in key_lower:
                return 225
            elif 'parsed' in key_lower:
                return 235
            else:
                return 245
        elif 'keysight' in key_lower or 'xsan' in key_lower:
            if 'method' in key_lower:
                return 305
            elif 'args' in key_lower:
                return 315
            elif 'command' in key_lower:
                return 325
            else:
                return 335

        # Default high order for unknown columns
        return 900

    def update_from_data_keys(self, data_keys: Set[str], data_samples: Dict[str, any] = None):
        """Update column configuration based on available data keys"""
        if data_samples is None:
            data_samples = {}

        # Register any new dynamic columns
        for key in data_keys:
            if key not in self._default_columns and key not in self._custom_columns:
                sample_data = data_samples.get(key)
                self.register_dynamic_column(key, sample_data)

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