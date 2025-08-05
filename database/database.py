from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
import os
from typing import Generator
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL")

# Check if we should use SQLite fallback
USE_SQLITE_FALLBACK = os.getenv("USE_SQLITE_FALLBACK", "false").lower() == "true"

if not DATABASE_URL or USE_SQLITE_FALLBACK:
    print("🔧 Using SQLite database (fallback mode)")
    DATABASE_URL = "sqlite:///./universities.db"
    
    # Create engine for SQLite
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
else:
    print(f"🔧 Attempting to connect to Supabase database...")
    print(f"📋 DATABASE_URL: {DATABASE_URL[:50]}...")
    
    # Create engine for PostgreSQL (Supabase)
    try:
        engine = create_engine(
            DATABASE_URL,
            pool_pre_ping=True,
            pool_recycle=300,
            echo=False  # Disable SQL logging for cleaner output
        )
        print("✅ Supabase engine created successfully")
    except Exception as e:
        print(f"❌ Failed to connect to Supabase: {e}")
        print("🔄 Falling back to SQLite database...")
        
        # Fallback to SQLite
        DATABASE_URL = "sqlite:///./universities.db"
        engine = create_engine(
            DATABASE_URL,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        print("✅ SQLite fallback engine created successfully")

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