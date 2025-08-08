#!/usr/bin/env python3
"""
Enhanced Collection Vectorizer for UniversityDataCollectionResult table
Creates optimized text representations and vectors from the rich collection data
"""

import json
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session
import openai
import os
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnhancedCollectionVectorizer:
    def __init__(self):
        self.client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.embedding_model = "text-embedding-3-small"
        
    def create_structured_collection_text(self, collection_result: Any) -> str:
        """
        Create a structured, comprehensive text representation from collection data
        """
        sections = []
        
        # 1. Core Identity Section
        identity_parts = [f"University: {collection_result.name}"]
        
        if collection_result.type:
            identity_parts.append(f"Type: {collection_result.type}")
        
        if collection_result.founded_year:
            identity_parts.append(f"Founded: {collection_result.founded_year}")
            
        sections.append(" | ".join(identity_parts))
        
        # 2. Location Section
        location_parts = []
        if collection_result.city:
            location_parts.append(collection_result.city)
        if collection_result.state:
            location_parts.append(collection_result.state)
        if collection_result.country:
            location_parts.append(collection_result.country)
            
        if location_parts:
            sections.append(f"Location: {', '.join(location_parts)}")
        
        # 3. Academic Profile Section (Enhanced with collection data)
        academic_parts = []
        
        if collection_result.student_population:
            academic_parts.append(f"Student Population: {collection_result.student_population:,}")
        
        if collection_result.undergraduate_population:
            academic_parts.append(f"Undergraduate: {collection_result.undergraduate_population:,}")
            
        if collection_result.graduate_population:
            academic_parts.append(f"Graduate: {collection_result.graduate_population:,}")
        
        if collection_result.faculty_count:
            academic_parts.append(f"Faculty: {collection_result.faculty_count:,}")
            
        if collection_result.student_faculty_ratio:
            academic_parts.append(f"Student-Faculty Ratio: {collection_result.student_faculty_ratio:.1f}")
            
        if collection_result.acceptance_rate:
            academic_parts.append(f"Acceptance Rate: {collection_result.acceptance_rate:.1%}")
            
        if collection_result.international_students_percentage:
            academic_parts.append(f"International Students: {collection_result.international_students_percentage:.1%}")
            
        if academic_parts:
            sections.append("Academic Profile: " + " | ".join(academic_parts))
        
        # 4. Rankings Section (Enhanced)
        rankings_parts = []
        if collection_result.world_ranking:
            rankings_parts.append(f"World Rank: #{collection_result.world_ranking}")
        if collection_result.national_ranking:
            rankings_parts.append(f"National Rank: #{collection_result.national_ranking}")
        if collection_result.regional_ranking:
            rankings_parts.append(f"Regional Rank: #{collection_result.regional_ranking}")
            
        if collection_result.subject_rankings:
            try:
                subject_rankings = collection_result.subject_rankings
                if isinstance(subject_rankings, str):
                    subject_rankings = json.loads(subject_rankings)
                
                if isinstance(subject_rankings, dict):
                    top_subjects = []
                    for subject, rank in subject_rankings.items():
                        if isinstance(rank, (int, float)) and rank <= 50:  # Top 50 subjects
                            top_subjects.append(f"{subject}: #{rank}")
                        if len(top_subjects) >= 5:  # Limit to top 5
                            break
                    
                    if top_subjects:
                        rankings_parts.append(f"Top Subjects: {', '.join(top_subjects)}")
            except Exception as e:
                logger.warning(f"Error parsing subject rankings: {e}")
            
        if rankings_parts:
            sections.append("Rankings: " + " | ".join(rankings_parts))
        
        # 5. Financial Information Section (Enhanced)
        financial_parts = []
        if collection_result.tuition_domestic:
            financial_parts.append(f"Domestic Tuition: ${collection_result.tuition_domestic:,.0f}")
        if collection_result.tuition_international:
            financial_parts.append(f"International Tuition: ${collection_result.tuition_international:,.0f}")
        if collection_result.room_and_board:
            financial_parts.append(f"Room & Board: ${collection_result.room_and_board:,.0f}")
        if collection_result.total_cost_of_attendance:
            financial_parts.append(f"Total Cost: ${collection_result.total_cost_of_attendance:,.0f}")
        if collection_result.average_financial_aid_package:
            financial_parts.append(f"Avg Financial Aid: ${collection_result.average_financial_aid_package:,.0f}")
            
        if financial_parts:
            sections.append("Financial: " + " | ".join(financial_parts))
        
        # 6. Programs Section (From JSON data)
        if collection_result.programs:
            try:
                programs_data = collection_result.programs
                if isinstance(programs_data, str):
                    programs_data = json.loads(programs_data)
                
                if isinstance(programs_data, list):
                    program_names = []
                    for program in programs_data:
                        if isinstance(program, dict) and 'name' in program:
                            program_names.append(program['name'])
                        elif isinstance(program, str):
                            program_names.append(program)
                    
                    if program_names:
                        # Group by first word (field)
                        program_fields = {}
                        for program_name in program_names:
                            field = program_name.split()[0] if ' ' in program_name else program_name
                            if field not in program_fields:
                                program_fields[field] = []
                            program_fields[field].append(program_name)
                        
                        program_sections = []
                        for field, names in program_fields.items():
                            program_sections.append(f"{field}: {', '.join(names[:5])}")
                        
                        if program_sections:
                            sections.append("Academic Programs: " + " | ".join(program_sections))
                            
            except Exception as e:
                logger.warning(f"Error parsing programs: {e}")
        
        # 7. Student Life Section (From JSON data)
        if collection_result.student_life:
            try:
                student_life_data = collection_result.student_life
                if isinstance(student_life_data, str):
                    student_life_data = json.loads(student_life_data)
                
                if isinstance(student_life_data, dict):
                    life_sections = []
                    for category, items in student_life_data.items():
                        if isinstance(items, list) and items:
                            life_sections.append(f"{category}: {', '.join(items[:3])}")
                    
                    if life_sections:
                        sections.append("Student Life: " + " | ".join(life_sections))
                        
            except Exception as e:
                logger.warning(f"Error parsing student life: {e}")
        
        # 8. Campus Information Section
        campus_parts = []
        if collection_result.campus_size:
            campus_parts.append(f"Campus Size: {collection_result.campus_size}")
        if collection_result.campus_type:
            campus_parts.append(f"Campus Type: {collection_result.campus_type}")
        if collection_result.climate:
            campus_parts.append(f"Climate: {collection_result.climate}")
        if collection_result.timezone:
            campus_parts.append(f"Timezone: {collection_result.timezone}")
            
        if campus_parts:
            sections.append("Campus: " + " | ".join(campus_parts))
        
        # 9. Mission and Values Section
        mission_parts = []
        if collection_result.description:
            desc = collection_result.description[:500] + "..." if len(collection_result.description) > 500 else collection_result.description
            mission_parts.append(f"Description: {desc}")
        
        if collection_result.mission_statement:
            mission = collection_result.mission_statement[:300] + "..." if len(collection_result.mission_statement) > 300 else collection_result.mission_statement
            mission_parts.append(f"Mission: {mission}")
        
        if collection_result.vision_statement:
            vision = collection_result.vision_statement[:300] + "..." if len(collection_result.vision_statement) > 300 else collection_result.vision_statement
            mission_parts.append(f"Vision: {vision}")
            
        if mission_parts:
            sections.append("Mission & Values: " + " | ".join(mission_parts))
        
        # 10. Additional Information Section
        additional_parts = []
        if collection_result.website:
            additional_parts.append(f"Website: {collection_result.website}")
        if collection_result.phone:
            additional_parts.append(f"Phone: {collection_result.phone}")
        if collection_result.email:
            additional_parts.append(f"Email: {collection_result.email}")
        if collection_result.confidence_score:
            additional_parts.append(f"Data Confidence: {collection_result.confidence_score:.1%}")
            
        if additional_parts:
            sections.append("Additional Info: " + " | ".join(additional_parts))
        
        return "\n".join(sections)
    
    def create_specialized_collection_text(self, collection_result: Any) -> Dict[str, str]:
        """
        Create specialized text representations for different matching aspects
        """
        texts = {}
        
        # 1. Academic Focus Text
        academic_parts = [f"University: {collection_result.name}"]
        
        # Add programs
        if collection_result.programs:
            try:
                programs_data = collection_result.programs
                if isinstance(programs_data, str):
                    programs_data = json.loads(programs_data)
                
                if isinstance(programs_data, list):
                    program_names = []
                    for program in programs_data:
                        if isinstance(program, dict) and 'name' in program:
                            program_names.append(program['name'])
                        elif isinstance(program, str):
                            program_names.append(program)
                    
                    if program_names:
                        academic_parts.append(f"Programs: {', '.join(program_names[:15])}")
            except Exception as e:
                logger.warning(f"Error parsing programs for academic text: {e}")
        
        if collection_result.student_population:
            academic_parts.append(f"Student Population: {collection_result.student_population:,}")
        if collection_result.faculty_count:
            academic_parts.append(f"Faculty Count: {collection_result.faculty_count:,}")
        if collection_result.acceptance_rate:
            academic_parts.append(f"Acceptance Rate: {collection_result.acceptance_rate:.1%}")
            
        texts['academic'] = " | ".join(academic_parts)
        
        # 2. Financial Profile Text
        financial_parts = [f"University: {collection_result.name}"]
        if collection_result.tuition_domestic:
            financial_parts.append(f"Domestic Tuition: ${collection_result.tuition_domestic:,.0f}")
        if collection_result.tuition_international:
            financial_parts.append(f"International Tuition: ${collection_result.tuition_international:,.0f}")
        if collection_result.total_cost_of_attendance:
            financial_parts.append(f"Total Cost: ${collection_result.total_cost_of_attendance:,.0f}")
        if collection_result.average_financial_aid_package:
            financial_parts.append(f"Avg Financial Aid: ${collection_result.average_financial_aid_package:,.0f}")
        if collection_result.acceptance_rate:
            financial_parts.append(f"Acceptance Rate: {collection_result.acceptance_rate:.1%}")
            
        texts['financial'] = " | ".join(financial_parts)
        
        # 3. Location and Environment Text
        location_parts = [f"University: {collection_result.name}"]
        if collection_result.city:
            location_parts.append(f"City: {collection_result.city}")
        if collection_result.state:
            location_parts.append(f"State: {collection_result.state}")
        if collection_result.country:
            location_parts.append(f"Country: {collection_result.country}")
        if collection_result.type:
            location_parts.append(f"Type: {collection_result.type}")
        if collection_result.campus_type:
            location_parts.append(f"Campus Type: {collection_result.campus_type}")
        if collection_result.climate:
            location_parts.append(f"Climate: {collection_result.climate}")
            
        texts['location'] = " | ".join(location_parts)
        
        # 4. Reputation and Rankings Text
        reputation_parts = [f"University: {collection_result.name}"]
        if collection_result.world_ranking:
            reputation_parts.append(f"World Ranking: #{collection_result.world_ranking}")
        if collection_result.national_ranking:
            reputation_parts.append(f"National Ranking: #{collection_result.national_ranking}")
        if collection_result.regional_ranking:
            reputation_parts.append(f"Regional Ranking: #{collection_result.regional_ranking}")
        if collection_result.founded_year:
            reputation_parts.append(f"Founded: {collection_result.founded_year}")
        if collection_result.description:
            desc = collection_result.description[:200] + "..." if len(collection_result.description) > 200 else collection_result.description
            reputation_parts.append(f"Description: {desc}")
            
        texts['reputation'] = " | ".join(reputation_parts)
        
        # 5. Student Life Text
        student_life_parts = [f"University: {collection_result.name}"]
        if collection_result.student_life:
            try:
                student_life_data = collection_result.student_life
                if isinstance(student_life_data, str):
                    student_life_data = json.loads(student_life_data)
                
                if isinstance(student_life_data, dict):
                    for category, items in student_life_data.items():
                        if isinstance(items, list) and items:
                            student_life_parts.append(f"{category}: {', '.join(items[:5])}")
            except Exception as e:
                logger.warning(f"Error parsing student life for specialized text: {e}")
                
        texts['student_life'] = " | ".join(student_life_parts)
        
        return texts
    
    async def generate_collection_embedding(self, collection_result: Any) -> Dict[str, Any]:
        """
        Generate comprehensive embeddings for a collection result
        """
        try:
            # Create main text representation
            main_text = self.create_structured_collection_text(collection_result)
            
            # Create specialized texts
            specialized_texts = self.create_specialized_collection_text(collection_result)
            
            # Generate main embedding
            main_response = self.client.embeddings.create(
                model=self.embedding_model,
                input=main_text,
                encoding_format="float"
            )
            main_embedding = main_response.data[0].embedding
            
            # Generate specialized embeddings
            specialized_embeddings = {}
            for aspect, text in specialized_texts.items():
                response = self.client.embeddings.create(
                    model=self.embedding_model,
                    input=text,
                    encoding_format="float"
                )
                specialized_embeddings[aspect] = response.data[0].embedding
            
            return {
                'main_embedding': main_embedding,
                'specialized_embeddings': specialized_embeddings,
                'main_text': main_text,
                'specialized_texts': specialized_texts,
                'embedding_model': self.embedding_model,
                'generated_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error generating collection embedding: {e}")
            raise
    
    def calculate_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """Calculate cosine similarity between two embeddings"""
        try:
            # Convert to numpy arrays
            vec1 = np.array(embedding1)
            vec2 = np.array(embedding2)
            
            # Calculate cosine similarity
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
                
            similarity = dot_product / (norm1 * norm2)
            return float(similarity)
            
        except Exception as e:
            logger.error(f"Error calculating similarity: {e}")
            return 0.0
    
    def create_matching_profile(self, collection_result: Any) -> Dict[str, Any]:
        """
        Create a comprehensive matching profile for a collection result
        """
        # Parse JSON fields
        programs_list = []
        if collection_result.programs:
            try:
                programs_data = collection_result.programs
                if isinstance(programs_data, str):
                    programs_data = json.loads(programs_data)
                
                if isinstance(programs_data, list):
                    for program in programs_data:
                        if isinstance(program, dict) and 'name' in program:
                            programs_list.append(program['name'])
                        elif isinstance(program, str):
                            programs_list.append(program)
            except Exception as e:
                logger.warning(f"Error parsing programs for profile: {e}")
        
        student_life_dict = {}
        if collection_result.student_life:
            try:
                student_life_data = collection_result.student_life
                if isinstance(student_life_data, str):
                    student_life_data = json.loads(student_life_data)
                
                if isinstance(student_life_data, dict):
                    student_life_dict = student_life_data
            except Exception as e:
                logger.warning(f"Error parsing student life for profile: {e}")
        
        subject_rankings_dict = {}
        if collection_result.subject_rankings:
            try:
                subject_rankings = collection_result.subject_rankings
                if isinstance(subject_rankings, str):
                    subject_rankings = json.loads(subject_rankings)
                
                if isinstance(subject_rankings, dict):
                    subject_rankings_dict = subject_rankings
            except Exception as e:
                logger.warning(f"Error parsing subject rankings for profile: {e}")
        
        profile = {
            'collection_id': str(collection_result.id),
            'name': collection_result.name,
            'basic_info': {
                'type': collection_result.type,
                'location': {
                    'city': collection_result.city,
                    'state': collection_result.state,
                    'country': collection_result.country
                },
                'founded_year': collection_result.founded_year,
                'student_population': collection_result.student_population,
                'undergraduate_population': collection_result.undergraduate_population,
                'graduate_population': collection_result.graduate_population,
                'faculty_count': collection_result.faculty_count,
                'student_faculty_ratio': collection_result.student_faculty_ratio,
                'international_students_percentage': collection_result.international_students_percentage
            },
            'academic_profile': {
                'acceptance_rate': collection_result.acceptance_rate,
                'world_ranking': collection_result.world_ranking,
                'national_ranking': collection_result.national_ranking,
                'regional_ranking': collection_result.regional_ranking,
                'subject_rankings': subject_rankings_dict,
                'programs': programs_list
            },
            'financial_profile': {
                'tuition_domestic': collection_result.tuition_domestic,
                'tuition_international': collection_result.tuition_international,
                'room_and_board': collection_result.room_and_board,
                'total_cost_of_attendance': collection_result.total_cost_of_attendance,
                'financial_aid_available': collection_result.financial_aid_available,
                'average_financial_aid_package': collection_result.average_financial_aid_package,
                'scholarships_available': collection_result.scholarships_available
            },
            'campus_profile': {
                'campus_size': collection_result.campus_size,
                'campus_type': collection_result.campus_type,
                'climate': collection_result.climate,
                'timezone': collection_result.timezone
            },
            'student_life_profile': student_life_dict,
            'descriptive_profile': {
                'description': collection_result.description,
                'mission_statement': collection_result.mission_statement,
                'vision_statement': collection_result.vision_statement
            },
            'metadata': {
                'confidence_score': collection_result.confidence_score,
                'source_urls': collection_result.source_urls,
                'last_updated': collection_result.last_updated,
                'website': collection_result.website,
                'phone': collection_result.phone,
                'email': collection_result.email
            }
        }
        
        return profile 