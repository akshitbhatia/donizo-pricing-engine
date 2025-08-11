import logging
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
import uuid
from datetime import datetime
import json

from app.models import FeedbackResponse, UserType, VerdictType
from app.database import Feedback, Quote, MaterialUsage, Task as TaskDB, VendorReliability
from app.config import settings

logger = logging.getLogger(__name__)

class FeedbackService:
    def __init__(self):
        self.impact_threshold = settings.feedback_impact_threshold
        
    async def process_feedback(
        self,
        quote_id: str,
        user_type: UserType,
        verdict: VerdictType,
        comment: Optional[str] = None,
        material_feedback: Optional[Dict[str, str]] = None,
        pricing_feedback: Optional[Dict[str, str]] = None,
        db: Session = None
    ) -> FeedbackResponse:
        """
        Process user feedback and update system learning.
        
        Args:
            quote_id: Quote identifier
            user_type: Type of user providing feedback
            verdict: User's verdict on the quote
            comment: Additional feedback comment
            material_feedback: Feedback on specific materials
            pricing_feedback: Feedback on pricing aspects
            db: Database session
            
        Returns:
            Feedback processing result with learning insights
        """
        try:
            logger.info(f"Processing feedback for quote {quote_id}: {verdict}")
            
            # Step 1: Validate quote exists
            quote = db.query(Quote).filter(Quote.id == quote_id).first()
            if not quote:
                raise ValueError(f"Quote {quote_id} not found")
            
            # Step 2: Calculate impact score
            impact_score = self._calculate_impact_score(verdict, user_type, quote)
            
            # Step 3: Generate learning insights
            learning_insights = await self._generate_learning_insights(
                quote, verdict, comment, material_feedback, pricing_feedback, db
            )
            
            # Step 4: Create feedback record
            feedback_id = str(uuid.uuid4())
            feedback = Feedback(
                id=feedback_id,
                quote_id=quote_id,
                user_type=user_type.value,
                verdict=verdict.value,
                comment=comment,
                material_feedback=json.dumps(material_feedback) if material_feedback else None,
                pricing_feedback=json.dumps(pricing_feedback) if pricing_feedback else None,
                impact_score=impact_score
            )
            db.add(feedback)
            
            # Step 5: Update system learning
            await self._update_system_learning(
                quote, verdict, material_feedback, pricing_feedback, db
            )
            
            db.commit()
            
            # Step 6: Create response
            response = FeedbackResponse(
                feedback_id=feedback_id,
                quote_id=quote_id,
                user_type=user_type,
                verdict=verdict,
                comment=comment,
                processed_at=datetime.utcnow(),
                impact_score=impact_score,
                learning_insights=learning_insights
            )
            
            logger.info(f"Feedback processed successfully with impact score: {impact_score}")
            return response
            
        except Exception as e:
            logger.error(f"Error processing feedback: {str(e)}")
            db.rollback()
            raise
    
    def _calculate_impact_score(
        self, 
        verdict: VerdictType, 
        user_type: UserType, 
        quote: Quote
    ) -> float:
        """Calculate the impact score of feedback on system learning"""
        try:
            base_score = 0.5
            
            # Adjust based on verdict
            verdict_weights = {
                VerdictType.REJECTED: 1.0,
                VerdictType.OVERPRICED: 0.8,
                VerdictType.UNDERPRICED: 0.8,
                VerdictType.MODIFIED: 0.6,
                VerdictType.ACCEPTED: 0.3
            }
            
            base_score *= verdict_weights.get(verdict, 0.5)
            
            # Adjust based on user type
            user_weights = {
                UserType.CONTRACTOR: 1.0,
                UserType.ARCHITECT: 0.9,
                UserType.CLIENT: 0.7
            }
            
            base_score *= user_weights.get(user_type, 0.5)
            
            # Adjust based on quote confidence
            # Lower confidence quotes have higher impact when feedback is negative
            if verdict in [VerdictType.REJECTED, VerdictType.OVERPRICED, VerdictType.UNDERPRICED]:
                confidence_factor = 1.0 - quote.confidence_score
                base_score *= (1.0 + confidence_factor)
            
            # Adjust based on quote value
            # Higher value quotes have more impact
            value_factor = min(quote.total_estimate / 1000.0, 2.0)  # Cap at 2x
            base_score *= value_factor
            
            return max(0.0, min(1.0, base_score))
            
        except Exception as e:
            logger.error(f"Error calculating impact score: {e}")
            return 0.5
    
    async def _generate_learning_insights(
        self,
        quote: Quote,
        verdict: VerdictType,
        comment: Optional[str],
        material_feedback: Optional[Dict[str, str]],
        pricing_feedback: Optional[Dict[str, str]],
        db: Session
    ) -> List[str]:
        """Generate learning insights from feedback"""
        insights = []
        
        try:
            # Analyze verdict patterns
            if verdict == VerdictType.REJECTED:
                insights.append("Quote was completely rejected - review pricing strategy")
            elif verdict == VerdictType.OVERPRICED:
                insights.append("Quote was overpriced - consider reducing margins or finding cheaper materials")
            elif verdict == VerdictType.UNDERPRICED:
                insights.append("Quote was underpriced - review cost calculations and margins")
            elif verdict == VerdictType.MODIFIED:
                insights.append("Quote was modified - analyze what changes were made")
            
            # Analyze confidence vs outcome
            if quote.confidence_score > 0.8 and verdict in [VerdictType.REJECTED, VerdictType.OVERPRICED]:
                insights.append("High confidence quote was rejected - review confidence scoring logic")
            elif quote.confidence_score < 0.5 and verdict == VerdictType.ACCEPTED:
                insights.append("Low confidence quote was accepted - may be too conservative")
            
            # Analyze regional patterns
            if quote.region:
                insights.append(f"Regional feedback for {quote.region} - update regional pricing if needed")
            
            # Analyze material feedback
            if material_feedback:
                for material, feedback_text in material_feedback.items():
                    if 'expensive' in feedback_text.lower():
                        insights.append(f"Material {material} considered expensive - review pricing")
                    elif 'quality' in feedback_text.lower():
                        insights.append(f"Quality feedback for {material} - consider alternative suppliers")
            
            # Analyze pricing feedback
            if pricing_feedback:
                for aspect, feedback_text in pricing_feedback.items():
                    insights.append(f"Pricing feedback on {aspect}: {feedback_text}")
            
            # Analyze comment sentiment
            if comment:
                if any(word in comment.lower() for word in ['expensive', 'overpriced', 'high']):
                    insights.append("User indicated pricing was too high")
                elif any(word in comment.lower() for word in ['cheap', 'good price', 'reasonable']):
                    insights.append("User indicated pricing was reasonable")
                elif any(word in comment.lower() for word in ['quality', 'material']):
                    insights.append("User provided material quality feedback")
            
            # Add default insight if none generated
            if not insights:
                insights.append("Feedback received - monitoring for patterns")
            
            return insights
            
        except Exception as e:
            logger.error(f"Error generating learning insights: {e}")
            return ["Error analyzing feedback"]
    
    async def _update_system_learning(
        self,
        quote: Quote,
        verdict: VerdictType,
        material_feedback: Optional[Dict[str, str]],
        pricing_feedback: Optional[Dict[str, str]],
        db: Session
    ):
        """Update system learning based on feedback"""
        try:
            # Update vendor reliability scores
            await self._update_vendor_reliability(quote, verdict, db)
            
            # Update regional pricing if needed
            await self._update_regional_pricing(quote, verdict, db)
            
            # Update material pricing if feedback provided
            if material_feedback:
                await self._update_material_pricing(quote, material_feedback, db)
            
            # Log feedback for pattern analysis
            await self._log_feedback_patterns(quote, verdict, db)
            
        except Exception as e:
            logger.error(f"Error updating system learning: {e}")
    
    async def _update_vendor_reliability(
        self, 
        quote: Quote, 
        verdict: VerdictType, 
        db: Session
    ):
        """Update vendor reliability scores based on feedback"""
        try:
            # Get materials used in this quote
            material_usages = db.query(MaterialUsage).filter(
                MaterialUsage.quote_id == quote.id
            ).all()
            
            # Get unique vendors
            vendors = set()
            for usage in material_usages:
                # This would typically join with materials table to get vendor
                # For now, we'll use a placeholder
                pass
            
            # Update vendor reliability for each vendor
            for vendor in vendors:
                accepted = verdict == VerdictType.ACCEPTED
                
                vendor_reliability = db.query(VendorReliability).filter(
                    VendorReliability.vendor_name == vendor
                ).first()
                
                if vendor_reliability is None:
                    vendor_reliability = VendorReliability(vendor_name=vendor)
                    db.add(vendor_reliability)
                
                vendor_reliability.total_quotes += 1
                if accepted:
                    vendor_reliability.accepted_quotes += 1
                
                # Calculate new reliability score
                vendor_reliability.reliability_score = (
                    vendor_reliability.accepted_quotes / vendor_reliability.total_quotes
                )
                vendor_reliability.updated_at = datetime.utcnow()
            
        except Exception as e:
            logger.error(f"Error updating vendor reliability: {e}")
    
    async def _update_regional_pricing(
        self, 
        quote: Quote, 
        verdict: VerdictType, 
        db: Session
    ):
        """Update regional pricing multipliers based on feedback"""
        try:
            if not quote.region:
                return
            
            # This would typically update regional pricing table
            # For now, we'll log the feedback for manual review
            if verdict in [VerdictType.OVERPRICED, VerdictType.REJECTED]:
                logger.info(f"Consider reducing regional multiplier for {quote.region}")
            elif verdict == VerdictType.UNDERPRICED:
                logger.info(f"Consider increasing regional multiplier for {quote.region}")
                
        except Exception as e:
            logger.error(f"Error updating regional pricing: {e}")
    
    async def _update_material_pricing(
        self, 
        quote: Quote, 
        material_feedback: Dict[str, str], 
        db: Session
    ):
        """Update material pricing based on feedback"""
        try:
            for material_name, feedback_text in material_feedback.items():
                if 'expensive' in feedback_text.lower():
                    logger.info(f"Consider reviewing pricing for {material_name}")
                elif 'cheap' in feedback_text.lower():
                    logger.info(f"Consider increasing pricing for {material_name}")
                    
        except Exception as e:
            logger.error(f"Error updating material pricing: {e}")
    
    async def _log_feedback_patterns(
        self, 
        quote: Quote, 
        verdict: VerdictType, 
        db: Session
    ):
        """Log feedback patterns for analysis"""
        try:
            # This would typically log to a separate analytics table
            # For now, we'll just log to the application log
            logger.info(f"Feedback pattern: {verdict.value} for {quote.region} region, "
                       f"confidence: {quote.confidence_score:.2f}, "
                       f"value: €{quote.total_estimate:.2f}")
                       
        except Exception as e:
            logger.error(f"Error logging feedback patterns: {e}")
    
    async def get_feedback_analytics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        region: Optional[str] = None,
        user_type: Optional[str] = None,
        db: Session = None
    ) -> Dict[str, Any]:
        """Get feedback analytics for system improvement"""
        try:
            query = db.query(Feedback)
            
            if start_date:
                query = query.filter(Feedback.created_at >= start_date)
            if end_date:
                query = query.filter(Feedback.created_at <= end_date)
            if user_type:
                query = query.filter(Feedback.user_type == user_type)
            
            feedbacks = query.all()
            
            # Calculate analytics
            total_feedback = len(feedbacks)
            if total_feedback == 0:
                return {"message": "No feedback found for the specified criteria"}
            
            # Verdict distribution
            verdict_counts = {}
            for feedback in feedbacks:
                verdict = feedback.verdict
                verdict_counts[verdict] = verdict_counts.get(verdict, 0) + 1
            
            # Average impact score
            avg_impact = sum(f.impact_score for f in feedbacks if f.impact_score) / total_feedback
            
            # Regional analysis
            regional_feedback = {}
            for feedback in feedbacks:
                # Get quote region
                quote = db.query(Quote).filter(Quote.id == feedback.quote_id).first()
                if quote and quote.region:
                    if quote.region not in regional_feedback:
                        regional_feedback[quote.region] = []
                    regional_feedback[quote.region].append(feedback.verdict)
            
            # Calculate regional acceptance rates
            regional_rates = {}
            for region, verdicts in regional_feedback.items():
                accepted = sum(1 for v in verdicts if v == 'accepted')
                regional_rates[region] = accepted / len(verdicts)
            
            return {
                "total_feedback": total_feedback,
                "verdict_distribution": verdict_counts,
                "average_impact_score": avg_impact,
                "regional_acceptance_rates": regional_rates,
                "date_range": {
                    "start": start_date.isoformat() if start_date else None,
                    "end": end_date.isoformat() if end_date else None
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting feedback analytics: {e}")
            return {"error": str(e)}
    
    async def get_quote_feedback_history(
        self,
        quote_id: str,
        db: Session = None
    ) -> List[Dict[str, Any]]:
        """Get feedback history for a specific quote"""
        try:
            feedbacks = db.query(Feedback).filter(
                Feedback.quote_id == quote_id
            ).order_by(Feedback.created_at.desc()).all()
            
            return [
                {
                    "id": feedback.id,
                    "user_type": feedback.user_type,
                    "verdict": feedback.verdict,
                    "comment": feedback.comment,
                    "impact_score": feedback.impact_score,
                    "created_at": feedback.created_at.isoformat(),
                    "material_feedback": json.loads(feedback.material_feedback) if feedback.material_feedback else None,
                    "pricing_feedback": json.loads(feedback.pricing_feedback) if feedback.pricing_feedback else None
                }
                for feedback in feedbacks
            ]
            
        except Exception as e:
            logger.error(f"Error getting quote feedback history: {e}")
            return []
