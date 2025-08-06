#!/usr/bin/env python3
"""
Setup script for the University Data Collector
"""

import os
import sys
import subprocess
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        return False
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} detected")
    return True

def check_environment():
    """Check environment setup"""
    print("\n🔍 Checking environment...")
    
    # Check if we're in the right directory
    current_dir = Path.cwd()
    if not (current_dir / "university_data_collector.py").exists():
        print("❌ university_data_collector.py not found in current directory")
        print("Please run this script from the app directory")
        return False
    
    # Check for required directories
    required_dirs = ["../database", "../browser_tools"]
    for dir_path in required_dirs:
        if not Path(dir_path).exists():
            print(f"❌ Required directory not found: {dir_path}")
            return False
    
    print("✅ Environment check passed")
    return True

def install_dependencies():
    """Install required dependencies"""
    print("\n📦 Installing dependencies...")
    
    try:
        # Install browser-tools requirements
        browser_tools_req = Path("../browser_tools/requirements.txt")
        if browser_tools_req.exists():
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", str(browser_tools_req)])
            print("✅ Browser-tools dependencies installed")
        else:
            print("⚠️  browser_tools/requirements.txt not found")
        
        # Install Playwright browsers
        print("Installing Playwright browsers...")
        subprocess.check_call([sys.executable, "-m", "playwright", "install", "chromium"])
        print("✅ Playwright browsers installed")
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing dependencies: {e}")
        return False
    
    return True

def create_env_template():
    """Create .env file template"""
    env_file = Path(".env")
    if not env_file.exists():
        print("\n📝 Creating .env file template...")
        env_content = """# OpenAI API Configuration
OPENAI_API_KEY=your-openai-api-key-here

# Database Configuration (optional - will use default if not set)
DATABASE_URL=sqlite:///universities.db

# Browser Configuration
BROWSER_HEADLESS=true
BROWSER_TIMEOUT=30000

# Rate Limiting
SEARCH_DELAY=2
SCRAPE_DELAY=1

# LLM Configuration
LLM_MODEL=gpt-4
LLM_TEMPERATURE=0.1
LLM_MAX_TOKENS=4000
"""
        with open(env_file, "w") as f:
            f.write(env_content)
        print("✅ .env file created")
        print("⚠️  Please update the .env file with your OpenAI API key")
    else:
        print("ℹ️  .env file already exists")

def create_directories():
    """Create necessary directories"""
    print("\n📁 Creating directories...")
    
    directories = ["output", "logs"]
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"✅ Created directory: {directory}")

def make_executable():
    """Make the script executable"""
    script_path = Path("university_data_collector.py")
    if script_path.exists():
        try:
            os.chmod(script_path, 0o755)
            print("✅ Made university_data_collector.py executable")
        except Exception as e:
            print(f"⚠️  Could not make script executable: {e}")

def run_database_migration():
    """Run database migration if needed"""
    print("\n🗄️  Checking database...")
    
    try:
        # Check if alembic is available
        subprocess.run([sys.executable, "-m", "alembic", "--version"], 
                      capture_output=True, check=True)
        
        # Run migration
        print("Running database migration...")
        subprocess.check_call([sys.executable, "-m", "alembic", "upgrade", "head"])
        print("✅ Database migration completed")
        
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("⚠️  Alembic not found or migration failed")
        print("You may need to run: pip install alembic")

def main():
    """Main setup function"""
    print("🚀 Setting up University Data Collector")
    print("=" * 50)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Check environment
    if not check_environment():
        sys.exit(1)
    
    # Install dependencies
    if not install_dependencies():
        print("❌ Failed to install dependencies")
        sys.exit(1)
    
    # Create directories
    create_directories()
    
    # Create env file
    create_env_template()
    
    # Make script executable
    make_executable()
    
    # Run database migration
    run_database_migration()
    
    print("\n" + "=" * 50)
    print("✅ Setup completed successfully!")
    print("\n📋 Next steps:")
    print("1. Update the .env file with your OpenAI API key")
    print("2. Test the collector with a single university:")
    print("   python university_data_collector.py 'Stanford University'")
    print("3. Or use the example file:")
    print("   python university_data_collector.py --file universities_example.txt")
    print("\n📖 For more options, run:")
    print("   python university_data_collector.py --help")

if __name__ == "__main__":
    main() 