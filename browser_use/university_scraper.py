import asyncio
import json
import time
from typing import Dict, List, Any, Optional
from datetime import datetime
import aiohttp
from playwright.async_api import async_playwright, Browser, Page
import openai
from sqlalchemy.orm import Session
from database.models import UniversityDataCollection, UniversitySearchTask, LLMAnalysisResult, University
from database.database import get_db

class UniversityDataScraper:
    def __init__(self, openai_api_key: str, db_session: Session):
        self.openai_api_key = openai_api_key
        self.db_session = db_session
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        
        # Configure OpenAI
        openai.api_key = openai_api_key
        
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
            "accreditation": "string",
            "student_population": "integer",
            "faculty_count": "integer",
            "acceptance_rate": "float",
            "tuition_domestic": "float",
            "tuition_international": "float",
            "world_ranking": "integer",
            "national_ranking": "integer",
            "description": "string",
            "mission_statement": "string",
            "vision_statement": "string",
            "programs": [
                {
                    "name": "string",
                    "level": "string",  # Bachelor, Master, PhD
                    "field": "string",
                    "duration": "string",
                    "tuition": "float",
                    "description": "string",
                    "requirements": "string"
                }
            ],
            "facilities": [
                {
                    "name": "string",
                    "type": "string",  # Library, Lab, Sports, etc.
                    "description": "string",
                    "capacity": "integer"
                }
            ],
            "confidence_score": "float",
            "source_urls": ["string"]
        }

    async def initialize_browser(self):
        """Initialize the browser for web scraping"""
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(headless=True)
        self.page = await self.browser.new_page()
        
        # Set user agent to avoid detection
        await self.page.set_extra_http_headers({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })

    async def close_browser(self):
        """Close the browser"""
        if self.browser:
            await self.browser.close()

    async def search_university_info(self, university_name: str, search_queries: List[str] = None) -> Dict[str, Any]:
        """Search for university information using multiple search engines"""
        if not search_queries:
            search_queries = [
                f"{university_name} university official website",
                f"{university_name} university admissions requirements",
                f"{university_name} university programs degrees",
                f"{university_name} university tuition fees",
                f"{university_name} university ranking",
                f"{university_name} university student population",
                f"{university_name} university faculty staff"
            ]

        search_results = {}
        
        # Search on Google
        try:
            await self.page.goto("https://www.google.com")
            await self.page.wait_for_load_state("networkidle")
            
            for query in search_queries:
                # Type search query
                await self.page.fill('textarea[name="q"]', query)
                await self.page.press('textarea[name="q"]', 'Enter')
                await self.page.wait_for_load_state("networkidle")
                
                # Extract search results
                results = await self.page.query_selector_all('div.g')
                query_results = []
                
                for result in results[:5]:  # Get top 5 results
                    try:
                        title_elem = await result.query_selector('h3')
                        link_elem = await result.query_selector('a')
                        snippet_elem = await result.query_selector('.VwiC3b')
                        
                        if title_elem and link_elem:
                            title = await title_elem.inner_text()
                            link = await link_elem.get_attribute('href')
                            snippet = await snippet_elem.inner_text() if snippet_elem else ""
                            
                            query_results.append({
                                "title": title,
                                "url": link,
                                "snippet": snippet
                            })
                    except Exception as e:
                        print(f"Error extracting search result: {e}")
                        continue
                
                search_results[query] = query_results
                
                # Wait between searches to avoid rate limiting
                await asyncio.sleep(2)
                
        except Exception as e:
            print(f"Error during Google search: {e}")
        
        return search_results

    async def scrape_webpage_content(self, url: str) -> Dict[str, Any]:
        """Scrape content from a specific webpage"""
        try:
            await self.page.goto(url, wait_until="networkidle", timeout=30000)
            
            # Extract page content
            title = await self.page.title()
            
            # Get main content
            content = await self.page.evaluate("""
                () => {
                    // Remove script and style elements
                    const scripts = document.querySelectorAll('script, style, nav, footer, header');
                    scripts.forEach(el => el.remove());
                    
                    // Get main content
                    const main = document.querySelector('main') || document.querySelector('#main') || document.querySelector('.main') || document.body;
                    return main.innerText;
                }
            """)
            
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
            print(f"Error scraping {url}: {e}")
            return {
                "url": url,
                "error": str(e),
                "scraped_at": datetime.now().isoformat()
            }

    async def analyze_with_llm(self, university_name: str, scraped_content: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze scraped content with LLM to extract structured university data"""
        
        # Prepare content for LLM
        content_text = ""
        source_urls = []
        
        for item in scraped_content:
            if "content" in item:
                content_text += f"\n\nSource: {item['url']}\nTitle: {item.get('title', 'N/A')}\nContent: {item['content'][:2000]}\n"
                source_urls.append(item['url'])
        
        # Create prompt for LLM
        prompt = f"""
You are an expert university data analyst. Your task is to extract comprehensive information about {university_name} from the provided web content.

Please analyze the following content and extract university information in the exact JSON format specified below. Only include information that you can confidently extract from the provided content. If information is not available, use null for that field.

Content to analyze:
{content_text}

Please return the data in this exact JSON format:
{json.dumps(self.university_data_schema, indent=2)}

Important guidelines:
1. Only extract information that is explicitly mentioned in the provided content
2. Be accurate and precise with numbers and dates
3. For rankings, use only the most recent and reliable ranking mentioned
4. For tuition, specify if it's annual or per semester
5. Include source URLs for verification
6. Provide a confidence score (0.0 to 1.0) based on the quality and completeness of available information

Return only the JSON object, no additional text.
"""

        try:
            start_time = time.time()
            
            response = await openai.ChatCompletion.acreate(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a university data extraction expert. Return only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=4000
            )
            
            processing_time = time.time() - start_time
            
            # Parse LLM response
            llm_response = response.choices[0].message.content.strip()
            
            # Try to extract JSON from response
            try:
                # Remove any markdown formatting
                if llm_response.startswith("```json"):
                    llm_response = llm_response[7:]
                if llm_response.endswith("```"):
                    llm_response = llm_response[:-3]
                
                structured_data = json.loads(llm_response)
                
                # Calculate confidence score
                confidence_score = self._calculate_confidence_score(structured_data)
                
                return {
                    "raw_response": llm_response,
                    "structured_data": structured_data,
                    "confidence_score": confidence_score,
                    "processing_time": processing_time,
                    "source_urls": source_urls
                }
                
            except json.JSONDecodeError as e:
                print(f"Error parsing LLM response as JSON: {e}")
                return {
                    "raw_response": llm_response,
                    "structured_data": None,
                    "confidence_score": 0.0,
                    "processing_time": processing_time,
                    "error": f"JSON parsing error: {e}",
                    "source_urls": source_urls
                }
                
        except Exception as e:
            print(f"Error calling LLM API: {e}")
            return {
                "raw_response": None,
                "structured_data": None,
                "confidence_score": 0.0,
                "processing_time": 0.0,
                "error": str(e),
                "source_urls": source_urls
            }

    def _calculate_confidence_score(self, data: Dict[str, Any]) -> float:
        """Calculate confidence score based on data completeness and quality"""
        if not data:
            return 0.0
        
        # Define important fields
        important_fields = [
            "name", "website", "country", "city", "student_population", 
            "acceptance_rate", "tuition_domestic", "description"
        ]
        
        # Count filled important fields
        filled_fields = 0
        for field in important_fields:
            if data.get(field) and data[field] != "" and data[field] is not None:
                filled_fields += 1
        
        # Base score on completeness
        completeness_score = filled_fields / len(important_fields)
        
        # Bonus for having programs and facilities
        if data.get("programs") and len(data["programs"]) > 0:
            completeness_score += 0.1
        
        if data.get("facilities") and len(data["facilities"]) > 0:
            completeness_score += 0.1
        
        # Bonus for having source URLs
        if data.get("source_urls") and len(data["source_urls"]) > 0:
            completeness_score += 0.1
        
        return min(completeness_score, 1.0)

    async def collect_university_data(self, university_name: str) -> Dict[str, Any]:
        """Main method to collect university data using browser and LLM"""
        
        # Create data collection record
        data_collection = UniversityDataCollection(
            university_name=university_name,
            status="in_progress",
            started_at=datetime.now()
        )
        self.db_session.add(data_collection)
        self.db_session.commit()
        
        try:
            # Initialize browser
            await self.initialize_browser()
            
            # Search for university information
            print(f"Searching for information about {university_name}...")
            search_results = await self.search_university_info(university_name)
            
            # Update search results in database
            data_collection.search_results = search_results
            self.db_session.commit()
            
            # Extract URLs from search results
            urls_to_scrape = []
            for query, results in search_results.items():
                for result in results:
                    if result.get("url") and "http" in result["url"]:
                        urls_to_scrape.append(result["url"])
            
            # Remove duplicates and limit to top 10 URLs
            urls_to_scrape = list(set(urls_to_scrape))[:10]
            
            # Scrape content from URLs
            print(f"Scraping content from {len(urls_to_scrape)} URLs...")
            scraped_content = []
            
            for url in urls_to_scrape:
                try:
                    content = await self.scrape_webpage_content(url)
                    scraped_content.append(content)
                    await asyncio.sleep(1)  # Rate limiting
                except Exception as e:
                    print(f"Error scraping {url}: {e}")
                    continue
            
            # Update scraped content in database
            data_collection.scraped_content = scraped_content
            self.db_session.commit()
            
            # Analyze with LLM
            print("Analyzing content with LLM...")
            llm_analysis = await self.analyze_with_llm(university_name, scraped_content)
            
            # Save LLM analysis result
            llm_result = LLMAnalysisResult(
                data_collection_id=data_collection.id,
                analysis_type="university_info",
                model_used="gpt-4",
                prompt_used="University data extraction prompt",
                raw_response=llm_analysis.get("raw_response"),
                structured_data=llm_analysis.get("structured_data"),
                confidence_score=llm_analysis.get("confidence_score", 0.0),
                processing_time=llm_analysis.get("processing_time"),
                data_completeness=self._calculate_confidence_score(llm_analysis.get("structured_data", {})),
                source_citations=llm_analysis.get("source_urls", [])
            )
            self.db_session.add(llm_result)
            
            # Update data collection with results
            data_collection.llm_analysis = llm_analysis
            data_collection.extracted_data = llm_analysis.get("structured_data")
            data_collection.confidence_score = llm_analysis.get("confidence_score", 0.0)
            data_collection.status = "completed"
            data_collection.completed_at = datetime.now()
            
            self.db_session.commit()
            
            print(f"Data collection completed for {university_name} with confidence score: {llm_analysis.get('confidence_score', 0.0)}")
            
            return {
                "success": True,
                "data_collection_id": data_collection.id,
                "extracted_data": llm_analysis.get("structured_data"),
                "confidence_score": llm_analysis.get("confidence_score", 0.0),
                "source_urls": llm_analysis.get("source_urls", [])
            }
            
        except Exception as e:
            print(f"Error collecting data for {university_name}: {e}")
            
            # Update status to failed
            data_collection.status = "failed"
            data_collection.error_message = str(e)
            data_collection.completed_at = datetime.now()
            self.db_session.commit()
            
            return {
                "success": False,
                "error": str(e),
                "data_collection_id": data_collection.id
            }
        
        finally:
            await self.close_browser()

async def main():
    """Example usage of the UniversityDataScraper"""
    # You'll need to set up your database session and OpenAI API key
    db_session = next(get_db())
    
    scraper = UniversityDataScraper(
        openai_api_key="your-openai-api-key-here",
        db_session=db_session
    )
    
    # Collect data for a university
    result = await scraper.collect_university_data("Stanford University")
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    asyncio.run(main()) 