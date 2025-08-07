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
    
    async def generate_personality_profile(
        self, 
        questionnaire_response
    ) -> Dict[str, Any]:
        """Generate personality profile using LLM"""
        
        # Extract answers and preferred majors from the questionnaire response
        answers = questionnaire_response.answers
        preferred_majors = questionnaire_response.preferred_majors or []
        
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
            
            # Generate concise summary
            summary = await self._generate_personality_summary(profile_data, answers, preferred_majors)
            profile_data['summary'] = summary
            
            return profile_data
            
        except Exception as e:
            # Fallback profile if LLM fails
            fallback_profile = self._create_fallback_profile(answers, preferred_majors)
            fallback_summary = self._create_fallback_summary(answers, preferred_majors)
            fallback_profile['summary'] = fallback_summary
            return fallback_profile

    async def _generate_personality_summary(
        self, 
        profile_data: Dict[str, Any], 
        answers: Dict[str, Any], 
        preferred_majors: List[str]
    ) -> str:
        """Generate a concise personality summary"""
        
        summary_prompt = f"""
        Based on the following personality profile and questionnaire responses, create a concise, engaging 2-3 sentence summary that captures the user's key personality traits, learning style, and academic interests. This summary should be written in a friendly, professional tone and highlight what makes this person unique.

        Personality Profile:
        {json.dumps(profile_data, indent=2)}

        Questionnaire Responses:
        {json.dumps(answers, indent=2)}

        Preferred Majors:
        {', '.join(preferred_majors)}

        Please write a concise summary (2-3 sentences) that includes:
        1. Key personality traits
        2. Learning style preference
        3. Academic/career interests
        4. What makes them unique

        Make it engaging and personal, as if describing a friend to someone.
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert at creating concise, engaging personality summaries. Write in a warm, professional tone that captures the essence of a person."
                    },
                    {
                        "role": "user",
                        "content": summary_prompt
                    }
                ],
                temperature=0.8,
                max_tokens=200
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            # Fallback summary
            return self._create_fallback_summary(answers, preferred_majors)

    def _create_fallback_summary(self, answers: Dict[str, Any], preferred_majors: List[str]) -> str:
        """Create a fallback summary when LLM fails"""
        
        # Extract key information from answers
        answer_text = str(answers).lower()
        
        # Determine personality traits
        traits = []
        if "introvert" in answer_text or "quiet" in answer_text:
            traits.append("introverted")
        elif "extrovert" in answer_text or "social" in answer_text:
            traits.append("outgoing")
        else:
            traits.append("balanced")
            
        if "analytical" in answer_text or "logical" in answer_text:
            traits.append("analytical")
        elif "creative" in answer_text or "artistic" in answer_text:
            traits.append("creative")
        else:
            traits.append("practical")
            
        # Determine learning style
        if "hands-on" in answer_text or "practical" in answer_text:
            learning_style = "hands-on learning"
        elif "visual" in answer_text or "see" in answer_text:
            learning_style = "visual learning"
        elif "read" in answer_text or "text" in answer_text:
            learning_style = "reading and writing"
        else:
            learning_style = "mixed learning approaches"
            
        # Create summary
        personality_desc = " and ".join(traits)
        majors_desc = ", ".join(preferred_majors) if preferred_majors else "various academic fields"
        
        return f"This {personality_desc} individual thrives on {learning_style} and shows strong interest in {majors_desc}. They approach challenges with determination and are eager to find the perfect academic environment to support their growth and development."
    
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