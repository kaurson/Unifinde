import json
import asyncio
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
import os
from dotenv import load_dotenv
from datetime import datetime

from .scraper import UniversityScraper
from .browser_use_scraper import BrowserUseScraper, BrowserUseConfig

# Load environment variables
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class LLMConfig:
    """Configuration for LLM integration"""
    provider: str  # "openai", "anthropic", "local", etc.
    api_key: Optional[str] = None
    model: str = "gpt-4"  # Default model
    base_url: Optional[str] = None  # For local or custom endpoints
    temperature: float = 0.1
    max_tokens: int = 1000
    timeout: int = 30

@dataclass
class ScraperConfig:
    """Configuration for scraper selection"""
    type: str = "browser_use"  # "browser_use" or "selenium"
    headless: bool = True
    disable_security: bool = True
    chrome_instance_path: Optional[str] = None
    extra_chromium_args: Optional[List[str]] = None

class FieldType(Enum):
    """Types of fields that can be requested"""
    BASIC_INFO = "basic_info"
    CONTACT = "contact"
    ACADEMIC = "academic"
    STATISTICS = "statistics"
    PROGRAMS = "programs"
    FACILITIES = "facilities"
    ABOUT = "about"
    ALL = "all"

@dataclass
class FieldRequest:
    """Request for specific university information fields"""
    university_name: str
    fields: List[FieldType]
    priority: int = 1  # 1 = highest, 5 = lowest
    source_url: Optional[str] = None

@dataclass
class FieldResponse:
    """Response with requested university information"""
    university_name: str
    fields: Dict[str, Any]
    confidence_score: float
    source_url: str
    scraped_at: str
    status: str  # "success", "partial", "failed"

class UniversityMCPServer:
    def __init__(self, llm_config: Optional[LLMConfig] = None, scraper_config: Optional[ScraperConfig] = None):
        """
        Initialize the MCP server for university data collection
        
        Args:
            llm_config: Configuration for LLM integration
            scraper_config: Configuration for scraper selection
        """
        # Initialize configurations
        self.llm_config = llm_config or self._load_default_llm_config()
        self.scraper_config = scraper_config or self._load_default_scraper_config()
        self.llm_client = None
        self.scraper = None
        
        # Available fields for LLM to request
        self.available_fields = {
            "basic_info": {
                "name": "University name",
                "website": "Official website URL",
                "country": "Country location",
                "city": "City location",
                "state": "State/Province location"
            },
            "contact": {
                "phone": "Contact phone number",
                "email": "Contact email address",
                "address": "Physical address"
            },
            "academic": {
                "founded_year": "Year university was founded",
                "type": "Public or Private university",
                "accreditation": "Accreditation information"
            },
            "statistics": {
                "student_population": "Total number of students",
                "faculty_count": "Number of faculty members",
                "acceptance_rate": "Acceptance rate percentage",
                "tuition_domestic": "Domestic tuition fees",
                "tuition_international": "International tuition fees"
            },
            "programs": {
                "programs_list": "List of academic programs offered",
                "program_levels": "Available degree levels (Bachelor, Master, PhD)",
                "program_fields": "Fields of study available"
            },
            "facilities": {
                "facilities_list": "List of campus facilities",
                "facility_types": "Types of facilities available"
            },
            "about": {
                "description": "University description",
                "mission_statement": "University mission statement",
                "vision_statement": "University vision statement"
            }
        }
    
    def _load_default_llm_config(self) -> LLMConfig:
        """Load default LLM configuration from environment variables"""
        return LLMConfig(
            provider=os.getenv("LLM_PROVIDER", "openai"),
            api_key=os.getenv("LLM_API_KEY"),
            model=os.getenv("LLM_MODEL", "gpt-4"),
            base_url=os.getenv("LLM_BASE_URL"),
            temperature=float(os.getenv("LLM_TEMPERATURE", "0.1")),
            max_tokens=int(os.getenv("LLM_MAX_TOKENS", "1000")),
            timeout=int(os.getenv("LLM_TIMEOUT", "30"))
        )
    
    def _load_default_scraper_config(self) -> ScraperConfig:
        """Load default scraper configuration from environment variables"""
        return ScraperConfig(
            type=os.getenv("SCRAPER_TYPE", "browser_use"),
            headless=os.getenv("SCRAPER_HEADLESS", "true").lower() == "true",
            disable_security=os.getenv("SCRAPER_DISABLE_SECURITY", "true").lower() == "true",
            chrome_instance_path=os.getenv("CHROME_INSTANCE_PATH"),
            extra_chromium_args=os.getenv("EXTRA_CHROMIUM_ARGS", "").split(",") if os.getenv("EXTRA_CHROMIUM_ARGS") else None
        )
    
    def get_llm_config(self) -> LLMConfig:
        """Get current LLM configuration"""
        return self.llm_config
    
    def get_scraper_config(self) -> ScraperConfig:
        """Get current scraper configuration"""
        return self.scraper_config
    
    def update_llm_config(self, config: LLMConfig):
        """Update LLM configuration"""
        self.llm_config = config
        # Reset LLM client to use new config
        self.llm_client = None
    
    def update_scraper_config(self, config: ScraperConfig):
        """Update scraper configuration"""
        self.scraper_config = config
        # Reset scraper to use new config
        self.scraper = None
    
    async def _initialize_scraper(self):
        """Initialize the appropriate scraper based on configuration"""
        if self.scraper is not None:
            return
        
        try:
            if self.scraper_config.type == "browser_use":
                # Use Browser-use with Chromium (default)
                browser_use_config = BrowserUseConfig(
                    headless=True,
                    disable_security=True
                )
                self.scraper = BrowserUseScraper(browser_use_config)
            elif self.scraper_config.type == "selenium":
                # Fallback to Selenium
                self.scraper = UniversityScraper(headless=True)
            else:
                # Default to Browser-use with Chromium
                browser_use_config = BrowserUseConfig(
                    headless=True,
                    disable_security=True
                )
                self.scraper = BrowserUseScraper(browser_use_config)
                
        except Exception as e:
            logger.error(f"Failed to initialize scraper: {e}")
            # Fallback to Selenium
            self.scraper = UniversityScraper(headless=True)
    
    async def initialize_llm_client(self):
        """Initialize LLM client based on configuration"""
        if self.llm_client is not None:
            return
        
        try:
            if self.llm_config.provider == "openai":
                import openai
                self.llm_client = openai.AsyncOpenAI(
                    api_key=self.llm_config.api_key,
                    base_url=self.llm_config.base_url
                )
            elif self.llm_config.provider == "anthropic":
                import anthropic
                self.llm_client = anthropic.AsyncAnthropic(
                    api_key=self.llm_config.api_key,
                    base_url=self.llm_config.base_url
                )
            elif self.llm_config.provider == "local":
                # For local models (Ollama, etc.)
                import openai
                self.llm_client = openai.AsyncOpenAI(
                    api_key="not-needed",
                    base_url=self.llm_config.base_url or "http://localhost:11434/v1"
                )
            else:
                logger.warning(f"Unknown LLM provider: {self.llm_config.provider}")
                
        except ImportError as e:
            logger.error(f"Failed to import LLM library for {self.llm_config.provider}: {e}")
        except Exception as e:
            logger.error(f"Failed to initialize LLM client: {e}")
    
    async def ask_llm(self, prompt: str, context: str = "") -> str:
        """Ask the LLM a question with optional context"""
        await self.initialize_llm_client()
        
        if not self.llm_client:
            return "LLM not available"
        
        try:
            full_prompt = f"{context}\n\n{prompt}" if context else prompt
            
            if self.llm_config.provider == "openai":
                response = await self.llm_client.chat.completions.create(
                    model=self.llm_config.model,
                    messages=[{"role": "user", "content": full_prompt}],
                    temperature=self.llm_config.temperature,
                    max_tokens=self.llm_config.max_tokens
                )
                return response.choices[0].message.content
            
            elif self.llm_config.provider == "anthropic":
                response = await self.llm_client.messages.create(
                    model=self.llm_config.model,
                    max_tokens=self.llm_config.max_tokens,
                    temperature=self.llm_config.temperature,
                    messages=[{"role": "user", "content": full_prompt}]
                )
                return response.content[0].text
            
            elif self.llm_config.provider == "local":
                response = await self.llm_client.chat.completions.create(
                    model=self.llm_config.model,
                    messages=[{"role": "user", "content": full_prompt}],
                    temperature=self.llm_config.temperature,
                    max_tokens=self.llm_config.max_tokens
                )
                return response.choices[0].message.content
                
        except Exception as e:
            logger.error(f"Error asking LLM: {e}")
            return f"Error: {str(e)}"
    
    async def process_field_request_with_llm(self, request: FieldRequest) -> FieldResponse:
        """
        Process a field request using LLM to enhance data extraction
        
        Args:
            request: FieldRequest object with university name and requested fields
            
        Returns:
            FieldResponse with collected data enhanced by LLM
        """
        # First, get basic scraped data
        basic_response = await self.process_field_request(request)
        
        if basic_response.status == "failed":
            return basic_response
        
        # Use LLM to enhance the data
        try:
            enhanced_data = await self._enhance_data_with_llm(basic_response.fields, request)
            basic_response.fields = enhanced_data
            basic_response.confidence_score = min(1.0, basic_response.confidence_score + 0.1)  # Boost confidence
        except Exception as e:
            logger.warning(f"LLM enhancement failed: {e}")
        
        return basic_response
    
    async def _enhance_data_with_llm(self, data: Dict[str, Any], request: FieldRequest) -> Dict[str, Any]:
        """Use LLM to enhance scraped data"""
        if not self.llm_client:
            return data
        
        enhanced_data = data.copy()
        
        # Create context for LLM
        context = f"""
        University: {request.university_name}
        Requested fields: {[f.value for f in request.fields]}
        Current data: {json.dumps(data, indent=2)}
        
        Please enhance this data by:
        1. Extracting missing information from the provided data
        2. Structuring the data better
        3. Adding any relevant insights
        4. Validating the data for accuracy
        """
        
        prompt = f"""
        Analyze the university data and enhance it. Focus on the requested fields: {[f.value for f in request.fields]}.
        
        Return the enhanced data as a JSON object with the same structure as the input.
        """
        
        llm_response = await self.ask_llm(prompt, context)
        
        try:
            # Try to parse LLM response as JSON
            enhanced = json.loads(llm_response)
            # Merge with original data
            for key, value in enhanced.items():
                if value and (key not in enhanced_data or not enhanced_data[key]):
                    enhanced_data[key] = value
        except json.JSONDecodeError:
            logger.warning("LLM response was not valid JSON")
        
        return enhanced_data
    
    def get_available_fields(self) -> Dict[str, Dict[str, str]]:
        """Get list of available fields that can be requested"""
        return self.available_fields
    
    def get_field_schema(self) -> Dict[str, Any]:
        """Get JSON schema for field requests"""
        return {
            "type": "object",
            "properties": {
                "university_name": {
                    "type": "string",
                    "description": "Name of the university to research"
                },
                "fields": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "enum": list(self.available_fields.keys())
                    },
                    "description": "List of field categories to collect"
                },
                "priority": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 5,
                    "default": 1,
                    "description": "Priority level (1=highest, 5=lowest)"
                },
                "source_url": {
                    "type": "string",
                    "format": "uri",
                    "description": "Optional specific website URL to scrape"
                }
            },
            "required": ["university_name", "fields"]
        }
    
    async def process_field_request(self, request: FieldRequest) -> FieldResponse:
        """
        Process a field request from an LLM
        
        Args:
            request: FieldRequest object with university name and requested fields
            
        Returns:
            FieldResponse with collected data
        """
        try:
            # Initialize scraper
            await self._initialize_scraper()
            
            # Search for university website
            if isinstance(self.scraper, BrowserUseScraper):
                # Use Browser Use scraper
                async with self.scraper as browser_scraper:
                    search_results = await browser_scraper.search_university(request.university_name)
            else:
                # Use Selenium scraper
                search_results = self.scraper.search_university(request.university_name)
            
            if not search_results:
                return FieldResponse(
                    university_name=request.university_name,
                    fields={},
                    confidence_score=0.0,
                    source_url="",
                    scraped_at="",
                    status="failed"
                )
            
            # Use provided URL or best search result
            target_url = request.source_url or search_results[0]["url"]
            
            # Scrape university website
            if isinstance(self.scraper, BrowserUseScraper):
                # Use Browser Use scraper
                async with self.scraper as browser_scraper:
                    scraped_data = await browser_scraper.scrape_university_website(target_url)
            else:
                # Use Selenium scraper
                scraped_data = self.scraper.scrape_university_website(target_url)
            
            if not scraped_data:
                return FieldResponse(
                    university_name=request.university_name,
                    fields={},
                    confidence_score=0.0,
                    source_url=target_url,
                    scraped_at="",
                    status="failed"
                )
            
            # Filter data based on requested fields
            filtered_data = self._filter_data_by_fields(scraped_data, request.fields)
            
            # Calculate confidence score
            confidence = self._calculate_confidence(filtered_data, request.fields)
            
            return FieldResponse(
                university_name=scraped_data.get("name", request.university_name),
                fields=filtered_data,
                confidence_score=confidence,
                source_url=target_url,
                scraped_at=datetime.now().isoformat(),
                status="success" if confidence > 0.5 else "partial"
            )
            
        except Exception as e:
            logger.error(f"Error processing field request for {request.university_name}: {e}")
            return FieldResponse(
                university_name=request.university_name,
                fields={},
                confidence_score=0.0,
                source_url="",
                scraped_at="",
                status="failed"
            )
    
    def _filter_data_by_fields(self, data: Dict[str, Any], requested_fields: List[FieldType]) -> Dict[str, Any]:
        """Filter scraped data based on requested fields"""
        filtered_data = {}
        
        field_mapping = {
            FieldType.BASIC_INFO: ["name", "website", "country", "city", "state"],
            FieldType.CONTACT: ["contact_info"],
            FieldType.ACADEMIC: ["academic_info"],
            FieldType.STATISTICS: ["statistics"],
            FieldType.PROGRAMS: ["programs"],
            FieldType.FACILITIES: ["facilities"],
            FieldType.ABOUT: ["about"]
        }
        
        for field_type in requested_fields:
            if field_type == FieldType.ALL:
                filtered_data.update(data)
                break
            
            field_keys = field_mapping.get(field_type, [])
            for key in field_keys:
                if key in data:
                    filtered_data[key] = data[key]
        
        return filtered_data
    
    def _calculate_confidence(self, data: Dict[str, Any], requested_fields: List[FieldType]) -> float:
        """Calculate confidence score based on data completeness"""
        if not data:
            return 0.0
        
        total_fields = 0
        filled_fields = 0
        
        for field_type in requested_fields:
            if field_type == FieldType.ALL:
                # Count all available fields
                for field_category in self.available_fields.values():
                    total_fields += len(field_category)
                    for field_name in field_category:
                        if self._has_field_data(data, field_name):
                            filled_fields += 1
                break
            else:
                # Count fields in specific category
                field_category = self.available_fields.get(field_type.value, {})
                total_fields += len(field_category)
                for field_name in field_category:
                    if self._has_field_data(data, field_name):
                        filled_fields += 1
        
        if total_fields == 0:
            return 0.0
        
        return filled_fields / total_fields
    
    def _has_field_data(self, data: Dict[str, Any], field_name: str) -> bool:
        """Check if field has meaningful data"""
        # Navigate through nested dictionaries
        keys = field_name.split('.')
        current = data
        
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return False
        
        # Check if the value is meaningful
        if current is None:
            return False
        if isinstance(current, str) and not current.strip():
            return False
        if isinstance(current, (list, dict)) and not current:
            return False
        
        return True
    
    def close(self):
        """Close the server and cleanup resources"""
        if self.scraper:
            self.scraper.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

# Example usage and API endpoints
class UniversityMCPServerAPI:
    """API wrapper for the MCP server"""
    
    def __init__(self):
        self.server = UniversityMCPServer()
    
    async def handle_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming request from LLM"""
        try:
            # Parse request
            university_name = request_data.get("university_name")
            fields = [FieldType(field) for field in request_data.get("fields", [])]
            priority = request_data.get("priority", 1)
            source_url = request_data.get("source_url")
            
            # Create field request
            field_request = FieldRequest(
                university_name=university_name,
                fields=fields,
                priority=priority,
                source_url=source_url
            )
            
            # Process request
            response = await self.server.process_field_request_with_llm(field_request)
            
            return {
                "status": "success",
                "data": asdict(response)
            }
            
        except Exception as e:
            logger.error(f"Error handling request: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    def get_schema(self) -> Dict[str, Any]:
        """Get the schema for requests"""
        return {
            "available_fields": self.server.get_available_fields(),
            "request_schema": self.server.get_field_schema()
        }
    
    def close(self):
        """Close the API server"""
        self.server.close() 