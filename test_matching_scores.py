#!/usr/bin/env python3
"""
Test Matching Scores Script

This script tests the matching system to show actual similarity scores.
"""

import asyncio
import sys
import os

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.database import get_db
from database.models import User
from api.vector_matcher import VectorMatchingService

async def test_matching_scores():
    """Test matching scores to show actual similarity values"""
    
    print("🎯 Testing Matching Scores")
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
        
        print(f"Testing with user: {user.email}")
        print(f"User name: {user.name}")
        if user.preferred_majors:
            print(f"Preferred majors: {', '.join(user.preferred_majors)}")
        if user.preferred_locations:
            print(f"Preferred locations: {', '.join(user.preferred_locations)}")
        
        print("\n🔍 Generating matches...")
        
        # Generate matches
        matches = await vector_service.find_collection_matches(user, db, limit=10)
        
        print(f"\n✅ Generated {len(matches)} matches")
        print("\n📊 Top 10 Matches:")
        print("-" * 80)
        
        for i, match in enumerate(matches):
            print(f"{i+1:2d}. {match['university_name']}")
            print(f"     Similarity: {match['similarity_score']:.6f}")
            print(f"     Location: {match['university_data'].get('city', 'N/A')}, {match['university_data'].get('country', 'N/A')}")
            print(f"     Type: {match['university_data'].get('type', 'N/A')}")
            if match['match_reasons']:
                print(f"     Reasons: {match['match_reasons'][0] if match['match_reasons'] else 'N/A'}")
            print()
        
        # Show similarity score distribution
        similarities = [match['similarity_score'] for match in matches]
        print(f"📈 Similarity Score Statistics:")
        print(f"   Min: {min(similarities):.6f}")
        print(f"   Max: {max(similarities):.6f}")
        print(f"   Mean: {sum(similarities)/len(similarities):.6f}")
        print(f"   Range: {max(similarities) - min(similarities):.6f}")
        
        # Check if scores are reasonable
        if max(similarities) > 0.9:
            print("⚠️  WARNING: Some similarity scores are very high (>0.9)")
        elif max(similarities) < 0.01:
            print("⚠️  WARNING: All similarity scores are very low (<0.01)")
        else:
            print("✅ Similarity scores look reasonable")
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        db.close()

async def main():
    """Main function"""
    print("🎓 University Matching App - Test Matching Scores")
    print("=" * 60)
    
    await test_matching_scores()
    
    print("\n🎉 Testing completed!")

if __name__ == "__main__":
    asyncio.run(main()) 