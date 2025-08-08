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

# Import the matching prompt
MATCHING_PROMPT = """
You are a psychologist and counselor with 20+ years of experience helping tens of thousands of students find their career path and plan out their educational journey after high school. You ask the same 23 questions of everyone, and based on their answers, you will conduct a thorough analysis of their profile. The importance, weight of all questions and answers are equal when conducting the analysis. First, give a quick personality snapshot. Then give the top 3 most suitable university types with qualities for the profile. Provide a reason why each of these university types with these qualities is on the list, based on the profile's answers, and why in that order. Then give the profile, based on the questionnaire answers, ranging from 1, the best, to 10, a list of countries the profile is most suitable for studying in. Provide a reason why each of these countries is on the list, based on the profile's answers, and why in that order. Then give notes, insights about what campus and environment are most suitable for the profile. The information should be: climate, campus type, size physically + student body, student life, sports, financial aid/ scholarships, location like city + size, university type, world ranking, and majors' rankings in the world.
This is the questionnaire:
Would you rather marry Stephen Hawking or a short shelf-life chocolate cake?
Who is/was your childhood celebrity crush?
Do you put bread in the fridge or the cabinet? 
Has evolution changed your life?
Do you thank ChatGPT? Why?
Your most unpopular opinion.	
What is the acceptable height of a sock starting from the ankle? 
Beans? breakfast / lunch / midnight snack
Why did the chicken come before the egg?
Why did the egg come before the chicken?
Diving into the Mariana Trench or climbing Mount Everest?
How many people do you need to steal a car? 0 - 10
Who's your favourite villain?
One piece of gum left, and your friend asks for one? Take turns chewing it / chew it together at the same time / take it yourself / throw it away (no one deserves it) / Give it to your friend
Would you rather have the professors send you streak snaps or them never even knowing your name?
How many "in one" does your shampoo have?
In what order do you dry yourself after a shower?
The Trolley problem.  A trolley is heading toward 5 people. You can pull a lever to divert it, but it will hit your grandma, who's going to die soon anyway. Do you pull the lever?
Would you rather be a boulder or a grain of sand?
Cereal or milk first?
Best Ice Cream flavour?
Would you rather live in an apartment but on the first floor, or in a house but only in the attic? 
Favorite internet trend?

Note: Question 12 tells whether the profile is a team person or solo. Question 15 tells whether the profile likes a big student body or a small one. Question 19 tells whether the profile likes to have more presence and live in an environment where one can be more noticeable, or be a grain of sand that wants to be part of a big world but play a small role, be a small part of it. Question 22 tells whether you would like to live in a smaller space but see more, rather than live in a bigger space but not see, experience as much. It also tells whether having more material value balances the inability to enjoy your environment as much, or giving up more on the material value to experience more.
"""

class QuestionnaireService:
    def __init__(self):
        self.client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    async def generate_personality_profile(
        self, 
        questionnaire_response
    ) -> Dict[str, Any]:
        """Generate personality profile using the matching prompt"""
        
        # Extract answers and preferred majors from the questionnaire response
        answers = questionnaire_response.answers
        preferred_majors = questionnaire_response.preferred_majors or []
        
        prompt = self._create_matching_prompt(answers, preferred_majors)
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": MATCHING_PROMPT
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7,
                max_tokens=1500
            )
            
            # Parse the response
            profile_text = response.choices[0].message.content
            
            # Generate concise summary
            summary = await self._generate_personality_summary(profile_text, answers, preferred_majors)
            
            # Create structured profile data
            profile_data = {
                "analysis": profile_text,
                "summary": summary,
                "personality_type": self._extract_personality_type(profile_text),
                "learning_style": self._extract_learning_style(profile_text),
                "career_interests": preferred_majors,
                "strengths": self._extract_strengths(profile_text),
                "areas_for_development": self._extract_development_areas(profile_text),
                "study_preferences": self._extract_study_preferences(profile_text),
                "work_environment_preferences": self._extract_work_preferences(profile_text),
                "communication_style": self._extract_communication_style(profile_text),
                "leadership_style": self._extract_leadership_style(profile_text),
                "stress_management": self._extract_stress_management(profile_text),
                "confidence_score": 0.85
            }
            
            return profile_data
            
        except Exception as e:
            # Fallback profile if LLM fails
            fallback_profile = self._create_fallback_profile(answers, preferred_majors)
            fallback_summary = self._create_fallback_summary(answers, preferred_majors)
            fallback_profile['summary'] = fallback_summary
            return fallback_profile

    async def _generate_personality_summary(
        self, 
        profile_text: str, 
        answers: Dict[str, Any], 
        preferred_majors: List[str]
    ) -> str:
        """Generate a concise personality summary"""
        
        summary_prompt = f"""
        Based on the following personality profile and questionnaire responses, create a concise, engaging 2-3 sentence summary that captures the user's key personality traits, learning style, and academic interests. This summary should be written in a friendly, professional tone and highlight what makes this person unique.

        Personality Profile:
        {json.dumps(profile_text, indent=2)}

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
    
    def _create_matching_prompt(self, answers: Dict[str, Any], preferred_majors: List[str]) -> str:
        """Create prompt using the matching prompt format"""
        
        # Map the answers to the 23 questions format
        question_mapping = {
            "q1": "Would you rather marry Stephen Hawking or a short shelf-life chocolate cake?",
            "q2": "Who is/was your childhood celebrity crush?",
            "q3": "Do you put bread in the fridge or the cabinet?",
            "q4": "Has evolution changed your life?",
            "q5": "Do you thank ChatGPT? Why?",
            "q6": "Your most unpopular opinion.",
            "q7": "What is the acceptable height of a sock starting from the ankle?",
            "q8": "Beans? breakfast / lunch / midnight snack",
            "q9": "Why did the chicken come before the egg?",
            "q10": "Why did the egg come before the chicken?",
            "q11": "Diving into the Mariana Trench or climbing Mount Everest?",
            "q12": "How many people do you need to steal a car? 0 - 10",
            "q13": "Who's your favourite villain?",
            "q14": "One piece of gum left, and your friend asks for one? Take turns chewing it / chew it together at the same time / take it yourself / throw it away (no one deserves it) / Give it to your friend",
            "q15": "Would you rather have the professors send you streak snaps or them never even knowing your name?",
            "q16": "How many \"in one\" does your shampoo have?",
            "q17": "In what order do you dry yourself after a shower?",
            "q18": "The Trolley problem. A trolley is heading toward 5 people. You can pull a lever to divert it, but it will hit your grandma, who's going to die soon anyway. Do you pull the lever?",
            "q19": "Would you rather be a boulder or a grain of sand?",
            "q20": "Cereal or milk first?",
            "q21": "Best Ice Cream flavour?",
            "q22": "Would you rather live in an apartment but on the first floor, or in a house but only in the attic?",
            "q23": "Favorite internet trend?"
        }
        
        # Create the answers section
        answers_text = "Based on the questionnaire answers:\n"
        
        # Get the questions from the database to map them properly
        from database.database import get_db
        from database.models import Question
        
        # Get a database session
        db = next(get_db())
        try:
            # Get all questions ordered by order_index
            questions = db.query(Question).filter(Question.is_active == True).order_by(Question.order_index).all()
            
            # Map answers to questions by order
            for i, question in enumerate(questions, 1):
                if question.id in answers:
                    answer = answers[question.id]
                    question_text = question.question_text
                    answers_text += f"Q{i}: {question_text}\nAnswer: {answer}\n\n"
                else:
                    # If no answer for this question, use a default
                    question_text = question.question_text
                    answers_text += f"Q{i}: {question_text}\nAnswer: No answer provided\n\n"
        finally:
            db.close()
        
        if preferred_majors:
            answers_text += f"Preferred Majors: {', '.join(preferred_majors)}\n\n"
        
        prompt = f"""
{answers_text}

Please provide a comprehensive analysis following the format specified in the system prompt:
1. Quick personality snapshot
2. Top 3 most suitable university types with qualities
3. List of countries (1-10 ranking) most suitable for studying
4. Notes and insights about campus and environment preferences

Please structure your response clearly with these sections.
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

    def _extract_study_preferences(self, profile_text: str) -> Dict[str, Any]:
        """Extract study preferences from analysis text"""
        text_lower = profile_text.lower()
        
        preferences = {
            "preferred_environment": "flexible",
            "group_work": "mixed",
            "online_learning": "mixed"
        }
        
        if "small" in text_lower and "student" in text_lower:
            preferences["preferred_environment"] = "small"
        elif "large" in text_lower and "student" in text_lower:
            preferences["preferred_environment"] = "large"
        
        if "team" in text_lower or "collaborative" in text_lower:
            preferences["group_work"] = "preferred"
        elif "individual" in text_lower or "solo" in text_lower:
            preferences["group_work"] = "individual"
        
        return preferences

    def _extract_work_preferences(self, profile_text: str) -> Dict[str, Any]:
        """Extract work environment preferences from analysis text"""
        text_lower = profile_text.lower()
        
        preferences = {
            "collaboration": "moderate",
            "structure": "moderate"
        }
        
        if "team" in text_lower or "collaborative" in text_lower:
            preferences["collaboration"] = "high"
        elif "independent" in text_lower or "solo" in text_lower:
            preferences["collaboration"] = "low"
        
        if "structured" in text_lower or "organized" in text_lower:
            preferences["structure"] = "high"
        elif "flexible" in text_lower or "creative" in text_lower:
            preferences["structure"] = "low"
        
        return preferences

    def _extract_communication_style(self, profile_text: str) -> str:
        """Extract communication style from analysis text"""
        text_lower = profile_text.lower()
        
        if "direct" in text_lower or "assertive" in text_lower:
            return "direct"
        elif "diplomatic" in text_lower or "empathetic" in text_lower:
            return "diplomatic"
        else:
            return "balanced"

    def _extract_leadership_style(self, profile_text: str) -> str:
        """Extract leadership style from analysis text"""
        text_lower = profile_text.lower()
        
        if "collaborative" in text_lower or "team" in text_lower:
            return "collaborative"
        elif "independent" in text_lower or "solo" in text_lower:
            return "independent"
        else:
            return "situational"

    def _extract_stress_management(self, profile_text: str) -> str:
        """Extract stress management approach from analysis text"""
        text_lower = profile_text.lower()
        
        if "proactive" in text_lower or "planning" in text_lower:
            return "proactive"
        elif "adaptive" in text_lower or "flexible" in text_lower:
            return "adaptive"
        else:
            return "balanced" 