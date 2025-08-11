#!/usr/bin/env python3
"""
Database initialization script for Smart Semantic Pricing Engine.
Creates tables and loads sample material data.
"""

import sys
import os
import logging
from datetime import datetime
import json

# Add the parent directory to the path so we can import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import init_db, engine, SessionLocal, Material, RegionalPricing
from app.services.embedding_service import EmbeddingService
from scripts.generate_sample_data import generate_materials_data

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def initialize_database():
    """Initialize the database with tables and sample data"""
    try:
        logger.info("Starting database initialization...")
        
        # Step 1: Initialize database tables
        init_db()
        logger.info("Database tables created successfully")
        
        # Step 2: Generate sample materials data
        materials_data = generate_materials_data()
        logger.info(f"Generated {len(materials_data)} sample materials")
        
        # Step 3: Load materials into database
        await load_materials_data(materials_data)
        logger.info("Sample materials loaded successfully")
        
        # Step 4: Initialize embeddings (optional - can be done later)
        logger.info("Database initialization completed successfully!")
        
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise

async def load_materials_data(materials_data: list):
    """Load materials data into the database"""
    try:
        db = SessionLocal()
        embedding_service = EmbeddingService()
        
        # Check if materials already exist
        existing_count = db.query(Material).count()
        if existing_count > 0:
            logger.info(f"Database already contains {existing_count} materials. Skipping data load.")
            return
        
        logger.info("Loading materials data...")
        
        # Process materials in batches
        batch_size = 50
        for i in range(0, len(materials_data), batch_size):
            batch = materials_data[i:i + batch_size]
            
            for material_data in batch:
                try:
                    # Generate embedding for material
                    text = f"{material_data['material_name']} {material_data['description']}"
                    embedding = await embedding_service.get_embedding(text)
                    
                    # Create material record
                    material = Material(
                        material_name=material_data['material_name'],
                        description=material_data['description'],
                        unit_price=material_data['unit_price'],
                        unit=material_data['unit'],
                        region=material_data['region'],
                        vendor=material_data['vendor'],
                        quality_score=material_data['quality_score'],
                        embedding=json.dumps(embedding),
                        source_url=material_data['source_url'],
                        updated_at=datetime.utcnow()
                    )
                    
                    db.add(material)
                    
                except Exception as e:
                    logger.error(f"Error processing material {material_data['material_name']}: {e}")
                    continue
            
            # Commit batch
            try:
                db.commit()
                logger.info(f"Loaded batch {i//batch_size + 1}/{(len(materials_data) + batch_size - 1)//batch_size}")
            except Exception as e:
                logger.error(f"Error committing batch: {e}")
                db.rollback()
        
        db.close()
        logger.info("Materials data loading completed")
        
    except Exception as e:
        logger.error(f"Error loading materials data: {e}")
        raise

def create_sample_regional_pricing():
    """Create sample regional pricing data"""
    try:
        db = SessionLocal()
        
        # Check if regional pricing already exists
        existing_count = db.query(RegionalPricing).count()
        if existing_count > 0:
            logger.info(f"Regional pricing already exists ({existing_count} records). Skipping.")
            return
        
        # Sample regional multipliers
        regional_data = [
            ("Île-de-France", 1.15),
            ("Provence-Alpes-Côte d'Azur", 1.10),
            ("Auvergne-Rhône-Alpes", 1.05),
            ("Occitanie", 1.00),
            ("Nouvelle-Aquitaine", 0.95),
            ("Hauts-de-France", 0.90),
            ("Grand Est", 0.95),
            ("Bourgogne-Franche-Comté", 0.90),
            ("Centre-Val de Loire", 0.95),
            ("Normandie", 0.90),
            ("Bretagne", 0.95),
            ("Pays de la Loire", 0.95),
            ("Corse", 1.20),
        ]
        
        for region, multiplier in regional_data:
            regional_pricing = RegionalPricing(
                region=region,
                multiplier=multiplier
            )
            db.add(regional_pricing)
        
        db.commit()
        logger.info(f"Created {len(regional_data)} regional pricing records")
        db.close()
        
    except Exception as e:
        logger.error(f"Error creating regional pricing: {e}")
        raise

async def main():
    """Main initialization function"""
    try:
        # Initialize database
        await initialize_database()
        
        # Create regional pricing
        create_sample_regional_pricing()
        
        logger.info("Database initialization completed successfully!")
        
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
