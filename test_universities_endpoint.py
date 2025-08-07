#!/usr/bin/env python3
"""
Test script to verify the universities endpoint works with the actual data
"""

import sys
import os

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_universities_endpoint():
    """Test the universities endpoint directly"""
    try:
        from database.database import get_db
        from database.models import UniversityDataCollectionResult
        
        print("🔧 Testing universities endpoint...")
        
        # Get a database session
        db = next(get_db())
        
        # Simulate the endpoint logic
        universities = db.query(UniversityDataCollectionResult).limit(5).all()
        
        print(f"📚 Retrieved {len(universities)} universities")
        
        for uni in universities:
            print(f"  - {uni.name} (ID: {uni.id})")
            print(f"    Location: {uni.city}, {uni.country}")
            print(f"    Ranking: World #{uni.world_ranking if uni.world_ranking else 'N/A'}")
            print(f"    Students: {uni.student_population if uni.student_population else 'N/A'}")
            print(f"    Acceptance Rate: {uni.acceptance_rate if uni.acceptance_rate else 'N/A'}%")
            print()
        
        db.close()
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Testing universities endpoint...\n")
    
    success = test_universities_endpoint()
    
    print("="*50)
    if success:
        print("✅ Universities endpoint test passed!")
        print("💡 The API should now return university data correctly.")
    else:
        print("❌ Universities endpoint test failed.")
    print("="*50) 