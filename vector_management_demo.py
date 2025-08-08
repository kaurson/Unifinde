#!/usr/bin/env python3
"""
Vector Management Demo Script

This script demonstrates the new vector storage system for efficient vector matching.
It shows how vectors are stored, retrieved, and cached to avoid redundant computations.
"""

import asyncio
import sys
import os
from sqlalchemy.orm import Session

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.database import get_db
from database.models import User, University, UserVector, UniversityVector, VectorSearchCache
from api.vector_matcher import VectorMatchingService

async def demo_vector_storage():
    """Demonstrate the vector storage system"""
    
    print("🚀 Vector Storage System Demo")
    print("=" * 50)
    
    # Get database session
    db = next(get_db())
    vector_service = VectorMatchingService()
    
    try:
        # 1. Check current vector statistics
        print("\n1. 📊 Current Vector Statistics")
        print("-" * 30)
        stats = await vector_service.get_vector_statistics(db)
        print(f"Users with vectors: {stats['users']['with_vectors']}/{stats['users']['total']} ({stats['users']['coverage_percentage']:.1f}%)")
        print(f"Universities with vectors: {stats['universities']['with_vectors']}/{stats['universities']['total']} ({stats['universities']['coverage_percentage']:.1f}%)")
        print(f"Collection vectors: {stats['collection_vectors']}")
        print(f"Cache entries: {stats['cache']['total_entries']} (expired: {stats['cache']['expired_entries']})")
        
        # 2. Generate vectors for users without them
        print("\n2. 🔄 Generating User Vectors")
        print("-" * 30)
        users_without_vectors = db.query(User).outerjoin(
            UserVector, User.id == UserVector.user_id
        ).filter(UserVector.id.is_(None)).limit(5).all()
        
        if users_without_vectors:
            print(f"Found {len(users_without_vectors)} users without vectors")
            await vector_service.batch_generate_user_vectors(db, len(users_without_vectors))
            print("✅ User vectors generated successfully")
        else:
            print("✅ All users already have vectors")
        
        # 3. Generate vectors for universities without them
        print("\n3. 🏫 Generating University Vectors")
        print("-" * 30)
        universities_without_vectors = db.query(University).outerjoin(
            UniversityVector, University.id == UniversityVector.university_id
        ).filter(UniversityVector.id.is_(None)).limit(5).all()
        
        if universities_without_vectors:
            print(f"Found {len(universities_without_vectors)} universities without vectors")
            await vector_service.batch_generate_university_vectors(db, len(universities_without_vectors))
            print("✅ University vectors generated successfully")
        else:
            print("✅ All universities already have vectors")
        
        # 4. Demonstrate vector retrieval (no regeneration)
        print("\n4. 🔍 Demonstrating Vector Retrieval")
        print("-" * 30)
        
        # Get a user and university to test with
        user = db.query(User).first()
        university = db.query(University).first()
        
        if user and university:
            print(f"Testing with user: {user.email}")
            print(f"Testing with university: {university.name}")
            
            # First call - should generate and store vectors
            print("\nFirst call (generating vectors)...")
            start_time = asyncio.get_event_loop().time()
            user_embedding1 = await vector_service.generate_user_embedding(user, db)
            university_embedding1 = await vector_service.generate_university_embedding(university, db)
            first_call_time = asyncio.get_event_loop().time() - start_time
            
            print(f"First call completed in {first_call_time:.2f} seconds")
            print(f"User embedding dimensions: {len(user_embedding1)}")
            print(f"University embedding dimensions: {len(university_embedding1)}")
            
            # Second call - should retrieve stored vectors
            print("\nSecond call (retrieving stored vectors)...")
            start_time = asyncio.get_event_loop().time()
            user_embedding2 = await vector_service.generate_user_embedding(user, db)
            university_embedding2 = await vector_service.generate_university_embedding(university, db)
            second_call_time = asyncio.get_event_loop().time() - start_time
            
            print(f"Second call completed in {second_call_time:.2f} seconds")
            print(f"Speed improvement: {first_call_time/second_call_time:.1f}x faster")
            
            # Verify embeddings are identical
            user_identical = user_embedding1 == user_embedding2
            university_identical = university_embedding1 == university_embedding2
            print(f"User embeddings identical: {user_identical}")
            print(f"University embeddings identical: {university_identical}")
        
        # 5. Demonstrate caching
        print("\n5. 💾 Demonstrating Caching")
        print("-" * 30)
        
        # Clean up expired cache first
        await vector_service.cleanup_expired_cache(db)
        
        # Check cache statistics
        cache_stats = db.query(VectorSearchCache).count()
        print(f"Active cache entries: {cache_stats}")
        
        # 6. Performance metrics
        print("\n6. 📈 Performance Metrics")
        print("-" * 30)
        performance = await vector_service.get_vector_performance_metrics(db)
        
        print(f"Average user vector dimensions: {performance['performance_metrics']['average_user_vector_dimensions']:.0f}")
        print(f"Average university vector dimensions: {performance['performance_metrics']['average_university_vector_dimensions']:.0f}")
        print(f"Cache utilization rate: {performance['performance_metrics']['cache_utilization_rate']:.1f}%")
        print(f"Total vectors stored: {performance['storage_efficiency']['total_vectors_stored']}")
        
        # 7. Optimization demonstration
        print("\n7. ⚡ Optimization Demo")
        print("-" * 30)
        
        optimization_results = await vector_service.optimize_vector_storage(db)
        print(f"Invalid user vectors removed: {optimization_results['invalid_user_vectors_removed']}")
        print(f"Invalid university vectors removed: {optimization_results['invalid_university_vectors_removed']}")
        print(f"User vectors regenerated: {optimization_results['user_vectors_regenerated']}")
        print(f"University vectors regenerated: {optimization_results['university_vectors_regenerated']}")
        print(f"Cache entries cleaned: {optimization_results['cache_entries_cleaned']}")
        
        print("\n✅ Vector storage demo completed successfully!")
        
    except Exception as e:
        print(f"❌ Error during demo: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        db.close()

async def demo_matching_with_caching():
    """Demonstrate matching with caching"""
    
    print("\n🎯 Matching with Caching Demo")
    print("=" * 50)
    
    db = next(get_db())
    vector_service = VectorMatchingService()
    
    try:
        # Get a user with personality profile
        user = db.query(User).filter(User.personality_profile.isnot(None)).first()
        
        if not user:
            print("❌ No user with personality profile found. Please complete questionnaire first.")
            return
        
        print(f"Testing matching with user: {user.email}")
        
        # First matching call
        print("\nFirst matching call (generating and caching)...")
        start_time = asyncio.get_event_loop().time()
        matches1 = await vector_service.find_matches_with_cache(user, db, limit=5)
        first_call_time = asyncio.get_event_loop().time() - start_time
        
        print(f"Generated {len(matches1)} matches in {first_call_time:.2f} seconds")
        
        # Second matching call (should use cache)
        print("\nSecond matching call (using cache)...")
        start_time = asyncio.get_event_loop().time()
        matches2 = await vector_service.find_matches_with_cache(user, db, limit=5)
        second_call_time = asyncio.get_event_loop().time() - start_time
        
        print(f"Retrieved {len(matches2)} matches in {second_call_time:.2f} seconds")
        print(f"Speed improvement: {first_call_time/second_call_time:.1f}x faster")
        
        # Verify results are identical
        identical = len(matches1) == len(matches2)
        if identical:
            for i, (m1, m2) in enumerate(zip(matches1, matches2)):
                if m1['university_id'] != m2['university_id'] or abs(m1['similarity_score'] - m2['similarity_score']) > 0.001:
                    identical = False
                    break
        
        print(f"Results identical: {identical}")
        
        print("\n✅ Matching with caching demo completed successfully!")
        
    except Exception as e:
        print(f"❌ Error during matching demo: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        db.close()

async def main():
    """Main demo function"""
    print("🎓 University Matching App - Vector Storage Demo")
    print("=" * 60)
    
    await demo_vector_storage()
    await demo_matching_with_caching()
    
    print("\n🎉 All demos completed!")
    print("\nKey Benefits of Vector Storage:")
    print("✅ Vectors are stored in database to avoid regeneration")
    print("✅ In-memory caching for frequently accessed vectors")
    print("✅ Search results are cached to avoid redundant computations")
    print("✅ Automatic vector invalidation when profiles change")
    print("✅ Batch vector generation for efficiency")
    print("✅ Performance monitoring and optimization tools")

if __name__ == "__main__":
    asyncio.run(main()) 