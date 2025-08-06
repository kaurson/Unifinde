from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Dict, Any
import asyncio
import os
from datetime import datetime

from database.database import get_db
from database.models import UniversityDataCollection, University, LLMAnalysisResult
from browser_use.university_scraper import UniversityDataScraper

router = APIRouter(prefix="/university-data", tags=["university-data-collection"])

# Background task to run the scraper
async def run_university_scraper(university_name: str, db_session: Session):
    """Background task to run university data scraping"""
    try:
        # Get OpenAI API key from environment
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if not openai_api_key:
            raise Exception("OPENAI_API_KEY environment variable not set")
        
        # Create scraper instance
        scraper = UniversityDataScraper(
            openai_api_key=openai_api_key,
            db_session=db_session
        )
        
        # Run the data collection
        result = await scraper.collect_university_data(university_name)
        
        # If successful, create or update university record
        if result.get("success") and result.get("extracted_data"):
            await create_or_update_university(result["extracted_data"], db_session)
            
    except Exception as e:
        print(f"Error in background task for {university_name}: {e}")
        # Update the data collection record with error
        data_collection = db_session.query(UniversityDataCollection).filter(
            UniversityDataCollection.university_name == university_name,
            UniversityDataCollection.status == "in_progress"
        ).first()
        
        if data_collection:
            data_collection.status = "failed"
            data_collection.error_message = str(e)
            data_collection.completed_at = datetime.now()
            db_session.commit()

async def create_or_update_university(extracted_data: Dict[str, Any], db_session: Session):
    """Create or update university record from extracted data"""
    try:
        university_name = extracted_data.get("name")
        if not university_name:
            return
        
        # Check if university already exists
        university = db_session.query(University).filter(
            University.name == university_name
        ).first()
        
        if not university:
            university = University(name=university_name)
            db_session.add(university)
        
        # Update university data
        university.website = extracted_data.get("website")
        university.country = extracted_data.get("country")
        university.city = extracted_data.get("city")
        university.state = extracted_data.get("state")
        university.phone = extracted_data.get("phone")
        university.email = extracted_data.get("email")
        university.founded_year = extracted_data.get("founded_year")
        university.type = extracted_data.get("type")
        university.accreditation = extracted_data.get("accreditation")
        university.student_population = extracted_data.get("student_population")
        university.faculty_count = extracted_data.get("faculty_count")
        university.acceptance_rate = extracted_data.get("acceptance_rate")
        university.tuition_domestic = extracted_data.get("tuition_domestic")
        university.tuition_international = extracted_data.get("tuition_international")
        university.world_ranking = extracted_data.get("world_ranking")
        university.national_ranking = extracted_data.get("national_ranking")
        university.description = extracted_data.get("description")
        university.mission_statement = extracted_data.get("mission_statement")
        university.vision_statement = extracted_data.get("vision_statement")
        university.last_updated = datetime.now()
        
        db_session.commit()
        
        print(f"University record created/updated: {university_name}")
        
    except Exception as e:
        print(f"Error creating/updating university: {e}")
        db_session.rollback()

@router.post("/collect")
async def collect_university_data(
    university_name: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Trigger university data collection using browser-use tool and LLM
    """
    try:
        # Check if data collection is already in progress
        existing_collection = db.query(UniversityDataCollection).filter(
            UniversityDataCollection.university_name == university_name,
            UniversityDataCollection.status.in_(["pending", "in_progress"])
        ).first()
        
        if existing_collection:
            return {
                "message": f"Data collection for {university_name} is already in progress",
                "collection_id": existing_collection.id,
                "status": existing_collection.status
            }
        
        # Create new data collection record
        data_collection = UniversityDataCollection(
            university_name=university_name,
            status="pending",
            created_at=datetime.now()
        )
        db.add(data_collection)
        db.commit()
        
        # Start background task
        background_tasks.add_task(run_university_scraper, university_name, db)
        
        return {
            "message": f"Data collection started for {university_name}",
            "collection_id": data_collection.id,
            "status": "pending"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error starting data collection: {str(e)}")

@router.get("/status/{collection_id}")
async def get_collection_status(
    collection_id: int,
    db: Session = Depends(get_db)
):
    """
    Get the status of a university data collection task
    """
    try:
        collection = db.query(UniversityDataCollection).filter(
            UniversityDataCollection.id == collection_id
        ).first()
        
        if not collection:
            raise HTTPException(status_code=404, detail="Data collection not found")
        
        return {
            "collection_id": collection.id,
            "university_name": collection.university_name,
            "status": collection.status,
            "created_at": collection.created_at,
            "started_at": collection.started_at,
            "completed_at": collection.completed_at,
            "confidence_score": collection.confidence_score,
            "error_message": collection.error_message
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting collection status: {str(e)}")

@router.get("/collections")
async def list_collections(
    status: str = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """
    List university data collections with optional filtering
    """
    try:
        query = db.query(UniversityDataCollection)
        
        if status:
            query = query.filter(UniversityDataCollection.status == status)
        
        collections = query.order_by(UniversityDataCollection.created_at.desc()).offset(offset).limit(limit).all()
        
        return {
            "collections": [
                {
                    "id": c.id,
                    "university_name": c.university_name,
                    "status": c.status,
                    "created_at": c.created_at,
                    "completed_at": c.completed_at,
                    "confidence_score": c.confidence_score
                }
                for c in collections
            ],
            "total": query.count()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing collections: {str(e)}")

@router.get("/collections/{collection_id}/results")
async def get_collection_results(
    collection_id: int,
    db: Session = Depends(get_db)
):
    """
    Get the results of a completed university data collection
    """
    try:
        collection = db.query(UniversityDataCollection).filter(
            UniversityDataCollection.id == collection_id
        ).first()
        
        if not collection:
            raise HTTPException(status_code=404, detail="Data collection not found")
        
        if collection.status != "completed":
            return {
                "message": f"Data collection is not completed yet. Current status: {collection.status}",
                "status": collection.status
            }
        
        # Get LLM analysis results
        llm_results = db.query(LLMAnalysisResult).filter(
            LLMAnalysisResult.data_collection_id == collection_id
        ).all()
        
        return {
            "collection_id": collection.id,
            "university_name": collection.university_name,
            "status": collection.status,
            "confidence_score": collection.confidence_score,
            "extracted_data": collection.extracted_data,
            "llm_analysis": collection.llm_analysis,
            "source_urls": collection.search_results,
            "llm_results": [
                {
                    "id": result.id,
                    "analysis_type": result.analysis_type,
                    "model_used": result.model_used,
                    "confidence_score": result.confidence_score,
                    "processing_time": result.processing_time,
                    "data_completeness": result.data_completeness,
                    "source_citations": result.source_citations
                }
                for result in llm_results
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting collection results: {str(e)}")

@router.delete("/collections/{collection_id}")
async def delete_collection(
    collection_id: int,
    db: Session = Depends(get_db)
):
    """
    Delete a university data collection
    """
    try:
        collection = db.query(UniversityDataCollection).filter(
            UniversityDataCollection.id == collection_id
        ).first()
        
        if not collection:
            raise HTTPException(status_code=404, detail="Data collection not found")
        
        # Delete associated LLM results
        db.query(LLMAnalysisResult).filter(
            LLMAnalysisResult.data_collection_id == collection_id
        ).delete()
        
        # Delete the collection
        db.delete(collection)
        db.commit()
        
        return {"message": f"Data collection {collection_id} deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting collection: {str(e)}")

@router.post("/collect-batch")
async def collect_multiple_universities(
    university_names: List[str],
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Trigger data collection for multiple universities
    """
    try:
        results = []
        
        for university_name in university_names:
            # Check if already in progress
            existing = db.query(UniversityDataCollection).filter(
                UniversityDataCollection.university_name == university_name,
                UniversityDataCollection.status.in_(["pending", "in_progress"])
            ).first()
            
            if existing:
                results.append({
                    "university_name": university_name,
                    "status": "already_in_progress",
                    "collection_id": existing.id
                })
                continue
            
            # Create new collection
            collection = UniversityDataCollection(
                university_name=university_name,
                status="pending"
            )
            db.add(collection)
            db.commit()
            
            # Add to background tasks
            background_tasks.add_task(run_university_scraper, university_name, db)
            
            results.append({
                "university_name": university_name,
                "status": "started",
                "collection_id": collection.id
            })
        
        return {
            "message": f"Batch collection started for {len(university_names)} universities",
            "results": results
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error starting batch collection: {str(e)}") 