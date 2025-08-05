import openai
import os
from typing import Dict, Any, List
import json
from sqlalchemy.orm import Session
import sys

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.models import User
from database.database import get_db

class QuestionnaireService:
    def __init__(self):
        self.client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        # Standard questionnaire questions
        self.questions = {
            "learning_style": [
                "How do you prefer to learn new things?",
                "Do you prefer hands-on activities or theoretical study?",
                "How do you handle group projects vs individual work?"
            ],
            "personality": [
                "How would you describe your social energy level?",
                "Do you prefer structured environments or flexible ones?",
                "How do you handle stress and pressure?"
            ],
            "career_interests": [
                "What subjects do you enjoy most in school?",
                "What kind of problems do you like solving?",
                "What are your long-term career goals?"
            ],
            "study_preferences": [
                "How many hours can you dedicate to studying per week?",
                "Do you prefer online or in-person learning?",
                "What size of institution do you prefer?"
            ],
            "financial_preferences": [
                "What is your budget for tuition?",
                "Are you open to student loans?",
                "Do you qualify for financial aid?"
            ]
        }
    
    def get_questionnaire(self) -> Dict[str, List[str]]:
        """Get the standard questionnaire questions"""
        return self.questions
    
    async def generate_personality_profile(
        self, 
        answers: Dict[str, Any], 
        preferred_majors: List[str]
    ) -> Dict[str, Any]:
        """Generate personality profile using LLM"""
        
        prompt = self._create_personality_prompt(answers, preferred_majors)
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert career counselor and personality analyst. Analyze the user's responses and create a comprehensive personality profile that will help match them with suitable universities and programs."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7,
                max_tokens=1000
            )
            
            # Parse the response
            profile_text = response.choices[0].message.content
            
            # Try to extract structured data
            try:
                # Look for JSON-like structure in the response
                profile_data = self._extract_profile_data(profile_text)
            except:
                # Fallback to basic structure
                profile_data = self._create_basic_profile(profile_text, answers, preferred_majors)
            
            return profile_data
            
        except Exception as e:
            # Fallback profile if LLM fails
            return self._create_fallback_profile(answers, preferred_majors)
    
    def _create_personality_prompt(self, answers: Dict[str, Any], preferred_majors: List[str]) -> str:
        """Create prompt for personality analysis"""
        
        prompt = f"""
        Based on the following questionnaire responses and preferred majors, create a comprehensive personality profile:

        Questionnaire Responses:
        {json.dumps(answers, indent=2)}

        Preferred Majors:
        {', '.join(preferred_majors)}

        Please analyze this information and provide a structured personality profile including:
        1. Personality type (e.g., introvert/extrovert, analytical/creative, etc.)
        2. Learning style preferences
        3. Career interests and strengths
        4. Areas for development
        5. Study preferences
        6. Work environment preferences
        7. Communication style
        8. Leadership style
        9. Stress management approach
        10. Confidence score (0-1)

        Please format your response as a JSON object with these fields:
        {{
            "personality_type": "string",
            "learning_style": "string", 
            "career_interests": ["array of strings"],
            "strengths": ["array of strings"],
            "areas_for_development": ["array of strings"],
            "study_preferences": {{"key": "value"}},
            "work_environment_preferences": {{"key": "value"}},
            "communication_style": "string",
            "leadership_style": "string",
            "stress_management": "string",
            "confidence_score": 0.85
        }}
        """
        
        return prompt
    
    def _extract_profile_data(self, profile_text: str) -> Dict[str, Any]:
        """Extract structured data from LLM response"""
        try:
            # Try to find JSON in the response
            start_idx = profile_text.find('{')
            end_idx = profile_text.rfind('}') + 1
            
            if start_idx != -1 and end_idx != 0:
                json_str = profile_text[start_idx:end_idx]
                return json.loads(json_str)
            else:
                raise ValueError("No JSON found in response")
                
        except (json.JSONDecodeError, ValueError):
            raise ValueError("Could not parse JSON from response")
    
    def _create_basic_profile(self, profile_text: str, answers: Dict[str, Any], preferred_majors: List[str]) -> Dict[str, Any]:
        """Create basic profile structure from text response"""
        
        # Extract key information from answers
        learning_style = self._extract_learning_style(answers)
        personality_type = self._extract_personality_type(answers)
        
        return {
            "personality_type": personality_type,
            "learning_style": learning_style,
            "career_interests": preferred_majors,
            "strengths": self._extract_strengths(answers),
            "areas_for_development": self._extract_development_areas(answers),
            "study_preferences": {
                "preferred_environment": "flexible" if "flexible" in str(answers).lower() else "structured",
                "group_work": "preferred" if "group" in str(answers).lower() else "individual",
                "online_learning": "preferred" if "online" in str(answers).lower() else "in_person"
            },
            "work_environment_preferences": {
                "collaboration": "high" if "group" in str(answers).lower() else "low",
                "structure": "high" if "structured" in str(answers).lower() else "low"
            },
            "communication_style": "direct" if "direct" in str(answers).lower() else "diplomatic",
            "leadership_style": "collaborative" if "group" in str(answers).lower() else "independent",
            "stress_management": "proactive" if "plan" in str(answers).lower() else "adaptive",
            "confidence_score": 0.75
        }
    
    def _create_fallback_profile(self, answers: Dict[str, Any], preferred_majors: List[str]) -> Dict[str, Any]:
        """Create fallback profile when LLM fails"""
        return {
            "personality_type": "balanced",
            "learning_style": "mixed",
            "career_interests": preferred_majors,
            "strengths": ["adaptable", "motivated"],
            "areas_for_development": ["specific skills based on major"],
            "study_preferences": {
                "preferred_environment": "flexible",
                "group_work": "mixed",
                "online_learning": "mixed"
            },
            "work_environment_preferences": {
                "collaboration": "moderate",
                "structure": "moderate"
            },
            "communication_style": "balanced",
            "leadership_style": "situational",
            "stress_management": "adaptive",
            "confidence_score": 0.7
        }
    
    def _extract_learning_style(self, answers: Dict[str, Any]) -> str:
        """Extract learning style from answers"""
        answer_text = str(answers).lower()
        
        if "hands-on" in answer_text or "practical" in answer_text:
            return "kinesthetic"
        elif "visual" in answer_text or "see" in answer_text:
            return "visual"
        elif "audio" in answer_text or "hear" in answer_text:
            return "auditory"
        elif "read" in answer_text or "text" in answer_text:
            return "reading/writing"
        else:
            return "mixed"
    
    def _extract_personality_type(self, answers: Dict[str, Any]) -> str:
        """Extract personality type from answers"""
        answer_text = str(answers).lower()
        
        if "introvert" in answer_text or "quiet" in answer_text:
            return "introverted"
        elif "extrovert" in answer_text or "social" in answer_text:
            return "extroverted"
        else:
            return "ambivert"
    
    def _extract_strengths(self, answers: Dict[str, Any]) -> List[str]:
        """Extract strengths from answers"""
        strengths = []
        answer_text = str(answers).lower()
        
        if "analytical" in answer_text or "logical" in answer_text:
            strengths.append("analytical thinking")
        if "creative" in answer_text or "artistic" in answer_text:
            strengths.append("creativity")
        if "leadership" in answer_text or "organize" in answer_text:
            strengths.append("leadership")
        if "team" in answer_text or "collaborate" in answer_text:
            strengths.append("teamwork")
        
        if not strengths:
            strengths = ["motivated", "adaptable"]
        
        return strengths
    
    def _extract_development_areas(self, answers: Dict[str, Any]) -> List[str]:
        """Extract areas for development from answers"""
        areas = []
        answer_text = str(answers).lower()
        
        if "stress" in answer_text or "pressure" in answer_text:
            areas.append("stress management")
        if "public speaking" in answer_text or "presentation" in answer_text:
            areas.append("public speaking")
        if "time management" in answer_text:
            areas.append("time management")
        
        if not areas:
            areas = ["skill development in chosen field"]
        
        return areas 