import openai
import os
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session
import json
import numpy as np
import sys
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass
from enum import Enum

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.models import User, StudentProfile, UserVector, UniversityVector, VectorSearchCache
from app.models import University, Program
from database.database import get_db
from api.vector_matcher import VectorMatchingService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MatchType(Enum):
    PERFECT = "perfect"
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"

@dataclass
class MatchScore:
    overall: float
    academic: float
    financial: float
    location: float
    personality: float
    career: float
    social: float
    
    def to_dict(self) -> Dict[str, float]:
        return {
            "overall": self.overall,
            "academic": self.academic,
            "financial": self.financial,
            "location": self.location,
            "personality": self.personality,
            "career": self.career,
            "social": self.social
        }

@dataclass
class MatchResult:
    university_id: str
    program_id: Optional[str]
    university_name: str
    program_name: Optional[str]
    match_score: MatchScore
    match_type: MatchType
    confidence: str
    reasons: List[str]
    warnings: List[str]
    university_data: Dict[str, Any]
    program_data: Optional[Dict[str, Any]]
    matching_method: str
    similarity_score: float
    user_preferences: Dict[str, Any]
    created_at: datetime

class EnhancedMatchingService:
    def __init__(self):
        self.client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.vector_matcher = VectorMatchingService()
        
        # Enhanced matching weights with more granular categories
        self.weights = {
            "academic_fit": 0.25,
            "financial_fit": 0.20,
            "location_fit": 0.15,
            "personality_fit": 0.20,
            "career_fit": 0.10,
            "social_fit": 0.10
        }
        
        # Score thresholds for match types
        self.score_thresholds = {
            MatchType.PERFECT: 0.9,
            MatchType.EXCELLENT: 0.8,
            MatchType.GOOD: 0.7,
            MatchType.FAIR: 0.6,
            MatchType.POOR: 0.0
        }
    
    async def generate_enhanced_matches(
        self, 
        user: User, 
        db: Session, 
        use_vector_matching: bool = True, 
        limit: int = 20,
        include_programs: bool = True,
        min_score: float = 0.5
    ) -> List[MatchResult]:
        """Generate enhanced matches with detailed scoring and analysis"""
        
        # Check cache first
        cache_key = self._generate_cache_key(user, use_vector_matching, limit, include_programs, min_score)
        cached_result = await self._get_cached_matches(cache_key, db)
        if cached_result:
            return cached_result
        
        if use_vector_matching:
            matches = await self._generate_enhanced_vector_matches(user, db, limit, include_programs, min_score)
        else:
            matches = await self._generate_enhanced_traditional_matches(user, db, limit, include_programs, min_score)
        
        # Cache the results
        await self._cache_matches(cache_key, matches, db)
        
        return matches
    
    async def _generate_enhanced_vector_matches(
        self, 
        user: User, 
        db: Session, 
        limit: int, 
        include_programs: bool,
        min_score: float
    ) -> List[MatchResult]:
        """Generate enhanced matches using vector similarity with detailed analysis"""
        
        try:
            # Get vector matches
            vector_matches = await self.vector_matcher.find_matches(user, db, limit * 2)  # Get more for filtering
            
            enhanced_matches = []
            
            for match in vector_matches:
                university_id = match["university_id"]
                university = db.query(University).filter(University.id == university_id).first()
                
                if not university:
                    continue
                
                # Get programs if requested
                programs = []
                if include_programs:
                    programs = db.query(Program).filter(Program.university_id == university_id).all()
                
                if programs:
                    # Create match for each program
                    for program in programs:
                        match_score = await self._calculate_enhanced_match_score(user, university, program)
                        
                        if match_score.overall >= min_score:
                            match_result = await self._create_enhanced_match_result(
                                user, university, program, match_score, match["similarity_score"], "vector_similarity"
                            )
                            enhanced_matches.append(match_result)
                else:
                    # Create match for university only
                    match_score = await self._calculate_enhanced_match_score(user, university, None)
                    
                    if match_score.overall >= min_score:
                        match_result = await self._create_enhanced_match_result(
                            user, university, None, match_score, match["similarity_score"], "vector_similarity"
                        )
                        enhanced_matches.append(match_result)
            
            # Sort by overall score and return top matches
            enhanced_matches.sort(key=lambda x: x.match_score.overall, reverse=True)
            return enhanced_matches[:limit]
            
        except Exception as e:
            logger.error(f"Error in enhanced vector matching: {e}")
            # Fallback to traditional matching
            return await self._generate_enhanced_traditional_matches(user, db, limit, include_programs, min_score)
    
    async def _generate_enhanced_traditional_matches(
        self, 
        user: User, 
        db: Session, 
        limit: int, 
        include_programs: bool,
        min_score: float
    ) -> List[MatchResult]:
        """Generate enhanced matches using traditional scoring with detailed analysis"""
        
        universities = db.query(University).all()
        enhanced_matches = []
        
        for university in universities:
            programs = []
            if include_programs:
                programs = db.query(Program).filter(Program.university_id == university.id).all()
            
            if programs:
                # Create match for each program
                for program in programs:
                    match_score = await self._calculate_enhanced_match_score(user, university, program)
                    
                    if match_score.overall >= min_score:
                        match_result = await self._create_enhanced_match_result(
                            user, university, program, match_score, match_score.overall, "traditional_scoring"
                        )
                        enhanced_matches.append(match_result)
            else:
                # Create match for university only
                match_score = await self._calculate_enhanced_match_score(user, university, None)
                
                if match_score.overall >= min_score:
                    match_result = await self._create_enhanced_match_result(
                        user, university, None, match_score, match_score.overall, "traditional_scoring"
                    )
                    enhanced_matches.append(match_result)
        
        # Sort by overall score and return top matches
        enhanced_matches.sort(key=lambda x: x.match_score.overall, reverse=True)
        return enhanced_matches[:limit]
    
    async def _calculate_enhanced_match_score(
        self, 
        user: User, 
        university: University, 
        program: Optional[Program] = None
    ) -> MatchScore:
        """Calculate comprehensive match scores with enhanced criteria"""
        
        # Calculate individual scores
        academic_score = await self._calculate_enhanced_academic_fit(user, university, program)
        financial_score = await self._calculate_enhanced_financial_fit(user, university, program)
        location_score = await self._calculate_enhanced_location_fit(user, university)
        personality_score = await self._calculate_enhanced_personality_fit(user, university, program)
        career_score = await self._calculate_enhanced_career_fit(user, university, program)
        social_score = await self._calculate_enhanced_social_fit(user, university)
        
        # Calculate overall score
        overall_score = (
            academic_score * self.weights["academic_fit"] +
            financial_score * self.weights["financial_fit"] +
            location_score * self.weights["location_fit"] +
            personality_score * self.weights["personality_fit"] +
            career_score * self.weights["career_fit"] +
            social_score * self.weights["social_fit"]
        )
        
        return MatchScore(
            overall=overall_score,
            academic=academic_score,
            financial=financial_score,
            location=location_score,
            personality=personality_score,
            career=career_score,
            social=social_score
        )
    
    async def _calculate_enhanced_academic_fit(
        self, 
        user: User, 
        university: University, 
        program: Optional[Program] = None
    ) -> float:
        """Calculate enhanced academic fit score"""
        score = 0.5  # Base score
        
        # University acceptance rate fit
        if user.min_acceptance_rate and university.acceptance_rate:
            if university.acceptance_rate >= user.min_acceptance_rate:
                score += 0.2
            else:
                # Gradual penalty based on how far below the threshold
                penalty = min(0.2, (user.min_acceptance_rate - university.acceptance_rate) * 2)
                score -= penalty
        
        # University ranking consideration
        if university.national_ranking:
            if university.national_ranking <= 10:
                score += 0.15
            elif university.national_ranking <= 25:
                score += 0.12
            elif university.national_ranking <= 50:
                score += 0.10
            elif university.national_ranking <= 100:
                score += 0.05
        
        # Program field match
        if program and user.preferred_majors:
            if program.field in user.preferred_majors:
                score += 0.25
            elif any(major.lower() in program.field.lower() for major in user.preferred_majors):
                score += 0.15
            elif any(program.field.lower() in major.lower() for major in user.preferred_majors):
                score += 0.10
        
        # Student profile academic fit
        if user.student_profile:
            student = user.student_profile
            
            # GPA consideration
            if student.gpa and university.acceptance_rate:
                if student.gpa >= 3.8 and university.acceptance_rate <= 0.2:
                    score += 0.1
                elif student.gpa >= 3.5 and university.acceptance_rate <= 0.3:
                    score += 0.08
                elif student.gpa >= 3.0 and university.acceptance_rate <= 0.5:
                    score += 0.05
            
            # Test scores consideration
            if student.sat_total and university.acceptance_rate:
                if student.sat_total >= 1400 and university.acceptance_rate <= 0.2:
                    score += 0.08
                elif student.sat_total >= 1300 and university.acceptance_rate <= 0.3:
                    score += 0.05
            
            # Research experience bonus for research universities
            if student.research_experience and university.type:
                if "research" in university.type.lower() or university.faculty_count and university.faculty_count > 500:
                    score += 0.05
        
        return min(1.0, max(0.0, score))
    
    async def _calculate_enhanced_financial_fit(
        self, 
        user: User, 
        university: University, 
        program: Optional[Program] = None
    ) -> float:
        """Calculate enhanced financial fit score"""
        score = 0.5  # Base score
        
        # Tuition fit
        if user.max_tuition and university.tuition_domestic:
            if university.tuition_domestic <= user.max_tuition:
                score += 0.3
            else:
                # Calculate how much over budget
                over_budget_ratio = (university.tuition_domestic - user.max_tuition) / user.max_tuition
                if over_budget_ratio <= 0.1:  # Within 10% of budget
                    score += 0.15
                elif over_budget_ratio <= 0.2:  # Within 20% of budget
                    score += 0.05
                else:
                    score -= 0.2
        
        # University type preference
        if user.preferred_university_type and university.type:
            if university.type.lower() == user.preferred_university_type.lower():
                score += 0.1
        
        # Program-specific tuition
        if program and program.tuition and user.max_tuition:
            if program.tuition <= user.max_tuition:
                score += 0.1
            else:
                over_budget_ratio = (program.tuition - user.max_tuition) / user.max_tuition
                if over_budget_ratio <= 0.1:
                    score += 0.05
        
        # Financial aid consideration
        if user.student_profile and user.student_profile.financial_aid_needed:
            if university.tuition_domestic and university.tuition_domestic > 30000:
                # Private universities often have more financial aid
                if university.type and "private" in university.type.lower():
                    score += 0.05
        
        # Income-based considerations
        if user.income and university.tuition_domestic:
            income_to_tuition_ratio = user.income / university.tuition_domestic
            if income_to_tuition_ratio >= 3:
                score += 0.1
            elif income_to_tuition_ratio >= 2:
                score += 0.05
        
        return min(1.0, max(0.0, score))
    
    async def _calculate_enhanced_location_fit(self, user: User, university: University) -> float:
        """Calculate enhanced location fit score"""
        score = 0.5  # Base score
        
        # Location preference match
        if user.preferred_locations and university.city:
            if university.city in user.preferred_locations:
                score += 0.3
            elif university.state in user.preferred_locations:
                score += 0.2
            elif university.country in user.preferred_locations:
                score += 0.1
        
        # Climate considerations (if available)
        # This could be enhanced with actual climate data
        
        # Urban/rural preference
        if user.student_profile and user.student_profile.preferred_campus_environment:
            env_prefs = user.student_profile.preferred_campus_environment
            if university.student_population:
                if university.student_population > 20000 and "urban" in env_prefs:
                    score += 0.1
                elif university.student_population < 5000 and "rural" in env_prefs:
                    score += 0.1
        
        return min(1.0, max(0.0, score))
    
    async def _calculate_enhanced_personality_fit(
        self, 
        user: User, 
        university: University, 
        program: Optional[Program] = None
    ) -> float:
        """Calculate enhanced personality fit score using LLM"""
        
        if not user.personality_profile:
            return 0.5  # Default score if no personality profile
        
        try:
            prompt = self._create_enhanced_personality_match_prompt(user, university, program)
            
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert in matching students with universities based on personality fit. Analyze the compatibility and return a score between 0 and 1."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,
                max_tokens=100
            )
            
            # Extract score from response
            response_text = response.choices[0].message.content
            score = self._extract_score_from_response(response_text)
            
            return score
            
        except Exception as e:
            logger.error(f"Error in personality matching: {e}")
            # Fallback to basic personality matching
            return self._calculate_basic_personality_fit(user, university, program)
    
    async def _calculate_enhanced_career_fit(
        self, 
        user: User, 
        university: University, 
        program: Optional[Program] = None
    ) -> float:
        """Calculate enhanced career fit score"""
        score = 0.5  # Base score
        
        if user.student_profile:
            student = user.student_profile
            
            # Career aspirations match
            if student.career_aspirations and program and program.field:
                career_lower = student.career_aspirations.lower()
                field_lower = program.field.lower()
                
                if field_lower in career_lower or career_lower in field_lower:
                    score += 0.2
                elif any(word in career_lower for word in field_lower.split()):
                    score += 0.1
            
            # Industry preferences match
            if student.industry_preferences and program:
                for industry in student.industry_preferences:
                    if industry.lower() in program.field.lower():
                        score += 0.1
                        break
            
            # University reputation for career outcomes
            if university.national_ranking and university.national_ranking <= 50:
                score += 0.1
            
            # Alumni network consideration
            if university.student_population and university.student_population > 10000:
                score += 0.05  # Larger universities often have larger alumni networks
        
        return min(1.0, max(0.0, score))
    
    async def _calculate_enhanced_social_fit(self, user: User, university: University) -> float:
        """Calculate enhanced social fit score"""
        score = 0.5  # Base score
        
        # Student population size preference
        if user.student_profile and user.student_profile.preferred_class_size:
            class_size_pref = user.student_profile.preferred_class_size.lower()
            
            if university.student_population:
                if class_size_pref == "small" and university.student_population < 5000:
                    score += 0.15
                elif class_size_pref == "medium" and 5000 <= university.student_population <= 15000:
                    score += 0.15
                elif class_size_pref == "large" and university.student_population > 15000:
                    score += 0.15
        
        # Extracurricular opportunities
        if user.student_profile:
            student = user.student_profile
            
            # Sports activities
            if student.sports_activities and university.student_population:
                if university.student_population > 10000:
                    score += 0.05  # Larger universities typically have more sports opportunities
            
            # Leadership opportunities
            if student.leadership_positions and university.student_population:
                if university.student_population > 5000:
                    score += 0.05  # More opportunities for leadership in larger universities
        
        return min(1.0, max(0.0, score))
    
    async def _create_enhanced_match_result(
        self,
        user: User,
        university: University,
        program: Optional[Program],
        match_score: MatchScore,
        similarity_score: float,
        matching_method: str
    ) -> MatchResult:
        """Create an enhanced match result with detailed analysis"""
        
        # Determine match type
        match_type = self._determine_match_type(match_score.overall)
        
        # Generate reasons and warnings
        reasons = await self._generate_match_reasons(user, university, program, match_score)
        warnings = await self._generate_match_warnings(user, university, program, match_score)
        
        # Determine confidence level
        confidence = self._calculate_confidence_level(match_score.overall, len(reasons), len(warnings))
        
        return MatchResult(
            university_id=str(university.id),
            program_id=str(program.id) if program else None,
            university_name=university.name,
            program_name=program.name if program else None,
            match_score=match_score,
            match_type=match_type,
            confidence=confidence,
            reasons=reasons,
            warnings=warnings,
            university_data=university.to_dict(),
            program_data=program.to_dict() if program else None,
            matching_method=matching_method,
            similarity_score=similarity_score,
            user_preferences=self._get_user_preferences(user),
            created_at=datetime.now()
        )
    
    def _determine_match_type(self, overall_score: float) -> MatchType:
        """Determine match type based on overall score"""
        for match_type, threshold in sorted(self.score_thresholds.items(), key=lambda x: x[1], reverse=True):
            if overall_score >= threshold:
                return match_type
        return MatchType.POOR
    
    def _calculate_confidence_level(self, score: float, reasons_count: int, warnings_count: int) -> str:
        """Calculate confidence level based on score and analysis quality"""
        if score >= 0.8 and reasons_count >= 3 and warnings_count == 0:
            return "very_high"
        elif score >= 0.7 and reasons_count >= 2:
            return "high"
        elif score >= 0.6 and reasons_count >= 1:
            return "medium"
        elif score >= 0.5:
            return "low"
        else:
            return "very_low"
    
    async def _generate_match_reasons(
        self,
        user: User,
        university: University,
        program: Optional[Program],
        match_score: MatchScore
    ) -> List[str]:
        """Generate detailed reasons for the match"""
        reasons = []
        
        # Academic reasons
        if match_score.academic > 0.7:
            reasons.append("Strong academic fit with your profile")
        elif match_score.academic > 0.6:
            reasons.append("Good academic compatibility")
        
        # Financial reasons
        if match_score.financial > 0.8:
            reasons.append("Excellent financial fit within your budget")
        elif match_score.financial > 0.7:
            reasons.append("Good financial compatibility")
        
        # Location reasons
        if match_score.location > 0.7:
            reasons.append("Location matches your preferences")
        
        # Personality reasons
        if match_score.personality > 0.7:
            reasons.append("Strong personality and learning style compatibility")
        
        # Career reasons
        if match_score.career > 0.7:
            reasons.append("Excellent alignment with your career goals")
        
        # Social reasons
        if match_score.social > 0.7:
            reasons.append("Good social environment fit")
        
        # Specific program match
        if program and user.preferred_majors:
            if program.field in user.preferred_majors:
                reasons.append(f"Offers your preferred major: {program.field}")
        
        # University ranking
        if university.national_ranking and university.national_ranking <= 50:
            reasons.append(f"Top-ranked university (#{university.national_ranking} nationally)")
        
        return reasons
    
    async def _generate_match_warnings(
        self,
        user: User,
        university: University,
        program: Optional[Program],
        match_score: MatchScore
    ) -> List[str]:
        """Generate warnings about potential issues"""
        warnings = []
        
        # Financial warnings
        if match_score.financial < 0.6:
            if user.max_tuition and university.tuition_domestic:
                if university.tuition_domestic > user.max_tuition:
                    over_budget = university.tuition_domestic - user.max_tuition
                    warnings.append(f"Tuition ${over_budget:,.0f} over your budget")
        
        # Academic warnings
        if match_score.academic < 0.6:
            if user.min_acceptance_rate and university.acceptance_rate:
                if university.acceptance_rate < user.min_acceptance_rate:
                    warnings.append("Very competitive admission requirements")
        
        # Location warnings
        if match_score.location < 0.5:
            warnings.append("Location may not match your preferences")
        
        # Program warnings
        if program and user.preferred_majors:
            if program.field not in user.preferred_majors:
                warnings.append(f"Program field ({program.field}) not in your preferred majors")
        
        return warnings
    
    def _create_enhanced_personality_match_prompt(
        self, 
        user: User, 
        university: University, 
        program: Optional[Program] = None
    ) -> str:
        """Create enhanced prompt for personality matching"""
        
        prompt = f"""
        Analyze the personality fit between a student and a university/program:

        Student Personality Profile:
        {json.dumps(user.personality_profile, indent=2)}

        Student Profile Information:
        {self._get_student_profile_text(user)}

        University Information:
        - Name: {university.name}
        - Type: {university.type}
        - Location: {university.city}, {university.state}, {university.country}
        - Student Population: {university.student_population}
        - Description: {university.description}

        Program Information:
        {f"- Name: {program.name}" if program else "- No specific program"}
        {f"- Field: {program.field}" if program else ""}
        {f"- Level: {program.level}" if program else ""}

        Based on this information, rate the personality fit between 0 and 1, where:
        0 = Poor fit (personality and environment are incompatible)
        0.5 = Neutral fit (some compatibility, some differences)
        1 = Excellent fit (personality and environment are highly compatible)

        Consider factors like:
        - Learning style compatibility
        - Social environment preferences
        - Work environment preferences
        - Communication style fit
        - Leadership style alignment
        - Stress tolerance and academic rigor
        - Cultural fit and diversity preferences

        Return only a number between 0 and 1.
        """
        
        return prompt
    
    def _get_student_profile_text(self, user: User) -> str:
        """Get student profile information as text"""
        if not user.student_profile:
            return "No student profile available"
        
        student = user.student_profile
        profile_parts = []
        
        if student.gpa:
            profile_parts.append(f"GPA: {student.gpa}")
        
        if student.preferred_class_size:
            profile_parts.append(f"Preferred class size: {student.preferred_class_size}")
        
        if student.preferred_teaching_style:
            profile_parts.append(f"Preferred teaching style: {', '.join(student.preferred_teaching_style)}")
        
        if student.preferred_campus_environment:
            profile_parts.append(f"Preferred campus environment: {', '.join(student.preferred_campus_environment)}")
        
        if student.career_aspirations:
            profile_parts.append(f"Career aspirations: {student.career_aspirations}")
        
        return "\n".join(profile_parts) if profile_parts else "Limited student profile information"
    
    def _extract_score_from_response(self, response_text: str) -> float:
        """Extract numerical score from LLM response"""
        try:
            import re
            numbers = re.findall(r'\d+\.?\d*', response_text)
            if numbers:
                score = float(numbers[0])
                return min(1.0, max(0.0, score))
            else:
                return 0.5
        except:
            return 0.5
    
    def _calculate_basic_personality_fit(
        self, 
        user: User, 
        university: University, 
        program: Optional[Program] = None
    ) -> float:
        """Calculate basic personality fit without LLM"""
        score = 0.5  # Base score
        
        if not user.personality_profile:
            return score
        
        profile = user.personality_profile
        
        # Learning style compatibility
        if "learning_style" in profile:
            learning_style = profile["learning_style"].lower()
            if "kinesthetic" in learning_style and university.student_population and university.student_population > 10000:
                score += 0.1
            elif "visual" in learning_style and university.facilities:
                score += 0.05
        
        # Social environment preferences
        if "work_environment_preferences" in profile:
            env_prefs = profile["work_environment_preferences"]
            if "collaboration" in env_prefs:
                if env_prefs["collaboration"] == "high" and university.student_population and university.student_population > 5000:
                    score += 0.1
        
        return min(1.0, max(0.0, score))
    
    def _get_user_preferences(self, user: User) -> Dict[str, Any]:
        """Get user preferences for matching"""
        return {
            "preferred_majors": user.preferred_majors,
            "preferred_locations": user.preferred_locations,
            "min_acceptance_rate": user.min_acceptance_rate,
            "max_tuition": user.max_tuition,
            "preferred_university_type": user.preferred_university_type
        }
    
    def _generate_cache_key(
        self, 
        user: User, 
        use_vector_matching: bool, 
        limit: int, 
        include_programs: bool, 
        min_score: float
    ) -> str:
        """Generate cache key for match results"""
        import hashlib
        
        key_data = {
            "user_id": str(user.id),
            "use_vector_matching": use_vector_matching,
            "limit": limit,
            "include_programs": include_programs,
            "min_score": min_score,
            "user_updated": user.updated_at.isoformat() if user.updated_at else None
        }
        
        key_string = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    async def _get_cached_matches(self, cache_key: str, db: Session) -> Optional[List[MatchResult]]:
        """Get cached match results"""
        try:
            cache_entry = db.query(VectorSearchCache).filter(
                VectorSearchCache.cache_key == cache_key,
                VectorSearchCache.expires_at > datetime.now()
            ).first()
            
            if cache_entry:
                # Convert cached results back to MatchResult objects
                cached_data = cache_entry.results
                return [self._dict_to_match_result(match_dict) for match_dict in cached_data]
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting cached matches: {e}")
            return None
    
    async def _cache_matches(self, cache_key: str, matches: List[MatchResult], db: Session):
        """Cache match results"""
        try:
            # Convert MatchResult objects to dictionaries
            match_dicts = [self._match_result_to_dict(match) for match in matches]
            
            # Create or update cache entry
            cache_entry = db.query(VectorSearchCache).filter(
                VectorSearchCache.cache_key == cache_key
            ).first()
            
            if cache_entry:
                cache_entry.results = match_dicts
                cache_entry.expires_at = datetime.now() + timedelta(hours=1)
            else:
                # Use the first match's university_id as user_id for cache (since this is university matching)
                user_id = matches[0].university_id if matches else None
                cache_entry = VectorSearchCache(
                    user_id=user_id,
                    search_type="enhanced_university_match",
                    embedding_model="text-embedding-3-small",
                    results=match_dicts,
                    cache_key=cache_key,
                    expires_at=datetime.now() + timedelta(hours=1)
                )
                db.add(cache_entry)
            
            db.commit()
            
        except Exception as e:
            logger.error(f"Error caching matches: {e}")
            db.rollback()
    
    def _match_result_to_dict(self, match: MatchResult) -> Dict[str, Any]:
        """Convert MatchResult to dictionary for caching"""
        return {
            "university_id": match.university_id,
            "program_id": match.program_id,
            "university_name": match.university_name,
            "program_name": match.program_name,
            "match_score": match.match_score.to_dict(),
            "match_type": match.match_type.value,
            "confidence": match.confidence,
            "reasons": match.reasons,
            "warnings": match.warnings,
            "university_data": match.university_data,
            "program_data": match.program_data,
            "matching_method": match.matching_method,
            "similarity_score": match.similarity_score,
            "user_preferences": match.user_preferences,
            "created_at": match.created_at.isoformat()
        }
    
    def _dict_to_match_result(self, match_dict: Dict[str, Any]) -> MatchResult:
        """Convert dictionary back to MatchResult"""
        return MatchResult(
            university_id=match_dict["university_id"],
            program_id=match_dict["program_id"],
            university_name=match_dict["university_name"],
            program_name=match_dict["program_name"],
            match_score=MatchScore(**match_dict["match_score"]),
            match_type=MatchType(match_dict["match_type"]),
            confidence=match_dict["confidence"],
            reasons=match_dict["reasons"],
            warnings=match_dict["warnings"],
            university_data=match_dict["university_data"],
            program_data=match_dict["program_data"],
            matching_method=match_dict["matching_method"],
            similarity_score=match_dict["similarity_score"],
            user_preferences=match_dict["user_preferences"],
            created_at=datetime.fromisoformat(match_dict["created_at"])
        )
    
    def clear_cache(self):
        """Clear the vector matching cache"""
        self.vector_matcher.clear_cache() 