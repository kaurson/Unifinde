#!/usr/bin/env python3
"""
Script to create a new table for storing vectors from university data collection results.
This table will not have foreign key constraints to the universities table.
"""

import sys
import os
from datetime import datetime
import uuid

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.database import get_db
from sqlalchemy import Column, String, LargeBinary, Integer, Text, DateTime, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import numpy as np

# Create a new base for this table
Base = declarative_base()

class CollectionVector(Base):
    """Model for storing university embeddings from collection results"""
    __tablename__ = 'collection_vectors'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    collection_result_id = Column(String(36), nullable=False)  # Reference to collection result
    university_name = Column(String(200), nullable=False)  # University name from collection
    
    # Vector data
    embedding = Column(LargeBinary, nullable=False)  # Stored as numpy array bytes
    embedding_dimension = Column(Integer, nullable=False)  # Dimension of the embedding vector
    embedding_model = Column(String(100), nullable=False)  # Model used to generate embedding
    
    # Source text that was embedded
    source_text = Column(Text, nullable=False)  # The text that was used to generate the embedding
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self) -> str:
        return f'<CollectionVector {self.university_name}>'
    
    def get_embedding_array(self) -> np.ndarray:
        """Convert stored bytes back to numpy array"""
        return np.frombuffer(self.embedding, dtype=np.float32)
    
    def set_embedding_array(self, embedding_array: np.ndarray) -> None:
        """Convert numpy array to bytes for storage"""
        self.embedding = embedding_array.tobytes()
        self.embedding_dimension = len(embedding_array)

def create_collection_vectors_table():
    """Create the collection_vectors table"""
    
    print("🏗️  Creating Collection Vectors Table")
    print("=" * 40)
    
    # Get database engine
    from database.database import engine
    
    try:
        # Create the table
        Base.metadata.create_all(bind=engine)
        print("✅ Collection vectors table created successfully!")
        
        # Verify table exists
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        if 'collection_vectors' in tables:
            print("✅ Table 'collection_vectors' verified in database")
        else:
            print("❌ Table 'collection_vectors' not found in database")
            
    except Exception as e:
        print(f"❌ Error creating table: {e}")
        import traceback
        traceback.print_exc()

def drop_collection_vectors_table():
    """Drop the collection_vectors table"""
    
    print("🗑️  Dropping Collection Vectors Table")
    print("=" * 40)
    
    # Get database engine
    from database.database import engine
    
    try:
        # Drop the table
        Base.metadata.drop_all(bind=engine)
        print("✅ Collection vectors table dropped successfully!")
        
    except Exception as e:
        print(f"❌ Error dropping table: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Create collection vectors table")
    parser.add_argument("--create", action="store_true", help="Create collection vectors table")
    parser.add_argument("--drop", action="store_true", help="Drop collection vectors table")
    
    args = parser.parse_args()
    
    if args.create:
        create_collection_vectors_table()
    elif args.drop:
        drop_collection_vectors_table()
    else:
        print("Please specify an option:")
        print("  --create : Create collection vectors table")
        print("  --drop   : Drop collection vectors table")
        print("\nExample: python3 create_collection_vectors_table.py --create") 