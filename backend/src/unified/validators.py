#!/usr/bin/env python3
"""
Validation utilities to ensure code quality and prevent placeholders.
"""

import re
import ast
import inspect
from typing import Any, List, Optional, Callable
from functools import wraps
from pathlib import Path

# Import enforcement to ensure real systems
from .enforcement import EnforcementError, require_real_decorator

# Comprehensive list of banned words/patterns
BANNED_WORDS = [
    'test', 'demo', 'sample', 'example', 'placeholder',
    'todo', 'fixme', 'mock', 'fake', 'stub', 'dummy',
    'temp', 'tmp', 'foo', 'bar', 'baz', 'lorem', 'ipsum'
]

BANNED_EMAILS = [
    '@example.com', '@test.com', '@demo.com', '@sample.com',
    '@foo.com', '@bar.com', '@localhost', '@temp.com'
]

BANNED_PATHS = [
    '/tmp/', '/temp/', 'C:\\temp\\', 'C:\\tmp\\',
    '/test/', '/demo/', '/sample/', '/example/'
]

class CodeValidator:
    """Validate code for quality and compliance"""
    
    @staticmethod
    def scan_for_banned_words(code: str, context: str = "code") -> List[str]:
        """Scan code for banned placeholder words"""
        violations = []
        
        # Check for banned words (case-insensitive)
        for word in BANNED_WORDS:
            # Use word boundaries to avoid false positives
            pattern = rf'\b{word}\b'
            if re.search(pattern, code, re.IGNORECASE):
                # Skip if it's in a comment explaining not to use it
                if not re.search(rf'#.*no {word}|#.*never.*{word}', code, re.IGNORECASE):
                    violations.append(f"Found banned word '{word}' in {context}")
        
        # Check for banned email domains
        for email in BANNED_EMAILS:
            if email in code.lower():
                violations.append(f"Found banned email domain '{email}' in {context}")
        
        # Check for banned paths
        for path in BANNED_PATHS:
            if path.lower() in code.lower():
                violations.append(f"Found banned path '{path}' in {context}")
        
        # Check for specific patterns
        patterns = [
            (r'=\s*None\s*#.*later', "Found 'None # ...later' placeholder"),
            (r'pass\s*#.*implement', "Found 'pass # ...implement' placeholder"),
            (r'raise NotImplementedError', "Found NotImplementedError placeholder"),
            (r'return\s+\[\s*\].*#.*empty', "Found empty return placeholder"),
            (r'return\s+\{\s*\}.*#.*empty', "Found empty return placeholder"),
        ]
        
        for pattern, message in patterns:
            if re.search(pattern, code, re.IGNORECASE):
                violations.append(f"{message} in {context}")
        
        return violations
    
    @staticmethod
    def validate_no_mock_imports(code: str) -> List[str]:
        """Check for mock-related imports"""
        violations = []
        
        mock_imports = [
            'from unittest.mock import',
            'from mock import',
            'import mock',
            'from faker import',
            'import faker',
            'from factory import',
            'import factory'
        ]
        
        for mock_import in mock_imports:
            if mock_import in code:
                violations.append(f"Found mock import: {mock_import}")
        
        return violations
    
    @staticmethod
    def validate_message_id_format(message_id: str) -> bool:
        """Validate Usenet Message-ID format"""
        # Format: <unique-part@domain>
        pattern = r'^<[a-zA-Z0-9._-]+@[a-zA-Z0-9.-]+>$'
        
        if not re.match(pattern, message_id):
            raise ValueError(f"Invalid Message-ID format: {message_id}")
        
        # Check for test/demo patterns
        if any(banned in message_id.lower() for banned in ['test', 'demo', 'example']):
            raise ValueError(f"Message-ID contains banned word: {message_id}")
        
        return True
    
    @staticmethod
    def validate_share_id_format(share_id: str) -> bool:
        """Validate share ID format"""
        # Should be a real hash or UUID, not TEST-123
        if re.match(r'^(TEST|DEMO|SAMPLE|EXAMPLE)-', share_id, re.IGNORECASE):
            raise ValueError(f"Share ID looks like placeholder: {share_id}")
        
        # Should be at least 8 characters of random data
        if len(share_id) < 8:
            raise ValueError(f"Share ID too short: {share_id}")
        
        return True
    
    @staticmethod
    def validate_ast_node(node: ast.AST, filename: str = "unknown") -> List[str]:
        """Validate an AST node for compliance"""
        violations = []
        
        # Check for Mock/Fake/Stub class definitions
        if isinstance(node, ast.ClassDef):
            if any(banned in node.name for banned in ['Mock', 'Fake', 'Stub', 'Dummy']):
                if 'TestCase' not in node.name:  # Allow TestCase classes
                    violations.append(f"Class {node.name} appears to be a mock")
        
        # Check for random data generation
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Attribute):
                if (hasattr(node.func.value, 'id') and 
                    node.func.value.id == 'random' and 
                    node.func.attr in ['uniform', 'randint', 'random', 'choice']):
                    violations.append(f"Random data generation detected at line {node.lineno}")
        
        # Check for hardcoded test values in assignments
        if isinstance(node, ast.Assign):
            if isinstance(node.value, ast.Constant):
                value = str(node.value.value)
                if any(banned in value.lower() for banned in ['test', 'demo', 'example']):
                    violations.append(f"Hardcoded test value at line {node.lineno}: {value}")
        
        return violations

@require_real_decorator
def validate_implementation(func: Callable) -> Callable:
    """Decorator to ensure implementation is real, not mock"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Get function source
        try:
            source = inspect.getsource(func)
            
            # Check for banned words
            violations = CodeValidator.scan_for_banned_words(source, func.__name__)
            
            # Check for mock imports
            violations.extend(CodeValidator.validate_no_mock_imports(source))
            
            if violations:
                raise EnforcementError(
                    f"Function {func.__name__} contains violations:\n" + 
                    "\n".join(f"  - {v}" for v in violations)
                )
            
            # Parse AST for deeper checks
            tree = ast.parse(source)
            for node in ast.walk(tree):
                violations.extend(CodeValidator.validate_ast_node(node, func.__name__))
            
            if violations:
                raise EnforcementError(
                    f"Function {func.__name__} AST violations:\n" + 
                    "\n".join(f"  - {v}" for v in violations)
                )
                
        except (OSError, TypeError):
            # Can't get source for some functions
            pass
        
        # Execute the function
        result = func(*args, **kwargs)
        
        # Validate the result doesn't contain test data
        if isinstance(result, dict):
            for key, value in result.items():
                if isinstance(value, str):
                    if any(banned in value.lower() for banned in ['test@example.com', 'demo', '/tmp/test']):
                        raise EnforcementError(f"Function {func.__name__} returned test data: {value}")
        
        return result
    
    return wrapper

def validate_api_endpoint(request_data: dict) -> dict:
    """Validate API request doesn't contain forbidden fields"""
    # Check for email fields
    if 'email' in request_data:
        raise EnforcementError("Email field not allowed in API requests")
    
    # Check for permission fields
    if 'permissions' in request_data:
        if isinstance(request_data['permissions'], str):
            if request_data['permissions'] in ['read', 'write', 'admin']:
                raise EnforcementError("Permission levels not allowed - use binary access")
    
    # Check for test data in values
    for key, value in request_data.items():
        if isinstance(value, str):
            if any(banned in value.lower() for banned in BANNED_WORDS):
                raise EnforcementError(f"Request contains banned word in {key}: {value}")
    
    return request_data

def validate_database_schema(schema: str) -> bool:
    """Validate database schema doesn't include forbidden fields"""
    violations = []
    
    # Check for email columns
    if re.search(r'\bemail\s+\w+', schema, re.IGNORECASE):
        violations.append("Database schema contains email field")
    
    # Check for permission columns that suggest levels
    if re.search(r'permission.*VARCHAR.*read|write|admin', schema, re.IGNORECASE):
        violations.append("Database schema contains permission levels")
    
    # Check for test/demo tables
    if re.search(r'CREATE TABLE.*test_|demo_|sample_', schema, re.IGNORECASE):
        violations.append("Database schema contains test tables")
    
    if violations:
        raise EnforcementError("Schema violations:\n" + "\n".join(violations))
    
    return True

def validate_file_path(filepath: str) -> bool:
    """Validate file path is not a test/temp path"""
    path_lower = filepath.lower()
    
    # Check for temp/test paths
    if any(banned in path_lower for banned in ['/tmp/', '/temp/', 'test/', 'demo/']):
        raise EnforcementError(f"Path appears to be temporary/test: {filepath}")
    
    # Check file extension isn't .example, .sample, etc
    path = Path(filepath)
    if path.suffix in ['.example', '.sample', '.demo', '.test']:
        if path.name != '.env.example':  # Allow .env.example
            raise EnforcementError(f"File has placeholder extension: {filepath}")
    
    return True

# Self-test when imported
def _self_test():
    """Run self-test to ensure validators work"""
    try:
        # This should pass
        CodeValidator.validate_message_id_format("<1234567890.abcdef@newsserver.com>")
        
        # This should fail
        try:
            CodeValidator.validate_message_id_format("<TEST-123@example.com>")
            assert False, "Should have failed on TEST message ID"
        except ValueError:
            pass  # Expected
        
        # This should fail
        try:
            validate_file_path("/tmp/test/file.txt")
            assert False, "Should have failed on temp path"
        except EnforcementError:
            pass  # Expected
        
        return True
    except Exception as e:
        print(f"Validator self-test failed: {e}")
        return False

# Run self-test on import
if _self_test():
    print("✅ Validators loaded and self-tested successfully")
else:
    print("❌ Validator self-test failed")