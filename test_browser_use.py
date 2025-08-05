#!/usr/bin/env python3
"""
Test script for Browser-use integration with Chromium
"""

import asyncio
import json
from app.browser_use_scraper import BrowserUseScraper, BrowserUseConfig

async def test_browser_use():
    """Test Browser-use scraper functionality"""
    print("🧪 Testing Browser-use Integration with Chromium")
    print("=" * 50)
    
    # Configure Browser-use with Chromium
    config = BrowserUseConfig(
        headless=True,  # Set to False to see the browser in action
        disable_security=True,
        extra_chromium_args=["--no-sandbox", "--disable-dev-shm-usage"]
    )
    
    try:
        print("🚀 Initializing Browser-use scraper...")
        async with BrowserUseScraper(config) as scraper:
            print("✅ Browser-use scraper initialized successfully")
            
            # Test university search
            print("\n🔍 Testing university search...")
            search_results = await scraper.search_university("MIT")
            
            if search_results:
                print(f"✅ Found {len(search_results)} search results")
                for i, result in enumerate(search_results[:3]):  # Show first 3 results
                    print(f"  {i+1}. {result['title']}")
                    print(f"     URL: {result['url']}")
                
                # Test website scraping
                print(f"\n🌐 Testing website scraping for: {search_results[0]['title']}")
                scraped_data = await scraper.scrape_university_website(search_results[0]['url'])
                
                print("✅ Website scraping completed")
                print(f"📊 Extracted data:")
                print(f"  Name: {scraped_data.get('name', 'N/A')}")
                print(f"  Website: {scraped_data.get('website', 'N/A')}")
                
                # Show contact info
                contact_info = scraped_data.get('contact_info', {})
                if any(contact_info.values()):
                    print(f"  Contact Info:")
                    for key, value in contact_info.items():
                        if value:
                            print(f"    {key}: {value}")
                
                # Show academic info
                academic_info = scraped_data.get('academic_info', {})
                if any(academic_info.values()):
                    print(f"  Academic Info:")
                    for key, value in academic_info.items():
                        if value:
                            print(f"    {key}: {value}")
                
                # Show statistics
                statistics = scraped_data.get('statistics', {})
                if any(statistics.values()):
                    print(f"  Statistics:")
                    for key, value in statistics.items():
                        if value:
                            print(f"    {key}: {value}")
                
                # Save test results to JSON
                test_results = {
                    "test": "browser_use_integration",
                    "search_results": search_results,
                    "scraped_data": scraped_data,
                    "status": "success"
                }
                
                with open("test_browser_use_results.json", "w") as f:
                    json.dump(test_results, f, indent=2)
                
                print(f"\n💾 Test results saved to: test_browser_use_results.json")
                
            else:
                print("❌ No search results found")
                
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()

async def test_multiple_universities():
    """Test scraping multiple universities"""
    print("\n🎓 Testing Multiple Universities")
    print("=" * 30)
    
    config = BrowserUseConfig(headless=True, disable_security=True)
    
    universities = ["Harvard University"]
    
    try:
        async with BrowserUseScraper(config) as scraper:
            for university in universities:
                print(f"\n🔍 Searching for: {university}")
                results = await scraper.search_university(university)
                
                if results:
                    print(f"✅ Found {len(results)} results")
                    url = results[0]['url']
                    print(f"🌐 Scraping: {url}")
                    
                    data = await scraper.scrape_university_website(url)
                    print(f"📊 Extracted: {data.get('name', 'Unknown')}")
                    
                    # Brief delay between requests
                    await asyncio.sleep(1)
                else:
                    print(f"❌ No results found for {university}")
                    
    except Exception as e:
        print(f"❌ Error: {e}")

async def main():
    """Run all tests"""
    print("🚀 Browser-use Integration Test Suite")
    print("=" * 50)
    
    # Test basic functionality
    await test_browser_use()
    
    # Test multiple universities
    await test_multiple_universities()
    
    print("\n" + "=" * 50)
    print("✅ All tests completed!")

if __name__ == "__main__":
    asyncio.run(main()) 