from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import logging
from datetime import datetime
import uuid
from typing import List, Optional

from app.models import (
    MaterialPriceRequest, MaterialPriceResponse, 
    GenerateProposalRequest, GenerateProposalResponse,
    FeedbackRequest, FeedbackResponse
)
from app.services.material_service import MaterialService
from app.services.pricing_service import PricingService
from app.services.feedback_service import FeedbackService
from app.database import get_db
from app.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Smart Semantic Pricing Engine",
    description="A semantic material pricing engine for renovation projects",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
material_service = MaterialService()
pricing_service = PricingService()
feedback_service = FeedbackService()

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "Smart Semantic Pricing Engine v1.0.0",
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/material-price", response_model=List[MaterialPriceResponse])
async def get_material_price(
    query: str = Query(..., description="Search query for materials"),
    region: Optional[str] = Query(None, description="Geographic region"),
    unit: Optional[str] = Query(None, description="Unit filter"),
    quality_score: Optional[int] = Query(None, description="Minimum quality score"),
    vendor: Optional[str] = Query(None, description="Vendor filter"),
    limit: int = Query(5, description="Number of results to return", ge=1, le=20),
    db=Depends(get_db)
):
    """
    Semantic material search endpoint.
    
    Supports fuzzy, vague, and multilingual queries.
    Returns materials with confidence scores and pricing information.
    """
    try:
        logger.info(f"Material search request: query='{query}', region='{region}', limit={limit}")
        
        # Validate query
        if not query.strip():
            raise HTTPException(status_code=400, detail="Query cannot be empty")
        
        # Search for materials
        materials = await material_service.search_materials(
            query=query,
            region=region,
            unit=unit,
            quality_score=quality_score,
            vendor=vendor,
            limit=limit,
            db=db
        )
        
        logger.info(f"Found {len(materials)} materials for query '{query}'")
        return materials
        
    except Exception as e:
        logger.error(f"Error in material search: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.post("/generate-proposal", response_model=GenerateProposalResponse)
async def generate_proposal(
    request: GenerateProposalRequest,
    db=Depends(get_db)
):
    """
    Generate a comprehensive quote proposal from contractor transcript.
    
    Analyzes the transcript, identifies materials and tasks,
    calculates pricing with VAT and margins, and provides confidence scores.
    """
    try:
        logger.info(f"Quote generation request: transcript='{request.transcript[:100]}...'")
        
        # Validate transcript
        if not request.transcript.strip():
            raise HTTPException(status_code=400, detail="Transcript cannot be empty")
        
        # Generate proposal
        proposal = await pricing_service.generate_proposal(
            transcript=request.transcript,
            user_type=request.user_type,
            db=db
        )
        
        logger.info(f"Generated proposal with {len(proposal.tasks)} tasks, total: €{proposal.total_estimate}")
        return proposal
        
    except Exception as e:
        logger.error(f"Error in proposal generation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.post("/feedback", response_model=FeedbackResponse)
async def submit_feedback(
    request: FeedbackRequest,
    db=Depends(get_db)
):
    """
    Submit feedback for a quote to improve the system.
    
    Tracks user feedback to improve confidence scoring,
    material selection, and pricing logic over time.
    """
    try:
        logger.info(f"Feedback submission: quote_id='{request.quote_id}', verdict='{request.verdict}'")
        
        # Validate feedback
        if not request.quote_id:
            raise HTTPException(status_code=400, detail="Quote ID is required")
        
        if request.verdict not in ["accepted", "rejected", "overpriced", "underpriced", "modified"]:
            raise HTTPException(status_code=400, detail="Invalid verdict")
        
        # Process feedback
        feedback_result = await feedback_service.process_feedback(
            quote_id=request.quote_id,
            user_type=request.user_type,
            verdict=request.verdict,
            comment=request.comment,
            db=db
        )
        
        logger.info(f"Feedback processed successfully for quote {request.quote_id}")
        return feedback_result
        
    except Exception as e:
        logger.error(f"Error in feedback processing: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/health")
async def health_check():
    """Detailed health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "services": {
            "material_service": "operational",
            "pricing_service": "operational",
            "feedback_service": "operational"
        }
    }

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
