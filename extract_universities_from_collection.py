#!/usr/bin/env python3
"""
Script to extract universities from university_data_collection_results table 
and populate the universities table for the enhanced matching system.
"""

import sys
import os
from datetime import datetime

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.database import get_db
from database.models import UniversityDataCollectionResult
from app.models import University, Program, Facility

def extract_universities_from_collection():
    """Extract universities from university_data_collection_results and create University records"""
    
    print("🏫 Extracting Universities from Collection Results")
    print("=" * 55)
    
    # Get database session
    db = next(get_db())
    
    try:
        # Get all university data collection results
        collection_results = db.query(UniversityDataCollectionResult).all()
        
        if not collection_results:
            print("❌ No university data collection results found")
            return []
        
        print(f"📊 Found {len(collection_results)} university data collection results")
        
        # Check if universities table already has data
        existing_universities = db.query(University).count()
        if existing_universities > 0:
            print(f"✅ Universities table already has {existing_universities} universities")
            return db.query(University).all()
        
        # Extract and create universities
        created_universities = []
        successful_extractions = 0
        
        for result in collection_results:
            try:
                # Skip if no name
                if not result.name:
                    continue
                
                # Create university from collection result
                university = University(
                    name=result.name,
                    website=result.website,
                    country=result.country,
                    city=result.city,
                    state=result.state,
                    founded_year=result.founded_year,
                    type=result.type,
                    student_population=result.student_population,
                    faculty_count=result.faculty_count,
                    acceptance_rate=result.acceptance_rate,
                    tuition_domestic=result.tuition_domestic,
                    tuition_international=result.tuition_international,
                    world_ranking=result.world_ranking,
                    national_ranking=result.national_ranking,
                    description=result.description,
                    mission_statement=result.mission_statement,
                    confidence_score=result.confidence_score or 0.7
                )
                
                db.add(university)
                db.commit()
                db.refresh(university)
                
                # Create programs if available
                if result.programs:
                    try:
                        programs_data = result.programs
                        if isinstance(programs_data, list):
                            for prog in programs_data:
                                if isinstance(prog, dict) and prog.get('name'):
                                    program = Program(
                                        university_id=university.id,
                                        name=prog['name'],
                                        level=prog.get('level', 'Bachelor'),
                                        field=prog.get('field', 'General'),
                                        duration=prog.get('duration', '4 years'),
                                        tuition=prog.get('tuition'),
                                        description=prog.get('description', f"{prog['name']} program")
                                    )
                                    db.add(program)
                    except Exception as e:
                        print(f"⚠️  Warning: Could not create programs for {university.name}: {e}")
                
                # Create facilities if available
                if hasattr(result, 'facilities') and result.facilities:
                    try:
                        facilities_data = result.facilities
                        if isinstance(facilities_data, list):
                            for fac in facilities_data:
                                if isinstance(fac, dict) and fac.get('name'):
                                    facility = Facility(
                                        university_id=university.id,
                                        name=fac['name'],
                                        type=fac.get('type', 'General'),
                                        description=fac.get('description', f"{fac['name']} facility"),
                                        capacity=fac.get('capacity')
                                    )
                                    db.add(facility)
                    except Exception as e:
                        print(f"⚠️  Warning: Could not create facilities for {university.name}: {e}")
                
                created_universities.append(university)
                successful_extractions += 1
                
                print(f"✅ Created {university.name} ({university.city}, {university.state})")
                
            except Exception as e:
                print(f"❌ Error creating university from {result.name}: {e}")
                db.rollback()
                continue
        
        db.commit()
        
        print(f"\n🎉 Successfully extracted {successful_extractions} universities from collection results")
        print(f"📋 Total universities in database: {len(created_universities)}")
        
        return created_universities
        
    except Exception as e:
        print(f"❌ Error extracting universities: {e}")
        db.rollback()
        import traceback
        traceback.print_exc()
        return []
    
    finally:
        db.close()

def list_collection_results():
    """List all university data collection results"""
    
    print("📋 University Data Collection Results")
    print("=" * 40)
    
    # Get database session
    db = next(get_db())
    
    try:
        results = db.query(UniversityDataCollectionResult).all()
        
        if not results:
            print("No university data collection results found")
            return []
        
        print(f"Found {len(results)} collection results:")
        print()
        
        for i, result in enumerate(results, 1):
            print(f"{i}. {result.name or 'Unnamed University'}")
            print(f"   Location: {result.city or 'N/A'}, {result.state or 'N/A'}, {result.country or 'N/A'}")
            print(f"   Type: {result.type or 'N/A'}")
            print(f"   Students: {result.student_population or 'N/A'}")
            print(f"   Acceptance Rate: {result.acceptance_rate:.1%}" if result.acceptance_rate else "   Acceptance Rate: N/A")
            print(f"   Tuition: ${result.tuition_domestic:,}" if result.tuition_domestic else "   Tuition: N/A")
            print(f"   National Ranking: #{result.national_ranking}" if result.national_ranking else "   National Ranking: N/A")
            print(f"   Confidence: {result.confidence_score:.2f}" if result.confidence_score else "   Confidence: N/A")
            print(f"   Success: {result.success}")
            print()
        
        return results
        
    except Exception as e:
        print(f"❌ Error listing collection results: {e}")
        return []
    
    finally:
        db.close()

def test_matching_with_extracted_universities():
    """Test the enhanced matching system with extracted universities"""
    
    print("🧪 Testing Enhanced Matching with Extracted Universities")
    print("=" * 60)
    
    # First extract universities
    universities = extract_universities_from_collection()
    
    if not universities:
        print("❌ No universities available for testing")
        return
    
    print(f"✅ Using {len(universities)} universities for testing")
    
    # Now run the enhanced matching test
    try:
        from test_enhanced_matching import test_enhanced_matching
        import asyncio
        
        print("\n🚀 Running Enhanced Matching Tests...")
        asyncio.run(test_enhanced_matching())
        
    except Exception as e:
        print(f"❌ Error running matching tests: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Extract universities from collection results")
    parser.add_argument("--list", action="store_true", help="List university data collection results")
    parser.add_argument("--extract", action="store_true", help="Extract universities from collection results")
    parser.add_argument("--test", action="store_true", help="Test matching with extracted universities")
    
    args = parser.parse_args()
    
    if args.list:
        list_collection_results()
    elif args.extract:
        extract_universities_from_collection()
    elif args.test:
        test_matching_with_extracted_universities()
    else:
        print("Please specify an option:")
        print("  --list    : List university data collection results")
        print("  --extract : Extract universities from collection results")
        print("  --test    : Test matching with extracted universities")
        print("\nExample: python3 extract_universities_from_collection.py --extract") 