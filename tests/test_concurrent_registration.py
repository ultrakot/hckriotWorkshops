#!/usr/bin/env python3
"""
Test script to demonstrate concurrent registration protection.
Simulates multiple users registering simultaneously.
"""

# Fix imports from parent directory
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import threading
import time
import requests
import json
from concurrent.futures import ThreadPoolExecutor, as_completed

def simulate_registration(user_id, workshop_id, auth_token):
    """Simulate a single user registration."""
    
    url = f"http://localhost:5000/workshops/{workshop_id}/register"
    headers = {
        'Authorization': f'Bearer {auth_token}',
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.post(url, headers=headers)
        return {
            'user_id': user_id,
            'status_code': response.status_code,
            'response': response.json(),
            'timestamp': time.time()
        }
    except Exception as e:
        return {
            'user_id': user_id,
            'error': str(e),
            'timestamp': time.time()
        }

def test_concurrent_registrations():
    """Test concurrent registrations for a workshop with limited capacity."""
    
    print("=== Testing Concurrent Registration Protection ===")
    print("Simulating 50 users trying to register for a workshop with capacity of 10")
    
    # Configuration
    WORKSHOP_ID = 1  # Workshop with capacity 10
    NUM_USERS = 50   # More users than capacity
    AUTH_TOKEN = "your_test_jwt_token_here"  # Replace with valid token
    
    # Create thread pool for concurrent requests
    results = []
    start_time = time.time()
    
    with ThreadPoolExecutor(max_workers=20) as executor:
        # Submit all registration requests simultaneously
        future_to_user = {
            executor.submit(simulate_registration, user_id, WORKSHOP_ID, AUTH_TOKEN): user_id 
            for user_id in range(1, NUM_USERS + 1)
        }
        
        # Collect results as they complete
        for future in as_completed(future_to_user):
            user_id = future_to_user[future]
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                results.append({
                    'user_id': user_id,
                    'error': f'Request failed: {e}',
                    'timestamp': time.time()
                })
    
    end_time = time.time()
    
    # Analyze results
    print(f"\n=== Results (completed in {end_time - start_time:.2f}s) ===")
    
    success_count = len([r for r in results if r.get('status_code') == 200])
    conflict_count = len([r for r in results if r.get('status_code') == 409])
    error_count = len([r for r in results if r.get('status_code', 0) >= 400])
    
    print(f"Successful registrations: {success_count}")
    print(f"Conflicts (already registered): {conflict_count}")
    print(f"Other errors: {error_count}")
    
    # Show some successful registrations
    successful = [r for r in results if r.get('status_code') == 200][:10]
    print(f"\nFirst 10 successful registrations:")
    for result in successful:
        status = result['response'].get('workshop_status', 'unknown')
        print(f"  User {result['user_id']}: {status}")
    
    # Show conflicts
    conflicts = [r for r in results if r.get('status_code') == 409][:5]
    if conflicts:
        print(f"\nSample conflicts:")
        for result in conflicts:
            message = result['response'].get('message', 'Conflict')
            print(f"  User {result['user_id']}: {message}")
    
    # Verify no overbooking occurred
    registered_users = [r for r in results if r.get('response', {}).get('workshop_status') == 'REGISTERED']
    waitlisted_users = [r for r in results if r.get('response', {}).get('workshop_status') == 'WAITLISTED']
    
    print(f"\n=== Capacity Verification ===")
    print(f"Registered users: {len(registered_users)} (should be <= 10)")
    print(f"Waitlisted users: {len(waitlisted_users)}")
    
    if len(registered_users) <= 10:
        print("SUCCESS: No overbooking occurred!")
    else:
        print("FAILURE: Overbooking detected - race condition exists!")
    
    return results

if __name__ == "__main__":
    print("IMPORTANT: Make sure your server is running with the improved registration logic!")
    print("This test requires:")
    print("1. Server running on localhost:5000")
    print("2. Valid JWT token for authentication")
    print("3. Workshop with ID=1 and capacity=10")
    print("\nStarting test in 3 seconds...")
    time.sleep(3)
    
    test_concurrent_registrations() 