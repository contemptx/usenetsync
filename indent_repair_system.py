#!/usr/bin/env python3
"""
Advanced Indentation Detection and Repair System for UsenetSync
Automatically detects and fixes indentation issues in Python files
"""

import os
import sys
import re
import ast
import shutil
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple, Optional, Set
from dataclasses import dataclass
from enum import Enum

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class IndentationType(Enum):
    """Types of indentation"""
    SPACES = "spaces"
    TABS = "tabs"
    MIXED = "mixed"
    INCONSISTENT = "inconsistent"

@dataclass
class IndentationIssue:
    """Represents an indentation issue"""
    line_number: int
    line_content: str
    issue_type: str
    expected_indent: int
    actual_indent: int
    severity: str  # 'error', 'warning', 'info'
    suggestion: str
    auto_fixable: bool = True

@dataclass
class FileAnalysis:
    """Analysis result for a file"""
    file_path: str
    indentation_type: IndentationType
    indent_size: int
    issues: List[IndentationIssue]
    total_lines: int
    fixable_issues: int
    syntax_valid: bool
    error_message: Optional[str] = None

class IndentationAnalyzer:
    """Analyzes Python files for indentation issues"""
    
    def __init__(self):
        self.keywords_requiring_indent = {
            'if', 'elif', 'else', 'for', 'while', 'try', 'except', 'finally',
            'with', 'def', 'class', 'async', 'match', 'case'
        }
        
        # Common indentation patterns
        self.common_indent_sizes = [2, 4, 8]
        self.preferred_indent_size = 4  # PEP 8 standard
        
    def analyze_file(self, file_path: str) -> FileAnalysis:
        """Comprehensive file analysis"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            lines = content.split('\n')
            issues = []
            
            # Detect indentation type and size
            indent_type, indent_size = self.detect_indentation_style(lines)
            
            # Check syntax validity first
            syntax_valid, syntax_error = self.check_syntax(content, file_path)
            
            # Analyze each line
            expected_indent_level = 0
            brace_stack = []
            in_multiline_string = False
            string_delimiter = None
            
            for line_num, line in enumerate(lines, 1):
                # Handle multiline strings
                in_multiline_string, string_delimiter = self.check_multiline_string(
                    line, in_multiline_string, string_delimiter
                )
                
                if in_multiline_string:
                    continue
                
                # Skip empty lines and comments
                stripped = line.strip()
                if not stripped or stripped.startswith('#'):
                    continue
                
                # Analyze this line
                line_issues = self.analyze_line(
                    line, line_num, expected_indent_level, indent_size, indent_type
                )
                issues.extend(line_issues)
                
                # Update expected indentation for next line
                expected_indent_level = self.calculate_next_indent_level(
                    line, expected_indent_level, brace_stack
                )
            
            return FileAnalysis(
                file_path=file_path,
                indentation_type=indent_type,
                indent_size=indent_size,
                issues=issues,
                total_lines=len(lines),
                fixable_issues=sum(1 for issue in issues if issue.auto_fixable),
                syntax_valid=syntax_valid,
                error_message=syntax_error
            )
            
        except Exception as e:
            return FileAnalysis(
                file_path=file_path,
                indentation_type=IndentationType.INCONSISTENT,
                indent_size=0,
                issues=[],
                total_lines=0,
                fixable_issues=0,
                syntax_valid=False,
                error_message=str(e)
            )
    
    def detect_indentation_style(self, lines: List[str]) -> Tuple[IndentationType, int]:
        """Detect the indentation style used in the file"""
        space_indents = []
        tab_indents = []
        mixed_lines = 0
        
        for line in lines:
            if not line.strip():
                continue
                
            # Count leading whitespace
            leading_spaces = len(line) - len(line.lstrip(' '))
            leading_tabs = len(line) - len(line.lstrip('\t'))
            
            # Check for mixed indentation on same line
            if leading_spaces > 0 and leading_tabs > 0:
                mixed_lines += 1
                continue
            
            if leading_spaces > 0:
                space_indents.append(leading_spaces)
            elif leading_tabs > 0:
                tab_indents.append(leading_tabs)
        
        # Determine predominant style
        if mixed_lines > 0:
            return IndentationType.MIXED, 0
        
        if space_indents and tab_indents:
            return IndentationType.INCONSISTENT, 0
        
        if tab_indents:
            return IndentationType.TABS, 1
        
        if space_indents:
            # Find most common indentation size
            indent_size = self.find_common_indent_size(space_indents)
            return IndentationType.SPACES, indent_size
        
        return IndentationType.SPACES, self.preferred_indent_size
    
    def find_common_indent_size(self, indents: List[int]) -> int:
        """Find the most common indentation size"""
        if not indents:
            return self.preferred_indent_size
        
        # Calculate differences between consecutive indentation levels
        diffs = []
        sorted_indents = sorted(set(indents))
        
        for i in range(1, len(sorted_indents)):
            diff = sorted_indents[i] - sorted_indents[i-1]
            if diff > 0:
                diffs.append(diff)
        
        if not diffs:
            return self.preferred_indent_size
        
        # Find GCD of all differences
        from math import gcd
        result = diffs[0]
        for diff in diffs[1:]:
            result = gcd(result, diff)
        
        # Validate against common sizes
        if result in self.common_indent_sizes:
            return result
        
        # Default to most common size in the file
        from collections import Counter
        counter = Counter(diffs)
        most_common = counter.most_common(1)[0][0]
        
        return most_common if most_common in self.common_indent_sizes else self.preferred_indent_size
    
    def check_syntax(self, content: str, file_path: str) -> Tuple[bool, Optional[str]]:
        """Check if the file has valid Python syntax"""
        try:
            ast.parse(content)
            return True, None
        except SyntaxError as e:
            return False, f"Syntax error at line {e.lineno}: {e.msg}"
        except Exception as e:
            return False, str(e)
    
    def check_multiline_string(self, line: str, in_multiline: bool, 
                             delimiter: Optional[str]) -> Tuple[bool, Optional[str]]:
        """Check if we're inside a multiline string"""
        if in_multiline:
            if delimiter in line:
                # Check if it's actually the end (not escaped)
                if line.count(delimiter) % 2 == 1:  # Odd number means it ends
                    return False, None
            return True, delimiter
        else:
            # Check for start of multiline string
            for delim in ['"""', "'''"]:
                if delim in line:
                    if line.count(delim) % 2 == 1:  # Odd number means it starts
                        return True, delim
            return False, None
    
    def analyze_line(self, line: str, line_num: int, expected_level: int, 
                    indent_size: int, indent_type: IndentationType) -> List[IndentationIssue]:
        """Analyze a single line for indentation issues"""
        issues = []
        stripped = line.strip()
        
        if not stripped or stripped.startswith('#'):
            return issues
        
        # Calculate actual indentation
        if indent_type == IndentationType.TABS:
            actual_indent = len(line) - len(line.lstrip('\t'))
            indent_char = '\t'
        else:
            actual_indent = len(line) - len(line.lstrip(' '))
            indent_char = ' '
        
        # Expected indentation in characters
        if indent_type == IndentationType.TABS:
            expected_indent = expected_level
        else:
            expected_indent = expected_level * indent_size
        
        # Check for mixed indentation
        if '\t' in line[:len(line) - len(line.lstrip())] and ' ' in line[:len(line) - len(line.lstrip())]:
            issues.append(IndentationIssue(
                line_number=line_num,
                line_content=line,
                issue_type="mixed_indentation",
                expected_indent=expected_indent,
                actual_indent=actual_indent,
                severity="error",
                suggestion=f"Use only {'tabs' if indent_type == IndentationType.TABS else 'spaces'} for indentation",
                auto_fixable=True
            ))
        
        # Check indentation level
        if actual_indent != expected_indent:
            # Special cases
            if self.is_continuation_line(line, stripped):
                # Continuation lines can have different indentation
                if actual_indent <= expected_indent:
                    issues.append(IndentationIssue(
                        line_number=line_num,
                        line_content=line,
                        issue_type="insufficient_continuation_indent",
                        expected_indent=expected_indent + indent_size,
                        actual_indent=actual_indent,
                        severity="warning",
                        suggestion=f"Continuation lines should be indented more than the base level",
                        auto_fixable=True
                    ))
            else:
                # Regular indentation error
                severity = "error"
                if abs(actual_indent - expected_indent) == 1:
                    severity = "warning"  # Minor off-by-one
                
                issues.append(IndentationIssue(
                    line_number=line_num,
                    line_content=line,
                    issue_type="incorrect_indentation",
                    expected_indent=expected_indent,
                    actual_indent=actual_indent,
                    severity=severity,
                    suggestion=f"Expected {expected_indent} {indent_char * expected_indent}, got {actual_indent}",
                    auto_fixable=True
                ))
        
        return issues
    
    def is_continuation_line(self, line: str, stripped: str) -> bool:
        """Check if this is a continuation line"""
        continuation_indicators = [
            '+', '-', '*', '/', '//', '%', '**', '<<', '>>', '&', '|', '^',
            'and', 'or', 'not', 'in', 'is', '==', '!=', '<', '>', '<=', '>=',
            '.', ',', '(', '[', '{'
        ]
        
        # Check if line starts with continuation operator
        for indicator in continuation_indicators:
            if stripped.startswith(indicator):
                return True
        
        return False
    
    def calculate_next_indent_level(self, line: str, current_level: int, 
                                  brace_stack: List[str]) -> int:
        """Calculate expected indentation level for the next line"""
        stripped = line.strip()
        
        # Handle opening braces/brackets
        for char in line:
            if char in '([{':
                brace_stack.append(char)
            elif char in ')]}':
                if brace_stack:
                    brace_stack.pop()
        
        # If we have unclosed braces, maintain current level
        if brace_stack:
            return current_level
        
        # Check for keywords that increase indentation
        if self.line_increases_indent(stripped):
            return current_level + 1
        
        # Check for keywords that decrease indentation
        if self.line_decreases_indent(stripped):
            return max(0, current_level - 1)
        
        return current_level
    
    def line_increases_indent(self, stripped_line: str) -> bool:
        """Check if line should increase indentation for next line"""
        if not stripped_line.endswith(':'):
            return False
        
        # Remove trailing colon and check for keywords
        line_without_colon = stripped_line[:-1].strip()
        
        # Simple keyword check
        for keyword in self.keywords_requiring_indent:
            if line_without_colon.startswith(keyword + ' ') or line_without_colon == keyword:
                return True
        
        # Check for function/class definitions
        if line_without_colon.startswith(('def ', 'class ', 'async def ')):
            return True
        
        return False
    
    def line_decreases_indent(self, stripped_line: str) -> bool:
        """Check if line should decrease indentation"""
        return stripped_line.startswith(('else:', 'elif ', 'except', 'except:', 'finally:'))

class IndentationRepairer:
    """Repairs indentation issues in Python files"""
    
    def __init__(self, analyzer: IndentationAnalyzer):
        self.analyzer = analyzer
        
    def repair_file(self, file_path: str, backup: bool = True, 
                   force_style: Optional[IndentationType] = None,
                   force_size: Optional[int] = None) -> Dict:
        """Repair indentation issues in a file"""
        try:
            # Analyze the file first
            analysis = self.analyzer.analyze_file(file_path)
            
            if not analysis.issues:
                return {
                    'success': True,
                    'message': 'No indentation issues found',
                    'changes_made': 0,
                    'backup_created': False
                }
            
            # Create backup if requested
            backup_path = None
            if backup:
                backup_path = self.create_backup(file_path)
            
            # Read the file
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Determine target indentation style
            target_type = force_style or IndentationType.SPACES
            target_size = force_size or self.analyzer.preferred_indent_size
            
            if analysis.indentation_type == IndentationType.MIXED or analysis.indentation_type == IndentationType.INCONSISTENT:
                # Convert entire file to consistent style
                repaired_lines = self.convert_indentation_style(lines, target_type, target_size)
                changes_made = len([line for line in repaired_lines if line != lines[repaired_lines.index(line)]])
            else:
                # Fix specific issues
                repaired_lines, changes_made = self.fix_specific_issues(lines, analysis.issues, target_type, target_size)
            
            # Write the repaired file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(repaired_lines)
            
            # Verify the repair worked
            verification = self.verify_repair(file_path)
            
            return {
                'success': True,
                'message': f'Repaired {changes_made} indentation issues',
                'changes_made': changes_made,
                'backup_created': backup_path is not None,
                'backup_path': backup_path,
                'verification': verification
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Failed to repair file: {str(e)}',
                'changes_made': 0,
                'backup_created': False
            }
    
    def create_backup(self, file_path: str) -> str:
        """Create a backup of the file"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = f"{file_path}.backup_{timestamp}"
        shutil.copy2(file_path, backup_path)
        return backup_path
    
    def convert_indentation_style(self, lines: List[str], target_type: IndentationType, 
                                target_size: int) -> List[str]:
        """Convert entire file to consistent indentation style"""
        repaired_lines = []
        
        for line in lines:
            if not line.strip():
                repaired_lines.append(line)
                continue
            
            # Calculate current indentation level
            content = line.lstrip()
            if not content:
                repaired_lines.append(line)
                continue
            
            # Count leading whitespace
            leading_spaces = len(line) - len(line.lstrip(' '))
            leading_tabs = len(line) - len(line.lstrip('\t'))
            
            # Determine indent level
            if leading_tabs > 0:
                indent_level = leading_tabs
            else:
                indent_level = leading_spaces // max(1, target_size)
            
            # Apply target indentation
            if target_type == IndentationType.TABS:
                new_line = '\t' * indent_level + content
            else:
                new_line = ' ' * (indent_level * target_size) + content
            
            repaired_lines.append(new_line)
        
        return repaired_lines
    
    def fix_specific_issues(self, lines: List[str], issues: List[IndentationIssue],
                          target_type: IndentationType, target_size: int) -> Tuple[List[str], int]:
        """Fix specific indentation issues"""
        repaired_lines = lines.copy()
        changes_made = 0
        
        # Sort issues by line number (descending to avoid index shifting)
        sorted_issues = sorted(issues, key=lambda x: x.line_number, reverse=True)
        
        for issue in sorted_issues:
            if not issue.auto_fixable:
                continue
            
            line_index = issue.line_number - 1
            if line_index >= len(repaired_lines):
                continue
            
            line = repaired_lines[line_index]
            content = line.lstrip()
            
            if not content:
                continue
            
            # Calculate correct indentation
            if target_type == IndentationType.TABS:
                expected_chars = issue.expected_indent
                new_indent = '\t' * expected_chars
            else:
                new_indent = ' ' * issue.expected_indent
            
            # Apply the fix
            new_line = new_indent + content
            
            if new_line != line:
                repaired_lines[line_index] = new_line
                changes_made += 1
        
        return repaired_lines, changes_made
    
    def verify_repair(self, file_path: str) -> Dict:
        """Verify that the repair was successful"""
        try:
            # Re-analyze the file
            new_analysis = self.analyzer.analyze_file(file_path)
            
            return {
                'syntax_valid': new_analysis.syntax_valid,
                'remaining_issues': len(new_analysis.issues),
                'indentation_consistent': new_analysis.indentation_type not in [
                    IndentationType.MIXED, IndentationType.INCONSISTENT
                ],
                'error_message': new_analysis.error_message
            }
        except Exception as e:
            return {
                'syntax_valid': False,
                'remaining_issues': -1,
                'indentation_consistent': False,
                'error_message': str(e)
            }

class BatchIndentationRepairer:
    """Repair indentation issues across multiple files"""
    
    def __init__(self):
        self.analyzer = IndentationAnalyzer()
        self.repairer = IndentationRepairer(self.analyzer)
        
    def scan_directory(self, directory: str, recursive: bool = True) -> List[str]:
        """Scan directory for Python files"""
        python_files = []
        path = Path(directory)
        
        if recursive:
            python_files = list(path.rglob('*.py'))
        else:
            python_files = list(path.glob('*.py'))
        
        return [str(f) for f in python_files]
    
    def analyze_project(self, directory: str, recursive: bool = True) -> Dict:
        """Analyze entire project for indentation issues"""
        files = self.scan_directory(directory, recursive)
        results = {
            'total_files': len(files),
            'files_with_issues': 0,
            'total_issues': 0,
            'fixable_issues': 0,
            'file_analyses': [],
            'summary_by_type': {}
        }
        
        issue_types = {}
        
        for file_path in files:
            try:
                analysis = self.analyzer.analyze_file(file_path)
                results['file_analyses'].append(analysis)
                
                if analysis.issues:
                    results['files_with_issues'] += 1
                    results['total_issues'] += len(analysis.issues)
                    results['fixable_issues'] += analysis.fixable_issues
                    
                    # Count issue types
                    for issue in analysis.issues:
                        issue_type = issue.issue_type
                        if issue_type not in issue_types:
                            issue_types[issue_type] = 0
                        issue_types[issue_type] += 1
                        
            except Exception as e:
                logger.error(f"Failed to analyze {file_path}: {e}")
        
        results['summary_by_type'] = issue_types
        return results
    
    def repair_project(self, directory: str, recursive: bool = True, 
                      backup: bool = True, dry_run: bool = False) -> Dict:
        """Repair indentation issues across entire project"""
        files = self.scan_directory(directory, recursive)
        results = {
            'total_files': len(files),
            'files_processed': 0,
            'files_repaired': 0,
            'total_changes': 0,
            'errors': [],
            'file_results': []
        }
        
        for file_path in files:
            try:
                if dry_run:
                    # Just analyze, don't repair
                    analysis = self.analyzer.analyze_file(file_path)
                    file_result = {
                        'file': file_path,
                        'issues_found': len(analysis.issues),
                        'would_repair': analysis.fixable_issues > 0,
                        'dry_run': True
                    }
                else:
                    # Actually repair
                    repair_result = self.repairer.repair_file(file_path, backup)
                    file_result = {
                        'file': file_path,
                        'success': repair_result['success'],
                        'changes_made': repair_result['changes_made'],
                        'backup_created': repair_result.get('backup_created', False)
                    }
                    
                    if repair_result['success'] and repair_result['changes_made'] > 0:
                        results['files_repaired'] += 1
                        results['total_changes'] += repair_result['changes_made']
                
                results['file_results'].append(file_result)
                results['files_processed'] += 1
                
            except Exception as e:
                error_msg = f"Failed to process {file_path}: {str(e)}"
                results['errors'].append(error_msg)
                logger.error(error_msg)
        
        return results

def main():
    """Main function for command-line usage"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Python Indentation Repair System')
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Analyze command
    analyze_parser = subparsers.add_parser('analyze', help='Analyze files for indentation issues')
    analyze_parser.add_argument('path', help='File or directory to analyze')
    analyze_parser.add_argument('--recursive', '-r', action='store_true', help='Recursive directory scan')
    
    # Repair command
    repair_parser = subparsers.add_parser('repair', help='Repair indentation issues')
    repair_parser.add_argument('path', help='File or directory to repair')
    repair_parser.add_argument('--recursive', '-r', action='store_true', help='Recursive directory scan')
    repair_parser.add_argument('--no-backup', action='store_true', help='Do not create backups')
    repair_parser.add_argument('--dry-run', action='store_true', help='Show what would be repaired')
    repair_parser.add_argument('--force-spaces', action='store_true', help='Force spaces indentation')
    repair_parser.add_argument('--force-tabs', action='store_true', help='Force tabs indentation')
    repair_parser.add_argument('--indent-size', type=int, default=4, help='Indentation size for spaces')
    
    # Check command
    check_parser = subparsers.add_parser('check', help='Quick check for indentation issues')
    check_parser.add_argument('file', help='File to check')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    try:
        if args.command == 'analyze':
            batch_repairer = BatchIndentationRepairer()
            
            if Path(args.path).is_file():
                analysis = batch_repairer.analyzer.analyze_file(args.path)
                print(f"File: {analysis.file_path}")
                print(f"Indentation: {analysis.indentation_type.value} (size: {analysis.indent_size})")
                print(f"Issues found: {len(analysis.issues)}")
                print(f"Fixable: {analysis.fixable_issues}")
                
                if analysis.issues:
                    print("\nIssues:")
                    for issue in analysis.issues:
                        print(f"  Line {issue.line_number}: {issue.issue_type} - {issue.suggestion}")
            else:
                results = batch_repairer.analyze_project(args.path, args.recursive)
                print(f"Analyzed {results['total_files']} files")
                print(f"Files with issues: {results['files_with_issues']}")
                print(f"Total issues: {results['total_issues']}")
                print(f"Fixable issues: {results['fixable_issues']}")
                
                if results['summary_by_type']:
                    print("\nIssue types:")
                    for issue_type, count in results['summary_by_type'].items():
                        print(f"  {issue_type}: {count}")
        
        elif args.command == 'repair':
            batch_repairer = BatchIndentationRepairer()
            
            if Path(args.path).is_file():
                force_style = None
                if args.force_spaces:
                    force_style = IndentationType.SPACES
                elif args.force_tabs:
                    force_style = IndentationType.TABS
                
                result = batch_repairer.repairer.repair_file(
                    args.path, 
                    backup=not args.no_backup,
                    force_style=force_style,
                    force_size=args.indent_size
                )
                
                if result['success']:
                    print(f"Repaired {result['changes_made']} issues in {args.path}")
                    if result['backup_created']:
                        print(f"Backup created: {result['backup_path']}")
                else:
                    print(f"Failed to repair: {result['message']}")
            else:
                results = batch_repairer.repair_project(
                    args.path, 
                    args.recursive, 
                    backup=not args.no_backup,
                    dry_run=args.dry_run
                )
                
                if args.dry_run:
                    print(f"Would process {results['files_processed']} files")
                    would_repair = sum(1 for r in results['file_results'] if r.get('would_repair', False))
                    print(f"Would repair {would_repair} files")
                else:
                    print(f"Processed {results['files_processed']} files")
                    print(f"Repaired {results['files_repaired']} files")
                    print(f"Total changes: {results['total_changes']}")
                
                if results['errors']:
                    print(f"\nErrors: {len(results['errors'])}")
                    for error in results['errors']:
                        print(f"  {error}")
        
        elif args.command == 'check':
            analyzer = IndentationAnalyzer()
            analysis = analyzer.analyze_file(args.file)
            
            if analysis.syntax_valid:
                if analysis.issues:
                    print(f"Found {len(analysis.issues)} indentation issues")
                    sys.exit(1)
                else:
                    print("No indentation issues found")
                    sys.exit(0)
            else:
                print(f"Syntax error: {analysis.error_message}")
                sys.exit(2)
    
    except KeyboardInterrupt:
        print("\nOperation cancelled")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
