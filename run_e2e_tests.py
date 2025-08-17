#!/usr/bin/env python3
"""
E2E Test Runner - Validates all UsenetSync functionality
"""

import os
import sys
import json
import time
import subprocess
import tempfile
from pathlib import Path
from datetime import datetime

class E2ETestRunner:
    def __init__(self):
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "tests": [],
            "passed": 0,
            "failed": 0,
            "skipped": 0
        }
        
    def log(self, level, msg):
        print(f"[{datetime.now().strftime('%H:%M:%S')}] [{level}] {msg}")
        
    def run_test(self, name, test_func):
        """Run a single test"""
        self.log("TEST", f"Running: {name}")
        try:
            result = test_func()
            if result:
                self.log("PASS", f"✅ {name}")
                self.results["passed"] += 1
                self.results["tests"].append({"name": name, "status": "passed"})
            else:
                self.log("FAIL", f"❌ {name}")
                self.results["failed"] += 1
                self.results["tests"].append({"name": name, "status": "failed"})
            return result
        except Exception as e:
            self.log("ERROR", f"❌ {name}: {str(e)}")
            self.results["failed"] += 1
            self.results["tests"].append({"name": name, "status": "error", "error": str(e)})
            return False
    
    def test_python_backend(self):
        """Test Python backend is functional"""
        try:
            # Test imports
            sys.path.insert(0, '/workspace/src')
            
            # Test database config
            from database.postgresql_manager import PostgresConfig
            config = PostgresConfig(
                host="localhost",
                port=5432,
                database="usenet_sync",
                user="postgres",
                password="postgres"
            )
            
            # Test integrated backend
            from core.integrated_backend import create_integrated_backend
            backend = create_integrated_backend({
                "host": "localhost",
                "port": 5432,
                "database": "usenet_sync",
                "user": "postgres",
                "password": "postgres"
            })
            
            return True
        except Exception as e:
            self.log("ERROR", f"Python backend error: {e}")
            return False
    
    def test_database_setup(self):
        """Test database is accessible"""
        try:
            import psycopg2
            conn = psycopg2.connect(
                host="localhost",
                port=5432,
                database="usenet_sync",
                user="postgres",
                password="postgres"
            )
            cursor = conn.cursor()
            
            # Create tables if needed
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS shares (
                    share_id TEXT PRIMARY KEY,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS files (
                    file_id TEXT PRIMARY KEY,
                    file_name TEXT,
                    file_size BIGINT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.commit()
            cursor.close()
            conn.close()
            return True
        except Exception as e:
            self.log("ERROR", f"Database error: {e}")
            return False
    
    def test_rust_backend(self):
        """Test Rust/Tauri backend compiles"""
        try:
            result = subprocess.run(
                ["cargo", "check", "--manifest-path", "usenet-sync-app/src-tauri/Cargo.toml"],
                capture_output=True,
                timeout=30,
                cwd="/workspace"
            )
            return result.returncode == 0
        except Exception as e:
            self.log("ERROR", f"Rust backend error: {e}")
            return False
    
    def test_frontend_build(self):
        """Test frontend builds successfully"""
        try:
            result = subprocess.run(
                ["npm", "run", "build"],
                capture_output=True,
                timeout=60,
                cwd="/workspace/usenet-sync-app"
            )
            return result.returncode == 0
        except Exception as e:
            self.log("ERROR", f"Frontend build error: {e}")
            return False
    
    def test_file_operations(self):
        """Test basic file operations"""
        try:
            # Create test file
            test_dir = Path("/tmp/usenet_test")
            test_dir.mkdir(exist_ok=True)
            
            test_file = test_dir / "test.txt"
            test_file.write_text("Test content for E2E")
            
            # Test encryption
            sys.path.insert(0, '/workspace/src')
            from security.enhanced_security_system import EnhancedSecuritySystem
            from database.postgresql_manager import PostgresConfig, ShardedPostgreSQLManager
            
            config = PostgresConfig(
                host="localhost",
                port=5432,
                database="usenet_sync",
                user="postgres",
                password="postgres"
            )
            
            db_manager = ShardedPostgreSQLManager(config)
            security = EnhancedSecuritySystem(db_manager)
            
            # Basic encryption test
            data = b"Test data"
            encrypted = security.encrypt_file_content(data, "password")
            decrypted = security.decrypt_file_content(encrypted, "password")
            
            return decrypted == data
        except Exception as e:
            self.log("ERROR", f"File operations error: {e}")
            return False
    
    def test_version_control(self):
        """Test version control system"""
        try:
            sys.path.insert(0, '/workspace/src')
            from core.version_control import VersionControl
            from database.postgresql_manager import PostgresConfig, ShardedPostgreSQLManager
            
            config = PostgresConfig(
                host="localhost",
                port=5432,
                database="usenet_sync",
                user="postgres",
                password="postgres"
            )
            
            db_manager = ShardedPostgreSQLManager(config)
            vc = VersionControl(db_manager)
            
            # Create version control tables
            import asyncio
            async def init_vc():
                await vc.initialize()
                return True
            
            return asyncio.run(init_vc())
        except Exception as e:
            self.log("ERROR", f"Version control error: {e}")
            return False
    
    def test_bandwidth_control(self):
        """Test bandwidth control"""
        try:
            sys.path.insert(0, '/workspace/src')
            from networking.bandwidth_controller import BandwidthController
            
            controller = BandwidthController()
            controller.set_upload_limit(1024 * 1024)  # 1 MB/s
            
            # Test token consumption
            import asyncio
            async def test_bandwidth():
                consumed = await controller.consume_upload_tokens(1024)
                return consumed
            
            return asyncio.run(test_bandwidth())
        except Exception as e:
            self.log("ERROR", f"Bandwidth control error: {e}")
            return False
    
    def test_logging_system(self):
        """Test logging system"""
        try:
            sys.path.insert(0, '/workspace/src')
            from core.log_manager import LogManager, LogLevel
            from pathlib import Path
            
            log_dir = Path("/tmp/usenet_logs")
            log_dir.mkdir(exist_ok=True)
            
            # Create log manager without database for simplicity
            log_manager = LogManager(log_dir=log_dir, db_manager=None)
            log_manager.start()
            
            # Write test log
            log_manager.log(LogLevel.INFO, "E2E test log entry", "test", {"test": True})
            
            # Check log file exists
            log_files = list(log_dir.glob("*.log"))
            log_manager.stop()
            
            return len(log_files) > 0
        except Exception as e:
            self.log("ERROR", f"Logging system error: {e}")
            return False
    
    def test_cli_interface(self):
        """Test CLI interface"""
        try:
            result = subprocess.run(
                ["python3", "src/cli.py", "--help"],
                capture_output=True,
                timeout=10,
                cwd="/workspace"
            )
            return result.returncode == 0 and b"Usage:" in result.stdout
        except Exception as e:
            self.log("ERROR", f"CLI interface error: {e}")
            return False
    
    def run_all_tests(self):
        """Run all E2E tests"""
        print("\n" + "="*60)
        print("🧪 USENETSYNC E2E TEST SUITE")
        print("="*60 + "\n")
        
        tests = [
            ("Database Setup", self.test_database_setup),
            ("Python Backend", self.test_python_backend),
            ("Rust Backend Compilation", self.test_rust_backend),
            ("Frontend Build", self.test_frontend_build),
            ("File Operations", self.test_file_operations),
            ("Version Control", self.test_version_control),
            ("Bandwidth Control", self.test_bandwidth_control),
            ("Logging System", self.test_logging_system),
            ("CLI Interface", self.test_cli_interface),
        ]
        
        for name, test_func in tests:
            self.run_test(name, test_func)
            time.sleep(0.5)  # Small delay between tests
        
        # Generate report
        self.generate_report()
        
    def generate_report(self):
        """Generate test report"""
        print("\n" + "="*60)
        print("📊 TEST RESULTS")
        print("="*60)
        
        total = self.results["passed"] + self.results["failed"] + self.results["skipped"]
        if total > 0:
            pass_rate = (self.results["passed"] / total) * 100
        else:
            pass_rate = 0
            
        print(f"""
Total Tests:  {total}
Passed:       {self.results["passed"]} ✅
Failed:       {self.results["failed"]} ❌
Skipped:      {self.results["skipped"]} ⏭️
Pass Rate:    {pass_rate:.1f}%
        """)
        
        if self.results["failed"] > 0:
            print("\n❌ FAILED TESTS:")
            for test in self.results["tests"]:
                if test["status"] in ["failed", "error"]:
                    print(f"  • {test['name']}")
                    if "error" in test:
                        print(f"    Error: {test['error'][:100]}")
        
        # Save report
        report_file = f"e2e_report_{int(time.time())}.json"
        with open(report_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        print(f"\n📄 Report saved to: {report_file}")
        
        if self.results["failed"] == 0:
            print("\n✅ ALL TESTS PASSED!")
        else:
            print(f"\n⚠️  {self.results['failed']} tests need attention")
        
        return self.results["failed"] == 0

if __name__ == "__main__":
    # Ensure we have cargo
    subprocess.run(["source", "/usr/local/cargo/env"], shell=True)
    
    runner = E2ETestRunner()
    runner.run_all_tests()
    sys.exit(0 if runner.results["failed"] == 0 else 1)