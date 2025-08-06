from api.main import app

# This file serves as the entry point for the FastAPI application
# The app object is imported from api.main where the FastAPI application is defined

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 