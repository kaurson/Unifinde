#!/usr/bin/env python3
"""
MySQL Database Setup Script for UniApp
This script helps set up the MySQL database for the university matching application.
"""

import os
import sys
from dotenv import load_dotenv

def create_env_file():
    """Create .env file with MySQL configuration"""
    env_content = """# Database Configuration
# For MySQL (recommended for production)
DATABASE_URL=mysql+pymysql://root:password@localhost:3306/uniapp

# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here

# Security Configuration
SECRET_KEY=your_secret_key_here
COOKIE_SECURE=false

# Server Configuration
HOST=0.0.0.0
PORT=8000
"""
    
    with open('.env', 'w') as f:
        f.write(env_content)
    
    print("✅ Created .env file with MySQL configuration")
    print("📝 Please update the DATABASE_URL with your MySQL credentials")

def install_mysql_dependencies():
    """Install MySQL dependencies"""
    print("🔧 Installing MySQL dependencies...")
    os.system("pip install pymysql cryptography")

def create_database_sql():
    """Generate SQL to create the database"""
    sql = """
-- Create the database
CREATE DATABASE IF NOT EXISTS uniapp CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Use the database
USE uniapp;

-- Create a user for the application (optional)
-- CREATE USER 'uniapp_user'@'localhost' IDENTIFIED BY 'your_password';
-- GRANT ALL PRIVILEGES ON uniapp.* TO 'uniapp_user'@'localhost';
-- FLUSH PRIVILEGES;
"""
    
    with open('setup_database.sql', 'w') as f:
        f.write(sql)
    
    print("✅ Created setup_database.sql")
    print("📝 Run this SQL in MySQL to create the database:")

def main():
    print("🚀 MySQL Database Setup for UniApp")
    print("=" * 50)
    
    # Create .env file
    create_env_file()
    
    # Install dependencies
    install_mysql_dependencies()
    
    # Create SQL setup file
    create_database_sql()
    
    print("\n📋 Next Steps:")
    print("1. Install MySQL if not already installed")
    print("2. Start MySQL service")
    print("3. Run: mysql -u root -p < setup_database.sql")
    print("4. Update .env file with your MySQL credentials")
    print("5. Run: python -c 'from database.database import init_db; init_db()'")
    print("6. Run: alembic upgrade head")
    
    print("\n🔧 MySQL Installation:")
    print("- macOS: brew install mysql")
    print("- Ubuntu: sudo apt install mysql-server")
    print("- Windows: Download from mysql.com")

if __name__ == "__main__":
    main() 