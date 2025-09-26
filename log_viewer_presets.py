#!/usr/bin/env python3
"""
Log Viewer Column Presets Configuration

Define custom column presets for the log viewer HTML files.
You can modify this file to create your own preset combinations.

Preset Format:
- 'preset_name': ['column1', 'column2', 'column3', ...]
- Use exact column names as they appear in your CSV files
- Order matters - columns will appear in the order listed
- If a column doesn't exist in a particular log file, it will be ignored
"""

# Default presets that work across all log types
DEFAULT_PRESETS = {
    'basic': [
        'timestamp',
        'level',
        'command_method',
        'command_str'
    ],

    'detailed': [
        'timestamp',
        'level',
        'command_method',
        'command_str',
        'raw_response',
        'parsed_response'
    ],

    'network': [
        'timestamp',
        'level',
        'command_method',
        'raw_response'
    ],

    'timing': [
        'timestamp',
        'send_timestamp',
        'receive_timestamp',
        'level',
        'command_method',
        'command_str'
    ],

    'frequency_analysis': [
        'timestamp',
        'level',
        'command_method',
        'set_lo_frequency_freq',
        'parsed_response_set_lo_frequency_freq',
        'switch_connection_matrix',
        'switch_connection_y',
        'switch_connection_port'
    ],

    'channel_config': [
        'timestamp',
        'level',
        'command_method',
        'address',
        'parsed_response_channels',
        'get_response_channels',
        'set_response_channels'
    ],

    'peak_detection': [
        'timestamp',
        'level',
        'command_method',
        'peak_data',
        'frequency_range_ghz',
        'amplitude_range_dbm',
        'peak_count'
    ],

    'debug': [
        'timestamp',
        'level',
        'command_method',
        'command_str',
        'raw_response',
        'parsed_response',
        'raw_data'
    ]
}

# Test-specific presets for different types of tests
TEST_SPECIFIC_PRESETS = {
    'fwd_tests': {
        'fwd_basic': [
            'timestamp',
            'level',
            'command_method',
            'command_str',
            'switch_connection_matrix',
            'switch_connection_y',
            'switch_connection_port',
            'set_lo_frequency_freq'
        ],

        'fwd_detailed': [
            'timestamp',
            'level',
            'command_method',
            'command_str',
            'raw_response',
            'switch_connection_matrix',
            'switch_connection_y',
            'switch_connection_port',
            'set_lo_frequency_converter',
            'set_lo_frequency_freq',
            'peak_data'
        ]
    },

    'rtn_tests': {
        'rtn_basic': [
            'timestamp',
            'level',
            'command_method',
            'command_str',
            '**kwargs_address',
            'parsed_response_switch_connection_matrix',
            'parsed_response_switch_connection_y',
            'parsed_response_switch_connection_port'
        ],

        'rtn_detailed': [
            'timestamp',
            'level',
            'command_method',
            'command_str',
            'raw_response',
            '**kwargs_address',
            'parsed_response_channels',
            'parsed_response_switch_connection_matrix',
            'parsed_response_switch_connection_y',
            'parsed_response_switch_connection_port',
            'parsed_response_set_lo_frequency_freq'
        ]
    },

    'setup_tests': {
        'setup_basic': [
            'timestamp',
            'level',
            'command_method',
            'raw_data'
        ]
    }
}

def get_presets_for_test_type(test_name: str = None) -> dict:
    """
    Get appropriate presets based on test type.

    Args:
        test_name: Name of the test (e.g., 'test_fwd_defaults', 'test_rtn_defaults')

    Returns:
        Dictionary of presets appropriate for the test type
    """
    presets = DEFAULT_PRESETS.copy()

    if test_name:
        test_name_lower = test_name.lower()

        # Add test-specific presets based on test name
        if 'fwd' in test_name_lower:
            presets.update(TEST_SPECIFIC_PRESETS.get('fwd_tests', {}))
        elif 'rtn' in test_name_lower:
            presets.update(TEST_SPECIFIC_PRESETS.get('rtn_tests', {}))
        elif 'setup' in test_name_lower:
            presets.update(TEST_SPECIFIC_PRESETS.get('setup_tests', {}))

    return presets

def get_default_column_order(available_columns: list) -> list:
    """
    Get the default column order, prioritizing timestamp first.

    Args:
        available_columns: List of all available columns

    Returns:
        List of columns in preferred order
    """
    # Priority order for common columns
    priority_order = [
        'timestamp',
        'send_timestamp',
        'receive_timestamp',
        'level',
        'command_method',
        'command_str',
        'raw_response',
        'parsed_response',
        'address',
        'switch_connection_matrix',
        'switch_connection_y',
        'switch_connection_port',
        'set_lo_frequency_converter',
        'set_lo_frequency_freq'
    ]

    # Start with priority columns that exist
    ordered_columns = [col for col in priority_order if col in available_columns]

    # Add remaining columns alphabetically
    remaining_columns = [col for col in sorted(available_columns) if col not in ordered_columns]
    ordered_columns.extend(remaining_columns)

    return ordered_columns

# Example of how to add your own custom presets:
#
# CUSTOM_PRESETS = {
#     'my_analysis': [
#         'timestamp',
#         'level',
#         'custom_field1',
#         'custom_field2'
#     ]
# }
#
# Then modify get_presets_for_test_type() to include CUSTOM_PRESETS