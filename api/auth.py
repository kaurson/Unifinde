from fastapi import HTTPException, Depends, status, Response, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from jose import jwt
from datetime import datetime, timedelta
import sys
import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.models import User
from database.database import get_db

# JWT Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-here")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days for better user experience
COOKIE_NAME = "auth_token"
COOKIE_SECURE = os.getenv("COOKIE_SECURE", "false").lower() == "true"  # Set to true in production with HTTPS

security = HTTPBearer(auto_error=False)  # Make it optional for cookie-based auth

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> Optional[str]:
    """Verify JWT token and return user email"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            return None
        return email
    except jwt.JWTError:
        return None

def set_auth_cookie(response: Response, token: str):
    """Set HTTP-only cookie with auth token"""
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,  # Convert minutes to seconds
        httponly=True,
        secure=COOKIE_SECURE,
        samesite="lax",
        path="/"
    )

def clear_auth_cookie(response: Response):
    """Clear auth cookie"""
    response.delete_cookie(
        key=COOKIE_NAME,
        path="/"
    )

def get_token_from_cookie(request: Request) -> Optional[str]:
    """Get token from cookie"""
    return request.cookies.get(COOKIE_NAME)

async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Get current authenticated user from cookie or bearer token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    token = None
    
    # Try to get token from cookie first
    token = get_token_from_cookie(request)
    
    # If no cookie token, try bearer token
    if not token and credentials:
        token = credentials.credentials
    
    if not token:
        raise credentials_exception
    
    try:
        email = verify_token(token)
        if email is None:
            raise credentials_exception
    except Exception:
        raise credentials_exception
    
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise credentials_exception
    
    return user

def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Get current active user (can be extended for user status checks)"""
    return current_user 