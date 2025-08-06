#!/usr/bin/env python3

import os
import socket
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def check_supabase_project():
    """Check if Supabase project is accessible"""
    
    print("🔍 Diagnosing Supabase Connection Issues...")
    print("=" * 60)
    
    # Get DATABASE_URL
    DATABASE_URL = os.getenv("DATABASE_URL")
    if not DATABASE_URL:
        print("❌ DATABASE_URL not found in .env file")
        return False
    
    print(f"📋 DATABASE_URL: {DATABASE_URL[:60]}...")
    
    # Extract project reference
    if "supabase.co" in DATABASE_URL:
        try:
            # Extract project ref from URL
            parts = DATABASE_URL.split("@")
            if len(parts) > 1:
                host_part = parts[1].split("/")[0]
                project_ref = host_part.split(".")[0]
                print(f"🔍 Project Reference: {project_ref}")
                
                # Test different hostname patterns
                hostname_patterns = [
                    f"db.{project_ref}.supabase.co",
                    f"{project_ref}.supabase.co",
                    f"postgres.{project_ref}.supabase.co"
                ]
                
                print("\n🔍 Testing hostname patterns:")
                for hostname in hostname_patterns:
                    try:
                        ip = socket.gethostbyname(hostname)
                        print(f"✅ {hostname} → {ip}")
                    except socket.gaierror:
                        print(f"❌ {hostname} → Cannot resolve")
                
                # Check Supabase project status via API
                print(f"\n🔍 Checking project status...")
                try:
                    # Try to access the project dashboard
                    dashboard_url = f"https://supabase.com/dashboard/project/{project_ref}"
                    print(f"📊 Dashboard URL: {dashboard_url}")
                    print("💡 Please check if your project is active in the dashboard")
                    
                except Exception as e:
                    print(f"❌ Error checking project status: {e}")
                
            else:
                print("❌ Could not extract project reference from DATABASE_URL")
                
        except Exception as e:
            print(f"❌ Error parsing DATABASE_URL: {e}")
    
    print("\n🔧 Troubleshooting Steps:")
    print("1. Go to https://supabase.com/dashboard")
    print("2. Check if your project is active (not paused)")
    print("3. If paused, click 'Resume' to reactivate")
    print("4. Go to Settings → Database")
    print("5. Copy the exact 'Connection string' shown there")
    print("6. Update your .env file with the correct DATABASE_URL")
    
    return True

if __name__ == "__main__":
    check_supabase_project() 