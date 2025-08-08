#!/usr/bin/env python3
"""
Analyze Database Fields Script
Identifies which fields are most commonly empty or missing data
"""

import sys
import os
from sqlalchemy import func
from rich.console import Console
from rich.table import Table

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.models import UniversityDataCollectionResult
from database.database import get_db

console = Console()

def analyze_database_fields():
    """Analyze which fields are most commonly empty in the database"""
    
    try:
        db_session = next(get_db())
        
        # Get total count of universities
        total_universities = db_session.query(UniversityDataCollectionResult).count()
        console.print(f"📊 Analyzing {total_universities} universities in database...")
        
        # Define fields to analyze
        fields_to_analyze = [
            'name', 'website', 'country', 'city', 'state', 'phone', 'email',
            'founded_year', 'type', 'student_population', 'undergraduate_population',
            'graduate_population', 'international_students_percentage', 'faculty_count',
            'student_faculty_ratio', 'acceptance_rate', 'tuition_domestic',
            'tuition_international', 'room_and_board', 'total_cost_of_attendance',
            'financial_aid_available', 'average_financial_aid_package',
            'scholarships_available', 'world_ranking', 'national_ranking',
            'regional_ranking', 'subject_rankings', 'description', 'mission_statement',
            'vision_statement', 'campus_size', 'campus_type', 'climate', 'timezone',
            'programs', 'student_life', 'financial_aid', 'international_students',
            'alumni', 'confidence_score', 'source_urls'
        ]
        
        # Create analysis table
        table = Table(title="Database Field Analysis")
        table.add_column("Field", style="cyan")
        table.add_column("Filled Count", style="green")
        table.add_column("Empty Count", style="red")
        table.add_column("Fill Rate %", style="yellow")
        table.add_column("Status", style="magenta")
        
        field_analysis = []
        
        for field in fields_to_analyze:
            # Count non-null values
            filled_count = db_session.query(func.count(getattr(UniversityDataCollectionResult, field))).filter(
                getattr(UniversityDataCollectionResult, field).isnot(None)
            ).scalar()
            
            empty_count = total_universities - filled_count
            fill_rate = (filled_count / total_universities * 100) if total_universities > 0 else 0
            
            # Determine status
            if fill_rate >= 90:
                status = "✅ Excellent"
            elif fill_rate >= 70:
                status = "🟡 Good"
            elif fill_rate >= 50:
                status = "🟠 Fair"
            else:
                status = "🔴 Poor"
            
            field_analysis.append({
                'field': field,
                'filled': filled_count,
                'empty': empty_count,
                'rate': fill_rate,
                'status': status
            })
            
            table.add_row(
                field,
                str(filled_count),
                str(empty_count),
                f"{fill_rate:.1f}%",
                status
            )
        
        console.print(table)
        
        # Show summary
        console.print(f"\n📈 Summary:")
        excellent = len([f for f in field_analysis if f['rate'] >= 90])
        good = len([f for f in field_analysis if 70 <= f['rate'] < 90])
        fair = len([f for f in field_analysis if 50 <= f['rate'] < 70])
        poor = len([f for f in field_analysis if f['rate'] < 50])
        
        console.print(f"✅ Excellent (90%+): {excellent} fields")
        console.print(f"🟡 Good (70-89%): {good} fields")
        console.print(f"🟠 Fair (50-69%): {fair} fields")
        console.print(f"🔴 Poor (<50%): {poor} fields")
        
        # Show worst fields
        console.print(f"\n🔴 Fields needing most attention:")
        worst_fields = sorted(field_analysis, key=lambda x: x['rate'])[:10]
        for field in worst_fields:
            console.print(f"   {field['field']}: {field['rate']:.1f}% filled ({field['empty']} empty)")
        
        # Show sample data for a few universities
        console.print(f"\n📋 Sample data from first 3 universities:")
        sample_universities = db_session.query(UniversityDataCollectionResult).limit(3).all()
        
        for i, uni in enumerate(sample_universities, 1):
            console.print(f"\n   University {i}: {uni.name}")
            console.print(f"   - Website: {uni.website or 'N/A'}")
            console.print(f"   - Student Population: {uni.student_population or 'N/A'}")
            console.print(f"   - Acceptance Rate: {uni.acceptance_rate or 'N/A'}")
            console.print(f"   - Tuition Domestic: {uni.tuition_domestic or 'N/A'}")
            console.print(f"   - Tuition International: {uni.tuition_international or 'N/A'}")
            console.print(f"   - Faculty Count: {uni.faculty_count or 'N/A'}")
            console.print(f"   - Confidence Score: {uni.confidence_score or 'N/A'}")
        
        db_session.close()
        
    except Exception as e:
        console.print(f"❌ Error analyzing database: {e}")

if __name__ == "__main__":
    analyze_database_fields() 