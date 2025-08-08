from sqlalchemy import Column, Integer, String, DateTime, Text, Float, Boolean, ForeignKey, JSON, LargeBinary
from sqlalchemy.orm import DeclarativeBase, relationship
from sqlalchemy.sql import func
from typing import Optional, List, Dict, Any
import json
import uuid
from datetime import datetime
import numpy as np

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = 'users'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(120), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    name = Column(String(100), nullable=False)
    age = Column(Integer, nullable=True)
    phone = Column(String(20), nullable=True)
    income = Column(Float, nullable=True)
    
    # Profile information
    personality_profile = Column(JSON, nullable=True)  # LLM-generated personality analysis
    personality_summary = Column(Text, nullable=True)  # Concise text summary
    questionnaire_answers = Column(JSON, nullable=True)  # Raw questionnaire responses
    preferred_majors = Column(JSON, nullable=True)  # List of preferred fields of study
    preferred_locations = Column(JSON, nullable=True)  # Preferred study locations
    
    # Matching preferences
    min_acceptance_rate = Column(Float, nullable=True)
    max_tuition = Column(Float, nullable=True)
    preferred_university_type = Column(String(50), nullable=True)  # Public, Private, etc.
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    student_profile = relationship("StudentProfile", back_populates="user", uselist=False)
    user_answers = relationship("UserAnswer", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f'<User {self.username}>'
    
    def to_dict(self) -> dict:
        """Convert user object to dictionary"""
        return {
            'id': str(self.id),
            'username': self.username,
            'email': self.email,
            'name': self.name,
            'age': self.age,
            'phone': self.phone,
            'income': self.income,
            'personality_profile': self.personality_profile,
            'personality_summary': self.personality_summary,
            'questionnaire_answers': self.questionnaire_answers,
            'preferred_majors': self.preferred_majors,
            'preferred_locations': self.preferred_locations,
            'min_acceptance_rate': self.min_acceptance_rate,
            'max_tuition': self.max_tuition,
            'preferred_university_type': self.preferred_university_type,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'student_profile': self.student_profile.to_dict() if self.student_profile else None
        }

class Question(Base):
    __tablename__ = 'questions'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    question_text = Column(Text, nullable=False, index=True)  # Changed from unique=True to index=True
    question_type = Column(String(50), nullable=False, default='text')  # text, multiple_choice, scale, etc.
    category = Column(String(100), nullable=True)  # personality, preferences, etc.
    order_index = Column(Integer, nullable=False, default=0)
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user_answers = relationship("UserAnswer", back_populates="question", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f'<Question {self.question_text[:50]}...>'
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert question object to dictionary"""
        return {
            'id': str(self.id),
            'question_text': self.question_text,
            'question_type': self.question_type,
            'category': self.category,
            'order_index': self.order_index,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class UserAnswer(Base):
    __tablename__ = 'user_answers'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey('users.id'), nullable=False)
    question_id = Column(String(36), ForeignKey('questions.id'), nullable=False)
    answer_text = Column(Text, nullable=False)
    answer_data = Column(JSON, nullable=True)  # For structured answers (choices, ratings, etc.)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="user_answers")
    question = relationship("Question", back_populates="user_answers")
    
    def __repr__(self) -> str:
        return f'<UserAnswer {self.user_id} - {self.question_id}>'
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert user answer object to dictionary"""
        return {
            'id': str(self.id),
            'user_id': str(self.user_id),
            'question_id': str(self.question_id),
            'answer_text': self.answer_text,
            'answer_data': self.answer_data,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class StudentProfile(Base):
    __tablename__ = 'student_profiles'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey('users.id'), nullable=False, unique=True)
    
    # Academic Information
    current_school = Column(String(200), nullable=True)
    graduation_year = Column(Integer, nullable=True)
    gpa = Column(Float, nullable=True)
    class_rank = Column(Integer, nullable=True)
    class_size = Column(Integer, nullable=True)
    
    # Standardized Test Scores
    sat_total = Column(Integer, nullable=True)
    sat_math = Column(Integer, nullable=True)
    sat_evidence_based_reading = Column(Integer, nullable=True)
    sat_writing = Column(Integer, nullable=True)
    act_composite = Column(Integer, nullable=True)
    act_math = Column(Integer, nullable=True)
    act_english = Column(Integer, nullable=True)
    act_reading = Column(Integer, nullable=True)
    act_science = Column(Integer, nullable=True)
    
    # Advanced Placement (AP) Scores
    ap_scores = Column(JSON, nullable=True)  # {"AP Calculus BC": 5, "AP Physics": 4, ...}
    
    # International Baccalaureate (IB) Scores
    ib_diploma = Column(Boolean, default=False)
    ib_total_score = Column(Integer, nullable=True)
    ib_subject_scores = Column(JSON, nullable=True)
    
    # Academic Achievements
    honors_classes = Column(JSON, nullable=True)  # List of honors/AP classes taken
    academic_awards = Column(JSON, nullable=True)  # List of academic awards
    research_experience = Column(JSON, nullable=True)  # Research projects and publications
    
    # Extracurricular Activities
    leadership_positions = Column(JSON, nullable=True)  # Club president, team captain, etc.
    volunteer_hours = Column(Integer, nullable=True)
    work_experience = Column(JSON, nullable=True)  # Jobs and internships
    sports_activities = Column(JSON, nullable=True)  # Sports participation
    artistic_activities = Column(JSON, nullable=True)  # Music, art, theater, etc.
    
    # Personal Information
    citizenship = Column(String(100), nullable=True)
    first_language = Column(String(100), nullable=True)
    languages_spoken = Column(JSON, nullable=True)  # List of languages and proficiency levels
    disabilities = Column(JSON, nullable=True)  # Accommodations needed
    military_service = Column(Boolean, default=False)
    
    # Financial Information
    family_income = Column(Float, nullable=True)
    financial_aid_needed = Column(Boolean, default=True)
    scholarship_applications = Column(JSON, nullable=True)  # Scholarships applied for
    
    # Study Preferences
    preferred_class_size = Column(String(50), nullable=True)  # Small, Medium, Large
    preferred_teaching_style = Column(JSON, nullable=True)  # Lecture, Discussion, Hands-on, etc.
    preferred_campus_environment = Column(JSON, nullable=True)  # Urban, Suburban, Rural, etc.
    housing_preferences = Column(JSON, nullable=True)  # On-campus, Off-campus, etc.
    
    # Career Goals
    career_aspirations = Column(Text, nullable=True)
    industry_preferences = Column(JSON, nullable=True)  # Tech, Healthcare, Finance, etc.
    salary_expectations = Column(Float, nullable=True)
    
    # Additional Information
    special_circumstances = Column(Text, nullable=True)  # Personal challenges, unique experiences
    essay_topics = Column(JSON, nullable=True)  # Potential essay topics
    recommendation_letters = Column(JSON, nullable=True)  # Who will write recommendations
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    profile_completion_percentage = Column(Float, default=0.0)
    
    # Relationships
    user = relationship("User", back_populates="student_profile")
    
    def __repr__(self) -> str:
        return f'<StudentProfile {self.user_id}>'
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert student profile object to dictionary"""
        return {
            'id': str(self.id),
            'user_id': str(self.user_id),
            'current_school': self.current_school,
            'graduation_year': self.graduation_year,
            'gpa': self.gpa,
            'class_rank': self.class_rank,
            'class_size': self.class_size,
            'sat_total': self.sat_total,
            'sat_math': self.sat_math,
            'sat_evidence_based_reading': self.sat_evidence_based_reading,
            'sat_writing': self.sat_writing,
            'act_composite': self.act_composite,
            'act_math': self.act_math,
            'act_english': self.act_english,
            'act_reading': self.act_reading,
            'act_science': self.act_science,
            'ap_scores': self.ap_scores,
            'ib_diploma': self.ib_diploma,
            'ib_total_score': self.ib_total_score,
            'ib_subject_scores': self.ib_subject_scores,
            'honors_classes': self.honors_classes,
            'academic_awards': self.academic_awards,
            'research_experience': self.research_experience,
            'leadership_positions': self.leadership_positions,
            'volunteer_hours': self.volunteer_hours,
            'work_experience': self.work_experience,
            'sports_activities': self.sports_activities,
            'artistic_activities': self.artistic_activities,
            'citizenship': self.citizenship,
            'first_language': self.first_language,
            'languages_spoken': self.languages_spoken,
            'disabilities': self.disabilities,
            'military_service': self.military_service,
            'family_income': self.family_income,
            'financial_aid_needed': self.financial_aid_needed,
            'scholarship_applications': self.scholarship_applications,
            'preferred_class_size': self.preferred_class_size,
            'preferred_teaching_style': self.preferred_teaching_style,
            'preferred_campus_environment': self.preferred_campus_environment,
            'housing_preferences': self.housing_preferences,
            'career_aspirations': self.career_aspirations,
            'industry_preferences': self.industry_preferences,
            'salary_expectations': self.salary_expectations,
            'special_circumstances': self.special_circumstances,
            'essay_topics': self.essay_topics,
            'recommendation_letters': self.recommendation_letters,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'profile_completion_percentage': self.profile_completion_percentage
        }
    
    def calculate_completion_percentage(self) -> float:
        """Calculate the completion percentage of the student profile"""
        fields = [
            self.current_school, self.graduation_year, self.gpa, self.class_rank,
            self.sat_total, self.act_composite, self.ap_scores, self.ib_diploma,
            self.honors_classes, self.academic_awards, self.research_experience,
            self.leadership_positions, self.volunteer_hours, self.work_experience,
            self.sports_activities, self.artistic_activities, self.citizenship,
            self.first_language, self.languages_spoken, self.family_income,
            self.preferred_class_size, self.preferred_teaching_style,
            self.preferred_campus_environment, self.career_aspirations,
            self.industry_preferences, self.salary_expectations
        ]
        
        completed_fields = sum(1 for field in fields if field is not None and field != "")
        total_fields = len(fields)
        
        return (completed_fields / total_fields) * 100 if total_fields > 0 else 0.0

class UniversityDataCollectionResult(Base):
    __tablename__ = 'university_data_collection_results'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Metadata fields
    total_universities = Column(Integer, nullable=True)
    successful_collections = Column(Integer, nullable=True)
    failed_collections = Column(Integer, nullable=True)
    generated_at = Column(DateTime(timezone=True), nullable=True)
    script_version = Column(String(50), nullable=True)
    
    # Results fields
    success = Column(Boolean, nullable=True)
    data_collection_id = Column(Integer, nullable=True)
    
    # Extracted data fields
    name = Column(String(200), nullable=True)
    website = Column(String(500), nullable=True)
    country = Column(String(100), nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    phone = Column(String(50), nullable=True)
    email = Column(String(200), nullable=True)
    founded_year = Column(Integer, nullable=True)
    type = Column(String(100), nullable=True)
    student_population = Column(Integer, nullable=True)
    undergraduate_population = Column(Integer, nullable=True)
    graduate_population = Column(Integer, nullable=True)
    international_students_percentage = Column(Float, nullable=True)
    faculty_count = Column(Integer, nullable=True)
    student_faculty_ratio = Column(Float, nullable=True)
    acceptance_rate = Column(Float, nullable=True)
    tuition_domestic = Column(Float, nullable=True)
    tuition_international = Column(Float, nullable=True)
    room_and_board = Column(Float, nullable=True)
    total_cost_of_attendance = Column(Float, nullable=True)
    financial_aid_available = Column(Boolean, nullable=True)
    average_financial_aid_package = Column(Float, nullable=True)
    scholarships_available = Column(Boolean, nullable=True)
    world_ranking = Column(Integer, nullable=True)
    national_ranking = Column(Integer, nullable=True)
    regional_ranking = Column(Integer, nullable=True)
    subject_rankings = Column(JSON, nullable=True)
    description = Column(Text, nullable=True)
    mission_statement = Column(Text, nullable=True)
    vision_statement = Column(Text, nullable=True)
    campus_size = Column(String(100), nullable=True)
    campus_type = Column(String(100), nullable=True)
    climate = Column(String(100), nullable=True)
    timezone = Column(String(100), nullable=True)
    programs = Column(JSON, nullable=True)
    student_life = Column(JSON, nullable=True)
    financial_aid = Column(JSON, nullable=True)
    international_students = Column(JSON, nullable=True)
    alumni = Column(JSON, nullable=True)
    confidence_score = Column(Float, nullable=True)
    source_urls = Column(JSON, nullable=True)
    last_updated = Column(String(50), nullable=True)
    
    # Additional metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self) -> str:
        return f'<UniversityDataCollectionResult {self.name}>'
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert university data collection result object to dictionary"""
        return {
            'id': str(self.id),
            'total_universities': self.total_universities,
            'successful_collections': self.successful_collections,
            'failed_collections': self.failed_collections,
            'generated_at': self.generated_at.isoformat() if self.generated_at else None,
            'script_version': self.script_version,
            'success': self.success,
            'data_collection_id': self.data_collection_id,
            'name': self.name,
            'website': self.website,
            'country': self.country,
            'city': self.city,
            'state': self.state,
            'phone': self.phone,
            'email': self.email,
            'founded_year': self.founded_year,
            'type': self.type,
            'student_population': self.student_population,
            'undergraduate_population': self.undergraduate_population,
            'graduate_population': self.graduate_population,
            'international_students_percentage': self.international_students_percentage,
            'faculty_count': self.faculty_count,
            'student_faculty_ratio': self.student_faculty_ratio,
            'acceptance_rate': self.acceptance_rate,
            'tuition_domestic': self.tuition_domestic,
            'tuition_international': self.tuition_international,
            'room_and_board': self.room_and_board,
            'total_cost_of_attendance': self.total_cost_of_attendance,
            'financial_aid_available': self.financial_aid_available,
            'average_financial_aid_package': self.average_financial_aid_package,
            'scholarships_available': self.scholarships_available,
            'world_ranking': self.world_ranking,
            'national_ranking': self.national_ranking,
            'regional_ranking': self.regional_ranking,
            'subject_rankings': self.subject_rankings,
            'description': self.description,
            'mission_statement': self.mission_statement,
            'vision_statement': self.vision_statement,
            'campus_size': self.campus_size,
            'campus_type': self.campus_type,
            'climate': self.climate,
            'timezone': self.timezone,
            'programs': self.programs,
            'student_life': self.student_life,
            'financial_aid': self.financial_aid,
            'international_students': self.international_students,
            'alumni': self.alumni,
            'confidence_score': self.confidence_score,
            'source_urls': self.source_urls,
            'last_updated': self.last_updated,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class University(Base):
    """Model for storing university information"""
    __tablename__ = 'universities'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(200), nullable=False, index=True)
    website = Column(String(500), nullable=True)
    country = Column(String(100), nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    postal_code = Column(String(20), nullable=True)
    phone = Column(String(50), nullable=True)
    email = Column(String(200), nullable=True)
    
    # Academic information
    founded_year = Column(Integer, nullable=True)
    type = Column(String(100), nullable=True)  # Public, Private, etc.
    accreditation = Column(Text, nullable=True)
    
    # Statistics
    student_population = Column(Integer, nullable=True)
    faculty_count = Column(Integer, nullable=True)
    acceptance_rate = Column(Float, nullable=True)
    tuition_domestic = Column(Float, nullable=True)
    tuition_international = Column(Float, nullable=True)
    
    # Rankings and reputation
    world_ranking = Column(Integer, nullable=True)
    national_ranking = Column(Integer, nullable=True)
    
    # Additional data
    description = Column(Text, nullable=True)
    mission_statement = Column(Text, nullable=True)
    vision_statement = Column(Text, nullable=True)
    
    # Metadata
    scraped_at = Column(DateTime(timezone=True), server_default=func.now())
    last_updated = Column(DateTime(timezone=True), onupdate=func.now())
    source_url = Column(String(500), nullable=True)
    confidence_score = Column(Float, default=0.0)
    
    # Relationships
    programs = relationship("Program", back_populates="university", cascade="all, delete-orphan")
    facilities = relationship("Facility", back_populates="university", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f'<University {self.name}>'
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert university object to dictionary"""
        return {
            'id': str(self.id),
            'name': self.name,
            'website': self.website,
            'country': self.country,
            'city': self.city,
            'state': self.state,
            'postal_code': self.postal_code,
            'phone': self.phone,
            'email': self.email,
            'founded_year': self.founded_year,
            'type': self.type,
            'accreditation': self.accreditation,
            'student_population': self.student_population,
            'faculty_count': self.faculty_count,
            'acceptance_rate': self.acceptance_rate,
            'tuition_domestic': self.tuition_domestic,
            'tuition_international': self.tuition_international,
            'world_ranking': self.world_ranking,
            'national_ranking': self.national_ranking,
            'description': self.description,
            'mission_statement': self.mission_statement,
            'vision_statement': self.vision_statement,
            'scraped_at': self.scraped_at.isoformat() if self.scraped_at else None,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None,
            'source_url': self.source_url,
            'confidence_score': self.confidence_score,
            'programs': [program.to_dict() for program in self.programs],
            'facilities': [facility.to_dict() for facility in self.facilities]
        }


class Program(Base):
    """Model for storing university programs"""
    __tablename__ = 'programs'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    university_id = Column(String(36), ForeignKey('universities.id'), nullable=False)
    name = Column(String(200), nullable=False)
    level = Column(String(50), nullable=True)  # Bachelor, Master, PhD, etc.
    field = Column(String(100), nullable=True)  # Computer Science, Engineering, etc.
    duration = Column(String(50), nullable=True)  # 4 years, 2 years, etc.
    tuition = Column(Float, nullable=True)
    description = Column(Text, nullable=True)
    
    # Relationships
    university = relationship("University", back_populates="programs")
    
    def __repr__(self) -> str:
        return f'<Program {self.name}>'
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert program object to dictionary"""
        return {
            'id': str(self.id),
            'university_id': str(self.university_id),
            'name': self.name,
            'level': self.level,
            'field': self.field,
            'duration': self.duration,
            'tuition': self.tuition,
            'description': self.description
        }


class Facility(Base):
    """Model for storing university facilities"""
    __tablename__ = 'facilities'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    university_id = Column(String(36), ForeignKey('universities.id'), nullable=False)
    name = Column(String(200), nullable=False)
    type = Column(String(100), nullable=True)  # Library, Lab, Sports, etc.
    description = Column(Text, nullable=True)
    capacity = Column(Integer, nullable=True)
    
    # Relationships
    university = relationship("University", back_populates="facilities")
    
    def __repr__(self) -> str:
        return f'<Facility {self.name}>'
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert facility object to dictionary"""
        return {
            'id': str(self.id),
            'university_id': str(self.university_id),
            'name': self.name,
            'type': self.type,
            'description': self.description,
            'capacity': self.capacity
        }


class UserVector(Base):
    """Model for storing user embeddings for similarity search"""
    __tablename__ = 'user_vectors'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey('users.id'), nullable=False, unique=True)
    
    # Vector data
    embedding = Column(LargeBinary, nullable=False)  # Stored as numpy array bytes
    embedding_dimension = Column(Integer, nullable=False)  # Dimension of the embedding vector
    embedding_model = Column(String(100), nullable=False)  # Model used to generate embedding (e.g., 'text-embedding-3-small')
    
    # Source text that was embedded
    source_text = Column(Text, nullable=False)  # The text that was used to generate the embedding
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", backref="vector")
    
    def __repr__(self) -> str:
        return f'<UserVector {self.user_id}>'
    
    def get_embedding_array(self) -> np.ndarray:
        """Convert stored bytes back to numpy array"""
        return np.frombuffer(self.embedding, dtype=np.float32)
    
    def set_embedding_array(self, embedding_array: np.ndarray) -> None:
        """Convert numpy array to bytes for storage"""
        self.embedding = embedding_array.tobytes()
        self.embedding_dimension = len(embedding_array)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert user vector object to dictionary"""
        return {
            'id': str(self.id),
            'user_id': str(self.user_id),
            'embedding_dimension': self.embedding_dimension,
            'embedding_model': self.embedding_model,
            'source_text': self.source_text,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class UniversityVector(Base):
    """Model for storing university embeddings for similarity search"""
    __tablename__ = 'university_vectors'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    university_id = Column(String(36), ForeignKey('universities.id'), nullable=False, unique=True)
    
    # Vector data
    embedding = Column(LargeBinary, nullable=False)  # Stored as numpy array bytes
    embedding_dimension = Column(Integer, nullable=False)  # Dimension of the embedding vector
    embedding_model = Column(String(100), nullable=False)  # Model used to generate embedding
    
    # Source text that was embedded
    source_text = Column(Text, nullable=False)  # The text that was used to generate the embedding
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    university = relationship("University", backref="vector")
    
    def __repr__(self) -> str:
        return f'<UniversityVector {self.university_id}>'
    
    def get_embedding_array(self) -> np.ndarray:
        """Convert stored bytes back to numpy array"""
        return np.frombuffer(self.embedding, dtype=np.float32)
    
    def set_embedding_array(self, embedding_array: np.ndarray) -> None:
        """Convert numpy array to bytes for storage"""
        self.embedding = embedding_array.tobytes()
        self.embedding_dimension = len(embedding_array)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert university vector object to dictionary"""
        return {
            'id': str(self.id),
            'university_id': str(self.university_id),
            'embedding_dimension': self.embedding_dimension,
            'embedding_model': self.embedding_model,
            'source_text': self.source_text,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class VectorSearchCache(Base):
    """Model for caching vector search results to improve performance"""
    __tablename__ = 'vector_search_cache'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Search parameters
    user_id = Column(String(36), ForeignKey('users.id'), nullable=False)
    search_type = Column(String(50), nullable=False)  # 'university_match', 'similar_users', etc.
    embedding_model = Column(String(100), nullable=False)
    
    # Search results (stored as JSON)
    results = Column(JSON, nullable=False)  # List of matches with similarity scores
    
    # Cache metadata
    cache_key = Column(String(255), nullable=False, unique=True)  # Hash of search parameters
    expires_at = Column(DateTime(timezone=True), nullable=False)  # When cache expires
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", backref="vector_search_caches")
    
    def __repr__(self) -> str:
        return f'<VectorSearchCache {self.search_type} for {self.user_id}>'
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert vector search cache object to dictionary"""
        return {
            'id': str(self.id),
            'user_id': str(self.user_id),
            'search_type': self.search_type,
            'embedding_model': self.embedding_model,
            'results': self.results,
            'cache_key': self.cache_key,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class CollectionResultVector(Base):
    """Model for storing collection result embeddings for similarity search"""
    __tablename__ = 'collection_result_vectors'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    collection_result_id = Column(String(36), ForeignKey('university_data_collection_results.id'), nullable=False, unique=True)
    
    # Vector data
    embedding = Column(LargeBinary, nullable=False)  # Stored as numpy array bytes
    embedding_dimension = Column(Integer, nullable=False)  # Dimension of the embedding vector
    embedding_model = Column(String(100), nullable=False)  # Model used to generate embedding
    
    # Source text that was embedded
    source_text = Column(Text, nullable=False)  # The text that was used to generate the embedding
    
    # Specialized embeddings and metadata (stored as JSON)
    specialized_data = Column(JSON, nullable=True)  # Specialized embeddings and matching profiles
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    collection_result = relationship("UniversityDataCollectionResult", backref="vector")
    
    def __repr__(self) -> str:
        return f'<CollectionResultVector {self.collection_result_id}>'
    
    def get_embedding_array(self) -> np.ndarray:
        """Get embedding as numpy array"""
        return np.frombuffer(self.embedding, dtype=np.float32)
    
    def set_embedding_array(self, embedding_array: np.ndarray) -> None:
        """Set embedding from numpy array"""
        self.embedding = embedding_array.tobytes()
        self.embedding_dimension = len(embedding_array)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert vector object to dictionary"""
        return {
            'id': str(self.id),
            'collection_result_id': str(self.collection_result_id),
            'embedding_dimension': self.embedding_dimension,
            'embedding_model': self.embedding_model,
            'source_text': self.source_text,
            'specialized_data': self.specialized_data,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class UserUniversitySuggestion(Base):
    """Model for storing university suggestions for each user to avoid duplicate generation"""
    __tablename__ = 'user_university_suggestions'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey('users.id'), nullable=False)
    
    # Suggestion data
    university_id = Column(String(36), nullable=False)  # Can be from University or UniversityDataCollectionResult
    university_name = Column(String(200), nullable=False)
    similarity_score = Column(Float, nullable=False)
    matching_method = Column(String(50), nullable=False)  # vector_similarity, traditional_scoring, collection_vector_similarity
    confidence = Column(String(20), nullable=True)  # high, medium, low, very_low
    
    # Match details
    match_reasons = Column(JSON, nullable=True)  # List of reasons why this university matches
    user_preferences = Column(JSON, nullable=True)  # User preferences used for matching
    university_data = Column(JSON, nullable=True)  # Full university data
    
    # Program information (if applicable)
    program_id = Column(String(36), nullable=True)
    program_name = Column(String(200), nullable=True)
    program_data = Column(JSON, nullable=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", backref="university_suggestions")
    
    def __repr__(self) -> str:
        return f'<UserUniversitySuggestion {self.user_id} -> {self.university_name}>'
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert suggestion object to dictionary"""
        return {
            'id': str(self.id),
            'user_id': str(self.user_id),
            'university_id': self.university_id,
            'university_name': self.university_name,
            'similarity_score': self.similarity_score,
            'matching_method': self.matching_method,
            'confidence': self.confidence,
            'match_reasons': self.match_reasons,
            'user_preferences': self.user_preferences,
            'university_data': self.university_data,
            'program_id': self.program_id,
            'program_name': self.program_name,
            'program_data': self.program_data,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
