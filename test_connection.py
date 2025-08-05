#!/usr/bin/env python3
"""
Test script to verify Supabase database connection
"""

import os
from dotenv import load_dotenv
import psycopg2
from urllib.parse import urlparse

# Load environment variables
load_dotenv()

def test_connection():
    """Test the database connection"""
    database_url = os.getenv("DATABASE_URL")
    
    if not database_url:
        print("❌ DATABASE_URL not found in environment variables")
        return False
    
    print(f"🔗 Testing connection to: {database_url[:50]}...")
    
    # Parse the URL to extract components
    try:
        parsed = urlparse(database_url)
        print(f"📋 Connection details:")
        print(f"   Host: {parsed.hostname}")
        print(f"   Port: {parsed.port}")
        print(f"   Database: {parsed.path[1:]}")
        print(f"   Username: {parsed.username}")
        print(f"   Password: {'*' * len(parsed.password) if parsed.password else 'None'}")
    except Exception as e:
        print(f"❌ Error parsing DATABASE_URL: {e}")
        return False
    
    # Test DNS resolution
    try:
        import socket
        ip = socket.gethostbyname(parsed.hostname)
        print(f"✅ DNS resolution successful: {parsed.hostname} → {ip}")
    except socket.gaierror as e:
        print(f"❌ DNS resolution failed for {parsed.hostname}: {e}")
        print("💡 Please check your Supabase project settings and ensure the hostname is correct")
        return False
    
    # Test database connection
    try:
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        print(f"✅ Database connection successful!")
        print(f"📊 PostgreSQL version: {version[0]}")
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

if __name__ == "__main__":
    test_connection() 