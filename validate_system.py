#!/usr/bin/env python3
"""
System Validation - Check what's actually working in UsenetSync
"""

import os
import sys
import subprocess
import json
from datetime import datetime
from pathlib import Path

class SystemValidator:
    def __init__(self):
        self.report = {
            "timestamp": datetime.now().isoformat(),
            "components": {},
            "issues": [],
            "recommendations": []
        }
        
    def check_component(self, name, check_func):
        """Check a system component"""
        print(f"Checking {name}...", end=" ")
        try:
            result, details = check_func()
            self.report["components"][name] = {
                "status": "✅ OK" if result else "❌ FAILED",
                "details": details
            }
            print("✅" if result else "❌")
            return result
        except Exception as e:
            self.report["components"][name] = {
                "status": "❌ ERROR",
                "details": str(e)
            }
            print("❌")
            return False
    
    def check_database(self):
        """Check PostgreSQL database"""
        try:
            result = subprocess.run(
                ["pg_isready", "-h", "localhost", "-p", "5432"],
                capture_output=True,
                timeout=5
            )
            if result.returncode == 0:
                # Check if we can connect
                import psycopg2
                conn = psycopg2.connect(
                    host="localhost",
                    port=5432,
                    database="usenet_sync",
                    user="postgres",
                    password="postgres"
                )
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public'")
                table_count = cursor.fetchone()[0]
                cursor.close()
                conn.close()
                return True, f"Database running with {table_count} tables"
            else:
                return False, "PostgreSQL not running"
        except Exception as e:
            return False, str(e)
    
    def check_python_backend(self):
        """Check Python backend modules"""
        issues = []
        working = []
        
        # Test critical imports
        modules = [
            "src.cli",
            "src.core.integrated_backend",
            "src.database.postgresql_manager",
            "src.security.enhanced_security_system",
            "src.networking.bandwidth_controller",
            "src.core.version_control"
        ]
        
        sys.path.insert(0, '/workspace')
        for module in modules:
            try:
                __import__(module)
                working.append(module)
            except Exception as e:
                issues.append(f"{module}: {str(e)[:50]}")
        
        success = len(working) > len(issues)
        details = f"Working: {len(working)}/{len(modules)} modules"
        if issues:
            details += f" | Issues: {', '.join(issues[:3])}"
        
        return success, details
    
    def check_rust_backend(self):
        """Check Rust/Tauri backend"""
        try:
            # Check if cargo is available
            cargo_check = subprocess.run(
                ["cargo", "--version"],
                capture_output=True,
                timeout=5
            )
            
            if cargo_check.returncode != 0:
                return False, "Cargo not found"
            
            # Check if Tauri app builds
            tauri_path = Path("/workspace/usenet-sync-app/src-tauri")
            if not tauri_path.exists():
                return False, "Tauri app not found"
            
            # Check Cargo.toml
            cargo_toml = tauri_path / "Cargo.toml"
            if cargo_toml.exists():
                with open(cargo_toml) as f:
                    content = f.read()
                    has_tauri = "tauri" in content
                    has_deps = "serde" in content and "tokio" in content
                    
                if has_tauri and has_deps:
                    return True, "Tauri app configured correctly"
                else:
                    return False, "Missing dependencies"
            
            return False, "Cargo.toml not found"
            
        except Exception as e:
            return False, str(e)
    
    def check_frontend(self):
        """Check frontend application"""
        try:
            app_path = Path("/workspace/usenet-sync-app")
            
            # Check package.json
            package_json = app_path / "package.json"
            if not package_json.exists():
                return False, "package.json not found"
            
            with open(package_json) as f:
                package = json.load(f)
                
            # Check dependencies
            deps = package.get("dependencies", {})
            required = ["react", "react-dom", "@tauri-apps/api", "zustand"]
            missing = [d for d in required if d not in deps]
            
            if missing:
                return False, f"Missing deps: {', '.join(missing)}"
            
            # Check if build works
            dist_path = app_path / "dist"
            if dist_path.exists():
                return True, "Frontend built successfully"
            else:
                # Try to build
                result = subprocess.run(
                    ["npm", "run", "build"],
                    capture_output=True,
                    timeout=30,
                    cwd=str(app_path)
                )
                if result.returncode == 0:
                    return True, "Frontend builds successfully"
                else:
                    return False, "Build failed"
                    
        except Exception as e:
            return False, str(e)
    
    def check_file_system(self):
        """Check file system structure"""
        required_dirs = [
            "/workspace/src",
            "/workspace/usenet-sync-app",
            "/workspace/usenet-sync-app/src",
            "/workspace/usenet-sync-app/src-tauri"
        ]
        
        missing = []
        for dir_path in required_dirs:
            if not Path(dir_path).exists():
                missing.append(dir_path)
        
        if missing:
            return False, f"Missing dirs: {', '.join(missing)}"
        
        # Check key files
        key_files = [
            "/workspace/src/cli.py",
            "/workspace/src/core/integrated_backend.py",
            "/workspace/usenet-sync-app/src/App.tsx",
            "/workspace/usenet-sync-app/src-tauri/src/main.rs"
        ]
        
        missing_files = []
        for file_path in key_files:
            if not Path(file_path).exists():
                missing_files.append(file_path)
        
        if missing_files:
            return False, f"Missing files: {', '.join(missing_files)}"
        
        return True, "All required files present"
    
    def check_network_config(self):
        """Check network configuration"""
        # Check if we have Usenet credentials
        has_creds = bool(os.getenv("NNTP_HOST") or os.getenv("NNTP_USER"))
        
        # Check localhost connectivity
        try:
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex(('localhost', 5432))
            sock.close()
            postgres_accessible = result == 0
        except:
            postgres_accessible = False
        
        details = []
        if has_creds:
            details.append("NNTP configured")
        if postgres_accessible:
            details.append("PostgreSQL accessible")
            
        return len(details) > 0, " | ".join(details) if details else "No network services"
    
    def run_validation(self):
        """Run complete system validation"""
        print("\n" + "="*60)
        print("🔍 USENETSYNC SYSTEM VALIDATION")
        print("="*60 + "\n")
        
        # Check all components
        checks = [
            ("File System", self.check_file_system),
            ("Database", self.check_database),
            ("Python Backend", self.check_python_backend),
            ("Rust Backend", self.check_rust_backend),
            ("Frontend", self.check_frontend),
            ("Network Config", self.check_network_config)
        ]
        
        results = {}
        for name, check_func in checks:
            results[name] = self.check_component(name, check_func)
        
        # Generate recommendations
        if not results["Database"]:
            self.report["recommendations"].append(
                "Start PostgreSQL: sudo service postgresql start"
            )
        
        if not results["Python Backend"]:
            self.report["recommendations"].append(
                "Install Python deps: pip install -r requirements.txt"
            )
        
        if not results["Rust Backend"]:
            self.report["recommendations"].append(
                "Install Rust: curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh"
            )
        
        # Print summary
        print("\n" + "="*60)
        print("📊 VALIDATION SUMMARY")
        print("="*60)
        
        working = sum(1 for v in results.values() if v)
        total = len(results)
        
        print(f"\nComponents Working: {working}/{total}")
        print("\nComponent Status:")
        for name, status in self.report["components"].items():
            print(f"  {name}: {status['status']}")
            if status['details']:
                print(f"    → {status['details']}")
        
        if self.report["recommendations"]:
            print("\n📌 Recommendations:")
            for rec in self.report["recommendations"]:
                print(f"  • {rec}")
        
        # Overall status
        if working == total:
            print("\n✅ SYSTEM FULLY OPERATIONAL")
            return True
        elif working >= total * 0.7:
            print("\n⚠️  SYSTEM PARTIALLY OPERATIONAL")
            return True
        else:
            print("\n❌ SYSTEM NEEDS ATTENTION")
            return False
        
        # Save report
        report_file = f"validation_report_{int(datetime.now().timestamp())}.json"
        with open(report_file, 'w') as f:
            json.dump(self.report, f, indent=2)
        print(f"\n📄 Full report: {report_file}")

if __name__ == "__main__":
    validator = SystemValidator()
    success = validator.run_validation()
    sys.exit(0 if success else 1)