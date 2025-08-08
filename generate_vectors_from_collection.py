#!/usr/bin/env python3
"""
Script to generate embeddings directly from university_data_collection_results table 
and store them in the collection_vectors table for vector-based matching.
"""

import sys
import os
import asyncio
from datetime import datetime
import json
import uuid

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.database import get_db
from database.models import UniversityDataCollectionResult
from api.vector_matcher import VectorMatchingService

# Import the new CollectionVector model
from create_collection_vectors_table import CollectionVector

def create_university_text_from_collection(result):
    """Create a comprehensive text representation of a university from collection result"""
    
    text_parts = []
    
    # Basic university information
    text_parts.append(f"University: {result.name}")
    
    if result.description:
        text_parts.append(f"Description: {result.description}")
    
    if result.mission_statement:
        text_parts.append(f"Mission: {result.mission_statement}")
    
    # Location and basic info
    location_parts = []
    if result.city:
        location_parts.append(result.city)
    if result.state:
        location_parts.append(result.state)
    if result.country:
        location_parts.append(result.country)
    
    if location_parts:
        text_parts.append(f"Location: {', '.join(location_parts)}")
    
    # Academic information
    if result.type:
        text_parts.append(f"Type: {result.type}")
    
    if result.founded_year:
        text_parts.append(f"Founded: {result.founded_year}")
    
    if result.student_population:
        text_parts.append(f"Student Population: {result.student_population:,}")
    
    if result.faculty_count:
        text_parts.append(f"Faculty Count: {result.faculty_count:,}")
    
    if result.acceptance_rate:
        text_parts.append(f"Acceptance Rate: {result.acceptance_rate:.1%}")
    
    if result.tuition_domestic:
        text_parts.append(f"Domestic Tuition: ${result.tuition_domestic:,}")
    
    if result.tuition_international:
        text_parts.append(f"International Tuition: ${result.tuition_international:,}")
    
    # Rankings
    if result.world_ranking:
        text_parts.append(f"World Ranking: #{result.world_ranking}")
    
    if result.national_ranking:
        text_parts.append(f"National Ranking: #{result.national_ranking}")
    
    # Programs from collection data
    if result.programs:
        try:
            programs_data = result.programs
            if isinstance(programs_data, list):
                program_names = []
                for prog in programs_data[:10]:  # Limit to first 10
                    if isinstance(prog, dict) and prog.get('name'):
                        program_names.append(prog['name'])
                if program_names:
                    text_parts.append(f"Programs: {', '.join(program_names)}")
        except Exception as e:
            print(f"   ⚠️  Warning: Could not process programs: {e}")
    
    # Facilities from collection data
    if hasattr(result, 'facilities') and result.facilities:
        try:
            facilities_data = result.facilities
            if isinstance(facilities_data, list):
                facility_names = []
                for fac in facilities_data[:10]:  # Limit to first 10
                    if isinstance(fac, dict) and fac.get('name'):
                        facility_names.append(fac['name'])
                if facility_names:
                    text_parts.append(f"Facilities: {', '.join(facility_names)}")
        except Exception as e:
            print(f"   ⚠️  Warning: Could not process facilities: {e}")
    
    # Additional data from collection
    if result.student_life:
        text_parts.append(f"Student Life: {str(result.student_life)[:200]}...")
    
    if result.financial_aid:
        text_parts.append(f"Financial Aid: {str(result.financial_aid)[:200]}...")
    
    return " | ".join(text_parts)

async def generate_vectors_from_collection():
    """Generate embeddings from university_data_collection_results and store in collection_vectors table"""
    
    print("🧠 Generating Vectors from Collection Results")
    print("=" * 50)
    
    # Get database session
    db = next(get_db())
    
    try:
        # Get all university data collection results
        collection_results = db.query(UniversityDataCollectionResult).all()
        
        if not collection_results:
            print("❌ No university data collection results found")
            return
        
        print(f"📊 Found {len(collection_results)} collection results to process")
        
        # Initialize vector matcher
        vector_matcher = VectorMatchingService()
        
        # Check existing vectors
        existing_vectors = db.query(CollectionVector).count()
        print(f"📋 Existing vectors in database: {existing_vectors}")
        
        # Process collection results
        successful_generations = 0
        skipped_count = 0
        error_count = 0
        
        for i, result in enumerate(collection_results, 1):
            try:
                print(f"\n[{i}/{len(collection_results)}] Processing: {result.name or 'Unnamed University'}")
                
                # Skip if no name
                if not result.name:
                    print(f"   ⏭️  No name, skipping...")
                    skipped_count += 1
                    continue
                
                # Check if vector already exists for this university name
                existing_vector = db.query(CollectionVector).filter(
                    CollectionVector.university_name == result.name
                ).first()
                
                if existing_vector:
                    print(f"   ⏭️  Vector already exists for {result.name}, skipping...")
                    skipped_count += 1
                    continue
                
                # Create university text for embedding
                university_text = create_university_text_from_collection(result)
                
                print(f"   📝 Text length: {len(university_text)} characters")
                
                # Generate embedding using OpenAI directly
                import openai
                client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
                
                print(f"   🧠 Generating embedding...")
                response = client.embeddings.create(
                    model="text-embedding-3-small",
                    input=university_text,
                    encoding_format="float"
                )
                embedding = response.data[0].embedding
                
                if embedding is None:
                    print(f"   ❌ Failed to generate embedding")
                    error_count += 1
                    continue
                
                # Store vector in database
                collection_vector = CollectionVector(
                    id=str(uuid.uuid4()),
                    collection_result_id=str(result.id),
                    university_name=result.name,
                    embedding_model="text-embedding-3-small",
                    source_text=university_text,
                    created_at=datetime.now()
                )
                
                # Set the embedding using the model's method
                import numpy as np
                embedding_array = np.array(embedding, dtype=np.float32)
                collection_vector.set_embedding_array(embedding_array)
                
                db.add(collection_vector)
                db.commit()
                
                print(f"   ✅ Vector generated and stored ({len(embedding)} dimensions)")
                successful_generations += 1
                
            except Exception as e:
                print(f"   ❌ Error processing {result.name}: {e}")
                db.rollback()
                error_count += 1
                continue
        
        print(f"\n🎉 Vector Generation Complete!")
        print(f"   ✅ Successfully generated: {successful_generations}")
        print(f"   ⏭️  Skipped (already exists): {skipped_count}")
        print(f"   ❌ Errors: {error_count}")
        print(f"   📊 Total vectors in database: {db.query(CollectionVector).count()}")
        
    except Exception as e:
        print(f"❌ Error generating vectors from collection: {e}")
        db.rollback()
        import traceback
        traceback.print_exc()
    
    finally:
        db.close()

def list_collection_vectors():
    """List all vectors generated from collection results"""
    
    print("📋 Vectors from Collection Results")
    print("=" * 35)
    
    # Get database session
    db = next(get_db())
    
    try:
        vectors = db.query(CollectionVector).all()
        
        if not vectors:
            print("No vectors found in database")
            return
        
        print(f"Found {len(vectors)} vectors:")
        print()
        
        for i, vector in enumerate(vectors, 1):
            print(f"{i}. {vector.university_name}")
            print(f"   Vector ID: {vector.id}")
            print(f"   Collection Result ID: {vector.collection_result_id}")
            print(f"   Embedding Model: {vector.embedding_model}")
            print(f"   Embedding Dimensions: {vector.embedding_dimension}")
            print(f"   Source Text Length: {len(vector.source_text)}")
            print(f"   Created: {vector.created_at}")
            print()
        
    except Exception as e:
        print(f"❌ Error listing vectors: {e}")
    
    finally:
        db.close()

def test_collection_vector_matching():
    """Test vector-based matching with vectors from collection results"""
    
    print("🧪 Testing Vector Matching from Collection")
    print("=" * 45)
    
    # Get database session
    db = next(get_db())
    
    try:
        # Check if we have vectors
        vector_count = db.query(CollectionVector).count()
        if vector_count == 0:
            print("❌ No vectors found. Please generate vectors first.")
            return
        
        print(f"✅ Found {vector_count} vectors")
        
        # Get a sample vector for testing
        sample_vector = db.query(CollectionVector).first()
        if not sample_vector:
            print("❌ No sample vector found")
            return
        
        print(f"🧪 Testing with: {sample_vector.university_name}")
        
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
    
    parser = argparse.ArgumentParser(description="Generate vectors from university data collection results")
    parser.add_argument("--generate", action="store_true", help="Generate vectors from collection results")
    parser.add_argument("--list", action="store_true", help="List all vectors from collection")
    parser.add_argument("--test", action="store_true", help="Test vector-based matching")
    
    args = parser.parse_args()
    
    if args.generate:
        asyncio.run(generate_vectors_from_collection())
    elif args.list:
        list_collection_vectors()
    elif args.test:
        test_collection_vector_matching()
    else:
        print("Please specify an option:")
        print("  --generate : Generate vectors from collection results")
        print("  --list     : List all vectors from collection")
        print("  --test     : Test vector-based matching")
        print("\nExample: python3 generate_vectors_from_collection.py --generate") 