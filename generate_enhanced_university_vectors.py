#!/usr/bin/env python3
"""
Enhanced script to generate comprehensive university vectors
Uses structured text representations and specialized embeddings for better matching
"""

import sys
import os
import asyncio
from datetime import datetime
import json
import numpy as np

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.database import get_db
from app.models import University, Program, Facility
from database.models import UniversityVector
from api.enhanced_university_vectorizer import EnhancedUniversityVectorizer

async def generate_enhanced_university_vectors():
    """Generate enhanced embeddings for all universities"""
    
    print("🧠 Generating Enhanced University Vectors")
    print("=" * 50)
    
    # Initialize vectorizer
    vectorizer = EnhancedUniversityVectorizer()
    
    # Get database session
    db = next(get_db())
    
    try:
        # Get all universities with their programs and facilities
        universities = db.query(University).all()
        
        total_universities = len(universities)
        print(f"Found {total_universities} universities to process")
        
        success_count = 0
        error_count = 0
        
        for i, university in enumerate(universities, 1):
            print(f"\n[{i}/{total_universities}] Processing: {university.name}")
            
            try:
                # Get related programs and facilities
                programs = db.query(Program).filter(Program.university_id == university.id).all()
                facilities = db.query(Facility).filter(Facility.university_id == university.id).all()
                
                print(f"  - Found {len(programs)} programs and {len(facilities)} facilities")
                
                # Generate enhanced embeddings
                embedding_data = await vectorizer.generate_university_embedding(
                    university, programs, facilities
                )
                
                # Check if vector already exists
                existing_vector = db.query(UniversityVector).filter(
                    UniversityVector.university_id == university.id
                ).first()
                
                if existing_vector:
                    # Update existing vector
                    existing_vector.set_embedding_array(np.array(embedding_data['main_embedding']))
                    existing_vector.embedding_model = embedding_data['embedding_model']
                    existing_vector.source_text = embedding_data['main_text']
                    existing_vector.updated_at = datetime.now()
                    print(f"  ✅ Updated existing vector")
                else:
                    # Create new vector
                    new_vector = UniversityVector(
                        university_id=university.id,
                        embedding_model=embedding_data['embedding_model'],
                        source_text=embedding_data['main_text']
                    )
                    new_vector.set_embedding_array(np.array(embedding_data['main_embedding']))
                    db.add(new_vector)
                    print(f"  ✅ Created new vector")
                
                # Store specialized embeddings as JSON in a separate field or table
                # For now, we'll store them as part of the source_text metadata
                specialized_data = {
                    'specialized_embeddings': embedding_data['specialized_embeddings'],
                    'specialized_texts': embedding_data['specialized_texts'],
                    'matching_profile': vectorizer.create_matching_profile(university, programs, facilities)
                }
                
                # You could create a separate table for specialized embeddings
                # For now, we'll store the main embedding and keep specialized data in memory
                
                success_count += 1
                
            except Exception as e:
                print(f"  ❌ Error processing {university.name}: {str(e)}")
                error_count += 1
                continue
        
        # Commit all changes
        db.commit()
        
        print(f"\n🎉 Vector Generation Complete!")
        print(f"✅ Successfully processed: {success_count} universities")
        print(f"❌ Errors: {error_count} universities")
        print(f"📊 Success rate: {(success_count/total_universities)*100:.1f}%")
        
    except Exception as e:
        print(f"❌ Database error: {str(e)}")
        db.rollback()
    finally:
        db.close()

async def test_enhanced_matching():
    """Test the enhanced matching system"""
    
    print("\n🧪 Testing Enhanced Matching System")
    print("=" * 40)
    
    vectorizer = EnhancedUniversityVectorizer()
    db = next(get_db())
    
    try:
        # Get a sample university
        university = db.query(University).first()
        if not university:
            print("❌ No universities found in database")
            return
        
        programs = db.query(Program).filter(Program.university_id == university.id).all()
        facilities = db.query(Facility).filter(Facility.university_id == university.id).all()
        
        print(f"Testing with: {university.name}")
        
        # Generate embeddings
        embedding_data = await vectorizer.generate_university_embedding(
            university, programs, facilities
        )
        
        print(f"✅ Generated main embedding: {len(embedding_data['main_embedding'])} dimensions")
        print(f"✅ Generated specialized embeddings: {list(embedding_data['specialized_embeddings'].keys())}")
        
        # Test text generation
        main_text = vectorizer.create_structured_university_text(university, programs, facilities)
        print(f"📝 Main text length: {len(main_text)} characters")
        
        # Show a preview of the text
        print(f"📄 Text preview: {main_text[:200]}...")
        
        # Test matching profile
        profile = vectorizer.create_matching_profile(university, programs, facilities)
        print(f"📊 Profile created with {len(profile['academic_profile']['programs'])} programs")
        
    except Exception as e:
        print(f"❌ Test error: {str(e)}")
    finally:
        db.close()

async def list_enhanced_vectors():
    """List all enhanced university vectors"""
    
    print("\n📋 Enhanced University Vectors")
    print("=" * 30)
    
    db = next(get_db())
    
    try:
        vectors = db.query(UniversityVector).all()
        
        if not vectors:
            print("No vectors found")
            return
        
        print(f"Found {len(vectors)} university vectors:")
        
        for vector in vectors:
            university = db.query(University).filter(University.id == vector.university_id).first()
            university_name = university.name if university else "Unknown"
            
            embedding_array = vector.get_embedding_array()
            print(f"  - {university_name}")
            print(f"    Dimensions: {vector.embedding_dimension}")
            print(f"    Model: {vector.embedding_model}")
            print(f"    Created: {vector.created_at}")
            print(f"    Updated: {vector.updated_at}")
            print()
            
    except Exception as e:
        print(f"❌ Error listing vectors: {str(e)}")
    finally:
        db.close()

async def clear_enhanced_vectors():
    """Clear all enhanced university vectors"""
    
    print("\n🗑️ Clearing Enhanced University Vectors")
    print("=" * 35)
    
    db = next(get_db())
    
    try:
        count = db.query(UniversityVector).count()
        print(f"Found {count} vectors to delete")
        
        if count > 0:
            db.query(UniversityVector).delete()
            db.commit()
            print(f"✅ Deleted {count} vectors")
        else:
            print("No vectors to delete")
            
    except Exception as e:
        print(f"❌ Error clearing vectors: {str(e)}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Enhanced University Vector Generator")
    parser.add_argument("--action", choices=["generate", "test", "list", "clear"], 
                       default="generate", help="Action to perform")
    
    args = parser.parse_args()
    
    if args.action == "generate":
        asyncio.run(generate_enhanced_university_vectors())
    elif args.action == "test":
        asyncio.run(test_enhanced_matching())
    elif args.action == "list":
        asyncio.run(list_enhanced_vectors())
    elif args.action == "clear":
        asyncio.run(clear_enhanced_vectors()) 