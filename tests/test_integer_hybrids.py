#!/usr/bin/env python3
"""
Test script for integer-based hybrid properties in models.
Tests both UserRole and RegistrationStatus hybrid conversions.
"""

# Fix imports from parent directory
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import UserRole, RegistrationStatus, Users, Registration

def test_integer_hybrid_approaches():
    """Test both integer-based hybrid approaches."""
    print("=== Testing Integer-Based Hybrid Approaches ===")
    print("Both UserRole and RegistrationStatus: Database integers -> Application enums\n")
    
    # Test UserRole hybrid approach
    print("1. Testing UserRole (Integer -> Enum):")
    user = Users(Name="Test User", Email="test@example.com")
    
    # Test setting with enum
    user.Role = UserRole.ADMIN
    print(f"   Set Role=UserRole.ADMIN: DB={user._role}, Enum={user.Role}")
    
    # Test setting with integer  
    user.Role = 2
    print(f"   Set Role=2: DB={user._role}, Enum={user.Role}")
    
    # Test RegistrationStatus hybrid approach  
    print("\n2. Testing RegistrationStatus (Integer -> Enum):")
    registration = Registration(WorkshopId=1, UserId=1)
    
    # Test setting with enum
    registration.Status = RegistrationStatus.WAITLISTED
    print(f"   Set Status=WAITLISTED: DB={registration._status}, Enum={registration.Status}")
    
    # Test setting with integer
    registration.Status = 3  # Should be CANCELLED
    print(f"   Set Status=3: DB={registration._status}, Enum={registration.Status}")
    
    # Test default values
    print("\n3. Testing default values:")
    default_user = Users(Name="Default User", Email="default@test.com")
    default_reg = Registration(WorkshopId=1, UserId=1)
    print(f"   Default user role: DB={default_user._role}, Enum={default_user.Role}")
    print(f"   Default registration status: DB={default_reg._status}, Enum={default_reg.Status}")
    
    # Test enum properties
    print("\n4. Testing enum properties:")
    print(f"   ADMIN level: {UserRole.ADMIN.level}")
    print(f"   CANCELLED status_id: {RegistrationStatus.CANCELLED.status_id}")
    
    # Test role checking methods
    print("\n5. Testing role checking methods:")
    admin_user = Users(Name="Admin", Email="admin@test.com", Role=UserRole.ADMIN)
    print(f"   Admin user is_admin(): {admin_user.is_admin()}")
    print(f"   Admin user can_manage_workshops(): {admin_user.can_manage_workshops()}")
    
    # Test status comparisons
    print("\n6. Testing status comparisons:")
    reg1 = Registration(WorkshopId=1, UserId=1, Status=RegistrationStatus.REGISTERED)
    reg2 = Registration(WorkshopId=1, UserId=2, Status=RegistrationStatus.CANCELLED)
    print(f"   Registration 1 status: {reg1.Status} (DB: {reg1._status})")
    print(f"   Registration 2 status: {reg2.Status} (DB: {reg2._status})")
    print(f"   Are they the same? {reg1.Status == reg2.Status}")
    print(f"   Is reg1 registered? {reg1.Status == RegistrationStatus.REGISTERED}")
    
    print("\nInteger-based hybrid approaches test completed!")
    print("\nBenefits of this approach:")
    print("- Both Role and Status stored as efficient integers in DB")
    print("- Application code uses readable enums")
    print("- Lookup tables provide normalization and documentation")
    print("- All existing code continues to work unchanged")
    print("- Better performance with integer comparisons")

if __name__ == "__main__":
    test_integer_hybrid_approaches() 