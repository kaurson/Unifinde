#!/usr/bin/env python3
"""
Hybrid Batch University Data Collection Script
Combines LLM knowledge with targeted web scraping for critical missing fields
"""

import asyncio
import csv
import json
import sys
import os
import argparse
import time
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import logging
from dataclasses import dataclass
from rich.console import Console
from rich.table import Table
import signal
import re
from urllib.parse import urljoin, urlparse

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv('.env')

from openai import AsyncOpenAI
from sqlalchemy.orm import Session
from database.models import UniversityDataCollectionResult
from database.database import get_db

# Import browser tools for targeted scraping
from browser_tools.university_scraper import UniversityDataScraper

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('batch_university_collection_hybrid.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class UniversityEntry:
    """Represents a university entry from the CSV"""
    rank: Optional[float]
    name: str
    country: str
    student_population: Optional[float]
    students_to_staff_ratio: Optional[float]
    international_students: Optional[str]
    female_to_male_ratio: Optional[str]
    overall_score: Optional[float]
    year: Optional[int]
    
    @classmethod
    def from_csv_row(cls, row: Dict[str, str]) -> 'UniversityEntry':
        """Create UniversityEntry from CSV row"""
        return cls(
            rank=float(row.get('Rank', 0)) if row.get('Rank') else None,
            name=row.get('Name', '').strip(),
            country=row.get('Country', '').strip(),
            student_population=float(row.get('Student Population', 0)) if row.get('Student Population') else None,
            students_to_staff_ratio=float(row.get('Students to Staff Ratio', 0)) if row.get('Students to Staff Ratio') else None,
            international_students=row.get('International Students', '').strip(),
            female_to_male_ratio=row.get('Female to Male Ratio', '').strip(),
            overall_score=float(row.get('Overall Score', 0)) if row.get('Overall Score') else None,
            year=int(row.get('Year', 0)) if row.get('Year') else None
        )

class HybridBatchUniversityCollector:
    """Hybrid batch university data collector using LLM + targeted web scraping"""
    
    def __init__(self, openai_api_key: str = None):
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        if not self.openai_api_key:
            raise ValueError("OpenAI API key is required. Set OPENAI_API_KEY environment variable or pass it to the constructor.")
        
        self.console = Console()
        self.openai_client = AsyncOpenAI(api_key=self.openai_api_key)
        self.db_session = next(get_db())
        self.results = []
        self.start_time = None
        self.interrupted = False
        
        # Initialize browser scraper for targeted scraping
        self.scraper = UniversityDataScraper()
        
        # Set up signal handler for graceful interruption
        signal.signal(signal.SIGINT, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle Ctrl+C gracefully"""
        self.interrupted = True
        self.console.print("\n[red]⚠️  Interruption detected. Finishing current university and stopping gracefully...[/red]")
    
    def load_universities_from_csv(self, csv_file: str, limit: Optional[int] = None, 
                                 start_rank: Optional[int] = None, 
                                 end_rank: Optional[int] = None,
                                 countries: Optional[List[str]] = None) -> List[UniversityEntry]:
        """Load universities from CSV file with filtering options"""
        universities = []
        
        try:
            with open(csv_file, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                
                for row in reader:
                    # Apply rank filters
                    if start_rank is not None:
                        try:
                            rank = float(row.get('Rank', 0))
                            if rank < start_rank:
                                continue
                        except (ValueError, TypeError):
                            continue
                    
                    if end_rank is not None:
                        try:
                            rank = float(row.get('Rank', 0))
                            if rank > end_rank:
                                continue
                        except (ValueError, TypeError):
                            continue
                    
                    # Apply country filter
                    if countries and row.get('Country', '').strip() not in countries:
                        continue
                    
                    # Create university entry
                    university = UniversityEntry.from_csv_row(row)
                    universities.append(university)
                    
                    # Apply limit
                    if limit and len(universities) >= limit:
                        break
        
        except Exception as e:
            self.console.print(f"[red]❌ Error loading CSV file: {e}[/red]")
            return []
        
        return universities
    
    def create_summary_table(self, universities: List[UniversityEntry]) -> Table:
        """Create a summary table of universities to be processed"""
        table = Table(title="Universities to Process")
        table.add_column("Rank", style="cyan", no_wrap=True)
        table.add_column("Name", style="magenta")
        table.add_column("Country", style="green")
        table.add_column("Students", style="yellow", no_wrap=True)
        table.add_column("Score", style="blue", no_wrap=True)
        
        for uni in universities:
            table.add_row(
                str(uni.rank) if uni.rank else "N/A",
                uni.name,
                uni.country,
                f"{uni.student_population:,}" if uni.student_population else "N/A",
                f"{uni.overall_score:.1f}" if uni.overall_score else "N/A"
            )
        
        return table
    
    async def collect_university_data_llm_base(self, university_name: str) -> Dict[str, Any]:
        """Collect university data using LLM knowledge as base"""
        
        try:
            self.console.print(f"🧠 Collecting base data for {university_name} using LLM...")
            
            # Use LLM to generate comprehensive university information
            prompt = f"""
You are a university data expert. For {university_name}, please provide comprehensive information in JSON format including:

1. Official website URL (common patterns like .edu domains)
2. Contact information (email, phone)
3. Location details (city, state, country)
4. Basic statistics (student population, faculty count, etc.)
5. Academic programs and rankings
6. Financial information (tuition, costs, financial aid)
7. International student services

CRITICAL: For numeric fields, provide actual numbers only. Do NOT use text like "info not provided", "N/A", "unknown", etc. If you don't know a value, use null or omit the field entirely.

IMPORTANT: Be conservative with your data. Only provide information you are confident about. It's better to leave a field as null than to provide incorrect information.

SPECIAL ATTENTION: The following fields are particularly difficult to find but very valuable:
- tuition_domestic: Annual tuition for domestic students (in USD if possible)
- tuition_international: Annual tuition for international students (in USD if possible)
- acceptance_rate: Percentage of applicants accepted (e.g., 15.5 for 15.5%)
- total_cost_of_attendance: Total annual cost including tuition, room, board, fees
- room_and_board: Annual cost for housing and meals
- average_financial_aid_package: Average financial aid amount per student
- regional_ranking: Regional ranking (e.g., Asia, Europe, North America)

Return the data in this JSON format:
{{
    "name": "{university_name}",
    "website": "string",
    "country": "string",
    "city": "string",
    "state": "string",
    "phone": "string",
    "email": "string",
    "founded_year": integer or null,
    "type": "string",
    "student_population": integer or null,
    "undergraduate_population": integer or null,
    "graduate_population": integer or null,
    "international_students_percentage": float or null,
    "faculty_count": integer or null,
    "student_faculty_ratio": float or null,
    "acceptance_rate": float or null,
    "tuition_domestic": float or null,
    "tuition_international": float or null,
    "room_and_board": float or null,
    "total_cost_of_attendance": float or null,
    "financial_aid_available": boolean or null,
    "average_financial_aid_package": float or null,
    "scholarships_available": boolean or null,
    "world_ranking": integer or null,
    "national_ranking": integer or null,
    "regional_ranking": integer or null,
    "subject_rankings": {{
        "engineering": integer or null,
        "business": integer or null,
        "computer_science": integer or null,
        "medicine": integer or null,
        "law": integer or null,
        "arts": integer or null,
        "sciences": integer or null
    }},
    "description": "string",
    "mission_statement": "string",
    "vision_statement": "string",
    "campus_size": "string",
    "campus_type": "string",
    "climate": "string",
    "timezone": "string",
    "programs": [
        {{
            "name": "string",
            "level": "string",
            "field": "string",
            "department": "string",
            "duration": "string",
            "tuition": float or null,
            "description": "string",
            "requirements": "string",
            "career_outcomes": "string",
            "accreditation": "string",
            "enrollment_capacity": integer or null,
            "available": boolean or null
        }}
    ],
    "student_life": {{
        "housing_options": ["string"],
        "student_organizations": integer or null,
        "sports_teams": ["string"],
        "campus_activities": ["string"],
        "health_services": boolean or null,
        "counseling_services": boolean or null
    }},
    "financial_aid": {{
        "need_based_aid": boolean or null,
        "merit_based_aid": boolean or null,
        "scholarships": [
            {{
                "name": "string",
                "amount": float or null,
                "eligibility": "string",
                "application_required": boolean or null
            }}
        ],
        "grants": ["string"],
        "work_study_available": boolean or null,
        "loan_options": ["string"]
    }},
    "international_students": {{
        "international_office": boolean or null,
        "english_language_requirements": ["string"],
        "visa_support": boolean or null,
        "international_student_services": ["string"],
        "cultural_programs": ["string"]
    }},
    "alumni": {{
        "alumni_network_size": integer or null,
        "notable_alumni": ["string"],
        "alumni_association": boolean or null,
        "alumni_events": integer or null
    }},
    "confidence_score": float,
    "source_urls": ["string"],
    "last_updated": "string"
}}
"""
            
            response = await self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a university data expert. Provide comprehensive information about universities in JSON format."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=3000
            )
            
            llm_response = response.choices[0].message.content.strip()
            
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
                
                return {
                    "success": True,
                    "data": structured_data,
                    "confidence_score": 0.6  # Base confidence for LLM data
                }
                
            except json.JSONDecodeError as e:
                self.console.print(f"❌ Error parsing LLM response: {e}")
                return {
                    "success": False,
                    "error": f"JSON parsing error: {e}"
                }
                
        except Exception as e:
            self.console.print(f"❌ Error collecting LLM data for {university_name}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def enhance_with_web_scraping(self, university_name: str, llm_data: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance LLM data with targeted web scraping for critical missing fields"""
        
        try:
            self.console.print(f"🌐 Enhancing data for {university_name} with web scraping...")
            
            # Get website from LLM data
            website = llm_data.get('website', '')
            if not website:
                self.console.print(f"   ⚠️  No website found, attempting web search anyway...")
            
            # Define critical fields to enhance - prioritized by database analysis
            critical_fields = [
                # Financial data (hardest to get)
                'tuition_domestic', 'tuition_international', 'total_cost_of_attendance',
                'room_and_board', 'average_financial_aid_package',
                
                # Admissions data
                'acceptance_rate',
                
                # Rankings (regional is hardest)
                'regional_ranking',
                
                # Basic stats
                'student_population', 'faculty_count'
            ]
            
            # Check which critical fields are missing or need enhancement
            missing_fields = []
            for field in critical_fields:
                if not llm_data.get(field) or llm_data.get(field) == 0:
                    missing_fields.append(field)
            
            if not missing_fields:
                self.console.print(f"   ✅ All critical fields present, attempting web enhancement for accuracy...")
                # Still try web scraping to improve accuracy of existing data
                missing_fields = critical_fields
            
            self.console.print(f"   🔍 Attempting web enhancement for fields: {', '.join(missing_fields)}")
            
            # Try to scrape official website for missing data
            try:
                # Use the existing scraper to get additional data
                scraped_data = await self.scraper.collect_university_data(university_name)
                
                if scraped_data.get("success"):
                    extracted_data = scraped_data.get("extracted_data", {})
                    
                    # Merge scraped data with LLM data, prioritizing scraped data for critical fields
                    enhanced_data = llm_data.copy()
                    enhanced_count = 0
                    
                    for field in critical_fields:
                        if field in extracted_data and extracted_data[field]:
                            # Only enhance if the scraped data is different/better than LLM data
                            llm_value = llm_data.get(field)
                            scraped_value = extracted_data[field]
                            
                            # If LLM data is missing or scraped data is more specific
                            if not llm_value or (scraped_value and scraped_value != llm_value):
                                enhanced_data[field] = scraped_value
                                enhanced_count += 1
                                self.console.print(f"   ✅ Enhanced {field}: {scraped_value} (was: {llm_value})")
                    
                    # Update confidence score based on enhancement
                    if enhanced_count > 0:
                        # Higher confidence boost for financial/admissions data
                        confidence_boost = 0.0
                        for field in ['tuition_domestic', 'tuition_international', 'acceptance_rate', 'total_cost_of_attendance']:
                            if field in enhanced_data and enhanced_data[field] != llm_data.get(field):
                                confidence_boost += 0.08  # Higher boost for hard-to-get data
                        
                        enhanced_data['confidence_score'] = min(0.95, 0.6 + confidence_boost + (enhanced_count * 0.03))
                        self.console.print(f"   📈 Enhanced {enhanced_count} fields, confidence: {enhanced_data['confidence_score']:.2f}")
                    else:
                        enhanced_data['confidence_score'] = 0.7  # Good LLM data, no web enhancement needed
                        self.console.print(f"   📊 No field enhancements needed, confidence: {enhanced_data['confidence_score']:.2f}")
                    
                    return enhanced_data
                else:
                    self.console.print(f"   ⚠️  Web scraping failed, using LLM data only")
                    llm_data['confidence_score'] = 0.6  # Base confidence for LLM-only data
                    return llm_data
                    
            except Exception as e:
                self.console.print(f"   ⚠️  Web scraping error: {e}")
                llm_data['confidence_score'] = 0.6  # Base confidence for LLM-only data
                return llm_data
                
        except Exception as e:
            self.console.print(f"❌ Error in web enhancement for {university_name}: {e}")
            llm_data['confidence_score'] = 0.6  # Base confidence for LLM-only data
            return llm_data
    
    async def collect_university_data_hybrid(self, university_name: str) -> Dict[str, Any]:
        """Collect university data using hybrid approach (LLM + targeted web scraping)"""
        
        try:
            # Step 1: Get base data from LLM
            llm_result = await self.collect_university_data_llm_base(university_name)
            
            if not llm_result.get("success"):
                return llm_result
            
            llm_data = llm_result.get("data", {})
            
            # Step 2: Enhance with web scraping for critical missing fields
            enhanced_data = await self.enhance_with_web_scraping(university_name, llm_data)
            
            # Step 3: Save to database
            return await self.save_to_database(enhanced_data)
            
        except Exception as e:
            self.console.print(f"❌ Error in hybrid collection for {university_name}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def save_to_database(self, structured_data: Dict[str, Any]) -> Dict[str, Any]:
        """Save enhanced data to database"""
        
        try:
            # Helper function to safely convert values
            def safe_int(value):
                """Safely convert value to integer, return None if invalid"""
                if value is None:
                    return None
                if isinstance(value, int):
                    return value
                if isinstance(value, str):
                    # Remove common text that indicates missing data
                    value = value.lower().strip()
                    if value in ['', 'n/a', 'none', 'null', 'info not provided', 'not available', 'unknown']:
                        return None
                    try:
                        return int(float(value))
                    except (ValueError, TypeError):
                        return None
                try:
                    return int(float(value))
                except (ValueError, TypeError):
                    return None
            
            def safe_float(value):
                """Safely convert value to float, return None if invalid"""
                if value is None:
                    return None
                if isinstance(value, (int, float)):
                    return float(value)
                if isinstance(value, str):
                    # Remove common text that indicates missing data
                    value = value.lower().strip()
                    if value in ['', 'n/a', 'none', 'null', 'info not provided', 'not available', 'unknown']:
                        return None
                    try:
                        return float(value)
                    except (ValueError, TypeError):
                        return None
                try:
                    return float(value)
                except (ValueError, TypeError):
                    return None
            
            def safe_bool(value):
                """Safely convert value to boolean, return None if invalid"""
                if value is None:
                    return None
                if isinstance(value, bool):
                    return value
                if isinstance(value, str):
                    value = value.lower().strip()
                    if value in ['true', 'yes', '1', 'available']:
                        return True
                    elif value in ['false', 'no', '0', 'not available']:
                        return False
                    else:
                        return None
                return bool(value) if value is not None else None
            
            confidence_score = structured_data.get('confidence_score', 0.6)
            
            # Save to database with proper data validation
            result_data = {
                'total_universities': 1,
                'successful_collections': 1,
                'failed_collections': 0,
                'generated_at': datetime.now(),
                'script_version': '1.0.0-hybrid',
                'success': True,
                'data_collection_id': None,
                'name': structured_data.get('name'),
                'website': structured_data.get('website'),
                'country': structured_data.get('country'),
                'city': structured_data.get('city'),
                'state': structured_data.get('state'),
                'phone': structured_data.get('phone'),
                'email': structured_data.get('email'),
                'founded_year': safe_int(structured_data.get('founded_year')),
                'type': structured_data.get('type'),
                'student_population': safe_int(structured_data.get('student_population')),
                'undergraduate_population': safe_int(structured_data.get('undergraduate_population')),
                'graduate_population': safe_int(structured_data.get('graduate_population')),
                'international_students_percentage': safe_float(structured_data.get('international_students_percentage')),
                'faculty_count': safe_int(structured_data.get('faculty_count')),
                'student_faculty_ratio': safe_float(structured_data.get('student_faculty_ratio')),
                'acceptance_rate': safe_float(structured_data.get('acceptance_rate')),
                'tuition_domestic': safe_float(structured_data.get('tuition_domestic')),
                'tuition_international': safe_float(structured_data.get('tuition_international')),
                'room_and_board': safe_float(structured_data.get('room_and_board')),
                'total_cost_of_attendance': safe_float(structured_data.get('total_cost_of_attendance')),
                'financial_aid_available': safe_bool(structured_data.get('financial_aid_available')),
                'average_financial_aid_package': safe_float(structured_data.get('average_financial_aid_package')),
                'scholarships_available': safe_bool(structured_data.get('scholarships_available')),
                'world_ranking': safe_int(structured_data.get('world_ranking')),
                'national_ranking': safe_int(structured_data.get('national_ranking')),
                'regional_ranking': safe_int(structured_data.get('regional_ranking')),
                'subject_rankings': json.dumps(structured_data.get('subject_rankings', {})) if structured_data.get('subject_rankings') else None,
                'description': structured_data.get('description'),
                'mission_statement': structured_data.get('mission_statement'),
                'vision_statement': structured_data.get('vision_statement'),
                'campus_size': structured_data.get('campus_size'),
                'campus_type': structured_data.get('campus_type'),
                'climate': structured_data.get('climate'),
                'timezone': structured_data.get('timezone'),
                'programs': json.dumps(structured_data.get('programs', [])) if structured_data.get('programs') else None,
                'student_life': json.dumps(structured_data.get('student_life', {})) if structured_data.get('student_life') else None,
                'financial_aid': json.dumps(structured_data.get('financial_aid', {})) if structured_data.get('financial_aid') else None,
                'international_students': json.dumps(structured_data.get('international_students', {})) if structured_data.get('international_students') else None,
                'alumni': json.dumps(structured_data.get('alumni', {})) if structured_data.get('alumni') else None,
                'confidence_score': confidence_score,
                'source_urls': json.dumps(structured_data.get('source_urls', [])) if structured_data.get('source_urls') else None,
                'last_updated': datetime.now().strftime('%Y-%m-%d')
            }
            
            # Create and save the result record
            result_record = UniversityDataCollectionResult(**result_data)
            self.db_session.add(result_record)
            
            try:
                self.db_session.commit()
                self.console.print(f"✅ Results saved to database with ID: {result_record.id}")
            except Exception as db_error:
                # Rollback the session and try again
                self.console.print(f"⚠️  Database error, rolling back and retrying: {db_error}")
                self.db_session.rollback()
                
                # Try to commit again
                try:
                    self.db_session.add(result_record)
                    self.db_session.commit()
                    self.console.print(f"✅ Results saved to database with ID: {result_record.id} (retry successful)")
                except Exception as retry_error:
                    self.console.print(f"❌ Database retry failed: {retry_error}")
                    self.db_session.rollback()
                    return {
                        "success": False,
                        "error": f"Database save failed: {retry_error}"
                    }
            
            return {
                "success": True,
                "result_record_id": result_record.id,
                "extracted_data": structured_data,
                "confidence_score": confidence_score,
                "source_urls": structured_data.get("source_urls", [])
            }
            
        except Exception as e:
            self.console.print(f"❌ Error saving to database: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def collect_universities_batch(self, universities: List[UniversityEntry], 
                                       delay: int = 3, save_progress: bool = True, 
                                       max_retries: int = 2, max_concurrent: int = 2) -> List[Dict[str, Any]]:
        """Collect data for multiple universities with parallel processing"""
        
        self.start_time = time.time()
        results = []
        successful = 0
        failed = 0
        skipped = 0
        
        # Create semaphore to limit concurrent operations (lower for hybrid approach)
        semaphore = asyncio.Semaphore(max_concurrent)
        
        self.console.print(f"\n🎓 Hybrid Batch University Data Collection")
        self.console.print(f"Processing {len(universities)} universities with {delay}s delay")
        self.console.print(f"🔄 Max concurrent operations: {max_concurrent}")
        self.console.print(f"🔄 Max retries per university: {max_retries}")
        self.console.print(f"🧠 Using hybrid approach (LLM + targeted web scraping)")
        
        # Create tasks for all universities
        tasks = []
        for i, university in enumerate(universities):
            task = asyncio.create_task(
                self._process_single_university_with_semaphore(
                    university, i + 1, len(universities), max_retries, delay, semaphore
                )
            )
            tasks.append(task)
            # Small delay between task creation to stagger starts
            await asyncio.sleep(0.5)
        
        # Process results as they complete
        completed = 0
        for task in asyncio.as_completed(tasks):
            try:
                result = await task
                results.append(result)
                completed += 1
                
                if result.get("success"):
                    successful += 1
                elif result.get("skipped"):
                    skipped += 1
                else:
                    failed += 1
                
                # Update progress
                avg_confidence = sum(r.get("confidence_score", 0) for r in results if r.get("success")) / max(successful, 1)
                eta_seconds = (len(universities) - completed) * (delay + 15) / max_concurrent  # Rough estimate
                eta = timedelta(seconds=int(eta_seconds))
                
                self.console.print(f"📊 Progress: {successful} successful, {failed} failed, {skipped} skipped ({completed/len(universities)*100:.1f}%) | Avg Confidence: {avg_confidence:.2f} | ETA: {eta} | Completed: {completed}/{len(universities)}")
                
            except Exception as e:
                self.console.print(f"❌ Task failed: {e}")
                failed += 1
                completed += 1
        
        return results
    
    async def _process_single_university_with_semaphore(self, university: UniversityEntry, index: int, total: int,
                                                       max_retries: int, delay: int, semaphore: asyncio.Semaphore) -> Dict[str, Any]:
        """Process a single university with semaphore control"""
        async with semaphore:
            return await self._process_single_university(university, index, total, max_retries, delay)
    
    async def _process_single_university(self, university: UniversityEntry, index: int, total: int,
                                       max_retries: int, delay: int) -> Dict[str, Any]:
        """Process a single university with retry logic"""
        
        self.console.print(f"\n📚 University {index}/{total}: {university.name}")
        self.console.print(f"   Country: {university.country} | Rank: {university.rank} | Students: {university.student_population:,}" if university.student_population else f"   Country: {university.country} | Rank: {university.rank} | Students: N/A")
        
        # Check if university already exists
        if self.check_university_exists(university.name):
            existing_info = self.get_existing_university_info(university.name)
            self.console.print(f"   ⏭️  Skipping {university.name} (already exists in database)")
            return {
                "success": True,
                "skipped": True,
                "university_name": university.name,
                "reason": "Already exists in database",
                "existing_data": existing_info
            }
        
        # Retry logic for API issues
        for attempt in range(max_retries):
            try:
                logger.info(f"Starting hybrid data collection for: {university.name}")
                
                # Collect data using hybrid approach
                result = await self.collect_university_data_hybrid(university.name)
                
                if result.get("success"):
                    confidence_score = result.get("confidence_score", 0.0)
                    self.console.print(f"✅ Success! Confidence: {confidence_score:.2f}")
                    
                    # Log detailed information
                    extracted_data = result.get("extracted_data", {})
                    logger.info(f"✅ Successfully collected data for {university.name}")
                    logger.info(f"   Confidence Score: {confidence_score:.2f}")
                    logger.info(f"   Collection ID: {result.get('result_record_id')}")
                    logger.info(f"   Name: {extracted_data.get('name', 'N/A')}")
                    logger.info(f"   Website: {extracted_data.get('website', 'N/A')}")
                    logger.info(f"   Location: {extracted_data.get('city', 'N/A')}, {extracted_data.get('state', 'N/A')}")
                    logger.info(f"   Student Population: {extracted_data.get('student_population', 'N/A')}")
                    logger.info(f"   Acceptance Rate: {extracted_data.get('acceptance_rate', 'N/A')}")
                    
                    return {
                        "success": True,
                        "university_name": university.name,
                        "confidence_score": confidence_score,
                        "result_record_id": result.get("result_record_id"),
                        "source_urls": result.get("source_urls", []),
                        "extracted_data": extracted_data,
                        "csv_data": {
                            "rank": university.rank,
                            "country": university.country,
                            "student_population": university.student_population,
                            "overall_score": university.overall_score,
                            "year": university.year
                        }
                    }
                else:
                    error_msg = result.get("error", "Unknown error")
                    self.console.print(f"❌ Failed: {error_msg}")
                    
                    if attempt < max_retries - 1:
                        self.console.print(f"⏳ Waiting before retry...")
                        await asyncio.sleep(delay * 2)  # Longer delay for retries
                        self.console.print(f"🔄 Retry attempt {attempt + 2}/{max_retries} for {university.name}")
                    else:
                        logger.error(f"❌ Error collecting data for {university.name}: {error_msg}")
                        return {
                            "success": False,
                            "university_name": university.name,
                            "error": error_msg,
                            "attempts": attempt + 1
                        }
                        
            except Exception as e:
                error_msg = str(e)
                self.console.print(f"❌ Unexpected error: {error_msg}")
                
                if attempt < max_retries - 1:
                    self.console.print(f"⏳ Waiting before retry...")
                    await asyncio.sleep(delay * 2)
                    self.console.print(f"🔄 Retry attempt {attempt + 2}/{max_retries} for {university.name}")
                else:
                    logger.error(f"❌ Error collecting data for {university.name}: {error_msg}")
                    return {
                        "success": False,
                        "university_name": university.name,
                        "error": error_msg,
                        "attempts": attempt + 1
                    }
        
        # If we get here, all retries failed
        return {
            "success": False,
            "university_name": university.name,
            "error": "All retry attempts failed",
            "attempts": max_retries
        }
    
    def save_progress(self, results: List[Dict[str, Any]], filename: str = None) -> str:
        """Save progress to JSON file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"output/batch_university_collection_hybrid_{timestamp}.json"
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        # Calculate statistics
        successful = len([r for r in results if r.get("success") and not r.get("skipped")])
        failed = len([r for r in results if not r.get("success")])
        skipped = len([r for r in results if r.get("skipped")])
        
        # Create output structure
        output_data = {
            "metadata": {
                "total_universities": len(results),
                "successful_collections": successful,
                "failed_collections": failed,
                "skipped_collections": skipped,
                "generated_at": datetime.now().isoformat(),
                "script_version": "1.0.0-hybrid"
            },
            "results": results
        }
        
        # Save to file
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False, default=str)
        
        return filename
    
    def print_final_summary(self, results: List[Dict[str, Any]], universities: List[UniversityEntry]):
        """Print final summary of the collection process"""
        
        # Calculate statistics
        successful = len([r for r in results if r.get("success") and not r.get("skipped")])
        failed = len([r for r in results if not r.get("success")])
        skipped = len([r for r in results if r.get("skipped")])
        
        # Calculate average confidence
        confidence_scores = [r.get("confidence_score", 0) for r in results if r.get("success") and not r.get("skipped")]
        avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0
        
        # Calculate timing
        total_time = time.time() - self.start_time if self.start_time else 0
        avg_time_per_uni = total_time / len(universities) if universities else 0
        
        # Create summary table
        summary_table = Table(title="Final Collection Summary")
        summary_table.add_column("Metric", style="cyan")
        summary_table.add_column("Value", style="green")
        
        summary_table.add_row("Total Universities", str(len(universities)))
        summary_table.add_row("Processed", str(len(results)))
        summary_table.add_row("Successful", f"{successful} ({successful/len(universities)*100:.1f}%)" if universities else "0")
        summary_table.add_row("Failed", str(failed))
        summary_table.add_row("Skipped (Already Exist)", str(skipped))
        summary_table.add_row("Average Confidence", f"{avg_confidence:.2f}")
        summary_table.add_row("Total Time", str(timedelta(seconds=int(total_time))))
        summary_table.add_row("Avg Time per University", f"{avg_time_per_uni:.1f}s")
        
        self.console.print(summary_table)
    
    def close(self):
        """Clean up resources"""
        if self.db_session:
            self.db_session.close()
    
    def check_university_exists(self, university_name: str) -> bool:
        """Check if university already exists in database"""
        try:
            # Check if university exists in the database
            existing = self.db_session.query(UniversityDataCollectionResult).filter(
                UniversityDataCollectionResult.name.ilike(f"%{university_name}%")
            ).first()
            return existing is not None
        except Exception as e:
            logger.error(f"Error checking if university exists: {e}")
            return False
    
    def get_existing_university_info(self, university_name: str) -> Dict[str, Any]:
        """Get information about existing university"""
        try:
            existing = self.db_session.query(UniversityDataCollectionResult).filter(
                UniversityDataCollectionResult.name.ilike(f"%{university_name}%")
            ).first()
            if existing:
                return {
                    "confidence_score": existing.confidence_score,
                    "website": existing.website
                }
            return {
                "confidence_score": 0.0,
                "website": "N/A"
            }
        except Exception as e:
            logger.error(f"Error getting existing university info: {e}")
            return {}

async def main():
    """Main function for hybrid command-line usage"""
    parser = argparse.ArgumentParser(
        description="Hybrid Batch University Data Collection Script (LLM + Targeted Web Scraping)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process top 20 universities using hybrid approach (skips existing)
  python batch_university_collector_hybrid.py "THE World University Rankings 2016-2025.csv" --limit 20
  
  # Process with higher concurrency
  python batch_university_collector_hybrid.py "THE World University Rankings 2016-2025.csv" --limit 50 --max-concurrent 3
  
  # Process specific countries
  python batch_university_collector_hybrid.py "THE World University Rankings 2016-2025.csv" --countries "United States" "United Kingdom"
        """
    )
    
    parser.add_argument(
        "csv_file",
        help="CSV file containing university data"
    )
    
    parser.add_argument(
        "--limit", "-l",
        type=int,
        help="Limit number of universities to process"
    )
    
    parser.add_argument(
        "--start-rank", "-s",
        type=int,
        help="Start processing from this rank (inclusive)"
    )
    
    parser.add_argument(
        "--end-rank", "-e",
        type=int,
        help="End processing at this rank (inclusive)"
    )
    
    parser.add_argument(
        "--countries", "-c",
        nargs="+",
        help="Only process universities from these countries"
    )
    
    parser.add_argument(
        "--delay", "-d",
        type=int,
        default=3,
        help="Delay between universities in seconds (default: 3)"
    )
    
    parser.add_argument(
        "--output", "-o",
        help="Output JSON file name (default: auto-generated with timestamp)"
    )
    
    parser.add_argument(
        "--openai-key",
        help="OpenAI API key (or set OPENAI_API_KEY environment variable)"
    )
    
    parser.add_argument(
        "--no-save-progress",
        action="store_true",
        help="Don't save progress checkpoints"
    )
    
    parser.add_argument(
        "--max-retries",
        type=int,
        default=2,
        help="Maximum number of retry attempts per university (default: 2)"
    )
    
    parser.add_argument(
        "--max-concurrent",
        type=int,
        default=2,
        help="Maximum number of concurrent university processing operations (default: 2)"
    )
    
    args = parser.parse_args()
    
    # Validate CSV file
    csv_path = Path(args.csv_file)
    if not csv_path.exists():
        parser.error(f"CSV file not found: {args.csv_file}")
    
    # Initialize collector
    try:
        collector = HybridBatchUniversityCollector(openai_api_key=args.openai_key)
    except ValueError as e:
        print(f"❌ {e}")
        sys.exit(1)
    
    try:
        # Load universities from CSV
        console = Console()
        console.print(f"[blue]📖 Loading universities from: {args.csv_file}[/blue]")
        
        universities = collector.load_universities_from_csv(
            args.csv_file,
            limit=args.limit,
            start_rank=args.start_rank,
            end_rank=args.end_rank,
            countries=args.countries
        )
        
        if not universities:
            console.print("[red]❌ No universities found matching the criteria[/red]")
            sys.exit(1)
        
        console.print(f"[green]✅ Loaded {len(universities)} universities[/green]")
        
        # Show summary table
        summary_table = collector.create_summary_table(universities[:10])  # Show first 10
        console.print(summary_table)
        if len(universities) > 10:
            console.print(f"[yellow]... and {len(universities) - 10} more universities[/yellow]")
        
        # Start collection immediately
        console.print(f"\n[green]🎯 Starting hybrid batch collection...[/green]")
        console.print(f"[blue]🔄 Max retries per university: {args.max_retries}[/blue]")
        console.print(f"[blue]⚡ Max concurrent operations: {args.max_concurrent}[/blue]")
        console.print(f"[blue]🧠 Using hybrid approach (LLM + targeted web scraping)[/blue]")
        
        results = await collector.collect_universities_batch(
            universities, 
            delay=args.delay,
            save_progress=not args.no_save_progress,
            max_retries=args.max_retries,
            max_concurrent=args.max_concurrent
        )
        
        # Print final summary
        collector.print_final_summary(results, universities)
        
        # Save results
        if args.output:
            output_file = collector.save_progress(results, args.output)
            console.print(f"[green]✅ Results saved to: {output_file}[/green]")
        else:
            output_file = collector.save_progress(results)
            console.print(f"[green]✅ Results saved to: {output_file}[/green]")
        
        # Exit with error code if any collections failed
        failed_count = len([r for r in results if not r.get("success")])
        if failed_count > 0:
            console.print(f"[yellow]⚠️  {failed_count} collections failed[/yellow]")
            sys.exit(1)
        else:
            console.print("[green]✅ All collections completed successfully![/green]")
            
    except KeyboardInterrupt:
        console.print("\n[yellow]⚠️  Collection interrupted by user[/yellow]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]❌ Unexpected error: {e}[/red]")
        sys.exit(1)
    finally:
        collector.close()

if __name__ == "__main__":
    asyncio.run(main()) 