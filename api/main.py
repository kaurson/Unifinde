from fastapi import FastAPI, Depends, HTTPException, status, Response
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import bcrypt
import sys
import os
from dotenv import load_dotenv
from sqlalchemy import or_
import json

# Load environment variables
load_dotenv()

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.database import get_db, engine
from database.models import Base as DatabaseBase, User, UniversityDataCollectionResult, Question, UserAnswer
from app.models import Base as AppBase, University, Program, Facility
from api.schemas import (
    UserCreate, UserLogin, UserProfile, UserUpdate, AuthResponse,
    UniversityResponse, ProgramResponse,
    QuestionnaireResponse, PersonalityProfile,
    QuestionResponse, UserAnswerCreate, UserAnswerResponse, QuestionnaireSubmission
)
from api.auth import get_current_user, create_access_token, set_auth_cookie, clear_auth_cookie
from api.matching import MatchingService
from api.enhanced_matching import EnhancedMatchingService
from api.questionnaire import QuestionnaireService
from api.vector_matcher import VectorMatchingService
from api.user_suggestions import UserSuggestionsService
from database.models import CollectionResultVector
# from api.school_scraper import SchoolScraperService
# from api.university_data_collection import router as university_data_router

# Create database tables
from database.models import Base as DatabaseBase
from app.models import Base as AppBase

# Create all tables from both model files
DatabaseBase.metadata.create_all(bind=engine)
AppBase.metadata.create_all(bind=engine)

app = FastAPI(
    title="University Matching App",
    description="An AI-powered app that matches students with universities and programs",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
        "http://localhost:8000",
        "http://127.0.0.1:8000"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# Security
# security = HTTPBearer() # This line is removed as per the new_code, as the security object is no longer used for login/register.

# Include routers
# app.include_router(university_data_router)

@app.get("/")
async def root():
    return {"message": "University Matching API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "database": "connected"}

@app.get("/test-auth")
async def test_auth(current_user: User = Depends(get_current_user)):
    """Test endpoint to check if authentication is working"""
    return {
        "authenticated": True,
        "user_id": str(current_user.id),
        "email": current_user.email,
        "username": current_user.username,
        "has_personality_profile": bool(current_user.personality_profile)
    }

@app.get("/vectors/status")
async def check_vectors_status(db: Session = Depends(get_db)):
    """Check the status of collection vectors"""
    try:
        collection_vectors_count = db.query(CollectionResultVector).count()
        collection_results_count = db.query(UniversityDataCollectionResult).count()
        
        return {
            "collection_vectors_count": collection_vectors_count,
            "collection_results_count": collection_results_count,
            "vectors_generated": collection_vectors_count > 0,
            "status": "ready" if collection_vectors_count > 0 else "needs_generation"
        }
    except Exception as e:
        return {
            "error": str(e),
            "status": "error"
        }

# Authentication endpoints
@app.options("/{full_path:path}")
async def options_handler(full_path: str):
    """Handle all CORS preflight requests"""
    return {"message": "OK"}

@app.post("/auth/register", response_model=AuthResponse)
async def register(user_data: UserCreate, response: Response, db: Session = Depends(get_db)):
    """Register new user"""
    try:
        # Check if user already exists
        existing_user = db.query(User).filter(
            (User.email == user_data.email) | (User.username == user_data.username)
        ).first()
        
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email or username already registered"
            )
        
        # Hash password
        password_hash = bcrypt.hashpw(user_data.password.encode('utf-8'), bcrypt.gensalt())
        
        # Create new user
        new_user = User(
            username=user_data.username,
            email=user_data.email,
            password_hash=password_hash.decode('utf-8'),
            name=user_data.name
        )
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        # Create access token and set cookie
        access_token = create_access_token(data={"sub": new_user.email})
        set_auth_cookie(response, access_token)
        
        return AuthResponse(
            access_token=access_token,
            token_type="bearer",
            user=UserProfile(
                id=str(new_user.id),
                username=new_user.username,
                email=new_user.email,
                name=new_user.name,
                age=new_user.age,
                phone=new_user.phone,
                income=new_user.income,
                personality_profile=new_user.personality_profile,
                personality_summary=new_user.personality_summary,
                questionnaire_answers=new_user.questionnaire_answers,
                preferred_majors=new_user.preferred_majors,
                preferred_locations=new_user.preferred_locations,
                min_acceptance_rate=new_user.min_acceptance_rate,
                max_tuition=new_user.max_tuition,
                preferred_university_type=new_user.preferred_university_type,
                created_at=new_user.created_at,
                updated_at=new_user.updated_at
            )
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Registration error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )

@app.post("/auth/login", response_model=AuthResponse)
async def login(user_data: UserLogin, response: Response, db: Session = Depends(get_db)):
    """Login user"""
    try:
        user = db.query(User).filter(User.email == user_data.email).first()
        
        if not user or not bcrypt.checkpw(user_data.password.encode('utf-8'), user.password_hash.encode('utf-8')):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Create access token and set cookie
        access_token = create_access_token(data={"sub": user.email})
        set_auth_cookie(response, access_token)
        
        return AuthResponse(
            access_token=access_token,
            token_type="bearer",
            user=UserProfile(
                id=str(user.id),
                username=user.username,
                email=user.email,
                name=user.name,
                age=user.age,
                phone=user.phone,
                income=user.income,
                personality_profile=user.personality_profile,
                personality_summary=user.personality_summary,
                questionnaire_answers=user.questionnaire_answers,
                preferred_majors=user.preferred_majors,
                preferred_locations=user.preferred_locations,
                min_acceptance_rate=user.min_acceptance_rate,
                max_tuition=user.max_tuition,
                preferred_university_type=user.preferred_university_type,
                created_at=user.created_at,
                updated_at=user.updated_at
            )
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )

@app.post("/auth/logout")
async def logout(response: Response):
    """Clear authentication cookies"""
    clear_auth_cookie(response)
    return {"message": "Logged out successfully"}

@app.get("/profile", response_model=UserProfile)
async def get_profile(current_user: User = Depends(get_current_user)):
    """Get current user profile"""
    return UserProfile(
        id=str(current_user.id),
        username=current_user.username,
        email=current_user.email,
        name=current_user.name,
        age=current_user.age,
        phone=current_user.phone,
        income=current_user.income,
        personality_profile=current_user.personality_profile,
        personality_summary=current_user.personality_summary,
        questionnaire_answers=current_user.questionnaire_answers,
        preferred_majors=current_user.preferred_majors,
        preferred_locations=current_user.preferred_locations,
        min_acceptance_rate=current_user.min_acceptance_rate,
        max_tuition=current_user.max_tuition,
        preferred_university_type=current_user.preferred_university_type,
        created_at=current_user.created_at,
        updated_at=current_user.updated_at
    )

@app.put("/profile", response_model=UserProfile)
async def update_profile(
    profile_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update user profile and invalidate cached vectors"""
    try:
        # Update basic profile fields
        if profile_data.name is not None:
            current_user.name = profile_data.name
        if profile_data.age is not None:
            current_user.age = profile_data.age
        if profile_data.phone is not None:
            current_user.phone = profile_data.phone
        if profile_data.income is not None:
            current_user.income = profile_data.income
        if profile_data.preferred_majors is not None:
            current_user.preferred_majors = profile_data.preferred_majors
        if profile_data.preferred_locations is not None:
            current_user.preferred_locations = profile_data.preferred_locations
        if profile_data.min_acceptance_rate is not None:
            current_user.min_acceptance_rate = profile_data.min_acceptance_rate
        if profile_data.max_tuition is not None:
            current_user.max_tuition = profile_data.max_tuition
        if profile_data.preferred_university_type is not None:
            current_user.preferred_university_type = profile_data.preferred_university_type
        
        # Update student profile if provided
        if profile_data.student_profile is not None:
            if not current_user.student_profile:
                # Create new student profile
                student_profile = StudentProfile(user_id=current_user.id)
                db.add(student_profile)
                db.commit()
                db.refresh(student_profile)
                current_user.student_profile = student_profile
            
            # Update student profile fields
            student_profile = current_user.student_profile
            for field, value in profile_data.student_profile.dict(exclude_unset=True).items():
                if hasattr(student_profile, field):
                    setattr(student_profile, field, value)
        
        db.commit()
        db.refresh(current_user)
        
        # Invalidate user vector since profile has changed
        try:
            vector_service = VectorMatchingService()
            await vector_service.invalidate_user_vector(current_user.id, db)
        except Exception as e:
            # Log the error but don't fail the profile update
            print(f"Warning: Failed to invalidate user vector: {e}")
        
        return current_user
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update profile: {str(e)}"
        )

# Questionnaire endpoints
@app.get("/questions", response_model=List[QuestionResponse])
async def get_questions(
    active_only: bool = True,
    db: Session = Depends(get_db)
):
    """Get all questions"""
    query = db.query(Question)
    
    if active_only:
        query = query.filter(Question.is_active == True)
    
    questions = query.order_by(Question.order_index).all()
    
    return [
        QuestionResponse(
            id=str(question.id),
            question_text=question.question_text,
            question_type=question.question_type,
            category=question.category,
            order_index=question.order_index,
            is_active=question.is_active,
            created_at=question.created_at,
            updated_at=question.updated_at
        ) for question in questions
    ]

@app.get("/questions/{question_id}", response_model=QuestionResponse)
async def get_question(question_id: str, db: Session = Depends(get_db)):
    """Get a specific question by ID"""
    question = db.query(Question).filter(Question.id == question_id).first()
    
    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question not found"
        )
    
    return QuestionResponse(
        id=str(question.id),
        question_text=question.question_text,
        question_type=question.question_type,
        category=question.category,
        order_index=question.order_index,
        is_active=question.is_active,
        created_at=question.created_at,
        updated_at=question.updated_at
    )

@app.post("/questions/{question_id}/answer", response_model=UserAnswerResponse)
async def submit_answer(
    question_id: str,
    answer_data: UserAnswerCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Submit an answer to a specific question"""
    
    # Verify the question exists
    question = db.query(Question).filter(Question.id == question_id).first()
    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question not found"
        )
    
    # Check if user already answered this question
    existing_answer = db.query(UserAnswer).filter(
        UserAnswer.user_id == current_user.id,
        UserAnswer.question_id == question_id
    ).first()
    
    if existing_answer:
        # Update existing answer
        existing_answer.answer_text = answer_data.answer_text
        existing_answer.answer_data = answer_data.answer_data
        db.commit()
        db.refresh(existing_answer)
        
        return UserAnswerResponse(
            id=str(existing_answer.id),
            user_id=str(existing_answer.user_id),
            question_id=str(existing_answer.question_id),
            answer_text=existing_answer.answer_text,
            answer_data=existing_answer.answer_data,
            created_at=existing_answer.created_at,
            updated_at=existing_answer.updated_at
        )
    else:
        # Create new answer
        new_answer = UserAnswer(
            user_id=current_user.id,
            question_id=question_id,
            answer_text=answer_data.answer_text,
            answer_data=answer_data.answer_data
        )
        
        db.add(new_answer)
        db.commit()
        db.refresh(new_answer)
        
        return UserAnswerResponse(
            id=str(new_answer.id),
            user_id=str(new_answer.user_id),
            question_id=str(new_answer.question_id),
            answer_text=new_answer.answer_text,
            answer_data=new_answer.answer_data,
            created_at=new_answer.created_at,
            updated_at=new_answer.updated_at
        )

@app.get("/user/answers", response_model=List[UserAnswerResponse])
async def get_user_answers(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all answers for the current user"""
    answers = db.query(UserAnswer).filter(UserAnswer.user_id == current_user.id).all()
    
    return [
        UserAnswerResponse(
            id=str(answer.id),
            user_id=str(answer.user_id),
            question_id=str(answer.question_id),
            answer_text=answer.answer_text,
            answer_data=answer.answer_data,
            created_at=answer.created_at,
            updated_at=answer.updated_at
        ) for answer in answers
    ]

@app.post("/questionnaire/submit", response_model=PersonalityProfile)
async def submit_questionnaire(
    questionnaire_data: QuestionnaireSubmission,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Submit complete questionnaire and generate personality profile"""
    try:
        # Save all answers
        for answer_data in questionnaire_data.answers:
            # Check if answer already exists
            existing_answer = db.query(UserAnswer).filter(
                UserAnswer.user_id == current_user.id,
                UserAnswer.question_id == answer_data.question_id
            ).first()
            
            if existing_answer:
                # Update existing answer
                existing_answer.answer_text = answer_data.answer_text
                existing_answer.answer_data = answer_data.answer_data
            else:
                # Create new answer
                new_answer = UserAnswer(
                    user_id=current_user.id,
                    question_id=answer_data.question_id,
                    answer_text=answer_data.answer_text,
                    answer_data=answer_data.answer_data
                )
                db.add(new_answer)
        
        # Update user preferences
        if questionnaire_data.preferred_majors:
            current_user.preferred_majors = questionnaire_data.preferred_majors
        if questionnaire_data.preferred_locations:
            current_user.preferred_locations = questionnaire_data.preferred_locations
        
        # Generate personality profile
        questionnaire_service = QuestionnaireService()
        
        # Convert answers to the format expected by the service
        answers_dict = {answer.question_id: answer.answer_text for answer in questionnaire_data.answers}
        
        questionnaire_response = QuestionnaireResponse(
            answers=answers_dict,
            preferred_majors=questionnaire_data.preferred_majors or [],
            preferred_locations=questionnaire_data.preferred_locations or []
        )
        
        personality_profile = await questionnaire_service.generate_personality_profile(
            questionnaire_response
        )
        
        # Update user with personality profile
        current_user.personality_profile = personality_profile
        current_user.personality_summary = personality_profile.get('summary', '')
        
        db.commit()
        db.refresh(current_user)
        
        return personality_profile
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit questionnaire: {str(e)}"
        )

# University endpoints
@app.get("/universities", response_model=List[UniversityResponse])
async def get_universities(
    skip: int = 0,
    limit: int = 100,
    country: Optional[str] = None,
    field: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get universities with optional filtering"""
    query = db.query(University)
    
    if country:
        query = query.filter(University.country == country)
    
    if field:
        # Filter by programs that offer the specified field
        query = query.join(Program).filter(Program.field.contains(field))
    
    universities = query.offset(skip).limit(limit).all()
    
    return [
        UniversityResponse(
            id=str(university.id),
            name=university.name,
            website=university.website,
            country=university.country,
            city=university.city,
            state=university.state,
            postal_code=university.postal_code,
            phone=university.phone,
            email=university.email,
            founded_year=university.founded_year,
            type=university.type,
            accreditation=university.accreditation,
            student_population=university.student_population,
            faculty_count=university.faculty_count,
            acceptance_rate=university.acceptance_rate,
            tuition_domestic=university.tuition_domestic,
            tuition_international=university.tuition_international,
            world_ranking=university.world_ranking,
            national_ranking=university.national_ranking,
            description=university.description,
            mission_statement=university.mission_statement,
            vision_statement=university.vision_statement,
            scraped_at=university.scraped_at,
            last_updated=university.last_updated,
            source_url=university.source_url,
            confidence_score=university.confidence_score,
            programs=[
                ProgramResponse(
                    id=str(program.id),
                    university_id=str(program.university_id),
                    name=program.name,
                    level=program.level,
                    field=program.field,
                    duration=program.duration,
                    tuition=program.tuition,
                    description=program.description
                ) for program in university.programs
            ]
        ) for university in universities
    ]

@app.get("/browse-universities")
async def browse_universities(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    country: Optional[str] = None,
    state: Optional[str] = None,
    type: Optional[str] = None,
    has_ranking: Optional[bool] = None,
    has_programs: Optional[bool] = None,
    min_acceptance_rate: Optional[float] = None,
    max_acceptance_rate: Optional[float] = None,
    min_tuition: Optional[float] = None,
    max_tuition: Optional[float] = None,
    min_student_population: Optional[int] = None,
    max_student_population: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Browse all universities from collection results with comprehensive filtering"""
    from database.models import UniversityDataCollectionResult
    
    # Start with base query
    query = db.query(UniversityDataCollectionResult)
    
    # Apply filters
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                UniversityDataCollectionResult.name.ilike(search_term),
                UniversityDataCollectionResult.city.ilike(search_term),
                UniversityDataCollectionResult.state.ilike(search_term),
                UniversityDataCollectionResult.country.ilike(search_term),
                UniversityDataCollectionResult.description.ilike(search_term)
            )
        )
    
    if country:
        query = query.filter(UniversityDataCollectionResult.country.ilike(f"%{country}%"))
    
    if state:
        query = query.filter(UniversityDataCollectionResult.state.ilike(f"%{state}%"))
    
    if type:
        query = query.filter(UniversityDataCollectionResult.type.ilike(f"%{type}%"))
    
    if has_ranking:
        query = query.filter(
            or_(
                UniversityDataCollectionResult.world_ranking.isnot(None),
                UniversityDataCollectionResult.national_ranking.isnot(None),
                UniversityDataCollectionResult.regional_ranking.isnot(None)
            )
        )
    
    if has_programs:
        query = query.filter(UniversityDataCollectionResult.programs.isnot(None))
    
    if min_acceptance_rate is not None:
        query = query.filter(UniversityDataCollectionResult.acceptance_rate >= min_acceptance_rate)
    
    if max_acceptance_rate is not None:
        query = query.filter(UniversityDataCollectionResult.acceptance_rate <= max_acceptance_rate)
    
    if min_tuition is not None:
        query = query.filter(UniversityDataCollectionResult.tuition_domestic >= min_tuition)
    
    if max_tuition is not None:
        query = query.filter(UniversityDataCollectionResult.tuition_domestic <= max_tuition)
    
    if min_student_population is not None:
        query = query.filter(UniversityDataCollectionResult.student_population >= min_student_population)
    
    if max_student_population is not None:
        query = query.filter(UniversityDataCollectionResult.student_population <= max_student_population)
    
    # Get total count for pagination
    total_count = query.count()
    
    # Apply pagination
    universities = query.offset(skip).limit(limit).all()
    
    # Convert to response format
    results = []
    for university in universities:
        # Parse JSON fields safely
        programs = None
        student_life = None
        subject_rankings = None
        
        try:
            if university.programs:
                programs = json.loads(university.programs) if isinstance(university.programs, str) else university.programs
        except:
            programs = None
            
        try:
            if university.student_life:
                student_life = json.loads(university.student_life) if isinstance(university.student_life, str) else university.student_life
        except:
            student_life = None
            
        try:
            if university.subject_rankings:
                subject_rankings = json.loads(university.subject_rankings) if isinstance(university.subject_rankings, str) else university.subject_rankings
        except:
            subject_rankings = None
        
        results.append({
            "id": str(university.id),
            "name": university.name,
            "website": university.website,
            "country": university.country,
            "city": university.city,
            "state": university.state,
            "phone": university.phone,
            "email": university.email,
            "founded_year": university.founded_year,
            "type": university.type,
            "student_population": university.student_population,
            "undergraduate_population": university.undergraduate_population,
            "graduate_population": university.graduate_population,
            "faculty_count": university.faculty_count,
            "student_faculty_ratio": university.student_faculty_ratio,
            "acceptance_rate": university.acceptance_rate,
            "tuition_domestic": university.tuition_domestic,
            "tuition_international": university.tuition_international,
            "room_and_board": university.room_and_board,
            "total_cost_of_attendance": university.total_cost_of_attendance,
            "financial_aid_available": university.financial_aid_available,
            "average_financial_aid_package": university.average_financial_aid_package,
            "scholarships_available": university.scholarships_available,
            "world_ranking": university.world_ranking,
            "national_ranking": university.national_ranking,
            "regional_ranking": university.regional_ranking,
            "subject_rankings": subject_rankings,
            "description": university.description,
            "mission_statement": university.mission_statement,
            "vision_statement": university.vision_statement,
            "campus_size": university.campus_size,
            "campus_type": university.campus_type,
            "climate": university.climate,
            "timezone": university.timezone,
            "international_students_percentage": university.international_students_percentage,
            "programs": programs,
            "student_life": student_life,
            "confidence_score": university.confidence_score,
            "source_urls": university.source_urls,
            "last_updated": university.last_updated,
            "created_at": university.created_at.isoformat() if university.created_at else None,
            "updated_at": university.updated_at.isoformat() if university.updated_at else None
        })
    
    return {
        "universities": results,
        "total_count": total_count,
        "skip": skip,
        "limit": limit,
        "has_more": skip + limit < total_count
    }

@app.get("/universities/{university_id}", response_model=UniversityResponse)
async def get_university(university_id: str, db: Session = Depends(get_db)):
    """Get a specific university by ID"""
    university = db.query(University).filter(University.id == university_id).first()
    
    if not university:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="University not found"
        )
    
    return UniversityResponse(
        id=str(university.id),
        name=university.name,
        website=university.website,
        country=university.country,
        city=university.city,
        state=university.state,
        postal_code=university.postal_code,
        phone=university.phone,
        email=university.email,
        founded_year=university.founded_year,
        type=university.type,
        accreditation=university.accreditation,
        student_population=university.student_population,
        faculty_count=university.faculty_count,
        acceptance_rate=university.acceptance_rate,
        tuition_domestic=university.tuition_domestic,
        tuition_international=university.tuition_international,
        world_ranking=university.world_ranking,
        national_ranking=university.national_ranking,
        description=university.description,
        mission_statement=university.mission_statement,
        vision_statement=university.vision_statement,
        scraped_at=university.scraped_at,
        last_updated=university.last_updated,
        source_url=university.source_url,
        confidence_score=university.confidence_score,
        programs=[
            ProgramResponse(
                id=str(program.id),
                university_id=str(program.university_id),
                name=program.name,
                level=program.level,
                field=program.field,
                duration=program.duration,
                tuition=program.tuition,
                description=program.description
            ) for program in university.programs
        ]
    )

@app.get("/universities/collection/{university_id}")
async def get_collection_university(university_id: str, db: Session = Depends(get_db)):
    """Get a specific university from the collection results table"""
    from database.models import UniversityDataCollectionResult
    
    university = db.query(UniversityDataCollectionResult).filter(UniversityDataCollectionResult.id == university_id).first()
    
    if not university:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="University not found"
        )
    
    # Convert to the same format as UniversityResponse but with collection result fields
    return {
        "id": str(university.id),
        "name": university.name,
        "website": university.website,
        "country": university.country,
        "city": university.city,
        "state": university.state,
        "phone": university.phone,
        "email": university.email,
        "founded_year": university.founded_year,
        "type": university.type,
        "student_population": university.student_population,
        "undergraduate_population": university.undergraduate_population,
        "graduate_population": university.graduate_population,
        "faculty_count": university.faculty_count,
        "student_faculty_ratio": university.student_faculty_ratio,
        "acceptance_rate": university.acceptance_rate,
        "tuition_domestic": university.tuition_domestic,
        "tuition_international": university.tuition_international,
        "room_and_board": university.room_and_board,
        "total_cost_of_attendance": university.total_cost_of_attendance,
        "financial_aid_available": university.financial_aid_available,
        "average_financial_aid_package": university.average_financial_aid_package,
        "scholarships_available": university.scholarships_available,
        "world_ranking": university.world_ranking,
        "national_ranking": university.national_ranking,
        "regional_ranking": university.regional_ranking,
        "subject_rankings": university.subject_rankings,
        "description": university.description,
        "mission_statement": university.mission_statement,
        "vision_statement": university.vision_statement,
        "campus_size": university.campus_size,
        "campus_type": university.campus_type,
        "climate": university.climate,
        "timezone": university.timezone,
        "international_students_percentage": university.international_students_percentage,
        "programs": university.programs,
        "student_life": university.student_life,
        "financial_aid": university.financial_aid,
        "international_students": university.international_students,
        "alumni": university.alumni,
        "confidence_score": university.confidence_score,
        "source_urls": university.source_urls,
        "last_updated": university.last_updated,
        "created_at": university.created_at.isoformat() if university.created_at else None,
        "updated_at": university.updated_at.isoformat() if university.updated_at else None
    }

# Vector Matching endpoints
@app.post("/matches/generate")
async def generate_matches(
    use_vector_matching: bool = True,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate matches for current user using vector similarity or traditional scoring"""
    if not current_user.personality_profile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please complete the questionnaire first"
        )
    
    matching_service = MatchingService()
    
    try:
        matches = await matching_service.generate_matches(
            current_user, 
            db, 
            use_vector_matching=use_vector_matching,
            limit=limit
        )
        
        return {
            "message": f"Generated {len(matches)} matches using {'vector similarity' if use_vector_matching else 'traditional scoring'}",
            "matches": matches,
            "matching_method": "vector_similarity" if use_vector_matching else "traditional_scoring"
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate matches: {str(e)}"
        )

@app.get("/matches/compare")
async def compare_matching_methods(
    limit: int = 10,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Compare vector matching vs traditional matching results"""
    if not current_user.personality_profile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please complete the questionnaire first"
        )
    
    matching_service = MatchingService()
    
    try:
        comparison = await matching_service.compare_matching_methods(current_user, db, limit)
        return comparison
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to compare matching methods: {str(e)}"
        )

@app.get("/matches/similar-users")
async def get_similar_users(
    limit: int = 10,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Find users with similar profiles using vector similarity"""
    if not current_user.personality_profile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please complete the questionnaire first"
        )
    
    matching_service = MatchingService()
    
    try:
        similar_users = await matching_service.get_similar_users(current_user, db, limit)
        return {
            "similar_users": similar_users,
            "total_found": len(similar_users)
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to find similar users: {str(e)}"
        )

@app.post("/matches/clear-cache")
async def clear_matching_cache(current_user: User = Depends(get_current_user)):
    """Clear the vector matching cache"""
    matching_service = MatchingService()
    matching_service.clear_vector_cache()
    return {"message": "Vector matching cache cleared successfully"}

# New vector storage management endpoints
@app.get("/vectors/statistics")
async def get_vector_statistics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get statistics about stored vectors and vector storage performance"""
    try:
        vector_service = VectorMatchingService()
        stats = await vector_service.get_vector_statistics(db)
        performance_metrics = await vector_service.get_vector_performance_metrics(db)
        
        return {
            "vector_statistics": stats,
            "performance_metrics": performance_metrics
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get vector statistics: {str(e)}"
        )

@app.post("/vectors/optimize")
async def optimize_vector_storage(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Optimize vector storage by cleaning up invalid vectors and regenerating as needed"""
    try:
        vector_service = VectorMatchingService()
        optimization_results = await vector_service.optimize_vector_storage(db)
        
        return {
            "message": "Vector storage optimization completed",
            "optimization_results": optimization_results
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to optimize vector storage: {str(e)}"
        )

@app.post("/vectors/generate-batch")
async def generate_batch_vectors(
    vector_type: str = "university",  # "university" or "user"
    batch_size: int = 10,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate vectors in batch for universities or users that don't have them"""
    try:
        vector_service = VectorMatchingService()
        
        if vector_type == "university":
            await vector_service.batch_generate_university_vectors(db, batch_size)
            message = f"Generated vectors for up to {batch_size} universities"
        elif vector_type == "user":
            await vector_service.batch_generate_user_vectors(db, batch_size)
            message = f"Generated vectors for up to {batch_size} users"
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="vector_type must be 'university' or 'user'"
            )
        
        return {"message": message}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate batch vectors: {str(e)}"
        )

@app.post("/vectors/invalidate-user")
async def invalidate_user_vector(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Invalidate and regenerate user vector when profile changes"""
    try:
        vector_service = VectorMatchingService()
        await vector_service.invalidate_user_vector(current_user.id, db)
        
        return {"message": "User vector invalidated and will be regenerated on next use"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to invalidate user vector: {str(e)}"
        )

@app.post("/vectors/cleanup-cache")
async def cleanup_expired_cache(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Clean up expired cache entries"""
    try:
        vector_service = VectorMatchingService()
        await vector_service.cleanup_expired_cache(db)
        
        return {"message": "Expired cache entries cleaned up successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cleanup cache: {str(e)}"
        )

@app.post("/matches/generate-with-cache")
async def generate_matches_with_cache(
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate matches using vector storage with caching to avoid redundant computations"""
    if not current_user.personality_profile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please complete the questionnaire first"
        )
    
    vector_service = VectorMatchingService()
    
    try:
        matches = await vector_service.find_matches_with_cache(current_user, db, limit)
        
        return {
            "message": f"Generated {len(matches)} matches using vector storage with caching",
            "matches": matches,
            "matching_method": "vector_similarity_with_caching"
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate matches: {str(e)}"
        )

@app.post("/matches/collection/generate-with-cache")
async def generate_collection_matches_with_cache(
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate collection matches using vector storage with caching"""
    if not current_user.personality_profile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please complete the questionnaire first"
        )
    
    vector_service = VectorMatchingService()
    
    try:
        # Check if collection vectors exist
        collection_vectors_count = db.query(CollectionResultVector).count()
        
        if collection_vectors_count == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No collection vectors found. Please generate collection vectors first."
            )
        
        matches = await vector_service.find_collection_matches_with_cache(current_user, db, limit)
        
        return {
            "message": f"Generated {len(matches)} collection matches using vector storage with caching",
            "matches": matches,
            "matching_method": "collection_vector_similarity_with_caching",
            "total_collection_vectors": collection_vectors_count
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate collection matches: {str(e)}"
        )

@app.post("/matches/collection/generate")
async def generate_collection_matches(
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate matches for current user using pre-generated collection result vectors"""
    if not current_user.personality_profile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please complete the questionnaire first"
        )
    
    suggestions_service = UserSuggestionsService()
    
    try:
        # Check if collection vectors exist
        collection_vectors_count = db.query(CollectionResultVector).count()
        print(f"Found {collection_vectors_count} collection vectors")
        
        if collection_vectors_count == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No collection vectors found. Please generate vectors first."
            )
        
        vector_matcher = VectorMatchingService()
        print(f"Generating matches for user {current_user.email}")
        
        matches = await vector_matcher.find_collection_matches(
            current_user, 
            db, 
            limit=limit
        )
        
        print(f"Generated {len(matches)} matches")
        
        # Save suggestions to database
        suggestions_service.save_suggestions(current_user, matches, db)
        
        return {
            "message": f"Generated {len(matches)} matches using collection result vectors",
            "matches": matches,
            "matching_method": "collection_vector_similarity",
            "total_vectors_available": collection_vectors_count,
            "suggestions_saved": True
        }
    
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        print(f"Error in generate_collection_matches: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate collection matches: {str(e)}"
        )

# Enhanced Matching endpoints
@app.post("/matches/enhanced/generate")
async def generate_enhanced_matches(
    use_vector_matching: bool = True,
    limit: int = 20,
    include_programs: bool = True,
    min_score: float = 0.5,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate enhanced matches with detailed scoring and analysis"""
    if not current_user.personality_profile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please complete the questionnaire first"
        )
    
    enhanced_matching_service = EnhancedMatchingService()
    suggestions_service = UserSuggestionsService()
    
    try:
        matches = await enhanced_matching_service.generate_enhanced_matches(
            current_user, 
            db, 
            use_vector_matching=use_vector_matching,
            limit=limit,
            include_programs=include_programs,
            min_score=min_score
        )
        
        # Convert MatchResult objects to dictionaries for JSON response
        match_dicts = []
        for match in matches:
            match_dict = {
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
            match_dicts.append(match_dict)
        
        # Save suggestions to database
        suggestions_service.save_suggestions(current_user, match_dicts, db)
        
        return {
            "message": f"Generated {len(match_dicts)} enhanced matches using {'vector similarity' if use_vector_matching else 'traditional scoring'}",
            "matches": match_dicts,
            "matching_method": "vector_similarity" if use_vector_matching else "traditional_scoring",
            "suggestions_saved": True
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate enhanced matches: {str(e)}"
        )


# User Suggestions endpoints
@app.get("/suggestions")
async def get_user_suggestions(
    limit: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get saved university suggestions for the current user"""
    suggestions_service = UserSuggestionsService()
    
    try:
        suggestions = suggestions_service.get_user_suggestions(current_user, db, limit)
        stats = suggestions_service.get_suggestion_stats(current_user, db)
        
        return {
            "suggestions": suggestions,
            "stats": stats,
            "total_count": len(suggestions)
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve suggestions: {str(e)}"
        )


@app.post("/suggestions/clear")
async def clear_user_suggestions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Clear all saved suggestions for the current user"""
    suggestions_service = UserSuggestionsService()
    
    try:
        cleared = suggestions_service.clear_suggestions(current_user, db)
        
        return {
            "message": "Suggestions cleared successfully" if cleared else "No suggestions to clear",
            "cleared": cleared
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear suggestions: {str(e)}"
        )


@app.get("/suggestions/stats")
async def get_suggestion_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get statistics about user's suggestions"""
    suggestions_service = UserSuggestionsService()
    
    try:
        stats = suggestions_service.get_suggestion_stats(current_user, db)
        
        return {
            "stats": stats,
            "has_suggestions": suggestions_service.has_suggestions(current_user, db)
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve suggestion stats: {str(e)}"
        )


@app.post("/suggestions/regenerate")
async def regenerate_suggestions(
    use_vector_matching: bool = True,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Regenerate university suggestions for the current user"""
    if not current_user.personality_profile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please complete the questionnaire first"
        )
    
    suggestions_service = UserSuggestionsService()
    
    try:
        # Clear existing suggestions
        suggestions_service.clear_suggestions(current_user, db)
        
        # Generate new suggestions using collection matches (most comprehensive)
        vector_matcher = VectorMatchingService()
        matches = await vector_matcher.find_collection_matches(
            current_user, 
            db, 
            limit=limit
        )
        
        # Save new suggestions
        suggestions_service.save_suggestions(current_user, matches, db)
        
        return {
            "message": f"Regenerated {len(matches)} suggestions",
            "suggestions_count": len(matches),
            "matching_method": "collection_vector_similarity"
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to regenerate suggestions: {str(e)}"
        )

@app.get("/matches/enhanced/analysis")
async def get_matching_analysis(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get detailed analysis of user's matching profile"""
    if not current_user.personality_profile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please complete the questionnaire first"
        )
    
    enhanced_matching_service = EnhancedMatchingService()
    
    try:
        # Generate a small set of matches for analysis
        matches = await enhanced_matching_service.generate_enhanced_matches(
            current_user, 
            db, 
            use_vector_matching=True,
            limit=10,
            include_programs=True,
            min_score=0.3
        )
        
        # Calculate average scores
        if matches:
            avg_scores = {
                "overall": sum(m.match_score.overall for m in matches) / len(matches),
                "academic": sum(m.match_score.academic for m in matches) / len(matches),
                "financial": sum(m.match_score.financial for m in matches) / len(matches),
                "location": sum(m.match_score.location for m in matches) / len(matches),
                "personality": sum(m.match_score.personality for m in matches) / len(matches),
                "career": sum(m.match_score.career for m in matches) / len(matches),
                "social": sum(m.match_score.social for m in matches) / len(matches)
            }
        else:
            avg_scores = {
                "overall": 0.0,
                "academic": 0.0,
                "financial": 0.0,
                "location": 0.0,
                "personality": 0.0,
                "career": 0.0,
                "social": 0.0
            }
        
        # Generate recommendations
        recommendations = []
        
        if avg_scores["academic"] < 0.6:
            recommendations.append("Consider improving your academic profile or adjusting your university preferences")
        
        if avg_scores["financial"] < 0.6:
            recommendations.append("Consider expanding your budget or looking for universities with better financial aid")
        
        if avg_scores["location"] < 0.6:
            recommendations.append("Consider being more flexible with location preferences")
        
        if avg_scores["personality"] < 0.6:
            recommendations.append("Consider universities with different learning environments")
        
        return {
            "user_profile_summary": {
                "name": current_user.name,
                "preferred_majors": current_user.preferred_majors,
                "preferred_locations": current_user.preferred_locations,
                "max_tuition": current_user.max_tuition,
                "preferred_university_type": current_user.preferred_university_type
            },
            "average_match_scores": avg_scores,
            "recommendations": recommendations,
            "total_universities_analyzed": len(matches),
            "profile_completeness": _calculate_profile_completeness(current_user)
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate matching analysis: {str(e)}"
        )

@app.post("/matches/enhanced/filter")
async def filter_enhanced_matches(
    filters: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Filter enhanced matches based on specific criteria"""
    if not current_user.personality_profile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please complete the questionnaire first"
        )
    
    enhanced_matching_service = EnhancedMatchingService()
    
    try:
        # Generate initial matches
        initial_matches = await enhanced_matching_service.generate_enhanced_matches(
            current_user, 
            db, 
            use_vector_matching=True,
            limit=50,  # Get more matches for filtering
            include_programs=True,
            min_score=0.3
        )
        
        # Apply filters
        filtered_matches = []
        for match in initial_matches:
            if _apply_filters(match, filters):
                filtered_matches.append(match)
        
        # Convert to dictionaries
        match_dicts = []
        for match in filtered_matches:
            match_dict = {
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
            match_dicts.append(match_dict)
        
        return {
            "message": f"Filtered {len(filtered_matches)} matches from {len(initial_matches)} total matches",
            "matches": match_dicts,
            "filters_applied": filters,
            "total_matches": len(filtered_matches)
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to filter matches: {str(e)}"
        )

def _apply_filters(match, filters: Dict[str, Any]) -> bool:
    """Apply filters to a match"""
    university_data = match.university_data
    
    # Location filter
    if "locations" in filters and filters["locations"]:
        if university_data.get("city") not in filters["locations"]:
            return False
    
    # Tuition filter
    if "max_tuition" in filters and filters["max_tuition"]:
        if university_data.get("tuition_domestic", 0) > filters["max_tuition"]:
            return False
    
    # University type filter
    if "university_types" in filters and filters["university_types"]:
        if university_data.get("type") not in filters["university_types"]:
            return False
    
    # Program field filter
    if "program_fields" in filters and filters["program_fields"] and match.program_data:
        if match.program_data.get("field") not in filters["program_fields"]:
            return False
    
    # Match score filter
    if "min_overall_score" in filters and filters["min_overall_score"]:
        if match.match_score.overall < filters["min_overall_score"]:
            return False
    
    # Match type filter
    if "match_types" in filters and filters["match_types"]:
        if match.match_type.value not in filters["match_types"]:
            return False
    
    return True

def _calculate_profile_completeness(user: User) -> float:
    """Calculate the completeness of user profile"""
    total_fields = 0
    filled_fields = 0
    
    # Basic profile fields
    basic_fields = [
        user.name, user.age, user.phone, user.income,
        user.preferred_majors, user.preferred_locations,
        user.min_acceptance_rate, user.max_tuition,
        user.preferred_university_type, user.personality_profile
    ]
    
    for field in basic_fields:
        total_fields += 1
        if field is not None and field != []:
            filled_fields += 1
    
    # Student profile fields
    if user.student_profile:
        student = user.student_profile
        student_fields = [
            student.gpa, student.sat_total, student.act_composite,
            student.current_school, student.graduation_year,
            student.preferred_class_size, student.career_aspirations
        ]
        
        for field in student_fields:
            total_fields += 1
            if field is not None:
                filled_fields += 1
    
    return (filled_fields / total_fields) * 100 if total_fields > 0 else 0

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 