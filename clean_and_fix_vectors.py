#!/usr/bin/env python3
"""
Script to clean and fix collection result vectors by removing NaN values
"""

import sys
import os
import numpy as np
import json
from sqlalchemy.orm import Session

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.database import get_db, engine
from database.models import CollectionResultVector, UniversityDataCollectionResult

def clean_and_fix_vectors():
    """Clean vectors by removing NaN values and fixing embedding data"""
    
    db = next(get_db())
    
    try:
        # Get all vectors
        vectors = db.query(CollectionResultVector).all()
        print(f"Found {len(vectors)} vectors to clean")
        
        fixed_count = 0
        deleted_count = 0
        
        for i, vector in enumerate(vectors):
            try:
                # Get embedding array
                embedding = vector.get_embedding_array()
                
                # Check if embedding has NaN values
                if np.isnan(embedding).any():
                    print(f"Vector {i+1} ({vector.collection_result_id}): Contains NaN values, cleaning...")
                    
                    # Clean the embedding by replacing NaN with 0
                    cleaned_embedding = np.nan_to_num(embedding, nan=0.0, posinf=0.0, neginf=0.0)
                    
                    # Convert back to list and update the vector
                    cleaned_list = cleaned_embedding.tolist()
                    
                    # Update the vector data
                    vector.embedding_data = json.dumps(cleaned_list)
                    vector.embedding_dimension = len(cleaned_list)
                    
                    fixed_count += 1
                    print(f"  ✅ Fixed vector {i+1}")
                    
                else:
                    print(f"Vector {i+1} ({vector.collection_result_id}): No NaN values found")
                
            except Exception as e:
                print(f"Vector {i+1} ({vector.collection_result_id}): Error - {e}")
                # Delete problematic vectors
                db.delete(vector)
                deleted_count += 1
                continue
        
        # Commit all changes
        db.commit()
        
        print(f"\nSummary:")
        print(f"Fixed vectors: {fixed_count}")
        print(f"Deleted vectors: {deleted_count}")
        print(f"Total processed: {len(vectors)}")
        
        # Verify the fix
        print(f"\nVerifying fix...")
        verify_vectors()
        
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

def verify_vectors():
    """Verify that vectors are now clean"""
    
    db = next(get_db())
    
    try:
        vectors = db.query(CollectionResultVector).all()
        print(f"Verifying {len(vectors)} vectors...")
        
        clean_count = 0
        problematic_count = 0
        
        for i, vector in enumerate(vectors):
            try:
                embedding = vector.get_embedding_array()
                
                if np.isnan(embedding).any():
                    print(f"❌ Vector {i+1} still has NaN values")
                    problematic_count += 1
                else:
                    clean_count += 1
                    
            except Exception as e:
                print(f"❌ Vector {i+1} error: {e}")
                problematic_count += 1
        
        print(f"\nVerification Results:")
        print(f"Clean vectors: {clean_count}")
        print(f"Problematic vectors: {problematic_count}")
        
        if problematic_count == 0:
            print("✅ All vectors are now clean!")
        else:
            print("❌ Some vectors still have issues")
            
    except Exception as e:
        print(f"Verification error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    clean_and_fix_vectors() 