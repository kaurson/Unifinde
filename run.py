import asyncio
import json
import os
import re
import xml.etree.ElementTree as ET
from datetime import datetime
from urllib.parse import urljoin, urlparse
from app.tool.browser_tool_playwright import BrowserToolPlaywright

def save_to_json(data: dict, filename: str = None):
    """
    Save the collected data to a JSON file.
    
    Args:
        data: Dictionary containing the search results
        filename: Optional custom filename, defaults to timestamp-based name
    """
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"university_search_{timestamp}.json"
    
    # Ensure the filename has .json extension
    if not filename.endswith('.json'):
        filename += '.json'
    
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"💾 Data saved to: {filename}")
        return filename
    except Exception as e:
        print(f"❌ Error saving to JSON: {e}")
        return None

def extract_text_content(html_content: str) -> str:
    """Extract clean text content from HTML"""
    if not html_content:
        return ""
    
    # Remove HTML tags and decode entities
    import re
    from html import unescape
    
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', ' ', html_content)
    # Decode HTML entities
    text = unescape(text)
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

def safe_get_output(result, default=""):
    """Safely get output from a ToolResult object"""
    try:
        if hasattr(result, 'output') and result.output is not None:
            return result.output
        elif hasattr(result, 'error') and result.error is not None:
            return f"Error: {result.error}"
        else:
            return default
    except Exception as e:
        print(f"Warning: Could not extract output from result: {e}")
        return default

async def safe_browser_action(browser_tool, action, **kwargs):
    """Safely execute a browser action with error handling"""
    try:
        result = await browser_tool.execute(action=action, **kwargs)
        if hasattr(result, 'is_success') and result.is_success():
            return result
        else:
            print(f"Warning: Browser action '{action}' may have failed")
            return result
    except Exception as e:
        print(f"Error executing browser action '{action}': {e}")
        # Return a mock result to prevent crashes
        from app.tool.base import ToolResult
        return ToolResult(output=f"Error: {str(e)}", error=str(e))

async def get_page_content_simple(browser_tool):
    """Get page content using a simple approach that doesn't rely on extract_content"""
    try:
        # Get current state which includes page information
        state_result = await browser_tool.get_current_state()
        if state_result.is_success():
            state_data = json.loads(state_result.output)
            # Try to get page content directly from the page object
            if hasattr(browser_tool, 'page') and browser_tool.page:
                try:
                    content = await browser_tool.page.content()
                    return extract_text_content(content)
                except Exception as e:
                    print(f"Warning: Could not get page content directly: {e}")
                    return ""
        return ""
    except Exception as e:
        print(f"Error getting page content: {e}")
        return ""

async def get_sitemap_urls(browser_tool, base_url: str):
    """Retrieve and parse the university's sitemap to get all URLs"""
    print("🗺️  Retrieving university sitemap...")
    
    sitemap_urls = []
    common_sitemap_paths = [
        "/sitemap.xml",
        "/sitemap_index.xml",
        "/sitemap/sitemap.xml",
        "/robots.txt"
    ]
    
    # Try to find sitemap from robots.txt first
    try:
        robots_url = urljoin(base_url, "/robots.txt")
        await safe_browser_action(browser_tool, "go_to_url", url=robots_url)
        await safe_browser_action(browser_tool, "wait", seconds=2)
        
        robots_content = await get_page_content_simple(browser_tool)
        if robots_content:
            # Look for sitemap entries in robots.txt
            sitemap_lines = [line.strip() for line in robots_content.split('\n') if line.strip().lower().startswith('sitemap:')]
            for line in sitemap_lines:
                sitemap_url = line.split(':', 1)[1].strip()
                sitemap_urls.append(sitemap_url)
                print(f"📋 Found sitemap in robots.txt: {sitemap_url}")
    except Exception as e:
        print(f"Warning: Could not access robots.txt: {e}")
    
    # Try common sitemap paths
    for path in common_sitemap_paths:
        try:
            sitemap_url = urljoin(base_url, path)
            await safe_browser_action(browser_tool, "go_to_url", url=sitemap_url)
            await safe_browser_action(browser_tool, "wait", seconds=2)
            
            content = await get_page_content_simple(browser_tool)
            if content and ("<?xml" in content or "<urlset" in content or "<sitemapindex" in content):
                sitemap_urls.append(sitemap_url)
                print(f"📋 Found sitemap at: {sitemap_url}")
                break
        except Exception as e:
            print(f"Warning: Could not access {path}: {e}")
            continue
    
    return sitemap_urls

async def parse_sitemap_content(content: str, base_url: str):
    """Parse sitemap XML content and extract all URLs"""
    urls = []
    
    try:
        # Try to parse as XML
        root = ET.fromstring(content)
        
        # Handle sitemap index
        if 'sitemapindex' in root.tag:
            print("📋 Found sitemap index, extracting sitemap URLs...")
            for sitemap in root.findall('.//{*}sitemap/{*}loc'):
                sitemap_url = sitemap.text.strip()
                urls.append(sitemap_url)
                print(f"  📄 Sitemap: {sitemap_url}")
        
        # Handle URL set
        elif 'urlset' in root.tag:
            print("📋 Found URL set, extracting page URLs...")
            for url_elem in root.findall('.//{*}url/{*}loc'):
                page_url = url_elem.text.strip()
                urls.append(page_url)
                print(f"  📄 Page: {page_url}")
        
        # Also look for lastmod and priority if available
        for url_elem in root.findall('.//{*}url'):
            loc_elem = url_elem.find('{*}loc')
            if loc_elem is not None:
                page_url = loc_elem.text.strip()
                urls.append(page_url)
    
    except ET.ParseError as e:
        print(f"Warning: Could not parse sitemap XML: {e}")
        # Fallback: try to extract URLs using regex
        url_pattern = r'<loc>(.*?)</loc>'
        urls = re.findall(url_pattern, content)
        print(f"📋 Extracted {len(urls)} URLs using regex fallback")
    
    # Filter URLs to only include the same domain
    base_domain = urlparse(base_url).netloc
    filtered_urls = []
    for url in urls:
        try:
            parsed_url = urlparse(url)
            if parsed_url.netloc == base_domain:
                filtered_urls.append(url)
        except Exception:
            continue
    
    return list(set(filtered_urls))  # Remove duplicates

async def get_all_sitemap_urls(browser_tool, base_url: str):
    """Get all URLs from sitemaps recursively"""
    all_urls = []
    sitemap_urls = await get_sitemap_urls(browser_tool, base_url)
    
    for sitemap_url in sitemap_urls:
        try:
            await safe_browser_action(browser_tool, "go_to_url", url=sitemap_url)
            await safe_browser_action(browser_tool, "wait", seconds=2)
            
            content = await get_page_content_simple(browser_tool)
            if content:
                urls = await parse_sitemap_content(content, base_url)
                all_urls.extend(urls)
        except Exception as e:
            print(f"Warning: Could not process sitemap {sitemap_url}: {e}")
            continue
    
    # If no sitemaps found, try to discover URLs by crawling the main site
    if not all_urls:
        print("📋 No sitemaps found, crawling main site for URLs...")
        all_urls = await crawl_site_for_urls(browser_tool, base_url)
    
    return list(set(all_urls))  # Remove duplicates

async def crawl_site_for_urls(browser_tool, base_url: str):
    """Crawl the main site to discover URLs when no sitemap is available"""
    urls = [base_url]
    discovered_urls = set()
    
    try:
        await safe_browser_action(browser_tool, "go_to_url", url=base_url)
        await safe_browser_action(browser_tool, "wait", seconds=3)
        
        content = await get_page_content_simple(browser_tool)
        if content:
            # Extract links from HTML content
            link_pattern = r'href=["\']([^"\']+)["\']'
            links = re.findall(link_pattern, content)
            
            base_domain = urlparse(base_url).netloc
            for link in links:
                try:
                    full_url = urljoin(base_url, link)
                    parsed_url = urlparse(full_url)
                    
                    # Only include URLs from the same domain
                    if parsed_url.netloc == base_domain:
                        discovered_urls.add(full_url)
                except Exception:
                    continue
            
            urls.extend(list(discovered_urls))
            print(f"📋 Discovered {len(discovered_urls)} URLs by crawling")
    
    except Exception as e:
        print(f"Warning: Error crawling site: {e}")
    
    return urls

def categorize_url(url: str):
    """Categorize a URL based on its path and content"""
    url_lower = url.lower()
    
    categories = {
        "academic_programs": ["academic", "program", "degree", "major", "course", "curriculum", "school", "college", "department"],
        "scholarships": ["financial", "aid", "scholarship", "grant", "tuition", "cost", "funding", "money"],
        "admission_requirements": ["admission", "apply", "requirement", "application", "deadline", "test", "score"],
        "international_students": ["international", "visa", "global", "overseas", "foreign", "study abroad"],
        "research_areas": ["research", "innovation", "discovery", "laboratory", "study", "investigation", "faculty"],
        "contact_info": ["contact", "about", "directory", "phone", "email", "address"],
        "campus_life": ["campus", "student", "life", "housing", "dining", "activities", "clubs"],
        "faculty": ["faculty", "professor", "staff", "directory", "people"],
        "news": ["news", "events", "announcement", "press", "media"],
        "library": ["library", "resources", "database", "catalog"]
    }
    
    for category, keywords in categories.items():
        if any(keyword in url_lower for keyword in keywords):
            return category
    
    return "general"

async def analyze_page_content(content: str, url: str):
    """Analyze page content and extract relevant information"""
    page_data = {
        "url": url,
        "category": categorize_url(url),
        "content_summary": "",
        "extracted_info": {}
    }
    
    if not content:
        return page_data
    
    # Extract content summary (first 500 characters)
    page_data["content_summary"] = content[:500] + "..." if len(content) > 500 else content
    
    # Extract specific information based on category
    category = page_data["category"]
    
    if category == "academic_programs":
        program_keywords = ["program", "degree", "major", "course", "curriculum", "school", "college"]
        programs_found = []
        for keyword in program_keywords:
            if keyword.lower() in content.lower():
                sentences = re.findall(r'[^.]*' + keyword + r'[^.]*\.', content, re.IGNORECASE)
                programs_found.extend(sentences[:2])
        page_data["extracted_info"]["programs"] = list(set(programs_found))[:5]
    
    elif category == "scholarships":
        scholarship_keywords = ["scholarship", "financial aid", "grant", "tuition", "cost", "funding"]
        scholarships_found = []
        for keyword in scholarship_keywords:
            if keyword.lower() in content.lower():
                sentences = re.findall(r'[^.]*' + keyword + r'[^.]*\.', content, re.IGNORECASE)
                scholarships_found.extend(sentences[:2])
        page_data["extracted_info"]["scholarships"] = list(set(scholarships_found))[:5]
    
    elif category == "admission_requirements":
        admission_keywords = ["requirement", "application", "deadline", "test", "score", "transcript"]
        admission_info = []
        for keyword in admission_keywords:
            if keyword.lower() in content.lower():
                sentences = re.findall(r'[^.]*' + keyword + r'[^.]*\.', content, re.IGNORECASE)
                admission_info.extend(sentences[:2])
        page_data["extracted_info"]["requirements"] = list(set(admission_info))[:5]
    
    elif category == "international_students":
        international_keywords = ["international", "visa", "global", "overseas", "foreign"]
        international_info = []
        for keyword in international_keywords:
            if keyword.lower() in content.lower():
                sentences = re.findall(r'[^.]*' + keyword + r'[^.]*\.', content, re.IGNORECASE)
                international_info.extend(sentences[:2])
        page_data["extracted_info"]["international_info"] = list(set(international_info))[:5]
    
    elif category == "research_areas":
        research_keywords = ["research", "innovation", "discovery", "laboratory", "study", "investigation"]
        research_areas = []
        for keyword in research_keywords:
            if keyword.lower() in content.lower():
                sentences = re.findall(r'[^.]*' + keyword + r'[^.]*\.', content, re.IGNORECASE)
                research_areas.extend(sentences[:2])
        page_data["extracted_info"]["research"] = list(set(research_areas))[:5]
    
    elif category == "contact_info":
        # Extract contact information
        emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', content)
        phones = re.findall(r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', content)
        address_pattern = r'\d+\s+[A-Za-z\s]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Drive|Dr)'
        addresses = re.findall(address_pattern, content, re.IGNORECASE)
        
        page_data["extracted_info"]["emails"] = list(set(emails))[:5]
        page_data["extracted_info"]["phone_numbers"] = list(set(phones))[:3]
        page_data["extracted_info"]["addresses"] = list(set(addresses))[:3]
    
    return page_data

async def search_university_info_comprehensive(browser_tool, university_name: str, base_url: str):
    """Comprehensive university information search using sitemap crawling"""
    print(f"🗺️  Starting comprehensive search for {university_name}...")
    
    university_data = {
        "university_name": university_name,
        "base_url": base_url,
        "search_timestamp": datetime.now().isoformat(),
        "sitemap_analysis": {},
        "pages_analyzed": 0,
        "pages_by_category": {},
        "comprehensive_data": {
            "academic_programs": [],
            "scholarships": [],
            "admission_requirements": [],
            "international_students": [],
            "research_areas": [],
            "contact_info": [],
            "campus_life": [],
            "faculty": [],
            "news": [],
            "library": [],
            "general": []
        },
        "errors": []
    }
    
    try:
        # Get all URLs from sitemap
        all_urls = await get_all_sitemap_urls(browser_tool, base_url)
        print(f"📋 Found {len(all_urls)} URLs to analyze")
        
        university_data["sitemap_analysis"]["total_urls_found"] = len(all_urls)
        university_data["sitemap_analysis"]["urls"] = all_urls
        
        # Analyze each page
        for i, url in enumerate(all_urls[:50]):  # Limit to first 50 URLs to avoid timeout
            try:
                print(f"📄 Analyzing page {i+1}/{min(len(all_urls), 50)}: {url}")
                
                await safe_browser_action(browser_tool, "go_to_url", url=url)
                await safe_browser_action(browser_tool, "wait", seconds=2)
                
                content = await get_page_content_simple(browser_tool)
                if content:
                    page_data = await analyze_page_content(content, url)
                    category = page_data["category"]
                    
                    # Store page data by category
                    if category not in university_data["pages_by_category"]:
                        university_data["pages_by_category"][category] = []
                    university_data["pages_by_category"][category].append(page_data)
                    
                    # Add extracted info to comprehensive data
                    if page_data["extracted_info"]:
                        university_data["comprehensive_data"][category].append(page_data["extracted_info"])
                    
                    university_data["pages_analyzed"] += 1
                    print(f"  ✅ Categorized as: {category}")
                else:
                    print(f"  ⚠️  No content found")
                
            except Exception as e:
                print(f"  ❌ Error analyzing {url}: {e}")
                university_data["errors"].append(f"Error analyzing {url}: {str(e)}")
                continue
        
        print(f"✅ Comprehensive analysis completed! Analyzed {university_data['pages_analyzed']} pages")
        
    except Exception as e:
        print(f"❌ Error during comprehensive search: {e}")
        university_data["errors"].append(str(e))
    
    return university_data

async def get_university_data(university_name: str):
    browser_tool = BrowserToolPlaywright()
    
    # Initialize data collection
    search_data = {
        "university_name": university_name,
        "search_timestamp": datetime.now().isoformat(),
        "navigation_result": None,
        "page_state": None,
        "university_information": {},
        "errors": []
    }
    
    try:
        print(f"🔍 Researching {university_name}...")
        
        base_url = "https://www.harvard.edu"
        
        # Navigate to university homepage
        result = await safe_browser_action(browser_tool, "go_to_url", url=base_url)
        print(f"Navigation result: {safe_get_output(result)}")
        search_data["navigation_result"] = safe_get_output(result)
        
        # Wait for page to load
        await safe_browser_action(browser_tool, "wait", seconds=3)
        
        # Get current state
        state_result = await browser_tool.get_current_state()
        if state_result.is_success():
            try:
                state_data = json.loads(state_result.output)
                print(f"Current URL: {state_data.get('url')}")
                print(f"Page title: {state_data.get('title')}")
                print(f"Screenshot captured: {'Yes' if state_result.base64_image else 'No'}")
                
                # Store page state data
                search_data["page_state"] = {
                    "url": state_data.get('url'),
                    "title": state_data.get('title'),
                    "screenshot_available": bool(state_result.base64_image)
                }
            except json.JSONDecodeError:
                print("Warning: Could not parse state data")
                search_data["errors"].append("Failed to parse page state data")
        else:
            search_data["errors"].append("Failed to get page state")
        
        # Collect comprehensive university information using sitemap
        print("🔍 Starting comprehensive university information collection...")
        university_info = await search_university_info_comprehensive(browser_tool, university_name, base_url)
        search_data["university_information"] = university_info
        
        print(f"✅ Successfully collected comprehensive data for {university_name}")
        
    except Exception as e:
        error_msg = f"Error during search: {e}"
        print(f"❌ {error_msg}")
        search_data["errors"].append(error_msg)
    finally:
        await browser_tool.cleanup()
    
    return search_data

async def main():
    """Main function to run the university search and save results"""
    university_name = "Harvard University"
    
    # Get the search data
    search_data = await get_university_data(university_name)
    
    # Save to JSON file
    saved_file = save_to_json(search_data)
    
    if saved_file:
        print(f"🎉 Search completed! Results saved to: {saved_file}")
        print(f"📊 Comprehensive data collection summary:")
        
        university_info = search_data.get('university_information', {})
        sitemap_analysis = university_info.get('sitemap_analysis', {})
        comprehensive_data = university_info.get('comprehensive_data', {})
        
        print(f"   - Total URLs found: {sitemap_analysis.get('total_urls_found', 0)}")
        print(f"   - Pages analyzed: {university_info.get('pages_analyzed', 0)}")
        print(f"   - Categories found: {len(university_info.get('pages_by_category', {}))}")
        
        for category, data in comprehensive_data.items():
            if data:
                print(f"   - {category.replace('_', ' ').title()}: {len(data)} entries")
        
        print(f"   - Errors encountered: {len(search_data.get('errors', []))}")
    else:
        print("⚠️  Search completed but failed to save results")

if __name__ == "__main__":
    asyncio.run(main())