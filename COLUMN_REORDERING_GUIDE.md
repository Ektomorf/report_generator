# Column Reordering & Custom Presets Guide

## New Features Added ✅

### 1. **Drag-and-Drop Column Reordering**
- **Drag Handle**: Each column has a `⋮⋮` handle for dragging
- **Visual Feedback**: Columns show hover effects and dragging states
- **Live Reordering**: Table updates immediately after dropping
- **Persistent Order**: Column order affects table display in real-time

### 2. **Intelligent Default Ordering**
- **Timestamp First**: `timestamp` column automatically appears first
- **Logical Grouping**: Related columns grouped together
- **Priority Ordering**: Important columns appear before less common ones

### 3. **Configurable Presets System**
- **External Configuration**: Edit `log_viewer_presets.py` to customize presets
- **Test-Specific Presets**: Different presets for FWD, RTN, and Setup tests
- **Smart Matching**: Presets automatically adapt to available columns

## How to Use

### Column Reordering
1. **Drag to Reorder**: Click and drag the `⋮⋮` handle next to any column
2. **Drop in Position**: Drop between other columns to reorder
3. **Instant Update**: Table columns reorder immediately
4. **Check/Uncheck**: Toggle column visibility independently

### Custom Presets
Edit `log_viewer_presets.py` to add your own presets:

```python
# Add to DEFAULT_PRESETS
'my_custom_view': [
    'timestamp',
    'level',
    'my_important_field',
    'another_field'
]
```

## Available Presets

### **Default Presets** (All Test Types)
- **Basic**: Essential columns (`timestamp`, `level`, `command_method`, `command_str`)
- **Detailed**: Basic + response data
- **Network**: Communication-focused view
- **Timing**: Timestamp analysis view
- **Debug**: Full diagnostic view

### **FWD Test Presets**
- **FWD Basic**: Forward path essentials
- **FWD Detailed**: Forward path with full data

### **RTN Test Presets**
- **RTN Basic**: Return path essentials
- **RTN Detailed**: Return path with full data

### **Setup Test Presets**
- **Setup Basic**: Minimal setup view

## Configuration Examples

### Add a Custom Analysis Preset
```python
# In log_viewer_presets.py, add to DEFAULT_PRESETS:
'frequency_analysis': [
    'timestamp',
    'level',
    'command_method',
    'set_lo_frequency_freq',
    'parsed_response_set_lo_frequency_freq',
    'switch_connection_matrix',
    'peak_data'
]
```

### Create Test-Specific Presets
```python
# Add new test type:
'my_special_tests': {
    'special_view': [
        'timestamp',
        'special_field1',
        'special_field2'
    ]
}
```

## Default Column Priority Order

1. **Timestamps**: `timestamp`, `send_timestamp`, `receive_timestamp`
2. **Log Info**: `level`, `command_method`, `command_str`
3. **Responses**: `raw_response`, `parsed_response`
4. **Hardware**: `address`, switch/LO frequency fields
5. **Everything Else**: Alphabetically sorted

## Testing Your Changes

1. **Edit Presets**: Modify `log_viewer_presets.py`
2. **Regenerate**: Run the log viewer tool again
3. **Test in Browser**: Open the HTML file and test your presets
4. **Verify Ordering**: Check that columns appear in your preferred order

## Browser Features

### Interactive Elements
- **Drag Handle**: `⋮⋮` icon for dragging columns
- **Hover Effects**: Visual feedback during interaction
- **Live Updates**: Changes apply immediately
- **Search Integration**: Search works with any column order

### Visual Indicators
- **Info Box**: Shows drag-and-drop instructions
- **Active Preset**: Highlighted preset button
- **Column Status**: Checkboxes show visibility state

## Tips

1. **Start with a Preset**: Apply a preset close to what you want, then drag to fine-tune
2. **Use Timestamps First**: The default ordering puts timestamps first for temporal analysis
3. **Group Related Columns**: Drag related fields together for easier analysis
4. **Test-Specific Views**: Use the appropriate test preset (FWD/RTN/Setup) as a starting point
5. **Save Custom Presets**: Add frequently-used column combinations to the presets file

The column reordering is intuitive and responsive - just drag and drop to organize your data exactly how you want to analyze it!