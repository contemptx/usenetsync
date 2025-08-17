#!/usr/bin/env python3
"""
Automated GitHub Workflow Manager
Provides AI-assisted development workflow with automatic error detection and rollback
"""

import os
import sys
import json
import time
import threading
import subprocess
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class WorkflowEvent:
    """Workflow event"""
    event_type: str
    timestamp: datetime
    file_path: str
    details: Dict
    action_taken: Optional[str] = None

class FileChangeHandler(FileSystemEventHandler):
    """Handle file system changes"""
    
    def __init__(self, workflow_manager):
        self.workflow_manager = workflow_manager
        self.last_events = {}
        self.debounce_time = 2  # seconds
    
    def on_modified(self, event):
        """Handle file modification"""
        if event.is_directory:
            return
        
        file_path = event.src_path
        now = time.time()
        
        # Debounce rapid changes
        if file_path in self.last_events:
            if now - self.last_events[file_path] < self.debounce_time:
                return
        
        self.last_events[file_path] = now
        
        # Only process Python files and configs
        if file_path.endswith(('.py', '.json', '.yml', '.yaml', '.md')):
            self.workflow_manager.handle_file_change(file_path)

class AutomatedWorkflowManager:
    """Manages automated GitHub workflows with AI assistance"""
    
    def __init__(self, project_root: str = None):
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self.workflow_dir = self.project_root / ".workflow"
        self.workflow_dir.mkdir(exist_ok=True)
        
        self.config = self.load_config()
        self.events = []
        self.observer = None
        self.monitoring = False
        
        # Import other managers
        sys.path.insert(0, str(self.project_root))
        try:
            from gitops_manager import GitOpsManager
            from update_github import GitHubUpdater
            self.gitops = GitOpsManager(self.project_root)
            self.updater = GitHubUpdater(self.project_root)
        except ImportError as e:
            logger.error(f"Failed to import managers: {e}")
            sys.exit(1)
        
        # Performance tracking
        self.performance_history = []
        
        # Error patterns to watch for
        self.error_patterns = [
            'SyntaxError',
            'ImportError',
            'ModuleNotFoundError',
            'IndentationError',
            'TypeError',
            'NameError',
            'AttributeError'
        ]
    
    def load_config(self) -> Dict:
        """Load workflow configuration"""
        config_file = self.workflow_dir / "workflow_config.json"
        
        default_config = {
            "auto_deploy": {
                "enabled": True,
                "validate_before_deploy": True,
                "auto_rollback_on_error": True,
                "max_auto_deployments_per_hour": 10
            },
            "monitoring": {
                "watch_directories": ["."],
                "ignore_patterns": [
                    "*.pyc",
                    "__pycache__",
                    ".git",
                    "*.log",
                    "*.db",
                    "data/*",
                    "logs/*"
                ],
                "health_check_interval": 60,
                "performance_tracking": True
            },
            "ai_assistance": {
                "auto_fix_syntax_errors": True,
                "suggest_improvements": True,
                "detect_security_issues": True,
                "performance_analysis": True
            },
            "notifications": {
                "deployment_success": True,
                "deployment_failure": True,
                "health_check_failure": True,
                "performance_degradation": True
            },
            "rollback": {
                "auto_rollback_threshold": 3,  # Auto rollback after 3 failures
                "health_check_timeout": 30,
                "max_rollback_attempts": 3
            }
        }
        
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    user_config = json.load(f)
                    default_config.update(user_config)
            except Exception as e:
                logger.warning(f"Could not load workflow config: {e}")
        else:
            with open(config_file, 'w') as f:
                json.dump(default_config, f, indent=2)
        
        return default_config
    
    def start_monitoring(self):
        """Start file system monitoring"""
        if self.monitoring:
            logger.warning("Monitoring already started")
            return
        
        logger.info("Starting automated workflow monitoring...")
        
        self.observer = Observer()
        handler = FileChangeHandler(self)
        
        for watch_dir in self.config['monitoring']['watch_directories']:
            full_path = self.project_root / watch_dir
            if full_path.exists():
                self.observer.schedule(handler, str(full_path), recursive=True)
                logger.info(f"Watching directory: {full_path}")
        
        self.observer.start()
        self.monitoring = True
        
        # Start health check thread
        if self.config['monitoring']['health_check_interval'] > 0:
            health_thread = threading.Thread(target=self.health_check_loop, daemon=True)
            health_thread.start()
        
        logger.info("Automated workflow monitoring started")
    
    def stop_monitoring(self):
        """Stop file system monitoring"""
        if not self.monitoring:
            return
        
        logger.info("Stopping workflow monitoring...")
        
        if self.observer:
            self.observer.stop()
            self.observer.join()
        
        self.monitoring = False
        logger.info("Workflow monitoring stopped")
    
    def handle_file_change(self, file_path: str):
        """Handle file change event"""
        rel_path = Path(file_path).relative_to(self.project_root)
        
        # Skip ignored patterns
        for pattern in self.config['monitoring']['ignore_patterns']:
            if pattern.replace('*', '') in str(rel_path):
                return
        
        logger.info(f"File changed: {rel_path}")
        
        # Create event
        event = WorkflowEvent(
            event_type='file_change',
            timestamp=datetime.now(),
            file_path=str(rel_path),
            details={'size': Path(file_path).stat().st_size if Path(file_path).exists() else 0}
        )
        
        self.events.append(event)
        
        # Process the change
        if self.config['auto_deploy']['enabled']:
            self.process_file_change(str(rel_path), event)
    
    def process_file_change(self, file_path: str, event: WorkflowEvent):
        """Process a file change"""
        try:
            # Validate the file
            if file_path.endswith('.py'):
                validation_result = self.validate_python_file(file_path)
                event.details['validation'] = validation_result
                
                if not validation_result['valid']:
                    logger.error(f"Validation failed for {file_path}: {validation_result['errors']}")
                    
                    # Try auto-fix if enabled
                    if self.config['ai_assistance']['auto_fix_syntax_errors']:
                        if self.auto_fix_syntax_errors(file_path, validation_result['errors']):
                            event.action_taken = 'auto_fixed_syntax'
                            logger.info(f"Auto-fixed syntax errors in {file_path}")
                        else:
                            event.action_taken = 'syntax_fix_failed'
                            return
                    else:
                        event.action_taken = 'validation_failed'
                        return
            
            # Check deployment rate limiting
            if not self.check_deployment_rate_limit():
                event.action_taken = 'rate_limited'
                logger.warning("Deployment rate limit exceeded")
                return
            
            # Perform intelligent deployment
            components_affected = self.analyze_affected_components([file_path])
            
            if components_affected:
                logger.info(f"Deploying components: {', '.join(components_affected)}")
                success = self.updater.update_components(
                    components_affected,
                    f"Auto-update {', '.join(components_affected)} - {datetime.now().strftime('%H:%M:%S')}"
                )
                
                if success:
                    event.action_taken = 'auto_deployed'
                    logger.info(f"Successfully auto-deployed {file_path}")
                    
                    # Schedule health check
                    threading.Timer(10.0, self.post_deployment_health_check).start()
                else:
                    event.action_taken = 'deployment_failed'
                    logger.error(f"Auto-deployment failed for {file_path}")
            else:
                # Fall back to individual file update
                success = self.updater.update_specific_files(
                    {file_path},
                    f"Auto-update {file_path} - {datetime.now().strftime('%H:%M:%S')}"
                )
                
                if success:
                    event.action_taken = 'file_updated'
                    logger.info(f"Successfully updated {file_path}")
                else:
                    event.action_taken = 'update_failed'
                    logger.error(f"Failed to update {file_path}")
                    
        except Exception as e:
            event.action_taken = 'processing_error'
            event.details['error'] = str(e)
            logger.error(f"Error processing file change for {file_path}: {e}")
    
    def validate_python_file(self, file_path: str) -> Dict:
        """Validate Python file"""
        full_path = self.project_root / file_path
        result = {
            'valid': False,
            'errors': [],
            'warnings': []
        }
        
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Syntax check
            try:
                compile(content, file_path, 'exec')
                result['valid'] = True
            except SyntaxError as e:
                result['errors'].append(f"Syntax error at line {e.lineno}: {e.msg}")
            except Exception as e:
                result['errors'].append(f"Compilation error: {e}")
            
            # Additional checks
            lines = content.split('\n')
            
            # Check for common issues
            for i, line in enumerate(lines, 1):
                stripped = line.strip()
                
                # Check for mixed tabs and spaces
                if '\t' in line and '    ' in line:
                    result['warnings'].append(f"Line {i}: Mixed tabs and spaces")
                
                # Check for long lines
                if len(line) > 120:
                    result['warnings'].append(f"Line {i}: Line too long ({len(line)} chars)")
                
                # Check for potential security issues
                if any(pattern in stripped.lower() for pattern in ['password', 'secret', 'api_key']):
                    if 'test' not in file_path.lower():
                        result['warnings'].append(f"Line {i}: Potential security issue")
        
        except Exception as e:
            result['errors'].append(f"File read error: {e}")
        
        return result
    
    def auto_fix_syntax_errors(self, file_path: str, errors: List[str]) -> bool:
        """Attempt to auto-fix common syntax errors, including indentation"""
        full_path = self.project_root / file_path
        
        try:
            # First, try the advanced indentation repair system
            from indent_repair_system import IndentationAnalyzer, IndentationRepairer
            
            analyzer = IndentationAnalyzer()
            repairer = IndentationRepairer(analyzer)
            
            # Analyze indentation issues
            analysis = analyzer.analyze_file(str(full_path))
            
            if analysis.issues:
                logger.info(f"Found {len(analysis.issues)} indentation issues in {file_path}")
                
                # Attempt to repair indentation
                repair_result = repairer.repair_file(str(full_path), backup=True)
                
                if repair_result['success'] and repair_result['changes_made'] > 0:
                    logger.info(f"Fixed {repair_result['changes_made']} indentation issues in {file_path}")
                    
                    # Check if this fixed the syntax errors
                    with open(full_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    try:
                        compile(content, file_path, 'exec')
                        logger.info(f"Indentation repair fixed syntax errors in {file_path}")
                        return True
                    except SyntaxError:
                        # Still has syntax errors, continue with other fixes
                        pass
            
            # If indentation repair didn't fix everything, try other common fixes
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            lines = content.split('\n')
            modified = False
            
            for error in errors:
                # Check for indentation-related errors
                if any(keyword in error.lower() for keyword in ['indent', 'dedent', 'unindent']):
                    # Indentation errors should have been handled above
                    continue
                
                if 'unexpected EOF while parsing' in error:
                    # Try adding missing closing brackets
                    open_parens = content.count('(') - content.count(')')
                    open_brackets = content.count('[') - content.count(']')
                    open_braces = content.count('{') - content.count('}')
                    
                    if open_parens > 0:
                        lines.append(')' * open_parens)
                        modified = True
                    if open_brackets > 0:
                        lines.append(']' * open_brackets)
                        modified = True
                    if open_braces > 0:
                        lines.append('}' * open_braces)
                        modified = True
                
                elif 'invalid syntax' in error and ':' in error:
                    # Extract line number if available
                    try:
                        line_num = int(error.split('line ')[1].split(':')[0])
                        if 0 < line_num <= len(lines):
                            line = lines[line_num - 1]
                            
                            # Fix missing colons
                            if any(keyword in line for keyword in ['if ', 'for ', 'while ', 'def ', 'class ', 'try', 'except', 'else', 'elif']):
                                if not line.strip().endswith(':'):
                                    lines[line_num - 1] = line.rstrip() + ':'
                                    modified = True
                    except (ValueError, IndexError):
                        pass
            
            if modified:
                # Create backup if not already created by indentation repair
                if not any('backup' in str(f) for f in full_path.parent.glob(f"{full_path.name}.backup*")):
                    backup_path = full_path.with_suffix(full_path.suffix + '.backup')
                    with open(backup_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                
                # Write fixed content
                with open(full_path, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(lines))
                
                logger.info(f"Auto-fixed additional syntax errors in {file_path}")
                return True
        
        except Exception as e:
            logger.error(f"Auto-fix failed for {file_path}: {e}")
        
        return False
    
    def analyze_affected_components(self, files: List[str]) -> List[str]:
        """Analyze which components are affected by file changes"""
        components = set()
        
        for file_path in files:
            filename = Path(file_path).name
            
            # Map files to components
            if filename in ['main.py', 'cli.py', 'setup.py']:
                components.add('core')
            elif 'database' in filename or 'db' in filename:
                components.add('database')
            elif 'security' in filename or 'user' in filename:
                components.add('security')
            elif 'upload' in filename:
                components.add('upload')
            elif 'download' in filename:
                components.add('download')
            elif 'publish' in filename or 'index' in filename:
                components.add('publishing')
            elif 'nntp' in filename or 'network' in filename:
                components.add('networking')
            elif 'monitor' in filename:
                components.add('monitoring')
            elif 'config' in filename:
                components.add('config')
            elif 'test' in filename:
                components.add('tests')
            elif 'integrat' in filename:
                components.add('integration')
        
        return list(components)
    
    def check_deployment_rate_limit(self) -> bool:
        """Check if deployment rate limit is exceeded"""
        max_per_hour = self.config['auto_deploy']['max_auto_deployments_per_hour']
        if max_per_hour <= 0:
            return True
        
        cutoff_time = datetime.now() - timedelta(hours=1)
        recent_deployments = [
            e for e in self.events
            if e.timestamp > cutoff_time and e.action_taken in ['auto_deployed', 'file_updated']
        ]
        
        return len(recent_deployments) < max_per_hour
    
    def post_deployment_health_check(self):
        """Perform health check after deployment"""
        logger.info("Performing post-deployment health check...")
        
        health_result = self.gitops.health_check()
        
        if not health_result['overall']:
            logger.error("Health check failed after deployment")
            
            if self.config['auto_deploy']['auto_rollback_on_error']:
                logger.info("Initiating automatic rollback...")
                success = self.gitops.rollback_deployment()
                
                if success:
                    logger.info("Automatic rollback completed")
                else:
                    logger.error("Automatic rollback failed")
        else:
            logger.info("Post-deployment health check passed")
    
    def health_check_loop(self):
        """Continuous health check loop"""
        interval = self.config['monitoring']['health_check_interval']
        
        while self.monitoring:
            try:
                health_result = self.gitops.health_check()
                
                if not health_result['overall']:
                    logger.warning("Health check failed")
                    
                    # Check if we should auto-rollback
                    recent_failures = [
                        e for e in self.events
                        if e.timestamp > datetime.now() - timedelta(minutes=10)
                        and e.details.get('health_check_failed')
                    ]
                    
                    if len(recent_failures) >= self.config['rollback']['auto_rollback_threshold']:
                        logger.error("Health check failure threshold reached, initiating rollback")
                        self.gitops.rollback_deployment()
                
                # Track performance
                if self.config['monitoring']['performance_tracking']:
                    self.track_performance(health_result)
                
            except Exception as e:
                logger.error(f"Health check loop error: {e}")
            
            time.sleep(interval)
    
    def track_performance(self, health_result: Dict):
        """Track system performance"""
        perf_data = {
            'timestamp': datetime.now(),
            'health_overall': health_result['overall'],
            'check_count': len(health_result['checks']),
            'memory_usage': self.get_memory_usage(),
            'cpu_usage': self.get_cpu_usage()
        }
        
        self.performance_history.append(perf_data)
        
        # Keep only last 100 records
        if len(self.performance_history) > 100:
            self.performance_history = self.performance_history[-100:]
    
    def get_memory_usage(self) -> float:
        """Get current memory usage"""
        try:
            import psutil
            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024  # MB
        except ImportError:
            return 0.0
    
    def get_cpu_usage(self) -> float:
        """Get current CPU usage"""
        try:
            import psutil
            return psutil.cpu_percent(interval=1)
        except ImportError:
            return 0.0
    
    def get_workflow_status(self) -> Dict:
        """Get current workflow status"""
        recent_events = [e for e in self.events if e.timestamp > datetime.now() - timedelta(hours=1)]
        
        return {
            'monitoring': self.monitoring,
            'recent_events': len(recent_events),
            'auto_deploy_enabled': self.config['auto_deploy']['enabled'],
            'last_event': self.events[-1].timestamp.isoformat() if self.events else None,
            'performance_samples': len(self.performance_history),
            'deployment_rate_ok': self.check_deployment_rate_limit()
        }

def main():
    """Main workflow function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Automated GitHub Workflow Manager')
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Start monitoring
    start_parser = subparsers.add_parser('start', help='Start automated monitoring')
    start_parser.add_argument('--daemon', action='store_true', help='Run as daemon')
    
    # Stop monitoring
    subparsers.add_parser('stop', help='Stop monitoring')
    
    # Status
    subparsers.add_parser('status', help='Show workflow status')
    
    # Manual deploy
    deploy_parser = subparsers.add_parser('deploy', help='Manual deployment')
    deploy_parser.add_argument('--components', nargs='+', help='Components to deploy')
    deploy_parser.add_argument('--files', nargs='+', help='Files to deploy')
    
    # Health check
    subparsers.add_parser('health', help='Manual health check')
    
    # Global options
    parser.add_argument('--project-root', help='Project root directory')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    try:
        workflow = AutomatedWorkflowManager(args.project_root)
        
        if args.command == 'start':
            workflow.start_monitoring()
            
            if args.daemon:
                logger.info("Running in daemon mode - press Ctrl+C to stop")
                try:
                    while True:
                        time.sleep(1)
                except KeyboardInterrupt:
                    pass
            else:
                logger.info("Monitoring started - use 'stop' command to stop")
            
        elif args.command == 'stop':
            workflow.stop_monitoring()
            
        elif args.command == 'status':
            status = workflow.get_workflow_status()
            print(json.dumps(status, indent=2, default=str))
            
        elif args.command == 'deploy':
            if args.components:
                success = workflow.updater.update_components(args.components)
            elif args.files:
                success = workflow.updater.update_specific_files(set(args.files))
            else:
                success = workflow.updater.update_modified()
            
            print("Deployment successful" if success else "Deployment failed")
            
        elif args.command == 'health':
            health = workflow.gitops.health_check()
            print(json.dumps(health, indent=2))
            print(f"\nOverall health: {'HEALTHY' if health['overall'] else 'UNHEALTHY'}")
        
        else:
            logger.error(f"Unknown command: {args.command}")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("Workflow interrupted")
        if 'workflow' in locals():
            workflow.stop_monitoring()
    except Exception as e:
        logger.error(f"Workflow failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
