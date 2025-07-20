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
    print(f"\n{'='*60}")
    print(f"=== {test_name} ===")
    print(f"Description: {description}")
    print(f"{'='*60}")
    
    start_time = time.time()
    
    try:
        # Run the test script
        result = subprocess.run([sys.executable, test_file], 
                              capture_output=True, 
                              text=True, 
                              timeout=60)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Print the output
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        
        success = result.returncode == 0
        status = "[PASSED]" if success else "[FAILED]"
        print(f"\n{status} ({duration:.1f}s)")
        
        return success
        
    except subprocess.TimeoutExpired:
        print("[FAILED] - Test timed out (60s limit)")
        return False
    except Exception as e:
        print(f"[FAILED] - Error running test: {e}")
        return False

def main():
    """Run all tests in sequence."""
    print("=== HackerIot Server - Complete Test Suite ===")
    print("Running all tests in recommended sequence...")
    print(f"Started at: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Get the tests directory
    tests_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Define tests in order of execution
    tests = [
        ("Import & Dependencies Test", 
         os.path.join(tests_dir, "test_imports.py"),
         "Verify all Python libraries are installed correctly"),
        
        ("Database Location Test", 
         os.path.join(tests_dir, "test_db_location.py"),
         "Verify database file exists and is accessible"),
        
        ("Comprehensive Database Test", 
         os.path.join(tests_dir, "test_database.py"),
         "Full database schema, connectivity, and API query testing")
    ]
    
    results = {}
    overall_start = time.time()
    
    # Run each test
    for test_name, test_file, description in tests:
        if os.path.exists(test_file):
            results[test_name] = run_test(test_name, test_file, description)
        else:
            print(f"\n[ERROR] Test file not found: {test_file}")
            results[test_name] = False
    
    overall_end = time.time()
    total_duration = overall_end - overall_start
    
    # Print summary
    print(f"\n{'='*80}")
    print("=== TEST SUITE SUMMARY ===")
    print(f"{'='*80}")
    
    passed = sum(results.values())
    total = len(results)
    
    for test_name, result in results.items():
        status = "[PASS]" if result else "[FAIL]"
        print(f"{test_name:.<50} {status}")
    
    print(f"\nOverall Result: {passed}/{total} tests passed")
    print(f"Total Duration: {total_duration:.1f} seconds")
    print(f"Completed at: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    if passed == total:
        print("\n*** ALL TESTS PASSED! ***")
        print("Your HackerIot server is ready for:")
        print("• Supabase integration")
        print("• Google OAuth setup")
        print("• Production deployment")
        print("\nNext steps:")
        print("1. Run: python migrate_user_table.py")
        print("2. Set up Supabase environment variables")
        print("3. Configure Google OAuth in Supabase dashboard")
        print("4. Start your server: python app.py")
        return True
    else:
        failed_tests = [name for name, result in results.items() if not result]
        print(f"\n[ERROR] {len(failed_tests)} TEST(S) FAILED:")
        for test_name in failed_tests:
            print(f"   • {test_name}")
        print("\nPlease fix the failed tests before proceeding.")
        print("Check the error messages above for troubleshooting guidance.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 