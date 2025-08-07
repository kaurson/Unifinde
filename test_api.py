#!/usr/bin/env python3
"""
Simple test script to check if the API can start and if there are universities in the database
"""

import sys
import os

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_database_connection():
    """Test database connection and check for universities"""
    try:
        from database.database import get_db, engine
        from database.models import UniversityDataCollectionResult
        from database.models import Base
        
        print("🔧 Testing database connection...")
        
        # Create tables if they don't exist
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables created/verified")
        
        # Get a database session
        db = next(get_db())
        
        # Check if there are any universities in the data collection results
        universities = db.query(UniversityDataCollectionResult).all()
        print(f"📚 Found {len(universities)} universities in database")
        
        if universities:
            print("📋 Sample universities:")
            for uni in universities[:3]:  # Show first 3
                print(f"  - {uni.name} (ID: {uni.id}) - {uni.city}, {uni.country}")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_api_imports():
    """Test if API imports work"""
    try:
        print("🔧 Testing API imports...")
        from api.main import app
        print("✅ API imports successful")
        return True
    except Exception as e:
        print(f"❌ API import test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Starting API tests...\n")
    
    # Test API imports
    api_ok = test_api_imports()
    
    # Test database connection
    db_ok = test_database_connection()
    
    print("\n" + "="*50)
    if api_ok and db_ok:
        print("✅ All tests passed! The API should be ready to start.")
        print("💡 You can now run: python3 start_server.py")
    else:
        print("❌ Some tests failed. Please check the errors above.")
    print("="*50) 