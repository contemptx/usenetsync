#!/usr/bin/env python3
"""
Consolidated Advanced GitHub Workflow Manager
Combines the best features from all existing workflows with enhanced capabilities
"""

import os
import sys
import json
import time
import shutil
import threading
import subprocess
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass, field
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import hashlib
import re

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [%(name)s] %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class DeploymentConfig:
    """Unified deployment configuration"""
    branch: str = "main"
    remote: str = "origin"
    auto_deploy: bool = True
    validate_before_deploy: bool = True
    auto_rollback: bool = True
    max_deployments_per_hour: int = 10
    check_syntax: bool = True
    check_security: bool = True
    check_performance: bool = True
    fix_indentation: bool = True
    create_workflows: bool = True
    monitoring_interval: int = 5
    health_check_timeout: int = 30
    rollback_on_health_failure: bool = True
    
@dataclass
class ValidationResult:
    """Validation result with details"""
    valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    auto_fixed: List[str] = field(default_factory=list)
    
@dataclass
class HealthMetrics:
    """System health metrics"""
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    response_time: float
    error_rate: float
    timestamp: datetime

class IndentationFixer:
    """Advanced indentation repair system"""
    
    def __init__(self):
        self.indent_pattern = re.compile(r'^(\s*)')
        self.block_keywords = {
            'if', 'elif', 'else', 'for', 'while', 'try', 
            'except', 'finally', 'with', 'def', 'class'
        }
        self.dedent_keywords = {'return', 'break', 'continue', 'raise', 'pass'}
        
    def analyze_indentation(self, content: str) -> Dict:
        """Analyze indentation issues in content"""
        lines = content.split('\n')
        issues = []
        indent_stack = [0]
        expected_indent = 0
        
        for i, line in enumerate(lines):
            if not line.strip():
                continue
                
            match = self.indent_pattern.match(line)
            current_indent = len(match.group(1))
            stripped = line.strip()
            
            # Check for mixed tabs and spaces
            if '\t' in match.group(1) and ' ' in match.group(1):
                issues.append({
                    'line': i + 1,
                    'type': 'mixed_indent',
                    'message': 'Mixed tabs and spaces'
                })
            
            # Check for incorrect indentation
            if current_indent not in indent_stack and current_indent != expected_indent:
                issues.append({
                    'line': i + 1,
                    'type': 'incorrect_indent',
                    'current': current_indent,
                    'expected': expected_indent,
                    'message': f'Expected indent {expected_indent}, got {current_indent}'
                })
            
            # Update expected indentation
            if any(stripped.startswith(kw + ' ') or stripped.startswith(kw + ':') 
                   for kw in self.block_keywords):
                expected_indent = current_indent + 4
                if expected_indent not in indent_stack:
                    indent_stack.append(expected_indent)
            elif any(stripped.startswith(kw) for kw in self.dedent_keywords):
                if len(indent_stack) > 1:
                    indent_stack.pop()
                expected_indent = indent_stack[-1]
                
        return {
            'issues': issues,
            'total_lines': len(lines),
            'has_tabs': any('\t' in line for line in lines),
            'consistent_spaces': self._check_consistent_spaces(lines)
        }
    
    def fix_indentation(self, content: str) -> Tuple[str, List[str]]:
        """Fix indentation issues automatically"""
        lines = content.split('\n')
        fixed_lines = []
        changes = []
        indent_stack = [0]
        current_indent = 0
        
        for i, line in enumerate(lines):
            if not line.strip():
                fixed_lines.append(line)
                continue
            
            stripped = line.strip()
            
            # Replace tabs with spaces
            if '\t' in line:
                line = line.replace('\t', '    ')
                changes.append(f"Line {i+1}: Replaced tabs with spaces")
            
            # Determine proper indentation
            if any(stripped.startswith(kw) for kw in self.dedent_keywords):
                if len(indent_stack) > 1:
                    indent_stack.pop()
                current_indent = indent_stack[-1]
            
            # Apply correct indentation
            fixed_line = ' ' * current_indent + stripped
            if fixed_line != line:
                changes.append(f"Line {i+1}: Fixed indentation from {len(line) - len(line.lstrip())} to {current_indent}")
            fixed_lines.append(fixed_line)
            
            # Update indent for next line if needed
            if stripped.endswith(':'):
                if any(stripped.startswith(kw) for kw in self.block_keywords):
                    current_indent += 4
                    if current_indent not in indent_stack:
                        indent_stack.append(current_indent)
        
        return '\n'.join(fixed_lines), changes
    
    def _check_consistent_spaces(self, lines: List[str]) -> bool:
        """Check if file uses consistent space indentation"""
        space_counts = set()
        for line in lines:
            if line.strip():
                match = self.indent_pattern.match(line)
                indent = match.group(1)
                if indent and not '\t' in indent:
                    space_counts.add(len(indent))
        
        # Check if all indents are multiples of 4
        return all(count % 4 == 0 for count in space_counts)

class FileChangeHandler(FileSystemEventHandler):
    """Enhanced file change handler"""
    
    def __init__(self, workflow_manager):
        self.workflow_manager = workflow_manager
        self.last_events = {}
        self.debounce_time = 2
        
    def on_modified(self, event):
        if event.is_directory:
            return
            
        file_path = Path(event.src_path)
        now = time.time()
        
        # Debounce rapid changes
        if str(file_path) in self.last_events:
            if now - self.last_events[str(file_path)] < self.debounce_time:
                return
                
        self.last_events[str(file_path)] = now
        
        # Process relevant files
        if file_path.suffix in {'.py', '.json', '.yml', '.yaml', '.md', '.txt', '.bat', '.sh'}:
            threading.Thread(
                target=self.workflow_manager.handle_file_change,
                args=(file_path,)
            ).start()

class ConsolidatedGitHubWorkflow:
    """Consolidated GitHub workflow with all advanced features"""
    
    def __init__(self, project_root: str = None):
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self.config = self.load_config()
        self.indent_fixer = IndentationFixer()
        self.deployment_history = []
        self.health_history = []
        self.observer = None
        self.monitoring = False
        self.last_deployment = None
        self.deployment_count = 0
        self.deployment_lock = threading.Lock()
        
        # Create necessary directories
        self.setup_directories()
        
    def setup_directories(self):
        """Create all necessary directories"""
        directories = [
            self.project_root / ".github" / "workflows",
            self.project_root / ".github" / "ISSUE_TEMPLATE",
            self.project_root / ".workflow",
            self.project_root / "scripts",
            self.project_root / "docs",
            self.project_root / "tests",
            self.project_root / "backups"
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            
    def load_config(self) -> DeploymentConfig:
        """Load unified configuration"""
        config_file = self.project_root / ".workflow" / "config.json"
        
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    data = json.load(f)
                return DeploymentConfig(**data)
            except Exception as e:
                logger.warning(f"Failed to load config: {e}, using defaults")
                
        config = DeploymentConfig()
        self.save_config(config)
        return config
        
    def save_config(self, config: DeploymentConfig):
        """Save configuration"""
        config_file = self.project_root / ".workflow" / "config.json"
        with open(config_file, 'w') as f:
            json.dump(config.__dict__, f, indent=2)
            
    def validate_file(self, file_path: Path) -> ValidationResult:
        """Comprehensive file validation"""
        result = ValidationResult(valid=True)
        
        if file_path.suffix != '.py':
            return result
            
        try:
            content = file_path.read_text(encoding='utf-8')
            
            # Syntax validation
            if self.config.check_syntax:
                try:
                    compile(content, str(file_path), 'exec')
                except SyntaxError as e:
                    result.valid = False
                    result.errors.append(f"Syntax error at line {e.lineno}: {e.msg}")
                    
            # Indentation check
            if self.config.fix_indentation:
                indent_analysis = self.indent_fixer.analyze_indentation(content)
                if indent_analysis['issues']:
                    result.warnings.extend([
                        f"Line {issue['line']}: {issue['message']}" 
                        for issue in indent_analysis['issues']
                    ])
                    
            # Security checks
            if self.config.check_security:
                security_patterns = [
                    (r'password\s*=\s*["\'].*["\']', 'Hardcoded password'),
                    (r'api_key\s*=\s*["\'].*["\']', 'Hardcoded API key'),
                    (r'secret\s*=\s*["\'].*["\']', 'Hardcoded secret'),
                    (r'eval\s*\(', 'Use of eval()'),
                    (r'exec\s*\(', 'Use of exec()'),
                    (r'pickle\.loads?\s*\(', 'Unsafe pickle usage')
                ]
                
                for pattern, message in security_patterns:
                    if re.search(pattern, content, re.IGNORECASE):
                        result.warnings.append(f"Security warning: {message}")
                        
            # Performance checks
            if self.config.check_performance:
                perf_patterns = [
                    (r'time\.sleep\s*\(\s*\d{3,}', 'Long sleep duration'),
                    (r'for\s+.*\s+in\s+.*for\s+.*\s+in', 'Nested loops detected'),
                    (r'\.read\(\)\.split\(', 'Inefficient file reading')
                ]
                
                for pattern, message in perf_patterns:
                    if re.search(pattern, content):
                        result.warnings.append(f"Performance warning: {message}")
                        
        except Exception as e:
            result.valid = False
            result.errors.append(f"Validation error: {e}")
            
        return result
        
    def auto_fix_file(self, file_path: Path) -> bool:
        """Automatically fix common issues"""
        if not self.config.fix_indentation or file_path.suffix != '.py':
            return False
            
        try:
            # Backup original
            backup_path = self.project_root / "backups" / f"{file_path.name}.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            shutil.copy2(file_path, backup_path)
            
            # Fix indentation
            content = file_path.read_text(encoding='utf-8')
            fixed_content, changes = self.indent_fixer.fix_indentation(content)
            
            if changes:
                file_path.write_text(fixed_content, encoding='utf-8')
                logger.info(f"Auto-fixed {len(changes)} issues in {file_path.name}")
                for change in changes[:5]:  # Show first 5 changes
                    logger.info(f"  - {change}")
                if len(changes) > 5:
                    logger.info(f"  ... and {len(changes) - 5} more")
                return True
                
        except Exception as e:
            logger.error(f"Failed to auto-fix {file_path}: {e}")
            
        return False
        
    def check_system_health(self) -> HealthMetrics:
        """Check system health metrics"""
        import psutil
        
        # Get system metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage(str(self.project_root))
        
        # Simple response time check
        start_time = time.time()
        try:
            subprocess.run(['git', 'status'], capture_output=True, timeout=5)
            response_time = time.time() - start_time
        except:
            response_time = 999.0
            
        # Calculate error rate from recent logs
        error_rate = self._calculate_error_rate()
        
        return HealthMetrics(
            cpu_usage=cpu_percent,
            memory_usage=memory.percent,
            disk_usage=disk.percent,
            response_time=response_time,
            error_rate=error_rate,
            timestamp=datetime.now()
        )
        
    def _calculate_error_rate(self) -> float:
        """Calculate recent error rate"""
        if not self.deployment_history:
            return 0.0
            
        recent = self.deployment_history[-10:]
        errors = sum(1 for d in recent if not d.get('success', True))
        return (errors / len(recent)) * 100
        
    def deploy_to_github(self, message: str = None, force: bool = False) -> Dict:
        """Deploy changes to GitHub with validation"""
        with self.deployment_lock:
            # Check deployment rate limit
            if not force and not self._check_deployment_rate():
                return {
                    'success': False,
                    'error': 'Deployment rate limit exceeded'
                }
                
            # Get changed files
            result = subprocess.run(
                ['git', 'status', '--porcelain'],
                capture_output=True,
                text=True
            )
            
            if not result.stdout.strip():
                return {
                    'success': True,
                    'message': 'No changes to deploy'
                }
                
            changed_files = []
            for line in result.stdout.strip().split('\n'):
                if line.strip():
                    parts = line.strip().split()
                    if len(parts) >= 2:
                        changed_files.append(Path(parts[1]))
                        
            # Validate all changed files
            if self.config.validate_before_deploy and not force:
                all_valid = True
                for file_path in changed_files:
                    if file_path.exists():
                        validation = self.validate_file(file_path)
                        
                        # Try auto-fix if needed
                        if not validation.valid and self.config.fix_indentation:
                            if self.auto_fix_file(file_path):
                                # Re-validate after fix
                                validation = self.validate_file(file_path)
                                
                        if not validation.valid:
                            all_valid = False
                            logger.error(f"Validation failed for {file_path}")
                            for error in validation.errors:
                                logger.error(f"  - {error}")
                                
                if not all_valid:
                    return {
                        'success': False,
                        'error': 'Validation failed for one or more files'
                    }
                    
            # Create comprehensive commit message
            if not message:
                message = self._generate_commit_message(changed_files)
                
            # Stage and commit
            try:
                subprocess.run(['git', 'add', '.'], check=True)
                subprocess.run(['git', 'commit', '-m', message], check=True)
                subprocess.run(['git', 'push', self.config.remote, self.config.branch], check=True)
                
                deployment = {
                    'id': hashlib.sha256(f"{datetime.now().isoformat()}".encode()).hexdigest()[:8],
                    'timestamp': datetime.now().isoformat(),
                    'message': message,
                    'files': [str(f) for f in changed_files],
                    'success': True
                }
                
                self.deployment_history.append(deployment)
                self.last_deployment = datetime.now()
                self.deployment_count += 1
                
                logger.info(f"Successfully deployed: {message}")
                
                # Post-deployment health check
                if self.config.rollback_on_health_failure:
                    threading.Thread(target=self._post_deployment_health_check).start()
                    
                return deployment
                
            except subprocess.CalledProcessError as e:
                error_msg = f"Git operation failed: {e}"
                logger.error(error_msg)
                
                self.deployment_history.append({
                    'timestamp': datetime.now().isoformat(),
                    'success': False,
                    'error': error_msg
                })
                
                return {
                    'success': False,
                    'error': error_msg
                }
                
    def _check_deployment_rate(self) -> bool:
        """Check if deployment rate is within limits"""
        if not self.last_deployment:
            return True
            
        hour_ago = datetime.now() - timedelta(hours=1)
        recent_deployments = [
            d for d in self.deployment_history 
            if datetime.fromisoformat(d['timestamp']) > hour_ago
        ]
        
        return len(recent_deployments) < self.config.max_deployments_per_hour
        
    def _generate_commit_message(self, files: List[Path]) -> str:
        """Generate intelligent commit message"""
        # Categorize files
        categories = {
            'feat': [],
            'fix': [],
            'docs': [],
            'style': [],
            'refactor': [],
            'test': [],
            'chore': []
        }
        
        for file in files:
            if 'test' in str(file):
                categories['test'].append(file)
            elif file.suffix in {'.md', '.txt', '.rst'}:
                categories['docs'].append(file)
            elif file.name.startswith('.'):
                categories['chore'].append(file)
            else:
                # Default to feat for now
                categories['feat'].append(file)
                
        # Build message
        main_category = max(categories.keys(), key=lambda k: len(categories[k]))
        file_count = len(files)
        
        if file_count == 1:
            message = f"{main_category}: Update {files[0].name}"
        else:
            message = f"{main_category}: Update {file_count} files"
            
        # Add details
        details = []
        for cat, cat_files in categories.items():
            if cat_files and cat != main_category:
                details.append(f"- {cat}: {len(cat_files)} files")
                
        if details:
            message += "\n\n" + "\n".join(details)
            
        return message
        
    def _post_deployment_health_check(self):
        """Check system health after deployment"""
        time.sleep(5)  # Wait for deployment to settle
        
        logger.info("Running post-deployment health check...")
        
        # Take multiple samples
        samples = []
        for _ in range(3):
            samples.append(self.check_system_health())
            time.sleep(2)
            
        # Analyze samples
        avg_cpu = sum(s.cpu_usage for s in samples) / len(samples)
        avg_memory = sum(s.memory_usage for s in samples) / len(samples)
        max_response_time = max(s.response_time for s in samples)
        
        # Check thresholds
        issues = []
        if avg_cpu > 80:
            issues.append(f"High CPU usage: {avg_cpu:.1f}%")
        if avg_memory > 85:
            issues.append(f"High memory usage: {avg_memory:.1f}%")
        if max_response_time > 5:
            issues.append(f"Slow response time: {max_response_time:.1f}s")
            
        if issues and self.config.auto_rollback:
            logger.warning("Health check failed: " + ", ".join(issues))
            self.rollback_deployment()
        else:
            logger.info("Health check passed")
            
    def rollback_deployment(self):
        """Rollback to previous deployment"""
        try:
            logger.warning("Initiating automatic rollback...")
            
            # Get previous commit
            result = subprocess.run(
                ['git', 'rev-parse', 'HEAD~1'],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                prev_commit = result.stdout.strip()
                
                # Rollback
                subprocess.run(['git', 'reset', '--hard', prev_commit], check=True)
                subprocess.run(['git', 'push', '--force', self.config.remote, self.config.branch], check=True)
                
                logger.info(f"Successfully rolled back to {prev_commit[:8]}")
                
                # Record rollback
                self.deployment_history.append({
                    'timestamp': datetime.now().isoformat(),
                    'type': 'rollback',
                    'to_commit': prev_commit[:8],
                    'success': True
                })
                
        except Exception as e:
            logger.error(f"Rollback failed: {e}")
            
    def handle_file_change(self, file_path: Path):
        """Handle file change event"""
        logger.info(f"Detected change in {file_path.name}")
        
        # Skip certain files
        if file_path.name.startswith('.') or file_path.suffix in {'.pyc', '.log', '.tmp'}:
            return
            
        # Validate file
        if file_path.suffix == '.py':
            validation = self.validate_file(file_path)
            
            if not validation.valid:
                # Try auto-fix
                if self.config.fix_indentation:
                    if self.auto_fix_file(file_path):
                        logger.info(f"Auto-fixed issues in {file_path.name}")
                        validation = self.validate_file(file_path)
                        
            # Log validation results
            if validation.errors:
                logger.error(f"Validation errors in {file_path.name}:")
                for error in validation.errors:
                    logger.error(f"  - {error}")
                    
            if validation.warnings:
                logger.warning(f"Validation warnings in {file_path.name}:")
                for warning in validation.warnings:
                    logger.warning(f"  - {warning}")
                    
        # Auto-deploy if enabled and validation passed
        if self.config.auto_deploy:
            if not file_path.suffix == '.py' or not validation.errors:
                self.deploy_to_github(f"Auto-update: {file_path.name}")
                
    def start_monitoring(self, daemon: bool = False):
        """Start file monitoring"""
        if self.monitoring:
            logger.warning("Monitoring already active")
            return
            
        logger.info("Starting file monitoring...")
        
        self.observer = Observer()
        handler = FileChangeHandler(self)
        
        # Watch project directory
        self.observer.schedule(handler, str(self.project_root), recursive=True)
        self.observer.start()
        
        self.monitoring = True
        logger.info("Monitoring started")
        
        # Start health monitoring
        threading.Thread(target=self._health_monitor_loop, daemon=True).start()
        
        if not daemon:
            try:
                while self.monitoring:
                    time.sleep(1)
            except KeyboardInterrupt:
                self.stop_monitoring()
        
    def stop_monitoring(self):
        """Stop file monitoring"""
        if not self.monitoring:
            return
            
        logger.info("Stopping monitoring...")
        
        self.monitoring = False
        if self.observer:
            self.observer.stop()
            self.observer.join()
            
        logger.info("Monitoring stopped")
        
    def _health_monitor_loop(self):
        """Background health monitoring"""
        while self.monitoring:
            try:
                metrics = self.check_system_health()
                self.health_history.append(metrics)
                
                # Keep only recent history
                cutoff = datetime.now() - timedelta(hours=1)
                self.health_history = [
                    m for m in self.health_history 
                    if m.timestamp > cutoff
                ]
                
            except Exception as e:
                logger.error(f"Health monitoring error: {e}")
                
            time.sleep(self.config.monitoring_interval)
            
    def generate_advanced_workflows(self):
        """Generate the most advanced GitHub workflows"""
        workflows = {
            'advanced-ci.yml': self._get_advanced_ci_workflow(),
            'security-advanced.yml': self._get_security_workflow(),
            'performance-monitor.yml': self._get_performance_workflow(),
            'dependency-scan.yml': self._get_dependency_workflow(),
            'codeql-analysis.yml': self._get_codeql_workflow()
        }
        
        workflow_dir = self.project_root / '.github' / 'workflows'
        
        for filename, content in workflows.items():
            file_path = workflow_dir / filename
            file_path.write_text(content)
            logger.info(f"Created workflow: {filename}")
            
    def _get_advanced_ci_workflow(self) -> str:
        """Get advanced CI workflow with all checks"""
        return """name: Advanced CI/CD Pipeline

on:
  push:
    branches: [ main, master, develop ]
  pull_request:
    branches: [ main, master ]
  schedule:
    - cron: '0 0 * * 0'  # Weekly on Sunday

env:
  PYTHON_VERSION: '3.9'
  NODE_VERSION: '16'

jobs:
  lint-and-format:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: ${{ env.PYTHON_VERSION }}
    
    - name: Cache dependencies
      uses: actions/cache@v3
      with:
        path: ~/.cache/pip
        key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements*.txt') }}
        restore-keys: |
          ${{ runner.os }}-pip-
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install black flake8 mypy pylint isort autopep8
        if [ -f requirements.txt ]; then pip install -r requirements.txt; fi
        if [ -f requirements-dev.txt ]; then pip install -r requirements-dev.txt; fi
    
    - name: Format with Black
      run: black . --check --diff
      
    - name: Lint with flake8
      run: |
        flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
        flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics
    
    - name: Type check with mypy
      run: mypy . --ignore-missing-imports || true
      
    - name: Sort imports with isort
      run: isort . --check-only --diff
    
  test:
    needs: lint-and-format
    runs-on: ${{ matrix.os }}
    strategy:
      fail-fast: false
      matrix:
        os: [ubuntu-latest, windows-latest, macos-latest]
        python-version: ['3.8', '3.9', '3.10', '3.11']
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install pytest pytest-cov pytest-xdist pytest-timeout
        if [ -f requirements.txt ]; then pip install -r requirements.txt; fi
      shell: bash
    
    - name: Run tests with coverage
      run: |
        pytest -v --cov=. --cov-report=xml --cov-report=term-missing --timeout=300
      
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
        flags: unittests
        name: codecov-umbrella
        fail_ci_if_error: false

  security-scan:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Run Trivy vulnerability scanner
      uses: aquasecurity/trivy-action@master
      with:
        scan-type: 'fs'
        scan-ref: '.'
        severity: 'CRITICAL,HIGH'
        
    - name: Run Semgrep
      uses: returntocorp/semgrep-action@v1
      with:
        config: >-
          p/security-audit
          p/python
          p/dockerfile
          
  performance-check:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: ${{ env.PYTHON_VERSION }}
        
    - name: Install dependencies
      run: |
        pip install memory-profiler line-profiler pytest-benchmark
        if [ -f requirements.txt ]; then pip install -r requirements.txt; fi
        
    - name: Run performance tests
      run: |
        python -m pytest tests/performance/ -v --benchmark-only || true
        
    - name: Check memory usage
      run: |
        for script in *.py; do
          echo "Checking memory usage for $script"
          python -m memory_profiler "$script" --help 2>/dev/null || true
        done

  build-and-deploy:
    needs: [test, security-scan]
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main' || github.ref == 'refs/heads/master'
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Build artifacts
      run: |
        echo "Building deployment artifacts..."
        mkdir -p dist
        cp -r *.py requirements*.txt dist/ 2>/dev/null || true
        
    - name: Create release
      if: startsWith(github.ref, 'refs/tags/')
      uses: actions/create-release@v1
      env:
        GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
      with:
        tag_name: ${{ github.ref }}
        release_name: Release ${{ github.ref }}
        draft: false
        prerelease: false
"""

    def _get_security_workflow(self) -> str:
        """Get advanced security scanning workflow"""
        return """name: Advanced Security Scanning

on:
  push:
    branches: [ main, master ]
  pull_request:
    branches: [ main, master ]
  schedule:
    - cron: '30 1 * * 1'

jobs:
  security:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Run GitGuardian scan
      uses: GitGuardian/ggshield-action@master
      env:
        GITHUB_PUSH_BEFORE_SHA: ${{ github.event.before }}
        GITHUB_PUSH_BASE_SHA: ${{ github.event.base }}
        GITHUB_PULL_BASE_SHA:  ${{ github.event.pull_request.base.sha }}
        GITHUB_DEFAULT_BRANCH: ${{ github.event.repository.default_branch }}
        GITGUARDIAN_API_KEY: ${{ secrets.GITGUARDIAN_API_KEY }}
        
    - name: Run Bandit security linter
      uses: jpy-git/bandit-action@master
      with:
        config_file: .bandit
        
    - name: OWASP Dependency Check
      uses: dependency-check/Dependency-Check_Action@main
      with:
        project: 'UsenetSync'
        path: '.'
        format: 'ALL'
        
    - name: Upload OWASP results
      uses: actions/upload-artifact@v3
      with:
        name: OWASP dependency check report
        path: reports/
"""

    def _get_performance_workflow(self) -> str:
        """Get performance monitoring workflow"""
        return """name: Performance Monitoring

on:
  push:
    branches: [ main, master ]
  schedule:
    - cron: '0 */6 * * *'  # Every 6 hours

jobs:
  performance:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'
        
    - name: Install dependencies
      run: |
        pip install pytest-benchmark memory-profiler py-spy
        if [ -f requirements.txt ]; then pip install -r requirements.txt; fi
        
    - name: Run performance benchmarks
      run: |
        pytest tests/performance/ --benchmark-json output.json || true
        
    - name: Store benchmark result
      uses: benchmark-action/github-action-benchmark@v1
      with:
        tool: 'pytest'
        output-file-path: output.json
        github-token: ${{ secrets.GITHUB_TOKEN }}
        auto-push: true
"""

    def _get_dependency_workflow(self) -> str:
        """Get dependency update workflow"""
        return """name: Dependency Updates

on:
  schedule:
    - cron: '0 0 * * 1'  # Weekly on Monday
  workflow_dispatch:

jobs:
  update:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'
        
    - name: Install pip-tools
      run: pip install pip-tools
      
    - name: Update dependencies
      run: |
        pip-compile --upgrade requirements.in -o requirements.txt
        pip-compile --upgrade requirements-dev.in -o requirements-dev.txt || true
        
    - name: Create Pull Request
      uses: peter-evans/create-pull-request@v4
      with:
        commit-message: 'chore: Update dependencies'
        title: 'Automated dependency updates'
        body: |
          This PR updates the project dependencies to their latest versions.
          
          Please review the changes and ensure all tests pass before merging.
        branch: update-dependencies
        delete-branch: true
"""

    def _get_codeql_workflow(self) -> str:
        """Get CodeQL analysis workflow"""
        return """name: CodeQL Analysis

on:
  push:
    branches: [ main, master ]
  pull_request:
    branches: [ main, master ]
  schedule:
    - cron: '45 2 * * 3'

jobs:
  analyze:
    name: Analyze
    runs-on: ubuntu-latest
    permissions:
      actions: read
      contents: read
      security-events: write

    strategy:
      fail-fast: false
      matrix:
        language: [ 'python' ]

    steps:
    - name: Checkout repository
      uses: actions/checkout@v3

    - name: Initialize CodeQL
      uses: github/codeql-action/init@v2
      with:
        languages: ${{ matrix.language }}
        queries: security-and-quality

    - name: Autobuild
      uses: github/codeql-action/autobuild@v2

    - name: Perform CodeQL Analysis
      uses: github/codeql-action/analyze@v2
      with:
        category: "/language:${{matrix.language}}"
"""

    def status(self) -> Dict:
        """Get current workflow status"""
        status = {
            'monitoring': self.monitoring,
            'config': self.config.__dict__,
            'recent_deployments': self.deployment_history[-5:],
            'health': {
                'current': None,
                'history': []
            }
        }
        
        # Get current health
        if self.health_history:
            current = self.health_history[-1]
            status['health']['current'] = {
                'cpu': f"{current.cpu_usage:.1f}%",
                'memory': f"{current.memory_usage:.1f}%",
                'disk': f"{current.disk_usage:.1f}%",
                'response_time': f"{current.response_time:.2f}s",
                'error_rate': f"{current.error_rate:.1f}%"
            }
            
        # Get health trend
        if len(self.health_history) > 5:
            for metric in self.health_history[-5:]:
                status['health']['history'].append({
                    'time': metric.timestamp.strftime('%H:%M:%S'),
                    'cpu': metric.cpu_usage,
                    'memory': metric.memory_usage
                })
                
        return status
        
    def cleanup_old_files(self):
        """Clean up old backup and log files"""
        # Clean old backups
        backup_dir = self.project_root / "backups"
        if backup_dir.exists():
            cutoff = datetime.now() - timedelta(days=7)
            for backup in backup_dir.iterdir():
                if backup.stat().st_mtime < cutoff.timestamp():
                    backup.unlink()
                    logger.info(f"Removed old backup: {backup.name}")
                    
        # Clean old workflow data
        workflow_file = self.workflow_dir / "history.json"
        if workflow_file.exists():
            cutoff = datetime.now() - timedelta(days=30)
            # Keep only recent history
            self.deployment_history = [
                d for d in self.deployment_history
                if datetime.fromisoformat(d['timestamp']) > cutoff
            ]
            
def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Consolidated GitHub Workflow Manager')
    parser.add_argument('command', choices=['start', 'stop', 'status', 'deploy', 'rollback', 'setup', 'validate', 'clean'],
                        help='Command to execute')
    parser.add_argument('--daemon', action='store_true', help='Run in background')
    parser.add_argument('--message', '-m', help='Commit message for deployment')
    parser.add_argument('--force', '-f', action='store_true', help='Force operation')
    parser.add_argument('--file', help='Specific file to validate')
    
    args = parser.parse_args()
    
    workflow = ConsolidatedGitHubWorkflow()
    
    if args.command == 'start':
        workflow.start_monitoring(daemon=args.daemon)
        
    elif args.command == 'stop':
        workflow.stop_monitoring()
        
    elif args.command == 'status':
        status = workflow.status()
        print(json.dumps(status, indent=2, default=str))
        
    elif args.command == 'deploy':
        result = workflow.deploy_to_github(message=args.message, force=args.force)
        if result['success']:
            print(f"✅ Deployment successful: {result.get('message', 'No message')}")
        else:
            print(f"❌ Deployment failed: {result.get('error', 'Unknown error')}")
            
    elif args.command == 'rollback':
        workflow.rollback_deployment()
        
    elif args.command == 'setup':
        print("Setting up advanced GitHub workflows...")
        workflow.generate_advanced_workflows()
        print("✅ Setup complete")
        
    elif args.command == 'validate':
        if args.file:
            file_path = Path(args.file)
            if file_path.exists():
                result = workflow.validate_file(file_path)
                print(f"Validation for {file_path.name}:")
                print(f"  Valid: {result.valid}")
                if result.errors:
                    print("  Errors:")
                    for error in result.errors:
                        print(f"    - {error}")
                if result.warnings:
                    print("  Warnings:")
                    for warning in result.warnings:
                        print(f"    - {warning}")
            else:
                print(f"File not found: {args.file}")
        else:
            print("Please specify a file to validate with --file")
            
    elif args.command == 'clean':
        workflow.cleanup_old_files()
        print("✅ Cleanup complete")

if __name__ == '__main__':
    main()
