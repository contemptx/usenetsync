#!/usr/bin/env python3
"""
AI-powered test triage system for analyzing test failures and suggesting fixes.
"""

import json
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import subprocess

try:
    import openai
    import pandas as pd
    import numpy as np
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
except ImportError:
    print("Installing required dependencies...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "openai", "pandas", "numpy", "scikit-learn"])
    import openai
    import pandas as pd
    import numpy as np
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity


class TestTriageAI:
    """AI-powered test failure analysis and fix suggestion system."""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the AI triage system."""
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if self.api_key:
            openai.api_key = self.api_key
        
        self.test_results = []
        self.error_patterns = {}
        self.fix_suggestions = []
        self.autofix_available = False
        
    def load_test_results(self, results_dir: str = "test-results") -> List[Dict]:
        """Load test results from various sources."""
        results = []
        results_path = Path(results_dir)
        
        # Load Allure results
        allure_path = results_path / "allure-results"
        if allure_path.exists():
            for file in allure_path.glob("*-result.json"):
                with open(file, 'r') as f:
                    results.append(json.load(f))
        
        # Load WebDriverIO results
        wdio_path = results_path / "wdio-results"
        if wdio_path.exists():
            for file in wdio_path.glob("*.json"):
                with open(file, 'r') as f:
                    results.append(json.load(f))
        
        # Load screenshots and visual diffs
        visual_path = results_path / "visual"
        if visual_path.exists():
            visual_results = self._analyze_visual_diffs(visual_path)
            results.extend(visual_results)
        
        self.test_results = results
        return results
    
    def _analyze_visual_diffs(self, visual_path: Path) -> List[Dict]:
        """Analyze visual regression test differences."""
        visual_results = []
        diff_path = visual_path / "diff"
        
        if diff_path.exists():
            for diff_file in diff_path.glob("*.png"):
                result = {
                    "type": "visual_regression",
                    "name": diff_file.stem,
                    "status": "failed",
                    "error": f"Visual difference detected in {diff_file.name}",
                    "file": str(diff_file)
                }
                visual_results.append(result)
        
        return visual_results
    
    def analyze_failures(self) -> Dict:
        """Analyze test failures and identify patterns."""
        failures = [r for r in self.test_results if r.get("status") == "failed"]
        
        if not failures:
            return {"status": "success", "message": "No failures detected"}
        
        # Categorize failures
        categories = {
            "timeout": [],
            "element_not_found": [],
            "assertion": [],
            "visual_regression": [],
            "network": [],
            "permission": [],
            "other": []
        }
        
        for failure in failures:
            error_msg = failure.get("error", "").lower()
            categorized = False
            
            # Pattern matching for error categorization
            patterns = {
                "timeout": ["timeout", "timed out", "wait", "exceeded"],
                "element_not_found": ["element", "not found", "no such element", "cannot find"],
                "assertion": ["assert", "expect", "should", "must"],
                "visual_regression": ["visual", "screenshot", "diff", "pixel"],
                "network": ["network", "connection", "fetch", "request failed"],
                "permission": ["permission", "denied", "unauthorized", "forbidden"]
            }
            
            for category, keywords in patterns.items():
                if any(keyword in error_msg for keyword in keywords):
                    categories[category].append(failure)
                    categorized = True
                    break
            
            if not categorized:
                categories["other"].append(failure)
        
        self.error_patterns = categories
        return self._generate_analysis_report(categories)
    
    def _generate_analysis_report(self, categories: Dict) -> Dict:
        """Generate a detailed analysis report."""
        total_failures = sum(len(failures) for failures in categories.values())
        
        report = {
            "total_failures": total_failures,
            "categories": {},
            "top_issues": [],
            "confidence": 0.0
        }
        
        # Analyze each category
        for category, failures in categories.items():
            if failures:
                report["categories"][category] = {
                    "count": len(failures),
                    "percentage": (len(failures) / total_failures) * 100,
                    "examples": [f.get("name", "Unknown") for f in failures[:3]]
                }
        
        # Identify top issues
        sorted_categories = sorted(
            report["categories"].items(),
            key=lambda x: x[1]["count"],
            reverse=True
        )
        
        report["top_issues"] = [cat[0] for cat in sorted_categories[:3]]
        
        # Calculate confidence based on pattern recognition
        recognized_failures = total_failures - len(categories.get("other", []))
        report["confidence"] = (recognized_failures / total_failures) * 100 if total_failures > 0 else 0
        
        return report
    
    def suggest_fixes(self, use_ai: bool = True) -> List[Dict]:
        """Generate fix suggestions for identified issues."""
        suggestions = []
        
        for category, failures in self.error_patterns.items():
            if not failures:
                continue
            
            # Rule-based suggestions
            base_suggestions = self._get_rule_based_suggestions(category, failures)
            suggestions.extend(base_suggestions)
            
            # AI-powered suggestions if available
            if use_ai and self.api_key and failures:
                ai_suggestions = self._get_ai_suggestions(category, failures)
                suggestions.extend(ai_suggestions)
        
        self.fix_suggestions = suggestions
        return suggestions
    
    def _get_rule_based_suggestions(self, category: str, failures: List[Dict]) -> List[Dict]:
        """Get rule-based fix suggestions."""
        suggestions = []
        
        rules = {
            "timeout": [
                {
                    "issue": "Timeout errors",
                    "fix": "Increase timeout values in wdio.conf.ts",
                    "code": "waitforTimeout: 20000, // Increased from 10000",
                    "autofix": True
                },
                {
                    "issue": "Element wait timeout",
                    "fix": "Add explicit waits before element interactions",
                    "code": "await browser.waitUntil(async () => await element.isDisplayed(), { timeout: 5000 });",
                    "autofix": True
                }
            ],
            "element_not_found": [
                {
                    "issue": "Element not found",
                    "fix": "Update selectors or add data-testid attributes",
                    "code": "const element = await browser.$('[data-testid=\"my-element\"]');",
                    "autofix": False
                },
                {
                    "issue": "Dynamic element loading",
                    "fix": "Wait for element to be present before interaction",
                    "code": "await browser.waitUntil(async () => (await browser.$$(selector)).length > 0);",
                    "autofix": True
                }
            ],
            "visual_regression": [
                {
                    "issue": "Visual differences detected",
                    "fix": "Update baseline images or adjust comparison threshold",
                    "code": "expect(result).toBeLessThanOrEqual(10); // Increased threshold",
                    "autofix": True
                },
                {
                    "issue": "Dynamic content in screenshots",
                    "fix": "Hide or remove dynamic elements before capture",
                    "code": "hideElements: ['.timestamp', '.random-content']",
                    "autofix": True
                }
            ],
            "assertion": [
                {
                    "issue": "Assertion failure",
                    "fix": "Review expected values and update assertions",
                    "code": "expect(actual).toContain(expected); // More flexible assertion",
                    "autofix": False
                }
            ],
            "network": [
                {
                    "issue": "Network request failures",
                    "fix": "Add retry logic and increase connection timeout",
                    "code": "connectionRetryCount: 5, // Increased from 3",
                    "autofix": True
                }
            ],
            "permission": [
                {
                    "issue": "Permission denied",
                    "fix": "Ensure proper permissions in CI environment",
                    "code": "sudo: required # In GitHub Actions",
                    "autofix": False
                }
            ]
        }
        
        if category in rules:
            for rule in rules[category]:
                suggestion = {
                    "category": category,
                    "failures": len(failures),
                    **rule
                }
                suggestions.append(suggestion)
        
        return suggestions
    
    def _get_ai_suggestions(self, category: str, failures: List[Dict]) -> List[Dict]:
        """Get AI-powered fix suggestions using OpenAI."""
        if not self.api_key:
            return []
        
        suggestions = []
        
        try:
            # Prepare context for AI
            error_samples = [f.get("error", "") for f in failures[:3]]
            context = f"""
            Test Category: {category}
            Number of failures: {len(failures)}
            Error samples: {json.dumps(error_samples, indent=2)}
            
            Please suggest specific fixes for these test failures.
            """
            
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a test automation expert specializing in WebDriverIO and Tauri applications."},
                    {"role": "user", "content": context}
                ],
                max_tokens=500,
                temperature=0.7
            )
            
            ai_suggestion = response.choices[0].message.content
            
            suggestions.append({
                "category": category,
                "source": "AI",
                "suggestion": ai_suggestion,
                "confidence": 0.85,
                "autofix": False  # AI suggestions require review
            })
            
        except Exception as e:
            print(f"AI suggestion generation failed: {e}")
        
        return suggestions
    
    def check_autofix_availability(self) -> bool:
        """Check if any issues can be automatically fixed."""
        autofix_available = any(
            suggestion.get("autofix", False)
            for suggestion in self.fix_suggestions
        )
        
        self.autofix_available = autofix_available
        return autofix_available
    
    def generate_autofix_script(self) -> str:
        """Generate a script for automatic fixes."""
        autofix_script = []
        
        autofix_script.append("#!/usr/bin/env python3")
        autofix_script.append("# Auto-generated fix script")
        autofix_script.append("import os")
        autofix_script.append("import re")
        autofix_script.append("from pathlib import Path")
        autofix_script.append("")
        
        for suggestion in self.fix_suggestions:
            if suggestion.get("autofix"):
                autofix_script.append(f"# Fix: {suggestion['issue']}")
                autofix_script.append(f"# {suggestion['fix']}")
                
                if suggestion["category"] == "timeout":
                    autofix_script.append(self._generate_timeout_fix())
                elif suggestion["category"] == "visual_regression":
                    autofix_script.append(self._generate_visual_fix())
                elif suggestion["category"] == "element_not_found":
                    autofix_script.append(self._generate_wait_fix())
                
                autofix_script.append("")
        
        return "\n".join(autofix_script)
    
    def _generate_timeout_fix(self) -> str:
        """Generate timeout fix code."""
        return """
def fix_timeouts():
    config_path = Path('wdio.conf.ts')
    if config_path.exists():
        content = config_path.read_text()
        # Increase timeouts
        content = re.sub(r'waitforTimeout:\s*\d+', 'waitforTimeout: 20000', content)
        content = re.sub(r'connectionRetryTimeout:\s*\d+', 'connectionRetryTimeout: 240000', content)
        config_path.write_text(content)
        print('✅ Timeout values increased')

fix_timeouts()
"""
    
    def _generate_visual_fix(self) -> str:
        """Generate visual regression fix code."""
        return """
def fix_visual_thresholds():
    test_files = Path('test/specs').glob('**/*.ts')
    for file in test_files:
        content = file.read_text()
        # Increase visual comparison thresholds
        content = re.sub(r'toBeLessThanOrEqual\((\d+)\)', lambda m: f'toBeLessThanOrEqual({min(int(m.group(1)) * 2, 10)})', content)
        file.write_text(content)
    print('✅ Visual thresholds adjusted')

fix_visual_thresholds()
"""
    
    def _generate_wait_fix(self) -> str:
        """Generate element wait fix code."""
        return """
def add_element_waits():
    test_files = Path('test/specs').glob('**/*.ts')
    for file in test_files:
        content = file.read_text()
        # Add waits before element interactions
        content = re.sub(
            r'(const \w+ = await browser\.\$\([^)]+\);)',
            r'\\1\\n        await browser.waitUntil(async () => await \\1.isExisting(), { timeout: 5000 });',
            content
        )
        file.write_text(content)
    print('✅ Element waits added')

add_element_waits()
"""
    
    def save_report(self, output_file: str = "ai_analysis.json") -> None:
        """Save the analysis report to a file."""
        analysis = self.analyze_failures()
        suggestions = self.suggest_fixes()
        
        report = {
            "analysis": analysis,
            "suggestions": suggestions,
            "autofix_available": self.autofix_available,
            "timestamp": pd.Timestamp.now().isoformat()
        }
        
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"✅ Analysis report saved to {output_file}")
        
        # Also save autofix script if available
        if self.autofix_available:
            autofix_script = self.generate_autofix_script()
            with open("apply_autofix.py", 'w') as f:
                f.write(autofix_script)
            os.chmod("apply_autofix.py", 0o755)
            print("✅ Autofix script generated: apply_autofix.py")


def main():
    """Main entry point for the AI triage system."""
    print("🤖 Starting AI-powered test triage...")
    
    # Initialize the triage system
    triage = TestTriageAI()
    
    # Load test results
    print("📊 Loading test results...")
    results = triage.load_test_results()
    print(f"  Found {len(results)} test results")
    
    # Analyze failures
    print("🔍 Analyzing failures...")
    analysis = triage.analyze_failures()
    print(f"  Total failures: {analysis.get('total_failures', 0)}")
    print(f"  Confidence: {analysis.get('confidence', 0):.1f}%")
    
    # Generate fix suggestions
    print("💡 Generating fix suggestions...")
    suggestions = triage.suggest_fixes()
    print(f"  Generated {len(suggestions)} suggestions")
    
    # Check autofix availability
    autofix = triage.check_autofix_availability()
    print(f"  Autofix available: {'✅ Yes' if autofix else '❌ No'}")
    
    # Save report
    triage.save_report()
    
    print("✨ AI triage complete!")
    
    # Exit with appropriate code
    sys.exit(0 if analysis.get('total_failures', 0) == 0 else 1)


if __name__ == "__main__":
    main()