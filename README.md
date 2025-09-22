# Test Report Generator

A modular Python package for generating HTML reports from RS ATS test results.

## Project Structure

The project has been refactored into a clean, modular OOP architecture:

```
report_generator/
├── main.py                     # Main entry point
├── __init__.py                # Package initialization
├── models.py                  # Data models and classes
├── parsers/                   # Parser modules
│   ├── __init__.py
│   ├── base_parser.py         # Abstract base parser
│   ├── test_result_parser.py  # Individual test result parser
│   └── setup_report_parser.py # Setup report parser
├── generators/                # Report generation modules
│   ├── __init__.py
│   ├── html_templates.py      # HTML templates
│   ├── html_report_generator.py # Individual report generator
│   └── index_generator.py     # Index page generator
├── services/                  # Business logic services
│   ├── __init__.py
│   └── report_service.py      # Main orchestrator service
└── test_report_generator.py   # Original monolithic file (legacy)
```

## Key Features

### Modular Design
- **Models**: Clean data classes for TestResult, SetupReport, etc.
- **Parsers**: Specialized parsers for different file types
- **Generators**: Separate HTML and PDF generation logic
- **Services**: High-level orchestration logic

### Dual Output Formats
- **HTML Reports**: Interactive reports with responsive design
- **PDF Reports**: Professional landscape PDFs optimized for wide tables
  - Uses A2 landscape format for maximum table width
  - ReportLab-based generation for reliable cross-platform support
  - Optimized styling for many columns and large datasets

### Object-Oriented Principles
- **Inheritance**: BaseParser provides common functionality
- **Encapsulation**: Each class has clear responsibilities
- **Polymorphism**: Different parsers implement the same interface
- **Single Responsibility**: Each class handles one specific task

### Improved Maintainability
- **Separation of Concerns**: Each module has a specific purpose
- **Easy Testing**: Individual components can be tested in isolation
- **Extensibility**: New parsers/generators can be added easily
- **Clean Interfaces**: Well-defined public APIs

## Usage

### Command Line
```bash
# Generate both HTML and PDF reports (default)
python main.py /path/to/test/results

# Generate only HTML reports (skip PDF)
python main.py /path/to/test/results --no-pdf

# With custom output directory
python main.py /path/to/test/results --output-dir ./reports

# Help
python main.py --help
```

### Programmatic Usage
```python
from services.report_service import ReportService
from pathlib import Path

# Create service instance
service = ReportService()

# Generate both HTML and PDF reports
input_dir = Path("output")
output_dir = Path("reports")
service.generate_reports(input_dir, output_dir)

# Generate only HTML reports
service.generate_reports(input_dir, output_dir, generate_pdf=False)
```

### Individual Components
```python
# Parse individual test results
from parsers.test_result_parser import TestResultParser
from pathlib import Path

parser = TestResultParser(Path("test_folder"))
test_result = parser.parse()

# Generate HTML report
from generators.html_report_generator import HTMLReportGenerator

html_generator = HTMLReportGenerator()
html_generator.generate_report(test_result, Path("output.html"))

# Generate PDF report
from generators.pdf_report_generator import PDFReportGenerator

pdf_generator = PDFReportGenerator()
pdf_generator.generate_report(test_result, Path("output.pdf"))
```

## Class Hierarchy

### Models
- `TestResult`: Represents individual test results
- `SetupReport`: Represents setup-level reports
- `LogEntry`: Represents log entries
- `TestSummary`: Represents test execution summaries

### Parsers
- `BaseParser`: Abstract base class for all parsers
  - `TestResultParser`: Parses individual test result files
  - `SetupReportParser`: Parses setup report.json files

### Generators
- `HTMLReportGenerator`: Generates individual HTML reports
- `PDFReportGenerator`: Generates individual PDF reports with landscape A2 format
- `IndexGenerator`: Generates HTML index pages with navigation
- `PDFIndexGenerator`: Generates PDF index pages with summary tables
- `HTMLTemplates`: Contains all HTML templates
- `PDFTemplates`: Contains PDF-optimized HTML templates

### Services
- `ReportService`: Main orchestrator that coordinates all components

## Benefits of the Refactored Design

1. **Maintainability**: Easier to modify and extend individual components
2. **Testability**: Each class can be unit tested independently
3. **Reusability**: Components can be used in different contexts
4. **Readability**: Clear separation makes the code easier to understand
5. **Extensibility**: New features can be added without modifying existing code
6. **Performance**: Better memory management with focused classes
7. **Error Handling**: Isolated error handling per component

## Migration from Legacy Code

The original `test_report_generator.py` file is preserved for reference. The new modular structure provides the same functionality with improved organization and maintainability.

Key improvements:
- ✅ Clean separation of concerns
- ✅ Proper OOP design patterns
- ✅ Easy to test individual components
- ✅ Better error handling and logging
- ✅ Extensible architecture for future features
- ✅ Type hints for better IDE support
- ✅ Comprehensive documentation
- ✅ Dual format output (HTML + PDF)
- ✅ Large landscape PDFs for wide tables (A2 format)
- ✅ Cross-platform PDF generation using ReportLab

## PDF Generation Features

### Large Page Format
- **A2 Landscape**: 594mm × 420mm (23.4" × 16.5") for maximum table width
- **Optimized for Wide Tables**: Handles many columns efficiently
- **Automatic Column Sizing**: Distributes space evenly while maintaining readability

### PDF-Specific Optimizations
- **Condensed Fonts**: Smaller font sizes to fit more data
- **Smart Truncation**: Long text values are intelligently truncated
- **Table Styling**: Professional borders, headers, and alternating row colors
- **Page Breaks**: Intelligent page breaks to avoid splitting critical content

### Cross-Platform Compatibility
- **ReportLab Backend**: Pure Python PDF generation (no external dependencies)
- **Fallback Support**: Graceful degradation if PDF libraries unavailable
- **Windows Compatible**: Works reliably on Windows without complex setup

## Dependencies

### Required
- `pathlib` (built-in)
- `json` (built-in)
- `argparse` (built-in)

### Optional (for PDF generation)
- `reportlab` - For PDF generation (recommended)
- `pdfkit` - Alternative PDF generation (requires wkhtmltopdf)

Install with:
```bash
pip install reportlab  # Recommended for PDF generation
```