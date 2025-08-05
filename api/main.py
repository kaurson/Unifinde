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

from database.models import Base, User, University, School, Program, UserMatch, UniversityMatch
from database.database import get_db, engine
from api.schemas import (
    UserCreate, UserLogin, UserProfile, UserUpdate,
    UniversityResponse, SchoolResponse, ProgramResponse,
    MatchResponse, QuestionnaireResponse, PersonalityProfile
)
from api.auth import get_current_user, create_access_token
from api.matching import MatchingService
from api.questionnaire import QuestionnaireService
from api.school_scraper import SchoolScraperService

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="University Matching App",
    description="An AI-powered app that matches students with universities and programs",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

@app.get("/")
async def root():
    return {"message": "University Matching API"}

# Authentication endpoints
@app.post("/auth/register", response_model=dict)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """Register a new user"""
    # Check if user already exists
    existing_user = db.query(User).filter(
        (User.email == user_data.email) | (User.username == user_data.username)
    ).first()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email or username already exists"
        )
    
    # Hash password
    password_hash = bcrypt.hashpw(user_data.password.encode('utf-8'), bcrypt.gensalt())
    
    # Create user
    user = User(
        username=user_data.username,
        email=user_data.email,
        password_hash=password_hash.decode('utf-8'),
        name=user_data.name
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # Create access token
    access_token = create_access_token(data={"sub": user.email})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user.to_dict()
    }

@app.post("/auth/login", response_model=dict)
async def login(user_data: UserLogin, db: Session = Depends(get_db)):
    """Login user"""
    user = db.query(User).filter(User.email == user_data.email).first()
    
    if not user or not bcrypt.checkpw(user_data.password.encode('utf-8'), user.password_hash.encode('utf-8')):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    access_token = create_access_token(data={"sub": user.email})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user.to_dict()
    }

# User profile endpoints
@app.get("/profile", response_model=UserProfile)
async def get_profile(current_user: User = Depends(get_current_user)):
    """Get current user's profile"""
    return current_user.to_dict()

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
    
    return current_user.to_dict()

# Questionnaire endpoints
@app.post("/questionnaire/submit", response_model=PersonalityProfile)
async def submit_questionnaire(
    questionnaire_data: QuestionnaireResponse,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Submit questionnaire and generate personality profile"""
    questionnaire_service = QuestionnaireService()
    
    # Save questionnaire answers
    current_user.questionnaire_answers = questionnaire_data.answers
    current_user.preferred_majors = questionnaire_data.preferred_majors
    current_user.preferred_locations = questionnaire_data.preferred_locations
    
    # Generate personality profile using LLM
    personality_profile = await questionnaire_service.generate_personality_profile(
        questionnaire_data.answers,
        questionnaire_data.preferred_majors
    )
    
    current_user.personality_profile = personality_profile
    
    db.commit()
    db.refresh(current_user)
    
    return personality_profile

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
        query = query.join(Program).filter(Program.field == field)
    
    universities = query.offset(skip).limit(limit).all()
    return [university.to_dict() for university in universities]

@app.get("/universities/{university_id}", response_model=UniversityResponse)
async def get_university(university_id: int, db: Session = Depends(get_db)):
    """Get specific university"""
    university = db.query(University).filter(University.id == university_id).first()
    
    if not university:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="University not found"
        )
    
    return university.to_dict()

# School endpoints
@app.get("/schools", response_model=List[SchoolResponse])
async def get_schools(
    skip: int = 0,
    limit: int = 100,
    country: Optional[str] = None,
    state: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get schools with optional filtering"""
    query = db.query(School)
    
    if country:
        query = query.filter(School.country == country)
    
    if state:
        query = query.filter(School.state == state)
    
    schools = query.offset(skip).limit(limit).all()
    return [school.to_dict() for school in schools]

@app.post("/schools/scrape")
async def scrape_school_data(
    school_name: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Scrape school data using browser automation"""
    scraper_service = SchoolScraperService()
    
    try:
        school_data = await scraper_service.scrape_school(school_name)
        
        # Save to database
        school = School(**school_data)
        db.add(school)
        db.commit()
        db.refresh(school)
        
        return {"message": "School data scraped successfully", "school": school.to_dict()}
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to scrape school data: {str(e)}"
        )

# Matching endpoints
@app.post("/matches/generate")
async def generate_matches(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate matches for current user"""
    if not current_user.personality_profile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please complete the questionnaire first"
        )
    
    matching_service = MatchingService()
    
    try:
        matches = await matching_service.generate_matches(current_user, db)
        
        # Save matches to database
        for match_data in matches:
            match = UserMatch(
                user_id=current_user.id,
                university_id=match_data["university_id"],
                program_id=match_data.get("program_id"),
                overall_score=match_data["overall_score"],
                academic_fit_score=match_data.get("academic_fit_score"),
                financial_fit_score=match_data.get("financial_fit_score"),
                location_fit_score=match_data.get("location_fit_score"),
                personality_fit_score=match_data.get("personality_fit_score"),
                user_preferences=match_data.get("user_preferences")
            )
            db.add(match)
        
        db.commit()
        
        return {"message": f"Generated {len(matches)} matches", "matches": matches}
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate matches: {str(e)}"
        )

@app.get("/matches", response_model=List[MatchResponse])
async def get_user_matches(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's matches"""
    matches = db.query(UserMatch).filter(UserMatch.user_id == current_user.id).all()
    return [match.to_dict() for match in matches]

@app.put("/matches/{match_id}/favorite")
async def toggle_favorite(
    match_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Toggle favorite status for a match"""
    match = db.query(UserMatch).filter(
        UserMatch.id == match_id,
        UserMatch.user_id == current_user.id
    ).first()
    
    if not match:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Match not found"
        )
    
    match.is_favorite = not match.is_favorite
    db.commit()
    
    return {"message": "Favorite status updated", "is_favorite": match.is_favorite}

@app.put("/matches/{match_id}/notes")
async def update_match_notes(
    match_id: int,
    notes: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update notes for a match"""
    match = db.query(UserMatch).filter(
        UserMatch.id == match_id,
        UserMatch.user_id == current_user.id
    ).first()
    
    if not match:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Match not found"
        )
    
    match.notes = notes
    db.commit()
    
    return {"message": "Notes updated successfully"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 