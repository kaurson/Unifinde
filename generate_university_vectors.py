#!/usr/bin/env python3
"""
Script to generate embeddings for all universities in the database 
and store them in the university_vectors table for vector-based matching.
"""

import sys
import os
import asyncio
from datetime import datetime
import json

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.database import get_db
from app.models import University, Program, Facility
from database.models import UniversityVector
from api.vector_matcher import VectorMatchingService

def create_university_text(university, programs=None, facilities=None):
    """Create a comprehensive text representation of a university for embedding"""
    
    text_parts = []
    
    # Basic university information
    text_parts.append(f"University: {university.name}")
    
    if university.description:
        text_parts.append(f"Description: {university.description}")
    
    if university.mission_statement:
        text_parts.append(f"Mission: {university.mission_statement}")
    
    # Location and basic info
    location_parts = []
    if university.city:
        location_parts.append(university.city)
    if university.state:
        location_parts.append(university.state)
    if university.country:
        location_parts.append(university.country)
    
    if location_parts:
        text_parts.append(f"Location: {', '.join(location_parts)}")
    
    # Academic information
    if university.type:
        text_parts.append(f"Type: {university.type}")
    
    if university.founded_year:
        text_parts.append(f"Founded: {university.founded_year}")
    
    if university.student_population:
        text_parts.append(f"Student Population: {university.student_population:,}")
    
    if university.faculty_count:
        text_parts.append(f"Faculty Count: {university.faculty_count:,}")
    
    if university.acceptance_rate:
        text_parts.append(f"Acceptance Rate: {university.acceptance_rate:.1%}")
    
    if university.tuition_domestic:
        text_parts.append(f"Domestic Tuition: ${university.tuition_domestic:,}")
    
    if university.tuition_international:
        text_parts.append(f"International Tuition: ${university.tuition_international:,}")
    
    # Rankings
    if university.world_ranking:
        text_parts.append(f"World Ranking: #{university.world_ranking}")
    
    if university.national_ranking:
        text_parts.append(f"National Ranking: #{university.national_ranking}")
    
    # Programs
    if programs:
        program_names = [prog.name for prog in programs if prog.name]
        if program_names:
            text_parts.append(f"Programs: {', '.join(program_names[:10])}")  # Limit to first 10
    
    # Facilities
    if facilities:
        facility_names = [fac.name for fac in facilities if fac.name]
        if facility_names:
            text_parts.append(f"Facilities: {', '.join(facility_names[:10])}")  # Limit to first 10
    
    return " | ".join(text_parts)

async def generate_university_vectors():
    """Generate embeddings for all universities and store in university_vectors table"""
    
    print("🧠 Generating University Vectors")
    print("=" * 40)
    
    # Get database session
    db = next(get_db())
    
    try:
        # Get all universities
        universities = db.query(University).all()
        
        if not universities:
            print("❌ No universities found in database")
            return
        
        print(f"📊 Found {len(universities)} universities to process")
        
        # Initialize vector matcher
        vector_matcher = VectorMatchingService()
        
        # Check existing vectors
        existing_vectors = db.query(UniversityVector).count()
        print(f"📋 Existing vectors in database: {existing_vectors}")
        
        # Process universities
        successful_generations = 0
        skipped_count = 0
        error_count = 0
        
        for i, university in enumerate(universities, 1):
            try:
                print(f"\n[{i}/{len(universities)}] Processing: {university.name}")
                
                # Check if vector already exists
                existing_vector = db.query(UniversityVector).filter(
                    UniversityVector.university_id == university.id
                ).first()
                
                if existing_vector:
                    print(f"   ⏭️  Vector already exists, skipping...")
                    skipped_count += 1
                    continue
                
                # Get related programs and facilities
                programs = db.query(Program).filter(Program.university_id == university.id).all()
                facilities = db.query(Facility).filter(Facility.university_id == university.id).all()
                
                # Create university text for embedding
                university_text = create_university_text(university, programs, facilities)
                
                print(f"   📝 Text length: {len(university_text)} characters")
                
                # Generate embedding using the vector matcher's method
                print(f"   🧠 Generating embedding...")
                embedding = await vector_matcher.generate_university_embedding(university)
                
                if embedding is None:
                    print(f"   ❌ Failed to generate embedding")
                    error_count += 1
                    continue
                
                # Store vector in database
                university_vector = UniversityVector(
                    university_id=university.id,
                    embedding_model="text-embedding-3-small",
                    source_text=university_text,
                    created_at=datetime.now()
                )
                
                # Set the embedding using the model's method
                import numpy as np
                embedding_array = np.array(embedding, dtype=np.float32)
                university_vector.set_embedding_array(embedding_array)
                
                db.add(university_vector)
                db.commit()
                
                print(f"   ✅ Vector generated and stored ({len(embedding)} dimensions)")
                successful_generations += 1
                
            except Exception as e:
                print(f"   ❌ Error processing {university.name}: {e}")
                db.rollback()
                error_count += 1
                continue
        
        print(f"\n🎉 Vector Generation Complete!")
        print(f"   ✅ Successfully generated: {successful_generations}")
        print(f"   ⏭️  Skipped (already exists): {skipped_count}")
        print(f"   ❌ Errors: {error_count}")
        print(f"   📊 Total vectors in database: {db.query(UniversityVector).count()}")
        
    except Exception as e:
        print(f"❌ Error generating university vectors: {e}")
        db.rollback()
        import traceback
        traceback.print_exc()
    
    finally:
        db.close()

def list_university_vectors():
    """List all university vectors in the database"""
    
    print("📋 University Vectors in Database")
    print("=" * 35)
    
    # Get database session
    db = next(get_db())
    
    try:
        vectors = db.query(UniversityVector).all()
        
        if not vectors:
            print("No university vectors found in database")
            return
        
        print(f"Found {len(vectors)} university vectors:")
        print()
        
        for i, vector in enumerate(vectors, 1):
            # Get university name
            university = db.query(University).filter(University.id == vector.university_id).first()
            university_name = university.name if university else "Unknown University"
            
            print(f"{i}. {university_name}")
            print(f"   Vector ID: {vector.id}")
            print(f"   University ID: {vector.university_id}")
            print(f"   Embedding Model: {vector.embedding_model}")
            print(f"   Embedding Dimensions: {vector.embedding_dimension}")
            print(f"   Source Text Length: {len(vector.source_text)}")
            print(f"   Created: {vector.created_at}")
            print()
        
    except Exception as e:
        print(f"❌ Error listing university vectors: {e}")
    
    finally:
        db.close()

def clear_university_vectors():
    """Clear all university vectors from the database"""
    
    print("🗑️  Clearing University Vectors")
    print("=" * 30)
    
    # Get database session
    db = next(get_db())
    
    try:
        count = db.query(UniversityVector).count()
        
        if count == 0:
            print("No university vectors to clear")
            return
        
        print(f"Found {count} university vectors to delete")
        
        # Delete all vectors
        db.query(UniversityVector).delete()
        db.commit()
        
        print(f"✅ Successfully deleted {count} university vectors")
        
    except Exception as e:
        print(f"❌ Error clearing university vectors: {e}")
        db.rollback()
    
    finally:
        db.close()

def test_vector_matching():
    """Test vector-based matching with generated vectors"""
    
    print("🧪 Testing Vector-Based Matching")
    print("=" * 35)
    
    # Get database session
    db = next(get_db())
    
    try:
        # Check if we have vectors
        vector_count = db.query(UniversityVector).count()
        if vector_count == 0:
            print("❌ No university vectors found. Please generate vectors first.")
            return
        
        print(f"✅ Found {vector_count} university vectors")
        
        # Get a sample university for testing
        sample_vector = db.query(UniversityVector).first()
        if not sample_vector:
            print("❌ No sample vector found")
            return
        
        university = db.query(University).filter(University.id == sample_vector.university_id).first()
        print(f"🧪 Testing with: {university.name}")
        
        # Test vector similarity
        from api.vector_matcher import VectorMatchingService
        import asyncio
        
        async def test_similarity():
            vector_matcher = VectorMatchingService()
            
            # Create a test query embedding directly using OpenAI
            import openai
            import os
            
            client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            
            test_query = "I'm interested in computer science and engineering programs"
            
            try:
                # Generate query embedding
                response = client.embeddings.create(
                    model="text-embedding-3-small",
                    input=test_query,
                    encoding_format="float"
                )
                query_embedding = response.data[0].embedding
                
                # Calculate similarity
                similarity = vector_matcher._calculate_similarity(query_embedding, sample_vector.get_embedding_array().tolist())
                
                print(f"📊 Similarity score: {similarity:.4f}")
                print(f"✅ Vector matching test completed successfully!")
                
            except Exception as e:
                print(f"❌ Error generating test embedding: {e}")
        
        asyncio.run(test_similarity())
        
    except Exception as e:
        print(f"❌ Error testing vector matching: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        db.close()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate university vectors for enhanced matching")
    parser.add_argument("--generate", action="store_true", help="Generate vectors for all universities")
    parser.add_argument("--list", action="store_true", help="List all university vectors")
    parser.add_argument("--clear", action="store_true", help="Clear all university vectors")
    parser.add_argument("--test", action="store_true", help="Test vector-based matching")
    
    args = parser.parse_args()
    
    if args.generate:
        asyncio.run(generate_university_vectors())
    elif args.list:
        list_university_vectors()
    elif args.clear:
        clear_university_vectors()
    elif args.test:
        test_vector_matching()
    else:
        print("Please specify an option:")
        print("  --generate : Generate vectors for all universities")
        print("  --list     : List all university vectors")
        print("  --clear    : Clear all university vectors")
        print("  --test     : Test vector-based matching")
        print("\nExample: python3 generate_university_vectors.py --generate") 