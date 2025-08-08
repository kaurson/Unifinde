#!/usr/bin/env python3
"""
Script to clean up problematic collection result vectors
"""

import sys
import os
import numpy as np
from sqlalchemy.orm import Session

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.database import get_db, engine
from database.models import CollectionResultVector, UniversityDataCollectionResult

def clean_problematic_vectors():
    """Remove vectors with NaN values or incorrect dimensions"""
    
    db = next(get_db())
    
    try:
        # Get all vectors
        vectors = db.query(CollectionResultVector).all()
        print(f"Found {len(vectors)} vectors to check")
        
        problematic_count = 0
        valid_count = 0
        
        for i, vector in enumerate(vectors):
            try:
                # Get embedding array
                embedding = vector.get_embedding_array()
                
                # Check dimensions
                if len(embedding) != 1536:
                    print(f"Vector {i+1} ({vector.collection_result_id}): Wrong dimensions {len(embedding)}")
                    problematic_count += 1
                    continue
                
                # Check for NaN values
                if np.isnan(embedding).any():
                    print(f"Vector {i+1} ({vector.collection_result_id}): Contains NaN values")
                    problematic_count += 1
                    continue
                
                valid_count += 1
                
            except Exception as e:
                print(f"Vector {i+1} ({vector.collection_result_id}): Error - {e}")
                problematic_count += 1
                continue
        
        print(f"\nSummary:")
        print(f"Valid vectors: {valid_count}")
        print(f"Problematic vectors: {problematic_count}")
        print(f"Total vectors: {len(vectors)}")
        
        if problematic_count > 0:
            print(f"\nRecommendation: Consider regenerating vectors for the problematic entries")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    clean_problematic_vectors() 