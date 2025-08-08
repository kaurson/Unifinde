#!/usr/bin/env python3
"""
Debug Similarity Issue Script

This script investigates why all similarity scores are 1.0 by examining vector content and text representations.
"""

import asyncio
import sys
import os
import numpy as np
from sqlalchemy.orm import Session

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.database import get_db
from database.models import CollectionResultVector, UniversityDataCollectionResult, User
from api.vector_matcher import VectorMatchingService

async def debug_similarity_issue():
    """Debug why all similarity scores are 1.0"""
    
    print("🔍 Debugging Similarity Issue")
    print("=" * 50)
    
    # Get database session
    db = next(get_db())
    vector_service = VectorMatchingService()
    
    try:
        # Get a sample user
        user = db.query(User).first()
        if not user:
            print("❌ No users found in database")
            return
        
        print(f"Using user: {user.email}")
        
        # Generate user embedding
        print("\n1. 🔍 User Embedding Analysis")
        print("-" * 30)
        user_embedding = await vector_service.generate_user_embedding(user, db)
        print(f"User embedding dimensions: {len(user_embedding)}")
        print(f"User embedding first 10 values: {user_embedding[:10]}")
        print(f"User embedding last 10 values: {user_embedding[-10:]}")
        print(f"User embedding mean: {np.mean(user_embedding):.6f}")
        print(f"User embedding std: {np.std(user_embedding):.6f}")
        print(f"User embedding min: {np.min(user_embedding):.6f}")
        print(f"User embedding max: {np.max(user_embedding):.6f}")
        
        # Get a few sample collection vectors
        print("\n2. 🔍 Collection Vector Analysis")
        print("-" * 30)
        collection_vectors = db.query(CollectionResultVector).limit(5).all()
        
        for i, vector in enumerate(collection_vectors):
            print(f"\nVector {i+1}:")
            
            # Get the collection result
            collection_result = db.query(UniversityDataCollectionResult).filter(
                UniversityDataCollectionResult.id == vector.collection_result_id
            ).first()
            
            if collection_result:
                print(f"  University: {collection_result.name}")
                print(f"  Location: {collection_result.city}, {collection_result.state}, {collection_result.country}")
                print(f"  Type: {collection_result.type}")
            
            # Get embedding
            embedding = vector.get_embedding_array().tolist()
            print(f"  Embedding dimensions: {len(embedding)}")
            print(f"  First 10 values: {embedding[:10]}")
            print(f"  Last 10 values: {embedding[-10:]}")
            print(f"  Mean: {np.mean(embedding):.6f}")
            print(f"  Std: {np.std(embedding):.6f}")
            print(f"  Min: {np.min(embedding):.6f}")
            print(f"  Max: {np.max(embedding):.6f}")
            
            # Check source text
            if vector.source_text:
                print(f"  Source text length: {len(vector.source_text)}")
                print(f"  Source text preview: {vector.source_text[:200]}...")
            else:
                print(f"  No source text available")
            
            # Calculate similarity with user
            similarity = vector_service._calculate_similarity(user_embedding, embedding)
            print(f"  Similarity with user: {similarity:.6f}")
        
        # Check if vectors are identical
        print("\n3. 🔍 Vector Identity Check")
        print("-" * 30)
        
        if len(collection_vectors) >= 2:
            vec1 = collection_vectors[0].get_embedding_array().tolist()
            vec2 = collection_vectors[1].get_embedding_array().tolist()
            
            # Check if vectors are identical
            are_identical = np.array_equal(np.array(vec1), np.array(vec2))
            print(f"First two vectors identical: {are_identical}")
            
            if are_identical:
                print("❌ PROBLEM: Vectors are identical!")
            else:
                # Check similarity between vectors
                similarity_between_vectors = vector_service._calculate_similarity(vec1, vec2)
                print(f"Similarity between first two vectors: {similarity_between_vectors:.6f}")
                
                if similarity_between_vectors > 0.99:
                    print("❌ PROBLEM: Vectors are nearly identical!")
                else:
                    print("✅ Vectors are different")
        
        # Check source text diversity
        print("\n4. 🔍 Source Text Diversity Check")
        print("-" * 30)
        
        sample_vectors = db.query(CollectionResultVector).limit(10).all()
        source_texts = []
        
        for vector in sample_vectors:
            if vector.source_text:
                source_texts.append(vector.source_text[:100])  # First 100 chars
        
        unique_texts = set(source_texts)
        print(f"Sample vectors: {len(sample_vectors)}")
        print(f"Unique source text prefixes: {len(unique_texts)}")
        
        if len(unique_texts) == 1:
            print("❌ PROBLEM: All vectors have identical source text!")
        elif len(unique_texts) < len(sample_vectors) * 0.5:
            print("⚠️  WARNING: Many vectors have similar source text")
        else:
            print("✅ Source texts are diverse")
        
        # Show a few unique source texts
        for i, text in enumerate(list(unique_texts)[:3]):
            print(f"  Sample text {i+1}: {text}...")
        
        # Test with a simple query
        print("\n5. 🔍 Simple Query Test")
        print("-" * 30)
        
        # Create a simple test query
        test_query = "I want to study computer science at a large public university"
        test_embedding = await vector_service._generate_embedding(test_query)
        test_embedding = vector_service._clean_embedding(test_embedding)
        
        print(f"Test query: {test_query}")
        print(f"Test embedding dimensions: {len(test_embedding)}")
        print(f"Test embedding mean: {np.mean(test_embedding):.6f}")
        print(f"Test embedding std: {np.std(test_embedding):.6f}")
        
        # Test similarity with first few vectors
        for i, vector in enumerate(collection_vectors[:3]):
            vec_embedding = vector.get_embedding_array().tolist()
            similarity = vector_service._calculate_similarity(test_embedding, vec_embedding)
            print(f"  Similarity with vector {i+1}: {similarity:.6f}")
        
    except Exception as e:
        print(f"❌ Error during debugging: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        db.close()

async def main():
    """Main function"""
    print("🎓 University Matching App - Debug Similarity Issue")
    print("=" * 60)
    
    await debug_similarity_issue()
    
    print("\n🔍 Debugging completed!")

if __name__ == "__main__":
    asyncio.run(main()) 