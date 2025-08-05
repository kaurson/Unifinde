import asyncio
import json
import re
from typing import Dict, Any, Optional, List
from playwright.async_api import async_playwright
import openai
import sys
import os

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.models import School
from database.database import get_db

class SchoolScraperService:
    def __init__(self):
        self.client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        # School data template
        self.school_template = {
            "name": "",
            "website": "",
            "country": "",
            "city": "",
            "state": "",
            "postal_code": "",
            "phone": "",
            "email": "",
            "student_population": None,
            "teacher_count": None,
            "graduation_rate": None,
            "college_acceptance_rate": None,
            "average_sat_score": None,
            "average_act_score": None,
            "ap_courses_offered": None,
            "test_scores": {},
            "rankings": {},
            "awards": [],
            "programs_offered": [],
            "extracurricular_activities": [],
            "sports_teams": [],
            "description": "",
            "mission_statement": "",
            "facilities": [],
            "source_url": "",
            "confidence_score": 0.0
        }
    
    async def scrape_school(self, school_name: str, location: Optional[str] = None) -> Dict[str, Any]:
        """Scrape school data using browser automation and AI"""
        
        search_query = f"{school_name}"
        if location:
            search_query += f" {location}"
        
        try:
            # Use browser automation to search for school information
            school_data = await self._search_school_info(search_query)
            
            # Use AI to extract and structure the data
            structured_data = await self._extract_school_data(school_data, school_name)
            
            # Fill in the template
            result = self.school_template.copy()
            result.update(structured_data)
            result["name"] = school_name
            result["source_url"] = school_data.get("source_url", "")
            
            return result
            
        except Exception as e:
            print(f"Error scraping school data: {e}")
            # Return basic data
            return {
                **self.school_template,
                "name": school_name,
                "confidence_score": 0.1
            }
    
    async def _search_school_info(self, search_query: str) -> Dict[str, Any]:
        """Search for school information using browser automation"""
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            try:
                # Search for the school
                await page.goto(f"https://www.google.com/search?q={search_query}+school+statistics+information")
                await page.wait_for_load_state("networkidle")
                
                # Get search results
                search_results = await page.query_selector_all("div.g")
                
                school_info = {
                    "search_results": [],
                    "source_url": page.url
                }
                
                # Extract information from search results
                for result in search_results[:5]:  # Get first 5 results
                    try:
                        title_elem = await result.query_selector("h3")
                        title = await title_elem.text_content() if title_elem else ""
                        
                        snippet_elem = await result.query_selector("div.VwiC3b")
                        snippet = await snippet_elem.text_content() if snippet_elem else ""
                        
                        link_elem = await result.query_selector("a")
                        link = await link_elem.get_attribute("href") if link_elem else ""
                        
                        school_info["search_results"].append({
                            "title": title,
                            "snippet": snippet,
                            "link": link
                        })
                    except Exception as e:
                        print(f"Error extracting search result: {e}")
                        continue
                
                # Try to visit the school's official website if found
                official_site = await self._find_official_website(school_info["search_results"])
                if official_site:
                    try:
                        await page.goto(official_site, timeout=10000)
                        await page.wait_for_load_state("networkidle")
                        
                        # Extract content from official website
                        content = await page.content()
                        school_info["official_website_content"] = content[:10000]  # Limit content size
                        school_info["official_website_url"] = official_site
                        
                    except Exception as e:
                        print(f"Error accessing official website: {e}")
                
                await browser.close()
                return school_info
                
            except Exception as e:
                await browser.close()
                raise e
    
    async def _find_official_website(self, search_results: list) -> Optional[str]:
        """Find the official school website from search results"""
        
        for result in search_results:
            title = result.get("title", "").lower()
            snippet = result.get("snippet", "").lower()
            link = result.get("link", "")
            
            # Look for official school indicators
            if any(indicator in title or indicator in snippet for indicator in [
                "official", "homepage", "main", "school district", "public school", "private school"
            ]):
                if link and not link.startswith("http"):
                    # Extract URL from Google search result
                    if "/url?q=" in link:
                        url_start = link.find("/url?q=") + 7
                        url_end = link.find("&", url_start)
                        if url_end == -1:
                            url_end = len(link)
                        return link[url_start:url_end]
                    else:
                        return link
        
        return None
    
    async def _extract_school_data(self, school_info: Dict[str, Any], school_name: str) -> Dict[str, Any]:
        """Use AI to extract structured school data from search results"""
        
        try:
            # Prepare context for AI
            context = self._prepare_context(school_info, school_name)
            
            # Use AI to extract data
            prompt = self._create_extraction_prompt(context, school_name)
            
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert in extracting structured school information from web search results. Extract relevant data and return it as a JSON object."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,
                max_tokens=2000
            )
            
            # Parse AI response
            response_text = response.choices[0].message.content
            extracted_data = self._parse_ai_response(response_text)
            
            return extracted_data
            
        except Exception as e:
            print(f"Error extracting school data with AI: {e}")
            # Fallback to basic extraction
            return self._basic_extraction(school_info, school_name)
    
    def _prepare_context(self, school_info: Dict[str, Any], school_name: str) -> str:
        """Prepare context for AI extraction"""
        
        context = f"School Name: {school_name}\n\n"
        
        # Add search results
        context += "Search Results:\n"
        for i, result in enumerate(school_info.get("search_results", [])[:3]):
            context += f"{i+1}. Title: {result.get('title', '')}\n"
            context += f"   Snippet: {result.get('snippet', '')}\n"
            context += f"   Link: {result.get('link', '')}\n\n"
        
        # Add official website content if available
        if "official_website_content" in school_info:
            context += f"Official Website: {school_info.get('official_website_url', '')}\n"
            # Extract key information from website content
            content = school_info["official_website_content"]
            # Look for common school information patterns
            patterns = {
                "phone": r"phone[:\s]*([\d\-\(\)\s]+)",
                "email": r"email[:\s]*([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})",
                "address": r"address[:\s]*([^<>]+)",
                "students": r"(\d+)\s*students?",
                "teachers": r"(\d+)\s*teachers?",
                "graduation": r"graduation\s*rate[:\s]*(\d+\.?\d*)%?",
                "acceptance": r"acceptance\s*rate[:\s]*(\d+\.?\d*)%?",
                "sat": r"sat[:\s]*(\d+)",
                "act": r"act[:\s]*(\d+)"
            }
            
            extracted_info = {}
            for key, pattern in patterns.items():
                matches = re.findall(pattern, content, re.IGNORECASE)
                if matches:
                    extracted_info[key] = matches[0]
            
            if extracted_info:
                context += "Extracted Information:\n"
                for key, value in extracted_info.items():
                    context += f"  {key}: {value}\n"
        
        return context
    
    def _create_extraction_prompt(self, context: str, school_name: str) -> str:
        """Create prompt for AI data extraction"""
        
        prompt = f"""
        Based on the following information about {school_name}, extract relevant school data and return it as a JSON object.

        Context:
        {context}

        Please extract the following information and return it as a JSON object:
        {{
            "website": "school website URL if found",
            "country": "country",
            "city": "city",
            "state": "state/province",
            "postal_code": "postal code",
            "phone": "phone number",
            "email": "email address",
            "student_population": number or null,
            "teacher_count": number or null,
            "graduation_rate": number (0-100) or null,
            "college_acceptance_rate": number (0-100) or null,
            "average_sat_score": number or null,
            "average_act_score": number or null,
            "ap_courses_offered": number or null,
            "test_scores": {{"key": "value"}},
            "rankings": {{"key": "value"}},
            "awards": ["array of awards"],
            "programs_offered": ["array of programs"],
            "extracurricular_activities": ["array of activities"],
            "sports_teams": ["array of sports"],
            "description": "school description",
            "mission_statement": "mission statement",
            "facilities": ["array of facilities"],
            "confidence_score": number between 0 and 1
        }}

        Only include information that is clearly stated or can be reasonably inferred. Use null for missing information. Set confidence_score based on how much reliable information was found.
        """
        
        return prompt
    
    def _parse_ai_response(self, response_text: str) -> Dict[str, Any]:
        """Parse AI response and extract JSON data"""
        
        try:
            # Try to find JSON in the response
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            
            if start_idx != -1 and end_idx != 0:
                json_str = response_text[start_idx:end_idx]
                return json.loads(json_str)
            else:
                raise ValueError("No JSON found in response")
                
        except (json.JSONDecodeError, ValueError) as e:
            print(f"Error parsing AI response: {e}")
            return {}
    
    def _basic_extraction(self, school_info: Dict[str, Any], school_name: str) -> Dict[str, Any]:
        """Basic extraction without AI"""
        
        extracted_data = {}
        
        # Extract basic information from search results
        for result in school_info.get("search_results", []):
            snippet = result.get("snippet", "").lower()
            
            # Extract phone numbers
            phone_match = re.search(r"(\d{3}[-.\s]?\d{3}[-.\s]?\d{4})", snippet)
            if phone_match and "phone" not in extracted_data:
                extracted_data["phone"] = phone_match.group(1)
            
            # Extract email addresses
            email_match = re.search(r"([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})", snippet)
            if email_match and "email" not in extracted_data:
                extracted_data["email"] = email_match.group(1)
            
            # Extract student population
            students_match = re.search(r"(\d+)\s*students?", snippet)
            if students_match and "student_population" not in extracted_data:
                extracted_data["student_population"] = int(students_match.group(1))
            
            # Extract graduation rate
            grad_match = re.search(r"graduation\s*rate[:\s]*(\d+\.?\d*)%?", snippet)
            if grad_match and "graduation_rate" not in extracted_data:
                extracted_data["graduation_rate"] = float(grad_match.group(1))
        
        extracted_data["confidence_score"] = 0.3  # Low confidence for basic extraction
        
        return extracted_data 