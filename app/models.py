from sqlalchemy import Column, Integer, String, Text, DateTime, Float, Boolean, ForeignKey
from sqlalchemy.orm import DeclarativeBase, relationship
from sqlalchemy.sql import func
from typing import Optional, List, Dict, Any
import json

class Base(DeclarativeBase):
    pass

class University(Base):
    __tablename__ = 'universities'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False, index=True)
    website = Column(String(500), nullable=True)
    country = Column(String(100), nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    postal_code = Column(String(20), nullable=True)
    phone = Column(String(50), nullable=True)
    email = Column(String(200), nullable=True)
    
    # Academic information
    founded_year = Column(Integer, nullable=True)
    type = Column(String(100), nullable=True)  # Public, Private, etc.
    accreditation = Column(Text, nullable=True)
    
    # Statistics
    student_population = Column(Integer, nullable=True)
    faculty_count = Column(Integer, nullable=True)
    acceptance_rate = Column(Float, nullable=True)
    tuition_domestic = Column(Float, nullable=True)
    tuition_international = Column(Float, nullable=True)
    
    # Rankings and reputation
    world_ranking = Column(Integer, nullable=True)
    national_ranking = Column(Integer, nullable=True)
    
    # Additional data
    description = Column(Text, nullable=True)
    mission_statement = Column(Text, nullable=True)
    vision_statement = Column(Text, nullable=True)
    
    # Metadata
    scraped_at = Column(DateTime(timezone=True), server_default=func.now())
    last_updated = Column(DateTime(timezone=True), onupdate=func.now())
    source_url = Column(String(500), nullable=True)
    confidence_score = Column(Float, default=0.0)
    
    # Relationships
    programs = relationship("Program", back_populates="university", cascade="all, delete-orphan")
    facilities = relationship("Facility", back_populates="university", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f'<University {self.name}>'
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert university object to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'website': self.website,
            'country': self.country,
            'city': self.city,
            'state': self.state,
            'postal_code': self.postal_code,
            'phone': self.phone,
            'email': self.email,
            'founded_year': self.founded_year,
            'type': self.type,
            'accreditation': self.accreditation,
            'student_population': self.student_population,
            'faculty_count': self.faculty_count,
            'acceptance_rate': self.acceptance_rate,
            'tuition_domestic': self.tuition_domestic,
            'tuition_international': self.tuition_international,
            'world_ranking': self.world_ranking,
            'national_ranking': self.national_ranking,
            'description': self.description,
            'mission_statement': self.mission_statement,
            'vision_statement': self.vision_statement,
            'scraped_at': self.scraped_at.isoformat() if self.scraped_at else None,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None,
            'source_url': self.source_url,
            'confidence_score': self.confidence_score,
            'programs': [program.to_dict() for program in self.programs],
            'facilities': [facility.to_dict() for facility in self.facilities]
        }

class Program(Base):
    __tablename__ = 'programs'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    university_id = Column(Integer, ForeignKey('universities.id'), nullable=False)
    name = Column(String(200), nullable=False)
    level = Column(String(50), nullable=True)  # Bachelor, Master, PhD, etc.
    field = Column(String(100), nullable=True)  # Computer Science, Engineering, etc.
    duration = Column(String(50), nullable=True)  # 4 years, 2 years, etc.
    tuition = Column(Float, nullable=True)
    description = Column(Text, nullable=True)
    requirements = Column(Text, nullable=True)
    
    university = relationship("University", back_populates="programs")
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'university_id': self.university_id,
            'name': self.name,
            'level': self.level,
            'field': self.field,
            'duration': self.duration,
            'tuition': self.tuition,
            'description': self.description,
            'requirements': self.requirements
        }

class Facility(Base):
    __tablename__ = 'facilities'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    university_id = Column(Integer, ForeignKey('universities.id'), nullable=False)
    name = Column(String(200), nullable=False)
    type = Column(String(100), nullable=True)  # Library, Lab, Sports, etc.
    description = Column(Text, nullable=True)
    capacity = Column(Integer, nullable=True)
    
    university = relationship("University", back_populates="facilities")
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'university_id': self.university_id,
            'name': self.name,
            'type': self.type,
            'description': self.description,
            'capacity': self.capacity
        } 