from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import List, Optional
import jwt
from datetime import datetime, timedelta
import bcrypt
import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.models import Base as DatabaseBase, User, UniversityDataCollectionResult, Question, UserAnswer
from app.models import Base as AppBase, University, Program, Facility
from database.database import get_db, engine
from api.schemas import (
    UserCreate, UserLogin, UserProfile, UserUpdate, AuthResponse,
    UniversityResponse, ProgramResponse,
    QuestionnaireResponse, PersonalityProfile,
    QuestionResponse, UserAnswerCreate, UserAnswerResponse, QuestionnaireSubmission
)
from api.auth import get_current_user, create_access_token
from api.matching import MatchingService
from api.questionnaire import QuestionnaireService
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
security = HTTPBearer()

# Include routers
# app.include_router(university_data_router)

@app.get("/")
async def root():
    return {"message": "University Matching API"}

# Authentication endpoints
@app.options("/{full_path:path}")
async def options_handler(full_path: str):
    """Handle all CORS preflight requests"""
    return {"message": "OK"}

@app.post("/auth/register", response_model=AuthResponse)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """Register a new user"""
    print(f"🔍 Registration attempt received for: {user_data.email}")
    try:
        # Check if user already exists
        existing_user = db.query(User).filter(
            (User.email == user_data.email) | (User.username == user_data.username)
        ).first()
        
        if existing_user:
            if existing_user.email == user_data.email:
                print(f"❌ Registration failed: Email already exists - {user_data.email}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="User with this email already exists"
                )
            else:
                print(f"❌ Registration failed: Username already taken - {user_data.username}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Username already taken"
                )
        
        # Hash password
        hashed_password = bcrypt.hashpw(user_data.password.encode('utf-8'), bcrypt.gensalt())
        
        # Create new user
        new_user = User(
            username=user_data.username,
            email=user_data.email,
            password_hash=hashed_password.decode('utf-8'),
            name=user_data.name
        )
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        # Create access token
        access_token = create_access_token(data={"sub": new_user.email})
        
        print(f"✅ Registration successful for: {user_data.email}")
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
async def login(user_data: UserLogin, db: Session = Depends(get_db)):
    """Login user"""
    try:
        user = db.query(User).filter(User.email == user_data.email).first()
        
        if not user or not bcrypt.checkpw(user_data.password.encode('utf-8'), user.password_hash.encode('utf-8')):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        access_token = create_access_token(data={"sub": user.email})
        
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
    """Update user profile"""
    for field, value in profile_data.dict(exclude_unset=True).items():
        setattr(current_user, field, value)
    
    db.commit()
    db.refresh(current_user)
    
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 