#!/usr/bin/env python3
"""
Test script for direct university website scraping with Playwright
"""

import asyncio
import json
from app.browser_use_scraper import BrowserUseScraper, BrowserUseConfig

async def test_direct_scraping():
    """Test direct website scraping without Google search"""
    print("🧪 Testing Direct Website Scraping with Playwright")
    print("=" * 50)
    
    # Configure Playwright scraper
    config = BrowserUseConfig(
        headless=True,
        disable_security=True,
        extra_chromium_args=["--no-sandbox", "--disable-dev-shm-usage"]
    )
    
    try:
        print("🚀 Initializing Playwright scraper...")
        async with BrowserUseScraper(config) as scraper:
            print("✅ Playwright scraper initialized successfully")
            
            # Test direct scraping of MIT website
            print("\n🌐 Testing direct scraping of MIT website...")
            mit_url = "https://web.mit.edu/"
            
            scraped_data = await scraper.scrape_university_website(mit_url)
            
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
            
            # Show programs (first few)
            programs = scraped_data.get('programs', [])
            if programs:
                print(f"  Programs (first 3):")
                for program in programs[:3]:
                    print(f"    - {program}")
            
            # Show about info
            about = scraped_data.get('about', {})
            if any(about.values()):
                print(f"  About Info:")
                for key, value in about.items():
                    if value:
                        print(f"    {key}: {value[:100]}...")  # Show first 100 chars
            
            # Save test results to JSON
            test_results = {
                "test": "direct_scraping",
                "url": mit_url,
                "scraped_data": scraped_data,
                "status": "success"
            }
            
            with open("test_direct_scraping_results.json", "w") as f:
                json.dump(test_results, f, indent=2)
            
            print(f"\n💾 Test results saved to: test_direct_scraping_results.json")
            
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()

async def test_multiple_universities_direct():
    """Test direct scraping of multiple university websites"""
    print("\n🎓 Testing Multiple Universities (Direct Scraping)")
    print("=" * 50)
    
    config = BrowserUseConfig(headless=True, disable_security=True)
    
    universities = [
        ("MIT", "https://web.mit.edu/"),
        ("Harvard", "https://www.harvard.edu/"),
        ("Stanford", "https://www.stanford.edu/")
    ]
    
    try:
        async with BrowserUseScraper(config) as scraper:
            for name, url in universities:
                print(f"\n🔍 Scraping: {name} ({url})")
                
                try:
                    data = await scraper.scrape_university_website(url)
                    print(f"✅ Successfully scraped {name}")
                    print(f"📊 Name: {data.get('name', 'Unknown')}")
                    
                    # Show some key data
                    contact = data.get('contact_info', {})
                    if contact.get('email') or contact.get('phone'):
                        print(f"📞 Contact: {contact.get('email', 'N/A')} | {contact.get('phone', 'N/A')}")
                    
                    # Brief delay between requests
                    await asyncio.sleep(1)
                    
                except Exception as e:
                    print(f"❌ Failed to scrape {name}: {e}")
                    
    except Exception as e:
        print(f"❌ Error: {e}")

async def main():
    """Run all direct scraping tests"""
    print("🚀 Direct Scraping Test Suite")
    print("=" * 50)
    
    # Test direct scraping
    await test_direct_scraping()
    
    # Test multiple universities
    await test_multiple_universities_direct()
    
    print("\n" + "=" * 50)
    print("✅ All direct scraping tests completed!")

if __name__ == "__main__":
    asyncio.run(main()) 