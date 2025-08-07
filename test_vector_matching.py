#!/usr/bin/env python3
"""
Test script for the vector-based matching system
"""

import asyncio
import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from api.vector_matcher import VectorMatchingService
from api.matching import MatchingService
from database.database import get_db
from database.models import User, StudentProfile
from app.models import University as AppUniversity, Program
from sqlalchemy.orm import Session

async def test_vector_matching():
    """Test the vector matching system"""
    
    print("🧪 Testing Vector-Based Matching System")
    print("=" * 50)
    
    # Get database session
    db = next(get_db())
    
    try:
        # Create a test user with comprehensive profile
        test_user = create_test_user(db)
        
        # Create some test universities
        test_universities = create_test_universities(db)
        
        print(f"✅ Created test user: {test_user.name}")
        print(f"✅ Created {len(test_universities)} test universities")
        
        # Test vector matching
        print("\n🔍 Testing Vector Matching...")
        vector_matcher = VectorMatchingService()
        
        matches = await vector_matcher.find_matches(test_user, db, limit=5)
        
        print(f"\n📊 Vector Matching Results (Top 5):")
        for i, match in enumerate(matches, 1):
            print(f"\n{i}. {match['university_name']}")
            print(f"   Similarity Score: {match['similarity_score']:.3f}")
            print(f"   Match Reasons: {', '.join(match['match_reasons'][:3])}")
        
        # Test traditional matching for comparison
        print("\n🔍 Testing Traditional Matching...")
        matching_service = MatchingService()
        
        traditional_matches = await matching_service.generate_matches(
            test_user, db, use_vector_matching=False, limit=5
        )
        
        print(f"\n📊 Traditional Matching Results (Top 5):")
        for i, match in enumerate(traditional_matches, 1):
            print(f"\n{i}. {match['university_name']}")
            print(f"   Overall Score: {match['overall_score']:.3f}")
            print(f"   Academic Fit: {match['academic_fit_score']:.3f}")
            print(f"   Financial Fit: {match['financial_fit_score']:.3f}")
            print(f"   Location Fit: {match['location_fit_score']:.3f}")
            print(f"   Personality Fit: {match['personality_fit_score']:.3f}")
        
        # Test comparison
        print("\n🔍 Comparing Matching Methods...")
        comparison = await matching_service.compare_matching_methods(test_user, db, limit=5)
        
        print(f"\n📊 Comparison Results:")
        print(f"   Common Universities: {comparison['common_universities']}")
        print(f"   Vector Only: {comparison['vector_only']}")
        print(f"   Traditional Only: {comparison['traditional_only']}")
        print(f"   Overlap Percentage: {comparison['overlap_percentage']:.1f}%")
        
        # Test similar users
        print("\n🔍 Testing Similar Users...")
        similar_users = await vector_matcher.get_similar_users(test_user, db, limit=3)
        
        print(f"\n📊 Similar Users Found: {len(similar_users)}")
        for i, user in enumerate(similar_users, 1):
            print(f"\n{i}. {user['name']} (@{user['username']})")
            print(f"   Similarity Score: {user['similarity_score']:.3f}")
            print(f"   Common Interests: {', '.join(user['common_interests'][:2])}")
        
        print("\n✅ All tests completed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        db.close()

def create_test_user(db: Session) -> User:
    """Create a test user with comprehensive profile"""
    
    # Check if test user already exists
    existing_user = db.query(User).filter(User.email == "test@example.com").first()
    if existing_user:
        return existing_user
    
    # Create user
    user = User(
        username="teststudent",
        email="test@example.com",
        password_hash="dummy_hash",
        name="Test Student",
        age=18,
        income=75000,
        preferred_majors=["Computer Science", "Engineering"],
        preferred_locations=["California", "New York"],
        min_acceptance_rate=0.3,
        max_tuition=50000,
        preferred_university_type="Private",
        personality_profile={
            "learning_style": "visual",
            "work_environment_preferences": {
                "collaboration": "high",
                "structure": "medium"
            },
            "communication_style": "direct",
            "leadership_style": "democratic"
        },
        questionnaire_answers={
            "q1": "I prefer hands-on learning",
            "q2": "I work well in teams",
            "q3": "I want to work in technology",
            "q4": "I prefer smaller class sizes",
            "q5": "I value research opportunities"
        }
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # Create student profile
    student_profile = StudentProfile(
        user_id=user.id,
        current_school="Test High School",
        graduation_year=2024,
        gpa=3.8,
        sat_total=1400,
        act_composite=30,
        academic_awards=["National Merit Scholar", "AP Scholar"],
        research_experience=["Science Fair Winner", "Summer Research Program"],
        leadership_positions=["Student Council President", "Robotics Team Captain"],
        sports_activities=["Varsity Soccer", "Track and Field"],
        artistic_activities=["School Band", "Art Club"],
        preferred_class_size="Small",
        preferred_teaching_style=["Discussion", "Hands-on"],
        preferred_campus_environment=["Urban", "Suburban"],
        career_aspirations="Software Engineer at a tech company",
        industry_preferences=["Technology", "Finance"],
        salary_expectations=80000
    )
    
    db.add(student_profile)
    db.commit()
    
    return user

def create_test_universities(db: Session) -> list:
    """Create test universities"""
    
    universities_data = [
        {
            "name": "Stanford University",
            "type": "Private",
            "city": "Stanford",
            "state": "California",
            "country": "USA",
            "student_population": 17000,
            "acceptance_rate": 0.04,
            "tuition_domestic": 56000,
            "national_ranking": 2,
            "description": "Stanford University is a private research university known for its strong programs in computer science, engineering, and entrepreneurship.",
            "mission_statement": "To promote the public welfare by exercising an influence in behalf of humanity and civilization."
        },
        {
            "name": "MIT",
            "type": "Private",
            "city": "Cambridge",
            "state": "Massachusetts",
            "country": "USA",
            "student_population": 11500,
            "acceptance_rate": 0.07,
            "tuition_domestic": 55000,
            "national_ranking": 1,
            "description": "MIT is a world-renowned private research university specializing in science, technology, engineering, and mathematics.",
            "mission_statement": "To advance knowledge and educate students in science, technology, and other areas of scholarship."
        },
        {
            "name": "UC Berkeley",
            "type": "Public",
            "city": "Berkeley",
            "state": "California",
            "country": "USA",
            "student_population": 42000,
            "acceptance_rate": 0.15,
            "tuition_domestic": 44000,
            "national_ranking": 22,
            "description": "UC Berkeley is a top-ranked public research university with excellent programs in computer science and engineering.",
            "mission_statement": "To serve society as a center of higher learning."
        },
        {
            "name": "New York University",
            "type": "Private",
            "city": "New York",
            "state": "New York",
            "country": "USA",
            "student_population": 52000,
            "acceptance_rate": 0.16,
            "tuition_domestic": 54000,
            "national_ranking": 30,
            "description": "NYU is a private research university located in the heart of New York City with strong programs in business and arts.",
            "mission_statement": "To be a top quality international center of scholarship, teaching and research."
        },
        {
            "name": "University of Texas at Austin",
            "type": "Public",
            "city": "Austin",
            "state": "Texas",
            "country": "USA",
            "student_population": 51000,
            "acceptance_rate": 0.32,
            "tuition_domestic": 38000,
            "national_ranking": 42,
            "description": "UT Austin is a large public research university with excellent computer science and engineering programs.",
            "mission_statement": "To transform lives for the benefit of society."
        }
    ]
    
    universities = []
    
    for uni_data in universities_data:
        # Check if university already exists
        existing = db.query(AppUniversity).filter(AppUniversity.name == uni_data["name"]).first()
        if existing:
            universities.append(existing)
            continue
        
        # Create university
        university = AppUniversity(**uni_data)
        db.add(university)
        db.commit()
        db.refresh(university)
        
        # Add some programs
        programs_data = [
            {
                "name": "Computer Science",
                "level": "Bachelor",
                "field": "Computer Science",
                "duration": "4 years",
                "tuition": uni_data["tuition_domestic"],
                "description": "Comprehensive computer science program"
            },
            {
                "name": "Electrical Engineering",
                "level": "Bachelor",
                "field": "Engineering",
                "duration": "4 years",
                "tuition": uni_data["tuition_domestic"],
                "description": "Electrical engineering program"
            }
        ]
        
        for prog_data in programs_data:
            program = Program(
                university_id=university.id,
                **prog_data
            )
            db.add(program)
        
        db.commit()
        universities.append(university)
    
    return universities

if __name__ == "__main__":
    asyncio.run(test_vector_matching()) 