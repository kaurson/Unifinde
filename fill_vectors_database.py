#!/usr/bin/env python3
"""
Script to fill the database with proper vectors by generating new embeddings
"""

import sys
import os
import numpy as np
import json
import openai
from sqlalchemy.orm import Session
from typing import List, Dict, Any

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.database import get_db, engine
from database.models import CollectionResultVector, UniversityDataCollectionResult

# Initialize OpenAI client
openai.api_key = os.getenv("OPENAI_API_KEY")
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def create_university_text(collection_result: UniversityDataCollectionResult) -> str:
    """Create comprehensive text representation of university for embedding"""
    
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
        text_parts.append(f"Type: {collection_result.type}")
    
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
    
    if collection_result.regional_ranking:
        text_parts.append(f"Regional ranking: #{collection_result.regional_ranking}")
    
    # Financial information
    if collection_result.tuition_domestic:
        text_parts.append(f"Domestic tuition: ${collection_result.tuition_domestic:,.2f}")
    
    if collection_result.tuition_international:
        text_parts.append(f"International tuition: ${collection_result.tuition_international:,.2f}")
    
    # Additional stats
    if collection_result.student_faculty_ratio:
        text_parts.append(f"Student-faculty ratio: {collection_result.student_faculty_ratio}:1")
    
    if collection_result.international_students_percentage:
        text_parts.append(f"International students: {collection_result.international_students_percentage}%")
    
    # Descriptions
    if collection_result.description:
        text_parts.append(f"Description: {collection_result.description}")
    
    if collection_result.mission_statement:
        text_parts.append(f"Mission: {collection_result.mission_statement}")
    
    if collection_result.vision_statement:
        text_parts.append(f"Vision: {collection_result.vision_statement}")
    
    # Programs
    if collection_result.programs:
        try:
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
                    text_parts.append(f"Programs offered: {', '.join(program_names[:10])}")  # Limit to first 10
        except:
            pass
    
    # Student life
    if collection_result.student_life:
        try:
            student_life_data = collection_result.student_life
            if isinstance(student_life_data, str):
                student_life_data = json.loads(student_life_data)
            
            if isinstance(student_life_data, dict):
                activities = []
                for category, details in student_life_data.items():
                    if isinstance(details, dict) and 'activities' in details:
                        activities.extend(details['activities'])
                
                if activities:
                    text_parts.append(f"Student activities: {', '.join(activities[:10])}")  # Limit to first 10
        except:
            pass
    
    return "\n".join(text_parts)

def generate_embedding(text: str) -> List[float]:
    """Generate embedding for text using OpenAI"""
    try:
        response = client.embeddings.create(
            model="text-embedding-3-small",
            input=text,
            encoding_format="float"
        )
        return response.data[0].embedding
    except Exception as e:
        print(f"Error generating embedding: {e}")
        # Return a default embedding of 1536 zeros
        return [0.0] * 1536

def fill_vectors_database():
    """Fill the database with proper vectors"""
    
    db = next(get_db())
    
    try:
        # Get all collection results
        collection_results = db.query(UniversityDataCollectionResult).all()
        print(f"Found {len(collection_results)} collection results to process")
        
        # Clear existing vectors first
        existing_vectors = db.query(CollectionResultVector).all()
        if existing_vectors:
            print(f"Clearing {len(existing_vectors)} existing vectors...")
            for vector in existing_vectors:
                db.delete(vector)
            db.commit()
            print("✅ Cleared existing vectors")
        
        success_count = 0
        error_count = 0
        
        for i, collection_result in enumerate(collection_results):
            try:
                print(f"Processing {i+1}/{len(collection_results)}: {collection_result.name}")
                
                # Create text representation
                university_text = create_university_text(collection_result)
                
                # Generate embedding
                embedding = generate_embedding(university_text)
                
                # Verify embedding is valid
                if len(embedding) != 1536:
                    print(f"  ⚠️  Warning: Embedding has {len(embedding)} dimensions, expected 1536")
                    # Pad or truncate to 1536
                    if len(embedding) < 1536:
                        embedding.extend([0.0] * (1536 - len(embedding)))
                    else:
                        embedding = embedding[:1536]
                
                # Check for NaN values
                if any(np.isnan(val) for val in embedding):
                    print(f"  ⚠️  Warning: Embedding contains NaN values, replacing with zeros")
                    embedding = [0.0 if np.isnan(val) else val for val in embedding]
                
                # Create vector record
                vector = CollectionResultVector(
                    collection_result_id=collection_result.id,
                    embedding=np.array(embedding, dtype=np.float32).tobytes(),  # Store as bytes
                    embedding_dimension=len(embedding),
                    embedding_model="text-embedding-3-small",
                    source_text=university_text,  # Store the text that was embedded
                    specialized_data="university_profile"
                )
                
                db.add(vector)
                success_count += 1
                print(f"  ✅ Created vector for {collection_result.name}")
                
                # Commit every 10 vectors to avoid memory issues
                if (i + 1) % 10 == 0:
                    db.commit()
                    print(f"  💾 Committed batch {i+1}")
                
            except Exception as e:
                print(f"  ❌ Error processing {collection_result.name}: {e}")
                error_count += 1
                continue
        
        # Final commit
        db.commit()
        
        print(f"\nSummary:")
        print(f"Successfully created vectors: {success_count}")
        print(f"Errors: {error_count}")
        print(f"Total processed: {len(collection_results)}")
        
        # Verify the results
        print(f"\nVerifying results...")
        verify_vectors()
        
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

def verify_vectors():
    """Verify that vectors are properly created"""
    
    db = next(get_db())
    
    try:
        vectors = db.query(CollectionResultVector).all()
        print(f"Verifying {len(vectors)} vectors...")
        
        valid_count = 0
        invalid_count = 0
        
        for i, vector in enumerate(vectors):
            try:
                embedding = vector.get_embedding_array()
                
                # Check dimensions
                if len(embedding) != 1536:
                    print(f"❌ Vector {i+1}: Wrong dimensions ({len(embedding)})")
                    invalid_count += 1
                    continue
                
                # Check for NaN values
                if np.isnan(embedding).any():
                    print(f"❌ Vector {i+1}: Contains NaN values")
                    invalid_count += 1
                    continue
                
                valid_count += 1
                
            except Exception as e:
                print(f"❌ Vector {i+1}: Error - {e}")
                invalid_count += 1
        
        print(f"\nVerification Results:")
        print(f"Valid vectors: {valid_count}")
        print(f"Invalid vectors: {invalid_count}")
        
        if invalid_count == 0:
            print("✅ All vectors are valid!")
        else:
            print("❌ Some vectors have issues")
            
    except Exception as e:
        print(f"Verification error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    fill_vectors_database() 