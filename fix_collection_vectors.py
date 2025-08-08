#!/usr/bin/env python3
"""
Fix Collection Vectors Script

This script regenerates collection vectors to fix NaN values and ensure proper embedding quality.
"""

import asyncio
import sys
import os
from sqlalchemy.orm import Session

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.database import get_db
from database.models import CollectionResultVector, UniversityDataCollectionResult
from api.vector_matcher import VectorMatchingService

async def fix_collection_vectors():
    """Fix collection vectors by regenerating them with proper cleaning"""
    
    print("🔧 Fixing Collection Vectors")
    print("=" * 50)
    
    # Get database session
    db = next(get_db())
    vector_service = VectorMatchingService()
    
    try:
        # Get all collection vectors
        collection_vectors = db.query(CollectionResultVector).all()
        print(f"Found {len(collection_vectors)} collection vectors to check")
        
        fixed_count = 0
        skipped_count = 0
        
        for i, vector in enumerate(collection_vectors):
            print(f"Processing vector {i+1}/{len(collection_vectors)}")
            
            # Get the collection result data
            collection_result = db.query(UniversityDataCollectionResult).filter(
                UniversityDataCollectionResult.id == vector.collection_result_id
            ).first()
            
            if not collection_result:
                print(f"Warning: No collection result found for vector {vector.collection_result_id}")
                skipped_count += 1
                continue
            
            try:
                # Get the current embedding
                current_embedding = vector.get_embedding_array().tolist()
                
                # Check if it has NaN values
                has_nan = any(np.isnan(val) for val in current_embedding if isinstance(val, (int, float)))
                has_inf = any(np.isinf(val) for val in current_embedding if isinstance(val, (int, float)))
                
                if has_nan or has_inf:
                    print(f"Vector {i+1} has NaN/inf values, regenerating...")
                    
                    # Create text representation for the collection result
                    text_representation = _create_collection_result_text(collection_result)
                    
                    # Generate new embedding
                    new_embedding = await vector_service._generate_embedding(text_representation)
                    
                    # Clean the embedding
                    cleaned_embedding = vector_service._clean_embedding(new_embedding)
                    
                    # Update the vector
                    vector.set_embedding_array(np.array(cleaned_embedding))
                    vector.embedding_dimension = len(cleaned_embedding)
                    vector.source_text = text_representation
                    
                    db.commit()
                    fixed_count += 1
                    print(f"✅ Fixed vector {i+1} for {collection_result.name}")
                else:
                    print(f"Vector {i+1} is clean, skipping")
                    skipped_count += 1
                    
            except Exception as e:
                print(f"Error processing vector {i+1}: {e}")
                skipped_count += 1
                continue
        
        print(f"\n✅ Collection vectors fixed!")
        print(f"Fixed: {fixed_count}")
        print(f"Skipped: {skipped_count}")
        print(f"Total: {len(collection_vectors)}")
        
    except Exception as e:
        print(f"❌ Error during vector fixing: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        db.close()

def _create_collection_result_text(collection_result: UniversityDataCollectionResult) -> str:
    """Create text representation for collection result"""
    
    text_parts = []
    
    # Basic information
    text_parts.append(f"University: {collection_result.name}")
    
    # Location
    location_parts = []
    if collection_result.city:
        location_parts.append(collection_result.city)
    if collection_result.state:
        location_parts.append(collection_result.state)
    if collection_result.country:
        location_parts.append(collection_result.country)
    
    if location_parts:
        text_parts.append(f"Location: {', '.join(location_parts)}")
    
    # Type and basic stats
    if collection_result.type:
        text_parts.append(f"University type: {collection_result.type}")
    
    if collection_result.student_population:
        text_parts.append(f"Student population: {collection_result.student_population:,}")
    
    if collection_result.faculty_count:
        text_parts.append(f"Faculty count: {collection_result.faculty_count:,}")
    
    # Academic information
    if collection_result.acceptance_rate:
        text_parts.append(f"Acceptance rate: {collection_result.acceptance_rate:.1%}")
    
    if collection_result.founded_year:
        text_parts.append(f"Founded: {collection_result.founded_year}")
    
    # Rankings
    if collection_result.world_ranking:
        text_parts.append(f"World ranking: #{collection_result.world_ranking}")
    
    if collection_result.national_ranking:
        text_parts.append(f"National ranking: #{collection_result.national_ranking}")
    
    # Financial information
    if collection_result.tuition_domestic:
        text_parts.append(f"Domestic tuition: ${collection_result.tuition_domestic:,.0f}")
    
    if collection_result.tuition_international:
        text_parts.append(f"International tuition: ${collection_result.tuition_international:,.0f}")
    
    # Descriptions
    if collection_result.description:
        text_parts.append(f"Description: {collection_result.description}")
    
    if collection_result.mission_statement:
        text_parts.append(f"Mission: {collection_result.mission_statement}")
    
    # Programs
    if collection_result.programs:
        try:
            import json
            programs_data = collection_result.programs
            if isinstance(programs_data, str):
                programs_data = json.loads(programs_data)
            
            if isinstance(programs_data, list):
                program_names = []
                for program in programs_data:
                    if isinstance(program, dict):
                        if 'name' in program:
                            program_names.append(program['name'])
                        elif 'field' in program:
                            program_names.append(program['field'])
                
                if program_names:
                    text_parts.append(f"Programs offered: {', '.join(program_names)}")
        except:
            pass
    
    # Create a structured summary
    summary_parts = []
    if collection_result.type:
        summary_parts.append(f"{collection_result.type} university")
    if collection_result.city and collection_result.country:
        summary_parts.append(f"located in {collection_result.city}, {collection_result.country}")
    if collection_result.student_population:
        summary_parts.append(f"with {collection_result.student_population:,} students")
    if collection_result.acceptance_rate:
        summary_parts.append(f"acceptance rate {collection_result.acceptance_rate:.1%}")
    if collection_result.tuition_domestic:
        summary_parts.append(f"tuition ${collection_result.tuition_domestic:,.0f}")
    
    if summary_parts:
        text_parts.append(f"University summary: {', '.join(summary_parts)}")
    
    return "\n".join(text_parts)

async def main():
    """Main function"""
    print("🎓 University Matching App - Fix Collection Vectors")
    print("=" * 60)
    
    await fix_collection_vectors()
    
    print("\n🎉 Collection vectors fixed successfully!")

if __name__ == "__main__":
    import numpy as np
    asyncio.run(main()) 