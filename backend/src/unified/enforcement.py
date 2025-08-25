#!/usr/bin/env python3
"""
Enforcement utilities to prevent mock usage and ensure real systems.
This module is imported by all other modules to enforce standards.
"""

import os
import sys
import re
import inspect
from typing import Any, Callable, List, Optional
from functools import wraps

class EnforcementError(Exception):
    """Raised when enforcement rules are violated"""
    pass

class RealSystemEnforcer:
    """Enforce real system usage throughout the application"""
    
    # Banned patterns that indicate mocks or placeholders
    BANNED_PATTERNS = [
        r'\btest@example\.com\b',
        r'\buser@example\.com\b',
        r'/tmp/test\b',
        r'C:\\temp\\test\b',
        r'\bTODO\b',
        r'\bFIXME\b',
        r'class\s+Mock',
        r'class\s+Fake',
        r'class\s+Stub',
        r'class\s+Test(?!Case)',  # Allow TestCase
        r'random\.uniform',
        r'random\.randint',
        r"'test'",
        r'"test"',
        r'\bplaceholder\b',
        r'\bdemo_',
        r'\bsample_',
        r'\bDEMO-',
        r'\bTEST-',
        r'example\.com',
        r'foo@bar',
        r'lorem\s+ipsum',
    ]
    
    @classmethod
    def require_real(cls) -> bool:
        """Ensure real systems are being used"""
        # Check environment flags
        if os.getenv('ALLOW_MOCKS', 'false').lower() == 'true':
            raise EnforcementError("MOCKS ARE NOT ALLOWED - Set ALLOW_MOCKS=false")
        
        # Check NNTP is real
        nntp_server = os.getenv('NNTP_SERVER', '')
        if not nntp_server or 'example' in nntp_server or 'test' in nntp_server:
            raise EnforcementError(f"Must use real NNTP server, not: {nntp_server}")
        
        if not nntp_server.startswith(('news.', 'nntp.', 'eu.news.', 'us.news.')):
            raise EnforcementError(f"NNTP server doesn't look real: {nntp_server}")
        
        # Check database is real
        db_path = os.getenv('DB_PATH', '')
        if ':memory:' in db_path:
            raise EnforcementError("In-memory database not allowed")
        
        if 'test' in db_path.lower() and 'unittest' not in sys.argv[0]:
            raise EnforcementError(f"Test database detected: {db_path}")
        
        # Check storage paths are real
        storage_path = os.getenv('STORAGE_PATH', '')
        if '/tmp' in storage_path or 'temp' in storage_path.lower():
            raise EnforcementError(f"Temporary storage not allowed: {storage_path}")
        
        return True
    
    @classmethod
    def scan_code(cls, code: str, filename: str = "unknown") -> List[str]:
        """Scan code for banned patterns"""
        violations = []
        
        for pattern in cls.BANNED_PATTERNS:
            matches = re.finditer(pattern, code, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                # Get line number
                line_num = code[:match.start()].count('\n') + 1
                violations.append(
                    f"{filename}:{line_num} - Found banned pattern: {match.group()}"
                )
        
        # Check for email fields in API endpoints
        email_pattern = r'email.*=.*request\.(get|json)'
        if re.search(email_pattern, code):
            violations.append(f"{filename} - Email field in API endpoint")
        
        # Check for permission levels
        perm_pattern = r'permission.*=.*(read|write|admin)'
        if re.search(perm_pattern, code, re.IGNORECASE):
            violations.append(f"{filename} - Permission levels detected (use binary access)")
        
        # Check for mock imports
        if 'from unittest.mock import' in code or 'import mock' in code:
            violations.append(f"{filename} - Mock imports detected")
        
        return violations
    
    @classmethod
    def validate_function(cls, func: Callable) -> Callable:
        """Decorator to validate function implementation"""
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Get function source
            try:
                source = inspect.getsource(func)
                violations = cls.scan_code(source, func.__name__)
                
                if violations:
                    raise EnforcementError(
                        f"Function {func.__name__} contains violations:\n" + 
                        "\n".join(violations)
                    )
            except OSError:
                # Can't get source for built-in functions
                pass
            
            return func(*args, **kwargs)
        
        return wrapper
    
    @classmethod
    def validate_class(cls, target_class: type) -> type:
        """Decorator to validate class implementation"""
        # Check class name
        if any(banned in target_class.__name__ for banned in ['Mock', 'Fake', 'Stub', 'Test']):
            if 'TestCase' not in target_class.__name__:
                raise EnforcementError(f"Class name suggests mock: {target_class.__name__}")
        
        # Check class source
        try:
            source = inspect.getsource(target_class)
            violations = cls.scan_code(source, target_class.__name__)
            
            if violations:
                raise EnforcementError(
                    f"Class {target_class.__name__} contains violations:\n" + 
                    "\n".join(violations)
                )
        except OSError:
            pass
        
        return target_class

class UsenetCorrectnessChecker:
    """Enforce Usenet one-way communication rules"""
    
    @staticmethod
    def validate_message_id(message_id: str, operation: str) -> bool:
        """Message-IDs must be client-generated"""
        if not message_id:
            raise EnforcementError("Message-ID is required")
        
        if operation == "POST" and not message_id:
            raise EnforcementError("Client must generate Message-ID before posting")
        
        if message_id.startswith(("server-", "auto-", "generated-")):
            raise EnforcementError("Message-ID must be client-generated, not server-assigned")
        
        # Validate format: <timestamp.random@domain>
        if not re.match(r'^<[\w.-]+@[\w.-]+>$', message_id):
            raise EnforcementError(f"Invalid Message-ID format: {message_id}")
        
        return True
    
    @staticmethod
    def validate_operation(operation: str) -> bool:
        """Only append operations allowed"""
        forbidden_ops = ["EDIT", "DELETE", "UPDATE", "MODIFY", "REPLACE"]
        if operation.upper() in forbidden_ops:
            raise EnforcementError(
                f"Operation {operation} not allowed - Usenet is append-only"
            )
        return True
    
    @staticmethod
    def validate_retry(message_id: str, previous_id: str) -> bool:
        """Retries must use same Message-ID for idempotency"""
        if message_id != previous_id:
            raise EnforcementError(
                "Retries must be idempotent - use same Message-ID"
            )
        return True
    
    @staticmethod
    def validate_access(user_has_key: bool, permission_level: Optional[str] = None) -> bool:
        """Binary access - no permission levels"""
        if permission_level is not None:
            raise EnforcementError(
                "Permission levels not allowed - Usenet uses binary access (encrypted or not)"
            )
        return user_has_key  # Simple binary check
    
    @staticmethod
    def validate_no_email(data: dict) -> bool:
        """Ensure no email fields in data"""
        if 'email' in data:
            raise EnforcementError("Email fields not allowed in Usenet context")
        
        # Check nested dictionaries
        for value in data.values():
            if isinstance(value, dict) and 'email' in value:
                raise EnforcementError("Email fields not allowed in nested data")
        
        return True

def require_real_decorator(func: Callable) -> Callable:
    """Decorator to ensure function uses real systems"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        RealSystemEnforcer.require_real()
        return RealSystemEnforcer.validate_function(func)(*args, **kwargs)
    return wrapper

def validate_no_mocks(filepath: str) -> bool:
    """Validate a file contains no mocks or placeholders"""
    with open(filepath, 'r') as f:
        content = f.read()
    
    violations = RealSystemEnforcer.scan_code(content, filepath)
    
    if violations:
        print(f"❌ Violations found in {filepath}:")
        for violation in violations:
            print(f"  - {violation}")
        return False
    
    print(f"✅ {filepath} is clean")
    return True

# Auto-run enforcement when module is imported
if __name__ != "__main__":
    try:
        RealSystemEnforcer.require_real()
        print("✅ Enforcement module loaded - real systems required")
    except EnforcementError as e:
        print(f"❌ Enforcement check failed: {e}")
        sys.exit(1)

# Command-line validation
if __name__ == "__main__":
    if len(sys.argv) > 1:
        for filepath in sys.argv[1:]:
            validate_no_mocks(filepath)
    else:
        print("Enforcement module active")
        print("Checking environment...")
        try:
            RealSystemEnforcer.require_real()
            print("✅ All enforcement checks passed")
        except EnforcementError as e:
            print(f"❌ {e}")
            sys.exit(1)