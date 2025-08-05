import openai
import os
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
import json
import numpy as np
import sys

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.models import User, University, Program, UserMatch
from database.database import get_db

class MatchingService:
    def __init__(self):
        self.client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        # Matching weights
        self.weights = {
            "academic_fit": 0.3,
            "financial_fit": 0.25,
            "location_fit": 0.2,
            "personality_fit": 0.25
        }
    
    async def generate_matches(self, user: User, db: Session) -> List[Dict[str, Any]]:
        """Generate matches for a user"""
        
        # Get all universities and programs
        universities = db.query(University).all()
        programs = db.query(Program).all()
        
        matches = []
        
        for university in universities:
            # Get programs for this university
            university_programs = [p for p in programs if p.university_id == university.id]
            
            if not university_programs:
                # Create a match with just the university
                match_score = await self._calculate_match_score(user, university, None)
                matches.append({
                    "university_id": university.id,
                    "program_id": None,
                    "overall_score": match_score["overall"],
                    "academic_fit_score": match_score["academic"],
                    "financial_fit_score": match_score["financial"],
                    "location_fit_score": match_score["location"],
                    "personality_fit_score": match_score["personality"],
                    "user_preferences": self._get_user_preferences(user)
                })
            else:
                # Create matches for each program
                for program in university_programs:
                    match_score = await self._calculate_match_score(user, university, program)
                    matches.append({
                        "university_id": university.id,
                        "program_id": program.id,
                        "overall_score": match_score["overall"],
                        "academic_fit_score": match_score["academic"],
                        "financial_fit_score": match_score["financial"],
                        "location_fit_score": match_score["location"],
                        "personality_fit_score": match_score["personality"],
                        "user_preferences": self._get_user_preferences(user)
                    })
        
        # Sort by overall score and return top matches
        matches.sort(key=lambda x: x["overall_score"], reverse=True)
        return matches[:20]  # Return top 20 matches
    
    async def _calculate_match_score(self, user: User, university: University, program: Program = None) -> Dict[str, float]:
        """Calculate match scores between user and university/program"""
        
        # Academic fit score
        academic_score = self._calculate_academic_fit(user, university, program)
        
        # Financial fit score
        financial_score = self._calculate_financial_fit(user, university, program)
        
        # Location fit score
        location_score = self._calculate_location_fit(user, university)
        
        # Personality fit score
        personality_score = await self._calculate_personality_fit(user, university, program)
        
        # Calculate overall score
        overall_score = (
            academic_score * self.weights["academic_fit"] +
            financial_score * self.weights["financial_fit"] +
            location_score * self.weights["location_fit"] +
            personality_score * self.weights["personality_fit"]
        )
        
        return {
            "overall": overall_score,
            "academic": academic_score,
            "financial": financial_score,
            "location": location_score,
            "personality": personality_score
        }
    
    def _calculate_academic_fit(self, user: User, university: University, program: Program = None) -> float:
        """Calculate academic fit score"""
        score = 0.5  # Base score
        
        # University acceptance rate fit
        if user.min_acceptance_rate and university.acceptance_rate:
            if university.acceptance_rate >= user.min_acceptance_rate:
                score += 0.2
            else:
                score -= 0.1
        
        # University ranking consideration
        if university.national_ranking:
            if university.national_ranking <= 50:
                score += 0.1
            elif university.national_ranking <= 100:
                score += 0.05
        
        # Program field match
        if program and user.preferred_majors:
            if program.field in user.preferred_majors:
                score += 0.2
            elif any(major.lower() in program.field.lower() for major in user.preferred_majors):
                score += 0.1
        
        return min(1.0, max(0.0, score))
    
    def _calculate_financial_fit(self, user: User, university: University, program: Program = None) -> float:
        """Calculate financial fit score"""
        score = 0.5  # Base score
        
        # Tuition fit
        if user.max_tuition and university.tuition_domestic:
            if university.tuition_domestic <= user.max_tuition:
                score += 0.3
            else:
                # Calculate how much over budget
                over_budget_ratio = (university.tuition_domestic - user.max_tuition) / user.max_tuition
                if over_budget_ratio <= 0.2:  # Within 20% of budget
                    score += 0.1
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
        
        return min(1.0, max(0.0, score))
    
    def _calculate_location_fit(self, user: User, university: University) -> float:
        """Calculate location fit score"""
        score = 0.5  # Base score
        
        # Location preference match
        if user.preferred_locations and university.city:
            if university.city in user.preferred_locations:
                score += 0.3
            elif university.state in user.preferred_locations:
                score += 0.2
            elif university.country in user.preferred_locations:
                score += 0.1
        
        # Climate and environment considerations could be added here
        
        return min(1.0, max(0.0, score))
    
    async def _calculate_personality_fit(self, user: User, university: University, program: Program = None) -> float:
        """Calculate personality fit score using LLM"""
        
        if not user.personality_profile:
            return 0.5  # Default score if no personality profile
        
        try:
            prompt = self._create_personality_match_prompt(user, university, program)
            
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
            # Fallback to basic personality matching
            return self._calculate_basic_personality_fit(user, university, program)
    
    def _create_personality_match_prompt(self, user: User, university: University, program: Program = None) -> str:
        """Create prompt for personality matching"""
        
        prompt = f"""
        Analyze the personality fit between a student and a university/program:

        Student Personality Profile:
        {json.dumps(user.personality_profile, indent=2)}

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

        Return only a number between 0 and 1.
        """
        
        return prompt
    
    def _extract_score_from_response(self, response_text: str) -> float:
        """Extract numerical score from LLM response"""
        try:
            # Look for numbers in the response
            import re
            numbers = re.findall(r'\d+\.?\d*', response_text)
            if numbers:
                score = float(numbers[0])
                return min(1.0, max(0.0, score))
            else:
                return 0.5
        except:
            return 0.5
    
    def _calculate_basic_personality_fit(self, user: User, university: University, program: Program = None) -> float:
        """Calculate basic personality fit without LLM"""
        score = 0.5  # Base score
        
        if not user.personality_profile:
            return score
        
        profile = user.personality_profile
        
        # Learning style compatibility
        if "learning_style" in profile:
            learning_style = profile["learning_style"].lower()
            if "kinesthetic" in learning_style and university.student_population and university.student_population > 10000:
                score += 0.1  # Large universities often have more hands-on opportunities
            elif "visual" in learning_style and university.facilities:
                score += 0.05  # Visual learners benefit from good facilities
        
        # Social environment preferences
        if "work_environment_preferences" in profile:
            env_prefs = profile["work_environment_preferences"]
            if "collaboration" in env_prefs:
                if env_prefs["collaboration"] == "high" and university.student_population and university.student_population > 5000:
                    score += 0.1  # Larger universities offer more collaboration opportunities
        
        # Communication style
        if "communication_style" in profile:
            comm_style = profile["communication_style"].lower()
            if "direct" in comm_style and university.type and "private" in university.type.lower():
                score += 0.05  # Private universities often have more direct communication
        
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