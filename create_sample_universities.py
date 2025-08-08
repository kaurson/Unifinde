#!/usr/bin/env python3
"""
Script to create sample universities in the database for testing the enhanced matching system.
"""

import sys
import os
from datetime import datetime

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.database import get_db
from app.models import University, Program, Facility

def create_sample_universities():
    """Create sample universities with programs and facilities"""
    
    print("🏫 Creating Sample Universities for Testing")
    print("=" * 50)
    
    # Get database session
    db = next(get_db())
    
    try:
        # Check if universities already exist
        existing_count = db.query(University).count()
        if existing_count > 0:
            print(f"✅ Found {existing_count} existing universities in database")
            return
        
        # Sample universities data
        universities_data = [
            {
                "name": "Stanford University",
                "website": "https://www.stanford.edu",
                "country": "United States",
                "city": "Stanford",
                "state": "California",
                "founded_year": 1885,
                "type": "Private",
                "student_population": 17000,
                "faculty_count": 2200,
                "acceptance_rate": 0.04,
                "tuition_domestic": 56000,
                "tuition_international": 56000,
                "world_ranking": 2,
                "national_ranking": 3,
                "description": "Stanford University is a private research university known for its academic achievements, wealth, and close proximity to Silicon Valley.",
                "mission_statement": "To promote the public welfare by exercising an influence in behalf of humanity and civilization.",
                "programs": [
                    {"name": "Computer Science", "level": "Bachelor", "field": "Computer Science", "duration": "4 years", "tuition": 56000},
                    {"name": "Electrical Engineering", "level": "Bachelor", "field": "Engineering", "duration": "4 years", "tuition": 56000},
                    {"name": "Business Administration", "level": "Bachelor", "field": "Business", "duration": "4 years", "tuition": 56000}
                ],
                "facilities": [
                    {"name": "Stanford Research Park", "type": "Research", "description": "Technology research and development center"},
                    {"name": "Stanford Stadium", "type": "Sports", "capacity": 50000},
                    {"name": "Green Library", "type": "Library", "description": "Main university library"}
                ]
            },
            {
                "name": "Massachusetts Institute of Technology",
                "website": "https://www.mit.edu",
                "country": "United States",
                "city": "Cambridge",
                "state": "Massachusetts",
                "founded_year": 1861,
                "type": "Private",
                "student_population": 11500,
                "faculty_count": 1000,
                "acceptance_rate": 0.07,
                "tuition_domestic": 55000,
                "tuition_international": 55000,
                "world_ranking": 1,
                "national_ranking": 2,
                "description": "MIT is a private research university known for its research and education in physical sciences and engineering.",
                "mission_statement": "To advance knowledge and educate students in science, technology, and other areas of scholarship.",
                "programs": [
                    {"name": "Computer Science and Engineering", "level": "Bachelor", "field": "Computer Science", "duration": "4 years", "tuition": 55000},
                    {"name": "Mechanical Engineering", "level": "Bachelor", "field": "Engineering", "duration": "4 years", "tuition": 55000},
                    {"name": "Physics", "level": "Bachelor", "field": "Physics", "duration": "4 years", "tuition": 55000}
                ],
                "facilities": [
                    {"name": "MIT Media Lab", "type": "Research", "description": "Interdisciplinary research laboratory"},
                    {"name": "Kresge Auditorium", "type": "Performance", "capacity": 1226},
                    {"name": "Barker Engineering Library", "type": "Library", "description": "Engineering and science library"}
                ]
            },
            {
                "name": "University of California, Berkeley",
                "website": "https://www.berkeley.edu",
                "country": "United States",
                "city": "Berkeley",
                "state": "California",
                "founded_year": 1868,
                "type": "Public",
                "student_population": 42000,
                "faculty_count": 1500,
                "acceptance_rate": 0.15,
                "tuition_domestic": 14000,
                "tuition_international": 44000,
                "world_ranking": 13,
                "national_ranking": 22,
                "description": "UC Berkeley is a public research university and a founding member of the University of California system.",
                "mission_statement": "To serve society as a center of higher learning, providing long-term societal benefits through transmitting advanced knowledge.",
                "programs": [
                    {"name": "Computer Science", "level": "Bachelor", "field": "Computer Science", "duration": "4 years", "tuition": 14000},
                    {"name": "Data Science", "level": "Bachelor", "field": "Data Science", "duration": "4 years", "tuition": 14000},
                    {"name": "Business Administration", "level": "Bachelor", "field": "Business", "duration": "4 years", "tuition": 14000}
                ],
                "facilities": [
                    {"name": "Sather Tower", "type": "Landmark", "description": "Iconic clock tower"},
                    {"name": "Memorial Stadium", "type": "Sports", "capacity": 63000},
                    {"name": "Doe Memorial Library", "type": "Library", "description": "Main library complex"}
                ]
            },
            {
                "name": "Harvard University",
                "website": "https://www.harvard.edu",
                "country": "United States",
                "city": "Cambridge",
                "state": "Massachusetts",
                "founded_year": 1636,
                "type": "Private",
                "student_population": 31000,
                "faculty_count": 2400,
                "acceptance_rate": 0.05,
                "tuition_domestic": 54000,
                "tuition_international": 54000,
                "world_ranking": 3,
                "national_ranking": 1,
                "description": "Harvard University is a private Ivy League research university and one of the most prestigious universities in the world.",
                "mission_statement": "To educate the citizens and citizen-leaders for our society through the transformative power of a liberal arts and sciences education.",
                "programs": [
                    {"name": "Computer Science", "level": "Bachelor", "field": "Computer Science", "duration": "4 years", "tuition": 54000},
                    {"name": "Economics", "level": "Bachelor", "field": "Economics", "duration": "4 years", "tuition": 54000},
                    {"name": "Psychology", "level": "Bachelor", "field": "Psychology", "duration": "4 years", "tuition": 54000}
                ],
                "facilities": [
                    {"name": "Widener Library", "type": "Library", "description": "Main library with over 3 million volumes"},
                    {"name": "Harvard Stadium", "type": "Sports", "capacity": 30323},
                    {"name": "Harvard Art Museums", "type": "Cultural", "description": "Art museum complex"}
                ]
            },
            {
                "name": "University of Michigan",
                "website": "https://www.umich.edu",
                "country": "United States",
                "city": "Ann Arbor",
                "state": "Michigan",
                "founded_year": 1817,
                "type": "Public",
                "student_population": 45000,
                "faculty_count": 6500,
                "acceptance_rate": 0.23,
                "tuition_domestic": 16000,
                "tuition_international": 52000,
                "world_ranking": 23,
                "national_ranking": 23,
                "description": "The University of Michigan is a public research university and a founding member of the Association of American Universities.",
                "mission_statement": "To serve the people of Michigan and the world through preeminence in creating, communicating, preserving and applying knowledge.",
                "programs": [
                    {"name": "Computer Science and Engineering", "level": "Bachelor", "field": "Computer Science", "duration": "4 years", "tuition": 16000},
                    {"name": "Mechanical Engineering", "level": "Bachelor", "field": "Engineering", "duration": "4 years", "tuition": 16000},
                    {"name": "Business Administration", "level": "Bachelor", "field": "Business", "duration": "4 years", "tuition": 16000}
                ],
                "facilities": [
                    {"name": "Michigan Stadium", "type": "Sports", "capacity": 107601},
                    {"name": "Hatcher Graduate Library", "type": "Library", "description": "Graduate library"},
                    {"name": "Michigan Union", "type": "Student Center", "description": "Student union building"}
                ]
            },
            {
                "name": "New York University",
                "website": "https://www.nyu.edu",
                "country": "United States",
                "city": "New York",
                "state": "New York",
                "founded_year": 1831,
                "type": "Private",
                "student_population": 52000,
                "faculty_count": 3000,
                "acceptance_rate": 0.16,
                "tuition_domestic": 56000,
                "tuition_international": 56000,
                "world_ranking": 42,
                "national_ranking": 30,
                "description": "NYU is a private research university with its main campus in New York City and campuses around the world.",
                "mission_statement": "To be a top quality international center of scholarship, teaching and research.",
                "programs": [
                    {"name": "Computer Science", "level": "Bachelor", "field": "Computer Science", "duration": "4 years", "tuition": 56000},
                    {"name": "Film and Television", "level": "Bachelor", "field": "Film", "duration": "4 years", "tuition": 56000},
                    {"name": "Business Administration", "level": "Bachelor", "field": "Business", "duration": "4 years", "tuition": 56000}
                ],
                "facilities": [
                    {"name": "Bobst Library", "type": "Library", "description": "Main university library"},
                    {"name": "Skirball Center", "type": "Performance", "capacity": 860},
                    {"name": "Kimmel Center", "type": "Student Center", "description": "Student center and dining"}
                ]
            },
            {
                "name": "University of Texas at Austin",
                "website": "https://www.utexas.edu",
                "country": "United States",
                "city": "Austin",
                "state": "Texas",
                "founded_year": 1883,
                "type": "Public",
                "student_population": 51000,
                "faculty_count": 3000,
                "acceptance_rate": 0.32,
                "tuition_domestic": 11000,
                "tuition_international": 40000,
                "world_ranking": 44,
                "national_ranking": 38,
                "description": "UT Austin is a public research university and the flagship institution of the University of Texas System.",
                "mission_statement": "To achieve excellence in the interrelated areas of undergraduate education, graduate education, research and public service.",
                "programs": [
                    {"name": "Computer Science", "level": "Bachelor", "field": "Computer Science", "duration": "4 years", "tuition": 11000},
                    {"name": "Petroleum Engineering", "level": "Bachelor", "field": "Engineering", "duration": "4 years", "tuition": 11000},
                    {"name": "Business Administration", "level": "Bachelor", "field": "Business", "duration": "4 years", "tuition": 11000}
                ],
                "facilities": [
                    {"name": "Darrell K Royal Stadium", "type": "Sports", "capacity": 100119},
                    {"name": "Perry-Castañeda Library", "type": "Library", "description": "Main university library"},
                    {"name": "Blanton Museum of Art", "type": "Cultural", "description": "Art museum"}
                ]
            },
            {
                "name": "University of Washington",
                "website": "https://www.washington.edu",
                "country": "United States",
                "city": "Seattle",
                "state": "Washington",
                "founded_year": 1861,
                "type": "Public",
                "student_population": 47000,
                "faculty_count": 4000,
                "acceptance_rate": 0.49,
                "tuition_domestic": 12000,
                "tuition_international": 39000,
                "world_ranking": 26,
                "national_ranking": 55,
                "description": "UW is a public research university and one of the oldest universities on the West Coast.",
                "mission_statement": "To preserve, advance, and disseminate knowledge.",
                "programs": [
                    {"name": "Computer Science and Engineering", "level": "Bachelor", "field": "Computer Science", "duration": "4 years", "tuition": 12000},
                    {"name": "Computer Engineering", "level": "Bachelor", "field": "Engineering", "duration": "4 years", "tuition": 12000},
                    {"name": "Informatics", "level": "Bachelor", "field": "Information Science", "duration": "4 years", "tuition": 12000}
                ],
                "facilities": [
                    {"name": "Husky Stadium", "type": "Sports", "capacity": 70083},
                    {"name": "Suzzallo Library", "type": "Library", "description": "Main library"},
                    {"name": "Henry Art Gallery", "type": "Cultural", "description": "Contemporary art museum"}
                ]
            },
            {
                "name": "Carnegie Mellon University",
                "website": "https://www.cmu.edu",
                "country": "United States",
                "city": "Pittsburgh",
                "state": "Pennsylvania",
                "founded_year": 1900,
                "type": "Private",
                "student_population": 15000,
                "faculty_count": 1400,
                "acceptance_rate": 0.15,
                "tuition_domestic": 58000,
                "tuition_international": 58000,
                "world_ranking": 28,
                "national_ranking": 22,
                "description": "CMU is a private research university known for its programs in computer science, engineering, and the arts.",
                "mission_statement": "To create a transformative educational experience for students focused on deep disciplinary knowledge.",
                "programs": [
                    {"name": "Computer Science", "level": "Bachelor", "field": "Computer Science", "duration": "4 years", "tuition": 58000},
                    {"name": "Robotics", "level": "Bachelor", "field": "Engineering", "duration": "4 years", "tuition": 58000},
                    {"name": "Drama", "level": "Bachelor", "field": "Arts", "duration": "4 years", "tuition": 58000}
                ],
                "facilities": [
                    {"name": "Hunt Library", "type": "Library", "description": "Main library"},
                    {"name": "Purnell Center", "type": "Performance", "capacity": 437},
                    {"name": "Robotics Institute", "type": "Research", "description": "Robotics research center"}
                ]
            },
            {
                "name": "University of Illinois at Urbana-Champaign",
                "website": "https://www.illinois.edu",
                "country": "United States",
                "city": "Champaign",
                "state": "Illinois",
                "founded_year": 1867,
                "type": "Public",
                "student_population": 52000,
                "faculty_count": 2500,
                "acceptance_rate": 0.59,
                "tuition_domestic": 15000,
                "tuition_international": 32000,
                "world_ranking": 85,
                "national_ranking": 47,
                "description": "UIUC is a public research university and the flagship campus of the University of Illinois system.",
                "mission_statement": "To enhance the lives of citizens in Illinois, across the nation and around the world through our leadership in learning.",
                "programs": [
                    {"name": "Computer Science", "level": "Bachelor", "field": "Computer Science", "duration": "4 years", "tuition": 15000},
                    {"name": "Electrical Engineering", "level": "Bachelor", "field": "Engineering", "duration": "4 years", "tuition": 15000},
                    {"name": "Agricultural Engineering", "level": "Bachelor", "field": "Engineering", "duration": "4 years", "tuition": 15000}
                ],
                "facilities": [
                    {"name": "Memorial Stadium", "type": "Sports", "capacity": 60670},
                    {"name": "Main Library", "type": "Library", "description": "Main university library"},
                    {"name": "Krannert Center", "type": "Performance", "capacity": 4000}
                ]
            }
        ]
        
        # Create universities
        created_universities = []
        for uni_data in universities_data:
            # Create university
            university = University(
                name=uni_data["name"],
                website=uni_data["website"],
                country=uni_data["country"],
                city=uni_data["city"],
                state=uni_data["state"],
                founded_year=uni_data["founded_year"],
                type=uni_data["type"],
                student_population=uni_data["student_population"],
                faculty_count=uni_data["faculty_count"],
                acceptance_rate=uni_data["acceptance_rate"],
                tuition_domestic=uni_data["tuition_domestic"],
                tuition_international=uni_data["tuition_international"],
                world_ranking=uni_data["world_ranking"],
                national_ranking=uni_data["national_ranking"],
                description=uni_data["description"],
                mission_statement=uni_data["mission_statement"],
                confidence_score=0.9
            )
            
            db.add(university)
            db.commit()
            db.refresh(university)
            
            # Create programs
            for prog_data in uni_data["programs"]:
                program = Program(
                    university_id=university.id,
                    name=prog_data["name"],
                    level=prog_data["level"],
                    field=prog_data["field"],
                    duration=prog_data["duration"],
                    tuition=prog_data["tuition"],
                    description=f"{prog_data['name']} program at {university.name}"
                )
                db.add(program)
            
            # Create facilities
            for fac_data in uni_data["facilities"]:
                facility = Facility(
                    university_id=university.id,
                    name=fac_data["name"],
                    type=fac_data["type"],
                    description=fac_data["description"],
                    capacity=fac_data.get("capacity")
                )
                db.add(facility)
            
            created_universities.append(university)
            print(f"✅ Created {university.name}")
        
        db.commit()
        
        # Print summary
        total_universities = len(created_universities)
        total_programs = sum(len(uni_data["programs"]) for uni_data in universities_data)
        total_facilities = sum(len(uni_data["facilities"]) for uni_data in universities_data)
        
        print(f"\n🎉 Successfully created {total_universities} universities with {total_programs} programs and {total_facilities} facilities")
        
        # Print university list
        print("\n📋 Created Universities:")
        for i, university in enumerate(created_universities, 1):
            print(f"   {i}. {university.name} ({university.city}, {university.state})")
        
        return created_universities
        
    except Exception as e:
        print(f"❌ Error creating universities: {e}")
        db.rollback()
        import traceback
        traceback.print_exc()
        return []
    
    finally:
        db.close()

def list_existing_universities():
    """List all existing universities in the database"""
    
    print("📋 Existing Universities in Database")
    print("=" * 40)
    
    # Get database session
    db = next(get_db())
    
    try:
        universities = db.query(University).all()
        
        if not universities:
            print("No universities found in database")
            return []
        
        print(f"Found {len(universities)} universities:")
        print()
        
        for i, university in enumerate(universities, 1):
            print(f"{i}. {university.name}")
            print(f"   Location: {university.city}, {university.state}, {university.country}")
            print(f"   Type: {university.type}")
            print(f"   Students: {university.student_population:,}")
            print(f"   Acceptance Rate: {university.acceptance_rate:.1%}")
            print(f"   Tuition: ${university.tuition_domestic:,}")
            print(f"   National Ranking: #{university.national_ranking}")
            
            # Count programs
            program_count = len(university.programs)
            print(f"   Programs: {program_count}")
            
            # Count facilities
            facility_count = len(university.facilities)
            print(f"   Facilities: {facility_count}")
            print()
        
        return universities
        
    except Exception as e:
        print(f"❌ Error listing universities: {e}")
        return []
    
    finally:
        db.close()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Manage sample universities in the database")
    parser.add_argument("--list", action="store_true", help="List existing universities")
    parser.add_argument("--create", action="store_true", help="Create sample universities")
    
    args = parser.parse_args()
    
    if args.list:
        list_existing_universities()
    elif args.create:
        create_sample_universities()
    else:
        print("Please specify --list to see existing universities or --create to add sample universities")
        print("Example: python3 create_sample_universities.py --create") 