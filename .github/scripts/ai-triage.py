#!/usr/bin/env python3
"""
AI-powered test failure triage and analysis
"""

import os
import sys
import json
import glob
import base64
import xmltodict
from pathlib import Path
from typing import Dict, List, Any, Optional
import cv2
import numpy as np
from PIL import Image
import openai
from langchain.chat_models import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage

class TestFailureAnalyzer:
    """Analyzes test failures using AI"""
    
    def __init__(self):
        self.openai_key = os.environ.get('OPENAI_API_KEY')
        if not self.openai_key:
            print("Warning: OPENAI_API_KEY not set, using mock analysis")
            self.use_mock = True
        else:
            self.use_mock = False
            openai.api_key = self.openai_key
            self.llm = ChatOpenAI(
                model="gpt-4-vision-preview",
                temperature=0.3,
                max_tokens=4096
            )
    
    def analyze_failures(self, artifacts_path: str) -> Dict[str, Any]:
        """Analyze all test failures"""
        results = {
            'failures': [],
            'patterns': [],
            'suggestions': [],
            'autofix_possible': False
        }
        
        # Parse JUnit XML results
        junit_files = glob.glob(f"{artifacts_path}/**/results-*.xml", recursive=True)
        for junit_file in junit_files:
            failures = self._parse_junit(junit_file)
            results['failures'].extend(failures)
        
        # Analyze screenshots
        screenshot_files = glob.glob(f"{artifacts_path}/**/visual-screenshots/**/*.png", recursive=True)
        for screenshot in screenshot_files:
            if 'diff' in screenshot or 'actual' in screenshot:
                analysis = self._analyze_screenshot(screenshot)
                if analysis:
                    results['failures'].append(analysis)
        
        # Find patterns
        results['patterns'] = self._find_patterns(results['failures'])
        
        # Generate suggestions
        results['suggestions'] = self._generate_suggestions(results)
        
        # Check if autofix is possible
        results['autofix_possible'] = self._can_autofix(results)
        
        return results
    
    def _parse_junit(self, junit_file: str) -> List[Dict[str, Any]]:
        """Parse JUnit XML file for failures"""
        failures = []
        
        try:
            with open(junit_file, 'r') as f:
                data = xmltodict.parse(f.read())
            
            testsuites = data.get('testsuites', data.get('testsuite', {}))
            if isinstance(testsuites, dict):
                testsuites = [testsuites]
            
            for suite in testsuites:
                if 'testcase' in suite:
                    testcases = suite['testcase']
                    if not isinstance(testcases, list):
                        testcases = [testcases]
                    
                    for testcase in testcases:
                        if 'failure' in testcase or 'error' in testcase:
                            failure = {
                                'type': 'test_failure',
                                'suite': suite.get('@name', 'unknown'),
                                'test': testcase.get('@name', 'unknown'),
                                'classname': testcase.get('@classname', ''),
                                'time': float(testcase.get('@time', 0))
                            }
                            
                            if 'failure' in testcase:
                                failure['message'] = testcase['failure'].get('@message', '')
                                failure['details'] = testcase['failure'].get('#text', '')
                            elif 'error' in testcase:
                                failure['message'] = testcase['error'].get('@message', '')
                                failure['details'] = testcase['error'].get('#text', '')
                            
                            failures.append(failure)
        
        except Exception as e:
            print(f"Error parsing {junit_file}: {e}")
        
        return failures
    
    def _analyze_screenshot(self, screenshot_path: str) -> Optional[Dict[str, Any]]:
        """Analyze a screenshot for visual differences"""
        if self.use_mock:
            return self._mock_screenshot_analysis(screenshot_path)
        
        try:
            # Load image
            image = cv2.imread(screenshot_path)
            
            # Convert to base64 for API
            _, buffer = cv2.imencode('.png', image)
            image_base64 = base64.b64encode(buffer).decode('utf-8')
            
            # Prepare message for GPT-4 Vision
            messages = [
                SystemMessage(content="""You are an expert at analyzing GUI test failures.
                Analyze this screenshot and identify:
                1. What UI elements are incorrect or misaligned
                2. Any visual regressions or styling issues
                3. Missing or incorrect content
                4. Potential causes of the issues
                5. Specific fixes that could resolve the problems
                
                Provide your analysis in JSON format."""),
                HumanMessage(content=[
                    {"type": "text", "text": f"Analyze this test failure screenshot from {Path(screenshot_path).name}:"},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_base64}"}}
                ])
            ]
            
            response = self.llm.invoke(messages)
            analysis = json.loads(response.content)
            
            return {
                'type': 'visual_regression',
                'screenshot': screenshot_path,
                'analysis': analysis
            }
        
        except Exception as e:
            print(f"Error analyzing screenshot {screenshot_path}: {e}")
            return None
    
    def _mock_screenshot_analysis(self, screenshot_path: str) -> Dict[str, Any]:
        """Mock analysis for testing without API"""
        filename = Path(screenshot_path).name
        
        if 'dashboard' in filename:
            return {
                'type': 'visual_regression',
                'screenshot': screenshot_path,
                'analysis': {
                    'issues': ['Stats widget misaligned', 'Dark mode toggle not visible'],
                    'causes': ['CSS flexbox issue', 'Missing component import'],
                    'fixes': [
                        'Add display: flex to stats container',
                        'Import DarkModeToggle component'
                    ]
                }
            }
        elif 'folder' in filename:
            return {
                'type': 'visual_regression',
                'screenshot': screenshot_path,
                'analysis': {
                    'issues': ['Folder list not rendering', 'Add button disabled'],
                    'causes': ['API connection failed', 'Missing permissions'],
                    'fixes': [
                        'Check backend API status',
                        'Verify folder permissions'
                    ]
                }
            }
        
        return None
    
    def _find_patterns(self, failures: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Find patterns in failures"""
        patterns = []
        
        # Group by failure type
        failure_types = {}
        for failure in failures:
            ftype = failure.get('type', 'unknown')
            if ftype not in failure_types:
                failure_types[ftype] = []
            failure_types[ftype].append(failure)
        
        # Analyze patterns
        for ftype, items in failure_types.items():
            if len(items) > 1:
                patterns.append({
                    'pattern': f"Multiple {ftype} failures",
                    'count': len(items),
                    'likely_cause': self._infer_cause(items)
                })
        
        # Check for timing-related failures
        slow_tests = [f for f in failures if f.get('time', 0) > 10]
        if slow_tests:
            patterns.append({
                'pattern': 'Slow test execution',
                'count': len(slow_tests),
                'likely_cause': 'Performance issue or timeout'
            })
        
        return patterns
    
    def _infer_cause(self, failures: List[Dict[str, Any]]) -> str:
        """Infer likely cause from failure patterns"""
        messages = [f.get('message', '') for f in failures]
        
        if any('timeout' in m.lower() for m in messages):
            return "Timeout issues - possibly slow backend or network"
        elif any('connection' in m.lower() for m in messages):
            return "Connection issues - backend may not be running"
        elif any('element not found' in m.lower() for m in messages):
            return "DOM changes - elements have different selectors"
        elif any('assertion' in m.lower() for m in messages):
            return "Logic changes - expected values have changed"
        
        return "Unknown - requires manual investigation"
    
    def _generate_suggestions(self, results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate fix suggestions based on analysis"""
        suggestions = []
        
        for failure in results['failures']:
            if failure['type'] == 'test_failure':
                suggestion = self._suggest_test_fix(failure)
            elif failure['type'] == 'visual_regression':
                suggestion = self._suggest_visual_fix(failure)
            else:
                suggestion = None
            
            if suggestion:
                suggestions.append(suggestion)
        
        # Add pattern-based suggestions
        for pattern in results['patterns']:
            if 'timeout' in pattern['likely_cause'].lower():
                suggestions.append({
                    'type': 'config',
                    'file': 'wdio.conf.ts',
                    'change': 'Increase waitforTimeout to 30000',
                    'priority': 'high'
                })
            elif 'connection' in pattern['likely_cause'].lower():
                suggestions.append({
                    'type': 'setup',
                    'action': 'Ensure backend is running before tests',
                    'priority': 'critical'
                })
        
        return suggestions
    
    def _suggest_test_fix(self, failure: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Suggest fix for test failure"""
        message = failure.get('message', '').lower()
        
        if 'element not found' in message:
            return {
                'type': 'selector',
                'test': failure['test'],
                'suggestion': 'Update element selector or add wait',
                'code': f"await browser.waitUntil(async () => await element.isDisplayed(), {{ timeout: 10000 }})"
            }
        elif 'timeout' in message:
            return {
                'type': 'timeout',
                'test': failure['test'],
                'suggestion': 'Increase timeout or optimize performance',
                'code': "{ timeout: 30000 }"
            }
        elif 'expected' in message and 'received' in message:
            return {
                'type': 'assertion',
                'test': failure['test'],
                'suggestion': 'Update expected value or fix logic',
                'review_needed': True
            }
        
        return None
    
    def _suggest_visual_fix(self, failure: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Suggest fix for visual regression"""
        analysis = failure.get('analysis', {})
        
        if 'fixes' in analysis:
            return {
                'type': 'visual',
                'screenshot': failure['screenshot'],
                'fixes': analysis['fixes'],
                'priority': 'medium'
            }
        
        return None
    
    def _can_autofix(self, results: Dict[str, Any]) -> bool:
        """Determine if automatic fixes can be applied"""
        # Check if we have clear, safe fixes
        safe_fixes = [
            s for s in results['suggestions']
            if s.get('type') in ['selector', 'timeout', 'config']
            and not s.get('review_needed')
        ]
        
        return len(safe_fixes) > 0
    
    def generate_report(self, results: Dict[str, Any]) -> str:
        """Generate markdown report"""
        report = ["# GUI Test Failure Analysis\n"]
        
        # Summary
        report.append("## Summary\n")
        report.append(f"- Total failures: {len(results['failures'])}")
        report.append(f"- Patterns identified: {len(results['patterns'])}")
        report.append(f"- Suggestions: {len(results['suggestions'])}")
        report.append(f"- Autofix possible: {'Yes' if results['autofix_possible'] else 'No'}\n")
        
        # Failures
        if results['failures']:
            report.append("## Failures\n")
            for failure in results['failures']:
                if failure['type'] == 'test_failure':
                    report.append(f"### ❌ {failure['test']}")
                    report.append(f"- Suite: {failure['suite']}")
                    report.append(f"- Message: {failure['message']}")
                elif failure['type'] == 'visual_regression':
                    report.append(f"### 🖼️ Visual Regression: {Path(failure['screenshot']).name}")
                    if 'analysis' in failure:
                        report.append(f"- Issues: {', '.join(failure['analysis'].get('issues', []))}")
                report.append("")
        
        # Patterns
        if results['patterns']:
            report.append("## Patterns Detected\n")
            for pattern in results['patterns']:
                report.append(f"- **{pattern['pattern']}** ({pattern['count']} occurrences)")
                report.append(f"  - Likely cause: {pattern['likely_cause']}")
            report.append("")
        
        # Suggestions
        if results['suggestions']:
            report.append("## Suggested Fixes\n")
            for i, suggestion in enumerate(results['suggestions'], 1):
                report.append(f"### {i}. {suggestion['type'].title()} Fix")
                if 'test' in suggestion:
                    report.append(f"- Test: {suggestion['test']}")
                if 'suggestion' in suggestion:
                    report.append(f"- Suggestion: {suggestion['suggestion']}")
                if 'code' in suggestion:
                    report.append(f"```javascript\n{suggestion['code']}\n```")
                if 'priority' in suggestion:
                    report.append(f"- Priority: {suggestion['priority']}")
                report.append("")
        
        return "\n".join(report)


def main():
    """Main entry point"""
    analyzer = TestFailureAnalyzer()
    
    # Analyze failures
    artifacts_path = "test-artifacts"
    results = analyzer.analyze_failures(artifacts_path)
    
    # Generate report
    report = analyzer.generate_report(results)
    print(report)
    
    # Save results
    with open("triage-results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    # Set GitHub Actions outputs
    if results['failures']:
        print("::set-output name=create-issue::true")
        print(f"::set-output name=issue-body::{report}")
    
    if results['autofix_possible']:
        print("::set-output name=autofix::true")
    
    # Exit with error if failures found
    sys.exit(1 if results['failures'] else 0)


if __name__ == "__main__":
    main()