#!/usr/bin/env python3
"""
Regenerate User Vectors Script

This script regenerates all user vectors with improved cleaning to fix corrupted embeddings.
"""

import asyncio
import sys
import os
import numpy as np
from sqlalchemy.orm import Session

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.database import get_db
from database.models import UserVector, User
from api.vector_matcher import VectorMatchingService

async def regenerate_user_vectors():
    """Regenerate all user vectors with improved cleaning"""
    
    print("🔄 Regenerating User Vectors")
    print("=" * 50)
    
    # Get database session
    db = next(get_db())
    vector_service = VectorMatchingService()
    
    try:
        # Get all users
        users = db.query(User).all()
        print(f"Found {len(users)} users to process")
        
        regenerated_count = 0
        skipped_count = 0
        
        for i, user in enumerate(users):
            print(f"Processing user {i+1}/{len(users)}: {user.email}")
            
            try:
                # Delete existing user vector
                existing_vector = db.query(UserVector).filter(UserVector.user_id == user.id).first()
                if existing_vector:
                    db.delete(existing_vector)
                    db.commit()
                    print(f"  Deleted existing vector for {user.email}")
                
                # Generate new user embedding
                user_embedding = await vector_service.generate_user_embedding(user, db)
                
                # Validate the new embedding
                if vector_service._is_valid_embedding(user_embedding):
                    print(f"  ✅ Generated valid embedding for {user.email}")
                    print(f"    Dimensions: {len(user_embedding)}")
                    print(f"    Mean: {np.mean(user_embedding):.6f}")
                    print(f"    Std: {np.std(user_embedding):.6f}")
                    print(f"    Min: {np.min(user_embedding):.6f}")
                    print(f"    Max: {np.max(user_embedding):.6f}")
                    regenerated_count += 1
                else:
                    print(f"  ❌ Failed to generate valid embedding for {user.email}")
                    skipped_count += 1
                    
            except Exception as e:
                print(f"  ❌ Error processing user {user.email}: {e}")
                skipped_count += 1
                continue
        
        print(f"\n✅ User vectors regeneration completed!")
        print(f"Regenerated: {regenerated_count}")
        print(f"Skipped: {skipped_count}")
        print(f"Total: {len(users)}")
        
        # Test the results
        print(f"\n🧪 Testing Results")
        print("-" * 30)
        
        test_user = db.query(User).first()
        if test_user:
            test_embedding = await vector_service.generate_user_embedding(test_user, db)
            print(f"Test user: {test_user.email}")
            print(f"Test embedding dimensions: {len(test_embedding)}")
            print(f"Test embedding mean: {np.mean(test_embedding):.6f}")
            print(f"Test embedding std: {np.std(test_embedding):.6f}")
            print(f"Test embedding min: {np.min(test_embedding):.6f}")
            print(f"Test embedding max: {np.max(test_embedding):.6f}")
            print(f"Test embedding valid: {vector_service._is_valid_embedding(test_embedding)}")
        
    except Exception as e:
        print(f"❌ Error during user vector regeneration: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        db.close()

async def main():
    """Main function"""
    print("🎓 University Matching App - Regenerate User Vectors")
    print("=" * 60)
    
    await regenerate_user_vectors()
    
    print("\n🎉 User vectors regeneration completed!")

if __name__ == "__main__":
    asyncio.run(main()) 