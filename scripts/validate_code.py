#!/usr/bin/env python3
"""
Auto-reject code with violations.
Run this before committing or in CI/CD pipeline.
"""

import sys
import os
import re
from pathlib import Path
from typing import List, Tuple

# Add backend/src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend', 'src'))

from unified.enforcement import RealSystemEnforcer, EnforcementError
from unified.validators import CodeValidator

class CodeReviewer:
    """Automated code review for compliance"""
    
    def __init__(self):
        self.violations = []
        self.warnings = []
        
    def review_file(self, filepath: Path) -> Tuple[str, List[str]]:
        """Review a single file for violations"""
        if not filepath.exists():
            return "SKIPPED", [f"File not found: {filepath}"]
        
        # Skip non-Python files
        if filepath.suffix != '.py':
            return "SKIPPED", ["Not a Python file"]
        
        violations = []
        
        try:
            with open(filepath, 'r') as f:
                content = f.read()
            
            # Check with enforcement module
            violations.extend(
                RealSystemEnforcer.scan_code(content, str(filepath))
            )
            
            # Check with validators
            violations.extend(
                CodeValidator.scan_for_banned_words(content, str(filepath))
            )
            
            violations.extend(
                CodeValidator.validate_no_mock_imports(content)
            )
            
            # Specific checks
            
            # Check for Mock/Fake classes
            if re.search(r'class\s+(Mock|Fake|Stub|Test)\w+', content):
                if 'TestCase' not in content:
                    violations.append("Mock/Fake/Stub class detected")
            
            # Check for random data
            if 'random.uniform' in content or 'random.randint' in content:
                violations.append("Random data generation detected")
            
            # Check for example emails
            if '@example.com' in content or 'test@' in content:
                violations.append("Example email detected")
            
            # Check for test paths
            if '/tmp/test' in content or r'C:\temp\test' in content:
                violations.append("Test path detected")
            
            # Check for TODO/FIXME
            if 'TODO' in content or 'FIXME' in content:
                violations.append("TODO/FIXME comment found")
            
            if violations:
                return "REJECTED", violations
            else:
                return "APPROVED", []
                
        except Exception as e:
            return "ERROR", [f"Failed to review: {e}"]
    
    def review_directory(self, directory: Path) -> dict:
        """Review all Python files in directory"""
        results = {
            'approved': [],
            'rejected': [],
            'skipped': [],
            'errors': []
        }
        
        for filepath in directory.rglob('*.py'):
            # Skip virtual environment
            if 'venv' in filepath.parts or '.venv' in filepath.parts:
                continue
            
            # Skip __pycache__
            if '__pycache__' in filepath.parts:
                continue
            
            status, violations = self.review_file(filepath)
            
            if status == "APPROVED":
                results['approved'].append(str(filepath))
            elif status == "REJECTED":
                results['rejected'].append({
                    'file': str(filepath),
                    'violations': violations
                })
            elif status == "SKIPPED":
                results['skipped'].append(str(filepath))
            else:  # ERROR
                results['errors'].append({
                    'file': str(filepath),
                    'error': violations
                })
        
        return results
    
    def print_report(self, results: dict):
        """Print a formatted report"""
        print("\n" + "="*60)
        print("CODE REVIEW REPORT")
        print("="*60)
        
        # Summary
        total_files = (len(results['approved']) + len(results['rejected']) + 
                      len(results['skipped']) + len(results['errors']))
        
        print(f"\nTotal files reviewed: {total_files}")
        print(f"✅ Approved: {len(results['approved'])}")
        print(f"❌ Rejected: {len(results['rejected'])}")
        print(f"⏭️  Skipped: {len(results['skipped'])}")
        print(f"⚠️  Errors: {len(results['errors'])}")
        
        # Detailed violations
        if results['rejected']:
            print("\n" + "="*60)
            print("VIOLATIONS FOUND")
            print("="*60)
            
            for item in results['rejected']:
                print(f"\n❌ {item['file']}")
                for violation in item['violations']:
                    print(f"   - {violation}")
        
        # Errors
        if results['errors']:
            print("\n" + "="*60)
            print("ERRORS")
            print("="*60)
            
            for item in results['errors']:
                print(f"\n⚠️  {item['file']}")
                for error in item['error']:
                    print(f"   - {error}")
        
        # Final verdict
        print("\n" + "="*60)
        if results['rejected'] or results['errors']:
            print("❌ CODE REJECTED - Fix violations before committing")
            return False
        else:
            print("✅ CODE APPROVED - No violations found")
            return True

def main():
    """Main entry point"""
    reviewer = CodeReviewer()
    
    # Check command line arguments
    if len(sys.argv) > 1:
        # Review specific files
        for filepath in sys.argv[1:]:
            path = Path(filepath)
            if path.is_dir():
                results = reviewer.review_directory(path)
                success = reviewer.print_report(results)
            else:
                status, violations = reviewer.review_file(path)
                print(f"\n{path}: {status}")
                if violations:
                    for v in violations:
                        print(f"  - {v}")
                success = (status == "APPROVED")
    else:
        # Review entire backend
        backend_dir = Path(__file__).parent.parent / 'backend' / 'src'
        results = reviewer.review_directory(backend_dir)
        success = reviewer.print_report(results)
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()