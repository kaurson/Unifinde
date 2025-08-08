#!/usr/bin/env python3
"""
Debug script to analyze why some collection vectors are giving zero similarity scores
"""

import sys
import os
import numpy as np
from datetime import datetime

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.database import get_db
from database.models import CollectionResultVector, UniversityDataCollectionResult, User
from api.vector_matcher import VectorMatchingService

async def debug_zero_vectors():
    """Debug why some vectors are giving zero similarity scores"""
    
    db = next(get_db())
    vector_service = VectorMatchingService()
    
    try:
        print("🔍 Debugging Zero Vectors Issue")
        print("=" * 50)
        
        # Get a test user
        test_user = db.query(User).first()
        if not test_user:
            print("❌ No users found in database")
            return
        
        print(f"Using test user: {test_user.email}")
        
        # Generate user embedding
        print("\n1. 📊 User Embedding Analysis")
        print("-" * 30)
        user_embedding = await vector_service.generate_user_embedding(test_user, db)
        print(f"User embedding dimensions: {len(user_embedding)}")
        print(f"User embedding mean: {np.mean(user_embedding):.6f}")
        print(f"User embedding std: {np.std(user_embedding):.6f}")
        print(f"User embedding min: {np.min(user_embedding):.6f}")
        print(f"User embedding max: {np.max(user_embedding):.6f}")
        
        # Check if user embedding is all zeros
        if np.all(np.array(user_embedding) == 0):
            print("❌ WARNING: User embedding is all zeros!")
        else:
            print("✅ User embedding looks good")
        
        # Get all collection vectors
        collection_vectors = db.query(CollectionResultVector).all()
        print(f"\n2. 📊 Collection Vectors Analysis")
        print("-" * 30)
        print(f"Total collection vectors: {len(collection_vectors)}")
        
        zero_vectors = []
        low_variance_vectors = []
        normal_vectors = []
        
        for i, vector in enumerate(collection_vectors):
            try:
                # Get the embedding
                embedding = vector.get_embedding_array().tolist()
                
                # Get collection result
                collection_result = db.query(UniversityDataCollectionResult).filter(
                    UniversityDataCollectionResult.id == vector.collection_result_id
                ).first()
                
                # Analyze embedding
                embedding_array = np.array(embedding)
                mean_val = np.mean(embedding_array)
                std_val = np.std(embedding_array)
                min_val = np.min(embedding_array)
                max_val = np.max(embedding_array)
                
                # Check for zero vectors
                if np.all(embedding_array == 0):
                    zero_vectors.append({
                        'index': i,
                        'vector_id': vector.id,
                        'university_name': collection_result.name if collection_result else 'Unknown',
                        'source_text_length': len(vector.source_text) if vector.source_text else 0
                    })
                elif std_val < 0.001:  # Very low variance
                    low_variance_vectors.append({
                        'index': i,
                        'vector_id': vector.id,
                        'university_name': collection_result.name if collection_result else 'Unknown',
                        'std': std_val,
                        'source_text_length': len(vector.source_text) if vector.source_text else 0
                    })
                else:
                    normal_vectors.append({
                        'index': i,
                        'vector_id': vector.id,
                        'university_name': collection_result.name if collection_result else 'Unknown',
                        'mean': mean_val,
                        'std': std_val
                    })
                
                # Calculate similarity with user
                similarity = vector_service._calculate_similarity(user_embedding, embedding)
                
                if similarity == 0.0:
                    print(f"Vector {i+1}: {collection_result.name if collection_result else 'Unknown'} - Similarity: 0.0")
                    print(f"  Embedding stats: mean={mean_val:.6f}, std={std_val:.6f}, min={min_val:.6f}, max={max_val:.6f}")
                    print(f"  Source text length: {len(vector.source_text) if vector.source_text else 0}")
                    if vector.source_text:
                        print(f"  Source text preview: {vector.source_text[:100]}...")
                    print()
                
            except Exception as e:
                print(f"Error analyzing vector {i+1}: {e}")
                continue
        
        print(f"\n3. 📈 Vector Statistics")
        print("-" * 30)
        print(f"Zero vectors: {len(zero_vectors)}")
        print(f"Low variance vectors: {len(low_variance_vectors)}")
        print(f"Normal vectors: {len(normal_vectors)}")
        
        if zero_vectors:
            print(f"\n4. 🚨 Zero Vectors Details")
            print("-" * 30)
            for zero_vec in zero_vectors[:10]:  # Show first 10
                print(f"Vector {zero_vec['index']+1}: {zero_vec['university_name']}")
                print(f"  Source text length: {zero_vec['source_text_length']}")
        
        if low_variance_vectors:
            print(f"\n5. ⚠️ Low Variance Vectors Details")
            print("-" * 30)
            for low_var_vec in low_variance_vectors[:10]:  # Show first 10
                print(f"Vector {low_var_vec['index']+1}: {low_var_vec['university_name']}")
                print(f"  Std: {low_var_vec['std']:.8f}")
                print(f"  Source text length: {low_var_vec['source_text_length']}")
        
        # Check source text quality
        print(f"\n6. 📝 Source Text Analysis")
        print("-" * 30)
        empty_text_count = 0
        short_text_count = 0
        normal_text_count = 0
        
        for vector in collection_vectors:
            if not vector.source_text:
                empty_text_count += 1
            elif len(vector.source_text) < 50:
                short_text_count += 1
            else:
                normal_text_count += 1
        
        print(f"Empty source text: {empty_text_count}")
        print(f"Short source text (<50 chars): {short_text_count}")
        print(f"Normal source text: {normal_text_count}")
        
        # Show examples of problematic source texts
        print(f"\n7. 🔍 Problematic Source Text Examples")
        print("-" * 30)
        problematic_count = 0
        for vector in collection_vectors:
            if not vector.source_text or len(vector.source_text) < 50:
                collection_result = db.query(UniversityDataCollectionResult).filter(
                    UniversityDataCollectionResult.id == vector.collection_result_id
                ).first()
                print(f"University: {collection_result.name if collection_result else 'Unknown'}")
                print(f"Source text: '{vector.source_text}'")
                print(f"Length: {len(vector.source_text) if vector.source_text else 0}")
                print()
                problematic_count += 1
                if problematic_count >= 5:  # Show first 5
                    break
        
        # Recommendations
        print(f"\n8. 💡 Recommendations")
        print("-" * 30)
        if zero_vectors:
            print("❌ Found zero vectors - these need to be regenerated")
            print("   Run: python fix_collection_vectors.py")
        
        if empty_text_count > 0:
            print("❌ Found vectors with empty source text - these need to be regenerated")
            print("   Run: python generate_collection_vectors.py")
        
        if low_variance_vectors:
            print("⚠️ Found vectors with very low variance - these may need regeneration")
        
        if not zero_vectors and not empty_text_count:
            print("✅ All vectors appear to be properly generated")
            print("   The zero similarity scores might be due to:")
            print("   - User profile not matching any universities")
            print("   - Threshold too high (currently 0.01)")
            print("   - Need to lower threshold or improve user profile")
        
    except Exception as e:
        print(f"❌ Error during debugging: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        db.close()

if __name__ == "__main__":
    import asyncio
    asyncio.run(debug_zero_vectors()) 