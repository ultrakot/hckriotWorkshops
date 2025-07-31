#!/usr/bin/env python3
"""
Test script for hybrid role functionality.
"""

# Fix imports from parent directory
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import UserRole, Users

def test_hybrid_approach():
    """Test the hybrid role approach."""
    print("=== Testing Hybrid Role Approach ===")
    print("Database stores integers, application uses enums\n")
    
    # Test creating users with enum values
    print("1. Creating users with enum values:")
    user1 = Users(Name="Test Admin", Email="admin@test.com", Role=UserRole.ADMIN)
    user2 = Users(Name="Test Leader", Email="leader@test.com", Role=UserRole.WORKSHOP_LEADER)
    user3 = Users(Name="Test Participant", Email="participant@test.com", Role=UserRole.PARTICIPANT)
    
    print(f"   Admin: Role={user1.Role}, DB Value={user1._role}")
    print(f"   Leader: Role={user2.Role}, DB Value={user2._role}")
    print(f"   Participant: Role={user3.Role}, DB Value={user3._role}")
    
    # Test creating users with integer values
    print("\n2. Creating users with integer values:")
    user4 = Users(Name="Test User", Email="test@test.com")
    user4.Role = 100  # Should convert to ADMIN
    print(f"   Set Role=100: Enum={user4.Role}, DB Value={user4._role}")
    
    # Test role checking methods
    print("\n3. Testing role checking methods:")
    print(f"   Admin is_admin(): {user1.is_admin()}")
    print(f"   Leader can_manage_workshops(): {user2.can_manage_workshops()}")
    print(f"   Participant can_manage_workshops(): {user3.can_manage_workshops()}")
    
    # Test role comparisons
    print("\n4. Testing role comparisons:")
    print(f"   ADMIN >= WORKSHOP_LEADER: {user1.Role >= UserRole.WORKSHOP_LEADER}")
    print(f"   WORKSHOP_LEADER >= PARTICIPANT: {user2.Role >= UserRole.PARTICIPANT}")
    print(f"   PARTICIPANT >= ADMIN: {user3.Role >= UserRole.ADMIN}")
    
    print("\nHybrid approach test completed!")
    print("\nThe hybrid approach allows:")
    print("- Efficient integer storage in database")
    print("- Readable enum usage in application code")
    print("- Seamless conversion between both")
    print("- All existing code continues to work")

if __name__ == "__main__":
    test_hybrid_approach() 