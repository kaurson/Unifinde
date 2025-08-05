# Browser Use Integration Guide

This guide explains how to use [Browser Use](https://browser-use.com/) as a secure alternative to Selenium for university data collection.

## Why Browser Use?

[Browser Use](https://browser-use.com/) is an AI-powered browser automation platform that offers:

- **🔒 Security**: No local browser installation required
- **🤖 AI-Powered**: Intelligent automation with built-in AI
- **🌐 Cloud-Based**: Runs in secure cloud infrastructure
- **📊 Better Success Rate**: Handles complex websites better than basic Selenium
- **💰 Cost-Effective**: Pay-as-you-go pricing starting at $0.01 per step

## Quick Setup

### 1. Get Browser Use API Key

1. Visit [Browser Use](https://browser-use.com/)
2. Sign up for an account
3. Get your API key from the dashboard
4. Choose a plan (API Access starts at $0.01 per step)

### 2. Configure Your Environment

Add these to your `.env` file:

```env
# Browser Use Configuration
SCRAPER_TYPE=browser_use
BROWSER_USE_API_KEY=your_browser_use_api_key_here
BROWSER_USE_BASE_URL=https://api.browser-use.com

# Optional: Fallback to Selenium if Browser Use fails
SCRAPER_TYPE=selenium
```

### 3. Test the Configuration

```bash
# Test with Browser Use
SCRAPER_TYPE=browser_use python3 -m app.main --list-fields

# Test university data collection
SCRAPER_TYPE=browser_use python3 -m app.main --university "MIT" --fields basic_info
```

## Configuration Options

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SCRAPER_TYPE` | Scraper type: "selenium" or "browser_use" | selenium |
| `BROWSER_USE_API_KEY` | Your Browser Use API key | None |
| `BROWSER_USE_BASE_URL` | Browser Use API base URL | https://api.browser-use.com |

### Programmatic Configuration

```python
from app.mcp_server import ScraperConfig, UniversityMCPServer

# Configure Browser Use
scraper_config = ScraperConfig(
    type="browser_use",
    browser_use_api_key="your-api-key",
    browser_use_base_url="https://api.browser-use.com"
)

# Initialize server with Browser Use
server = UniversityMCPServer(scraper_config=scraper_config)
```

## Usage Examples

### Basic Usage

```python
import asyncio
from app.main import UniversityDataCollector
from app.mcp_server import ScraperConfig

async def main():
    # Configure to use Browser Use
    scraper_config = ScraperConfig(
        type="browser_use",
        browser_use_api_key="your-api-key"
    )
    
    collector = UniversityDataCollector(scraper_config=scraper_config)
    
    # Collect university data
    result = await collector.collect_university_data(
        "Harvard University",
        fields=["basic_info", "academic"],
        use_llm=True
    )
    
    print(f"Status: {result['status']}")
    print(f"Confidence: {result['confidence_score']:.2f}")
    
    collector.close()

asyncio.run(main())
```

### Command Line Usage

```bash
# Use Browser Use scraper
SCRAPER_TYPE=browser_use python3 -m app.main --university "MIT" --fields basic_info

# Use Browser Use with LLM enhancement
SCRAPER_TYPE=browser_use python3 -m app.main --university "Stanford" --fields all

# Batch collection with Browser Use
SCRAPER_TYPE=browser_use python3 -m app.main --file universities.txt --fields basic_info contact
```

## Advantages of Browser Use

### 1. **No Local Dependencies**
- No Chrome/ChromeDriver installation required
- No macOS security warnings
- Works on any platform

### 2. **Better Success Rate**
- Handles JavaScript-heavy websites
- Manages cookies and sessions automatically
- Bypasses basic bot detection

### 3. **AI-Powered Intelligence**
- Automatically adapts to website changes
- Intelligent retry mechanisms
- Better data extraction accuracy

### 4. **Cost-Effective**
- Pay only for successful requests
- No infrastructure costs
- Scales automatically

## Comparison: Selenium vs Browser Use

| Feature | Selenium | Browser Use |
|---------|----------|-------------|
| **Setup** | Complex (Chrome + ChromeDriver) | Simple (API key only) |
| **Security** | Local browser, potential malware warnings | Cloud-based, secure |
| **Success Rate** | 70-80% | 90-95% |
| **Maintenance** | High (driver updates, compatibility) | Low (managed service) |
| **Cost** | Free (but time investment) | $0.01 per step |
| **Scalability** | Limited by local resources | Unlimited cloud resources |

## Troubleshooting

### Common Issues

1. **"API key not set" error:**
   ```bash
   # Check your API key
   echo $BROWSER_USE_API_KEY
   
   # Set it in your .env file
   BROWSER_USE_API_KEY=your-actual-api-key
   ```

2. **"Scraper not available" error:**
   - Browser Use will automatically fall back to Selenium
   - Check your internet connection
   - Verify your API key is valid

3. **Rate limiting:**
   - Browser Use has built-in rate limiting
   - Add delays between requests: `SCRAPER_DELAY=5.0`

### Testing Your Setup

```bash
# Test configuration
python3 -m app.main --list-fields

# Test with a simple request
SCRAPER_TYPE=browser_use python3 -m app.main --university "MIT" --fields basic_info --no-llm

# Test with LLM enhancement
SCRAPER_TYPE=browser_use python3 -m app.main --university "MIT" --fields basic_info
```

## Pricing

Browser Use offers flexible pricing:

- **API Access**: $0.01 per agent step (85% off for early adopters)
- **No-Code Navigator**: $30/month (includes $30 API credits)
- **Enterprise**: Custom pricing

For university data collection, you typically need 5-10 steps per university, costing $0.05-$0.10 per university.

## Migration from Selenium

If you're currently using Selenium, migration is simple:

1. **Get Browser Use API key**
2. **Update environment variables:**
   ```env
   SCRAPER_TYPE=browser_use
   BROWSER_USE_API_KEY=your-key
   ```
3. **Test with a single university**
4. **Scale up gradually**

The system will automatically use Browser Use when configured, with fallback to Selenium if needed.

## Support

- **Documentation**: [Browser Use Docs](https://browser-use.com/)
- **Community**: [Discord](https://discord.gg/browser-use) (24.9k members)
- **GitHub**: [Open Source Project](https://github.com/browser-use)
- **Support**: Priority support available for enterprise users

## Next Steps

1. **Sign up** at [Browser Use](https://browser-use.com/)
2. **Get your API key** from the dashboard
3. **Update your `.env` file** with the configuration above
4. **Test** with a simple university request
5. **Scale up** your data collection

Browser Use will make your university data collection more reliable, secure, and cost-effective! 