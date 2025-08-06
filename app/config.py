"""
Configuration file for the University Data Collection System
"""

import os
from pathlib import Path
from typing import Optional, List
from dataclasses import dataclass
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

@dataclass
class ProxyConfig:
    """Proxy configuration for browser"""
    server: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None

@dataclass
class BrowserConfig:
    """Browser configuration for BrowserUseTool"""
    headless: bool = True
    disable_security: bool = True
    chrome_instance_path: Optional[str] = None
    extra_chromium_args: Optional[List[str]] = None
    wss_url: Optional[str] = None
    cdp_url: Optional[str] = None
    proxy: Optional[ProxyConfig] = None
    max_content_length: int = 2000
    new_context_config: Optional[dict] = None

@dataclass
class LLMConfig:
    """LLM Configuration"""
    provider: str = "openai"  # "openai", "anthropic", "local", "ollama"
    api_key: Optional[str] = None
    model: str = "gpt-4"
    base_url: Optional[str] = None
    temperature: float = 0.1
    max_tokens: int = 1000
    timeout: int = 30

@dataclass
class ScraperConfig:
    """Scraper Configuration"""
    type: str = "selenium"  # "selenium" or "browser_use"
    headless: bool = True
    timeout: int = 10
    user_agent: str = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
    delay_between_requests: float = 2.0
    max_retries: int = 3
    browser_use_api_key: Optional[str] = None
    browser_use_base_url: str = "https://api.browser-use.com"

@dataclass
class DatabaseConfig:
    """Database Configuration"""
    url: str = "sqlite:///./universities.db"
    echo: bool = False
    pool_size: int = 10
    max_overflow: int = 20

@dataclass
class AppConfig:
    """Main Application Configuration"""
    llm: LLMConfig
    scraper: ScraperConfig
    database: DatabaseConfig
    browser_config: Optional[BrowserConfig] = None
    log_level: str = "INFO"
    debug: bool = False

def load_config() -> AppConfig:
    """Load configuration from environment variables"""
    
    # LLM Configuration
    llm_config = LLMConfig(
        provider=os.getenv("LLM_PROVIDER", "openai"),
        api_key=os.getenv("LLM_API_KEY"),
        model=os.getenv("LLM_MODEL", "gpt-4"),
        base_url=os.getenv("LLM_BASE_URL"),
        temperature=float(os.getenv("LLM_TEMPERATURE", "0.1")),
        max_tokens=int(os.getenv("LLM_MAX_TOKENS", "1000")),
        timeout=int(os.getenv("LLM_TIMEOUT", "30"))
    )
    
    # Scraper Configuration
    scraper_config = ScraperConfig(
        type=os.getenv("SCRAPER_TYPE", "selenium"),
        headless=os.getenv("SCRAPER_HEADLESS", "true").lower() == "true",
        timeout=int(os.getenv("SCRAPER_TIMEOUT", "10")),
        user_agent=os.getenv("SCRAPER_USER_AGENT", "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"),
        delay_between_requests=float(os.getenv("SCRAPER_DELAY", "2.0")),
        max_retries=int(os.getenv("SCRAPER_MAX_RETRIES", "3")),
        browser_use_api_key=os.getenv("BROWSER_USE_API_KEY"),
        browser_use_base_url=os.getenv("BROWSER_USE_BASE_URL", "https://api.browser-use.com")
    )
    
    # Browser Configuration
    browser_config = None
    if os.getenv("BROWSER_USE_ENABLED", "false").lower() == "true":
        proxy_config = None
        if os.getenv("BROWSER_PROXY_SERVER"):
            proxy_config = ProxyConfig(
                server=os.getenv("BROWSER_PROXY_SERVER"),
                username=os.getenv("BROWSER_PROXY_USERNAME"),
                password=os.getenv("BROWSER_PROXY_PASSWORD")
            )
        
        browser_config = BrowserConfig(
            headless=os.getenv("BROWSER_HEADLESS", "true").lower() == "true",
            disable_security=os.getenv("BROWSER_DISABLE_SECURITY", "true").lower() == "true",
            chrome_instance_path=os.getenv("BROWSER_CHROME_PATH"),
            extra_chromium_args=os.getenv("BROWSER_EXTRA_ARGS", "").split(",") if os.getenv("BROWSER_EXTRA_ARGS") else None,
            wss_url=os.getenv("BROWSER_WSS_URL"),
            cdp_url=os.getenv("BROWSER_CDP_URL"),
            proxy=proxy_config,
            max_content_length=int(os.getenv("BROWSER_MAX_CONTENT_LENGTH", "2000"))
        )
    
    # Database Configuration
    database_config = DatabaseConfig(
        url=os.getenv("DATABASE_URL", "sqlite:///./universities.db"),
        echo=os.getenv("DATABASE_ECHO", "false").lower() == "true",
        pool_size=int(os.getenv("DATABASE_POOL_SIZE", "10")),
        max_overflow=int(os.getenv("DATABASE_MAX_OVERFLOW", "20"))
    )
    
    # Main Configuration
    app_config = AppConfig(
        llm=llm_config,
        scraper=scraper_config,
        database=database_config,
        browser_config=browser_config,
        log_level=os.getenv("LOG_LEVEL", "INFO"),
        debug=os.getenv("DEBUG", "false").lower() == "true"
    )
    
    return app_config

def create_env_template():
    """Create a template .env file"""
    env_template = """# LLM Configuration
LLM_PROVIDER=openai
LLM_API_KEY=your_openai_api_key_here
LLM_MODEL=gpt-4
LLM_BASE_URL=
LLM_TEMPERATURE=0.1
LLM_MAX_TOKENS=1000
LLM_TIMEOUT=30

# Scraper Configuration
SCRAPER_TYPE=selenium
SCRAPER_HEADLESS=true
SCRAPER_TIMEOUT=10
SCRAPER_USER_AGENT=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36
SCRAPER_DELAY=2.0
SCRAPER_MAX_RETRIES=3

# Browser Use Configuration (Alternative to Selenium)
BROWSER_USE_API_KEY=your_browser_use_api_key_here
BROWSER_USE_BASE_URL=https://api.browser-use.com

# Browser Configuration for BrowserUseTool
BROWSER_USE_ENABLED=false
BROWSER_HEADLESS=true
BROWSER_DISABLE_SECURITY=true
BROWSER_CHROME_PATH=
BROWSER_EXTRA_ARGS=
BROWSER_WSS_URL=
BROWSER_CDP_URL=
BROWSER_MAX_CONTENT_LENGTH=2000

# Browser Proxy Configuration
BROWSER_PROXY_SERVER=
BROWSER_PROXY_USERNAME=
BROWSER_PROXY_PASSWORD=

# Database Configuration
DATABASE_URL=sqlite:///./universities.db
DATABASE_ECHO=false
DATABASE_POOL_SIZE=10
DATABASE_MAX_OVERFLOW=20

# Application Configuration
LOG_LEVEL=INFO
DEBUG=false
"""
    
    env_file = Path(".env")
    if not env_file.exists():
        with open(env_file, "w") as f:
            f.write(env_template)
        print("Created .env template file")
    else:
        print(".env file already exists")

# Example configurations for different LLM providers
EXAMPLE_CONFIGS = {
    "openai": {
        "LLM_PROVIDER": "openai",
        "LLM_API_KEY": "sk-your-openai-api-key",
        "LLM_MODEL": "gpt-4",
        "LLM_BASE_URL": "",
    },
    "anthropic": {
        "LLM_PROVIDER": "anthropic",
        "LLM_API_KEY": "sk-ant-your-anthropic-api-key",
        "LLM_MODEL": "claude-3-sonnet-20240229",
        "LLM_BASE_URL": "",
    },
    "ollama": {
        "LLM_PROVIDER": "local",
        "LLM_API_KEY": "not-needed",
        "LLM_MODEL": "llama2",
        "LLM_BASE_URL": "http://localhost:11434/v1",
    },
    "local_openai": {
        "LLM_PROVIDER": "local",
        "LLM_API_KEY": "not-needed",
        "LLM_MODEL": "gpt-4",
        "LLM_BASE_URL": "http://localhost:1234/v1",
    }
}

# Example configurations for different scrapers
SCRAPER_CONFIGS = {
    "selenium": {
        "SCRAPER_TYPE": "selenium",
        "SCRAPER_HEADLESS": "true",
        "SCRAPER_TIMEOUT": "10",
    },
    "browser_use": {
        "SCRAPER_TYPE": "browser_use",
        "BROWSER_USE_API_KEY": "your-browser-use-api-key",
        "BROWSER_USE_BASE_URL": "https://api.browser-use.com",
    }
}

def get_example_config(provider: str) -> dict:
    """Get example configuration for a specific provider"""
    return EXAMPLE_CONFIGS.get(provider, EXAMPLE_CONFIGS["openai"])

def get_scraper_config(scraper_type: str) -> dict:
    """Get example configuration for a specific scraper"""
    return SCRAPER_CONFIGS.get(scraper_type, SCRAPER_CONFIGS["selenium"])

if __name__ == "__main__":
    # Create .env template if it doesn't exist
    create_env_template()
    
    # Load and display current configuration
    config = load_config()
    print("Current Configuration:")
    print(f"LLM Provider: {config.llm.provider}")
    print(f"LLM Model: {config.llm.model}")
    print(f"Scraper Type: {config.scraper.type}")
    print(f"Database URL: {config.database.url}")
    print(f"Scraper Headless: {config.scraper.headless}")
    print(f"Browser Use Enabled: {config.browser_config is not None}") 