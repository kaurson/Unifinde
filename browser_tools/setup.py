#!/usr/bin/env python3
"""
Setup script for the browser-use university data collection tool
"""

import subprocess
import sys
import os
from pathlib import Path

def install_requirements():
    """Install required Python packages"""
    print("Installing Python requirements...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Python requirements installed successfully")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing Python requirements: {e}")
        return False
    return True

def install_playwright_browsers():
    """Install Playwright browsers"""
    print("Installing Playwright browsers...")
    try:
        subprocess.check_call([sys.executable, "-m", "playwright", "install", "chromium"])
        print("✅ Playwright browsers installed successfully")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing Playwright browsers: {e}")
        return False
    return True

def create_env_file():
    """Create .env file template"""
    env_file = Path(".env")
    if not env_file.exists():
        print("Creating .env file template...")
        env_content = """# OpenAI API Configuration
OPENAI_API_KEY=your-openai-api-key-here

# Database Configuration
DATABASE_URL=postgresql://username:password@localhost:5432/university_matching

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
        print("✅ .env file created. Please update with your API keys and database configuration.")
    else:
        print("ℹ️  .env file already exists")

def create_directories():
    """Create necessary directories"""
    directories = ["logs", "data", "temp"]
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
    print("✅ Directories created")

def main():
    """Main setup function"""
    print("🚀 Setting up University Data Collection Tool")
    print("=" * 50)
    
    # Change to the browser_use directory
    os.chdir(Path(__file__).parent)
    
    # Install requirements
    if not install_requirements():
        print("❌ Setup failed at requirements installation")
        return False
    
    # Install Playwright browsers
    if not install_playwright_browsers():
        print("❌ Setup failed at browser installation")
        return False
    
    # Create directories
    create_directories()
    
    # Create env file
    create_env_file()
    
    print("\n" + "=" * 50)
    print("✅ Setup completed successfully!")
    print("\nNext steps:")
    print("1. Update the .env file with your OpenAI API key and database configuration")
    print("2. Run database migrations to create the new tables")
    print("3. Test the tool with: python university_scraper.py")
    print("\nFor more information, see the README.md file")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 