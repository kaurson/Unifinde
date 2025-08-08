#!/usr/bin/env python3
"""
Enhanced University Vectorizer for better matching
Creates optimized text representations and vectors for universities
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

class EnhancedUniversityVectorizer:
    def __init__(self):
        self.client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.embedding_model = "text-embedding-3-small"
        
    def create_structured_university_text(self, university: Any, programs: List = None, facilities: List = None) -> str:
        """
        Create a structured, comprehensive text representation optimized for matching
        """
        sections = []
        
        # 1. Core Identity Section
        identity_parts = [f"University: {university.name}"]
        
        if university.type:
            identity_parts.append(f"Type: {university.type}")
        
        if university.founded_year:
            identity_parts.append(f"Founded: {university.founded_year}")
            
        sections.append(" | ".join(identity_parts))
        
        # 2. Location Section
        location_parts = []
        if university.city:
            location_parts.append(university.city)
        if university.state:
            location_parts.append(university.state)
        if university.country:
            location_parts.append(university.country)
            
        if location_parts:
            sections.append(f"Location: {', '.join(location_parts)}")
        
        # 3. Academic Profile Section
        academic_parts = []
        
        if university.student_population:
            academic_parts.append(f"Student Population: {university.student_population:,}")
        
        if university.faculty_count:
            academic_parts.append(f"Faculty: {university.faculty_count:,}")
            
        if university.acceptance_rate:
            academic_parts.append(f"Acceptance Rate: {university.acceptance_rate:.1%}")
            
        if academic_parts:
            sections.append("Academic Profile: " + " | ".join(academic_parts))
        
        # 4. Rankings Section
        rankings_parts = []
        if university.world_ranking:
            rankings_parts.append(f"World Rank: #{university.world_ranking}")
        if university.national_ranking:
            rankings_parts.append(f"National Rank: #{university.national_ranking}")
            
        if rankings_parts:
            sections.append("Rankings: " + " | ".join(rankings_parts))
        
        # 5. Financial Information Section
        financial_parts = []
        if university.tuition_domestic:
            financial_parts.append(f"Domestic Tuition: ${university.tuition_domestic:,.0f}")
        if university.tuition_international:
            financial_parts.append(f"International Tuition: ${university.tuition_international:,.0f}")
            
        if financial_parts:
            sections.append("Financial: " + " | ".join(financial_parts))
        
        # 6. Programs Section (Most important for matching)
        if programs:
            # Group programs by field for better representation
            program_fields = {}
            for program in programs:
                if program.field and program.name:
                    if program.field not in program_fields:
                        program_fields[program.field] = []
                    program_fields[program.field].append(program.name)
            
            if program_fields:
                program_sections = []
                for field, names in program_fields.items():
                    # Limit to top 5 programs per field to avoid token limits
                    program_sections.append(f"{field}: {', '.join(names[:5])}")
                
                sections.append("Academic Programs: " + " | ".join(program_sections))
        
        # 7. Facilities Section
        if facilities:
            facility_types = {}
            for facility in facilities:
                if facility.type and facility.name:
                    if facility.type not in facility_types:
                        facility_types[facility.type] = []
                    facility_types[facility.type].append(facility.name)
            
            if facility_types:
                facility_sections = []
                for ftype, names in facility_types.items():
                    facility_sections.append(f"{ftype}: {', '.join(names[:3])}")
                
                sections.append("Campus Facilities: " + " | ".join(facility_sections))
        
        # 8. Mission and Values Section
        mission_parts = []
        if university.description:
            # Truncate description to avoid token limits
            desc = university.description[:500] + "..." if len(university.description) > 500 else university.description
            mission_parts.append(f"Description: {desc}")
        
        if university.mission_statement:
            mission = university.mission_statement[:300] + "..." if len(university.mission_statement) > 300 else university.mission_statement
            mission_parts.append(f"Mission: {mission}")
            
        if mission_parts:
            sections.append("Mission & Values: " + " | ".join(mission_parts))
        
        return "\n".join(sections)
    
    def create_specialized_university_text(self, university: Any, programs: List = None, facilities: List = None) -> Dict[str, str]:
        """
        Create specialized text representations for different matching aspects
        """
        texts = {}
        
        # 1. Academic Focus Text
        academic_parts = [f"University: {university.name}"]
        if programs:
            program_names = [prog.name for prog in programs if prog.name]
            academic_parts.append(f"Programs: {', '.join(program_names[:15])}")
        
        if university.student_population:
            academic_parts.append(f"Student Population: {university.student_population:,}")
            
        if university.faculty_count:
            academic_parts.append(f"Faculty Count: {university.faculty_count:,}")
            
        texts['academic'] = " | ".join(academic_parts)
        
        # 2. Financial Profile Text
        financial_parts = [f"University: {university.name}"]
        if university.tuition_domestic:
            financial_parts.append(f"Domestic Tuition: ${university.tuition_domestic:,.0f}")
        if university.tuition_international:
            financial_parts.append(f"International Tuition: ${university.tuition_international:,.0f}")
        if university.acceptance_rate:
            financial_parts.append(f"Acceptance Rate: {university.acceptance_rate:.1%}")
            
        texts['financial'] = " | ".join(financial_parts)
        
        # 3. Location and Environment Text
        location_parts = [f"University: {university.name}"]
        if university.city:
            location_parts.append(f"City: {university.city}")
        if university.state:
            location_parts.append(f"State: {university.state}")
        if university.country:
            location_parts.append(f"Country: {university.country}")
        if university.type:
            location_parts.append(f"Type: {university.type}")
            
        texts['location'] = " | ".join(location_parts)
        
        # 4. Reputation and Rankings Text
        reputation_parts = [f"University: {university.name}"]
        if university.world_ranking:
            reputation_parts.append(f"World Ranking: #{university.world_ranking}")
        if university.national_ranking:
            reputation_parts.append(f"National Ranking: #{university.national_ranking}")
        if university.founded_year:
            reputation_parts.append(f"Founded: {university.founded_year}")
        if university.description:
            desc = university.description[:200] + "..." if len(university.description) > 200 else university.description
            reputation_parts.append(f"Description: {desc}")
            
        texts['reputation'] = " | ".join(reputation_parts)
        
        return texts
    
    async def generate_university_embedding(self, university: Any, programs: List = None, facilities: List = None) -> Dict[str, Any]:
        """
        Generate comprehensive embeddings for a university
        """
        try:
            # Create main text representation
            main_text = self.create_structured_university_text(university, programs, facilities)
            
            # Create specialized texts
            specialized_texts = self.create_specialized_university_text(university, programs, facilities)
            
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
            logger.error(f"Error generating university embedding: {e}")
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
    
    def create_matching_profile(self, university: Any, programs: List = None, facilities: List = None) -> Dict[str, Any]:
        """
        Create a comprehensive matching profile for a university
        """
        profile = {
            'university_id': str(university.id),
            'name': university.name,
            'basic_info': {
                'type': university.type,
                'location': {
                    'city': university.city,
                    'state': university.state,
                    'country': university.country
                },
                'founded_year': university.founded_year,
                'student_population': university.student_population,
                'faculty_count': university.faculty_count
            },
            'academic_profile': {
                'acceptance_rate': university.acceptance_rate,
                'world_ranking': university.world_ranking,
                'national_ranking': university.national_ranking,
                'programs': [prog.name for prog in (programs or []) if prog.name],
                'program_fields': list(set([prog.field for prog in (programs or []) if prog.field]))
            },
            'financial_profile': {
                'tuition_domestic': university.tuition_domestic,
                'tuition_international': university.tuition_international
            },
            'campus_profile': {
                'facilities': [fac.name for fac in (facilities or []) if fac.name],
                'facility_types': list(set([fac.type for fac in (facilities or []) if fac.type]))
            },
            'descriptive_profile': {
                'description': university.description,
                'mission_statement': university.mission_statement,
                'vision_statement': university.vision_statement
            }
        }
        
        return profile 