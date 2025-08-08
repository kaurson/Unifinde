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

from database.models import User, StudentProfile, UniversityDataCollectionResult, CollectionResultVector
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
        """Generate embedding vector for university profile (legacy method)"""
        
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
        """Find university matches for a user using vector similarity (legacy method)"""
        
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

    async def find_collection_matches(self, user: User, db: Session, limit: int = 20) -> List[Dict[str, Any]]:
        """Find university matches for a user using pre-generated collection result vectors"""
        
        print(f"Starting collection matches for user: {user.email}")
        
        # Generate user embedding
        print("Generating user embedding...")
        user_embedding = await self.generate_user_embedding(user)
        print(f"User embedding generated with {len(user_embedding)} dimensions")
        
        # Validate user embedding
        if len(user_embedding) < 100:
            logger.error(f"User embedding too short: {len(user_embedding)} dimensions")
            return []
        
        if any(np.isnan(val) for val in user_embedding if isinstance(val, (int, float))):
            logger.error("User embedding contains NaN values")
            return []
        
        # Get all collection result vectors
        print("Querying collection vectors...")
        collection_vectors = db.query(CollectionResultVector).all()
        print(f"Found {len(collection_vectors)} collection vectors")
        
        if not collection_vectors:
            logger.warning("No collection result vectors found. Please generate vectors first.")
            return []
        
        matches = []
        
        for i, vector in enumerate(collection_vectors):
            print(f"Processing vector {i+1}/{len(collection_vectors)}")
            
            # Get the collection result data
            collection_result = db.query(UniversityDataCollectionResult).filter(
                UniversityDataCollectionResult.id == vector.collection_result_id
            ).first()
            
            if not collection_result:
                print(f"Warning: No collection result found for vector {vector.collection_result_id}")
                continue
            
            # Get the pre-generated embedding
            try:
                university_embedding = vector.get_embedding_array().tolist()
                print(f"Vector {i+1} embedding dimensions: {len(university_embedding)}")
                
                # Check if embedding is valid (accept both 1536 and 3072 dimensions)
                if len(university_embedding) < 100:
                    print(f"Skipping vector {i+1}: embedding too short ({len(university_embedding)} dimensions)")
                    continue
                
                # Clean NaN values instead of skipping
                cleaned_embedding = []
                nan_count = 0
                for val in university_embedding:
                    if isinstance(val, (int, float)) and not np.isnan(val):
                        cleaned_embedding.append(float(val))
                    else:
                        cleaned_embedding.append(0.0)
                        nan_count += 1
                
                if nan_count > 0:
                    print(f"Vector {i+1}: Cleaned {nan_count} NaN values")
                
                university_embedding = cleaned_embedding
                    
            except Exception as e:
                print(f"Error getting embedding for vector {i+1}: {e}")
                continue
            
            # Calculate similarity
            try:
                similarity_score = self._calculate_similarity(user_embedding, university_embedding)
                print(f"Vector {i+1} similarity score: {similarity_score}")
                
                # Skip if similarity calculation failed
                if similarity_score == 0.0 and len(university_embedding) > 100:
                    print(f"Skipping vector {i+1}: similarity calculation failed")
                    continue
                    
            except Exception as e:
                print(f"Error calculating similarity for vector {i+1}: {e}")
                continue
            
            # Create match object with rich data from collection result
            try:
                match = {
                    "university_id": str(collection_result.id),
                    "university_name": collection_result.name,
                    "similarity_score": similarity_score,
                    "university_data": self._collection_result_to_dict(collection_result),
                    "match_reasons": await self._generate_collection_match_reasons(user, collection_result, similarity_score),
                    "vector_data": {
                        "embedding_model": vector.embedding_model,
                        "embedding_dimension": vector.embedding_dimension,
                        "specialized_data": vector.specialized_data
                    }
                }
                
                # Only add matches with 35% or higher similarity
                if similarity_score >= 0.4:  # Lowered threshold to get reasonable number of quality matches
                    matches.append(match)
                    print(f"Added match for {collection_result.name} (score: {similarity_score:.3f})")
                else:
                    print(f"Skipped {collection_result.name} (score: {similarity_score:.3f} < 0.35)")
                    
            except Exception as e:
                print(f"Error creating match for vector {i+1}: {e}")
                continue
        
        print(f"Created {len(matches)} matches")
        
        # Sort by similarity score and return top matches
        matches.sort(key=lambda x: x["similarity_score"], reverse=True)
        result = matches[:limit]
        print(f"Returning top {len(result)} matches")
        return result

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
            # Clean embeddings - remove NaN values and ensure they're valid
            def clean_embedding(embedding):
                # Convert to list if it's not already
                if not isinstance(embedding, list):
                    embedding = embedding.tolist() if hasattr(embedding, 'tolist') else list(embedding)
                
                # Remove NaN values and replace with 0
                cleaned = []
                for val in embedding:
                    if isinstance(val, (int, float)) and not np.isnan(val) and not np.isinf(val):
                        cleaned.append(float(val))
                    else:
                        cleaned.append(0.0)
                
                return cleaned
            
            embedding1 = clean_embedding(embedding1)
            embedding2 = clean_embedding(embedding2)
            
            # Use only the first 1536 dimensions for consistency
            max_dimensions = 1536
            embedding1 = embedding1[:max_dimensions]
            embedding2 = embedding2[:max_dimensions]
            
            # Pad if needed
            while len(embedding1) < max_dimensions:
                embedding1.append(0.0)
            while len(embedding2) < max_dimensions:
                embedding2.append(0.0)
            
            # Convert to numpy arrays
            vec1 = np.array(embedding1)
            vec2 = np.array(embedding2)
            
            # Check for zero vectors
            if np.all(vec1 == 0) or np.all(vec2 == 0):
                print(f"Warning: Zero vector detected - vec1 sum: {np.sum(vec1)}, vec2 sum: {np.sum(vec2)}")
                return 0.0
            
            # Calculate cosine similarity manually
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            
            # Check for division by zero
            if norm1 == 0 or norm2 == 0:
                print(f"Warning: Zero norm detected - norm1: {norm1}, norm2: {norm2}")
                return 0.0
            
            similarity = dot_product / (norm1 * norm2)
            
            # Ensure similarity is between 0 and 1
            similarity = max(0.0, min(1.0, similarity))
            
            # Debug info
            print(f"Debug - dot_product: {dot_product:.6f}, norm1: {norm1:.6f}, norm2: {norm2:.6f}, similarity: {similarity:.6f}")
            
            return similarity
            
        except Exception as e:
            print(f"Error calculating similarity: {e}")
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