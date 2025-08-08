#!/usr/bin/env python3
"""
Script to delete a specific record from the university_data_collection_results table
"""

from database.database import get_db
from database.models import UniversityDataCollectionResult

def delete_record_by_id(record_id):
    """Delete a record by its ID"""
    db = next(get_db())
    try:
        record = db.query(UniversityDataCollectionResult).filter_by(id=record_id).first()
        if record:
            print(f"Found record: {record.name} (ID: {record.id})")
            db.delete(record)
            db.commit()
            print("✅ Record deleted successfully")
        else:
            print("❌ Record not found")
    except Exception as e:
        print(f"❌ Error deleting record: {e}")
        db.rollback()
    finally:
        db.close()

def delete_second_record():
    """Delete the second record in the table"""
    db = next(get_db())
    try:
        # Get all records ordered by creation date
        records = db.query(UniversityDataCollectionResult).order_by(UniversityDataCollectionResult.created_at).all()
        
        if len(records) >= 2:
            second_record = records[1]  # Index 1 is the second record
            print(f"Deleting second record: {second_record.name} (ID: {second_record.id})")
            db.delete(second_record)
            db.commit()
            print("✅ Second record deleted successfully")
        else:
            print("❌ Not enough records to delete the second one")
    except Exception as e:
        print(f"❌ Error deleting second record: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    print("Deleting second record from university_data_collection_results table...")
    delete_second_record()
    
    # Show remaining records
    print("\nRemaining records:")
    db = next(get_db())
    try:
        records = db.query(UniversityDataCollectionResult).order_by(UniversityDataCollectionResult.created_at).all()
        for i, record in enumerate(records, 1):
            print(f"{i}. ID: {record.id}, Name: {record.name}, Created: {record.created_at}")
    finally:
        db.close() 