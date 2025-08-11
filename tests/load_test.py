#!/usr/bin/env python3
"""
Load testing script for Smart Semantic Pricing Engine using Locust
"""

from locust import HttpUser, task, between
import random
import json

class PricingEngineUser(HttpUser):
    wait_time = between(1, 3)  # Wait 1-3 seconds between requests
    
    def on_start(self):
        """Initialize user session"""
        # Test queries for material search
        self.test_queries = [
            "waterproof glue bathroom tiles",
            "matte tiles 60x60 bathroom wall",
            "colle carrelage salle de bain blanc",
            "glue tile interior wet wall high quality",
            "peinture murale blanche salon",
            "tuyau PVC évacuation cuisine",
            "câble électrique installation",
            "planche bois charpente",
            "laine isolation combles",
            "robinet mélangeur douche"
        ]
        
        # Test transcripts for quote generation
        self.test_transcripts = [
            "Need waterproof glue for bathroom tiles and white paint for walls",
            "J'ai besoin de colle pour carrelage salle de bain et peinture blanche",
            "Looking for durable tiles for kitchen floor, something easy to clean",
            "Besoin de tuyaux PVC pour évacuation et robinet pour lavabo",
            "Need electrical cable for new installation and some switches",
            "Carrelage sol extérieur résistant aux intempéries",
            "Isolation phonique pour appartement et peinture plafond",
            "Planches bois pour charpente et vis pour assemblage"
        ]
        
        # Store quote IDs for feedback testing
        self.quote_ids = []
    
    @task(3)
    def search_materials(self):
        """Test material search endpoint"""
        query = random.choice(self.test_queries)
        region = random.choice([
            "Île-de-France", "Provence-Alpes-Côte d'Azur", 
            "Auvergne-Rhône-Alpes", "Occitanie"
        ])
        limit = random.randint(1, 10)
        
        with self.client.get(
            f"/material-price?query={query}&region={region}&limit={limit}",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    response.success()
                else:
                    response.failure("Invalid response format")
            else:
                response.failure(f"HTTP {response.status_code}")
    
    @task(2)
    def generate_proposal(self):
        """Test quote generation endpoint"""
        transcript = random.choice(self.test_transcripts)
        user_type = random.choice(["contractor", "client", "architect"])
        region = random.choice([
            "Île-de-France", "Provence-Alpes-Côte d'Azur", 
            "Auvergne-Rhône-Alpes", "Occitanie"
        ])
        
        payload = {
            "transcript": transcript,
            "user_type": user_type,
            "region": region
        }
        
        with self.client.post(
            "/generate-proposal",
            json=payload,
            catch_response=True
        ) as response:
            if response.status_code == 200:
                data = response.json()
                if "quote_id" in data and "total_estimate" in data:
                    # Store quote ID for feedback testing
                    self.quote_ids.append(data["quote_id"])
                    response.success()
                else:
                    response.failure("Missing required fields in response")
            else:
                response.failure(f"HTTP {response.status_code}")
    
    @task(1)
    def submit_feedback(self):
        """Test feedback submission endpoint"""
        if not self.quote_ids:
            return  # Skip if no quotes available
        
        quote_id = random.choice(self.quote_ids)
        verdict = random.choice([
            "accepted", "rejected", "overpriced", "underpriced", "modified"
        ])
        user_type = random.choice(["contractor", "client"])
        
        payload = {
            "quote_id": quote_id,
            "user_type": user_type,
            "verdict": verdict,
            "comment": f"Test feedback for {verdict} quote"
        }
        
        with self.client.post(
            "/feedback",
            json=payload,
            catch_response=True
        ) as response:
            if response.status_code == 200:
                data = response.json()
                if "feedback_id" in data:
                    response.success()
                else:
                    response.failure("Missing feedback_id in response")
            else:
                response.failure(f"HTTP {response.status_code}")
    
    @task(1)
    def health_check(self):
        """Test health check endpoint"""
        with self.client.get("/health", catch_response=True) as response:
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "healthy":
                    response.success()
                else:
                    response.failure("Health check failed")
            else:
                response.failure(f"HTTP {response.status_code}")

class MaterialSearchUser(HttpUser):
    """Specialized user for material search testing"""
    wait_time = between(0.5, 1.5)
    
    def on_start(self):
        self.search_queries = [
            "tile", "glue", "paint", "pipe", "wire", "wood",
            "carrelage", "colle", "peinture", "tuyau", "fil", "bois"
        ]
    
    @task
    def search_materials_with_filters(self):
        """Test material search with various filters"""
        query = random.choice(self.search_queries)
        filters = []
        
        # Randomly add filters
        if random.random() < 0.5:
            filters.append("region=Île-de-France")
        if random.random() < 0.3:
            filters.append("unit=€/m²")
        if random.random() < 0.2:
            filters.append("quality_score=7")
        if random.random() < 0.4:
            filters.append("vendor=Leroy Merlin")
        
        limit = random.randint(1, 5)
        filters.append(f"limit={limit}")
        
        url = f"/material-price?query={query}&{'&'.join(filters)}"
        
        with self.client.get(url, catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"HTTP {response.status_code}")

class QuoteGenerationUser(HttpUser):
    """Specialized user for quote generation testing"""
    wait_time = between(2, 4)  # Longer wait time for complex operations
    
    def on_start(self):
        self.complex_transcripts = [
            "Need waterproof glue for bathroom tiles, white paint for walls, and some electrical work for new outlets",
            "J'ai besoin de carrelage pour salle de bain, peinture plafond, tuyaux PVC évacuation, et isolation phonique",
            "Complete bathroom renovation: tiles, adhesive, paint, plumbing fixtures, and electrical work",
            "Rénovation complète cuisine: carrelage sol et mur, peinture, plomberie, électricité, et isolation"
        ]
    
    @task
    def generate_complex_proposal(self):
        """Test complex quote generation"""
        transcript = random.choice(self.complex_transcripts)
        user_type = random.choice(["contractor", "architect"])
        region = random.choice([
            "Île-de-France", "Provence-Alpes-Côte d'Azur", 
            "Auvergne-Rhône-Alpes", "Occitanie"
        ])
        project_type = random.choice(["renovation", "new_build", "extension"])
        
        payload = {
            "transcript": transcript,
            "user_type": user_type,
            "region": region,
            "project_type": project_type
        }
        
        with self.client.post(
            "/generate-proposal",
            json=payload,
            catch_response=True
        ) as response:
            if response.status_code == 200:
                data = response.json()
                if "quote_id" in data and "tasks" in data and len(data["tasks"]) > 0:
                    response.success()
                else:
                    response.failure("Invalid quote response")
            else:
                response.failure(f"HTTP {response.status_code}")

# Configuration for different load test scenarios
class LightLoadUser(PricingEngineUser):
    """Light load testing - fewer users, more realistic usage"""
    wait_time = between(3, 6)

class HeavyLoadUser(PricingEngineUser):
    """Heavy load testing - more aggressive usage"""
    wait_time = between(0.5, 1.5)
    
    @task(5)  # More frequent material searches
    def search_materials(self):
        super().search_materials()
    
    @task(3)  # More frequent quote generation
    def generate_proposal(self):
        super().generate_proposal()
