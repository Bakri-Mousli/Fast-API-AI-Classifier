import sys
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent 
sys.path.insert(0, str(BASE_DIR))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.schemas import ClassificationOut, ComplaintIn
from app.services.classifier import classify_complaint
from app.config import settings
from app.services.classifier import load_government_structure
from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    try:
        await load_government_structure()
        print("Government structure uploaded successfully")
    except Exception as e:
        print(f"Failed to load government structure: {str(e)}")
        raise
    
    yield  # App runs here
   
    
app = FastAPI(
    title="Complaint Classification API",
    version="1.0.0",
    lifespan=lifespan
)

# Config of CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/classify", response_model=ClassificationOut)
async def classify_complaint_endpoint(complaint: ComplaintIn):
    try:
        priority, feedback = await classify_complaint(
            title=complaint.title,
            content=complaint.content
        )
        return {
            "priority": priority,
            "feedback": feedback
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Classification failed: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        workers=4
    )
    
    
