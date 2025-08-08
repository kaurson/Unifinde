#!/usr/bin/env python3
"""
Generate vectors from UniversityDataCollectionResult table
Uses the enhanced collection vectorizer for rich data from collection results
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
from database.models import UniversityDataCollectionResult, CollectionResultVector
from api.enhanced_collection_vectorizer import EnhancedCollectionVectorizer

async def generate_collection_vectors():
    """Generate enhanced vectors for all collection results"""
    
    print("\n🧠 Generating Vectors from Collection Results")
    print("=" * 50)
    
    vectorizer = EnhancedCollectionVectorizer()
    db = next(get_db())
    
    try:
        # Get all collection results
        collection_results = db.query(UniversityDataCollectionResult).all()
        total_results = len(collection_results)
        
        if total_results == 0:
            print("❌ No collection results found in database")
            return
        
        print(f"Found {total_results} collection results to process\n")
        
        success_count = 0
        error_count = 0
        
        for i, collection_result in enumerate(collection_results, 1):
            print(f"[{i}/{total_results}] Processing: {collection_result.name}")
            
            try:
                # Generate enhanced embeddings
                embedding_data = await vectorizer.generate_collection_embedding(collection_result)
                
                # Check if vector already exists
                existing_vector = db.query(CollectionResultVector).filter(
                    CollectionResultVector.collection_result_id == collection_result.id
                ).first()
                
                # Prepare specialized data
                specialized_data = {
                    'specialized_embeddings': embedding_data['specialized_embeddings'],
                    'specialized_texts': embedding_data['specialized_texts'],
                    'matching_profile': vectorizer.create_matching_profile(collection_result)
                }
                
                if existing_vector:
                    # Update existing vector
                    existing_vector.set_embedding_array(np.array(embedding_data['main_embedding']))
                    existing_vector.embedding_model = embedding_data['embedding_model']
                    existing_vector.source_text = embedding_data['main_text']
                    existing_vector.specialized_data = specialized_data
                    existing_vector.updated_at = datetime.now()
                    print(f"  ✅ Updated existing vector")
                else:
                    # Create new vector
                    new_vector = CollectionResultVector(
                        collection_result_id=collection_result.id,
                        embedding_model=embedding_data['embedding_model'],
                        source_text=embedding_data['main_text'],
                        specialized_data=specialized_data
                    )
                    new_vector.set_embedding_array(np.array(embedding_data['main_embedding']))
                    db.add(new_vector)
                    print(f"  ✅ Created new vector")
                
                # Commit after each vector to avoid losing progress
                db.commit()
                success_count += 1
                
            except Exception as e:
                print(f"  ❌ Error processing {collection_result.name}: {str(e)}")
                error_count += 1
                db.rollback()
                continue
        
        print(f"\n🎉 Vector Generation Complete!")
        print(f"✅ Successfully processed: {success_count} collection results")
        print(f"❌ Errors: {error_count} collection results")
        print(f"📊 Success rate: {(success_count/total_results)*100:.1f}%")
        
    except Exception as e:
        print(f"❌ Database error: {str(e)}")
        db.rollback()
    finally:
        db.close()

async def test_collection_vectorizer():
    """Test the collection vectorizer with sample data"""
    
    print("\n🧪 Testing Collection Vectorizer")
    print("=" * 35)
    
    vectorizer = EnhancedCollectionVectorizer()
    db = next(get_db())
    
    try:
        # Get a sample collection result
        collection_result = db.query(UniversityDataCollectionResult).first()
        if not collection_result:
            print("❌ No collection results found in database")
            return
        
        print(f"Testing with: {collection_result.name}")
        
        # Generate embeddings
        embedding_data = await vectorizer.generate_collection_embedding(collection_result)
        
        print(f"✅ Generated main embedding: {len(embedding_data['main_embedding'])} dimensions")
        print(f"✅ Generated specialized embeddings: {list(embedding_data['specialized_embeddings'].keys())}")
        
        # Test text generation
        main_text = vectorizer.create_structured_collection_text(collection_result)
        print(f"📝 Main text length: {len(main_text)} characters")
        
        # Show a preview of the text
        print(f"📄 Text preview: {main_text[:300]}...")
        
        # Test matching profile
        profile = vectorizer.create_matching_profile(collection_result)
        print(f"📊 Profile created with {len(profile['academic_profile']['programs'])} programs")
        
        # Show some profile details
        print(f"📍 Location: {profile['basic_info']['location']}")
        print(f"💰 Tuition: ${profile['financial_profile']['tuition_domestic']:,.0f}" if profile['financial_profile']['tuition_domestic'] else "💰 Tuition: Not available")
        print(f"🎯 Acceptance Rate: {profile['academic_profile']['acceptance_rate']:.1%}" if profile['academic_profile']['acceptance_rate'] else "🎯 Acceptance Rate: Not available")
        
    except Exception as e:
        print(f"❌ Test error: {str(e)}")
    finally:
        db.close()

async def list_collection_vectors():
    """List all vectors generated from collection results"""
    
    print("\n📋 Collection Result Vectors")
    print("=" * 30)
    
    db = next(get_db())
    
    try:
        vectors = db.query(CollectionResultVector).all()
        
        if not vectors:
            print("No vectors found")
            return
        
        print(f"Found {len(vectors)} vectors:")
        
        for vector in vectors:
            # Try to find the collection result
            collection_result = db.query(UniversityDataCollectionResult).filter(
                UniversityDataCollectionResult.id == vector.collection_result_id
            ).first()
            
            university_name = collection_result.name if collection_result else "Unknown"
            
            embedding_array = vector.get_embedding_array()
            print(f"  - {university_name}")
            print(f"    ID: {vector.collection_result_id}")
            print(f"    Dimensions: {vector.embedding_dimension}")
            print(f"    Model: {vector.embedding_model}")
            print(f"    Created: {vector.created_at}")
            print(f"    Updated: {vector.updated_at}")
            print()
            
    except Exception as e:
        print(f"❌ Error listing vectors: {str(e)}")
    finally:
        db.close()

async def analyze_collection_data():
    """Analyze the collection data to understand what's available"""
    
    print("\n📊 Analyzing Collection Data")
    print("=" * 30)
    
    db = next(get_db())
    
    try:
        collection_results = db.query(UniversityDataCollectionResult).all()
        
        if not collection_results:
            print("No collection results found")
            return
        
        print(f"Found {len(collection_results)} collection results")
        
        # Analyze data completeness
        fields_to_check = [
            'name', 'type', 'founded_year', 'student_population', 'faculty_count',
            'acceptance_rate', 'tuition_domestic', 'world_ranking', 'description',
            'programs', 'student_life', 'subject_rankings'
        ]
        
        field_stats = {}
        for field in fields_to_check:
            count = 0
            for result in collection_results:
                value = getattr(result, field, None)
                if value is not None and value != '':
                    count += 1
            field_stats[field] = count
        
        print("\nData Completeness:")
        for field, count in field_stats.items():
            percentage = (count / len(collection_results)) * 100
            print(f"  {field}: {count}/{len(collection_results)} ({percentage:.1f}%)")
        
        # Show sample data
        print(f"\nSample Collection Result:")
        sample = collection_results[0]
        print(f"  Name: {sample.name}")
        print(f"  Type: {sample.type}")
        print(f"  Location: {sample.city}, {sample.state}, {sample.country}")
        print(f"  Student Population: {sample.student_population:,}" if sample.student_population else "  Student Population: Not available")
        print(f"  Acceptance Rate: {sample.acceptance_rate:.1%}" if sample.acceptance_rate else "  Acceptance Rate: Not available")
        print(f"  Tuition: ${sample.tuition_domestic:,.0f}" if sample.tuition_domestic else "  Tuition: Not available")
        
        # Check JSON fields
        if sample.programs:
            try:
                programs_data = sample.programs
                if isinstance(programs_data, str):
                    programs_data = json.loads(programs_data)
                print(f"  Programs: {len(programs_data)} programs found" if isinstance(programs_data, list) else "  Programs: Data available")
            except:
                print("  Programs: Error parsing")
        
        if sample.student_life:
            try:
                student_life_data = sample.student_life
                if isinstance(student_life_data, str):
                    student_life_data = json.loads(student_life_data)
                print(f"  Student Life: {len(student_life_data)} categories found" if isinstance(student_life_data, dict) else "  Student Life: Data available")
            except:
                print("  Student Life: Error parsing")
        
    except Exception as e:
        print(f"❌ Analysis error: {str(e)}")
    finally:
        db.close()

async def clear_collection_vectors():
    """Clear all vectors generated from collection results"""
    
    print("\n🗑️ Clearing Collection Result Vectors")
    print("=" * 35)
    
    db = next(get_db())
    
    try:
        count = db.query(CollectionResultVector).count()
        print(f"Found {count} vectors to delete")
        
        if count > 0:
            db.query(CollectionResultVector).delete()
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
    
    parser = argparse.ArgumentParser(description="Collection Result Vector Generator")
    parser.add_argument("--action", choices=["generate", "test", "list", "analyze", "clear"], 
                       default="generate", help="Action to perform")
    
    args = parser.parse_args()
    
    if args.action == "generate":
        asyncio.run(generate_collection_vectors())
    elif args.action == "test":
        asyncio.run(test_collection_vectorizer())
    elif args.action == "list":
        asyncio.run(list_collection_vectors())
    elif args.action == "analyze":
        asyncio.run(analyze_collection_data())
    elif args.action == "clear":
        asyncio.run(clear_collection_vectors()) 