#!/usr/bin/env python3
"""
Script to create database tables for university data collection
"""

import sys
import os
from sqlalchemy import create_engine, text, inspect

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.database import get_db
from database.models import Base, UniversityDataCollection, UniversitySearchTask, LLMAnalysisResult

def create_tables():
    """Create all database tables"""
    print("Creating database tables...")
    
    # Get database session
    db_session = next(get_db())
    
    try:
        # Create all tables
        Base.metadata.create_all(bind=db_session.bind)
        print("✅ All tables created successfully!")
        
        # Verify tables exist
        inspector = inspect(db_session.bind)
        tables = inspector.get_table_names()
        print(f"Available tables: {tables}")
        
        # Check for our specific tables
        required_tables = [
            'university_data_collections',
            'university_search_tasks', 
            'llm_analysis_results'
        ]
        
        for table in required_tables:
            if table in tables:
                print(f"✅ Table '{table}' exists")
            else:
                print(f"❌ Table '{table}' missing")
                
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        return False
    finally:
        db_session.close()
    
    return True

if __name__ == "__main__":
    create_tables() 