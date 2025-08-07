from pydantic import BaseModel, EmailStr, validator
from typing import List, Optional, Dict, Any
from datetime import datetime
import re
import uuid

# Authentication schemas
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    name: str
    
    @validator('username')
    def validate_username(cls, v):
        if len(v) < 3:
            raise ValueError('Username must be at least 3 characters long')
        if len(v) > 50:
            raise ValueError('Username must be less than 50 characters')
        if not re.match(r'^[a-zA-Z0-9_]+$', v):
            raise ValueError('Username can only contain letters, numbers, and underscores')
        return v
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one number')
        return v
    
    @validator('name')
    def validate_name(cls, v):
        if len(v.strip()) < 2:
            raise ValueError('Name must be at least 2 characters long')
        if len(v) > 100:
            raise ValueError('Name must be less than 100 characters')
        return v.strip()

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserProfile(BaseModel):
    id: str  # UUID as string
    username: str
    email: str
    name: str
    age: Optional[int] = None
    phone: Optional[str] = None
    income: Optional[float] = None
    personality_profile: Optional[Dict[str, Any]] = None
    personality_summary: Optional[str] = None
    questionnaire_answers: Optional[Dict[str, Any]] = None
    preferred_majors: Optional[List[str]] = None
    preferred_locations: Optional[List[str]] = None
    min_acceptance_rate: Optional[float] = None
    max_tuition: Optional[float] = None
    preferred_university_type: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class AuthResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserProfile

class UserUpdate(BaseModel):
    name: Optional[str] = None
    age: Optional[int] = None
    phone: Optional[str] = None
    income: Optional[float] = None
    min_acceptance_rate: Optional[float] = None
    max_tuition: Optional[float] = None
    preferred_university_type: Optional[str] = None

# Questionnaire schemas
class QuestionResponse(BaseModel):
    id: str  # UUID as string
    question_text: str
    question_type: str
    category: Optional[str] = None
    order_index: int
    is_active: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class UserAnswerCreate(BaseModel):
    question_id: str  # UUID as string
    answer_text: str
    answer_data: Optional[Dict[str, Any]] = None

class UserAnswerResponse(BaseModel):
    id: str  # UUID as string
    user_id: str  # UUID as string
    question_id: str  # UUID as string
    answer_text: str
    answer_data: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class QuestionnaireSubmission(BaseModel):
    answers: List[UserAnswerCreate]
    preferred_majors: Optional[List[str]] = None
    preferred_locations: Optional[List[str]] = None

class QuestionnaireResponse(BaseModel):
    answers: Dict[str, Any]
    preferred_majors: List[str]
    preferred_locations: List[str]

class PersonalityProfile(BaseModel):
    personality_type: str
    learning_style: str
    career_interests: List[str]
    strengths: List[str]
    areas_for_development: List[str]
    study_preferences: Dict[str, Any]
    work_environment_preferences: Dict[str, Any]
    communication_style: str
    leadership_style: str
    stress_management: str
    confidence_score: float

# University schemas
class ProgramResponse(BaseModel):
    id: str  # UUID as string
    university_id: str  # UUID as string
    name: str
    level: Optional[str] = None
    field: Optional[str] = None
    duration: Optional[str] = None
    tuition: Optional[float] = None
    description: Optional[str] = None

class FacilityResponse(BaseModel):
    id: str  # UUID as string
    university_id: str  # UUID as string
    name: str
    type: Optional[str] = None
    description: Optional[str] = None
    capacity: Optional[int] = None

class UniversityResponse(BaseModel):
    id: str  # UUID as string
    name: str
    website: Optional[str] = None
    country: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    founded_year: Optional[int] = None
    type: Optional[str] = None
    accreditation: Optional[str] = None
    student_population: Optional[int] = None
    faculty_count: Optional[int] = None
    acceptance_rate: Optional[float] = None
    tuition_domestic: Optional[float] = None
    tuition_international: Optional[float] = None
    world_ranking: Optional[int] = None
    national_ranking: Optional[int] = None
    description: Optional[str] = None
    mission_statement: Optional[str] = None
    vision_statement: Optional[str] = None
    scraped_at: Optional[datetime] = None
    last_updated: Optional[datetime] = None
    source_url: Optional[str] = None
    confidence_score: Optional[float] = None
    programs: List[ProgramResponse] = []
    facilities: List[FacilityResponse] = []

class SchoolResponse(BaseModel):
    id: str  # UUID as string
    name: str
    website: Optional[str] = None
    country: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    student_population: Optional[int] = None
    teacher_count: Optional[int] = None
    graduation_rate: Optional[float] = None
    college_acceptance_rate: Optional[float] = None
    average_sat_score: Optional[int] = None
    average_act_score: Optional[int] = None
    ap_courses_offered: Optional[int] = None
    test_scores: Optional[Dict[str, Any]] = None
    rankings: Optional[Dict[str, Any]] = None
    awards: Optional[Dict[str, Any]] = None
    programs_offered: Optional[Dict[str, Any]] = None
    extracurricular_activities: Optional[Dict[str, Any]] = None
    sports_teams: Optional[Dict[str, Any]] = None
    description: Optional[str] = None
    mission_statement: Optional[str] = None
    facilities: Optional[Dict[str, Any]] = None
    scraped_at: Optional[datetime] = None
    last_updated: Optional[datetime] = None
    source_url: Optional[str] = None
    confidence_score: Optional[float] = None

class MatchResponse(BaseModel):
    id: str  # UUID as string
    user_id: str  # UUID as string
    university_id: str  # UUID as string
    program_id: Optional[str] = None  # UUID as string
    overall_score: float
    academic_fit_score: Optional[float] = None
    financial_fit_score: Optional[float] = None
    location_fit_score: Optional[float] = None
    personality_fit_score: Optional[float] = None
    user_preferences: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None
    is_favorite: bool
    notes: Optional[str] = None
    university: Optional[UniversityResponse] = None
    program: Optional[ProgramResponse] = None

class SchoolScrapingRequest(BaseModel):
    school_name: str
    location: Optional[str] = None

class SchoolScrapingResponse(BaseModel):
    success: bool
    school_data: Optional[SchoolResponse] = None
    error_message: Optional[str] = None 