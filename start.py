#!/usr/bin/env python3
"""
University Matching App Startup Script

This script helps you set up and run the complete university matching application.
It handles database initialization, dependency checking, and starting both backend and frontend servers.
"""

import os
import sys
import subprocess
import asyncio
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        print(f"Current version: {sys.version}")
        return False
    print(f"✅ Python version: {sys.version.split()[0]}")
    return True

def check_dependencies():
    """Check if required dependencies are installed"""
    required_packages = [
        'fastapi', 'uvicorn', 'sqlalchemy', 'alembic', 'psycopg2-binary',
        'python-dotenv', 'pydantic', 'bcrypt', 'openai', 'playwright'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ Missing packages: {', '.join(missing_packages)}")
        print("Run: pip install -r requirements.txt")
        return False
    
    print("✅ All Python dependencies are installed")
    return True

def check_env_file():
    """Check if .env file exists and has required variables"""
    env_file = Path('.env')
    if not env_file.exists():
        print("❌ .env file not found")
        print("Creating .env file with template...")
        create_env_template()
        return False
    
    # Check for required environment variables
    required_vars = ['DATABASE_URL', 'OPENAI_API_KEY', 'JWT_SECRET_KEY']
    missing_vars = []
    
    with open(env_file, 'r') as f:
        content = f.read()
        for var in required_vars:
            if f'{var}=' not in content or f'{var}=' in content and 'your_' in content:
                missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing or unconfigured environment variables: {', '.join(missing_vars)}")
        print("Please update your .env file with the required values")
        return False
    
    print("✅ Environment variables are configured")
    return True

def create_env_template():
    """Create a template .env file"""
    template = """# Database Configuration
DATABASE_URL=mysql+pymysql://root@localhost:3306/uniapp

# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here

# JWT Configuration
JWT_SECRET_KEY=your_jwt_secret_key_here

# Supabase Configuration (optional)
SUPABASE_URL=your_supabase_url_here
SUPABASE_KEY=your_supabase_key_here

# Server Configuration
HOST=0.0.0.0
PORT=8000
"""
    
    with open('.env', 'w') as f:
        f.write(template)
    
    print("✅ Created .env template file")
    print("Please update the .env file with your actual values")

def init_database():
    """Initialize the database"""
    try:
        print("🔄 Initializing database...")
        
        # Import and run database initialization
        sys.path.append('.')
        from database.database import init_db
        init_db()
        
        print("✅ Database initialized successfully")
        return True
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        return False

def install_playwright_browsers():
    """Install Playwright browsers"""
    try:
        print("🔄 Installing Playwright browsers...")
        subprocess.run([sys.executable, '-m', 'playwright', 'install'], check=True)
        print("✅ Playwright browsers installed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install Playwright browsers: {e}")
        return False

def check_frontend_dependencies():
    """Check if frontend dependencies are installed"""
    frontend_dir = Path('frontend')
    if not frontend_dir.exists():
        print("❌ Frontend directory not found")
        return False
    
    node_modules = frontend_dir / 'node_modules'
    if not node_modules.exists():
        print("❌ Frontend dependencies not installed")
        print("Run: cd frontend && npm install")
        return False
    
    print("✅ Frontend dependencies are installed")
    return True

def start_backend():
    """Start the FastAPI backend server"""
    try:
        print("🚀 Starting backend server...")
        print("Backend will be available at: http://localhost:8000")
        print("API documentation at: http://localhost:8000/docs")
        
        # Change to api directory and start server
        os.chdir('api')
        subprocess.run([
            sys.executable, '-m', 'uvicorn', 
            'main:app', 
            '--reload', 
            '--host', '0.0.0.0', 
            '--port', '8000'
        ])
    except KeyboardInterrupt:
        print("\n🛑 Backend server stopped")
    except Exception as e:
        print(f"❌ Failed to start backend server: {e}")

def start_frontend():
    """Start the Next.js frontend server"""
    try:
        print("🚀 Starting frontend server...")
        print("Frontend will be available at: http://localhost:3000")
        
        # Change to frontend directory and start server
        os.chdir('frontend')
        subprocess.run(['npm', 'run', 'dev'])
    except KeyboardInterrupt:
        print("\n🛑 Frontend server stopped")
    except Exception as e:
        print(f"❌ Failed to start frontend server: {e}")

def main():
    """Main startup function"""
    print("🎓 University Matching App Startup")
    print("=" * 50)
    
    # Check prerequisites
    if not check_python_version():
        return
    
    if not check_dependencies():
        return
    
    if not check_env_file():
        return
    
    if not check_frontend_dependencies():
        return
    
    # Initialize components
    if not init_database():
        return
    
    if not install_playwright_browsers():
        return
    
    print("\n✅ All checks passed! Ready to start the application.")
    print("\nChoose an option:")
    print("1. Start Backend Server")
    print("2. Start Frontend Server")
    print("3. Start Both (in separate terminals)")
    print("4. Exit")
    
    while True:
        choice = input("\nEnter your choice (1-4): ").strip()
        
        if choice == '1':
            start_backend()
            break
        elif choice == '2':
            start_frontend()
            break
        elif choice == '3':
            print("\n🔄 Starting both servers...")
            print("Backend: http://localhost:8000")
            print("Frontend: http://localhost:3000")
            print("API Docs: http://localhost:8000/docs")
            print("\nPress Ctrl+C to stop both servers")
            
            # Start both servers in separate processes
            try:
                backend_process = subprocess.Popen([
                    sys.executable, 'start.py', '--backend-only'
                ])
                frontend_process = subprocess.Popen([
                    sys.executable, 'start.py', '--frontend-only'
                ])
                
                backend_process.wait()
                frontend_process.wait()
            except KeyboardInterrupt:
                print("\n🛑 Stopping servers...")
                backend_process.terminate()
                frontend_process.terminate()
            break
        elif choice == '4':
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice. Please enter 1-4.")

if __name__ == "__main__":
    # Handle command line arguments for separate server startup
    if len(sys.argv) > 1:
        if sys.argv[1] == '--backend-only':
            start_backend()
        elif sys.argv[1] == '--frontend-only':
            start_frontend()
        else:
            print("Unknown argument. Use --backend-only or --frontend-only")
    else:
        main() 