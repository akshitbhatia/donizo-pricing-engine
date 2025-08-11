from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum
import uuid

class UserType(str, Enum):
    CONTRACTOR = "contractor"
    CLIENT = "client"
    ARCHITECT = "architect"

class VerdictType(str, Enum):
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    OVERPRICED = "overpriced"
    UNDERPRICED = "underpriced"
    MODIFIED = "modified"

class ConfidenceTier(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"

# Material Price Models
class MaterialPriceRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500, description="Search query for materials")
    region: Optional[str] = Field(None, max_length=100, description="Geographic region")
    unit: Optional[str] = Field(None, max_length=50, description="Unit filter")
    quality_score: Optional[int] = Field(None, ge=1, le=10, description="Minimum quality score")
    vendor: Optional[str] = Field(None, max_length=255, description="Vendor filter")
    limit: int = Field(5, ge=1, le=20, description="Number of results to return")

class MaterialPriceResponse(BaseModel):
    material_name: str = Field(..., description="Name of the material")
    description: str = Field(..., description="Detailed description")
    unit_price: float = Field(..., ge=0, description="Price per unit")
    unit: str = Field(..., description="Unit of measurement")
    region: str = Field(..., description="Geographic region")
    similarity_score: float = Field(..., ge=0, le=1, description="Semantic similarity score")
    confidence_tier: ConfidenceTier = Field(..., description="Confidence level")
    updated_at: datetime = Field(..., description="Last update timestamp")
    source: str = Field(..., description="Source URL or reference")
    vendor: Optional[str] = Field(None, description="Vendor name")
    quality_score: Optional[int] = Field(None, ge=1, le=10, description="Quality rating")

    @validator('similarity_score')
    def validate_similarity_score(cls, v):
        if not 0 <= v <= 1:
            raise ValueError('Similarity score must be between 0 and 1')
        return v

# Quote Generation Models
class MaterialItem(BaseModel):
    material_name: str = Field(..., description="Material name")
    quantity: float = Field(..., gt=0, description="Quantity needed")
    unit: str = Field(..., description="Unit of measurement")
    unit_price: float = Field(..., ge=0, description="Price per unit")
    total_price: float = Field(..., ge=0, description="Total price for this material")
    confidence_score: float = Field(..., ge=0, le=1, description="Confidence in material selection")

class Task(BaseModel):
    label: str = Field(..., description="Task description")
    materials: List[MaterialItem] = Field(..., description="Materials required for this task")
    estimated_duration: str = Field(..., description="Estimated time to complete")
    margin_protected_price: float = Field(..., ge=0, description="Price with margin protection")
    confidence_score: float = Field(..., ge=0, le=1, description="Confidence in task estimation")
    labor_cost: Optional[float] = Field(None, ge=0, description="Estimated labor cost")

class GenerateProposalRequest(BaseModel):
    transcript: str = Field(..., min_length=10, max_length=2000, description="Contractor's voice transcript")
    user_type: UserType = Field(UserType.CONTRACTOR, description="Type of user")
    region: Optional[str] = Field(None, max_length=100, description="Geographic region")
    project_type: Optional[str] = Field(None, max_length=100, description="Type of renovation project")

    @validator('transcript')
    def validate_transcript(cls, v):
        if len(v.strip()) < 10:
            raise ValueError('Transcript must be at least 10 characters long')
        return v

class GenerateProposalResponse(BaseModel):
    quote_id: str = Field(..., description="Unique quote identifier")
    transcript: str = Field(..., description="Original transcript")
    tasks: List[Task] = Field(..., description="List of tasks and materials")
    total_estimate: float = Field(..., ge=0, description="Total estimated cost")
    confidence_score: float = Field(..., ge=0, le=1, description="Overall confidence score")
    vat_rate: float = Field(..., ge=0, le=1, description="Applied VAT rate")
    margin_percentage: float = Field(..., ge=0, description="Applied margin percentage")
    created_at: datetime = Field(..., description="Quote creation timestamp")
    region: Optional[str] = Field(None, description="Geographic region")
    project_type: Optional[str] = Field(None, description="Project type")

    @validator('quote_id')
    def validate_quote_id(cls, v):
        try:
            uuid.UUID(v)
            return v
        except ValueError:
            raise ValueError('Quote ID must be a valid UUID')

# Feedback Models
class FeedbackRequest(BaseModel):
    quote_id: str = Field(..., description="Quote identifier")
    user_type: UserType = Field(..., description="Type of user providing feedback")
    verdict: VerdictType = Field(..., description="User's verdict on the quote")
    comment: Optional[str] = Field(None, max_length=1000, description="Additional feedback comment")
    material_feedback: Optional[Dict[str, str]] = Field(None, description="Feedback on specific materials")
    pricing_feedback: Optional[Dict[str, str]] = Field(None, description="Feedback on pricing aspects")

    @validator('quote_id')
    def validate_quote_id(cls, v):
        try:
            uuid.UUID(v)
            return v
        except ValueError:
            raise ValueError('Quote ID must be a valid UUID')

class FeedbackResponse(BaseModel):
    feedback_id: str = Field(..., description="Unique feedback identifier")
    quote_id: str = Field(..., description="Quote identifier")
    user_type: UserType = Field(..., description="User type")
    verdict: VerdictType = Field(..., description="User verdict")
    comment: Optional[str] = Field(None, description="User comment")
    processed_at: datetime = Field(..., description="Feedback processing timestamp")
    impact_score: float = Field(..., ge=0, le=1, description="Impact on system learning")
    learning_insights: List[str] = Field(..., description="Key insights for system improvement")

    @validator('feedback_id')
    def validate_feedback_id(cls, v):
        try:
            uuid.UUID(v)
            return v
        except ValueError:
            raise ValueError('Feedback ID must be a valid UUID')

# Database Models (for internal use)
class MaterialDB(BaseModel):
    id: int
    material_name: str
    description: str
    unit_price: float
    unit: str
    region: str
    vendor: Optional[str]
    quality_score: Optional[int]
    source_url: Optional[str]
    updated_at: datetime

class QuoteDB(BaseModel):
    id: str
    transcript: str
    total_estimate: float
    confidence_score: float
    user_type: str
    created_at: datetime
    region: Optional[str]
    project_type: Optional[str]

class FeedbackDB(BaseModel):
    id: int
    quote_id: str
    user_type: str
    verdict: str
    comment: Optional[str]
    created_at: datetime

# Utility Models
class SearchFilters(BaseModel):
    region: Optional[str] = None
    unit: Optional[str] = None
    quality_score: Optional[int] = None
    vendor: Optional[str] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None

class PricingConfig(BaseModel):
    base_margin: float = Field(0.25, ge=0, description="Base margin percentage")
    vat_renovation: float = Field(0.10, ge=0, le=1, description="VAT rate for renovation")
    vat_new_build: float = Field(0.20, ge=0, le=1, description="VAT rate for new build")
    regional_multipliers: Dict[str, float] = Field(default_factory=dict, description="Regional price multipliers")
    quality_multipliers: Dict[str, float] = Field(default_factory=dict, description="Quality-based multipliers")

# Response Models for Error Handling
class ErrorResponse(BaseModel):
    detail: str = Field(..., description="Error message")
    error_code: Optional[str] = Field(None, description="Error code")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")

class SuccessResponse(BaseModel):
    message: str = Field(..., description="Success message")
    data: Optional[Dict[str, Any]] = Field(None, description="Response data")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")
