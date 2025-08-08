from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from database.models import User, UserUniversitySuggestion
from datetime import datetime
import uuid


class UserSuggestionsService:
    """Service for managing user university suggestions"""
    
    def __init__(self):
        pass
    
    def save_suggestions(
        self, 
        user: User, 
        suggestions: List[Dict[str, Any]], 
        db: Session
    ) -> List[UserUniversitySuggestion]:
        """Save university suggestions for a user"""
        
        # Clear existing suggestions for this user
        db.query(UserUniversitySuggestion).filter(
            UserUniversitySuggestion.user_id == user.id
        ).delete()
        
        # Create new suggestions
        saved_suggestions = []
        for suggestion in suggestions:
            # Extract program information if available
            program_id = suggestion.get("program_id")
            program_name = suggestion.get("program_name")
            program_data = suggestion.get("program_data")
            
            # Create suggestion object
            user_suggestion = UserUniversitySuggestion(
                user_id=user.id,
                university_id=suggestion.get("university_id"),
                university_name=suggestion.get("university_name"),
                similarity_score=suggestion.get("similarity_score", 0.0),
                matching_method=suggestion.get("matching_method", "unknown"),
                confidence=suggestion.get("confidence"),
                match_reasons=suggestion.get("match_reasons"),
                user_preferences=suggestion.get("user_preferences"),
                university_data=suggestion.get("university_data"),
                program_id=program_id,
                program_name=program_name,
                program_data=program_data
            )
            
            db.add(user_suggestion)
            saved_suggestions.append(user_suggestion)
        
        db.commit()
        
        # Refresh objects to get IDs
        for suggestion in saved_suggestions:
            db.refresh(suggestion)
        
        return saved_suggestions
    
    def get_user_suggestions(
        self, 
        user: User, 
        db: Session, 
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get saved university suggestions for a user"""
        
        query = db.query(UserUniversitySuggestion).filter(
            UserUniversitySuggestion.user_id == user.id
        ).order_by(UserUniversitySuggestion.similarity_score.desc())
        
        if limit:
            query = query.limit(limit)
        
        suggestions = query.all()
        
        # Convert to dictionary format
        return [suggestion.to_dict() for suggestion in suggestions]
    
    def has_suggestions(self, user: User, db: Session) -> bool:
        """Check if user has saved suggestions"""
        count = db.query(UserUniversitySuggestion).filter(
            UserUniversitySuggestion.user_id == user.id
        ).count()
        return count > 0
    
    def clear_suggestions(self, user: User, db: Session) -> bool:
        """Clear all suggestions for a user"""
        deleted_count = db.query(UserUniversitySuggestion).filter(
            UserUniversitySuggestion.user_id == user.id
        ).delete()
        db.commit()
        return deleted_count > 0
    
    def update_suggestion(
        self, 
        suggestion_id: str, 
        updates: Dict[str, Any], 
        db: Session
    ) -> Optional[UserUniversitySuggestion]:
        """Update a specific suggestion"""
        
        suggestion = db.query(UserUniversitySuggestion).filter(
            UserUniversitySuggestion.id == suggestion_id
        ).first()
        
        if not suggestion:
            return None
        
        # Update fields
        for key, value in updates.items():
            if hasattr(suggestion, key):
                setattr(suggestion, key, value)
        
        suggestion.updated_at = datetime.now()
        db.commit()
        db.refresh(suggestion)
        
        return suggestion
    
    def get_suggestion_stats(self, user: User, db: Session) -> Dict[str, Any]:
        """Get statistics about user's suggestions"""
        
        suggestions = db.query(UserUniversitySuggestion).filter(
            UserUniversitySuggestion.user_id == user.id
        ).all()
        
        if not suggestions:
            return {
                "total_suggestions": 0,
                "average_score": 0.0,
                "highest_score": 0.0,
                "lowest_score": 0.0,
                "matching_methods": {},
                "confidence_levels": {}
            }
        
        scores = [s.similarity_score for s in suggestions]
        methods = {}
        confidence_levels = {}
        
        for suggestion in suggestions:
            # Count matching methods
            method = suggestion.matching_method
            methods[method] = methods.get(method, 0) + 1
            
            # Count confidence levels
            confidence = suggestion.confidence
            if confidence:
                confidence_levels[confidence] = confidence_levels.get(confidence, 0) + 1
        
        return {
            "total_suggestions": len(suggestions),
            "average_score": sum(scores) / len(scores),
            "highest_score": max(scores),
            "lowest_score": min(scores),
            "matching_methods": methods,
            "confidence_levels": confidence_levels,
            "last_updated": max(s.updated_at for s in suggestions).isoformat() if suggestions else None
        } 