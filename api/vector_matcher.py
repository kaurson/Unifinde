import openai
import os
import json
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import text
import sys
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import logging

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.models import User, StudentProfile
from app.models import University, Program
from database.database import get_db

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VectorMatchingService:
    def __init__(self):
        self.client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        # Initialize sentence transformer for text embeddings
        try:
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            logger.info("Loaded sentence transformer model")
        except Exception as e:
            logger.warning(f"Could not load sentence transformer: {e}")
            self.embedding_model = None
        
        # Cache for embeddings
        self.embedding_cache = {}
        
    async def generate_user_embedding(self, user: User) -> List[float]:
        """Generate embedding vector for user profile"""
        
        # Create comprehensive user profile text
        user_profile_text = self._create_user_profile_text(user)
        
        # Generate embedding using OpenAI
        try:
            response = self.client.embeddings.create(
                model="text-embedding-3-small",
                input=user_profile_text,
                encoding_format="float"
            )
            embedding = response.data[0].embedding
            logger.info(f"Generated user embedding with {len(embedding)} dimensions")
            return embedding
            
        except Exception as e:
            logger.error(f"Error generating user embedding: {e}")
            # Fallback to sentence transformer if available
            if self.embedding_model:
                embedding = self.embedding_model.encode(user_profile_text).tolist()
                return embedding
            else:
                # Return a default embedding
                return [0.0] * 1536  # Default OpenAI embedding size
    
    async def generate_university_embedding(self, university: University) -> List[float]:
        """Generate embedding vector for university profile"""
        
        # Create comprehensive university profile text
        university_profile_text = self._create_university_profile_text(university)
        
        # Check cache first
        cache_key = f"university_{university.id}"
        if cache_key in self.embedding_cache:
            return self.embedding_cache[cache_key]
        
        # Generate embedding using OpenAI
        try:
            response = self.client.embeddings.create(
                model="text-embedding-3-small",
                input=university_profile_text,
                encoding_format="float"
            )
            embedding = response.data[0].embedding
            
            # Cache the embedding
            self.embedding_cache[cache_key] = embedding
            logger.info(f"Generated university embedding for {university.name}")
            return embedding
            
        except Exception as e:
            logger.error(f"Error generating university embedding: {e}")
            # Fallback to sentence transformer if available
            if self.embedding_model:
                embedding = self.embedding_model.encode(university_profile_text).tolist()
                self.embedding_cache[cache_key] = embedding
                return embedding
            else:
                # Return a default embedding
                default_embedding = [0.0] * 1536
                self.embedding_cache[cache_key] = default_embedding
                return default_embedding
    
    def _create_user_profile_text(self, user: User) -> str:
        """Create comprehensive text representation of user profile"""
        
        profile_parts = []
        
        # Basic information
        profile_parts.append(f"User: {user.name}, Age: {user.age or 'Not specified'}")
        
        # Personality profile
        if user.personality_profile:
            profile_parts.append(f"Personality: {json.dumps(user.personality_profile, indent=2)}")
        
        # Questionnaire answers
        if user.questionnaire_answers:
            profile_parts.append(f"Questionnaire responses: {json.dumps(user.questionnaire_answers, indent=2)}")
        
        # Preferred majors
        if user.preferred_majors:
            profile_parts.append(f"Preferred fields of study: {', '.join(user.preferred_majors)}")
        
        # Preferred locations
        if user.preferred_locations:
            profile_parts.append(f"Preferred locations: {', '.join(user.preferred_locations)}")
        
        # Financial preferences
        if user.max_tuition:
            profile_parts.append(f"Maximum tuition budget: ${user.max_tuition:,.2f}")
        
        if user.income:
            profile_parts.append(f"Family income: ${user.income:,.2f}")
        
        # University type preference
        if user.preferred_university_type:
            profile_parts.append(f"Preferred university type: {user.preferred_university_type}")
        
        # Student profile information
        if user.student_profile:
            student = user.student_profile
            
            # Academic information
            if student.gpa:
                profile_parts.append(f"GPA: {student.gpa}")
            
            if student.sat_total:
                profile_parts.append(f"SAT Total: {student.sat_total}")
            
            if student.act_composite:
                profile_parts.append(f"ACT Composite: {student.act_composite}")
            
            # Academic achievements
            if student.academic_awards:
                profile_parts.append(f"Academic awards: {', '.join(student.academic_awards)}")
            
            if student.research_experience:
                profile_parts.append(f"Research experience: {json.dumps(student.research_experience, indent=2)}")
            
            # Extracurricular activities
            if student.leadership_positions:
                profile_parts.append(f"Leadership positions: {', '.join(student.leadership_positions)}")
            
            if student.sports_activities:
                profile_parts.append(f"Sports activities: {', '.join(student.sports_activities)}")
            
            if student.artistic_activities:
                profile_parts.append(f"Artistic activities: {', '.join(student.artistic_activities)}")
            
            # Study preferences
            if student.preferred_class_size:
                profile_parts.append(f"Preferred class size: {student.preferred_class_size}")
            
            if student.preferred_teaching_style:
                profile_parts.append(f"Preferred teaching style: {', '.join(student.preferred_teaching_style)}")
            
            if student.preferred_campus_environment:
                profile_parts.append(f"Preferred campus environment: {', '.join(student.preferred_campus_environment)}")
            
            # Career goals
            if student.career_aspirations:
                profile_parts.append(f"Career aspirations: {student.career_aspirations}")
            
            if student.industry_preferences:
                profile_parts.append(f"Industry preferences: {', '.join(student.industry_preferences)}")
        
        return "\n".join(profile_parts)
    
    def _create_university_profile_text(self, university: University) -> str:
        """Create comprehensive text representation of university profile"""
        
        profile_parts = []
        
        # Basic information
        profile_parts.append(f"University: {university.name}")
        
        # Location
        location_parts = []
        if university.city:
            location_parts.append(university.city)
        if university.state:
            location_parts.append(university.state)
        if university.country:
            location_parts.append(university.country)
        
        if location_parts:
            profile_parts.append(f"Location: {', '.join(location_parts)}")
        
        # Type and basic stats
        if university.type:
            profile_parts.append(f"Type: {university.type}")
        
        if university.student_population:
            profile_parts.append(f"Student population: {university.student_population:,}")
        
        if university.faculty_count:
            profile_parts.append(f"Faculty count: {university.faculty_count:,}")
        
        # Academic information
        if university.acceptance_rate:
            profile_parts.append(f"Acceptance rate: {university.acceptance_rate:.1%}")
        
        if university.founded_year:
            profile_parts.append(f"Founded: {university.founded_year}")
        
        # Rankings
        if university.world_ranking:
            profile_parts.append(f"World ranking: #{university.world_ranking}")
        
        if university.national_ranking:
            profile_parts.append(f"National ranking: #{university.national_ranking}")
        
        # Financial information
        if university.tuition_domestic:
            profile_parts.append(f"Domestic tuition: ${university.tuition_domestic:,.2f}")
        
        if university.tuition_international:
            profile_parts.append(f"International tuition: ${university.tuition_international:,.2f}")
        
        # Descriptions
        if university.description:
            profile_parts.append(f"Description: {university.description}")
        
        if university.mission_statement:
            profile_parts.append(f"Mission: {university.mission_statement}")
        
        if university.vision_statement:
            profile_parts.append(f"Vision: {university.vision_statement}")
        
        # Programs
        if university.programs:
            program_names = [program.name for program in university.programs]
            profile_parts.append(f"Programs offered: {', '.join(program_names)}")
        
        # Facilities
        if university.facilities:
            facility_names = [facility.name for facility in university.facilities]
            profile_parts.append(f"Facilities: {', '.join(facility_names)}")
        
        return "\n".join(profile_parts)
    
    async def find_matches(self, user: User, db: Session, limit: int = 20) -> List[Dict[str, Any]]:
        """Find university matches for a user using vector similarity"""
        
        # Generate user embedding
        user_embedding = await self.generate_user_embedding(user)
        
        # Get all universities
        universities = db.query(University).all()
        
        matches = []
        
        for university in universities:
            # Generate university embedding
            university_embedding = await self.generate_university_embedding(university)
            
            # Calculate similarity
            similarity_score = self._calculate_similarity(user_embedding, university_embedding)
            
            # Create match object
            match = {
                "university_id": str(university.id),
                "university_name": university.name,
                "similarity_score": similarity_score,
                "university_data": university.to_dict(),
                "match_reasons": await self._generate_match_reasons(user, university, similarity_score)
            }
            
            matches.append(match)
        
        # Sort by similarity score and return top matches
        matches.sort(key=lambda x: x["similarity_score"], reverse=True)
        return matches[:limit]
    
    def _calculate_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """Calculate cosine similarity between two embeddings"""
        
        # Ensure embeddings have the same length
        min_length = min(len(embedding1), len(embedding2))
        embedding1 = embedding1[:min_length]
        embedding2 = embedding2[:min_length]
        
        # Convert to numpy arrays
        vec1 = np.array(embedding1).reshape(1, -1)
        vec2 = np.array(embedding2).reshape(1, -1)
        
        # Calculate cosine similarity
        similarity = cosine_similarity(vec1, vec2)[0][0]
        
        # Ensure similarity is between 0 and 1
        return max(0.0, min(1.0, similarity))
    
    async def _generate_match_reasons(self, user: User, university: University, similarity_score: float) -> List[str]:
        """Generate reasons why this university matches the user"""
        
        reasons = []
        
        # High similarity score
        if similarity_score > 0.8:
            reasons.append("Excellent overall compatibility based on your profile")
        elif similarity_score > 0.6:
            reasons.append("Strong compatibility with your academic and personal preferences")
        elif similarity_score > 0.4:
            reasons.append("Good compatibility with your profile")
        else:
            reasons.append("Some compatibility with your profile")
        
        # Major match
        if user.preferred_majors and university.programs:
            university_programs = [program.field.lower() for program in university.programs if program.field]
            user_majors = [major.lower() for major in user.preferred_majors]
            
            matching_majors = [major for major in user_majors if major in university_programs]
            if matching_majors:
                reasons.append(f"Offers your preferred major(s): {', '.join(matching_majors)}")
        
        # Location match
        if user.preferred_locations and university.city:
            if university.city in user.preferred_locations:
                reasons.append(f"Located in your preferred city: {university.city}")
            elif university.state in user.preferred_locations:
                reasons.append(f"Located in your preferred state: {university.state}")
        
        # University type match
        if user.preferred_university_type and university.type:
            if university.type.lower() == user.preferred_university_type.lower():
                reasons.append(f"Matches your preferred university type: {university.type}")
        
        # Academic fit
        if user.student_profile and user.student_profile.gpa and university.acceptance_rate:
            if user.student_profile.gpa >= 3.5 and university.acceptance_rate <= 0.3:
                reasons.append("Strong academic profile matches selective university")
            elif user.student_profile.gpa >= 3.0 and university.acceptance_rate <= 0.5:
                reasons.append("Good academic fit for this university")
        
        return reasons
    
    async def get_similar_users(self, user: User, db: Session, limit: int = 10) -> List[Dict[str, Any]]:
        """Find users with similar profiles"""
        
        user_embedding = await self.generate_user_embedding(user)
        
        # Get all other users
        other_users = db.query(User).filter(User.id != user.id).all()
        
        similar_users = []
        
        for other_user in other_users:
            other_embedding = await self.generate_user_embedding(other_user)
            similarity = self._calculate_similarity(user_embedding, other_embedding)
            
            if similarity > 0.5:  # Only include reasonably similar users
                similar_users.append({
                    "user_id": str(other_user.id),
                    "username": other_user.username,
                    "name": other_user.name,
                    "similarity_score": similarity,
                    "common_interests": self._find_common_interests(user, other_user)
                })
        
        # Sort by similarity and return top matches
        similar_users.sort(key=lambda x: x["similarity_score"], reverse=True)
        return similar_users[:limit]
    
    def _find_common_interests(self, user1: User, user2: User) -> List[str]:
        """Find common interests between two users"""
        
        common_interests = []
        
        # Compare preferred majors
        if user1.preferred_majors and user2.preferred_majors:
            common_majors = set(user1.preferred_majors) & set(user2.preferred_majors)
            if common_majors:
                common_interests.append(f"Common majors: {', '.join(common_majors)}")
        
        # Compare preferred locations
        if user1.preferred_locations and user2.preferred_locations:
            common_locations = set(user1.preferred_locations) & set(user2.preferred_locations)
            if common_locations:
                common_interests.append(f"Common locations: {', '.join(common_locations)}")
        
        # Compare university type preferences
        if (user1.preferred_university_type and user2.preferred_university_type and 
            user1.preferred_university_type.lower() == user2.preferred_university_type.lower()):
            common_interests.append(f"Both prefer {user1.preferred_university_type} universities")
        
        return common_interests
    
    def clear_cache(self):
        """Clear the embedding cache"""
        self.embedding_cache.clear()
        logger.info("Cleared embedding cache") 