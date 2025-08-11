import logging
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
import numpy as np
from datetime import datetime
import json

from app.models import MaterialPriceResponse, ConfidenceTier, SearchFilters
from app.database import Material, get_materials_by_region
from app.config import settings, get_confidence_weights, get_embedding_config
from app.services.embedding_service import EmbeddingService

logger = logging.getLogger(__name__)

class MaterialService:
    def __init__(self):
        self.embedding_service = EmbeddingService()
        self.confidence_weights = get_confidence_weights()
        
    async def search_materials(
        self,
        query: str,
        region: Optional[str] = None,
        unit: Optional[str] = None,
        quality_score: Optional[int] = None,
        vendor: Optional[str] = None,
        limit: int = 5,
        db: Session = None
    ) -> List[MaterialPriceResponse]:
        """
        Search for materials using semantic similarity and filters.
        
        Args:
            query: Search query (supports fuzzy, vague, multilingual)
            region: Geographic region filter
            unit: Unit filter
            quality_score: Minimum quality score
            vendor: Vendor filter
            limit: Maximum number of results
            db: Database session
            
        Returns:
            List of materials with confidence scores and pricing
        """
        try:
            logger.info(f"Searching materials with query: '{query}', region: '{region}', limit: {limit}")
            
            # Step 1: Generate embedding for query
            query_embedding = await self.embedding_service.get_embedding(query)
            
            # Step 2: Build database query with filters
            db_query = db.query(Material)
            
            # Apply filters
            if region:
                db_query = db_query.filter(Material.region == region)
            if unit:
                db_query = db_query.filter(Material.unit == unit)
            if quality_score:
                db_query = db_query.filter(Material.quality_score >= quality_score)
            if vendor:
                db_query = db_query.filter(Material.vendor == vendor)
            
            # Get materials
            materials = db_query.limit(limit * 3).all()  # Get more for ranking
            
            if not materials:
                logger.warning(f"No materials found for query: '{query}'")
                return []
            
            # Step 3: Calculate similarity scores and rank
            ranked_materials = []
            for material in materials:
                similarity_score = await self._calculate_similarity_score(
                    query_embedding, material, query
                )
                
                confidence_score = await self._calculate_confidence_score(
                    material, similarity_score, region
                )
                
                ranked_materials.append({
                    'material': material,
                    'similarity_score': similarity_score,
                    'confidence_score': confidence_score
                })
            
            # Step 4: Sort by confidence score and return top results
            ranked_materials.sort(key=lambda x: x['confidence_score'], reverse=True)
            
            # Step 5: Convert to response format
            results = []
            for item in ranked_materials[:limit]:
                material = item['material']
                response = MaterialPriceResponse(
                    material_name=material.material_name,
                    description=material.description,
                    unit_price=material.unit_price,
                    unit=material.unit,
                    region=material.region,
                    similarity_score=item['similarity_score'],
                    confidence_tier=self._get_confidence_tier(item['confidence_score']),
                    updated_at=material.updated_at,
                    source=material.source_url or "Internal database",
                    vendor=material.vendor,
                    quality_score=material.quality_score
                )
                results.append(response)
            
            logger.info(f"Found {len(results)} materials for query '{query}'")
            return results
            
        except Exception as e:
            logger.error(f"Error in material search: {str(e)}")
            raise
    
    async def _calculate_similarity_score(
        self, 
        query_embedding: List[float], 
        material: Material, 
        query: str
    ) -> float:
        """Calculate semantic similarity between query and material"""
        try:
            # If material has embedding, use vector similarity
            if material.embedding:
                material_embedding = json.loads(material.embedding)
                similarity = self._cosine_similarity(query_embedding, material_embedding)
            else:
                # Fallback to text-based similarity
                similarity = self._text_similarity(query, material.material_name, material.description)
            
            return max(0.0, min(1.0, similarity))
            
        except Exception as e:
            logger.error(f"Error calculating similarity: {e}")
            return 0.0
    
    async def _calculate_confidence_score(
        self, 
        material: Material, 
        similarity_score: float, 
        region: Optional[str]
    ) -> float:
        """Calculate overall confidence score for material selection"""
        try:
            weights = self.confidence_weights
            
            # Semantic similarity (40%)
            semantic_score = similarity_score * weights['semantic_similarity']
            
            # Regional match (25%)
            regional_score = 0.0
            if region and material.region:
                if region.lower() == material.region.lower():
                    regional_score = 1.0
                elif region.lower() in material.region.lower() or material.region.lower() in region.lower():
                    regional_score = 0.7
            regional_score *= weights['regional_match']
            
            # Price range validation (20%)
            price_score = self._validate_price_range(material.unit_price)
            price_score *= weights['price_range']
            
            # Vendor reliability (15%)
            vendor_score = self._get_vendor_reliability(material.vendor)
            vendor_score *= weights['vendor_reliability']
            
            total_confidence = semantic_score + regional_score + price_score + vendor_score
            
            return max(0.0, min(1.0, total_confidence))
            
        except Exception as e:
            logger.error(f"Error calculating confidence: {e}")
            return 0.0
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        try:
            vec1 = np.array(vec1)
            vec2 = np.array(vec2)
            
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            return dot_product / (norm1 * norm2)
            
        except Exception as e:
            logger.error(f"Error in cosine similarity: {e}")
            return 0.0
    
    def _text_similarity(self, query: str, material_name: str, description: str) -> float:
        """Calculate text-based similarity as fallback"""
        try:
            query_lower = query.lower()
            name_lower = material_name.lower()
            desc_lower = description.lower()
            
            # Check for exact matches
            if query_lower in name_lower or query_lower in desc_lower:
                return 0.9
            
            # Check for word overlaps
            query_words = set(query_lower.split())
            name_words = set(name_lower.split())
            desc_words = set(desc_lower.split())
            
            name_overlap = len(query_words.intersection(name_words)) / len(query_words) if query_words else 0
            desc_overlap = len(query_words.intersection(desc_words)) / len(query_words) if query_words else 0
            
            return max(name_overlap, desc_overlap) * 0.7
            
        except Exception as e:
            logger.error(f"Error in text similarity: {e}")
            return 0.0
    
    def _validate_price_range(self, unit_price: float) -> float:
        """Validate if price is within reasonable range"""
        try:
            # Simple price validation - could be enhanced with historical data
            if 0.1 <= unit_price <= 1000.0:
                return 1.0
            elif 0.01 <= unit_price <= 10000.0:
                return 0.7
            else:
                return 0.3
        except Exception:
            return 0.5
    
    def _get_vendor_reliability(self, vendor: Optional[str]) -> float:
        """Get vendor reliability score"""
        if not vendor:
            return 0.5  # Default for unknown vendors
        
        # This would typically query a vendor reliability table
        # For now, return default values based on known vendors
        reliable_vendors = {
            'leroy merlin': 0.9,
            'castorama': 0.85,
            'brico depot': 0.8,
            'weldom': 0.75,
        }
        
        vendor_lower = vendor.lower()
        for known_vendor, score in reliable_vendors.items():
            if known_vendor in vendor_lower:
                return score
        
        return 0.5  # Default for unknown vendors
    
    def _get_confidence_tier(self, confidence_score: float) -> ConfidenceTier:
        """Convert confidence score to tier"""
        if confidence_score >= 0.8:
            return ConfidenceTier.HIGH
        elif confidence_score >= 0.6:
            return ConfidenceTier.MEDIUM
        else:
            return ConfidenceTier.LOW
    
    async def get_materials_by_category(
        self, 
        category: str, 
        region: Optional[str] = None,
        limit: int = 10,
        db: Session = None
    ) -> List[MaterialPriceResponse]:
        """Get materials by category (tiles, adhesives, etc.)"""
        try:
            # Map categories to keywords
            category_keywords = {
                'tiles': ['tile', 'carrelage', 'ceramic', 'porcelain'],
                'adhesives': ['glue', 'adhesive', 'mortar', 'colle'],
                'paints': ['paint', 'peinture', 'primer'],
                'plumbing': ['pipe', 'fitting', 'valve', 'tuyau'],
                'electrical': ['wire', 'cable', 'switch', 'fil'],
            }
            
            keywords = category_keywords.get(category.lower(), [category])
            
            # Build query
            db_query = db.query(Material)
            
            # Add keyword filters
            keyword_filters = []
            for keyword in keywords:
                keyword_filters.append(
                    or_(
                        Material.material_name.ilike(f'%{keyword}%'),
                        Material.description.ilike(f'%{keyword}%')
                    )
                )
            
            if keyword_filters:
                db_query = db_query.filter(or_(*keyword_filters))
            
            # Add region filter
            if region:
                db_query = db_query.filter(Material.region == region)
            
            # Get results
            materials = db_query.limit(limit).all()
            
            # Convert to response format
            results = []
            for material in materials:
                response = MaterialPriceResponse(
                    material_name=material.material_name,
                    description=material.description,
                    unit_price=material.unit_price,
                    unit=material.unit,
                    region=material.region,
                    similarity_score=0.8,  # Default for category search
                    confidence_tier=ConfidenceTier.MEDIUM,
                    updated_at=material.updated_at,
                    source=material.source_url or "Internal database",
                    vendor=material.vendor,
                    quality_score=material.quality_score
                )
                results.append(response)
            
            return results
            
        except Exception as e:
            logger.error(f"Error getting materials by category: {e}")
            raise
    
    async def update_material_embedding(
        self, 
        material_id: int, 
        db: Session = None
    ) -> bool:
        """Update material embedding"""
        try:
            material = db.query(Material).filter(Material.id == material_id).first()
            if not material:
                return False
            
            # Generate embedding for material name + description
            text = f"{material.material_name} {material.description}"
            embedding = await self.embedding_service.get_embedding(text)
            
            # Update material
            material.embedding = json.dumps(embedding)
            material.updated_at = datetime.utcnow()
            
            db.commit()
            logger.info(f"Updated embedding for material {material_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating material embedding: {e}")
            db.rollback()
            return False
