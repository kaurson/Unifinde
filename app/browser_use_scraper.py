import asyncio
import json
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from pathlib import Path

# Import Playwright directly
from playwright.async_api import async_playwright, Browser, BrowserContext, Page

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class BrowserUseConfig:
    """Configuration for Browser Use with Chromium"""
    headless: bool = True
    disable_security: bool = True
    chrome_instance_path: Optional[str] = None
    extra_chromium_args: Optional[List[str]] = None
    max_content_length: int = 2000

class BrowserUseScraper:
    """University scraper using Playwright with Chromium"""
    
    def __init__(self, config: BrowserUseConfig):
        """
        Initialize Browser Use scraper with Chromium
        
        Args:
            config: Browser Use configuration
        """
        self.config = config
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.lock = asyncio.Lock()
    
    async def __aenter__(self):
        """Async context manager entry"""
        await self._ensure_browser_initialized()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.cleanup()
    
    async def _ensure_browser_initialized(self) -> BrowserContext:
        """Ensure browser and context are initialized."""
        async with self.lock:
            if self.playwright is None:
                self.playwright = await async_playwright().start()
            
            if self.browser is None:
                browser_args = []
                
                if self.config.disable_security:
                    browser_args.extend([
                        "--disable-web-security",
                        "--disable-features=VizDisplayCompositor"
                    ])
                
                if self.config.extra_chromium_args:
                    browser_args.extend(self.config.extra_chromium_args)
                
                self.browser = await self.playwright.chromium.launch(
                    headless=self.config.headless,
                    args=browser_args
                )
            
            if self.context is None:
                self.context = await self.browser.new_context()
                self.page = await self.context.new_page()
            
            return self.context
    
    async def search_university(self, university_name: str) -> List[Dict[str, str]]:
        """
        Search for university using Google search
        
        Args:
            university_name: Name of the university to search for
            
        Returns:
            List of potential university matches
        """
        try:
            await self._ensure_browser_initialized()
            
            # Navigate to Google
            await self.page.goto('https://www.google.com')
            await self.page.wait_for_load_state('networkidle')
            
            # Find and fill search box using a more reliable selector
            search_input = self.page.locator('input[name="q"]')
            await search_input.fill(f"{university_name} official website")
            await search_input.press("Enter")
            await self.page.wait_for_load_state('networkidle')
            
            # Wait for search results
            await self.page.wait_for_selector('div.g', timeout=10000)
            
            # Extract search results
            results = await self.page.evaluate("""
                () => {
                    const searchResults = document.querySelectorAll('div.g');
                    return Array.from(searchResults, (result, index) => {
                        if (index >= 5) return null; // Limit to 5 results
                        const titleElement = result.querySelector('h3');
                        const linkElement = result.querySelector('a');
                        if (!titleElement || !linkElement) return null;
                        
                        return {
                            title: titleElement.textContent.trim(),
                            url: linkElement.href,
                            confidence: 0.8 // Default confidence
                        };
                    }).filter(Boolean);
                }
            """)
            
            logger.info(f"Found {len(results)} search results for {university_name}")
            return results
            
        except Exception as e:
            logger.error(f"Error searching for university {university_name}: {e}")
            return []
    
    async def scrape_university_website(self, url: str) -> Dict[str, Any]:
        """
        Scrape university website using Playwright
        
        Args:
            url: URL of the university website to scrape
            
        Returns:
            Dictionary with scraped university data
        """
        try:
            await self._ensure_browser_initialized()
            
            # Navigate to the university website
            await self.page.goto(url)
            await self.page.wait_for_load_state('networkidle')
            
            # Wait a bit for dynamic content to load
            await asyncio.sleep(2)
            
            # Extract structured data using page evaluation
            scraped_data = await self.page.evaluate("""
                () => {
                    const data = {
                        name: '',
                        website: window.location.href,
                        contact_info: {},
                        academic_info: {},
                        statistics: {},
                        programs: [],
                        facilities: [],
                        about: {}
                    };
                    
                    // Extract university name from title or h1
                    const title = document.title;
                    const h1 = document.querySelector('h1');
                    data.name = h1 ? h1.textContent.trim() : title;
                    
                    // Extract contact information
                    const contactSelectors = [
                        'a[href^="tel:"]',
                        'a[href^="mailto:"]',
                        '[class*="contact"]',
                        '[class*="phone"]',
                        '[class*="email"]'
                    ];
                    
                    contactSelectors.forEach(selector => {
                        const elements = document.querySelectorAll(selector);
                        elements.forEach(el => {
                            const text = el.textContent.trim();
                            const href = el.getAttribute('href');
                            
                            if (href && href.startsWith('tel:')) {
                                data.contact_info.phone = href.replace('tel:', '');
                            } else if (href && href.startsWith('mailto:')) {
                                data.contact_info.email = href.replace('mailto:', '');
                            } else if (text && text.length > 0) {
                                if (!data.contact_info.address) {
                                    data.contact_info.address = text;
                                }
                            }
                        });
                    });
                    
                    // Extract academic information
                    const academicText = document.body.textContent.toLowerCase();
                    const foundedMatch = academicText.match(/founded\\s+in?\\s+(\\d{4})/i);
                    if (foundedMatch) {
                        data.academic_info.founded_year = parseInt(foundedMatch[1]);
                    }
                    
                    // Look for university type
                    if (academicText.includes('public university') || academicText.includes('state university')) {
                        data.academic_info.type = 'Public';
                    } else if (academicText.includes('private university')) {
                        data.academic_info.type = 'Private';
                    }
                    
                    // Extract statistics (basic patterns)
                    const statsPatterns = [
                        { pattern: /(\\d{1,3}(?:,\\d{3})*)\\s+students?/i, field: 'student_population' },
                        { pattern: /(\\d{1,3}(?:,\\d{3})*)\\s+faculty/i, field: 'faculty_count' },
                        { pattern: /(\\d+(?:\\.\\d+)?%)\\s+acceptance\\s+rate/i, field: 'acceptance_rate' }
                    ];
                    
                    statsPatterns.forEach(({ pattern, field }) => {
                        const match = academicText.match(pattern);
                        if (match) {
                            data.statistics[field] = match[1];
                        }
                    });
                    
                    // Extract programs (look for program-related sections)
                    const programElements = document.querySelectorAll('h2, h3, h4');
                    programElements.forEach(el => {
                        const text = el.textContent.toLowerCase();
                        if (text.includes('program') || text.includes('degree') || text.includes('major')) {
                            const programText = el.textContent.trim();
                            if (programText && !data.programs.includes(programText)) {
                                data.programs.push(programText);
                            }
                        }
                    });
                    
                    // Extract about information
                    const aboutSelectors = [
                        '[class*="about"]',
                        '[class*="mission"]',
                        '[class*="vision"]',
                        '[class*="description"]'
                    ];
                    
                    aboutSelectors.forEach(selector => {
                        const elements = document.querySelectorAll(selector);
                        elements.forEach(el => {
                            const text = el.textContent.trim();
                            if (text && text.length > 50) { // Only meaningful content
                                if (el.className.toLowerCase().includes('mission')) {
                                    data.about.mission = text;
                                } else if (el.className.toLowerCase().includes('vision')) {
                                    data.about.vision = text;
                                } else if (!data.about.description) {
                                    data.about.description = text;
                                }
                            }
                        });
                    });
                    
                    return data;
                }
            """)
            
            # Clean up the data
            scraped_data = self._clean_scraped_data(scraped_data)
            
            logger.info(f"Successfully scraped data from {url}")
            return scraped_data
            
        except Exception as e:
            logger.error(f"Error scraping university website {url}: {e}")
            return {
                "name": "",
                "website": url,
                "contact_info": {},
                "academic_info": {},
                "statistics": {},
                "programs": [],
                "facilities": [],
                "about": {}
            }
    
    def _clean_scraped_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Clean and validate scraped data"""
        cleaned = {}
        
        # Clean basic info
        cleaned["name"] = data.get("name", "").strip()
        cleaned["website"] = data.get("website", "").strip()
        
        # Clean contact info
        contact_info = data.get("contact_info", {})
        cleaned["contact_info"] = {
            "phone": contact_info.get("phone", "").strip(),
            "email": contact_info.get("email", "").strip(),
            "address": contact_info.get("address", "").strip()
        }
        
        # Clean academic info
        academic_info = data.get("academic_info", {})
        cleaned["academic_info"] = {
            "founded_year": academic_info.get("founded_year"),
            "type": academic_info.get("type", "").strip()
        }
        
        # Clean statistics
        statistics = data.get("statistics", {})
        cleaned["statistics"] = {
            "student_population": statistics.get("student_population", "").strip(),
            "faculty_count": statistics.get("faculty_count", "").strip(),
            "acceptance_rate": statistics.get("acceptance_rate", "").strip()
        }
        
        # Clean programs (remove duplicates and empty entries)
        programs = data.get("programs", [])
        cleaned["programs"] = [p.strip() for p in programs if p.strip()]
        
        # Clean facilities
        facilities = data.get("facilities", [])
        cleaned["facilities"] = [f.strip() for f in facilities if f.strip()]
        
        # Clean about info
        about = data.get("about", {})
        cleaned["about"] = {
            "description": about.get("description", "").strip(),
            "mission": about.get("mission", "").strip(),
            "vision": about.get("vision", "").strip()
        }
        
        return cleaned
    
    async def cleanup(self):
        """Clean up browser resources."""
        async with self.lock:
            if self.page is not None:
                await self.page.close()
                self.page = None
            if self.context is not None:
                await self.context.close()
                self.context = None
            if self.browser is not None:
                await self.browser.close()
                self.browser = None
            if self.playwright is not None:
                await self.playwright.stop()
                self.playwright = None
    
    def close(self):
        """Synchronous close method for compatibility"""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # Schedule cleanup for later
                loop.create_task(self.cleanup())
            else:
                loop.run_until_complete(self.cleanup())
        except RuntimeError:
            # No event loop, create a new one
            asyncio.run(self.cleanup())

async def example_browser_use():
    """Example usage of Browser Use scraper"""
    config = BrowserUseConfig(
        headless=True,
        disable_security=True
    )
    
    async with BrowserUseScraper(config) as scraper:
        # Search for a university
        results = await scraper.search_university("MIT")
        print(f"Search results: {results}")
        
        if results:
            # Scrape the first result
            url = results[0]["url"]
            data = await scraper.scrape_university_website(url)
            print(f"Scraped data: {json.dumps(data, indent=2)}")

if __name__ == "__main__":
    asyncio.run(example_browser_use()) 