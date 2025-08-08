import asyncio
import json
import time
from typing import Dict, List, Any, Optional
from datetime import datetime
import aiohttp
from playwright.async_api import async_playwright, Browser, Page
from openai import AsyncOpenAI
from sqlalchemy.orm import Session
from database.models import UniversityDataCollectionResult
from database.database import get_db
from dotenv import load_dotenv
import os
import re

# Load environment variables
load_dotenv()

class UniversityDataScraper:
    def __init__(self, openai_api_key: str = None, db_session: Session = None):
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        if not self.openai_api_key:
            raise ValueError("OpenAI API key is required. Set OPENAI_API_KEY environment variable or pass it to the constructor.")
        
        self.db_session = db_session
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        
        # Configure OpenAI client
        self.openai_client = AsyncOpenAI(api_key=self.openai_api_key)
        
        # University data schema for LLM to fill
        self.university_data_schema = {
            "name": "string",
            "website": "string",
            "country": "string",
            "city": "string",
            "state": "string",
            "phone": "string",
            "email": "string",
            "founded_year": "integer",
            "type": "string",  # Public, Private, etc.
            "student_population": "integer",
            "undergraduate_population": "integer",
            "graduate_population": "integer",
            "international_students_percentage": "float",
            "faculty_count": "integer",
            "student_faculty_ratio": "float",
            "acceptance_rate": "float",
            "tuition_domestic": "float",
            "tuition_international": "float",
            "room_and_board": "float",
            "total_cost_of_attendance": "float",
            "financial_aid_available": "boolean",
            "average_financial_aid_package": "float",
            "scholarships_available": "boolean",
            "world_ranking": "integer",
            "national_ranking": "integer",
            "regional_ranking": "integer",
            "subject_rankings": {
                "engineering": "integer",
                "business": "integer",
                "computer_science": "integer",
                "medicine": "integer",
                "law": "integer",
                "arts": "integer",
                "sciences": "integer"
            },
            "description": "string",
            "mission_statement": "string",
            "vision_statement": "string",
            "campus_size": "string",
            "campus_type": "string",  # Urban, Suburban, Rural
            "climate": "string",
            "timezone": "string",
            "programs": [
                {
                    "name": "string",
                    "level": "string",  # Bachelor, Master, PhD, Certificate
                    "field": "string",
                    "department": "string",
                    "duration": "string",
                    "tuition": "float",
                    "description": "string",
                    "requirements": "string",
                    "career_outcomes": "string",
                    "accreditation": "string",
                    "enrollment_capacity": "integer",
                    "available": "boolean"
                }
            ],
            "student_life": {
                "housing_options": ["string"],
                "student_organizations": "integer",
                "sports_teams": ["string"],
                "campus_activities": ["string"],
                "health_services": "boolean",
                "counseling_services": "boolean"
            },
            "financial_aid": {
                "need_based_aid": "boolean",
                "merit_based_aid": "boolean",
                "scholarships": [
                    {
                        "name": "string",
                        "amount": "float",
                        "eligibility": "string",
                        "application_required": "boolean"
                    }
                ],
                "grants": ["string"],
                "work_study_available": "boolean",
                "loan_options": ["string"]
            },
            "international_students": {
                "international_office": "boolean",
                "english_language_requirements": ["string"],
                "visa_support": "boolean",
                "international_student_services": ["string"],
                "cultural_programs": ["string"]
            },
            "alumni": {
                "alumni_network_size": "integer",
                "notable_alumni": ["string"],
                "alumni_association": "boolean",
                "alumni_events": "integer"
            },
            "confidence_score": "float",
            "source_urls": ["string"],
            "last_updated": "string"
        }

    async def initialize_browser(self):
        """Initialize the browser for web scraping"""
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(
            headless=True,
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-accelerated-2d-canvas',
                '--no-first-run',
                '--no-zygote',
                '--disable-gpu',
                '--disable-background-timer-throttling',
                '--disable-backgrounding-occluded-windows',
                '--disable-renderer-backgrounding',
                '--disable-features=TranslateUI',
                '--disable-ipc-flooding-protection',
                '--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            ]
        )
        self.page = await self.browser.new_page()
        
        # Set user agent and other headers to avoid detection
        await self.page.set_extra_http_headers({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        
        # Set viewport
        await self.page.set_viewport_size({"width": 1920, "height": 1080})

    async def close_browser(self):
        """Close the browser"""
        if self.browser:
            await self.browser.close()

    async def search_university_info(self, university_name: str, search_queries: List[str] = None) -> Dict[str, Any]:
        """Search for university information using multiple search engines"""
        if not search_queries:
            search_queries = [
                # Essential Basic Information
                f"{university_name} university official website facts statistics",
                f"{university_name} university contact information location",
                f"{university_name} university email address phone number contact details",
                
                # SUBJECT RANKINGS - COMPACT
                f"{university_name} university rankings US News QS Times engineering business computer science",
                f"{university_name} university subject rankings 2024 medicine law arts sciences",
                
                # FINANCIAL AID - COMPACT
                f"{university_name} university tuition fees cost financial aid scholarships 2024",
                f"{university_name} university room board total cost of attendance",
                
                # INTERNATIONAL STUDENTS - COMPACT
                f"{university_name} university international students services requirements TOEFL IELTS",
                f"{university_name} university study abroad exchange programs",
                
                # Academic Programs - COMPACT
                f"{university_name} university undergraduate graduate programs majors degrees",
                f"{university_name} university schools colleges departments research",
                
                # Student Life - COMPACT
                f"{university_name} university student life housing organizations sports",
                f"{university_name} university campus facilities libraries labs",
                
                # Faculty and Alumni - COMPACT
                f"{university_name} university faculty staff student ratio",
                f"{university_name} university alumni network notable graduates"
            ]

        search_results = {}
        
        # Try multiple search strategies
        search_strategies = [
            self._try_wikipedia_academic_search,  # Most reliable - Wikipedia and academic sources
            self._try_educational_database_search,  # Educational databases and ranking sites
            self._try_google_search,  # Google as backup
            self._try_direct_search,  # Direct URL attempts
            self._try_bing_search,  # Bing as last resort (having issues)
            self._try_knowledge_based_fallback  # Final fallback using LLM knowledge
        ]
        
        for strategy in search_strategies:
            try:
                print(f"Trying search strategy: {strategy.__name__}")
                search_results = await strategy(university_name, search_queries)
                
                # Check if we got any results
                total_results = sum(len(results) for results in search_results.values())
                if total_results > 0:
                    print(f"✅ Search strategy {strategy.__name__} found {total_results} results")
                    break
                else:
                    print(f"❌ Search strategy {strategy.__name__} found no results")
                    
            except Exception as e:
                print(f"❌ Search strategy {strategy.__name__} failed: {e}")
                continue
        
        # If no results found from any strategy, return error
        total_results = sum(len(results) for results in search_results.values())
        if total_results == 0:
            print("❌ No search results found from any strategy")
            raise Exception(f"Failed to find any search results for {university_name}")
        
        return search_results

    async def _try_google_search(self, university_name: str, search_queries: List[str]) -> Dict[str, Any]:
        """Try Google search with enhanced anti-bot measures"""
        search_results = {}
        
        try:
            print("Attempting Google search with enhanced measures...")
            
            # Set up browser with better anti-detection
            await self.page.set_extra_http_headers({
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            })
            
            # Navigate to Google with shorter timeout
            await self.page.goto("https://www.google.com", wait_until="domcontentloaded", timeout=20000)
            await asyncio.sleep(2)
            
            # Handle various consent/cookie popups
            consent_selectors = [
                'button[id="L2AGLb"]',
                'button[aria-label*="Accept"]',
                'button[aria-label*="Agree"]',
                'button:has-text("Accept")',
                'button:has-text("Agree")',
                'button:has-text("I agree")',
                'button:has-text("Accept all")',
                'button:has-text("Reject all")',
                'button[data-testid="cookie-banner-accept"]',
                'button[data-testid="cookie-banner-reject"]'
            ]
            
            for selector in consent_selectors:
                try:
                    consent_button = await self.page.query_selector(selector)
                    if consent_button:
                        await consent_button.click()
                        await asyncio.sleep(1)
                        print(f"Clicked consent button: {selector}")
                        break
                except:
                    continue
            
            # Try to find search box with multiple selectors
            search_selectors = [
                'textarea[name="q"]',
                'input[name="q"]',
                'input[title="Search"]',
                'input[aria-label="Search"]',
                'textarea[aria-label="Search"]'
            ]
            
            # Perform searches with reduced number to avoid timeouts
            for i, query in enumerate(search_queries[:3]):  # Reduced to first 3 queries to avoid timeouts
                print(f"Searching for: {query}")
                
                try:
                    # Navigate back to Google homepage for each search to avoid element detachment issues
                    if i > 0:
                        await self.page.goto("https://www.google.com", wait_until="domcontentloaded", timeout=10000)
                        await asyncio.sleep(2)
                        
                        # Handle consent popup again if it appears
                        for selector in consent_selectors:
                            try:
                                consent_button = await self.page.query_selector(selector)
                                if consent_button:
                                    await consent_button.click()
                                    await asyncio.sleep(1)
                                    break
                            except:
                                continue
                    
                    # Find search box again for each search (to avoid detached element issues)
                    search_box = None
                    for selector in search_selectors:
                        try:
                            search_box = await self.page.query_selector(selector)
                            if search_box:
                                print(f"Found search box with selector: {selector}")
                                break
                        except:
                            continue
                    
                    if not search_box:
                        # Try to find any input field
                        search_box = await self.page.query_selector('input, textarea')
                    
                    if not search_box:
                        print(f"Could not find search input field for query: {query}")
                        search_results[query] = []
                        continue
                    
                    # Clear and fill search box with shorter timeout
                    try:
                        await search_box.click(timeout=5000)
                        await search_box.fill("")
                        await asyncio.sleep(0.5)
                        await search_box.type(query, delay=50)  # Faster typing
                        await asyncio.sleep(0.5)
                        
                        # Press Enter
                        await search_box.press('Enter')
                        await self.page.wait_for_load_state("domcontentloaded", timeout=10000)
                        await asyncio.sleep(1)
                    except Exception as e:
                        print(f"Error interacting with search box: {e}")
                        search_results[query] = []
                        continue
                    
                    # Extract results with multiple selectors
                    result_selectors = [
                        'div.g',
                        'div[data-sokoban-container]',
                        'div[jscontroller]',
                        'div[data-hveid]',
                        'div[data-ved]'
                    ]
                    
                    results = []
                    for selector in result_selectors:
                        try:
                            elements = await self.page.query_selector_all(selector)
                            if elements:
                                results.extend(elements)
                                print(f"Found {len(elements)} results with selector: {selector}")
                        except:
                            continue
                    
                    # Remove duplicates
                    unique_results = []
                    seen_urls = set()
                    
                    for result in results[:8]:  # Reduced to top 8 results
                        try:
                            # Try multiple selectors for title and link
                            title_selectors = ['h3', '.LC20lb', '.DKV0Md', 'a[href] h3']
                            link_selectors = ['a[href]', 'a']
                            snippet_selectors = ['.VwiC3b', '.st', '.aCOpRe', '.s3v9rd']
                            
                            title = None
                            link = None
                            snippet = ""
                            
                            # Extract title
                            for selector in title_selectors:
                                try:
                                    title_elem = await result.query_selector(selector)
                                    if title_elem:
                                        title = await title_elem.inner_text()
                                        if title:
                                            break
                                except:
                                    continue
                            
                            # Extract link
                            for selector in link_selectors:
                                try:
                                    link_elem = await result.query_selector(selector)
                                    if link_elem:
                                        link = await link_elem.get_attribute('href')
                                        if link and link.startswith('http'):
                                            break
                                except:
                                    continue
                            
                            # Extract snippet
                            for selector in snippet_selectors:
                                try:
                                    snippet_elem = await result.query_selector(selector)
                                    if snippet_elem:
                                        snippet = await snippet_elem.inner_text()
                                        if snippet:
                                            break
                                except:
                                    continue
                            
                            # Only include valid results
                            if title and link and link.startswith('http') and not link.startswith('https://www.google.com'):
                                if link not in seen_urls:
                                    seen_urls.add(link)
                                    unique_results.append({
                                        "title": title,
                                        "url": link,
                                        "snippet": snippet
                                    })
                                    print(f"  - Found: {title}")
                                    print(f"    URL: {link}")
                                    
                        except Exception as e:
                            print(f"    Error extracting result: {e}")
                            continue
                    
                    search_results[query] = unique_results
                    
                    # Wait between searches
                    if i < len(search_queries[:3]) - 1:
                        await asyncio.sleep(1)  # Reduced wait time
                        
                except Exception as e:
                    print(f"Error during search for '{query}': {e}")
                    search_results[query] = []
                    continue
                
        except Exception as e:
            print(f"Google search failed: {e}")
            # Return empty results for all queries
            for query in search_queries:
                search_results[query] = []
        
        return search_results

    async def _try_bing_search(self, university_name: str, search_queries: List[str]) -> Dict[str, Any]:
        """Try Bing search as alternative to Google"""
        search_results = {}
        
        try:
            print("Attempting Bing search...")
            await self.page.goto("https://www.bing.com", wait_until="domcontentloaded", timeout=15000)
            await asyncio.sleep(1)
            
            for i, query in enumerate(search_queries[:8]):  # Reduced to 8 queries to avoid timeouts
                print(f"Bing searching for: {query}")
                
                try:
                    # Find and fill search box
                    search_box = await self.page.query_selector('#sb_form_q')
                    if search_box:
                        await search_box.fill(query)
                        await asyncio.sleep(0.5)
                        await search_box.press('Enter')
                        await self.page.wait_for_load_state("domcontentloaded", timeout=10000)  # Reduced timeout
                        await asyncio.sleep(1)
                        
                        # Extract results
                        results = await self.page.query_selector_all('li.b_algo')
                        query_results = []
                        
                        for result in results[:8]:  # Reduced to 8 results
                            try:
                                title_elem = await result.query_selector('h2 a')
                                link_elem = await result.query_selector('h2 a')
                                snippet_elem = await result.query_selector('.b_caption p')
                                
                                if title_elem and link_elem:
                                    title = await title_elem.inner_text()
                                    link = await link_elem.get_attribute('href')
                                    snippet = await snippet_elem.inner_text() if snippet_elem else ""
                                    
                                    if link and link.startswith('http'):
                                        query_results.append({
                                            "title": title,
                                            "url": link,
                                            "snippet": snippet
                                        })
                                        print(f"  - Found: {title}")
                                        print(f"    URL: {link}")
                            except Exception as e:
                                print(f"    Error extracting Bing result: {e}")
                                continue
                        
                        search_results[query] = query_results
                        
                        if i < len(search_queries[:8]) - 1:
                            await asyncio.sleep(1)  # Reduced wait time
                            
                except Exception as e:
                    print(f"Error during Bing search for '{query}': {e}")
                    search_results[query] = []
                    continue
                    
        except Exception as e:
            print(f"Bing search failed: {e}")
            for query in search_queries:
                search_results[query] = []
        
        return search_results

    async def _try_direct_search(self, university_name: str, search_queries: List[str]) -> Dict[str, Any]:
        """Try direct search by constructing URLs"""
        search_results = {}
        
        try:
            print("Attempting direct search...")
            
            # Try to find university website directly
            direct_urls = [
                f"https://www.{university_name.lower().replace(' ', '')}.edu",
                f"https://{university_name.lower().replace(' ', '')}.edu",
                f"https://www.{university_name.lower().replace('university', 'uni').replace(' ', '')}.edu",
                f"https://{university_name.lower().replace('university', 'uni').replace(' ', '')}.edu"
            ]
            
            for url in direct_urls:
                try:
                    await self.page.goto(url, wait_until="networkidle", timeout=30000)
                    await asyncio.sleep(2)
                    
                    # Check if page loaded successfully
                    title = await self.page.title()
                    if title and "error" not in title.lower() and "not found" not in title.lower():
                        search_results[f"{university_name} university official website"] = [{
                            "title": title,
                            "url": url,
                            "snippet": f"Direct access to {university_name} official website"
                        }]
                        print(f"✅ Found direct website: {url}")
                        break
                        
                except Exception as e:
                    print(f"Direct access failed for {url}: {e}")
                    continue
        
        except Exception as e:
            print(f"Direct search failed: {e}")
        
        return search_results

    async def _try_educational_database_search(self, university_name: str, search_queries: List[str]) -> Dict[str, Any]:
        """Try searching educational databases and university websites directly"""
        search_results = {}
        
        try:
            print("Attempting educational database search...")
            
            # List of educational databases and university ranking sites
            educational_sites = [
                "https://www.usnews.com/best-colleges",
                "https://www.timeshighereducation.com/world-university-rankings",
                "https://www.topuniversities.com/university-rankings",
                "https://www.collegefactual.com",
                "https://www.collegesimply.com",
                "https://www.universityguru.com",
                "https://www.unirank.org",
                "https://www.edurank.org",
                "https://www.4icu.org",
                "https://www.webometrics.info"
            ]
            
            for site in educational_sites:
                try:
                    print(f"Searching on: {site}")
                    await self.page.goto(site, wait_until="domcontentloaded", timeout=15000)
                    await asyncio.sleep(2)
                    
                    # Try to find search functionality
                    search_selectors = [
                        'input[type="search"]',
                        'input[name*="search"]',
                        'input[placeholder*="search"]',
                        'input[placeholder*="Search"]',
                        'input[id*="search"]',
                        'input[class*="search"]',
                        '.search input',
                        '#search input',
                        'form input[type="text"]'
                    ]
                    
                    search_box = None
                    for selector in search_selectors:
                        try:
                            search_box = await self.page.query_selector(selector)
                            if search_box:
                                break
                        except:
                            continue
                    
                    if search_box:
                        # Try to search for the university
                        await search_box.fill(university_name)
                        await asyncio.sleep(1)
                        await search_box.press('Enter')
                        await self.page.wait_for_load_state("domcontentloaded", timeout=10000)
                        await asyncio.sleep(2)
                        
                        # Extract results
                        results = await self.page.query_selector_all('a[href*="http"]')
                        query_results = []
                        
                        for result in results[:10]:
                            try:
                                href = await result.get_attribute('href')
                                title = await result.inner_text()
                                
                                if href and href.startswith('http') and len(title.strip()) > 10:
                                    # Check if the URL contains university-related keywords
                                    if any(keyword in href.lower() for keyword in ['university', 'college', 'edu', 'academic']):
                                        query_results.append({
                                            "title": title.strip(),
                                            "url": href,
                                            "snippet": f"Found on {site}"
                                        })
                                        print(f"  - Found: {title.strip()}")
                                        print(f"    URL: {href}")
                            except Exception as e:
                                continue
                        
                        if query_results:
                            search_results[f"{university_name} on {site}"] = query_results
                    
                except Exception as e:
                    print(f"Error searching {site}: {e}")
                    continue
            
            # Also try direct university website access
            direct_urls = [
                f"https://www.{university_name.lower().replace(' ', '').replace('university', 'edu')}.edu",
                f"https://{university_name.lower().replace(' ', '').replace('university', 'edu')}.edu",
                f"https://www.{university_name.lower().replace(' ', '-')}.edu",
                f"https://{university_name.lower().replace(' ', '-')}.edu"
            ]
            
            for url in direct_urls:
                try:
                    await self.page.goto(url, wait_until="domcontentloaded", timeout=10000)
                    await asyncio.sleep(2)
                    
                    title = await self.page.title()
                    if title and "error" not in title.lower() and "not found" not in title.lower():
                        search_results[f"{university_name} official website"] = [{
                            "title": title,
                            "url": url,
                            "snippet": f"Direct access to {university_name} official website"
                        }]
                        print(f"✅ Found direct website: {url}")
                        break
                        
                except Exception as e:
                    print(f"Direct access failed for {url}: {e}")
                    continue
                    
        except Exception as e:
            print(f"Educational database search failed: {e}")
            for query in search_queries:
                search_results[query] = []
        
        return search_results

    async def _try_wikipedia_academic_search(self, university_name: str, search_queries: List[str]) -> Dict[str, Any]:
        """Try searching Wikipedia and academic sources for university information"""
        search_results = {}
        
        try:
            print("Attempting Wikipedia and academic source search...")
            
            # Try Wikipedia first
            try:
                wiki_url = f"https://en.wikipedia.org/wiki/{university_name.replace(' ', '_')}"
                await self.page.goto(wiki_url, wait_until="domcontentloaded", timeout=10000)
                await asyncio.sleep(2)
                
                # Check if page exists
                title = await self.page.title()
                if title and "does not exist" not in title.lower():
                    # Extract external links from Wikipedia
                    external_links = await self.page.query_selector_all('a[href^="http"]')
                    query_results = []
                    
                    for link in external_links[:15]:
                        try:
                            href = await link.get_attribute('href')
                            title_text = await link.inner_text()
                            
                            if href and len(title_text.strip()) > 5:
                                # Filter for university-related links
                                if any(keyword in href.lower() for keyword in ['university', 'college', 'edu', 'academic', 'research']):
                                    query_results.append({
                                        "title": title_text.strip(),
                                        "url": href,
                                        "snippet": f"External link from Wikipedia article about {university_name}"
                                    })
                                    print(f"  - Found: {title_text.strip()}")
                                    print(f"    URL: {href}")
                        except Exception as e:
                            continue
                    
                    if query_results:
                        search_results[f"{university_name} Wikipedia external links"] = query_results
                        
            except Exception as e:
                print(f"Wikipedia search failed: {e}")
            
            # Try academic databases
            academic_sites = [
                "https://scholar.google.com",
                "https://www.researchgate.net",
                "https://www.academia.edu",
                "https://www.linkedin.com/school"
            ]
            
            for site in academic_sites:
                try:
                    print(f"Searching academic site: {site}")
                    await self.page.goto(site, wait_until="domcontentloaded", timeout=10000)
                    await asyncio.sleep(2)
                    
                    # Look for search functionality
                    search_selectors = [
                        'input[type="search"]',
                        'input[name*="q"]',
                        'input[placeholder*="search"]',
                        'input[placeholder*="Search"]',
                        '.search input',
                        '#search input'
                    ]
                    
                    search_box = None
                    for selector in search_selectors:
                        try:
                            search_box = await self.page.query_selector(selector)
                            if search_box:
                                break
                        except:
                            continue
                    
                    if search_box:
                        await search_box.fill(university_name)
                        await asyncio.sleep(1)
                        await search_box.press('Enter')
                        await self.page.wait_for_load_state("domcontentloaded", timeout=10000)
                        await asyncio.sleep(2)
                        
                        # Extract results
                        results = await self.page.query_selector_all('a[href*="http"]')
                        query_results = []
                        
                        for result in results[:8]:
                            try:
                                href = await result.get_attribute('href')
                                title = await result.inner_text()
                                
                                if href and href.startswith('http') and len(title.strip()) > 5:
                                    query_results.append({
                                        "title": title.strip(),
                                        "url": href,
                                        "snippet": f"Found on {site}"
                                    })
                                    print(f"  - Found: {title.strip()}")
                                    print(f"    URL: {href}")
                            except Exception as e:
                                continue
                        
                        if query_results:
                            search_results[f"{university_name} on {site}"] = query_results
                    
                except Exception as e:
                    print(f"Error searching {site}: {e}")
                    continue
                    
        except Exception as e:
            print(f"Wikipedia and academic search failed: {e}")
            for query in search_queries:
                search_results[query] = []
        
        return search_results

    async def scrape_webpage_content(self, url: str) -> Dict[str, Any]:
        """Scrape content from a specific webpage"""
        try:
            # Set a shorter timeout and handle different load states
            await self.page.goto(url, wait_until="domcontentloaded", timeout=10000)  # Reduced timeout
            
            # Check if page loaded successfully
            title = await self.page.title()
            if not title or title.lower() in ['error', 'not found', '404', 'forbidden', 'access denied']:
                return {
                    "url": url,
                    "error": f"Page not accessible: {title}",
                    "scraped_at": datetime.now().isoformat()
                }
            
            # Get main content with more comprehensive extraction
            content = await self.page.evaluate("""
                () => {
                    // Remove script and style elements
                    const scripts = document.querySelectorAll('script, style, nav, footer, header, .ad, .advertisement, .cookie-banner, .popup');
                    scripts.forEach(el => el.remove());
                    
                    // Get main content - try multiple selectors
                    const mainSelectors = [
                        'main', '#main', '.main', '.content', '#content', '.page-content',
                        '.article', '.post', '.entry', '.body', '.text', '.description'
                    ];
                    
                    let main = null;
                    for (const selector of mainSelectors) {
                        main = document.querySelector(selector);
                        if (main && main.innerText.length > 100) break;
                    }
                    
                    if (!main) {
                        // Fallback to body if no main content found
                        main = document.body;
                    }
                    
                    // Extract all text content
                    let text = main.innerText;
                    
                    // Also extract structured data if available
                    const structuredData = [];
                    const metaTags = document.querySelectorAll('meta[name*="description"], meta[property*="description"]');
                    metaTags.forEach(tag => {
                        if (tag.content) structuredData.push(tag.content);
                    });
                    
                    // Extract lists and tables
                    const lists = Array.from(document.querySelectorAll('ul, ol, dl'));
                    lists.forEach(list => {
                        const items = Array.from(list.querySelectorAll('li, dt, dd'));
                        items.forEach(item => {
                            if (item.innerText.trim().length > 10) {
                                structuredData.push(item.innerText.trim());
                            }
                        });
                    });
                    
                    // Extract table data
                    const tables = Array.from(document.querySelectorAll('table'));
                    tables.forEach(table => {
                        const rows = Array.from(table.querySelectorAll('tr'));
                        rows.forEach(row => {
                            const cells = Array.from(row.querySelectorAll('td, th'));
                            const rowText = cells.map(cell => cell.innerText.trim()).join(' | ');
                            if (rowText.length > 10) {
                                structuredData.push(rowText);
                            }
                        });
                    });
                    
                    // Combine all content
                    const allContent = [text, ...structuredData].join('\\n\\n');
                    
                    return allContent;
                }
            """)
            
            # Check if content is meaningful
            if not content or len(content.strip()) < 50:
                return {
                    "url": url,
                    "error": "Page has insufficient content",
                    "scraped_at": datetime.now().isoformat()
                }
            
            # Extract links
            links = await self.page.evaluate("""
                () => {
                    const links = Array.from(document.querySelectorAll('a[href]'));
                    return links.map(link => ({
                        text: link.innerText,
                        href: link.href
                    })).slice(0, 20); // Limit to first 20 links
                }
            """)
            
            return {
                "url": url,
                "title": title,
                "content": content,
                "links": links,
                "scraped_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            error_msg = str(e)
            
            # Handle specific error types
            if "net::ERR_ABORTED" in error_msg:
                error_msg = "Page access blocked or resource not available"
            elif "net::ERR_HTTP2_PROTOCOL_ERROR" in error_msg:
                error_msg = "HTTP protocol error - site may be blocking access"
            elif "net::ERR_CONNECTION_TIMED_OUT" in error_msg:
                error_msg = "Connection timed out"
            elif "net::ERR_NAME_NOT_RESOLVED" in error_msg:
                error_msg = "Domain not found"
            elif "net::ERR_SSL_PROTOCOL_ERROR" in error_msg:
                error_msg = "SSL/TLS error"
            
            return {
                "url": url,
                "error": error_msg,
                "scraped_at": datetime.now().isoformat()
            }

    async def analyze_with_llm(self, university_name: str, scraped_content: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze scraped content with LLM using two-stage approach"""
        
        # Prepare content for LLM with optimized chunking system
        all_content_chunks = []
        source_urls = []
        
        # Process content in chunks to avoid token limits
        for item in scraped_content:
            if "content" in item and not item.get("error"):
                content = item['content']
                source_urls.append(item['url'])
        
                # Filter content for relevance before chunking
                relevant_keywords = [
                    'university', 'student', 'faculty', 'program', 'school', 'college',
                    'admission', 'tuition', 'cost', 'ranking', 'research', 'academic',
                    'degree', 'major', 'graduate', 'undergraduate', 'campus', 'facility',
                    'financial', 'aid', 'scholarship', 'alumni', 'career', 'international',
                    'contact', 'email', 'phone', 'address'
                ]
                
                # Check if content contains relevant keywords
                content_lower = content.lower()
                relevance_score = sum(1 for keyword in relevant_keywords if keyword in content_lower)
                
                # Only process content with sufficient relevance (reduced threshold for limited content)
                min_relevance = 1 if len(scraped_content) < 5 else 2  # Lower threshold if we have few pages
                if relevance_score >= min_relevance:
                    # Split content into larger chunks to reduce empty responses
                    chunk_size = 1200  # Increased chunk size
                    chunks = [content[i:i+chunk_size] for i in range(0, len(content), chunk_size)]
                    
                    for i, chunk in enumerate(chunks):
                        chunk_data = {
                            "url": item['url'],
                            "title": item.get('title', 'N/A'),
                            "content": chunk,
                            "chunk_index": i,
                            "total_chunks": len(chunks),
                            "relevance_score": relevance_score
                        }
                        all_content_chunks.append(chunk_data)
        
        # If we have very few chunks, be more lenient
        if len(all_content_chunks) < 5:
            print(f"⚠️  Limited content available ({len(all_content_chunks)} chunks). Using all available content.")
            # Use all chunks we have
        else:
            # Limit total chunks to avoid too many API calls
            if len(all_content_chunks) > 20:
                # Sort by relevance and take top chunks
                all_content_chunks.sort(key=lambda x: x['relevance_score'], reverse=True)
                all_content_chunks = all_content_chunks[:20]
        
        print(f"📝 Processing {len(all_content_chunks)} content chunks for LLM analysis...")
        
        # Check if we have enough content to proceed
        if len(all_content_chunks) == 0:
            print("❌ No usable content found. Falling back to knowledge-based extraction...")
            # Return a basic structure with minimal data
            return {
                "raw_response": "No scraped content available",
                "structured_data": {
                    "name": university_name,
                    "website": f"https://www.{university_name.lower().replace(' ', '').replace(',', '').replace('.', '')}.edu",
                    "country": "United States",  # Default assumption
                    "city": "Unknown",
                    "state": "Unknown",
                    "phone": "Unknown",
                    "email": f"info@{university_name.lower().replace(' ', '').replace(',', '').replace('.', '')}.edu",
                    "confidence_score": 0.1,
                    "source_urls": []
                },
                "confidence_score": 0.1,
                "processing_time": 0.0,
                "source_urls": [],
                "batches_processed": 0,
                "stage_2_completed": False
            }
        
        # Process chunks in larger batches to reduce API calls
        batch_size = 8  # Increased batch size
        all_results = []
        
        for i in range(0, len(all_content_chunks), batch_size):
            batch = all_content_chunks[i:i+batch_size]
            
            # Prepare content for this batch
            content_text = ""
            for chunk_data in batch:
                content_text += f"\n\nSource: {chunk_data['url']} (Chunk {chunk_data['chunk_index']+1}/{chunk_data['total_chunks']})\nTitle: {chunk_data['title']}\nContent: {chunk_data['content']}\n"
            
            # Create prompt for this batch
            prompt = f"""
Extract university data for {university_name} from this content batch. You MUST return a complete JSON object that matches the exact schema below.

{content_text}

You MUST return data in this EXACT JSON format with ALL fields filled:
{json.dumps(self.university_data_schema, indent=2)}

CRITICAL REQUIREMENTS:
1. You MUST return the COMPLETE JSON object with ALL fields from the schema above
2. Do NOT add any fields that are not in the schema
3. Do NOT remove any fields from the schema
4. Fill EVERY field - if you don't find information, use your knowledge of {university_name}
5. NEVER return null values - always provide some information
6. For ARRAY fields, provide MULTIPLE items (at least 5-10 items per array)

**CONTACT INFORMATION (VERY IMPORTANT):**
- Extract email addresses from the content (look for @ symbols, contact forms, etc.)
- Extract phone numbers (look for patterns like (123) 456-7890, +1-234-567-8900, etc.)
- Common email patterns: admissions@university.edu, info@university.edu, contact@university.edu
- If no specific email found, use general format: info@{university_name.lower().replace(' ', '').replace(',', '').replace('.', '')}.edu
- For phone numbers, look for main switchboard, admissions office, international office numbers

**ARRAY FIELDS - MUST PROVIDE MULTIPLE ITEMS:**

**PROGRAMS (at least 10 programs):**
- Include undergraduate and graduate programs
- Different fields: Engineering, Business, Arts, Sciences, Medicine, Law, Education
- Examples: Computer Science, Mechanical Engineering, Business Administration, Psychology, Biology, Medicine, Law, Education, etc.
- Fill ALL program details: name, level, field, department, duration, tuition, description, requirements, career outcomes, etc.
- Focus on AVAILABLE programs - set available: true for all programs
- Start dates not required - focus on program availability and offerings

**SUBJECT RANKINGS (VERY IMPORTANT):**
- Fill ALL subject rankings: engineering, business, computer_science, medicine, law, arts, sciences
- Use specific ranking numbers (1-50 range for top universities)
- If you don't know exact rankings, use typical rankings for {university_name}

**FINANCIAL AID (VERY IMPORTANT):**
- Fill ALL financial aid fields with specific details
- Include actual scholarship names, loan options, grant programs
- Provide specific costs and amounts

**INTERNATIONAL STUDENTS (VERY IMPORTANT):**
- Fill ALL international student fields
- Include English requirements, visa support, cultural programs
- Provide specific services and requirements

**ALUMNI (VERY IMPORTANT):**
- Fill ALL alumni fields
- Include network size, notable alumni names, association details

**EXTRACTION RULES:**
- Convert text numbers to actual numbers (e.g., "5%" → 0.05, "$50,000" → 50000)
- For rankings, extract the actual number (e.g., "ranked #3" → 3)
- For costs, extract the dollar amount without commas (e.g., "$45,000" → 45000)
- For percentages, convert to decimal (e.g., "23%" → 0.23)
- For arrays, provide MULTIPLE items (5-10 items minimum)
- For objects, fill all nested fields
- Use your knowledge of {university_name} to fill any missing information
- **SPECIFICALLY LOOK FOR EMAIL ADDRESSES AND PHONE NUMBERS in the content**

Return ONLY the complete JSON object matching the schema exactly with COMPREHENSIVE arrays.
"""

        try:
            start_time = time.time()
            
            response = await self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a university data extraction expert. Your job is to extract EVERY possible detail, number, statistic, and fact from the provided content. Fill every field with information if it exists. Be extremely thorough and comprehensive. Return only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=3000
            )
            
            processing_time = time.time() - start_time
            
            # Parse LLM response
            llm_response = response.choices[0].message.content.strip()
            
            # Check if response is empty or invalid
            if not llm_response or llm_response == "":
                print(f"Warning: Empty LLM response for batch {i // batch_size}")
                all_results.append({
                    "raw_response": "",
                    "structured_data": None,
                    "processing_time": processing_time,
                    "error": "Empty response from LLM",
                    "batch_index": i // batch_size
                })
            else:
                # Try to extract JSON from response
                try:
                    # Remove any markdown formatting
                    if llm_response.startswith("```json"):
                        llm_response = llm_response[7:]
                    if llm_response.endswith("```"):
                        llm_response = llm_response[:-3]
                    
                    # Try to find JSON in the response
                    json_start = llm_response.find('{')
                    json_end = llm_response.rfind('}') + 1
                    
                    if json_start != -1 and json_end > json_start:
                        json_content = llm_response[json_start:json_end]
                        structured_data = json.loads(json_content)
                    else:
                        # If no JSON found, try parsing the entire response
                        structured_data = json.loads(llm_response)
                    
                    all_results.append({
                        "raw_response": llm_response,
                        "structured_data": structured_data,
                        "processing_time": processing_time,
                        "batch_index": i // batch_size
                    })
                    
                except json.JSONDecodeError as e:
                    print(f"Error parsing LLM response as JSON for batch {i // batch_size}: {e}")
                    print(f"Response preview: {llm_response[:200]}...")
                    all_results.append({
                        "raw_response": llm_response,
                        "structured_data": None,
                        "processing_time": processing_time,
                        "error": f"JSON parsing error: {e}",
                        "batch_index": i // batch_size
                    })
                
        except Exception as e:
            print(f"Error calling LLM API for batch {i // batch_size}: {e}")
            all_results.append({
                "raw_response": None,
                "structured_data": None,
                "processing_time": 0.0,
                "error": str(e),
                "batch_index": i // batch_size
            })
        
        # Merge results from all batches
        merged_data = self._merge_batch_results(all_results)
        
        # STAGE 2: Fill missing fields with additional LLM pass
        print("Stage 2: Filling missing fields with additional LLM analysis...")
        filled_data = await self._fill_missing_fields(university_name, merged_data, source_urls)
        
        # Calculate confidence score
        confidence_score = self._calculate_confidence_score(filled_data)
        
        return {
            "raw_response": f"Processed {len(all_results)} batches + Stage 2 completion",
            "structured_data": filled_data,
            "confidence_score": confidence_score,
            "processing_time": sum(r.get("processing_time", 0) for r in all_results),
            "source_urls": source_urls,
            "batches_processed": len(all_results),
            "stage_2_completed": True
        }

    async def _fill_missing_fields(self, university_name: str, initial_data: Dict[str, Any], source_urls: List[str]) -> Dict[str, Any]:
        """Stage 2: Fill missing fields with focused LLM analysis"""
        
        # Identify missing or empty fields more thoroughly
        missing_fields = []
        
        def check_field(field_path, value):
            if value is None or value == "" or value == "Not Available" or value == "N/A":
                missing_fields.append(field_path)
            elif isinstance(value, dict):
                # Check nested objects
                for subfield, subvalue in value.items():
                    subfield_path = f"{field_path}.{subfield}"
                    check_field(subfield_path, subvalue)
            elif isinstance(value, list):
                # Check if list is empty or contains null values
                if len(value) == 0:
                    missing_fields.append(field_path)
                else:
                    # Check each item in the list
                    for i, item in enumerate(value):
                        if isinstance(item, dict):
                            for subfield, subvalue in item.items():
                                subfield_path = f"{field_path}[{i}].{subfield}"
                                check_field(subfield_path, subvalue)
                        elif item is None or item == "" or item == "Not Available":
                            missing_fields.append(f"{field_path}[{i}]")
        
        # Check all fields in the data
        for field, value in initial_data.items():
            check_field(field, value)
        
        if not missing_fields:
            print("No missing fields to fill!")
            return initial_data
        
        print(f"Filling {len(missing_fields)} missing fields: {missing_fields[:15]}...")
        
        # Create focused prompt for missing fields
        missing_fields_text = ", ".join(missing_fields[:25])  # Increased limit for prompt
        
        prompt = f"""
You are a university data expert. For {university_name}, you MUST return a COMPLETE JSON object with ALL fields filled.

CURRENT DATA (incomplete):
{json.dumps(initial_data, indent=2)}

MISSING FIELDS DETECTED: {missing_fields_text}

You MUST return the COMPLETE university data schema with ALL fields filled:

{json.dumps(self.university_data_schema, indent=2)}

CRITICAL INSTRUCTIONS:
1. Return the COMPLETE JSON object matching the schema exactly
2. Fill EVERY single field - no null values allowed
3. Use your comprehensive knowledge of {university_name} to provide accurate information
4. For ARRAY fields, provide MULTIPLE items (5-10 items minimum):

   **PROGRAMS (at least 10 programs):**
   - Computer Science, Mechanical Engineering, Electrical Engineering, Civil Engineering
   - Business Administration, Economics, Finance, Marketing
   - Psychology, Biology, Chemistry, Physics, Mathematics
   - Medicine, Law, Education, Arts, Humanities
   - Fill ALL program details for each
   - Focus on AVAILABLE programs - set available: true for all programs
   - Start dates not required - focus on program availability

5. For subject rankings, provide specific ranking numbers (1-50 range for top universities)
6. For financial aid, provide specific details:
   - List actual scholarship names (e.g., "Stanford Knight-Hennessy Scholars", "Stanford Financial Aid")
   - Specify loan options (e.g., "Federal Direct Loans", "Private Student Loans")
   - Include specific grant programs
7. For international students, provide specific details:
   - English requirements (e.g., "TOEFL 100+", "IELTS 7.0+")
   - Visa support services (e.g., "International Student Office", "Visa Advising")
   - Cultural programs (e.g., "International Student Association", "Cultural Events")
8. For alumni, provide specific details:
   - Alumni network size (e.g., "200,000+ alumni worldwide")
   - Notable alumni names (e.g., "Elon Musk", "Larry Page", "Sergey Brin")
   - Alumni association details
9. For any field you're unsure about, make an educated guess based on typical university standards
10. NEVER return null values - always provide some information
11. Be specific and detailed in your responses
12. If a field should be an array, provide MULTIPLE items (5-10 minimum)
13. If a field should be a number, provide a realistic number
14. If a field should be a boolean, provide true/false based on typical university offerings

Return the COMPLETE JSON object with ALL fields filled and COMPREHENSIVE arrays. Do not leave any null values.
"""

        try:
            response = await self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a university data expert. Fill missing fields with accurate information based on your knowledge of universities."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=4000
            )
            
            llm_response = response.choices[0].message.content.strip()
            
            # Try to extract JSON from response
            try:
                if llm_response.startswith("```json"):
                    llm_response = llm_response[7:]
                if llm_response.endswith("```"):
                    llm_response = llm_response[:-3]
                
                filled_data = json.loads(llm_response)
                print(f"✅ Stage 2 completed - filled missing fields")
                return filled_data
                
            except json.JSONDecodeError as e:
                print(f"Error parsing Stage 2 LLM response: {e}")
                return initial_data
                
        except Exception as e:
            print(f"Error in Stage 2 LLM call: {e}")
            return initial_data

    def _merge_batch_results(self, batch_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Merge results from multiple batches into a single comprehensive dataset"""
        merged_data = {}
        
        # Check if we have any valid structured data
        valid_batches = [batch for batch in batch_results if batch.get("structured_data")]
        
        if not valid_batches:
            print("⚠️  No valid structured data found in any batch. Using fallback data.")
            return {
                "name": "Unknown University",
                "website": "https://example.edu",
                "country": "Unknown",
                "city": "Unknown",
                "state": "Unknown",
                "phone": "Unknown",
                "email": "info@example.edu",
                "confidence_score": 0.0,
                "source_urls": []
            }
        
        for batch_result in valid_batches:
            batch_data = batch_result["structured_data"]
            
            # Merge simple fields (take first non-null value)
            for field, value in batch_data.items():
                if field not in merged_data or merged_data[field] is None or merged_data[field] == "":
                    if value is not None and value != "" and value != "Not Available":
                        merged_data[field] = value
                
            # Merge arrays (combine unique items)
            array_fields = ["programs", "source_urls"]
            for field in array_fields:
                if field in batch_data and batch_data[field]:
                    if field not in merged_data:
                        merged_data[field] = []
                    
                    # Add unique items
                    existing_items = {str(item) for item in merged_data[field]}
                    for item in batch_data[field]:
                        if str(item) not in existing_items:
                            merged_data[field].append(item)
            
            # Merge nested objects (recursively merge)
            object_fields = ["subject_rankings", "student_life", "financial_aid", 
                           "international_students", "alumni"]
            
            for field in object_fields:
                if field in batch_data and batch_data[field]:
                    if field not in merged_data:
                        merged_data[field] = {}
                    
                    # Recursively merge nested objects
                    merged_data[field] = self._merge_nested_objects(merged_data[field], batch_data[field])
        
        return merged_data

    def _merge_nested_objects(self, existing: Dict[str, Any], new: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively merge nested objects, taking first non-null values"""
        result = existing.copy()
        
        for key, value in new.items():
            if key not in result or result[key] is None or result[key] == "" or result[key] == "Not Available":
                if value is not None and value != "" and value != "Not Available":
                    result[key] = value
            elif isinstance(value, dict) and isinstance(result[key], dict):
                # Recursively merge nested dictionaries
                result[key] = self._merge_nested_objects(result[key], value)
            elif isinstance(value, list) and isinstance(result[key], list):
                # Merge arrays (combine unique items)
                existing_items = {str(item) for item in result[key]}
                for item in value:
                    if str(item) not in existing_items:
                        result[key].append(item)
        
        return result

    def _calculate_confidence_score(self, data: Dict[str, Any]) -> float:
        """Calculate confidence score based on data completeness and quality"""
        if not data:
            return 0.0
        
        # Define important fields with weights
        field_weights = {
            # Basic Info (weight: 0.15)
            "name": 0.05,
            "website": 0.05,
            "country": 0.02,
            "city": 0.02,
            "state": 0.01,
            
            # Demographics (weight: 0.20)
            "student_population": 0.08,
            "undergraduate_population": 0.06,
            "graduate_population": 0.06,
            
            # SUBJECT RANKINGS (weight: 0.20) - ENHANCED
            "subject_rankings": 0.20,
            
            # FINANCIAL AID (weight: 0.20) - ENHANCED
            "tuition_domestic": 0.06,
            "tuition_international": 0.04,
            "total_cost_of_attendance": 0.05,
            "financial_aid_available": 0.03,
            "scholarships_available": 0.02,
            
            # INTERNATIONAL STUDENTS (weight: 0.10) - ENHANCED
            "international_students_percentage": 0.05,
            "international_students": 0.05,
            
            # Academic (weight: 0.10)
            "acceptance_rate": 0.03,
            "description": 0.02,
            "programs": 0.03,
            "schools_colleges": 0.02,
            
            # Rankings (weight: 0.05)
            "world_ranking": 0.02,
            "national_ranking": 0.03,
            
            # Additional Details (weight: 0.05)
            "facilities": 0.02,
            "student_life": 0.01,
            "financial_aid": 0.01,
            "alumni": 0.01
        }
        
        total_score = 0.0
        max_possible_score = sum(field_weights.values())
        
        for field, weight in field_weights.items():
            value = data.get(field)
            
            if value is not None and value != "":
                if isinstance(value, (list, dict)):
                    # For arrays and objects, check if they have content
                    if len(value) > 0:
                        total_score += weight
                else:
                    # For simple values, check if they're not empty
                    if str(value).strip() != "":
                        total_score += weight
        
        # Bonus for having source URLs
        if data.get("source_urls") and len(data["source_urls"]) > 0:
            total_score += 0.05
        
        # Bonus for comprehensive data
        filled_fields = sum(1 for field in field_weights.keys() if data.get(field) and data[field] != "" and data[field] is not None)
        total_fields = len(field_weights)
        completeness_bonus = (filled_fields / total_fields) * 0.1
        
        total_score += completeness_bonus
        
        return min(total_score / max_possible_score, 1.0)

    async def collect_university_data(self, university_name: str) -> Dict[str, Any]:
        """Main method to collect university data using browser and LLM"""
        
        # Create a new browser instance for each university to avoid conflicts
        browser = None
        page = None
        playwright = None
        
        try:
            # Initialize browser for this specific university
            playwright = await async_playwright().start()
            browser = await playwright.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-accelerated-2d-canvas',
                    '--no-first-run',
                    '--no-zygote',
                    '--disable-gpu',
                    '--disable-background-timer-throttling',
                    '--disable-backgrounding-occluded-windows',
                    '--disable-renderer-backgrounding',
                    '--disable-features=TranslateUI',
                    '--disable-ipc-flooding-protection',
                    '--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                ]
            )
            page = await browser.new_page()
            
            # Set user agent and other headers to avoid detection
            await page.set_extra_http_headers({
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            })
            
            # Set viewport
            await page.set_viewport_size({"width": 1920, "height": 1080})
            
            # Temporarily set the page for this operation
            original_page = self.page
            self.page = page
            
            # Search for university information
            print(f"Searching for information about {university_name}...")
            search_results = await self.search_university_info(university_name)
            
            # Extract URLs from search results
            urls_to_scrape = []
            for query, results in search_results.items():
                for result in results:
                    if result.get("url") and "http" in result["url"]:
                        url = result["url"]
                        
                        # Filter out problematic URLs
                        skip_extensions = ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.zip', '.rar']
                        skip_domains = ['usnews.com', 'timeshighereducation.com', 'topuniversities.com']  # Sites that often block scraping
                        
                        # Check if URL should be skipped
                        should_skip = False
                        
                        # Skip PDF and other document files
                        for ext in skip_extensions:
                            if url.lower().endswith(ext):
                                should_skip = True
                                print(f"⏭️  Skipping document file: {url}")
                                break
                        
                        # Skip problematic domains
                        for domain in skip_domains:
                            if domain in url.lower():
                                should_skip = True
                                print(f"⏭️  Skipping blocked domain: {url}")
                                break
                        
                        # Skip URLs that are too long (likely API endpoints or complex queries)
                        if len(url) > 200:
                            should_skip = True
                            print(f"⏭️  Skipping long URL: {url[:100]}...")
                        
                        if not should_skip:
                            urls_to_scrape.append(url)
            
            # Remove duplicates and limit to top 20 URLs (reduced to avoid timeouts)
            urls_to_scrape = list(set(urls_to_scrape))[:20]
            print(f"📋 Selected {len(urls_to_scrape)} URLs for scraping (filtered from {sum(len(results) for results in search_results.values())} total results)")
            
            # Scrape content from URLs
            print(f"Scraping content from {len(urls_to_scrape)} URLs...")
            scraped_content = []
            successful_scrapes = 0
            failed_scrapes = 0
            
            for i, url in enumerate(urls_to_scrape, 1):
                try:
                    print(f"  [{i}/{len(urls_to_scrape)}] Scraping: {url}")
                    content = await self.scrape_webpage_content(url)
                    if content and not content.get("error"):
                        scraped_content.append(content)
                        successful_scrapes += 1
                        print(f"    ✅ Success")
                    else:
                        failed_scrapes += 1
                        print(f"    ❌ Failed: {content.get('error', 'Unknown error')}")
                    await asyncio.sleep(1)  # Increased delay to be more respectful
                except Exception as e:
                    failed_scrapes += 1
                    print(f"    ❌ Error scraping {url}: {e}")
                    continue
            
            print(f"📊 Scraping completed: {successful_scrapes} successful, {failed_scrapes} failed")
            
            # Check if we have enough content to proceed
            if len(scraped_content) < 3:
                print("⚠️  Warning: Very few pages scraped successfully. Proceeding with limited data...")
            
            # Analyze with LLM
            print("Analyzing content with LLM...")
            llm_analysis = await self.analyze_with_llm(university_name, scraped_content)
            
            # Save results to UniversityDataCollectionResult table
            print("Saving results to UniversityDataCollectionResult table...")
            extracted_data = llm_analysis.get("structured_data", {})
            
            # Prepare data for the new table
            result_data = {
                'total_universities': 1,
                'successful_collections': 1,
                'failed_collections': 0,
                'generated_at': datetime.now(),
                'script_version': '1.0.0',
                'success': True,
                'data_collection_id': None,  # No longer needed since we removed the collection table
                'name': extracted_data.get('name'),
                'website': extracted_data.get('website'),
                'country': extracted_data.get('country'),
                'city': extracted_data.get('city'),
                'state': extracted_data.get('state'),
                'phone': extracted_data.get('phone'),
                'email': extracted_data.get('email'),
                'founded_year': extracted_data.get('founded_year'),
                'type': extracted_data.get('type'),
                'student_population': extracted_data.get('student_population'),
                'undergraduate_population': extracted_data.get('undergraduate_population'),
                'graduate_population': extracted_data.get('graduate_population'),
                'international_students_percentage': extracted_data.get('international_students_percentage'),
                'faculty_count': extracted_data.get('faculty_count'),
                'student_faculty_ratio': extracted_data.get('student_faculty_ratio'),
                'acceptance_rate': extracted_data.get('acceptance_rate'),
                'tuition_domestic': extracted_data.get('tuition_domestic'),
                'tuition_international': extracted_data.get('tuition_international'),
                'room_and_board': extracted_data.get('room_and_board'),
                'total_cost_of_attendance': extracted_data.get('total_cost_of_attendance'),
                'financial_aid_available': extracted_data.get('financial_aid_available'),
                'average_financial_aid_package': extracted_data.get('average_financial_aid_package'),
                'scholarships_available': extracted_data.get('scholarships_available'),
                'world_ranking': extracted_data.get('world_ranking'),
                'national_ranking': extracted_data.get('national_ranking'),
                'regional_ranking': extracted_data.get('regional_ranking'),
                'subject_rankings': json.dumps(extracted_data.get('subject_rankings', {})) if extracted_data.get('subject_rankings') else None,
                'description': extracted_data.get('description'),
                'mission_statement': extracted_data.get('mission_statement'),
                'vision_statement': extracted_data.get('vision_statement'),
                'campus_size': extracted_data.get('campus_size'),
                'campus_type': extracted_data.get('campus_type'),
                'climate': extracted_data.get('climate'),
                'timezone': extracted_data.get('timezone'),
                'programs': json.dumps(extracted_data.get('programs', [])) if extracted_data.get('programs') else None,
                'student_life': json.dumps(extracted_data.get('student_life', {})) if extracted_data.get('student_life') else None,
                'financial_aid': json.dumps(extracted_data.get('financial_aid', {})) if extracted_data.get('financial_aid') else None,
                'international_students': json.dumps(extracted_data.get('international_students', {})) if extracted_data.get('international_students') else None,
                'alumni': json.dumps(extracted_data.get('alumni', {})) if extracted_data.get('alumni') else None,
                'confidence_score': llm_analysis.get("confidence_score", 0.0),
                'source_urls': json.dumps(llm_analysis.get("source_urls", [])) if llm_analysis.get("source_urls") else None,
                'last_updated': datetime.now().strftime('%Y-%m-%d')
            }
            
            # Create and save the result record
            result_record = UniversityDataCollectionResult(**result_data)
            self.db_session.add(result_record)
            self.db_session.commit()
            
            print(f"✅ Results saved to UniversityDataCollectionResult table with ID: {result_record.id}")
            print(f"Data collection completed for {university_name} with confidence score: {llm_analysis.get('confidence_score', 0.0)}")
            
            return {
                "success": True,
                "result_record_id": result_record.id,
                "extracted_data": llm_analysis.get("structured_data"),
                "confidence_score": llm_analysis.get("confidence_score", 0.0),
                "source_urls": llm_analysis.get("source_urls", [])
            }
            
        except Exception as e:
            print(f"Error collecting data for {university_name}: {e}")
            
            # Try to save a basic result even if scraping failed
            try:
                basic_data = {
                    'total_universities': 1,
                    'successful_collections': 0,
                    'failed_collections': 1,
                    'generated_at': datetime.now(),
                    'script_version': '1.0.0',
                    'success': False,
                    'data_collection_id': None,
                    'name': university_name,
                    'website': f"https://www.{university_name.lower().replace(' ', '').replace(',', '').replace('.', '')}.edu",
                    'country': "United States",  # Default assumption
                    'city': "Unknown",
                    'state': "Unknown",
                    'phone': "Unknown",
                    'email': f"info@{university_name.lower().replace(' ', '').replace(',', '').replace('.', '')}.edu",
                    'founded_year': None,
                    'type': "Unknown",
                    'student_population': None,
                    'undergraduate_population': None,
                    'graduate_population': None,
                    'international_students_percentage': None,
                    'faculty_count': None,
                    'student_faculty_ratio': None,
                    'acceptance_rate': None,
                    'tuition_domestic': None,
                    'tuition_international': None,
                    'room_and_board': None,
                    'total_cost_of_attendance': None,
                    'financial_aid_available': None,
                    'average_financial_aid_package': None,
                    'scholarships_available': None,
                    'world_ranking': None,
                    'national_ranking': None,
                    'regional_ranking': None,
                    'subject_rankings': None,
                    'description': f"Data collection failed for {university_name}",
                    'mission_statement': None,
                    'vision_statement': None,
                    'campus_size': None,
                    'campus_type': None,
                    'climate': None,
                    'timezone': None,
                    'programs': None,
                    'student_life': None,
                    'financial_aid': None,
                    'international_students': None,
                    'alumni': None,
                    'confidence_score': 0.0,
                    'source_urls': None,
                    'last_updated': datetime.now().strftime('%Y-%m-%d')
                }
                
                result_record = UniversityDataCollectionResult(**basic_data)
                self.db_session.add(result_record)
                self.db_session.commit()
                
                print(f"✅ Saved basic result for {university_name} with ID: {result_record.id}")
                
                return {
                    "success": False,
                    "error": str(e),
                    "result_record_id": result_record.id
                }
                
            except Exception as save_error:
                print(f"Failed to save basic result: {save_error}")
                return {
                    "success": False,
                    "error": str(e)
                }
        
        finally:
            # Restore original page and close the temporary browser
            self.page = original_page
            try:
                if browser:
                    await browser.close()
                if playwright:
                    await playwright.stop()
            except Exception as close_error:
                print(f"Warning: Error closing browser: {close_error}")

    async def collect_university_data_batch(self, university_names: List[str]) -> Dict[str, Any]:
        """Collect data for multiple universities and save in batch format"""
        
        print(f"Starting batch collection for {len(university_names)} universities...")
        
        results = []
        successful_collections = 0
        failed_collections = 0
        
        for university_name in university_names:
            print(f"\n{'='*60}")
            print(f"Processing: {university_name}")
            print(f"{'='*60}")
            
            try:
                # Collect data for this university
                result = await self.collect_university_data(university_name)
                
                if result.get("success"):
                    successful_collections += 1
                    results.append({
                        "success": True,
                        "result_record_id": result.get("result_record_id"),
                        "extracted_data": result.get("extracted_data"),
                        "confidence_score": result.get("confidence_score"),
                        "source_urls": result.get("source_urls")
                    })
                    print(f"✅ Successfully collected data for {university_name}")
                else:
                    failed_collections += 1
                    results.append({
                        "success": False,
                        "error": result.get("error")
                    })
                    print(f"❌ Failed to collect data for {university_name}: {result.get('error')}")
                    
            except Exception as e:
                failed_collections += 1
                results.append({
                    "success": False,
                    "error": str(e)
                })
                print(f"❌ Exception while collecting data for {university_name}: {e}")
                continue
        
        # Create batch result in the JSON format structure
        batch_result = {
            "metadata": {
                "total_universities": len(university_names),
                "successful_collections": successful_collections,
                "failed_collections": failed_collections,
                "generated_at": datetime.now().isoformat(),
                "script_version": "1.0.0"
            },
            "results": results
        }
        
        # Save batch result to database
        print(f"\nSaving batch results to database...")
        for result in results:
            if result.get("success") and result.get("extracted_data"):
                # Update the existing record with batch metadata
                if result.get("result_record_id"):
                    try:
                        existing_record = self.db_session.query(UniversityDataCollectionResult).filter_by(
                            id=result["result_record_id"]
                        ).first()
                        
                        if existing_record:
                            # Update with batch information
                            existing_record.total_universities = len(university_names)
                            existing_record.successful_collections = successful_collections
                            existing_record.failed_collections = failed_collections
                            existing_record.generated_at = datetime.now()
                            existing_record.script_version = "1.0.0"
                            self.db_session.commit()
                            print(f"✅ Updated batch metadata for record ID: {existing_record.id}")
                    except Exception as e:
                        print(f"❌ Error updating batch metadata: {e}")
        
        print(f"\n{'='*60}")
        print(f"BATCH COLLECTION COMPLETED")
        print(f"{'='*60}")
        print(f"Total universities: {len(university_names)}")
        print(f"Successful: {successful_collections}")
        print(f"Failed: {failed_collections}")
        print(f"Success rate: {(successful_collections/len(university_names)*100):.1f}%")
        
        return batch_result

    async def export_results_to_json(self, university_names: List[str] = None, output_file: str = None) -> str:
        """Export collected results to JSON file in the specified format"""
        
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"app/output/university_data_collection_{timestamp}.json"
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        # Query results from database
        query = self.db_session.query(UniversityDataCollectionResult)
        if university_names:
            query = query.filter(UniversityDataCollectionResult.name.in_(university_names))
        
        records = query.all()
        
        # Convert to JSON format
        results = []
        for record in records:
            result = {
                "success": True,
                "data_collection_id": record.data_collection_id,
                "extracted_data": {
                    "name": record.name,
                    "website": record.website,
                    "country": record.country,
                    "city": record.city,
                    "state": record.state,
                    "phone": record.phone,
                    "email": record.email,
                    "founded_year": record.founded_year,
                    "type": record.type,
                    "student_population": record.student_population,
                    "undergraduate_population": record.undergraduate_population,
                    "graduate_population": record.graduate_population,
                    "international_students_percentage": record.international_students_percentage,
                    "faculty_count": record.faculty_count,
                    "student_faculty_ratio": record.student_faculty_ratio,
                    "acceptance_rate": record.acceptance_rate,
                    "tuition_domestic": record.tuition_domestic,
                    "tuition_international": record.tuition_international,
                    "room_and_board": record.room_and_board,
                    "total_cost_of_attendance": record.total_cost_of_attendance,
                    "financial_aid_available": record.financial_aid_available,
                    "average_financial_aid_package": record.average_financial_aid_package,
                    "scholarships_available": record.scholarships_available,
                    "world_ranking": record.world_ranking,
                    "national_ranking": record.national_ranking,
                    "regional_ranking": record.regional_ranking,
                    "subject_rankings": json.loads(record.subject_rankings) if record.subject_rankings else {},
                    "description": record.description,
                    "mission_statement": record.mission_statement,
                    "vision_statement": record.vision_statement,
                    "campus_size": record.campus_size,
                    "campus_type": record.campus_type,
                    "climate": record.climate,
                    "timezone": record.timezone,
                    "programs": json.loads(record.programs) if record.programs else [],
                    "student_life": json.loads(record.student_life) if record.student_life else {},
                    "financial_aid": json.loads(record.financial_aid) if record.financial_aid else {},
                    "international_students": json.loads(record.international_students) if record.international_students else {},
                    "alumni": json.loads(record.alumni) if record.alumni else {},
                    "confidence_score": record.confidence_score,
                    "source_urls": json.loads(record.source_urls) if record.source_urls else [],
                    "last_updated": record.last_updated
                },
                "confidence_score": record.confidence_score,
                "source_urls": json.loads(record.source_urls) if record.source_urls else []
            }
            results.append(result)
        
        # Create the final JSON structure
        export_data = {
            "metadata": {
                "total_universities": len(records),
                "successful_collections": len([r for r in results if r["success"]]),
                "failed_collections": len([r for r in results if not r["success"]]),
                "generated_at": datetime.now().isoformat(),
                "script_version": "1.0.0"
            },
            "results": results
        }
        
        # Write to file
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"✅ Results exported to: {output_file}")
        return output_file

    async def _try_knowledge_based_fallback(self, university_name: str, search_queries: List[str]) -> Dict[str, Any]:
        """Fallback strategy using LLM knowledge when all web searches fail"""
        search_results = {}
        
        try:
            print("Attempting knowledge-based fallback search...")
            
            # Use LLM to generate comprehensive university information
            prompt = f"""
You are a university data expert. For {university_name}, please provide comprehensive information in JSON format including:

1. Official website URL (common patterns like .edu domains)
2. Contact information (email, phone)
3. Location details (city, state, country)
4. Basic statistics (student population, faculty count, etc.)
5. Academic programs and rankings
6. Financial information
7. International student services

Please provide this information in a structured format that can be used to create search results. Focus on providing accurate, well-known information about {university_name}.
"""
            
            response = await self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a university data expert. Provide comprehensive information about universities in JSON format."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=1500
            )
            
            llm_response = response.choices[0].message.content.strip()
            
            # Create mock search results based on LLM knowledge
            mock_results = []
            
            # Extract website from response
            if "www." in llm_response.lower() or ".edu" in llm_response.lower():
                # Try to extract website URL
                import re
                url_match = re.search(r'https?://[^\s]+', llm_response)
                if url_match:
                    website_url = url_match.group(0)
                    mock_results.append({
                        "title": f"{university_name} Official Website",
                        "url": website_url,
                        "snippet": f"Official website for {university_name} based on knowledge base"
                    })
            
            # Add common university website patterns
            common_domains = [
                f"https://www.{university_name.lower().replace(' ', '').replace('university', 'edu')}.edu",
                f"https://{university_name.lower().replace(' ', '').replace('university', 'edu')}.edu",
                f"https://www.{university_name.lower().replace(' ', '-')}.edu",
                f"https://{university_name.lower().replace(' ', '-')}.edu"
            ]
            
            for domain in common_domains:
                if domain not in [result.get('url', '') for result in mock_results]:
                    mock_results.append({
                        "title": f"{university_name} - Official Website",
                        "url": domain,
                        "snippet": f"Potential official website for {university_name}"
                    })
            
            # Add Wikipedia as a fallback
            wiki_url = f"https://en.wikipedia.org/wiki/{university_name.replace(' ', '_')}"
            mock_results.append({
                "title": f"{university_name} - Wikipedia",
                "url": wiki_url,
                "snippet": f"Wikipedia article about {university_name}"
            })
            
            # Add common university ranking sites
            ranking_sites = [
                f"https://www.usnews.com/best-colleges/search?school-name={university_name.replace(' ', '+')}",
                f"https://www.timeshighereducation.com/world-university-rankings/search?search={university_name.replace(' ', '+')}",
                f"https://www.topuniversities.com/university-rankings/search?search={university_name.replace(' ', '+')}"
            ]
            
            for site in ranking_sites:
                mock_results.append({
                    "title": f"{university_name} - Rankings",
                    "url": site,
                    "snippet": f"Ranking information for {university_name}"
                })
            
            if mock_results:
                search_results[f"{university_name} knowledge-based results"] = mock_results
                print(f"✅ Knowledge-based fallback found {len(mock_results)} results")
            
        except Exception as e:
            print(f"Knowledge-based fallback failed: {e}")
        
        return search_results

async def main():
    """Example usage of the UniversityDataScraper"""
    # You'll need to set up your database session and OpenAI API key
    db_session = next(get_db())
    
    scraper = UniversityDataScraper(
        openai_api_key="your-openai-api-key-here",
        db_session=db_session
    )
    
    # Example 1: Collect data for a single university
    print("Example 1: Single university collection")
    result = await scraper.collect_university_data("Stanford University")
    print(json.dumps(result, indent=2))
    
    # Example 2: Batch collection for multiple universities
    print("\nExample 2: Batch university collection")
    universities = [
        "Stanford University",
        "MIT",
        "Harvard University"
    ]
    
    batch_result = await scraper.collect_university_data_batch(universities)
    print(f"Batch collection completed: {batch_result['metadata']['successful_collections']} successful, {batch_result['metadata']['failed_collections']} failed")
    
    # Example 3: Export results to JSON file
    print("\nExample 3: Exporting results to JSON")
    output_file = await scraper.export_results_to_json()
    print(f"Results exported to: {output_file}")

if __name__ == "__main__":
    asyncio.run(main()) 