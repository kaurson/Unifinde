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
    matches = relationship("UserMatch", back_populates="user")
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
    
class School(Base):
    __tablename__ = 'schools'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False, index=True)
    website = Column(String(500), nullable=True)
    country = Column(String(100), nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    postal_code = Column(String(20), nullable=True)
    phone = Column(String(50), nullable=True)
    email = Column(String(200), nullable=True)
    
    # School statistics
    student_population = Column(Integer, nullable=True)
    teacher_count = Column(Integer, nullable=True)
    graduation_rate = Column(Float, nullable=True)
    college_acceptance_rate = Column(Float, nullable=True)
    average_sat_score = Column(Integer, nullable=True)
    average_act_score = Column(Integer, nullable=True)
    ap_courses_offered = Column(Integer, nullable=True)
    
    # Academic performance
    test_scores = Column(JSON, nullable=True)  # Various test scores
    rankings = Column(JSON, nullable=True)  # School rankings
    awards = Column(JSON, nullable=True)  # Awards and recognition
    
    # Programs and activities
    programs_offered = Column(JSON, nullable=True)
    extracurricular_activities = Column(JSON, nullable=True)
    sports_teams = Column(JSON, nullable=True)
    
    # Additional information
    description = Column(Text, nullable=True)
    mission_statement = Column(Text, nullable=True)
    facilities = Column(JSON, nullable=True)
    
    # Metadata
    scraped_at = Column(DateTime(timezone=True), server_default=func.now())
    last_updated = Column(DateTime(timezone=True), onupdate=func.now())
    source_url = Column(String(500), nullable=True)
    confidence_score = Column(Float, default=0.0)
    
    def __repr__(self) -> str:
        return f'<School {self.name}>'
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert school object to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'website': self.website,
            'country': self.country,
            'city': self.city,
            'state': self.state,
            'postal_code': self.postal_code,
            'phone': self.phone,
            'email': self.email,
            'student_population': self.student_population,
            'teacher_count': self.teacher_count,
            'graduation_rate': self.graduation_rate,
            'college_acceptance_rate': self.college_acceptance_rate,
            'average_sat_score': self.average_sat_score,
            'average_act_score': self.average_act_score,
            'ap_courses_offered': self.ap_courses_offered,
            'test_scores': self.test_scores,
            'rankings': self.rankings,
            'awards': self.awards,
            'programs_offered': self.programs_offered,
            'extracurricular_activities': self.extracurricular_activities,
            'sports_teams': self.sports_teams,
            'description': self.description,
            'mission_statement': self.mission_statement,
            'facilities': self.facilities,
            'scraped_at': self.scraped_at.isoformat() if self.scraped_at else None,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None,
            'source_url': self.source_url,
            'confidence_score': self.confidence_score
        }

class University(Base):
    __tablename__ = 'universities'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
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
    user_matches = relationship("UserMatch", back_populates="university")
    university_matches = relationship("UniversityMatch", back_populates="university")
    data_collections = relationship("UniversityDataCollection", back_populates="university")
    
    def __repr__(self) -> str:
        return f'<University {self.name}>'
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert university object to dictionary"""
        return {
            'id': self.id,
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
            'facilities': [facility.to_dict() for facility in self.facilities],
            'user_matches': [match.to_dict() for match in self.user_matches],
            'university_matches': [match.to_dict() for match in self.university_matches],
            'data_collections': [collection.to_dict() for collection in self.data_collections]
        }

class Program(Base):
    __tablename__ = 'programs'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    university_id = Column(Integer, ForeignKey('universities.id'), nullable=False)
    name = Column(String(200), nullable=False)
    level = Column(String(50), nullable=True)  # Bachelor, Master, PhD, etc.
    field = Column(String(100), nullable=True)  # Computer Science, Engineering, etc.
    duration = Column(String(50), nullable=True)  # 4 years, 2 years, etc.
    tuition = Column(Float, nullable=True)
    description = Column(Text, nullable=True)
    requirements = Column(Text, nullable=True)
    
    university = relationship("University", back_populates="programs")
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'university_id': self.university_id,
            'name': self.name,
            'level': self.level,
            'field': self.field,
            'duration': self.duration,
            'tuition': self.tuition,
            'description': self.description,
            'requirements': self.requirements
        }

class Facility(Base):
    __tablename__ = 'facilities'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    university_id = Column(Integer, ForeignKey('universities.id'), nullable=False)
    name = Column(String(200), nullable=False)
    type = Column(String(100), nullable=True)  # Library, Lab, Sports, etc.
    description = Column(Text, nullable=True)
    capacity = Column(Integer, nullable=True)
    
    university = relationship("University", back_populates="facilities")
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'university_id': self.university_id,
            'name': self.name,
            'type': self.type,
            'description': self.description,
            'capacity': self.capacity
        }

class UserMatch(Base):
    __tablename__ = 'user_matches'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    university_id = Column(Integer, ForeignKey('universities.id'), nullable=False)
    program_id = Column(Integer, ForeignKey('programs.id'), nullable=True)
    
    # Matching scores
    overall_score = Column(Float, nullable=False)
    academic_fit_score = Column(Float, nullable=True)
    financial_fit_score = Column(Float, nullable=True)
    location_fit_score = Column(Float, nullable=True)
    personality_fit_score = Column(Float, nullable=True)
    
    # User preferences
    user_preferences = Column(JSON, nullable=True)
    
    # Match metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    is_favorite = Column(Boolean, default=False)
    notes = Column(Text, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="matches")
    university = relationship("University", back_populates="user_matches")
    program = relationship("Program")
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'user_id': self.user_id,
            'university_id': self.university_id,
            'program_id': self.program_id,
            'overall_score': self.overall_score,
            'academic_fit_score': self.academic_fit_score,
            'financial_fit_score': self.financial_fit_score,
            'location_fit_score': self.location_fit_score,
            'personality_fit_score': self.personality_fit_score,
            'user_preferences': self.user_preferences,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'is_favorite': self.is_favorite,
            'notes': self.notes,
            'university': self.university.to_dict() if self.university else None,
            'program': self.program.to_dict() if self.program else None
        }

class UniversityMatch(Base):
    __tablename__ = 'university_matches'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    university_id = Column(Integer, ForeignKey('universities.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    
    # Matching scores (from university perspective)
    overall_score = Column(Float, nullable=False)
    academic_potential_score = Column(Float, nullable=True)
    financial_stability_score = Column(Float, nullable=True)
    cultural_fit_score = Column(Float, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    university = relationship("University", back_populates="university_matches")
    user = relationship("User")
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'university_id': self.university_id,
            'user_id': self.user_id,
            'overall_score': self.overall_score,
            'academic_potential_score': self.academic_potential_score,
            'financial_stability_score': self.financial_stability_score,
            'cultural_fit_score': self.cultural_fit_score,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'user': self.user.to_dict() if self.user else None
        }

class UniversityDataCollection(Base):
    __tablename__ = 'university_data_collections'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    university_name = Column(String(200), nullable=False, index=True)
    search_query = Column(String(500), nullable=True)
    target_urls = Column(JSON, nullable=True)  # List of URLs to scrape
    status = Column(String(50), default='pending')  # pending, in_progress, completed, failed
    
    # LLM Analysis Results
    llm_analysis = Column(JSON, nullable=True)  # Raw LLM response
    extracted_data = Column(JSON, nullable=True)  # Structured data extracted by LLM
    confidence_score = Column(Float, default=0.0)
    
    # Browser-use specific data
    browser_session_id = Column(String(100), nullable=True)
    scraped_content = Column(JSON, nullable=True)  # Raw scraped content from browser
    search_results = Column(JSON, nullable=True)  # Search engine results
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Relationships
    university = relationship("University", back_populates="data_collections")
    university_id = Column(Integer, ForeignKey('universities.id'), nullable=True)
    search_tasks = relationship("UniversitySearchTask", back_populates="data_collection")
    llm_analyses = relationship("LLMAnalysisResult", back_populates="data_collection")
    
    def __repr__(self) -> str:
        return f'<UniversityDataCollection {self.university_name}>'
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert university data collection object to dictionary"""
        return {
            'id': self.id,
            'university_name': self.university_name,
            'search_query': self.search_query,
            'target_urls': self.target_urls,
            'status': self.status,
            'llm_analysis': self.llm_analysis,
            'extracted_data': self.extracted_data,
            'confidence_score': self.confidence_score,
            'browser_session_id': self.browser_session_id,
            'scraped_content': self.scraped_content,
            'search_results': self.search_results,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'error_message': self.error_message,
            'university_id': self.university_id,
            'search_tasks': [task.to_dict() for task in self.search_tasks],
            'llm_analyses': [analysis.to_dict() for analysis in self.llm_analyses]
        }

class UniversitySearchTask(Base):
    __tablename__ = 'university_search_tasks'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    task_type = Column(String(100), nullable=False)  # 'university_info', 'programs', 'admissions', etc.
    university_name = Column(String(200), nullable=False, index=True)
    search_queries = Column(JSON, nullable=True)  # List of search queries to execute
    
    # Task configuration
    max_results = Column(Integer, default=10)
    search_engines = Column(JSON, nullable=True)  # ['google', 'bing', 'duckduckgo']
    include_news = Column(Boolean, default=True)
    include_social_media = Column(Boolean, default=False)
    
    # Task status
    status = Column(String(50), default='pending')  # pending, running, completed, failed
    progress = Column(Float, default=0.0)  # 0.0 to 1.0
    
    # Results
    search_results = Column(JSON, nullable=True)  # Raw search results
    processed_results = Column(JSON, nullable=True)  # Processed and filtered results
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Relationships
    data_collection = relationship("UniversityDataCollection", back_populates="search_tasks")
    data_collection_id = Column(Integer, ForeignKey('university_data_collections.id'), nullable=True)
    
    def __repr__(self) -> str:
        return f'<UniversitySearchTask {self.task_type} for {self.university_name}>'
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert university search task object to dictionary"""
        return {
            'id': self.id,
            'task_type': self.task_type,
            'university_name': self.university_name,
            'search_queries': self.search_queries,
            'max_results': self.max_results,
            'search_engines': self.search_engines,
            'include_news': self.include_news,
            'include_social_media': self.include_social_media,
            'status': self.status,
            'progress': self.progress,
            'search_results': self.search_results,
            'processed_results': self.processed_results,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'error_message': self.error_message,
            'data_collection_id': self.data_collection_id
        }

class LLMAnalysisResult(Base):
    __tablename__ = 'llm_analysis_results'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    data_collection_id = Column(Integer, ForeignKey('university_data_collections.id'), nullable=False)
    
    # Analysis details
    analysis_type = Column(String(100), nullable=False)  # 'university_info', 'programs', 'admissions', etc.
    model_used = Column(String(100), nullable=True)  # 'gpt-4', 'claude-3', etc.
    prompt_used = Column(Text, nullable=True)
    
    # Results
    raw_response = Column(Text, nullable=True)
    structured_data = Column(JSON, nullable=True)
    confidence_score = Column(Float, default=0.0)
    processing_time = Column(Float, nullable=True)  # seconds
    
    # Quality metrics
    data_completeness = Column(Float, default=0.0)  # 0.0 to 1.0
    data_accuracy = Column(Float, default=0.0)  # 0.0 to 1.0
    source_citations = Column(JSON, nullable=True)  # URLs and sources used
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    data_collection = relationship("UniversityDataCollection", back_populates="llm_analyses")
    
    def __repr__(self) -> str:
        return f'<LLMAnalysisResult {self.analysis_type}>'
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert LLM analysis result object to dictionary"""
        return {
            'id': self.id,
            'data_collection_id': self.data_collection_id,
            'analysis_type': self.analysis_type,
            'model_used': self.model_used,
            'prompt_used': self.prompt_used,
            'raw_response': self.raw_response,
            'structured_data': self.structured_data,
            'confidence_score': self.confidence_score,
            'processing_time': self.processing_time,
            'data_completeness': self.data_completeness,
            'data_accuracy': self.data_accuracy,
            'source_citations': self.source_citations,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
