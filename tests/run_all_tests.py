#!/usr/bin/env python3
"""
Test runner script - runs all tests in the recommended sequence.
Use this to run a complete test suite for your HackerIot server.
"""

import sys
import os
import subprocess
import time

def run_test(test_name, test_file, description):
    """Run a single test script and return the result."""
    print(f"\n--- {test_name} ---")
    print(f"{description}")
    
    start_time = time.time()
    
    try:
        # Run the test script
        result = subprocess.run([sys.executable, test_file], 
                              capture_output=True, 
                              text=True, 
                              timeout=120)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Print the output
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        
        success = result.returncode == 0
        status = "PASSED" if success else "FAILED"
        print(f"{status} ({duration:.1f}s)")
        
        return success
        
    except subprocess.TimeoutExpired:
        print("FAILED - Test timed out (120s limit)")
        return False
    except Exception as e:
        print(f"FAILED - Error running test: {e}")
        return False

def main():
    """Run all tests in sequence."""
    print("HackerIot Server - Test Suite")
    print("=" * 50)
    print(f"Started: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Get the tests directory
    tests_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Define tests in order of execution
    tests = [
        ("Import & Dependencies", 
         os.path.join(tests_dir, "test_imports.py"),
         "Verify all Python libraries are installed"),
        
        ("Database Location", 
         os.path.join(tests_dir, "test_db_location.py"),
         "Verify database file exists and is accessible"),
        
        ("Database Schema", 
         os.path.join(tests_dir, "test_database.py"),
         "Test database schema and data integrity"),
        
        ("Hybrid Role Properties", 
         os.path.join(tests_dir, "test_hybrid_role.py"),
         "Test integer-to-enum conversion for roles"),
        
        ("Integer Hybrids", 
         os.path.join(tests_dir, "test_integer_hybrids.py"),
         "Test Role and Status hybrid properties"),
        
        ("API Scenarios", 
         os.path.join(tests_dir, "test_scenarios.py"),
         "Test API endpoints with real scenarios"),
        
        ("Concurrent Registration", 
         os.path.join(tests_dir, "test_concurrent_registration.py"),
         "Test race condition protection")
    ]
    
    results = {}
    overall_start = time.time()
    
    print(f"\nRunning {len(tests)} test suites...\n")
    
    # Run each test
    for i, (test_name, test_file, description) in enumerate(tests, 1):
        print(f"[{i}/{len(tests)}] {test_name}")
        
        if os.path.exists(test_file):
            results[test_name] = run_test(test_name, test_file, description)
        else:
            print(f"ERROR: Test file not found: {os.path.basename(test_file)}")
            results[test_name] = False
    
    overall_end = time.time()
    total_duration = overall_end - overall_start
    
    # Print summary
    print(f"\n{'='*50}")
    print("TEST RESULTS")
    print(f"{'='*50}")
    
    passed = sum(results.values())
    total = len(results)
    
    for test_name, result in results.items():
        status = "PASS" if result else "FAIL"
        print(f"{status:<8} {test_name}")
    
    print(f"\nSummary: {passed}/{total} tests passed ({passed/total*100:.0f}%)")
    print(f"Duration: {total_duration:.1f} seconds")
    print(f"Completed: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    if passed == total:
        print(f"\n*** ALL TESTS PASSED ***")
        print("Your server is ready for production!")
        print("\nNext steps:")
        print("- Apply database constraints if needed")
        print("- Set up environment variables")
        print("- Start your server: python app.py")
        return True
    else:
        failed_tests = [name for name, result in results.items() if not result]
        print(f"\n{len(failed_tests)} TEST(S) FAILED:")
        for test_name in failed_tests:
            print(f"  - {test_name}")
        print("\nPlease fix failed tests before proceeding.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 