from sqlalchemy import Column, Integer, String, DateTime, Text, Float, Boolean, ForeignKey, JSON
from sqlalchemy.orm import DeclarativeBase, relationship
from sqlalchemy.sql import func
from typing import Optional, List, Dict, Any
import json

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(120), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    name = Column(String(100), nullable=False)
    age = Column(Integer, nullable=True)
    phone = Column(String(20), nullable=True)
    income = Column(Float, nullable=True)
    
    # Profile information
    personality_profile = Column(JSON, nullable=True)  # LLM-generated personality analysis
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
    
    def __repr__(self) -> str:
        return f'<User {self.username}>'
    
    def to_dict(self) -> dict:
        """Convert user object to dictionary"""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'name': self.name,
            'age': self.age,
            'phone': self.phone,
            'income': self.income,
            'personality_profile': self.personality_profile,
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

class StudentProfile(Base):
    __tablename__ = 'student_profiles'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, unique=True)
    
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
        return f'<StudentProfile {self.user.name if self.user else "Unknown"}>'
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert student profile object to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
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
        """Calculate the percentage of profile completion"""
        total_fields = 0
        completed_fields = 0
        
        # Basic academic info
        academic_fields = ['current_school', 'graduation_year', 'gpa', 'class_rank', 'class_size']
        for field in academic_fields:
            total_fields += 1
            if getattr(self, field) is not None:
                completed_fields += 1
        
        # Test scores
        test_fields = ['sat_total', 'act_composite']
        for field in test_fields:
            total_fields += 1
            if getattr(self, field) is not None:
                completed_fields += 1
        
        # Extracurricular
        extra_fields = ['leadership_positions', 'volunteer_hours', 'work_experience', 'sports_activities']
        for field in extra_fields:
            total_fields += 1
            if getattr(self, field) is not None:
                completed_fields += 1
        
        # Preferences
        pref_fields = ['preferred_class_size', 'preferred_campus_environment', 'career_aspirations']
        for field in pref_fields:
            total_fields += 1
            if getattr(self, field) is not None:
                completed_fields += 1
        
        return (completed_fields / total_fields * 100) if total_fields > 0 else 0.0

class UniversityDataCollectionResult(Base):
    __tablename__ = 'university_data_collection_results'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
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
            'id': self.id,
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
