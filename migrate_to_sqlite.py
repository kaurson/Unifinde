#!/usr/bin/env python3
"""
Migration script to move data from MySQL to SQLite database in project root
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def migrate_database():
    """Migrate data from MySQL to SQLite"""
    print("🔄 Starting database migration from MySQL to SQLite...")
    
    # Temporarily set MySQL URL for reading
    original_url = os.getenv("DATABASE_URL")
    os.environ["DATABASE_URL"] = "mysql+pymysql://root@localhost:3306/uniapp"
    
    try:
        # Import MySQL database connection
        from database.database import get_db as get_mysql_db
        from database.models import UniversityDataCollectionResult
        
        print("📖 Reading data from MySQL database...")
        mysql_db = next(get_mysql_db())
        
        # Get all data from MySQL
        mysql_results = mysql_db.query(UniversityDataCollectionResult).all()
        print(f"📊 Found {len(mysql_results)} records in MySQL database")
        
        # Close MySQL connection
        mysql_db.close()
        
        # Switch to SQLite
        print("🔄 Switching to SQLite database...")
        os.environ["DATABASE_URL"] = "sqlite:///./uniapp.db"
        
        # Import SQLite database connection
        from database.database import get_db as get_sqlite_db, init_db
        
        # Initialize SQLite database
        print("🔧 Creating SQLite database...")
        init_db()
        
        # Get SQLite connection
        sqlite_db = next(get_sqlite_db())
        
        # Clear existing data to avoid duplicates
        print("🧹 Clearing existing data from SQLite database...")
        sqlite_db.query(UniversityDataCollectionResult).delete()
        sqlite_db.commit()
        
        # Migrate data
        print("📝 Migrating data to SQLite...")
        migrated_count = 0
        
        for mysql_result in mysql_results:
            # Create new record in SQLite
            sqlite_result = UniversityDataCollectionResult(
                id=mysql_result.id,
                total_universities=mysql_result.total_universities,
                successful_collections=mysql_result.successful_collections,
                failed_collections=mysql_result.failed_collections,
                generated_at=mysql_result.generated_at,
                script_version=mysql_result.script_version,
                success=mysql_result.success,
                data_collection_id=mysql_result.data_collection_id,
                name=mysql_result.name,
                website=mysql_result.website,
                country=mysql_result.country,
                city=mysql_result.city,
                state=mysql_result.state,
                phone=mysql_result.phone,
                email=mysql_result.email,
                founded_year=mysql_result.founded_year,
                type=mysql_result.type,
                student_population=mysql_result.student_population,
                undergraduate_population=mysql_result.undergraduate_population,
                graduate_population=mysql_result.graduate_population,
                international_students_percentage=mysql_result.international_students_percentage,
                faculty_count=mysql_result.faculty_count,
                student_faculty_ratio=mysql_result.student_faculty_ratio,
                acceptance_rate=mysql_result.acceptance_rate,
                tuition_domestic=mysql_result.tuition_domestic,
                tuition_international=mysql_result.tuition_international,
                room_and_board=mysql_result.room_and_board,
                total_cost_of_attendance=mysql_result.total_cost_of_attendance,
                financial_aid_available=mysql_result.financial_aid_available,
                average_financial_aid_package=mysql_result.average_financial_aid_package,
                scholarships_available=mysql_result.scholarships_available,
                world_ranking=mysql_result.world_ranking,
                national_ranking=mysql_result.national_ranking,
                regional_ranking=mysql_result.regional_ranking,
                subject_rankings=mysql_result.subject_rankings,
                description=mysql_result.description,
                mission_statement=mysql_result.mission_statement,
                vision_statement=mysql_result.vision_statement,
                campus_size=mysql_result.campus_size,
                campus_type=mysql_result.campus_type,
                climate=mysql_result.climate,
                timezone=mysql_result.timezone,
                programs=mysql_result.programs,
                student_life=mysql_result.student_life,
                financial_aid=mysql_result.financial_aid,
                international_students=mysql_result.international_students,
                alumni=mysql_result.alumni,
                confidence_score=mysql_result.confidence_score,
                source_urls=mysql_result.source_urls,
                last_updated=mysql_result.last_updated,
                created_at=mysql_result.created_at,
                updated_at=mysql_result.updated_at
            )
            
            sqlite_db.add(sqlite_result)
            migrated_count += 1
        
        # Commit the migration
        sqlite_db.commit()
        sqlite_db.close()
        
        print(f"✅ Successfully migrated {migrated_count} records to SQLite database")
        print(f"📁 Database file created at: {Path.cwd() / 'uniapp.db'}")
        
        # Verify the migration
        print("🔍 Verifying migration...")
        verify_migration()
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        # Restore original URL
        if original_url:
            os.environ["DATABASE_URL"] = original_url
        return False
    
    # Update .env file
    update_env_file()
    
    return True

def verify_migration():
    """Verify that the migration was successful"""
    try:
        from database.database import get_db
        from database.models import UniversityDataCollectionResult
        
        db = next(get_db())
        results = db.query(UniversityDataCollectionResult).all()
        print(f"✅ Verification successful: {len(results)} records found in SQLite database")
        
        # Show some sample data
        if results:
            print("📋 Sample data:")
            for result in results[:3]:  # Show first 3 records
                print(f"  - {result.name} (Confidence: {result.confidence_score})")
        
        db.close()
        
    except Exception as e:
        print(f"❌ Verification failed: {e}")

def update_env_file():
    """Update the .env file to use SQLite"""
    env_file = Path(".env")
    if env_file.exists():
        print("📝 Updating .env file to use SQLite...")
        
        # Read current content
        with open(env_file, 'r') as f:
            content = f.read()
        
        # Replace MySQL URL with SQLite URL
        content = content.replace(
            "DATABASE_URL=mysql+pymysql://root@localhost:3306/uniapp",
            "DATABASE_URL=sqlite:///./uniapp.db"
        )
        
        # Write back
        with open(env_file, 'w') as f:
            f.write(content)
        
        print("✅ .env file updated successfully")

if __name__ == "__main__":
    success = migrate_database()
    if success:
        print("\n🎉 Migration completed successfully!")
        print("📁 Your database is now located at: ./uniapp.db")
        print("🔧 You can now run your data collection scripts with the local SQLite database")
    else:
        print("\n❌ Migration failed. Please check the error messages above.")
        sys.exit(1) 