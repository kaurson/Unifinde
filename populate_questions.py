#!/usr/bin/env python3
"""
Script to populate the database with questions from user_questions.txt
"""

import os
import sys
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.models import Question
from database.database import DATABASE_URL
from sqlalchemy.orm import Session

# Load environment variables
load_dotenv()

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def read_questions_from_file(filename: str = "user_questions.txt") -> list:
    """Read questions from file and parse question types"""
    questions = []
    
    if not os.path.exists(filename):
        print(f"❌ File {filename} not found!")
        return questions
    
    with open(filename, 'r', encoding='utf-8') as file:
        lines = file.readlines()
    
    for i, line in enumerate(lines, 1):
        line = line.strip()
        if not line:
            continue
            
        # Parse question and type
        question_text = line
        question_type = 'text'  # Default
        
        # Check for different separators and extract question type
        if '—- ' in line:
            parts = line.split('—- ')
            question_text = parts[0].strip()
            question_type = parts[1].strip().lower()
        elif '— ' in line:
            parts = line.split('— ')
            question_text = parts[0].strip()
            question_type = parts[1].strip().lower()
        
        # Map question types to standardized types
        if question_type == 'true or false':
            question_type = 'boolean'
        elif question_type == 'float':
            question_type = 'float'
        elif question_type == 'integer':
            question_type = 'integer'
        elif question_type == '3 options':
            question_type = 'multiple_choice_3'
        elif question_type == '5 options':
            question_type = 'multiple_choice_5'
        elif question_type == 'scale from 0 to 10':
            question_type = 'scale_0_10'
        elif question_type == 'text':
            question_type = 'text'
        else:
            # Try to infer type from question content
            if 'true or false' in question_text.lower():
                question_type = 'boolean'
            elif 'float' in question_text.lower():
                question_type = 'float'
            elif 'integer' in question_text.lower():
                question_type = 'integer'
            elif '3 options' in question_text.lower():
                question_type = 'multiple_choice_3'
            elif '5 options' in question_text.lower():
                question_type = 'multiple_choice_5'
            elif 'scale from 0 to 10' in question_text.lower():
                question_type = 'scale_0_10'
            else:
                question_type = 'text'  # Default to text
        
        questions.append({
            'question_text': question_text,
            'order_index': i,
            'question_type': question_type,
            'category': 'personality'
        })
    
    return questions

def populate_questions(db: Session, questions: list) -> bool:
    """Populate questions table with new questions"""
    try:
        # Check if questions already exist
        existing_count = db.query(Question).count()
        if existing_count > 0:
            print(f"⚠️  Found {existing_count} existing questions in database")
            response = input("Do you want to replace them? (y/N): ").strip().lower()
            if response != 'y':
                print("❌ Operation cancelled")
                return False
            
            # Delete existing questions
            db.query(Question).delete()
            print("🗑️  Deleted existing questions")
        
        # Add new questions
        for q_data in questions:
            question = Question(
                question_text=q_data['question_text'],
                question_type=q_data['question_type'],
                category=q_data['category'],
                order_index=q_data['order_index'],
                is_active=True
            )
            db.add(question)
        
        db.commit()
        print(f"✅ Successfully added {len(questions)} questions to database")
        return True
        
    except Exception as e:
        print(f"❌ Error populating questions: {e}")
        db.rollback()
        return False

def display_questions(db: Session):
    """Display all questions in the database"""
    questions = db.query(Question).order_by(Question.order_index).all()
    
    print(f"\n📋 Questions in Database ({len(questions)} total):")
    print("=" * 60)
    
    for i, question in enumerate(questions, 1):
        print(f" {i:2d}. {question.question_text}")
        print(f"     Type: {question.question_type}, Category: {question.category}")
        print()

def main():
    print("🧪 Question Database Population Script")
    print("=" * 50)
    
    # Create database connection using the same configuration as the main app
    from database.database import engine, SessionLocal
    db = SessionLocal()
    
    try:
        # Read questions from file
        questions = read_questions_from_file()
        if not questions:
            print("❌ No questions found in file")
            return
        
        print(f"✅ Read {len(questions)} questions from user_questions.txt")
        
        # Populate database
        if populate_questions(db, questions):
            # Display questions
            display_questions(db)
        else:
            print("❌ Failed to populate questions")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    main() 