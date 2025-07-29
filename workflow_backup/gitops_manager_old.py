#!/usr/bin/env python3
"""
GitOps Manager for UsenetSync
Advanced GitHub workflow management with deployment, validation, and rollback capabilities
"""

import os
import sys
import json
import shutil
import subprocess
import logging
import hashlib
import time
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass, asdict
from enum import Enum

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DeploymentState(Enum):
    """Deployment states"""
    PREPARING = "preparing"
    VALIDATING = "validating"
    TESTING = "testing"
    DEPLOYING = "deploying"
    DEPLOYED = "deployed"
    FAILED = "failed"
    ROLLING_BACK = "rolling_back"
    ROLLED_BACK = "rolled_back"

@dataclass
class DeploymentRecord:
    """Record of a deployment"""
    deployment_id: str
    timestamp: datetime
    commit_hash: str
    branch: str
    state: DeploymentState
    files_changed: List[str]
    validation_results: Dict
    test_results: Dict
    error_message: Optional[str] = None
    rollback_commit: Optional[str] = None
    deployment_time: Optional[float] = None

@dataclass
class ValidationResult:
    """Validation result"""
    passed: bool
    errors: List[str]
    warnings: List[str]
    files_checked: int
    performance_metrics: Dict

class GitOpsManager:
    """Advanced Git operations manager"""
    
    def __init__(self, project_root: str = None):
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self.gitops_dir = self.project_root / ".gitops"
        self.gitops_dir.mkdir(exist_ok=True)
        
        self.deployments_file = self.gitops_dir / "deployments.json"
        self.config_file = self.gitops_dir / "gitops_config.json"
        
        self.config = self.load_config()
        self.deployments = self.load_deployments()
        
        # Critical files that require extra validation
        self.critical_files = {
            'main.py',
            'enhanced_database_manager.py',
            'production_nntp_client.py',
            'enhanced_security_system.py',
            'enhanced_upload_system.py',
            'enhanced_download_system.py'
        }
        
        # Pre-deployment test commands
        self.test_commands = [
            ['python', '-m', 'py_compile', 'main.py'],
            ['python', '-c', 'import enhanced_database_manager'],
            ['python', '-c', 'import production_nntp_client'],
            ['python', '-c', 'import enhanced_security_system']
        ]
    
    def load_config(self) -> Dict:
        """Load GitOps configuration"""
        default_config = {
            "validation": {
                "require_tests": True,
                "require_syntax_check": True,
                "require_security_check": True,
                "max_file_size_mb": 50,
                "forbidden_patterns": [
                    "password",
                    "secret",
                    "api_key",
                    "private_key"
                ]
            },
            "deployment": {
                "auto_backup": True,
                "max_deployments_history": 50,
                "rollback_timeout_minutes": 10,
                "require_approval_for_critical": True,
                "staging_branch": "staging",
                "production_branch": "main"
            },
            "monitoring": {
                "check_interval_seconds": 30,
                "health_check_commands": [
                    ["python", "-c", "import main; print('OK')"]
                ],
                "performance_thresholds": {
                    "max_deployment_time": 300,
                    "max_validation_time": 120
                }
            },
            "notifications": {
                "on_deployment_success": True,
                "on_deployment_failure": True,
                "on_rollback": True
            }
        }
        
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    user_config = json.load(f)
                    default_config.update(user_config)
            except Exception as e:
                logger.warning(f"Could not load GitOps config: {e}")
        else:
            with open(self.config_file, 'w') as f:
                json.dump(default_config, f, indent=2)
        
        return default_config
    
    def load_deployments(self) -> List[DeploymentRecord]:
        """Load deployment history"""
        if not self.deployments_file.exists():
            return []
        
        try:
            with open(self.deployments_file, 'r') as f:
                data = json.load(f)
                deployments = []
                for item in data:
                    item['timestamp'] = datetime.fromisoformat(item['timestamp'])
                    item['state'] = DeploymentState(item['state'])
                    deployments.append(DeploymentRecord(**item))
                return deployments
        except Exception as e:
            logger.error(f"Failed to load deployments: {e}")
            return []
    
    def save_deployments(self):
        """Save deployment history"""
        try:
            data = []
            for deployment in self.deployments:
                item = asdict(deployment)
                item['timestamp'] = deployment.timestamp.isoformat()
                item['state'] = deployment.state.value
                data.append(item)
            
            with open(self.deployments_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save deployments: {e}")
    
    def get_current_commit(self) -> str:
        """Get current commit hash"""
        try:
            result = subprocess.run(
                ['git', 'rev-parse', 'HEAD'],
                capture_output=True, text=True, cwd=self.project_root
            )
            return result.stdout.strip() if result.returncode == 0 else ""
        except Exception:
            return ""
    
    def get_current_branch(self) -> str:
        """Get current branch name"""
        try:
            result = subprocess.run(
                ['git', 'branch', '--show-current'],
                capture_output=True, text=True, cwd=self.project_root
            )
            return result.stdout.strip() if result.returncode == 0 else ""
        except Exception:
            return ""
    
    def get_changed_files(self, since_commit: str = None) -> List[str]:
        """Get list of changed files"""
        try:
            if since_commit:
                cmd = ['git', 'diff', '--name-only', since_commit]
            else:
                cmd = ['git', 'diff', '--name-only', 'HEAD~1']
            
            result = subprocess.run(
                cmd, capture_output=True, text=True, cwd=self.project_root
            )
            
            if result.returncode == 0:
                files = [f for f in result.stdout.strip().split('\n') if f]
                return files
            return []
        except Exception:
            return []
    
    def validate_files(self, files: List[str]) -> ValidationResult:
        """Comprehensive file validation"""
        start_time = time.time()
        errors = []
        warnings = []
        files_checked = 0
        
        logger.info(f"Validating {len(files)} files...")
        
        for file_path in files:
            full_path = self.project_root / file_path
            if not full_path.exists():
                warnings.append(f"File not found: {file_path}")
                continue
            
            files_checked += 1
            
            # Check file size
            file_size = full_path.stat().st_size / (1024 * 1024)  # MB
            max_size = self.config['validation']['max_file_size_mb']
            if file_size > max_size:
                errors.append(f"File too large: {file_path} ({file_size:.1f}MB > {max_size}MB)")
            
            # Check for forbidden patterns
            if file_path.endswith('.py'):
                try:
                    with open(full_path, 'r', encoding='utf-8') as f:
                        content = f.read().lower()
                    
                    for pattern in self.config['validation']['forbidden_patterns']:
                        if pattern in content and 'test' not in file_path.lower():
                            warnings.append(f"Potential security issue in {file_path}: contains '{pattern}'")
                    
                    # Syntax check
                    try:
                        compile(open(full_path, 'r', encoding='utf-8').read(), file_path, 'exec')
                    except SyntaxError as e:
                        errors.append(f"Syntax error in {file_path}: {e}")
                    
                except UnicodeDecodeError:
                    errors.append(f"Encoding error in {file_path}")
                except Exception as e:
                    errors.append(f"Validation error in {file_path}: {e}")
        
        validation_time = time.time() - start_time
        performance_metrics = {
            'validation_time': validation_time,
            'files_per_second': files_checked / validation_time if validation_time > 0 else 0
        }
        
        # Check performance thresholds
        max_validation_time = self.config['monitoring']['performance_thresholds']['max_validation_time']
        if validation_time > max_validation_time:
            warnings.append(f"Validation took too long: {validation_time:.1f}s > {max_validation_time}s")
        
        passed = len(errors) == 0
        
        return ValidationResult(
            passed=passed,
            errors=errors,
            warnings=warnings,
            files_checked=files_checked,
            performance_metrics=performance_metrics
        )
    
    def run_tests(self) -> Dict:
        """Run pre-deployment tests"""
        logger.info("Running pre-deployment tests...")
        test_results = {
            'passed': True,
            'results': [],
            'total_time': 0
        }
        
        start_time = time.time()
        
        for test_cmd in self.test_commands:
            cmd_start = time.time()
            try:
                result = subprocess.run(
                    test_cmd, 
                    capture_output=True, 
                    text=True, 
                    cwd=self.project_root,
                    timeout=60
                )
                
                cmd_time = time.time() - cmd_start
                
                test_result = {
                    'command': ' '.join(test_cmd),
                    'passed': result.returncode == 0,
                    'output': result.stdout,
                    'error': result.stderr,
                    'time': cmd_time
                }
                
                test_results['results'].append(test_result)
                
                if result.returncode != 0:
                    test_results['passed'] = False
                    logger.error(f"Test failed: {' '.join(test_cmd)}")
                    logger.error(f"Error: {result.stderr}")
                else:
                    logger.info(f"Test passed: {' '.join(test_cmd)} ({cmd_time:.2f}s)")
                    
            except subprocess.TimeoutExpired:
                test_results['passed'] = False
                test_results['results'].append({
                    'command': ' '.join(test_cmd),
                    'passed': False,
                    'output': '',
                    'error': 'Test timed out',
                    'time': 60
                })
                logger.error(f"Test timed out: {' '.join(test_cmd)}")
            except Exception as e:
                test_results['passed'] = False
                test_results['results'].append({
                    'command': ' '.join(test_cmd),
                    'passed': False,
                    'output': '',
                    'error': str(e),
                    'time': 0
                })
                logger.error(f"Test error: {' '.join(test_cmd)}: {e}")
        
        test_results['total_time'] = time.time() - start_time
        return test_results
    
    def create_deployment_backup(self, deployment_id: str) -> bool:
        """Create deployment backup"""
        try:
            backup_dir = self.gitops_dir / "backups" / deployment_id
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            # Save current commit
            current_commit = self.get_current_commit()
            backup_info = {
                'deployment_id': deployment_id,
                'commit_hash': current_commit,
                'branch': self.get_current_branch(),
                'timestamp': datetime.now().isoformat(),
                'files': list(self.project_root.glob('*.py'))
            }
            
            with open(backup_dir / 'backup_info.json', 'w') as f:
                json.dump(backup_info, f, indent=2, default=str)
            
            logger.info(f"Created backup for deployment {deployment_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            return False
    
    def deploy_with_validation(self, commit_message: str = None, force: bool = False) -> DeploymentRecord:
        """Deploy with full validation pipeline"""
        deployment_id = hashlib.sha256(
            f"{time.time()}:{self.get_current_commit()}".encode()
        ).hexdigest()[:16]
        
        logger.info(f"Starting deployment {deployment_id}")
        
        # Create deployment record
        deployment = DeploymentRecord(
            deployment_id=deployment_id,
            timestamp=datetime.now(),
            commit_hash=self.get_current_commit(),
            branch=self.get_current_branch(),
            state=DeploymentState.PREPARING,
            files_changed=self.get_changed_files(),
            validation_results={},
            test_results={}
        )
        
        start_time = time.time()
        
        try:
            # Check if critical files changed
            critical_changed = any(
                Path(f).name in self.critical_files 
                for f in deployment.files_changed
            )
            
            if critical_changed and not force:
                if self.config['deployment']['require_approval_for_critical']:
                    logger.warning("Critical files changed - manual approval required")
                    approval = input("Critical files changed. Continue? (yes/no): ")
                    if approval.lower() != 'yes':
                        deployment.state = DeploymentState.FAILED
                        deployment.error_message = "Deployment cancelled - critical files changed"
                        self.deployments.append(deployment)
                        self.save_deployments()
                        return deployment
            
            # Create backup
            if self.config['deployment']['auto_backup']:
                if not self.create_deployment_backup(deployment_id):
                    if not force:
                        deployment.state = DeploymentState.FAILED
                        deployment.error_message = "Failed to create backup"
                        self.deployments.append(deployment)
                        self.save_deployments()
                        return deployment
            
            # Validation phase
            deployment.state = DeploymentState.VALIDATING
            logger.info("Validation phase...")
            
            validation_result = self.validate_files(deployment.files_changed)
            deployment.validation_results = asdict(validation_result)
            
            if not validation_result.passed and not force:
                deployment.state = DeploymentState.FAILED
                deployment.error_message = f"Validation failed: {'; '.join(validation_result.errors)}"
                self.deployments.append(deployment)
                self.save_deployments()
                return deployment
            
            # Testing phase
            if self.config['validation']['require_tests']:
                deployment.state = DeploymentState.TESTING
                logger.info("Testing phase...")
                
                test_results = self.run_tests()
                deployment.test_results = test_results
                
                if not test_results['passed'] and not force:
                    deployment.state = DeploymentState.FAILED
                    deployment.error_message = "Tests failed"
                    self.deployments.append(deployment)
                    self.save_deployments()
                    return deployment
            
            # Deployment phase
            deployment.state = DeploymentState.DEPLOYING
            logger.info("Deployment phase...")
            
            # Git operations
            try:
                # Add all changed files
                for file_path in deployment.files_changed:
                    cmd = ['git', 'add', file_path]
                    result = subprocess.run(cmd, cwd=self.project_root, capture_output=True)
                    if result.returncode != 0:
                        raise Exception(f"Failed to add {file_path}")
                
                # Commit
                if not commit_message:
                    commit_message = f"Automated deployment {deployment_id}"
                
                cmd = ['git', 'commit', '-m', commit_message]
                result = subprocess.run(cmd, cwd=self.project_root, capture_output=True)
                if result.returncode != 0:
                    logger.info("No changes to commit")
                
                # Push
                cmd = ['git', 'push']
                result = subprocess.run(cmd, cwd=self.project_root, capture_output=True)
                if result.returncode != 0:
                    raise Exception(f"Push failed: {result.stderr.decode()}")
                
                # Update deployment record
                deployment.state = DeploymentState.DEPLOYED
                deployment.deployment_time = time.time() - start_time
                
                logger.info(f"Deployment {deployment_id} completed successfully in {deployment.deployment_time:.2f}s")
                
            except Exception as e:
                deployment.state = DeploymentState.FAILED
                deployment.error_message = str(e)
                logger.error(f"Deployment failed: {e}")
        
        except Exception as e:
            deployment.state = DeploymentState.FAILED
            deployment.error_message = str(e)
            logger.error(f"Deployment pipeline failed: {e}")
        
        # Save deployment record
        self.deployments.append(deployment)
        self.save_deployments()
        
        # Cleanup old deployments
        self.cleanup_old_deployments()
        
        return deployment
    
    def rollback_deployment(self, deployment_id: str = None, to_commit: str = None) -> bool:
        """Rollback to previous deployment or specific commit"""
        logger.info(f"Starting rollback...")
        
        try:
            if to_commit:
                target_commit = to_commit
            elif deployment_id:
                # Find deployment
                deployment = next((d for d in self.deployments if d.deployment_id == deployment_id), None)
                if not deployment:
                    logger.error(f"Deployment {deployment_id} not found")
                    return False
                target_commit = deployment.commit_hash
            else:
                # Rollback to previous successful deployment
                successful_deployments = [
                    d for d in reversed(self.deployments) 
                    if d.state == DeploymentState.DEPLOYED
                ]
                if len(successful_deployments) < 2:
                    logger.error("No previous successful deployment found")
                    return False
                target_commit = successful_deployments[1].commit_hash
            
            logger.info(f"Rolling back to commit {target_commit[:8]}...")
            
            # Create rollback record
            rollback_deployment = DeploymentRecord(
                deployment_id=f"rollback_{int(time.time())}",
                timestamp=datetime.now(),
                commit_hash=target_commit,
                branch=self.get_current_branch(),
                state=DeploymentState.ROLLING_BACK,
                files_changed=[],
                validation_results={},
                test_results={},
                rollback_commit=self.get_current_commit()
            )
            
            # Perform rollback
            cmd = ['git', 'reset', '--hard', target_commit]
            result = subprocess.run(cmd, cwd=self.project_root, capture_output=True)
            
            if result.returncode != 0:
                logger.error(f"Rollback failed: {result.stderr.decode()}")
                rollback_deployment.state = DeploymentState.FAILED
                rollback_deployment.error_message = result.stderr.decode()
                return False
            
            # Force push if needed
            cmd = ['git', 'push', '--force']
            result = subprocess.run(cmd, cwd=self.project_root, capture_output=True)
            
            if result.returncode != 0:
                logger.warning(f"Force push failed: {result.stderr.decode()}")
            
            rollback_deployment.state = DeploymentState.ROLLED_BACK
            self.deployments.append(rollback_deployment)
            self.save_deployments()
            
            logger.info(f"Rollback completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Rollback failed: {e}")
            return False
    
    def health_check(self) -> Dict:
        """Perform system health check"""
        health_status = {
            'overall': True,
            'checks': [],
            'timestamp': datetime.now().isoformat()
        }
        
        for check_cmd in self.config['monitoring']['health_check_commands']:
            try:
                result = subprocess.run(
                    check_cmd,
                    capture_output=True,
                    text=True,
                    cwd=self.project_root,
                    timeout=30
                )
                
                check_result = {
                    'command': ' '.join(check_cmd),
                    'passed': result.returncode == 0,
                    'output': result.stdout,
                    'error': result.stderr
                }
                
                if result.returncode != 0:
                    health_status['overall'] = False
                
                health_status['checks'].append(check_result)
                
            except Exception as e:
                health_status['overall'] = False
                health_status['checks'].append({
                    'command': ' '.join(check_cmd),
                    'passed': False,
                    'output': '',
                    'error': str(e)
                })
        
        return health_status
    
    def get_deployment_status(self, deployment_id: str = None) -> Dict:
        """Get deployment status"""
        if deployment_id:
            deployment = next((d for d in self.deployments if d.deployment_id == deployment_id), None)
            if not deployment:
                return {'error': 'Deployment not found'}
            
            return {
                'deployment': asdict(deployment),
                'health': self.health_check()
            }
        else:
            # Get latest deployment
            if not self.deployments:
                return {'error': 'No deployments found'}
            
            latest = self.deployments[-1]
            return {
                'latest_deployment': asdict(latest),
                'health': self.health_check(),
                'total_deployments': len(self.deployments)
            }
    
    def cleanup_old_deployments(self):
        """Clean up old deployment records"""
        max_deployments = self.config['deployment']['max_deployments_history']
        if len(self.deployments) > max_deployments:
            self.deployments = self.deployments[-max_deployments:]
            self.save_deployments()
            logger.info(f"Cleaned up old deployments, keeping last {max_deployments}")
    
    def list_deployments(self, limit: int = 10) -> List[Dict]:
        """List recent deployments"""
        recent_deployments = list(reversed(self.deployments))[:limit]
        return [asdict(d) for d in recent_deployments]

def main():
    """Main GitOps function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='GitOps Manager for UsenetSync')
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Deploy command
    deploy_parser = subparsers.add_parser('deploy', help='Deploy with validation')
    deploy_parser.add_argument('--message', '-m', help='Commit message')
    deploy_parser.add_argument('--force', action='store_true', help='Force deployment')
    
    # Rollback command
    rollback_parser = subparsers.add_parser('rollback', help='Rollback deployment')
    rollback_parser.add_argument('--deployment-id', help='Deployment ID to rollback to')
    rollback_parser.add_argument('--commit', help='Commit hash to rollback to')
    
    # Status command
    status_parser = subparsers.add_parser('status', help='Get deployment status')
    status_parser.add_argument('--deployment-id', help='Specific deployment ID')
    
    # Health check command
    subparsers.add_parser('health', help='Perform health check')
    
    # List deployments command
    list_parser = subparsers.add_parser('list', help='List deployments')
    list_parser.add_argument('--limit', type=int, default=10, help='Number of deployments to show')
    
    # Validate command
    validate_parser = subparsers.add_parser('validate', help='Validate files only')
    validate_parser.add_argument('files', nargs='*', help='Files to validate')
    
    # Global options
    parser.add_argument('--project-root', help='Project root directory')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    try:
        gitops = GitOpsManager(args.project_root)
        
        if args.command == 'deploy':
            deployment = gitops.deploy_with_validation(args.message, args.force)
            print(f"Deployment {deployment.deployment_id}: {deployment.state.value}")
            if deployment.error_message:
                print(f"Error: {deployment.error_message}")
            
        elif args.command == 'rollback':
            success = gitops.rollback_deployment(args.deployment_id, args.commit)
            print("Rollback successful" if success else "Rollback failed")
            
        elif args.command == 'status':
            status = gitops.get_deployment_status(args.deployment_id)
            print(json.dumps(status, indent=2, default=str))
            
        elif args.command == 'health':
            health = gitops.health_check()
            print(json.dumps(health, indent=2))
            print(f"\nOverall health: {'HEALTHY' if health['overall'] else 'UNHEALTHY'}")
            
        elif args.command == 'list':
            deployments = gitops.list_deployments(args.limit)
            for deployment in deployments:
                print(f"{deployment['deployment_id'][:8]} - {deployment['state']} - {deployment['timestamp']}")
            
        elif args.command == 'validate':
            files = args.files if args.files else gitops.get_changed_files()
            result = gitops.validate_files(files)
            print(f"Validation: {'PASSED' if result.passed else 'FAILED'}")
            print(f"Files checked: {result.files_checked}")
            if result.errors:
                print("Errors:")
                for error in result.errors:
                    print(f"  - {error}")
            if result.warnings:
                print("Warnings:")
                for warning in result.warnings:
                    print(f"  - {warning}")
        
        else:
            logger.error(f"Unknown command: {args.command}")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("GitOps operation interrupted")
        sys.exit(1)
    except Exception as e:
        logger.error(f"GitOps operation failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
