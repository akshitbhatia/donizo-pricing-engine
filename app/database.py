from sqlalchemy import create_engine, Column, Integer, String, Float, Text, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
from datetime import datetime
from typing import Generator
import logging

from app.config import settings

# Configure logging
logger = logging.getLogger(__name__)

# Create database engine
engine = create_engine(
    settings.database_url,
    pool_size=settings.database_pool_size,
    max_overflow=settings.database_max_overflow,
    pool_pre_ping=True,
    echo=settings.debug
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for models
Base = declarative_base()

# Database Models
class Material(Base):
    __tablename__ = "materials"
    
    id = Column(Integer, primary_key=True, index=True)
    material_name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=False)
    unit_price = Column(Float, nullable=False)
    unit = Column(String(50), nullable=False)
    region = Column(String(100), nullable=False, index=True)
    vendor = Column(String(255), nullable=True, index=True)
    quality_score = Column(Integer, nullable=True)
    embedding = Column(String, nullable=True)  # Vector will be stored as string, converted in queries
    source_url = Column(Text, nullable=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<Material(id={self.id}, name='{self.material_name}', region='{self.region}')>"

class Quote(Base):
    __tablename__ = "quotes"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    transcript = Column(Text, nullable=False)
    total_estimate = Column(Float, nullable=False)
    confidence_score = Column(Float, nullable=False)
    user_type = Column(String(50), nullable=False)
    region = Column(String(100), nullable=True)
    project_type = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<Quote(id={self.id}, total={self.total_estimate}, confidence={self.confidence_score})>"

class Feedback(Base):
    __tablename__ = "feedback"
    
    id = Column(Integer, primary_key=True, index=True)
    quote_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    user_type = Column(String(50), nullable=False)
    verdict = Column(String(50), nullable=False)
    comment = Column(Text, nullable=True)
    material_feedback = Column(Text, nullable=True)  # JSON string
    pricing_feedback = Column(Text, nullable=True)   # JSON string
    impact_score = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<Feedback(id={self.id}, quote_id={self.quote_id}, verdict='{self.verdict}')>"

class MaterialUsage(Base):
    __tablename__ = "material_usage"
    
    id = Column(Integer, primary_key=True, index=True)
    quote_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    material_id = Column(Integer, nullable=False, index=True)
    quantity = Column(Float, nullable=False)
    unit_price = Column(Float, nullable=False)
    total_price = Column(Float, nullable=False)
    confidence_score = Column(Float, nullable=False)
    
    def __repr__(self):
        return f"<MaterialUsage(id={self.id}, quote_id={self.quote_id}, material_id={self.material_id})>"

class Task(Base):
    __tablename__ = "tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    quote_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    label = Column(String(255), nullable=False)
    estimated_duration = Column(String(100), nullable=False)
    margin_protected_price = Column(Float, nullable=False)
    confidence_score = Column(Float, nullable=False)
    labor_cost = Column(Float, nullable=True)
    
    def __repr__(self):
        return f"<Task(id={self.id}, quote_id={self.quote_id}, label='{self.label}')>"

class VendorReliability(Base):
    __tablename__ = "vendor_reliability"
    
    id = Column(Integer, primary_key=True, index=True)
    vendor_name = Column(String(255), nullable=False, unique=True, index=True)
    reliability_score = Column(Float, nullable=False, default=0.5)
    total_quotes = Column(Integer, nullable=False, default=0)
    accepted_quotes = Column(Integer, nullable=False, default=0)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<VendorReliability(vendor='{self.vendor_name}', score={self.reliability_score})>"

class RegionalPricing(Base):
    __tablename__ = "regional_pricing"
    
    id = Column(Integer, primary_key=True, index=True)
    region = Column(String(100), nullable=False, unique=True, index=True)
    multiplier = Column(Float, nullable=False, default=1.0)
    last_updated = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<RegionalPricing(region='{self.region}', multiplier={self.multiplier})>"

# Database dependency
def get_db() -> Generator[Session, None, None]:
    """Database session dependency for FastAPI"""
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Database session error: {e}")
        db.rollback()
        raise
    finally:
        db.close()

# Database initialization
def init_db():
    """Initialize database tables"""
    try:
        # Create all tables
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
        
        # Initialize regional pricing data
        db = SessionLocal()
        try:
            # Check if regional pricing data exists
            existing_regions = db.query(RegionalPricing).count()
            if existing_regions == 0:
                # Insert default regional multipliers
                for region, multiplier in settings.regional_multipliers.items():
                    regional_pricing = RegionalPricing(region=region, multiplier=multiplier)
                    db.add(regional_pricing)
                
                db.commit()
                logger.info("Regional pricing data initialized")
            
        except Exception as e:
            logger.error(f"Error initializing regional pricing: {e}")
            db.rollback()
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise

# Database utilities
def get_material_by_id(db: Session, material_id: int) -> Material:
    """Get material by ID"""
    return db.query(Material).filter(Material.id == material_id).first()

def get_materials_by_region(db: Session, region: str, limit: int = 100) -> list[Material]:
    """Get materials by region"""
    return db.query(Material).filter(Material.region == region).limit(limit).all()

def get_quote_by_id(db: Session, quote_id: str) -> Quote:
    """Get quote by ID"""
    return db.query(Quote).filter(Quote.id == quote_id).first()

def get_feedback_by_quote_id(db: Session, quote_id: str) -> list[Feedback]:
    """Get feedback by quote ID"""
    return db.query(Feedback).filter(Feedback.quote_id == quote_id).all()

def get_vendor_reliability(db: Session, vendor_name: str) -> VendorReliability:
    """Get vendor reliability score"""
    return db.query(VendorReliability).filter(VendorReliability.vendor_name == vendor_name).first()

def update_vendor_reliability(db: Session, vendor_name: str, accepted: bool):
    """Update vendor reliability based on quote acceptance"""
    vendor = get_vendor_reliability(db, vendor_name)
    if vendor is None:
        vendor = VendorReliability(vendor_name=vendor_name)
        db.add(vendor)
    
    vendor.total_quotes += 1
    if accepted:
        vendor.accepted_quotes += 1
    
    # Calculate reliability score
    vendor.reliability_score = vendor.accepted_quotes / vendor.total_quotes
    vendor.updated_at = datetime.utcnow()
    
    db.commit()

# Vector search utilities (placeholder for pgvector integration)
def create_vector_index():
    """Create vector index for semantic search"""
    # This would be implemented with pgvector extension
    # For now, we'll use a placeholder
    logger.info("Vector index creation would be implemented with pgvector")

def search_similar_materials(db: Session, query_embedding: list, limit: int = 10) -> list[Material]:
    """Search for similar materials using vector similarity"""
    # This would use pgvector's cosine similarity
    # For now, return empty list as placeholder
    logger.info("Vector search would be implemented with pgvector")
    return []
