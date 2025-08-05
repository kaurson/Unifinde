#!/usr/bin/env python3

import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# Load environment variables
load_dotenv()

def test_supabase_connection():
    """Test Supabase database connection"""
    
    # Get DATABASE_URL
    database_url = os.getenv("DATABASE_URL")
    
    print("🔍 Testing Supabase Connection...")
    print(f"📋 DATABASE_URL: {database_url}")
    
    if not database_url:
        print("❌ DATABASE_URL not found in environment variables")
        print("💡 Make sure your .env file contains the correct DATABASE_URL")
        return False
    
    try:
        # Create engine
        print("🔧 Creating database engine...")
        engine = create_engine(database_url, pool_pre_ping=True)
        
        # Test connection
        print("🔌 Testing connection...")
        with engine.connect() as connection:
            result = connection.execute(text("SELECT version();"))
            version = result.fetchone()
            print(f"✅ Connection successful!")
            print(f"📊 PostgreSQL version: {version[0]}")
            
        return True
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print("\n🔧 Troubleshooting tips:")
        print("1. Check if your Supabase project is active")
        print("2. Verify the DATABASE_URL format in your .env file")
        print("3. Make sure your IP is allowed in Supabase dashboard")
        print("4. Check if the password in the URL is correct")
        return False

if __name__ == "__main__":
    test_supabase_connection() 