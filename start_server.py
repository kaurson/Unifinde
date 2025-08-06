#!/usr/bin/env python3
"""
Start the FastAPI server for the University Matching App
"""

import uvicorn
import sys
import os

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    print("🚀 Starting University Matching API Server...")
    print("📡 Server will be available at: http://localhost:8000")
    print("📚 API Documentation will be available at: http://localhost:8000/docs")
    print("🔧 Press Ctrl+C to stop the server\n")
    
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 