from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
import os
from typing import Generator
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
load_dotenv()

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./uniapp.db")

# Check if we're using SQLite or MySQL
is_sqlite = DATABASE_URL.startswith("sqlite")
is_mysql = DATABASE_URL.startswith("mysql")

if is_sqlite:
    print("🔧 Using SQLite database")
    # Ensure the database file is created in the project root
    if DATABASE_URL.startswith("sqlite:///./"):
        # Extract the database filename
        db_filename = DATABASE_URL.replace("sqlite:///./", "")
        # Get the project root directory
        project_root = Path(__file__).parent.parent
        db_path = project_root / db_filename
        # Update the DATABASE_URL to use absolute path
        DATABASE_URL = f"sqlite:///{db_path}"
        print(f"📁 Database file will be created at: {db_path}")
    
    # Create engine for SQLite
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,  # Disable SQL logging for cleaner output
    )
elif is_mysql:
    print("🔧 Using MySQL database")
    # Create engine for MySQL
    engine = create_engine(
        DATABASE_URL,
        echo=False,  # Disable SQL logging for cleaner output
        pool_pre_ping=True,  # Verify connections before use
        pool_recycle=3600,  # Recycle connections every hour
    )
else:
    print("🔧 Using PostgreSQL database")
    # Create engine for PostgreSQL
    engine = create_engine(
        DATABASE_URL,
        echo=False,  # Disable SQL logging for cleaner output
    )

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db() -> Generator[Session, None, None]:
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Initialize database with tables"""
    from database.models import Base
    try:
        print("🔧 Creating database tables...")
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables created successfully")
    except Exception as e:
        print(f"❌ Failed to create database tables: {e}")
        raise 