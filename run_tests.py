#!/usr/bin/env python3
"""
Main test runner for UsenetSync
Run comprehensive end-to-end tests on production Usenet
"""

import os
import sys
import argparse
import logging
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

def setup_test_environment():
    """Set up the test environment"""
    # Create necessary directories
    dirs = [
        'tests/logs',
        'tests/e2e/test_workspace',
        'data',
        'temp',
        'logs'
    ]
    
    for dir_path in dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
    
    # Set up logging
    log_file = f"tests/logs/test_run_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    
    return log_file


def run_e2e_tests(test_filter=None):
    """Run end-to-end tests"""
    from tests.e2e.test_production_e2e import run_production_tests, ProductionE2ETestSuite
    import unittest
    
    print("=" * 80)
    print("USENETSYNC END-TO-END TEST SUITE")
    print("=" * 80)
    print()
    print("This will run comprehensive tests on production Usenet servers.")
    print("Tests include:")
    print("  - Connection health checks")
    print("  - Small/Medium/Large file uploads")
    print("  - Public/Private/Protected sharing")
    print("  - Incremental updates")
    print("  - Concurrent operations")
    print("  - Performance metrics")
    print()
    
    # Confirm before running
    response = input("Do you want to continue? (yes/no): ")
    if response.lower() not in ['yes', 'y']:
        print("Tests cancelled.")
        return False
    
    print()
    print("Starting tests...")
    print()
    
    if test_filter:
        # Run specific tests
        loader = unittest.TestLoader()
        suite = unittest.TestSuite()
        
        for test_name in test_filter:
            try:
                suite.addTest(ProductionE2ETestSuite(test_name))
            except Exception as e:
                print(f"Warning: Could not add test {test_name}: {e}")
        
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
    else:
        # Run all tests
        result = run_production_tests()
    
    return result


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Run UsenetSync tests')
    parser.add_argument(
        '--test',
        nargs='+',
        help='Specific test(s) to run (e.g., test_01_connection_health)'
    )
    parser.add_argument(
        '--skip-cleanup',
        action='store_true',
        help='Skip cleanup after tests'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    # Set environment variables
    if args.skip_cleanup:
        os.environ['CLEANUP_TESTS'] = 'false'
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Setup environment
    log_file = setup_test_environment()
    print(f"Logging to: {log_file}")
    print()
    
    # Run tests
    success = run_e2e_tests(args.test)
    
    # Print results location
    print()
    print(f"Test logs saved to: {log_file}")
    print(f"Test results saved to: tests/logs/e2e_results.json")
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()