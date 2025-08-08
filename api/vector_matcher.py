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
import hashlib
from datetime import datetime, timedelta

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.models import (
    User, StudentProfile, UniversityDataCollectionResult, CollectionResultVector,
    UserVector, UniversityVector, VectorSearchCache
)
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
        
        # Cache for embeddings (in-memory cache for frequently accessed vectors)
        self.embedding_cache = {}
        self.cache_ttl = timedelta(hours=1)  # Cache TTL for in-memory cache
        
    async def get_or_create_user_vector(self, user: User, db: Session) -> UserVector:
        """Get existing user vector or create new one if needed"""
        
        # Check if user vector already exists
        existing_vector = db.query(UserVector).filter(UserVector.user_id == user.id).first()
        
        if existing_vector:
            # Check if the vector is still valid (user profile hasn't changed significantly)
            if self._is_user_vector_still_valid(user, existing_vector):
                logger.info(f"Using existing user vector for {user.email}")
                return existing_vector
            else:
                logger.info(f"User profile changed, regenerating vector for {user.email}")
                # Delete old vector
                db.delete(existing_vector)
                db.commit()
        
        # Generate new user vector
        logger.info(f"Generating new user vector for {user.email}")
        user_profile_text = self._create_user_profile_text(user)
        embedding = await self._generate_embedding(user_profile_text)
        
        # Create and store new user vector
        user_vector = UserVector(
            user_id=user.id,
            embedding_dimension=len(embedding),
            embedding_model="text-embedding-3-small",
            source_text=user_profile_text
        )
        user_vector.set_embedding_array(np.array(embedding))
        
        db.add(user_vector)
        db.commit()
        db.refresh(user_vector)
        
        # Add to in-memory cache
        cache_key = f"user_{user.id}"
        self.embedding_cache[cache_key] = {
            'embedding': embedding,
            'created_at': datetime.now()
        }
        
        logger.info(f"Created and stored user vector for {user.email}")
        return user_vector
    
    async def get_or_create_university_vector(self, university: University, db: Session) -> UniversityVector:
        """Get existing university vector or create new one if needed"""
        
        # Check if university vector already exists
        existing_vector = db.query(UniversityVector).filter(UniversityVector.university_id == university.id).first()
        
        if existing_vector:
            # Check if the vector is still valid (university data hasn't changed significantly)
            if self._is_university_vector_still_valid(university, existing_vector):
                logger.info(f"Using existing university vector for {university.name}")
                return existing_vector
            else:
                logger.info(f"University data changed, regenerating vector for {university.name}")
                # Delete old vector
                db.delete(existing_vector)
                db.commit()
        
        # Generate new university vector
        logger.info(f"Generating new university vector for {university.name}")
        university_profile_text = self._create_university_profile_text(university)
        embedding = await self._generate_embedding(university_profile_text)
        
        # Create and store new university vector
        university_vector = UniversityVector(
            university_id=university.id,
            embedding_dimension=len(embedding),
            embedding_model="text-embedding-3-small",
            source_text=university_profile_text
        )
        university_vector.set_embedding_array(np.array(embedding))
        
        db.add(university_vector)
        db.commit()
        db.refresh(university_vector)
        
        # Add to in-memory cache
        cache_key = f"university_{university.id}"
        self.embedding_cache[cache_key] = {
            'embedding': embedding,
            'created_at': datetime.now()
        }
        
        logger.info(f"Created and stored university vector for {university.name}")
        return university_vector
    
    def _is_user_vector_still_valid(self, user: User, user_vector: UserVector) -> bool:
        """Check if stored user vector is still valid based on profile changes"""
        # For now, we'll consider vectors valid for 24 hours
        # In a more sophisticated implementation, you could hash the user profile
        # and compare it with a stored hash to detect changes
        if user_vector.updated_at is None:
            # If updated_at is None, consider the vector invalid
            return False
        
        vector_age = datetime.now() - user_vector.updated_at.replace(tzinfo=None)
        return vector_age < timedelta(hours=24)
    
    def _is_university_vector_still_valid(self, university: University, university_vector: UniversityVector) -> bool:
        """Check if stored university vector is still valid based on data changes"""
        # For now, we'll consider vectors valid for 7 days since university data changes less frequently
        if university_vector.updated_at is None:
            # If updated_at is None, consider the vector invalid
            return False
        
        vector_age = datetime.now() - university_vector.updated_at.replace(tzinfo=None)
        return vector_age < timedelta(days=7)
    
    async def _generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for given text using OpenAI API"""
        try:
            response = self.client.embeddings.create(
                model="text-embedding-3-small",
                input=text,
                encoding_format="float"
            )
            embedding = response.data[0].embedding
            
            # Validate and clean the embedding
            embedding = self._clean_embedding(embedding)
            
            return embedding
            
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            # Fallback to sentence transformer if available
            if self.embedding_model:
                try:
                    embedding = self.embedding_model.encode(text).tolist()
                    embedding = self._clean_embedding(embedding)
                    return embedding
                except Exception as fallback_error:
                    logger.error(f"Fallback embedding also failed: {fallback_error}")
            
            # Return a default embedding
            logger.warning("Using default embedding due to API failure")
            return [0.0] * 1536  # Default OpenAI embedding size
    
    def _clean_embedding(self, embedding: List[float]) -> List[float]:
        """Clean and validate embedding vector"""
        if not isinstance(embedding, list):
            embedding = embedding.tolist() if hasattr(embedding, 'tolist') else list(embedding)
        
        # Clean NaN, infinite, and extreme values more aggressively
        cleaned_embedding = []
        nan_count = 0
        inf_count = 0
        extreme_count = 0
        
        for val in embedding:
            if isinstance(val, (int, float)):
                if np.isnan(val):
                    cleaned_embedding.append(0.0)
                    nan_count += 1
                elif np.isinf(val):
                    cleaned_embedding.append(0.0)
                    inf_count += 1
                elif abs(val) > 1000:  # Extreme values
                    cleaned_embedding.append(0.0)
                    extreme_count += 1
                else:
                    cleaned_embedding.append(float(val))
            else:
                cleaned_embedding.append(0.0)
                nan_count += 1
        
        if nan_count > 0 or inf_count > 0 or extreme_count > 0:
            logger.info(f"Cleaned embedding: {nan_count} NaN, {inf_count} inf, {extreme_count} extreme values replaced")
        
        # Accept both 1536 and 3072 dimensions (OpenAI text-embedding-3-small can return either)
        if len(cleaned_embedding) == 3072:
            # Use the first 1536 dimensions for consistency
            cleaned_embedding = cleaned_embedding[:1536]
            logger.info(f"Truncated embedding from 3072 to 1536 dimensions")
        elif len(cleaned_embedding) > 1536:
            # Truncate to 1536 dimensions
            cleaned_embedding = cleaned_embedding[:1536]
            logger.info(f"Truncated embedding from {len(embedding)} to 1536 dimensions")
        elif len(cleaned_embedding) < 1536:
            # Pad with zeros
            while len(cleaned_embedding) < 1536:
                cleaned_embedding.append(0.0)
            logger.info(f"Padded embedding from {len(embedding)} to 1536 dimensions")
        
        # Final validation
        if len(cleaned_embedding) != 1536:
            logger.error(f"Embedding still has wrong dimensions: {len(cleaned_embedding)}")
            return [0.0] * 1536
        
        # Check for all zeros or very low variance
        if all(val == 0.0 for val in cleaned_embedding):
            logger.warning("Generated embedding is all zeros, using small random values")
            # Use small random values instead of all zeros
            import random
            cleaned_embedding = [random.uniform(0.001, 0.01) for _ in range(1536)]
        else:
            # Check variance - if too low, add some noise
            variance = np.var(cleaned_embedding)
            if variance < 1e-6:
                logger.warning(f"Embedding has very low variance ({variance}), adding small noise")
                import random
                noise = [random.uniform(-0.001, 0.001) for _ in range(1536)]
                cleaned_embedding = [a + b for a, b in zip(cleaned_embedding, noise)]
            
            # Normalize to reasonable range if needed
            max_val = max(abs(val) for val in cleaned_embedding)
            if max_val > 10:
                logger.warning(f"Embedding has large values (max: {max_val}), normalizing")
                cleaned_embedding = [val / max_val * 5 for val in cleaned_embedding]
        
        return cleaned_embedding
    
    def _is_valid_embedding(self, embedding: List[float]) -> bool:
        """Check if embedding is valid (no NaN, no extreme values)"""
        if not embedding or len(embedding) != 1536:
            return False
        
        # Check for NaN or infinite values
        for val in embedding:
            if not isinstance(val, (int, float)) or np.isnan(val) or np.isinf(val):
                return False
        
        # Check for extreme values (values that are too large)
        embedding_array = np.array(embedding)
        if np.any(np.abs(embedding_array) > 1000):
            return False
        
        # Check for reasonable variance
        variance = np.var(embedding_array)
        if variance < 1e-8 or variance > 100:
            return False
        
        return True
    
    def _get_cached_embedding(self, cache_key: str) -> Optional[List[float]]:
        """Get embedding from in-memory cache if it's still valid"""
        if cache_key in self.embedding_cache:
            cache_entry = self.embedding_cache[cache_key]
            cache_age = datetime.now() - cache_entry['created_at']
            if cache_age < self.cache_ttl:
                return cache_entry['embedding']
            else:
                # Remove expired cache entry
                del self.embedding_cache[cache_key]
        return None
    
    def _add_to_cache(self, cache_key: str, embedding: List[float]) -> None:
        """Add embedding to in-memory cache"""
        self.embedding_cache[cache_key] = {
            'embedding': embedding,
            'created_at': datetime.now()
        }
    
    async def generate_user_embedding(self, user: User, db: Session) -> List[float]:
        """Generate embedding vector for user profile (now uses vector storage)"""
        
        # Check in-memory cache first
        cache_key = f"user_{user.id}"
        cached_embedding = self._get_cached_embedding(cache_key)
        if cached_embedding:
            # Validate cached embedding
            if self._is_valid_embedding(cached_embedding):
                return cached_embedding
            else:
                # Remove invalid cached embedding
                if cache_key in self.embedding_cache:
                    del self.embedding_cache[cache_key]
        
        # Get or create user vector from database
        user_vector = await self.get_or_create_user_vector(user, db)
        embedding = user_vector.get_embedding_array().tolist()
        
        # Clean and validate the embedding
        embedding = self._clean_embedding(embedding)
        
        # Final validation
        if not self._is_valid_embedding(embedding):
            logger.error(f"Generated invalid user embedding for {user.email}, regenerating...")
            # Force regeneration by deleting the vector
            db.delete(user_vector)
            db.commit()
            
            # Generate fresh embedding
            user_profile_text = self._create_user_profile_text(user)
            embedding = await self._generate_embedding(user_profile_text)
            embedding = self._clean_embedding(embedding)
            
            # Create new vector
            user_vector = UserVector(
                user_id=user.id,
                embedding_dimension=len(embedding),
                embedding_model="text-embedding-3-small",
                source_text=user_profile_text
            )
            user_vector.set_embedding_array(np.array(embedding))
            
            db.add(user_vector)
            db.commit()
        
        # Add to in-memory cache only if valid
        if self._is_valid_embedding(embedding):
            self._add_to_cache(cache_key, embedding)
        
        return embedding
    
    async def generate_university_embedding(self, university: University, db: Session) -> List[float]:
        """Generate embedding vector for university profile (now uses vector storage)"""
        
        # Check in-memory cache first
        cache_key = f"university_{university.id}"
        cached_embedding = self._get_cached_embedding(cache_key)
        if cached_embedding:
            return cached_embedding
        
        # Get or create university vector from database
        university_vector = await self.get_or_create_university_vector(university, db)
        embedding = university_vector.get_embedding_array().tolist()
        
        # Add to in-memory cache
        self._add_to_cache(cache_key, embedding)
        
        return embedding
    
    def _create_user_profile_text(self, user: User) -> str:
        """Create comprehensive text representation of user profile"""
        
        profile_parts = []
        
        # Basic information
        profile_parts.append(f"Student Profile: {user.name}")
        if user.age:
            profile_parts.append(f"Age: {user.age} years old")
        
        # Academic interests and preferences
        if user.preferred_majors:
            profile_parts.append(f"Academic interests: {', '.join(user.preferred_majors)}")
            profile_parts.append(f"Fields of study: {', '.join(user.preferred_majors)}")
        
        # Location preferences
        if user.preferred_locations:
            profile_parts.append(f"Preferred locations: {', '.join(user.preferred_locations)}")
            profile_parts.append(f"Geographic preferences: {', '.join(user.preferred_locations)}")
        
        # Financial preferences
        if user.max_tuition:
            profile_parts.append(f"Budget: Maximum tuition ${user.max_tuition:,.0f} per year")
            profile_parts.append(f"Financial constraints: Tuition budget up to ${user.max_tuition:,.0f}")
        
        if user.income:
            profile_parts.append(f"Family income: ${user.income:,.0f} annually")
        
        # University type preference
        if user.preferred_university_type:
            profile_parts.append(f"University type preference: {user.preferred_university_type}")
            profile_parts.append(f"Institution type: {user.preferred_university_type} university")
        
        # Personality profile (simplified for better embedding)
        if user.personality_profile:
            if isinstance(user.personality_profile, dict):
                # Extract key personality traits
                traits = []
                for key, value in user.personality_profile.items():
                    if isinstance(value, str) and len(value) < 100:  # Short, meaningful traits
                        traits.append(f"{key}: {value}")
                if traits:
                    profile_parts.append(f"Personality traits: {', '.join(traits)}")
        
        # Student profile information
        if user.student_profile:
            student = user.student_profile
            
            # Academic performance
            if student.gpa:
                profile_parts.append(f"Academic performance: GPA {student.gpa}")
                if student.gpa >= 3.5:
                    profile_parts.append("High academic achiever")
                elif student.gpa >= 3.0:
                    profile_parts.append("Good academic standing")
            
            # Test scores
            if student.sat_total:
                profile_parts.append(f"SAT score: {student.sat_total}")
                if student.sat_total >= 1400:
                    profile_parts.append("Strong standardized test performance")
            
            if student.act_composite:
                profile_parts.append(f"ACT score: {student.act_composite}")
                if student.act_composite >= 30:
                    profile_parts.append("Excellent ACT performance")
            
            # Academic achievements
            if student.academic_awards:
                profile_parts.append(f"Academic achievements: {', '.join(student.academic_awards)}")
            
            if student.honors_classes:
                profile_parts.append(f"Advanced coursework: {', '.join(student.honors_classes)}")
            
            # Extracurricular activities
            if student.leadership_positions:
                profile_parts.append(f"Leadership experience: {', '.join(student.leadership_positions)}")
            
            if student.sports_activities:
                profile_parts.append(f"Athletic involvement: {', '.join(student.sports_activities)}")
            
            if student.artistic_activities:
                profile_parts.append(f"Creative activities: {', '.join(student.artistic_activities)}")
            
            if student.volunteer_hours:
                profile_parts.append(f"Community service: {student.volunteer_hours} volunteer hours")
            
            # Study preferences
            if student.preferred_class_size:
                profile_parts.append(f"Learning environment preference: {student.preferred_class_size} class size")
            
            if student.preferred_teaching_style:
                profile_parts.append(f"Teaching style preference: {', '.join(student.preferred_teaching_style)}")
            
            if student.preferred_campus_environment:
                profile_parts.append(f"Campus environment: {', '.join(student.preferred_campus_environment)}")
            
            # Career goals
            if student.career_aspirations:
                profile_parts.append(f"Career goals: {student.career_aspirations}")
            
            if student.industry_preferences:
                profile_parts.append(f"Industry interests: {', '.join(student.industry_preferences)}")
        
        # Create a structured summary
        summary_parts = []
        if user.preferred_majors:
            summary_parts.append(f"interested in {', '.join(user.preferred_majors)}")
        if user.preferred_locations:
            summary_parts.append(f"wants to study in {', '.join(user.preferred_locations)}")
        if user.max_tuition:
            summary_parts.append(f"budget up to ${user.max_tuition:,.0f}")
        if user.preferred_university_type:
            summary_parts.append(f"prefers {user.preferred_university_type} universities")
        
        if summary_parts:
            profile_parts.append(f"Student summary: {', '.join(summary_parts)}")
        
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
            profile_parts.append(f"Geographic location: {', '.join(location_parts)}")
        
        # Type and basic stats
        if university.type:
            profile_parts.append(f"University type: {university.type}")
            profile_parts.append(f"Institution type: {university.type} university")
        
        if university.student_population:
            profile_parts.append(f"Student population: {university.student_population:,}")
            profile_parts.append(f"Total enrollment: {university.student_population:,} students")
        
        if university.faculty_count:
            profile_parts.append(f"Faculty count: {university.faculty_count:,}")
            profile_parts.append(f"Academic staff: {university.faculty_count:,} faculty members")
        
        # Academic information
        if university.acceptance_rate:
            profile_parts.append(f"Acceptance rate: {university.acceptance_rate:.1%}")
            if university.acceptance_rate <= 0.2:
                profile_parts.append("Highly selective university")
            elif university.acceptance_rate <= 0.4:
                profile_parts.append("Selective university")
            elif university.acceptance_rate <= 0.6:
                profile_parts.append("Moderately selective university")
            else:
                profile_parts.append("Accessible university")
        
        if university.founded_year:
            profile_parts.append(f"Founded: {university.founded_year}")
            profile_parts.append(f"Established: {university.founded_year}")
        
        # Rankings
        if university.world_ranking:
            profile_parts.append(f"World ranking: #{university.world_ranking}")
            if university.world_ranking <= 100:
                profile_parts.append("Top 100 world university")
            elif university.world_ranking <= 500:
                profile_parts.append("Top 500 world university")
        
        if university.national_ranking:
            profile_parts.append(f"National ranking: #{university.national_ranking}")
            if university.national_ranking <= 50:
                profile_parts.append("Top 50 national university")
            elif university.national_ranking <= 100:
                profile_parts.append("Top 100 national university")
        
        # Financial information
        if university.tuition_domestic:
            profile_parts.append(f"Domestic tuition: ${university.tuition_domestic:,.0f}")
            profile_parts.append(f"Tuition cost: ${university.tuition_domestic:,.0f} per year")
        
        if university.tuition_international:
            profile_parts.append(f"International tuition: ${university.tuition_international:,.0f}")
            profile_parts.append(f"International student cost: ${university.tuition_international:,.0f} per year")
        
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
            profile_parts.append(f"Academic programs: {', '.join(program_names)}")
            
            # Extract program fields
            program_fields = [program.field for program in university.programs if program.field]
            if program_fields:
                profile_parts.append(f"Fields of study: {', '.join(program_fields)}")
        
        # Facilities
        if university.facilities:
            facility_names = [facility.name for facility in university.facilities]
            profile_parts.append(f"Facilities: {', '.join(facility_names)}")
            profile_parts.append(f"Campus facilities: {', '.join(facility_names)}")
        
        # Create a structured summary
        summary_parts = []
        if university.type:
            summary_parts.append(f"{university.type} university")
        if university.city and university.country:
            summary_parts.append(f"located in {university.city}, {university.country}")
        if university.student_population:
            summary_parts.append(f"with {university.student_population:,} students")
        if university.acceptance_rate:
            summary_parts.append(f"acceptance rate {university.acceptance_rate:.1%}")
        if university.tuition_domestic:
            summary_parts.append(f"tuition ${university.tuition_domestic:,.0f}")
        
        if summary_parts:
            profile_parts.append(f"University summary: {', '.join(summary_parts)}")
        
        return "\n".join(profile_parts)
    
    async def find_matches(self, user: User, db: Session, limit: int = 20) -> List[Dict[str, Any]]:
        """Find university matches for a user using vector similarity with stored vectors"""
        
        # Generate user embedding (uses vector storage)
        user_embedding = await self.generate_user_embedding(user, db)
        
        # Get all collection result vectors (since that's where the university data is)
        collection_vectors = db.query(CollectionResultVector).all()
        
        if not collection_vectors:
            logger.warning("No collection result vectors found. Please generate vectors first.")
            return []
        
        # Adaptive threshold system - start high and lower if needed
        thresholds = [0.1, 0.05, 0.02, 0.01, 0.005]  # Start with 10%, then 5%, 2%, 1%, 0.5%
        
        for threshold in thresholds:
            matches = []
            logger.info(f"Trying threshold: {threshold}")
            
            for i, vector in enumerate(collection_vectors):
                logger.info(f"Processing collection vector {i+1}/{len(collection_vectors)}")
                
                # Get the collection result data
                collection_result = db.query(UniversityDataCollectionResult).filter(
                    UniversityDataCollectionResult.id == vector.collection_result_id
                ).first()
                
                if not collection_result:
                    logger.warning(f"No collection result found for vector {vector.collection_result_id}")
                    continue
                
                # Get the pre-generated embedding
                try:
                    university_embedding = vector.get_embedding_array().tolist()
                    # Clean the embedding if needed
                    university_embedding = self._clean_embedding(university_embedding)
                        
                except Exception as e:
                    logger.error(f"Error getting embedding for vector {i+1}: {e}")
                    continue
                
                # Calculate similarity
                try:
                    similarity_score = self._calculate_similarity(user_embedding, university_embedding)
                    logger.info(f"Vector {i+1} similarity score: {similarity_score}")
                    
                    # Only include matches above the current threshold
                    if similarity_score >= threshold:
                        # Create match object
                        match = {
                            "university_id": str(collection_result.id),
                            "university_name": collection_result.name or "Unknown University",
                            "similarity_score": similarity_score,
                            "university_data": self._collection_result_to_dict(collection_result),
                            "match_reasons": await self._generate_collection_match_reasons(user, collection_result, similarity_score),
                            "source": "collection_data"
                        }
                        
                        matches.append(match)
                    else:
                        logger.info(f"Vector {i+1} similarity score {similarity_score} below threshold {threshold}, skipping")
                    
                except Exception as e:
                    logger.error(f"Error calculating similarity for vector {i+1}: {e}")
                    continue
            
            # Sort by similarity score
            matches.sort(key=lambda x: x["similarity_score"], reverse=True)
            logger.info(f"Generated {len(matches)} matches above threshold {threshold}")
            
            # If we found enough matches, return them
            if len(matches) >= min(limit, 5):  # At least 5 matches or the requested limit
                logger.info(f"Found sufficient matches with threshold {threshold}, returning top {limit}")
                return matches[:limit]
            else:
                logger.info(f"Only {len(matches)} matches found with threshold {threshold}, trying lower threshold...")
        
        # If we get here, return whatever we found with the lowest threshold
        logger.info(f"Using lowest threshold results: {len(matches)} matches")
        return matches[:limit]

    async def find_matches_with_cache(self, user: User, db: Session, limit: int = 20) -> List[Dict[str, Any]]:
        """Find university matches with caching to avoid redundant computations"""
        
        # Create cache key based on user and search parameters
        cache_key = self._create_search_cache_key(user.id, "university_match", limit)
        
        # Check if we have cached results
        cached_results = self._get_cached_search_results(user.id, cache_key, db)
        if cached_results:
            logger.info(f"Using cached search results for user {user.email}")
            return cached_results
        
        # Perform the search
        results = await self.find_matches(user, db, limit)
        
        # Cache the results
        self._cache_search_results(user.id, cache_key, results, db)
        
        return results
    
    def _create_search_cache_key(self, user_id: str, search_type: str, limit: int) -> str:
        """Create a unique cache key for search results"""
        cache_string = f"{user_id}_{search_type}_{limit}"
        return hashlib.md5(cache_string.encode()).hexdigest()
    
    def _get_cached_search_results(self, user_id: str, cache_key: str, db: Session) -> Optional[List[Dict[str, Any]]]:
        """Get cached search results if they exist and are still valid"""
        cached_entry = db.query(VectorSearchCache).filter(
            VectorSearchCache.user_id == user_id,
            VectorSearchCache.cache_key == cache_key,
            VectorSearchCache.expires_at > datetime.now()
        ).first()
        
        if cached_entry:
            return cached_entry.results
        return None
    
    def _cache_search_results(self, user_id: str, cache_key: str, results: List[Dict[str, Any]], db: Session) -> None:
        """Cache search results for future use"""
        # Remove any existing cache entry for this key
        db.query(VectorSearchCache).filter(
            VectorSearchCache.user_id == user_id,
            VectorSearchCache.cache_key == cache_key
        ).delete()
        
        # Create new cache entry
        cache_entry = VectorSearchCache(
            user_id=user_id,
            search_type="university_match",
            embedding_model="text-embedding-3-small",
            results=results,
            cache_key=cache_key,
            expires_at=datetime.now() + timedelta(hours=6)  # Cache for 6 hours
        )
        
        db.add(cache_entry)
        db.commit()
        logger.info(f"Cached search results for user {user_id}")
    
    async def batch_generate_university_vectors(self, db: Session, batch_size: int = 10) -> None:
        """Generate vectors for universities that don't have them yet"""
        
        # Get universities without vectors
        universities_without_vectors = db.query(University).outerjoin(
            UniversityVector, University.id == UniversityVector.university_id
        ).filter(UniversityVector.id.is_(None)).limit(batch_size).all()
        
        logger.info(f"Generating vectors for {len(universities_without_vectors)} universities")
        
        for i, university in enumerate(universities_without_vectors):
            try:
                await self.get_or_create_university_vector(university, db)
                logger.info(f"Generated vector {i+1}/{len(universities_without_vectors)} for {university.name}")
            except Exception as e:
                logger.error(f"Error generating vector for {university.name}: {e}")
                continue
        
        logger.info("Batch vector generation completed")
    
    async def batch_generate_user_vectors(self, db: Session, batch_size: int = 10) -> None:
        """Generate vectors for users that don't have them yet"""
        
        # Get users without vectors
        users_without_vectors = db.query(User).outerjoin(
            UserVector, User.id == UserVector.user_id
        ).filter(UserVector.id.is_(None)).limit(batch_size).all()
        
        logger.info(f"Generating vectors for {len(users_without_vectors)} users")
        
        for i, user in enumerate(users_without_vectors):
            try:
                await self.get_or_create_user_vector(user, db)
                logger.info(f"Generated vector {i+1}/{len(users_without_vectors)} for {user.email}")
            except Exception as e:
                logger.error(f"Error generating vector for {user.email}: {e}")
                continue
        
        logger.info("Batch user vector generation completed")
    
    async def cleanup_expired_cache(self, db: Session) -> None:
        """Clean up expired cache entries"""
        
        expired_count = db.query(VectorSearchCache).filter(
            VectorSearchCache.expires_at < datetime.now()
        ).delete()
        
        db.commit()
        logger.info(f"Cleaned up {expired_count} expired cache entries")
    
    async def get_vector_statistics(self, db: Session) -> Dict[str, Any]:
        """Get statistics about stored vectors"""
        
        total_users = db.query(User).count()
        users_with_vectors = db.query(UserVector).count()
        
        total_universities = db.query(University).count()
        universities_with_vectors = db.query(UniversityVector).count()
        
        total_collection_vectors = db.query(CollectionResultVector).count()
        
        cache_entries = db.query(VectorSearchCache).count()
        expired_cache_entries = db.query(VectorSearchCache).filter(
            VectorSearchCache.expires_at < datetime.now()
        ).count()
        
        return {
            "users": {
                "total": total_users,
                "with_vectors": users_with_vectors,
                "coverage_percentage": (users_with_vectors / total_users * 100) if total_users > 0 else 0
            },
            "universities": {
                "total": total_universities,
                "with_vectors": universities_with_vectors,
                "coverage_percentage": (universities_with_vectors / total_universities * 100) if total_universities > 0 else 0
            },
            "collection_vectors": total_collection_vectors,
            "cache": {
                "total_entries": cache_entries,
                "expired_entries": expired_cache_entries
            }
        }
    
    async def find_collection_matches(self, user: User, db: Session, limit: int = 20) -> List[Dict[str, Any]]:
        """Find university matches for a user using pre-generated collection result vectors with caching"""
        
        logger.info(f"Starting collection matches for user: {user.email}")
        
        # Generate user embedding (uses vector storage)
        logger.info("Generating user embedding...")
        user_embedding = await self.generate_user_embedding(user, db)
        logger.info(f"User embedding generated with {len(user_embedding)} dimensions")
        
        # Validate user embedding
        if len(user_embedding) not in [1536, 3072]:
            logger.error(f"User embedding has unexpected dimensions: {len(user_embedding)}")
            return []
        
        # Get all collection result vectors
        logger.info("Querying collection vectors...")
        collection_vectors = db.query(CollectionResultVector).all()
        logger.info(f"Found {len(collection_vectors)} collection vectors")
        
        if not collection_vectors:
            logger.warning("No collection result vectors found. Please generate vectors first.")
            return []
        
        # Adaptive threshold system - start high and lower if needed
        thresholds = [0.1, 0.05, 0.02, 0.01, 0.005]  # Start with 10%, then 5%, 2%, 1%, 0.5%
        
        for threshold in thresholds:
            matches = []
            logger.info(f"Trying threshold: {threshold}")
            
            for i, vector in enumerate(collection_vectors):
                logger.info(f"Processing vector {i+1}/{len(collection_vectors)}")
                
                # Get the collection result data
                collection_result = db.query(UniversityDataCollectionResult).filter(
                    UniversityDataCollectionResult.id == vector.collection_result_id
                ).first()
                
                if not collection_result:
                    logger.warning(f"No collection result found for vector {vector.collection_result_id}")
                    continue
                
                # Get the pre-generated embedding
                try:
                    university_embedding = vector.get_embedding_array().tolist()
                    # Clean the embedding if needed
                    university_embedding = self._clean_embedding(university_embedding)
                        
                except Exception as e:
                    logger.error(f"Error getting embedding for vector {i+1}: {e}")
                    continue
                
                # Calculate similarity
                try:
                    similarity_score = self._calculate_similarity(user_embedding, university_embedding)
                    logger.info(f"Vector {i+1} similarity score: {similarity_score}")
                    
                    # Only include matches above the current threshold
                    if similarity_score >= threshold:
                        # Create match object
                        match = {
                            "university_id": str(collection_result.id),
                            "university_name": collection_result.name or "Unknown University",
                            "similarity_score": similarity_score,
                            "university_data": self._collection_result_to_dict(collection_result),
                            "match_reasons": await self._generate_collection_match_reasons(user, collection_result, similarity_score),
                            "source": "collection_data"
                        }
                        
                        matches.append(match)
                    else:
                        logger.info(f"Vector {i+1} similarity score {similarity_score} below threshold {threshold}, skipping")
                    
                except Exception as e:
                    logger.error(f"Error calculating similarity for vector {i+1}: {e}")
                    continue
            
            # Sort by similarity score
            matches.sort(key=lambda x: x["similarity_score"], reverse=True)
            logger.info(f"Generated {len(matches)} matches above threshold {threshold}")
            
            # If we found enough matches, return them
            if len(matches) >= min(limit, 5):  # At least 5 matches or the requested limit
                logger.info(f"Found sufficient matches with threshold {threshold}, returning top {limit}")
                return matches[:limit]
            else:
                logger.info(f"Only {len(matches)} matches found with threshold {threshold}, trying lower threshold...")
        
        # If we get here, return whatever we found with the lowest threshold
        logger.info(f"Using lowest threshold results: {len(matches)} matches")
        return matches[:limit]

    async def find_collection_matches_with_cache(self, user: User, db: Session, limit: int = 20) -> List[Dict[str, Any]]:
        """Find collection matches with caching to avoid redundant computations"""
        
        # Create cache key based on user and search parameters
        cache_key = self._create_search_cache_key(user.id, "collection_match", limit)
        
        # Check if we have cached results
        cached_results = self._get_cached_search_results(user.id, cache_key, db)
        if cached_results:
            logger.info(f"Using cached collection search results for user {user.email}")
            return cached_results
        
        # Perform the search
        results = await self.find_collection_matches(user, db, limit)
        
        # Cache the results
        self._cache_search_results(user.id, cache_key, results, db)
        
        return results
    
    async def invalidate_user_vector(self, user_id: str, db: Session) -> None:
        """Invalidate and regenerate user vector when profile changes"""
        
        # Delete existing user vector
        user_vector = db.query(UserVector).filter(UserVector.user_id == user_id).first()
        if user_vector:
            db.delete(user_vector)
            db.commit()
            logger.info(f"Invalidated user vector for user {user_id}")
        
        # Remove from in-memory cache
        cache_key = f"user_{user_id}"
        if cache_key in self.embedding_cache:
            del self.embedding_cache[cache_key]
        
        # Clear related search cache entries
        db.query(VectorSearchCache).filter(VectorSearchCache.user_id == user_id).delete()
        db.commit()
        logger.info(f"Cleared search cache for user {user_id}")
    
    async def invalidate_university_vector(self, university_id: str, db: Session) -> None:
        """Invalidate and regenerate university vector when data changes"""
        
        # Delete existing university vector
        university_vector = db.query(UniversityVector).filter(UniversityVector.university_id == university_id).first()
        if university_vector:
            db.delete(university_vector)
            db.commit()
            logger.info(f"Invalidated university vector for university {university_id}")
        
        # Remove from in-memory cache
        cache_key = f"university_{university_id}"
        if cache_key in self.embedding_cache:
            del self.embedding_cache[cache_key]
    
    async def optimize_vector_storage(self, db: Session) -> Dict[str, Any]:
        """Optimize vector storage by cleaning up invalid vectors and regenerating as needed"""
        
        optimization_results = {
            "invalid_user_vectors_removed": 0,
            "invalid_university_vectors_removed": 0,
            "user_vectors_regenerated": 0,
            "university_vectors_regenerated": 0,
            "cache_entries_cleaned": 0
        }
        
        # Clean up expired cache entries
        expired_cache = db.query(VectorSearchCache).filter(
            VectorSearchCache.expires_at < datetime.now()
        ).delete()
        optimization_results["cache_entries_cleaned"] = expired_cache
        db.commit()
        
        # Find and remove invalid user vectors (users that no longer exist)
        invalid_user_vectors = db.query(UserVector).outerjoin(
            User, UserVector.user_id == User.id
        ).filter(User.id.is_(None)).all()
        
        for vector in invalid_user_vectors:
            db.delete(vector)
            optimization_results["invalid_user_vectors_removed"] += 1
        
        # Find and remove invalid university vectors (universities that no longer exist)
        invalid_university_vectors = db.query(UniversityVector).outerjoin(
            University, UniversityVector.university_id == University.id
        ).filter(University.id.is_(None)).all()
        
        for vector in invalid_university_vectors:
            db.delete(vector)
            optimization_results["invalid_university_vectors_removed"] += 1
        
        db.commit()
        
        # Regenerate vectors for users without vectors
        users_without_vectors = db.query(User).outerjoin(
            UserVector, User.id == UserVector.user_id
        ).filter(UserVector.id.is_(None)).limit(50).all()  # Limit to avoid long operations
        
        for user in users_without_vectors:
            try:
                await self.get_or_create_user_vector(user, db)
                optimization_results["user_vectors_regenerated"] += 1
            except Exception as e:
                logger.error(f"Error regenerating user vector for {user.email}: {e}")
        
        # Regenerate vectors for universities without vectors
        universities_without_vectors = db.query(University).outerjoin(
            UniversityVector, University.id == UniversityVector.university_id
        ).filter(UniversityVector.id.is_(None)).limit(50).all()  # Limit to avoid long operations
        
        for university in universities_without_vectors:
            try:
                await self.get_or_create_university_vector(university, db)
                optimization_results["university_vectors_regenerated"] += 1
            except Exception as e:
                logger.error(f"Error regenerating university vector for {university.name}: {e}")
        
        logger.info(f"Vector storage optimization completed: {optimization_results}")
        return optimization_results
    
    async def get_vector_performance_metrics(self, db: Session) -> Dict[str, Any]:
        """Get performance metrics for vector operations"""
        
        # Get vector generation statistics
        stats = await self.get_vector_statistics(db)
        
        # Calculate average vector dimensions
        user_vectors = db.query(UserVector).all()
        university_vectors = db.query(UniversityVector).all()
        
        avg_user_dimensions = sum(v.embedding_dimension for v in user_vectors) / len(user_vectors) if user_vectors else 0
        avg_university_dimensions = sum(v.embedding_dimension for v in university_vectors) / len(university_vectors) if university_vectors else 0
        
        # Get cache hit rate (this would need to be tracked over time in a real implementation)
        total_cache_entries = stats["cache"]["total_entries"]
        expired_cache_entries = stats["cache"]["expired_entries"]
        active_cache_entries = total_cache_entries - expired_cache_entries
        
        return {
            "vector_statistics": stats,
            "performance_metrics": {
                "average_user_vector_dimensions": avg_user_dimensions,
                "average_university_vector_dimensions": avg_university_dimensions,
                "active_cache_entries": active_cache_entries,
                "cache_utilization_rate": (active_cache_entries / total_cache_entries * 100) if total_cache_entries > 0 else 0
            },
            "storage_efficiency": {
                "user_vector_coverage": stats["users"]["coverage_percentage"],
                "university_vector_coverage": stats["universities"]["coverage_percentage"],
                "total_vectors_stored": stats["users"]["with_vectors"] + stats["universities"]["with_vectors"] + stats["collection_vectors"]
            }
        }

    def _collection_result_to_dict(self, collection_result: UniversityDataCollectionResult) -> Dict[str, Any]:
        """Convert collection result to dictionary format"""
        return {
            "id": str(collection_result.id),
            "name": collection_result.name,
            "type": collection_result.type,
            "founded_year": collection_result.founded_year,
            "student_population": collection_result.student_population,
            "undergraduate_population": collection_result.undergraduate_population,
            "graduate_population": collection_result.graduate_population,
            "faculty_count": collection_result.faculty_count,
            "student_faculty_ratio": collection_result.student_faculty_ratio,
            "international_students_percentage": collection_result.international_students_percentage,
            "acceptance_rate": collection_result.acceptance_rate,
            "tuition_domestic": collection_result.tuition_domestic,
            "tuition_international": collection_result.tuition_international,
            "room_and_board": collection_result.room_and_board,
            "total_cost_of_attendance": collection_result.total_cost_of_attendance,
            "average_financial_aid_package": collection_result.average_financial_aid_package,
            "scholarships_available": collection_result.scholarships_available,
            "world_ranking": collection_result.world_ranking,
            "regional_ranking": collection_result.regional_ranking,
            "national_ranking": collection_result.national_ranking,
            "subject_rankings": collection_result.subject_rankings,
            "description": collection_result.description,
            "mission_statement": collection_result.mission_statement,
            "vision_statement": collection_result.vision_statement,
            "programs": collection_result.programs,
            "student_life": collection_result.student_life,
            "campus_size": collection_result.campus_size,
            "campus_type": collection_result.campus_type,
            "climate": collection_result.climate,
            "timezone": collection_result.timezone,
            "city": collection_result.city,
            "state": collection_result.state,
            "country": collection_result.country,
            "website": collection_result.website,
            "phone": collection_result.phone,
            "email": collection_result.email,
            "confidence_score": collection_result.confidence_score,
            "created_at": collection_result.created_at.isoformat() if collection_result.created_at else None,
            "updated_at": collection_result.updated_at.isoformat() if collection_result.updated_at else None
        }

    async def _generate_collection_match_reasons(self, user: User, collection_result: UniversityDataCollectionResult, similarity_score: float) -> List[str]:
        """Generate reasons why this collection result university matches the user"""
        
        reasons = []
        
        # High similarity score
        if similarity_score >= 0.9:
            reasons.append("Exceptional overall compatibility based on your profile")
        elif similarity_score >= 0.8:
            reasons.append("Excellent overall compatibility based on your profile")
        elif similarity_score >= 0.7:
            reasons.append("Strong compatibility with your academic and personal preferences")
        elif similarity_score >= 0.6:
            reasons.append("Good compatibility with your profile")
        elif similarity_score >= 0.5:
            reasons.append("Moderate compatibility with your profile")
        elif similarity_score >= 0.4:
            reasons.append("Some compatibility with your profile")
        elif similarity_score >= 0.35:
            reasons.append("Basic compatibility with your profile")
        else:
            reasons.append("Limited compatibility with your profile")
        
        # Major match
        if user.preferred_majors and collection_result.programs:
            try:
                programs_data = collection_result.programs
                if isinstance(programs_data, str):
                    programs_data = json.loads(programs_data)
                
                if isinstance(programs_data, list):
                    university_programs = []
                    for program in programs_data:
                        if isinstance(program, dict) and 'name' in program:
                            university_programs.append(program['name'].lower())
                        elif isinstance(program, dict) and 'field' in program:
                            university_programs.append(program['field'].lower())
                    
                    user_majors = [major.lower() for major in user.preferred_majors]
                    matching_majors = [major for major in user_majors if any(major in prog for prog in university_programs)]
                    
                    if matching_majors:
                        reasons.append(f"Offers your preferred major(s): {', '.join(matching_majors)}")
            except:
                pass
        
        # Location match
        if user.preferred_locations:
            if collection_result.city and collection_result.city in user.preferred_locations:
                reasons.append(f"Located in your preferred city: {collection_result.city}")
            elif collection_result.state and collection_result.state in user.preferred_locations:
                reasons.append(f"Located in your preferred state: {collection_result.state}")
            elif collection_result.country and collection_result.country in user.preferred_locations:
                reasons.append(f"Located in your preferred country: {collection_result.country}")
        
        # University type match
        if user.preferred_university_type and collection_result.type:
            if collection_result.type.lower() == user.preferred_university_type.lower():
                reasons.append(f"Matches your preferred university type: {collection_result.type}")
        
        # Academic fit
        if user.student_profile and user.student_profile.gpa and collection_result.acceptance_rate:
            if user.student_profile.gpa >= 3.5 and collection_result.acceptance_rate <= 0.3:
                reasons.append("Strong academic profile matches selective university")
            elif user.student_profile.gpa >= 3.0 and collection_result.acceptance_rate <= 0.5:
                reasons.append("Good academic fit for this university")
        
        # Financial fit
        if user.max_tuition and collection_result.tuition_domestic:
            if collection_result.tuition_domestic <= user.max_tuition:
                reasons.append(f"Tuition fits your budget: ${collection_result.tuition_domestic:,.0f}")
        
        # Student life match
        if collection_result.student_life:
            try:
                student_life_data = collection_result.student_life
                if isinstance(student_life_data, str):
                    student_life_data = json.loads(student_life_data)
                
                if isinstance(student_life_data, dict):
                    activities = []
                    for category, details in student_life_data.items():
                        if isinstance(details, dict) and 'activities' in details:
                            activities.extend(details['activities'])
                    
                    if activities:
                        reasons.append(f"Rich student life with {len(activities)} activities available")
            except:
                pass
        
        return reasons
    
    def _calculate_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """Calculate cosine similarity between two embeddings"""
        
        try:
            # Ensure embeddings are lists and have the right dimensions
            if not isinstance(embedding1, list):
                embedding1 = embedding1.tolist() if hasattr(embedding1, 'tolist') else list(embedding1)
            if not isinstance(embedding2, list):
                embedding2 = embedding2.tolist() if hasattr(embedding2, 'tolist') else list(embedding2)
            
            # Ensure both embeddings have the same length (1536)
            max_dimensions = 1536
            embedding1 = embedding1[:max_dimensions]
            embedding2 = embedding2[:max_dimensions]
            
            # Pad if needed
            while len(embedding1) < max_dimensions:
                embedding1.append(0.0)
            while len(embedding2) < max_dimensions:
                embedding2.append(0.0)
            
            # Convert to numpy arrays
            vec1 = np.array(embedding1, dtype=np.float64)
            vec2 = np.array(embedding2, dtype=np.float64)
            
            # Check for zero vectors
            if np.all(vec1 == 0) or np.all(vec2 == 0):
                logger.warning("Zero vector detected in similarity calculation")
                return 0.0
            
            # Calculate cosine similarity manually
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            
            # Check for division by zero
            if norm1 == 0 or norm2 == 0:
                logger.warning("Zero norm detected in similarity calculation")
                return 0.0
            
            raw_similarity = dot_product / (norm1 * norm2)
            
            # Convert cosine similarity from [-1, 1] to [0, 1] scale
            # This preserves the relative differences while making all values positive
            # Formula: (similarity + 1) / 2
            similarity = (raw_similarity + 1) / 2
            
            # Ensure similarity is between 0 and 1 (should already be, but just in case)
            similarity = max(0.0, min(1.0, similarity))
            
            return similarity
            
        except Exception as e:
            logger.error(f"Error calculating similarity: {e}")
            return 0.0
    
    async def _generate_match_reasons(self, user: User, university: University, similarity_score: float) -> List[str]:
        """Generate reasons why this university matches the user"""
        
        reasons = []
        
        # High similarity score
        if similarity_score >= 0.9:
            reasons.append("Exceptional overall compatibility based on your profile")
        elif similarity_score >= 0.8:
            reasons.append("Excellent overall compatibility based on your profile")
        elif similarity_score >= 0.7:
            reasons.append("Strong compatibility with your academic and personal preferences")
        elif similarity_score >= 0.6:
            reasons.append("Good compatibility with your profile")
        elif similarity_score >= 0.5:
            reasons.append("Moderate compatibility with your profile")
        elif similarity_score >= 0.45:
            reasons.append("Some compatibility with your profile")
        else:
            reasons.append("Limited compatibility with your profile")
        
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
        
        user_embedding = await self.generate_user_embedding(user, db)
        
        # Get all other users
        other_users = db.query(User).filter(User.id != user.id).all()
        
        similar_users = []
        
        for other_user in other_users:
            other_embedding = await self.generate_user_embedding(other_user, db)
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