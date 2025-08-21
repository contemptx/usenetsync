#!/usr/bin/env python3
"""
Security Audit System for UsenetSync
Comprehensive security scanning, vulnerability detection, and compliance checking
"""

import os
import sys
import re
import ast
import json
import hashlib
import subprocess
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass, asdict
from enum import Enum
import secrets
import base64

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class VulnerabilityLevel(Enum):
    """Vulnerability severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class SecurityCategory(Enum):
    """Security issue categories"""
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    ENCRYPTION = "encryption"
    INPUT_VALIDATION = "input_validation"
    CODE_INJECTION = "code_injection"
    INFORMATION_DISCLOSURE = "information_disclosure"
    CRYPTOGRAPHY = "cryptography"
    CONFIGURATION = "configuration"
    DEPENDENCIES = "dependencies"
    DATA_PROTECTION = "data_protection"

@dataclass
class SecurityIssue:
    """Security vulnerability or issue"""
    id: str
    title: str
    description: str
    level: VulnerabilityLevel
    category: SecurityCategory
    file_path: str
    line_number: Optional[int]
    code_snippet: Optional[str]
    recommendation: str
    cwe_id: Optional[str] = None  # Common Weakness Enumeration
    cvss_score: Optional[float] = None
    auto_fixable: bool = False

@dataclass
class SecurityScanResult:
    """Result of security scan"""
    scan_id: str
    timestamp: datetime
    total_files_scanned: int
    total_issues: int
    issues_by_level: Dict[str, int]
    issues_by_category: Dict[str, int]
    issues: List[SecurityIssue]
    scan_duration: float
    compliance_score: float

class SecurityPatterns:
    """Security vulnerability patterns"""
    
    def __init__(self):
        self.patterns = {
            # Hardcoded credentials
            'hardcoded_password': {
                'pattern': r'(?i)(password|pwd|pass|secret|key|token)\s*[=:]\s*["\'][^"\']{3,}["\']',
                'level': VulnerabilityLevel.HIGH,
                'category': SecurityCategory.AUTHENTICATION,
                'description': 'Hardcoded password or secret detected'
            },
            
            # SQL Injection
            'sql_injection': {
                'pattern': r'(?i)(execute|query|select|insert|update|delete)\s*\(\s*["\'].*%.*["\']',
                'level': VulnerabilityLevel.HIGH,
                'category': SecurityCategory.CODE_INJECTION,
                'description': 'Potential SQL injection vulnerability'
            },
            
            # Command Injection
            'command_injection': {
                'pattern': r'(?i)(os\.system|subprocess\.call|subprocess\.run|subprocess\.Popen)\s*\([^)]*\+',
                'level': VulnerabilityLevel.HIGH,
                'category': SecurityCategory.CODE_INJECTION,
                'description': 'Potential command injection vulnerability'
            },
            
            # Weak Random
            'weak_random': {
                'pattern': r'(?i)random\.(random|randint|choice)',
                'level': VulnerabilityLevel.MEDIUM,
                'category': SecurityCategory.CRYPTOGRAPHY,
                'description': 'Use of weak random number generator for security purposes'
            },
            
            # Insecure Hash
            'insecure_hash': {
                'pattern': r'(?i)hashlib\.(md5|sha1)\(',
                'level': VulnerabilityLevel.MEDIUM,
                'category': SecurityCategory.CRYPTOGRAPHY,
                'description': 'Use of insecure hash algorithm'
            },
            
            # Debug Mode
            'debug_mode': {
                'pattern': r'(?i)debug\s*=\s*True',
                'level': VulnerabilityLevel.MEDIUM,
                'category': SecurityCategory.CONFIGURATION,
                'description': 'Debug mode enabled in production code'
            },
            
            # Insecure URL
            'insecure_url': {
                'pattern': r'http://[^\s\'"]+',
                'level': VulnerabilityLevel.LOW,
                'category': SecurityCategory.DATA_PROTECTION,
                'description': 'Insecure HTTP URL detected'
            },
            
            # Private Key
            'private_key': {
                'pattern': r'-----BEGIN\s+(RSA\s+)?PRIVATE\s+KEY-----',
                'level': VulnerabilityLevel.CRITICAL,
                'category': SecurityCategory.CRYPTOGRAPHY,
                'description': 'Private key embedded in code'
            },
            
            # API Key
            'api_key': {
                'pattern': r'(?i)(api[_-]?key|apikey|access[_-]?token)\s*[=:]\s*["\'][A-Za-z0-9]{20,}["\']',
                'level': VulnerabilityLevel.HIGH,
                'category': SecurityCategory.AUTHENTICATION,
                'description': 'API key or access token hardcoded'
            },
            
            # Unsafe Deserialization
            'unsafe_deserialization': {
                'pattern': r'(?i)(pickle\.loads?|yaml\.load|eval|exec)\(',
                'level': VulnerabilityLevel.HIGH,
                'category': SecurityCategory.CODE_INJECTION,
                'description': 'Potentially unsafe deserialization'
            }
        }
    
    def get_all_patterns(self) -> Dict[str, Dict]:
        """Get all security patterns"""
        return self.patterns

class CodeAnalyzer:
    """Analyzes code for security issues"""
    
    def __init__(self):
        self.patterns = SecurityPatterns()
        
    def analyze_file(self, file_path: str) -> List[SecurityIssue]:
        """Analyze a single file for security issues"""
        issues = []
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            lines = content.split('\n')
            
            # Pattern-based analysis
            issues.extend(self.pattern_analysis(file_path, content, lines))
            
            # AST-based analysis for Python files
            if file_path.endswith('.py'):
                issues.extend(self.ast_analysis(file_path, content))
            
            # Configuration file analysis
            if self.is_config_file(file_path):
                issues.extend(self.config_analysis(file_path, content, lines))
                
        except Exception as e:
            logger.error(f"Error analyzing {file_path}: {e}")
        
        return issues
    
    def pattern_analysis(self, file_path: str, content: str, lines: List[str]) -> List[SecurityIssue]:
        """Pattern-based security analysis"""
        issues = []
        patterns = self.patterns.get_all_patterns()
        
        for pattern_name, pattern_info in patterns.items():
            pattern = pattern_info['pattern']
            
            for line_num, line in enumerate(lines, 1):
                matches = re.finditer(pattern, line)
                
                for match in matches:
                    # Skip if in comments (simple check)
                    if line.strip().startswith('#'):
                        continue
                    
                    issue_id = f"{pattern_name}_{hashlib.md5(f'{file_path}:{line_num}:{match.group()}'.encode()).hexdigest()[:8]}"
                    
                    issue = SecurityIssue(
                        id=issue_id,
                        title=pattern_info['description'],
                        description=f"Pattern '{pattern_name}' detected: {match.group()}",
                        level=pattern_info['level'],
                        category=pattern_info['category'],
                        file_path=file_path,
                        line_number=line_num,
                        code_snippet=line.strip(),
                        recommendation=self.get_recommendation(pattern_name),
                        auto_fixable=self.is_auto_fixable(pattern_name)
                    )
                    
                    issues.append(issue)
        
        return issues
    
    def ast_analysis(self, file_path: str, content: str) -> List[SecurityIssue]:
        """AST-based analysis for Python files"""
        issues = []
        
        try:
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                # Check for dangerous function calls
                if isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name):
                        if node.func.id in ['eval', 'exec', 'compile']:
                            issues.append(self.create_ast_issue(
                                file_path, node, 'dangerous_function',
                                f'Dangerous function {node.func.id}() used',
                                VulnerabilityLevel.HIGH,
                                SecurityCategory.CODE_INJECTION
                            ))
                    
                    elif isinstance(node.func, ast.Attribute):
                        # Check for os.system calls
                        if (isinstance(node.func.value, ast.Name) and 
                            node.func.value.id == 'os' and 
                            node.func.attr == 'system'):
                            issues.append(self.create_ast_issue(
                                file_path, node, 'os_system',
                                'Use of os.system() detected',
                                VulnerabilityLevel.HIGH,
                                SecurityCategory.CODE_INJECTION
                            ))
                
                # Check for hardcoded strings that look like secrets
                elif isinstance(node, ast.Str):
                    if len(node.s) > 20 and self.looks_like_secret(node.s):
                        issues.append(self.create_ast_issue(
                            file_path, node, 'potential_secret',
                            'Potential hardcoded secret detected',
                            VulnerabilityLevel.MEDIUM,
                            SecurityCategory.AUTHENTICATION
                        ))
                
        except SyntaxError:
            # File has syntax errors, skip AST analysis
            pass
        except Exception as e:
            logger.debug(f"AST analysis error for {file_path}: {e}")
        
        return issues
    
    def config_analysis(self, file_path: str, content: str, lines: List[str]) -> List[SecurityIssue]:
        """Analyze configuration files"""
        issues = []
        
        # Check for common misconfigurations
        config_checks = {
            'debug_true': (r'(?i)debug\s*[=:]\s*true', VulnerabilityLevel.MEDIUM),
            'ssl_false': (r'(?i)ssl\s*[=:]\s*false', VulnerabilityLevel.HIGH),
            'verify_false': (r'(?i)verify\s*[=:]\s*false', VulnerabilityLevel.HIGH),
            'insecure_protocol': (r'(?i)protocol\s*[=:]\s*http(?!s)', VulnerabilityLevel.MEDIUM)
        }
        
        for line_num, line in enumerate(lines, 1):
            for check_name, (pattern, level) in config_checks.items():
                if re.search(pattern, line) and not line.strip().startswith('#'):
                    issue_id = f"config_{check_name}_{hashlib.md5(f'{file_path}:{line_num}'.encode()).hexdigest()[:8]}"
                    
                    issues.append(SecurityIssue(
                        id=issue_id,
                        title=f"Configuration issue: {check_name}",
                        description=f"Potentially insecure configuration: {line.strip()}",
                        level=level,
                        category=SecurityCategory.CONFIGURATION,
                        file_path=file_path,
                        line_number=line_num,
                        code_snippet=line.strip(),
                        recommendation=f"Review and secure the {check_name} configuration",
                        auto_fixable=False
                    ))
        
        return issues
    
    def create_ast_issue(self, file_path: str, node: ast.AST, pattern_name: str,
                        description: str, level: VulnerabilityLevel, 
                        category: SecurityCategory) -> SecurityIssue:
        """Create security issue from AST node"""
        issue_id = f"ast_{pattern_name}_{hashlib.md5(f'{file_path}:{node.lineno}'.encode()).hexdigest()[:8]}"
        
        return SecurityIssue(
            id=issue_id,
            title=description,
            description=description,
            level=level,
            category=category,
            file_path=file_path,
            line_number=getattr(node, 'lineno', None),
            code_snippet=None,  # Would need source map for exact code
            recommendation=self.get_recommendation(pattern_name),
            auto_fixable=False
        )
    
    def looks_like_secret(self, text: str) -> bool:
        """Check if text looks like a secret"""
        # High entropy strings that might be secrets
        if len(set(text)) / len(text) > 0.6:  # High character diversity
            if re.match(r'^[A-Za-z0-9+/=]{20,}$', text):  # Base64-like
                return True
            if re.match(r'^[A-Fa-f0-9]{20,}$', text):  # Hex-like
                return True
        return False
    
    def is_config_file(self, file_path: str) -> bool:
        """Check if file is a configuration file"""
        config_extensions = {'.json', '.yml', '.yaml', '.ini', '.cfg', '.conf', '.config'}
        return Path(file_path).suffix.lower() in config_extensions
    
    def get_recommendation(self, pattern_name: str) -> str:
        """Get security recommendation for pattern"""
        recommendations = {
            'hardcoded_password': 'Use environment variables or secure configuration files for passwords',
            'sql_injection': 'Use parameterized queries or prepared statements',
            'command_injection': 'Validate and sanitize input, use subprocess with shell=False',
            'weak_random': 'Use secrets module for cryptographic purposes',
            'insecure_hash': 'Use SHA-256 or better hash algorithms',
            'debug_mode': 'Disable debug mode in production',
            'insecure_url': 'Use HTTPS instead of HTTP',
            'private_key': 'Remove private keys from code, use secure key management',
            'api_key': 'Use environment variables or secure configuration for API keys',
            'unsafe_deserialization': 'Validate input and use safe serialization methods',
            'dangerous_function': 'Avoid using eval/exec, use safer alternatives',
            'os_system': 'Use subprocess module with proper input validation'
        }
        return recommendations.get(pattern_name, 'Review and fix this security issue')
    
    def is_auto_fixable(self, pattern_name: str) -> bool:
        """Check if issue can be automatically fixed"""
        auto_fixable = {
            'debug_mode', 'insecure_url', 'insecure_hash'
        }
        return pattern_name in auto_fixable

class DependencyScanner:
    """Scans dependencies for known vulnerabilities"""
    
    def __init__(self):
        self.vulnerability_db = self.load_vulnerability_db()
    
    def load_vulnerability_db(self) -> Dict:
        """Load vulnerability database (simplified)"""
        # In production, this would load from a real vulnerability database
        return {
            'requests': {
                '<2.20.0': {
                    'cve': 'CVE-2018-18074',
                    'severity': VulnerabilityLevel.HIGH,
                    'description': 'HTTP Request Smuggling vulnerability'
                }
            },
            'pyyaml': {
                '<5.1': {
                    'cve': 'CVE-2017-18342',
                    'severity': VulnerabilityLevel.HIGH,
                    'description': 'Arbitrary code execution via yaml.load()'
                }
            }
        }
    
    def scan_requirements(self, requirements_file: str) -> List[SecurityIssue]:
        """Scan requirements file for vulnerable dependencies"""
        issues = []
        
        if not Path(requirements_file).exists():
            return issues
        
        try:
            with open(requirements_file, 'r') as f:
                requirements = f.readlines()
            
            for line_num, line in enumerate(requirements, 1):
                line = line.strip()
                if line and not line.startswith('#'):
                    package_info = self.parse_requirement(line)
                    if package_info:
                        vuln_issues = self.check_vulnerability(package_info, requirements_file, line_num)
                        issues.extend(vuln_issues)
        
        except Exception as e:
            logger.error(f"Error scanning requirements: {e}")
        
        return issues
    
    def parse_requirement(self, requirement: str) -> Optional[Dict]:
        """Parse a requirement line"""
        # Simple parser for package==version format
        match = re.match(r'^([a-zA-Z0-9_-]+)\s*([>=<!=]+)\s*([0-9.]+)', requirement)
        if match:
            return {
                'name': match.group(1).lower(),
                'operator': match.group(2),
                'version': match.group(3)
            }
        return None
    
    def check_vulnerability(self, package_info: Dict, file_path: str, line_num: int) -> List[SecurityIssue]:
        """Check if package has known vulnerabilities"""
        issues = []
        package_name = package_info['name']
        
        if package_name in self.vulnerability_db:
            vulnerabilities = self.vulnerability_db[package_name]
            
            for version_range, vuln_info in vulnerabilities.items():
                if self.version_in_range(package_info['version'], version_range):
                    issue_id = f"dep_{package_name}_{vuln_info['cve']}"
                    
                    issues.append(SecurityIssue(
                        id=issue_id,
                        title=f"Vulnerable dependency: {package_name}",
                        description=f"{vuln_info['description']} ({vuln_info['cve']})",
                        level=vuln_info['severity'],
                        category=SecurityCategory.DEPENDENCIES,
                        file_path=file_path,
                        line_number=line_num,
                        code_snippet=f"{package_name}{package_info['operator']}{package_info['version']}",
                        recommendation=f"Update {package_name} to a version not affected by {vuln_info['cve']}",
                        cwe_id=vuln_info.get('cwe'),
                        auto_fixable=True
                    ))
        
        return issues
    
    def version_in_range(self, version: str, version_range: str) -> bool:
        """Check if version is in vulnerable range (simplified)"""
        # Simple version comparison - in production use packaging.version
        if version_range.startswith('<'):
            threshold = version_range[1:]
            return version < threshold
        return False

class SecurityAuditor:
    """Main security audit system"""
    
    def __init__(self, project_root: str = None):
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self.code_analyzer = CodeAnalyzer()
        self.dependency_scanner = DependencyScanner()
        
        # Files to exclude from scanning
        self.exclude_patterns = {
            '*.pyc', '__pycache__', '.git', '*.log', '*.db',
            'node_modules', 'venv', '.env', '*.backup*'
        }
    
    def scan_project(self, include_dependencies: bool = True) -> SecurityScanResult:
        """Perform comprehensive security scan"""
        scan_id = hashlib.sha256(f"{time.time()}:{self.project_root}".encode()).hexdigest()[:16]
        start_time = time.time()
        
        logger.info(f"Starting security scan {scan_id}")
        
        all_issues = []
        files_scanned = 0
        
        # Scan source code files
        for file_path in self.get_scannable_files():
            try:
                issues = self.code_analyzer.analyze_file(str(file_path))
                all_issues.extend(issues)
                files_scanned += 1
                
                if files_scanned % 10 == 0:
                    logger.info(f"Scanned {files_scanned} files...")
                    
            except Exception as e:
                logger.error(f"Error scanning {file_path}: {e}")
        
        # Scan dependencies
        if include_dependencies:
            requirements_files = ['requirements.txt', 'setup.py']
            for req_file in requirements_files:
                req_path = self.project_root / req_file
                if req_path.exists():
                    dep_issues = self.dependency_scanner.scan_requirements(str(req_path))
                    all_issues.extend(dep_issues)
        
        # Calculate statistics
        scan_duration = time.time() - start_time
        issues_by_level = self.count_by_level(all_issues)
        issues_by_category = self.count_by_category(all_issues)
        compliance_score = self.calculate_compliance_score(all_issues, files_scanned)
        
        result = SecurityScanResult(
            scan_id=scan_id,
            timestamp=datetime.now(),
            total_files_scanned=files_scanned,
            total_issues=len(all_issues),
            issues_by_level=issues_by_level,
            issues_by_category=issues_by_category,
            issues=all_issues,
            scan_duration=scan_duration,
            compliance_score=compliance_score
        )
        
        logger.info(f"Security scan completed: {len(all_issues)} issues found in {scan_duration:.2f}s")
        return result
    
    def get_scannable_files(self) -> List[Path]:
        """Get list of files to scan"""
        scannable_files = []
        
        for file_path in self.project_root.rglob('*'):
            if file_path.is_file():
                # Check if file should be excluded
                if self.should_exclude_file(file_path):
                    continue
                
                # Include Python files and configuration files
                if (file_path.suffix in {'.py', '.json', '.yml', '.yaml', '.ini', '.cfg', '.conf'} or
                    file_path.name in {'requirements.txt', 'setup.py'}):
                    scannable_files.append(file_path)
        
        return scannable_files
    
    def should_exclude_file(self, file_path: Path) -> bool:
        """Check if file should be excluded from scanning"""
        path_str = str(file_path.relative_to(self.project_root))
        
        for pattern in self.exclude_patterns:
            if pattern.replace('*', '') in path_str:
                return True
        
        return False
    
    def count_by_level(self, issues: List[SecurityIssue]) -> Dict[str, int]:
        """Count issues by severity level"""
        counts = {level.value: 0 for level in VulnerabilityLevel}
        for issue in issues:
            counts[issue.level.value] += 1
        return counts
    
    def count_by_category(self, issues: List[SecurityIssue]) -> Dict[str, int]:
        """Count issues by category"""
        counts = {category.value: 0 for category in SecurityCategory}
        for issue in issues:
            counts[issue.category.value] += 1
        return counts
    
    def calculate_compliance_score(self, issues: List[SecurityIssue], files_scanned: int) -> float:
        """Calculate security compliance score (0-100)"""
        if files_scanned == 0:
            return 100.0
        
        # Weight issues by severity
        severity_weights = {
            VulnerabilityLevel.LOW: 1,
            VulnerabilityLevel.MEDIUM: 2,
            VulnerabilityLevel.HIGH: 4,
            VulnerabilityLevel.CRITICAL: 8
        }
        
        weighted_issues = sum(severity_weights[issue.level] for issue in issues)
        max_possible_score = files_scanned * 2  # Arbitrary baseline
        
        score = max(0, 100 - (weighted_issues / max_possible_score * 100))
        return min(100.0, score)
    
    def generate_report(self, scan_result: SecurityScanResult, format: str = 'json') -> str:
        """Generate security report"""
        if format == 'json':
            return self.generate_json_report(scan_result)
        elif format == 'html':
            return self.generate_html_report(scan_result)
        else:
            return self.generate_text_report(scan_result)
    
    def generate_json_report(self, scan_result: SecurityScanResult) -> str:
        """Generate JSON report"""
        # Convert to serializable format
        report_data = asdict(scan_result)
        report_data['timestamp'] = scan_result.timestamp.isoformat()
        
        return json.dumps(report_data, indent=2, default=str)
    
    def generate_text_report(self, scan_result: SecurityScanResult) -> str:
        """Generate text report"""
        report = []
        report.append("=" * 60)
        report.append("SECURITY AUDIT REPORT")
        report.append("=" * 60)
        report.append(f"Scan ID: {scan_result.scan_id}")
        report.append(f"Timestamp: {scan_result.timestamp}")
        report.append(f"Files Scanned: {scan_result.total_files_scanned}")
        report.append(f"Total Issues: {scan_result.total_issues}")
        report.append(f"Compliance Score: {scan_result.compliance_score:.1f}/100")
        report.append(f"Scan Duration: {scan_result.scan_duration:.2f}s")
        report.append("")
        
        # Issues by level
        report.append("ISSUES BY SEVERITY:")
        for level, count in scan_result.issues_by_level.items():
            if count > 0:
                report.append(f"  {level.upper()}: {count}")
        report.append("")
        
        # Issues by category
        report.append("ISSUES BY CATEGORY:")
        for category, count in scan_result.issues_by_category.items():
            if count > 0:
                report.append(f"  {category.replace('_', ' ').title()}: {count}")
        report.append("")
        
        # Detailed issues
        if scan_result.issues:
            report.append("DETAILED ISSUES:")
            report.append("-" * 40)
            
            for issue in sorted(scan_result.issues, key=lambda x: (x.level.value, x.file_path)):
                report.append(f"ID: {issue.id}")
                report.append(f"Level: {issue.level.value.upper()}")
                report.append(f"Category: {issue.category.value.replace('_', ' ').title()}")
                report.append(f"File: {issue.file_path}")
                if issue.line_number:
                    report.append(f"Line: {issue.line_number}")
                report.append(f"Issue: {issue.title}")
                report.append(f"Description: {issue.description}")
                report.append(f"Recommendation: {issue.recommendation}")
                if issue.code_snippet:
                    report.append(f"Code: {issue.code_snippet}")
                report.append("-" * 40)
        
        return "\n".join(report)
    
    def generate_html_report(self, scan_result: SecurityScanResult) -> str:
        """Generate HTML report"""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Security Audit Report - {scan_result.scan_id}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background: #f0f0f0; padding: 20px; border-radius: 5px; }}
                .summary {{ margin: 20px 0; }}
                .issue {{ border: 1px solid #ddd; margin: 10px 0; padding: 15px; border-radius: 5px; }}
                .critical {{ border-left: 5px solid #d32f2f; }}
                .high {{ border-left: 5px solid #f57c00; }}
                .medium {{ border-left: 5px solid #fbc02d; }}
                .low {{ border-left: 5px solid #388e3c; }}
                .code {{ background: #f5f5f5; padding: 10px; font-family: monospace; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Security Audit Report</h1>
                <p><strong>Scan ID:</strong> {scan_result.scan_id}</p>
                <p><strong>Timestamp:</strong> {scan_result.timestamp}</p>
                <p><strong>Compliance Score:</strong> {scan_result.compliance_score:.1f}/100</p>
            </div>
            
            <div class="summary">
                <h2>Summary</h2>
                <p>Files Scanned: {scan_result.total_files_scanned}</p>
                <p>Total Issues: {scan_result.total_issues}</p>
                <p>Scan Duration: {scan_result.scan_duration:.2f}s</p>
            </div>
            
            <div class="issues">
                <h2>Issues</h2>
        """
        
        for issue in scan_result.issues:
            html += f"""
                <div class="issue {issue.level.value}">
                    <h3>{issue.title}</h3>
                    <p><strong>Level:</strong> {issue.level.value.upper()}</p>
                    <p><strong>Category:</strong> {issue.category.value.replace('_', ' ').title()}</p>
                    <p><strong>File:</strong> {issue.file_path}</p>
                    {f'<p><strong>Line:</strong> {issue.line_number}</p>' if issue.line_number else ''}
                    <p><strong>Description:</strong> {issue.description}</p>
                    <p><strong>Recommendation:</strong> {issue.recommendation}</p>
                    {f'<div class="code">{issue.code_snippet}</div>' if issue.code_snippet else ''}
                </div>
            """
        
        html += """
            </div>
        </body>
        </html>
        """
        
        return html

def main():
    """Main security audit function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Security Audit System')
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    