#!/usr/bin/env python3
"""
API tests for Smart Semantic Pricing Engine
"""

import pytest
import asyncio
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import json

from app.main import app
from app.database import Base, get_db
from app.config import settings

# Test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

@pytest.fixture(scope="module")
def setup_database():
    """Setup test database"""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

class TestHealthEndpoints:
    """Test health check endpoints"""
    
    def test_root_endpoint(self):
        """Test root endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Smart Semantic Pricing Engine v1.0.0"
        assert data["status"] == "healthy"
    
    def test_health_endpoint(self):
        """Test health endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "services" in data

class TestMaterialSearch:
    """Test material search functionality"""
    
    def test_material_search_basic(self, setup_database):
        """Test basic material search"""
        response = client.get("/material-price?query=waterproof%20glue")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_material_search_with_filters(self, setup_database):
        """Test material search with filters"""
        response = client.get(
            "/material-price?query=tiles&region=Paris&limit=3"
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) <= 3
    
    def test_material_search_empty_query(self, setup_database):
        """Test material search with empty query"""
        response = client.get("/material-price?query=")
        assert response.status_code == 400
    
    def test_material_search_invalid_limit(self, setup_database):
        """Test material search with invalid limit"""
        response = client.get("/material-price?query=tiles&limit=25")
        assert response.status_code == 422  # Validation error

class TestQuoteGeneration:
    """Test quote generation functionality"""
    
    def test_generate_proposal_basic(self, setup_database):
        """Test basic quote generation"""
        request_data = {
            "transcript": "Need waterproof glue for bathroom tiles and some white paint for the walls",
            "user_type": "contractor",
            "region": "Paris"
        }
        response = client.post("/generate-proposal", json=request_data)
        assert response.status_code == 200
        data = response.json()
        assert "quote_id" in data
        assert "total_estimate" in data
        assert "tasks" in data
        assert isinstance(data["tasks"], list)
    
    def test_generate_proposal_french_transcript(self, setup_database):
        """Test quote generation with French transcript"""
        request_data = {
            "transcript": "J'ai besoin de colle pour carrelage salle de bain et peinture blanche pour les murs",
            "user_type": "contractor",
            "region": "Marseille"
        }
        response = client.post("/generate-proposal", json=request_data)
        assert response.status_code == 200
        data = response.json()
        assert "quote_id" in data
    
    def test_generate_proposal_empty_transcript(self, setup_database):
        """Test quote generation with empty transcript"""
        request_data = {
            "transcript": "",
            "user_type": "contractor"
        }
        response = client.post("/generate-proposal", json=request_data)
        assert response.status_code == 400
    
    def test_generate_proposal_short_transcript(self, setup_database):
        """Test quote generation with short transcript"""
        request_data = {
            "transcript": "tiles",
            "user_type": "contractor"
        }
        response = client.post("/generate-proposal", json=request_data)
        assert response.status_code == 400
    
    def test_generate_proposal_invalid_user_type(self, setup_database):
        """Test quote generation with invalid user type"""
        request_data = {
            "transcript": "Need waterproof glue for bathroom tiles",
            "user_type": "invalid_type"
        }
        response = client.post("/generate-proposal", json=request_data)
        assert response.status_code == 422  # Validation error

class TestFeedback:
    """Test feedback functionality"""
    
    def test_submit_feedback_basic(self, setup_database):
        """Test basic feedback submission"""
        # First create a quote
        quote_request = {
            "transcript": "Need waterproof glue for bathroom tiles",
            "user_type": "contractor"
        }
        quote_response = client.post("/generate-proposal", json=quote_request)
        quote_data = quote_response.json()
        quote_id = quote_data["quote_id"]
        
        # Submit feedback
        feedback_data = {
            "quote_id": quote_id,
            "user_type": "contractor",
            "verdict": "accepted",
            "comment": "Good price and materials"
        }
        response = client.post("/feedback", json=feedback_data)
        assert response.status_code == 200
        data = response.json()
        assert "feedback_id" in data
        assert data["quote_id"] == quote_id
    
    def test_submit_feedback_invalid_quote_id(self, setup_database):
        """Test feedback submission with invalid quote ID"""
        feedback_data = {
            "quote_id": "invalid-uuid",
            "user_type": "contractor",
            "verdict": "accepted"
        }
        response = client.post("/feedback", json=feedback_data)
        assert response.status_code == 400
    
    def test_submit_feedback_invalid_verdict(self, setup_database):
        """Test feedback submission with invalid verdict"""
        feedback_data = {
            "quote_id": "123e4567-e89b-12d3-a456-426614174000",
            "user_type": "contractor",
            "verdict": "invalid_verdict"
        }
        response = client.post("/feedback", json=feedback_data)
        assert response.status_code == 400
    
    def test_submit_feedback_nonexistent_quote(self, setup_database):
        """Test feedback submission for non-existent quote"""
        feedback_data = {
            "quote_id": "123e4567-e89b-12d3-a456-426614174000",
            "user_type": "contractor",
            "verdict": "accepted"
        }
        response = client.post("/feedback", json=feedback_data)
        assert response.status_code == 500  # Quote not found error

class TestErrorHandling:
    """Test error handling"""
    
    def test_404_endpoint(self):
        """Test 404 handling"""
        response = client.get("/nonexistent-endpoint")
        assert response.status_code == 404
    
    def test_invalid_json(self):
        """Test invalid JSON handling"""
        response = client.post("/generate-proposal", data="invalid json")
        assert response.status_code == 422

def test_concurrent_requests(setup_database):
    """Test concurrent request handling"""
    import threading
    import time
    
    results = []
    errors = []
    
    def make_request():
        try:
            response = client.get("/material-price?query=tiles&limit=1")
            results.append(response.status_code)
        except Exception as e:
            errors.append(str(e))
    
    # Create multiple threads
    threads = []
    for _ in range(10):
        thread = threading.Thread(target=make_request)
        threads.append(thread)
        thread.start()
    
    # Wait for all threads to complete
    for thread in threads:
        thread.join()
    
    # Check results
    assert len(errors) == 0, f"Errors occurred: {errors}"
    assert all(status == 200 for status in results), f"Some requests failed: {results}"

if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
