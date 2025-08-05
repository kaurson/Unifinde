#!/usr/bin/env python3
"""
Setup script for the University Data Collection System
"""

import subprocess
import sys
import os
import platform
from pathlib import Path

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        print(f"Error output: {e.stderr}")
        return False

def check_python_version():
    """Check if Python version is compatible"""
    print("🐍 Checking Python version...")
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print(f"❌ Python 3.8+ required, found {version.major}.{version.minor}")
        return False
    print(f"✅ Python {version.major}.{version.minor}.{version.micro} is compatible")
    return True

def install_python_dependencies():
    """Install Python dependencies"""
    requirements_file = Path(__file__).parent / "requirements.txt"
    if requirements_file.exists():
        return run_command(f"pip install -r {requirements_file}", "Installing Python dependencies")
    else:
        print("⚠️  requirements.txt not found, installing basic dependencies...")
        return run_command("pip install selenium sqlalchemy aiohttp beautifulsoup4 requests python-dotenv webdriver-manager lxml", "Installing basic dependencies")

def check_chrome():
    """Check if Chrome is installed"""
    print("🌐 Checking Chrome browser...")
    
    system = platform.system().lower()
    
    if system == "darwin":  # macOS
        chrome_paths = [
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
            "/Applications/Chromium.app/Contents/MacOS/Chromium"
        ]
    elif system == "linux":
        chrome_paths = [
            "/usr/bin/google-chrome",
            "/usr/bin/chromium-browser",
            "/usr/bin/chromium"
        ]
    elif system == "windows":
        chrome_paths = [
            "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
            "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe"
        ]
    else:
        print("⚠️  Unknown operating system, please install Chrome manually")
        return False
    
    for path in chrome_paths:
        if os.path.exists(path):
            print(f"✅ Chrome found at: {path}")
            return True
    
    print("❌ Chrome not found. Please install Chrome browser:")
    if system == "darwin":
        print("  brew install --cask google-chrome")
    elif system == "linux":
        print("  sudo apt-get install google-chrome-stable")
    elif system == "windows":
        print("  Download from: https://www.google.com/chrome/")
    
    return False

def install_chromedriver():
    """Install ChromeDriver"""
    print("🚗 Checking ChromeDriver...")
    
    try:
        # Try to import webdriver_manager
        import webdriver_manager
        print("✅ webdriver-manager is available")
        return True
    except ImportError:
        print("⚠️  webdriver-manager not found, installing...")
        return run_command("pip install webdriver-manager", "Installing webdriver-manager")

def create_database():
    """Create the database and tables"""
    print("🗄️  Setting up database...")
    
    try:
        # Import and create database
        sys.path.append(str(Path(__file__).parent))
        from models import Base
        from sqlalchemy import create_engine
        
        engine = create_engine("sqlite:///universities.db")
        Base.metadata.create_all(engine)
        
        print("✅ Database created successfully")
        return True
    except Exception as e:
        print(f"❌ Database setup failed: {e}")
        return False

def run_test():
    """Run a simple test to verify installation"""
    print("🧪 Running installation test...")
    
    try:
        # Test imports
        sys.path.append(str(Path(__file__).parent))
        from scraper import UniversityScraper
        from mcp_server import UniversityMCPServer
        from models import University, Program, Facility
        
        print("✅ All modules imported successfully")
        
        # Test scraper initialization (without actually scraping)
        print("🔄 Testing scraper initialization...")
        scraper = UniversityScraper(headless=True)
        scraper.close()
        print("✅ Scraper test passed")
        
        return True
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def main():
    """Main setup function"""
    print("🎓 University Data Collection System - Setup")
    print("=" * 50)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Install Python dependencies
    if not install_python_dependencies():
        print("❌ Failed to install Python dependencies")
        sys.exit(1)
    
    # Check Chrome
    if not check_chrome():
        print("⚠️  Chrome not found, but continuing...")
    
    # Install ChromeDriver
    if not install_chromedriver():
        print("❌ Failed to install ChromeDriver")
        sys.exit(1)
    
    # Create database
    if not create_database():
        print("❌ Failed to create database")
        sys.exit(1)
    
    # Run test
    if not run_test():
        print("❌ Installation test failed")
        sys.exit(1)
    
    print("\n" + "=" * 50)
    print("🎉 Setup completed successfully!")
    print("=" * 50)
    
    print("\nNext steps:")
    print("1. Run examples: python app/example.py")
    print("2. Run tests: python app/test_system.py")
    print("3. Use command line: python -m app.main --help")
    print("4. Check documentation: app/README.md")
    
    print("\nExample usage:")
    print("python -m app.main --university 'MIT' --fields basic_info contact")

if __name__ == "__main__":
    main() 