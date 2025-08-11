import logging
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
import uuid
from datetime import datetime
import re

from app.models import (
    GenerateProposalResponse, Task, MaterialItem, UserType,
    get_pricing_config, get_labor_rates, get_material_categories
)
from app.database import Quote, Material, MaterialUsage, Task as TaskDB
from app.services.material_service import MaterialService
from app.services.embedding_service import EmbeddingService
from app.config import settings

logger = logging.getLogger(__name__)

class PricingService:
    def __init__(self):
        self.material_service = MaterialService()
        self.embedding_service = EmbeddingService()
        self.pricing_config = get_pricing_config()
        self.labor_rates = get_labor_rates()
        self.material_categories = get_material_categories()
        
    async def generate_proposal(
        self,
        transcript: str,
        user_type: UserType = UserType.CONTRACTOR,
        region: Optional[str] = None,
        project_type: Optional[str] = None,
        db: Session = None
    ) -> GenerateProposalResponse:
        """
        Generate a comprehensive quote proposal from contractor transcript.
        
        Args:
            transcript: Contractor's voice transcript
            user_type: Type of user (contractor, client, architect)
            region: Geographic region
            project_type: Type of renovation project
            db: Database session
            
        Returns:
            Complete quote proposal with tasks, materials, and pricing
        """
        try:
            logger.info(f"Generating proposal for transcript: '{transcript[:100]}...'")
            
            # Step 1: Extract materials and tasks from transcript
            extracted_data = await self._extract_materials_and_tasks(transcript, region, db)
            
            # Step 2: Calculate pricing for each task
            tasks = []
            total_materials_cost = 0.0
            total_labor_cost = 0.0
            
            for task_data in extracted_data['tasks']:
                task = await self._calculate_task_pricing(
                    task_data, region, project_type, db
                )
                tasks.append(task)
                
                # Accumulate costs
                task_materials_cost = sum(m.total_price for m in task.materials)
                total_materials_cost += task_materials_cost
                if task.labor_cost:
                    total_labor_cost += task.labor_cost
            
            # Step 3: Calculate total estimate with VAT and margins
            subtotal = total_materials_cost + total_labor_cost
            vat_rate = self._determine_vat_rate(project_type)
            vat_amount = subtotal * vat_rate
            margin_amount = subtotal * self.pricing_config['base_margin']
            
            total_estimate = subtotal + vat_amount + margin_amount
            
            # Step 4: Calculate overall confidence score
            confidence_score = self._calculate_overall_confidence(tasks)
            
            # Step 5: Create quote record
            quote_id = str(uuid.uuid4())
            quote = Quote(
                id=quote_id,
                transcript=transcript,
                total_estimate=total_estimate,
                confidence_score=confidence_score,
                user_type=user_type.value,
                region=region,
                project_type=project_type
            )
            db.add(quote)
            
            # Step 6: Save task and material usage records
            for task in tasks:
                task_db = TaskDB(
                    quote_id=quote_id,
                    label=task.label,
                    estimated_duration=task.estimated_duration,
                    margin_protected_price=task.margin_protected_price,
                    confidence_score=task.confidence_score,
                    labor_cost=task.labor_cost
                )
                db.add(task_db)
                
                # Save material usage
                for material in task.materials:
                    material_usage = MaterialUsage(
                        quote_id=quote_id,
                        material_id=material.material_id if hasattr(material, 'material_id') else 0,
                        quantity=material.quantity,
                        unit_price=material.unit_price,
                        total_price=material.total_price,
                        confidence_score=material.confidence_score
                    )
                    db.add(material_usage)
            
            db.commit()
            
            # Step 7: Create response
            response = GenerateProposalResponse(
                quote_id=quote_id,
                transcript=transcript,
                tasks=tasks,
                total_estimate=total_estimate,
                confidence_score=confidence_score,
                vat_rate=vat_rate,
                margin_percentage=self.pricing_config['base_margin'],
                created_at=datetime.utcnow(),
                region=region,
                project_type=project_type
            )
            
            logger.info(f"Generated proposal with {len(tasks)} tasks, total: €{total_estimate:.2f}")
            return response
            
        except Exception as e:
            logger.error(f"Error generating proposal: {str(e)}")
            db.rollback()
            raise
    
    async def _extract_materials_and_tasks(
        self, 
        transcript: str, 
        region: Optional[str],
        db: Session
    ) -> Dict[str, Any]:
        """Extract materials and tasks from transcript using NLP"""
        try:
            # Preprocess transcript
            processed_transcript = await self.embedding_service.preprocess_text(transcript)
            
            # Extract keywords
            keywords = await self.embedding_service.get_semantic_keywords(processed_transcript, top_k=10)
            
            # Identify materials mentioned
            materials = []
            for keyword in keywords:
                material_results = await self.material_service.search_materials(
                    query=keyword,
                    region=region,
                    limit=3,
                    db=db
                )
                materials.extend(material_results)
            
            # Identify tasks based on material categories and keywords
            tasks = self._identify_tasks(processed_transcript, keywords, materials)
            
            return {
                'materials': materials,
                'tasks': tasks,
                'keywords': keywords
            }
            
        except Exception as e:
            logger.error(f"Error extracting materials and tasks: {e}")
            # Return fallback data
            return {
                'materials': [],
                'tasks': [{'type': 'general', 'materials': [], 'duration': '1 day'}],
                'keywords': []
            }
    
    def _identify_tasks(
        self, 
        transcript: str, 
        keywords: List[str], 
        materials: List
    ) -> List[Dict[str, Any]]:
        """Identify tasks from transcript and materials"""
        tasks = []
        
        # Map keywords to task types
        task_keywords = {
            'tiling': ['tile', 'carrelage', 'bathroom', 'shower', 'wall'],
            'painting': ['paint', 'peinture', 'wall', 'ceiling'],
            'plumbing': ['pipe', 'tuyau', 'water', 'bathroom', 'kitchen'],
            'electrical': ['wire', 'fil', 'electric', 'switch', 'outlet'],
            'carpentry': ['wood', 'bois', 'door', 'window', 'cabinet'],
        }
        
        # Identify tasks based on keywords and materials
        identified_tasks = set()
        
        for keyword in keywords:
            for task_type, task_keywords_list in task_keywords.items():
                if any(k in keyword.lower() for k in task_keywords_list):
                    identified_tasks.add(task_type)
        
        # Create task objects
        for task_type in identified_tasks:
            task_materials = [m for m in materials if self._material_belongs_to_task(m, task_type)]
            
            tasks.append({
                'type': task_type,
                'materials': task_materials,
                'duration': self._estimate_task_duration(task_type, len(task_materials))
            })
        
        # If no specific tasks identified, create a general task
        if not tasks:
            tasks.append({
                'type': 'general',
                'materials': materials,
                'duration': '1 day'
            })
        
        return tasks
    
    def _material_belongs_to_task(self, material, task_type: str) -> bool:
        """Check if material belongs to a specific task type"""
        material_text = f"{material.material_name} {material.description}".lower()
        
        task_keywords = {
            'tiling': ['tile', 'carrelage', 'adhesive', 'grout'],
            'painting': ['paint', 'peinture', 'primer', 'brush'],
            'plumbing': ['pipe', 'tuyau', 'valve', 'fitting'],
            'electrical': ['wire', 'fil', 'cable', 'switch'],
            'carpentry': ['wood', 'bois', 'board', 'screw'],
        }
        
        keywords = task_keywords.get(task_type, [])
        return any(keyword in material_text for keyword in keywords)
    
    def _estimate_task_duration(self, task_type: str, material_count: int) -> str:
        """Estimate task duration based on type and materials"""
        base_durations = {
            'tiling': '2 days',
            'painting': '1 day',
            'plumbing': '1 day',
            'electrical': '1 day',
            'carpentry': '2 days',
            'general': '1 day'
        }
        
        duration = base_durations.get(task_type, '1 day')
        
        # Adjust based on material count
        if material_count > 5:
            if '1 day' in duration:
                duration = duration.replace('1 day', '2 days')
            elif '2 days' in duration:
                duration = duration.replace('2 days', '3 days')
        
        return duration
    
    async def _calculate_task_pricing(
        self,
        task_data: Dict[str, Any],
        region: Optional[str],
        project_type: Optional[str],
        db: Session
    ) -> Task:
        """Calculate pricing for a specific task"""
        try:
            task_type = task_data['type']
            materials = task_data['materials']
            duration = task_data['duration']
            
            # Calculate material costs
            material_items = []
            total_material_cost = 0.0
            
            for material in materials:
                # Estimate quantity based on task type
                quantity = self._estimate_material_quantity(material, task_type)
                total_price = material.unit_price * quantity
                
                material_item = MaterialItem(
                    material_name=material.material_name,
                    quantity=quantity,
                    unit=material.unit,
                    unit_price=material.unit_price,
                    total_price=total_price,
                    confidence_score=material.similarity_score
                )
                material_items.append(material_item)
                total_material_cost += total_price
            
            # Calculate labor cost
            labor_cost = self._calculate_labor_cost(task_type, duration)
            
            # Apply regional multiplier
            regional_multiplier = self._get_regional_multiplier(region)
            adjusted_material_cost = total_material_cost * regional_multiplier
            adjusted_labor_cost = labor_cost * regional_multiplier
            
            # Calculate margin-protected price
            margin_protected_price = (adjusted_material_cost + adjusted_labor_cost) * (1 + self.pricing_config['base_margin'])
            
            # Calculate task confidence
            task_confidence = self._calculate_task_confidence(material_items, task_type)
            
            # Create task label
            task_label = self._create_task_label(task_type, materials)
            
            return Task(
                label=task_label,
                materials=material_items,
                estimated_duration=duration,
                margin_protected_price=margin_protected_price,
                confidence_score=task_confidence,
                labor_cost=adjusted_labor_cost
            )
            
        except Exception as e:
            logger.error(f"Error calculating task pricing: {e}")
            # Return fallback task
            return Task(
                label=f"General {task_data.get('type', 'work')}",
                materials=[],
                estimated_duration="1 day",
                margin_protected_price=100.0,
                confidence_score=0.5,
                labor_cost=80.0
            )
    
    def _estimate_material_quantity(self, material, task_type: str) -> float:
        """Estimate material quantity based on task type and material"""
        # Base quantities for common materials
        base_quantities = {
            'tiles': 10.0,  # m²
            'adhesives': 5.0,  # kg
            'paints': 5.0,  # L
            'pipes': 10.0,  # m
            'wires': 20.0,  # m
            'wood': 5.0,  # m²
        }
        
        material_name = material.material_name.lower()
        
        # Determine material type
        for material_type, quantity in base_quantities.items():
            if material_type in material_name:
                return quantity
        
        # Default quantity
        return 1.0
    
    def _calculate_labor_cost(self, task_type: str, duration: str) -> float:
        """Calculate labor cost for task"""
        # Extract hours from duration
        hours = self._parse_duration_to_hours(duration)
        
        # Get labor rate for task type
        labor_rate = self.labor_rates.get(task_type, self.labor_rates['general'])
        
        return hours * labor_rate
    
    def _parse_duration_to_hours(self, duration: str) -> float:
        """Parse duration string to hours"""
        try:
            if 'day' in duration.lower():
                days = float(re.findall(r'\d+', duration)[0])
                return days * 8  # 8 hours per day
            elif 'hour' in duration.lower():
                return float(re.findall(r'\d+', duration)[0])
            else:
                return 8.0  # Default to 8 hours
        except:
            return 8.0
    
    def _get_regional_multiplier(self, region: Optional[str]) -> float:
        """Get regional price multiplier"""
        if not region:
            return 1.0
        
        return self.pricing_config['regional_multipliers'].get(region, 1.0)
    
    def _calculate_task_confidence(self, materials: List[MaterialItem], task_type: str) -> float:
        """Calculate confidence score for task"""
        if not materials:
            return 0.3
        
        # Average material confidence
        avg_material_confidence = sum(m.confidence_score for m in materials) / len(materials)
        
        # Task type confidence (some tasks are easier to estimate)
        task_confidence = {
            'tiling': 0.8,
            'painting': 0.9,
            'plumbing': 0.7,
            'electrical': 0.6,
            'carpentry': 0.7,
            'general': 0.5
        }
        
        task_type_confidence = task_confidence.get(task_type, 0.5)
        
        # Combine scores
        return (avg_material_confidence * 0.7) + (task_type_confidence * 0.3)
    
    def _create_task_label(self, task_type: str, materials: List) -> str:
        """Create human-readable task label"""
        task_labels = {
            'tiling': 'Tile Installation',
            'painting': 'Painting',
            'plumbing': 'Plumbing Work',
            'electrical': 'Electrical Work',
            'carpentry': 'Carpentry Work',
            'general': 'General Renovation'
        }
        
        base_label = task_labels.get(task_type, 'General Work')
        
        if materials:
            material_names = [m.material_name for m in materials[:2]]
            return f"{base_label} - {', '.join(material_names)}"
        
        return base_label
    
    def _determine_vat_rate(self, project_type: Optional[str]) -> float:
        """Determine VAT rate based on project type"""
        if project_type and 'new' in project_type.lower():
            return self.pricing_config['vat_new_build']
        else:
            return self.pricing_config['vat_renovation']
    
    def _calculate_overall_confidence(self, tasks: List[Task]) -> float:
        """Calculate overall confidence score for the proposal"""
        if not tasks:
            return 0.0
        
        # Weighted average of task confidences
        total_confidence = sum(task.confidence_score for task in tasks)
        return total_confidence / len(tasks)
    
    async def get_quote_history(
        self, 
        user_type: Optional[str] = None,
        region: Optional[str] = None,
        limit: int = 10,
        db: Session = None
    ) -> List[Dict[str, Any]]:
        """Get quote history for analysis"""
        try:
            query = db.query(Quote)
            
            if user_type:
                query = query.filter(Quote.user_type == user_type)
            if region:
                query = query.filter(Quote.region == region)
            
            quotes = query.order_by(Quote.created_at.desc()).limit(limit).all()
            
            return [
                {
                    'id': str(quote.id),
                    'transcript': quote.transcript,
                    'total_estimate': quote.total_estimate,
                    'confidence_score': quote.confidence_score,
                    'created_at': quote.created_at.isoformat(),
                    'region': quote.region,
                    'project_type': quote.project_type
                }
                for quote in quotes
            ]
            
        except Exception as e:
            logger.error(f"Error getting quote history: {e}")
            return []
