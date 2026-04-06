#!/usr/bin/env python3
"""
Program to remove lines from an XBRL XML file based on QNames listed in removedItems.txt
"""

import re
import sys
from pathlib import Path


def load_removed_qnames(removed_items_file):
    """
    Load the QNames to remove from the removedItems.txt file.
    
    Args:
        removed_items_file: Path to the removedItems.txt file
        
    Returns:
        Set of QNames to remove
    """
    with open(removed_items_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Split by comma and strip whitespace
    qnames = [qname.strip() for qname in content.split(',')]
    return set(qnames)


def should_remove_line(line, qnames_to_remove):
    """
    Check if a line contains any of the QNames to remove.
    
    Args:
        line: The line to check
        qnames_to_remove: Set of QNames to search for
        
    Returns:
        True if the line should be removed, False otherwise
    """
    for qname in qnames_to_remove:
        # Create pattern to match the QName in XML tags
        # This matches both opening tags like <us-gaap:ElementName and closing tags
        pattern = f'<{re.escape(qname)}[\\s>]|</{re.escape(qname)}>'
        if re.search(pattern, line):
            return True
    return False


def remove_items_from_xbrl(input_file, output_file, qnames_to_remove):
    """
    Remove lines containing specified QNames from the XBRL file.
    
    Args:
        input_file: Path to input XBRL XML file
        output_file: Path to output XBRL XML file
        qnames_to_remove: Set of QNames to remove
    """
    removed_count = 0
    total_lines = 0
    
    with open(input_file, 'r', encoding='utf-8') as infile, \
         open(output_file, 'w', encoding='utf-8') as outfile:
        
        for line in infile:
            total_lines += 1
            if should_remove_line(line, qnames_to_remove):
                removed_count += 1
                print(f"Removing line {total_lines}: {line.strip()[:100]}...")
            else:
                outfile.write(line)
    
    print(f"\nProcessing complete!")
    print(f"Total lines processed: {total_lines}")
    print(f"Lines removed: {removed_count}")
    print(f"Lines kept: {total_lines - removed_count}")
    print(f"Output written to: {output_file}")


def main():
    """Main function"""
    # Default file paths
    removed_items_file = '/Users/campbellpryde/Documents/GitHub/xule/unitTests/output/taxRoll/conf/removedItems.txt'
    input_file = '/Users/campbellpryde/Downloads/TestCo-2026-NonNeg-WithNew.xml'
    output_file = '/Users/campbellpryde/Downloads/TestCo-2026-NonNeg-Cleaned.xml'
    
    # Allow command line arguments to override defaults
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
    if len(sys.argv) > 2:
        output_file = sys.argv[2]
    if len(sys.argv) > 3:
        removed_items_file = sys.argv[3]
    
    # Verify files exist
    if not Path(removed_items_file).exists():
        print(f"Error: removedItems file not found: {removed_items_file}")
        sys.exit(1)
    
    if not Path(input_file).exists():
        print(f"Error: Input XBRL file not found: {input_file}")
        sys.exit(1)
    
    print(f"Loading QNames from: {removed_items_file}")
    qnames_to_remove = load_removed_qnames(removed_items_file)
    print(f"Found {len(qnames_to_remove)} QNames to remove\n")
    
    print(f"Processing XBRL file: {input_file}")
    remove_items_from_xbrl(input_file, output_file, qnames_to_remove)


if __name__ == '__main__':
    main()
