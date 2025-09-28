#!/usr/bin/env python3
"""
Cleanup script to remove duplicate failure sections from viewer HTML files.
"""

import re
from pathlib import Path


def clean_duplicate_failure_sections(html_path):
    """Remove duplicate failure sections from HTML file."""
    with open(html_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Pattern to match failure sections
    failure_section_pattern = r'<div class="failure-section"[^>]*>.*?</div>'
    
    # Find all failure sections
    matches = list(re.finditer(failure_section_pattern, content, flags=re.DOTALL))
    
    if len(matches) > 1:
        print(f"Found {len(matches)} duplicate failure sections in {html_path}")
        
        # Keep only the first failure section
        first_match = matches[0]
        
        # Remove all duplicate sections
        cleaned_content = content
        for match in reversed(matches[1:]):  # Reverse to maintain indices
            start, end = match.span()
            cleaned_content = cleaned_content[:start] + cleaned_content[end:]
        
        # Write the cleaned content back
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(cleaned_content)
        
        print(f"  Removed {len(matches) - 1} duplicate failure sections")
        return True
    
    return False


def main():
    """Main function to clean all viewer files."""
    base_dir = Path(__file__).parent
    
    # Look for all viewer HTML files
    viewer_files = list(base_dir.glob('output/**/*_viewer.html'))
    
    print(f"Found {len(viewer_files)} viewer files")
    
    cleaned_count = 0
    for html_path in viewer_files:
        if clean_duplicate_failure_sections(html_path):
            cleaned_count += 1
    
    print(f"Cleaned {cleaned_count} files with duplicate failure sections")


if __name__ == "__main__":
    main()