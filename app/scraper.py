import time
import re
from typing import Dict, List, Optional, Any
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class UniversityScraper:
    def __init__(self, headless: bool = True, timeout: int = 10):
        """
        Initialize the university scraper with headless browser
        
        Args:
            headless: Whether to run browser in headless mode
            timeout: Timeout for element waits in seconds
        """
        self.timeout = timeout
        self.driver = None
        self.setup_driver(headless)
    
    def setup_driver(self, headless: bool = True):
        """Setup Chrome driver with appropriate options"""
        chrome_options = Options()
        
        if headless:
            chrome_options.add_argument("--headless")
        
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        # Disable images and CSS for faster loading
        prefs = {
            "profile.managed_default_content_settings.images": 2,
            "profile.default_content_setting_values.notifications": 2
        }
        chrome_options.add_experimental_option("prefs", prefs)
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.implicitly_wait(5)
        except Exception as e:
            logger.error(f"Failed to initialize Chrome driver: {e}")
            raise
    
    def search_university(self, university_name: str) -> List[Dict[str, str]]:
        """
        Search for a university and return potential matches
        
        Args:
            university_name: Name of the university to search for
            
        Returns:
            List of potential university matches with name and website
        """
        try:
            # Search on Google
            search_query = f"{university_name} official website"
            self.driver.get(f"https://www.google.com/search?q={search_query}")
            
            # Wait for search results
            WebDriverWait(self.driver, self.timeout).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.g"))
            )
            
            results = []
            search_results = self.driver.find_elements(By.CSS_SELECTOR, "div.g")
            
            for result in search_results[:5]:  # Get top 5 results
                try:
                    title_element = result.find_element(By.CSS_SELECTOR, "h3")
                    link_element = result.find_element(By.CSS_SELECTOR, "a")
                    
                    title = title_element.text
                    link = link_element.get_attribute("href")
                    
                    if link and "http" in link:
                        results.append({
                            "title": title,
                            "url": link,
                            "confidence": self._calculate_confidence(title, university_name)
                        })
                except NoSuchElementException:
                    continue
            
            # Sort by confidence
            results.sort(key=lambda x: x["confidence"], reverse=True)
            return results
            
        except Exception as e:
            logger.error(f"Error searching for university {university_name}: {e}")
            return []
    
    def _calculate_confidence(self, title: str, university_name: str) -> float:
        """Calculate confidence score for search result"""
        title_lower = title.lower()
        uni_lower = university_name.lower()
        
        # Check for exact matches
        if uni_lower in title_lower:
            return 1.0
        
        # Check for partial matches
        uni_words = uni_lower.split()
        matches = sum(1 for word in uni_words if word in title_lower)
        
        if len(uni_words) > 0:
            return matches / len(uni_words)
        
        return 0.0
    
    def scrape_university_website(self, url: str) -> Dict[str, Any]:
        """
        Scrape university information from their official website
        
        Args:
            url: University website URL
            
        Returns:
            Dictionary containing scraped university information
        """
        try:
            self.driver.get(url)
            time.sleep(3)  # Allow page to load
            
            university_data = {
                "website": url,
                "name": self._extract_university_name(),
                "contact_info": self._extract_contact_info(),
                "academic_info": self._extract_academic_info(),
                "statistics": self._extract_statistics(),
                "programs": self._extract_programs(),
                "facilities": self._extract_facilities(),
                "about": self._extract_about_info()
            }
            
            return university_data
            
        except Exception as e:
            logger.error(f"Error scraping university website {url}: {e}")
            return {}
    
    def _extract_university_name(self) -> str:
        """Extract university name from page title or headings"""
        try:
            # Try to get from page title
            title = self.driver.title
            if title:
                # Clean up title
                title = re.sub(r'[-|]', ' ', title)
                title = re.sub(r'\s+', ' ', title).strip()
                return title
            
            # Try to get from main heading
            h1_elements = self.driver.find_elements(By.TAG_NAME, "h1")
            if h1_elements:
                return h1_elements[0].text.strip()
                
        except Exception as e:
            logger.warning(f"Error extracting university name: {e}")
        
        return ""
    
    def _extract_contact_info(self) -> Dict[str, str]:
        """Extract contact information from the website"""
        contact_info = {}
        
        try:
            # Look for contact information in various ways
            page_text = self.driver.page_source.lower()
            
            # Extract phone numbers
            phone_pattern = r'(\+?1?[-.\s]?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4})'
            phones = re.findall(phone_pattern, page_text)
            if phones:
                contact_info["phone"] = phones[0]
            
            # Extract email addresses
            email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            emails = re.findall(email_pattern, page_text)
            if emails:
                contact_info["email"] = emails[0]
            
            # Look for address information
            address_keywords = ["address", "location", "campus"]
            for keyword in address_keywords:
                try:
                    elements = self.driver.find_elements(By.XPATH, f"//*[contains(text(), '{keyword}')]")
                    for element in elements:
                        text = element.text.strip()
                        if len(text) > 10 and len(text) < 200:
                            contact_info["address"] = text
                            break
                except:
                    continue
                    
        except Exception as e:
            logger.warning(f"Error extracting contact info: {e}")
        
        return contact_info
    
    def _extract_academic_info(self) -> Dict[str, Any]:
        """Extract academic information like founded year, type, etc."""
        academic_info = {}
        
        try:
            page_text = self.driver.page_source.lower()
            
            # Look for founded year
            founded_patterns = [
                r'founded\s+in\s+(\d{4})',
                r'established\s+in\s+(\d{4})',
                r'(\d{4})\s*[-–]\s*founded'
            ]
            
            for pattern in founded_patterns:
                match = re.search(pattern, page_text)
                if match:
                    academic_info["founded_year"] = int(match.group(1))
                    break
            
            # Look for university type
            if "public university" in page_text:
                academic_info["type"] = "Public"
            elif "private university" in page_text:
                academic_info["type"] = "Private"
                
        except Exception as e:
            logger.warning(f"Error extracting academic info: {e}")
        
        return academic_info
    
    def _extract_statistics(self) -> Dict[str, Any]:
        """Extract university statistics"""
        stats = {}
        
        try:
            page_text = self.driver.page_source.lower()
            
            # Look for student population
            student_patterns = [
                r'(\d{1,3}(?:,\d{3})*)\s+students',
                r'student\s+body\s+of\s+(\d{1,3}(?:,\d{3})*)',
                r'enrollment\s+of\s+(\d{1,3}(?:,\d{3})*)'
            ]
            
            for pattern in student_patterns:
                match = re.search(pattern, page_text)
                if match:
                    stats["student_population"] = int(match.group(1).replace(",", ""))
                    break
            
            # Look for faculty count
            faculty_patterns = [
                r'(\d{1,3}(?:,\d{3})*)\s+faculty',
                r'(\d{1,3}(?:,\d{3})*)\s+professors'
            ]
            
            for pattern in faculty_patterns:
                match = re.search(pattern, page_text)
                if match:
                    stats["faculty_count"] = int(match.group(1).replace(",", ""))
                    break
                    
        except Exception as e:
            logger.warning(f"Error extracting statistics: {e}")
        
        return stats
    
    def _extract_programs(self) -> List[Dict[str, str]]:
        """Extract academic programs information"""
        programs = []
        
        try:
            # Look for program-related pages or sections
            program_keywords = ["programs", "academics", "degrees", "courses"]
            
            for keyword in program_keywords:
                try:
                    elements = self.driver.find_elements(By.XPATH, f"//a[contains(text(), '{keyword}')]")
                    for element in elements:
                        href = element.get_attribute("href")
                        if href and "program" in href.lower():
                            # Navigate to programs page
                            self.driver.get(href)
                            time.sleep(2)
                            
                            # Extract program information
                            program_elements = self.driver.find_elements(By.CSS_SELECTOR, "h2, h3, h4")
                            for elem in program_elements:
                                text = elem.text.strip()
                                if len(text) > 5 and len(text) < 100:
                                    programs.append({
                                        "name": text,
                                        "level": self._determine_program_level(text),
                                        "field": self._determine_program_field(text)
                                    })
                            break
                except:
                    continue
                    
        except Exception as e:
            logger.warning(f"Error extracting programs: {e}")
        
        return programs[:20]  # Limit to 20 programs
    
    def _extract_facilities(self) -> List[Dict[str, str]]:
        """Extract facilities information"""
        facilities = []
        
        try:
            facility_keywords = ["library", "laboratory", "lab", "gym", "sports", "campus"]
            
            for keyword in facility_keywords:
                try:
                    elements = self.driver.find_elements(By.XPATH, f"//*[contains(text(), '{keyword}')]")
                    for element in elements:
                        text = element.text.strip()
                        if len(text) > 5 and len(text) < 200:
                            facilities.append({
                                "name": text[:100],  # Truncate if too long
                                "type": keyword.title()
                            })
                except:
                    continue
                    
        except Exception as e:
            logger.warning(f"Error extracting facilities: {e}")
        
        return facilities[:10]  # Limit to 10 facilities
    
    def _extract_about_info(self) -> Dict[str, str]:
        """Extract about/mission information"""
        about_info = {}
        
        try:
            about_keywords = ["about", "mission", "vision", "history"]
            
            for keyword in about_keywords:
                try:
                    elements = self.driver.find_elements(By.XPATH, f"//*[contains(text(), '{keyword}')]")
                    for element in elements:
                        text = element.text.strip()
                        if len(text) > 50 and len(text) < 1000:
                            about_info[keyword] = text
                            break
                except:
                    continue
                    
        except Exception as e:
            logger.warning(f"Error extracting about info: {e}")
        
        return about_info
    
    def _determine_program_level(self, program_name: str) -> str:
        """Determine the level of a program (Bachelor, Master, PhD, etc.)"""
        name_lower = program_name.lower()
        
        if any(word in name_lower for word in ["bachelor", "b.s.", "b.a.", "undergraduate"]):
            return "Bachelor"
        elif any(word in name_lower for word in ["master", "m.s.", "m.a.", "graduate"]):
            return "Master"
        elif any(word in name_lower for word in ["phd", "doctorate", "doctoral"]):
            return "PhD"
        else:
            return "Unknown"
    
    def _determine_program_field(self, program_name: str) -> str:
        """Determine the field of a program"""
        name_lower = program_name.lower()
        
        fields = {
            "computer science": ["computer", "cs", "software", "programming"],
            "engineering": ["engineering", "mechanical", "electrical", "civil"],
            "business": ["business", "management", "finance", "marketing"],
            "medicine": ["medicine", "medical", "health", "nursing"],
            "arts": ["arts", "music", "drama", "theater"],
            "science": ["science", "physics", "chemistry", "biology"]
        }
        
        for field, keywords in fields.items():
            if any(keyword in name_lower for keyword in keywords):
                return field.title()
        
        return "General"
    
    def close(self):
        """Close the browser driver"""
        if self.driver:
            self.driver.quit()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close() 