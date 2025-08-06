#!/usr/bin/env python3
"""
Debug script for registration issues
"""

import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.database import get_db, engine
from database.models import User
from api.schemas import UserCreate
import bcrypt

def test_database_connection():
    """Test database connection"""
    print("🔍 Testing database connection...")
    try:
        # Test engine connection
        with engine.connect() as conn:
            result = conn.execute("SELECT 1")
            print("✅ Database connection successful")
            return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        # Try alternative connection test
        try:
            from sqlalchemy import text
            with engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                print("✅ Database connection successful (using text())")
                return True
        except Exception as e2:
            print(f"❌ Alternative connection test also failed: {e2}")
            return False

def test_user_creation():
    """Test user creation directly"""
    print("\n🔍 Testing user creation...")
    try:
        # Get database session
        db = next(get_db())
        
        # Test data
        test_user_data = UserCreate(
            username="debuguser",
            email="debug@example.com",
            password="DebugPass123",
            name="Debug User"
        )
        
        # Check if user exists
        existing_user = db.query(User).filter(
            (User.email == test_user_data.email) | (User.username == test_user_data.username)
        ).first()
        
        if existing_user:
            print("⚠️  Test user already exists, skipping creation")
            return True
        
        # Hash password
        password_hash = bcrypt.hashpw(test_user_data.password.encode('utf-8'), bcrypt.gensalt())
        
        # Create user
        user = User(
            username=test_user_data.username,
            email=test_user_data.email,
            password_hash=password_hash.decode('utf-8'),
            name=test_user_data.name
        )
        
        db.add(user)
        db.commit()
        db.refresh(user)
        
        print(f"✅ User created successfully: {user.username} (ID: {user.id})")
        
        # Clean up - delete test user
        db.delete(user)
        db.commit()
        print("🧹 Test user cleaned up")
        
        return True
        
    except Exception as e:
        print(f"❌ User creation failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

def test_jwt_secret():
    """Test JWT secret key"""
    print("\n🔍 Testing JWT secret key...")
    secret_key = os.getenv("JWT_SECRET_KEY", "your-secret-key-here")
    print(f"📝 JWT Secret Key: {secret_key[:10]}...")
    
    if secret_key == "your-secret-key-here":
        print("⚠️  Using default JWT secret key - consider setting JWT_SECRET_KEY environment variable")
    else:
        print("✅ JWT secret key is set")
    
    return True

def test_environment():
    """Test environment variables"""
    print("\n🔍 Testing environment variables...")
    
    # Check if .env file exists
    if os.path.exists('.env'):
        print("✅ .env file exists")
    else:
        print("⚠️  .env file not found")
    
    # Check important environment variables
    env_vars = ['JWT_SECRET_KEY', 'LLM_API_KEY', 'LLM_PROVIDER']
    for var in env_vars:
        value = os.getenv(var)
        if value:
            print(f"✅ {var}: {value[:10]}...")
        else:
            print(f"⚠️  {var}: Not set")

if __name__ == "__main__":
    print("🚀 Starting registration debug...\n")
    
    # Test database connection
    db_ok = test_database_connection()
    
    # Test environment
    test_environment()
    
    # Test JWT secret
    test_jwt_secret()
    
    # Test user creation
    if db_ok:
        test_user_creation()
    
    print("\n✨ Debug completed!") 