# Smart Semantic Pricing Engine v0

A semantic material pricing engine that survives real-world chaos: fuzzy queries, contradictory input, price/region constraints, VAT rules, confidence scoring, and constant change.

## Ultimate Objective

Build a core module of Donizo's pricing brain - the system that determines how every renovation job on Earth gets priced.

## Architecture Overview

### Core Components
1. **Data Ingestion Layer** - Material catalog with 5,000+ records
2. **Semantic Search Engine** - Vector embeddings with pgvector
3. **Query Processing** - Multi-language fuzzy matching
4. **Pricing Engine** - VAT, margins, regional pricing
5. **Quote Generator** - Task-based proposal generation
6. **Feedback System** - Continuous learning and improvement

### Technology Stack
- **Backend**: FastAPI (Python)
- **Vector DB**: PostgreSQL + pgvector
- **Embeddings**: Sentence Transformers (BGE-large-en-v1.5)
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Caching**: Redis
- **Async Tasks**: Celery
- **Containerization**: Docker

## Quick Start

### Prerequisites
- Python 3.9+
- PostgreSQL with pgvector extension
- Redis (optional, for caching)

### Installation
```bash
# Clone and setup
git clone <repository>
cd donizo-pricing-engine
pip install -r requirements.txt

# Setup environment
cp .env.example .env
# Edit .env with your database credentials

# Initialize database
python scripts/init_db.py

# Run the application
uvicorn app.main:app --reload
```

### API Endpoints
- `GET /material-price` - Semantic material search
- `POST /generate-proposal` - Generate quotes
- `POST /feedback` - Submit feedback for learning

## Embedding + DB Rationale

### Why pgvector?
- **Production Ready**: PostgreSQL is battle-tested for production workloads
- **ACID Compliance**: Ensures data consistency for pricing operations
- **Scalability**: Can handle millions of vectors with proper indexing
- **Ecosystem**: Rich tooling and monitoring capabilities
- **Cost Effective**: No additional cloud service costs

### Why BGE-large-en-v1.5?
- **Multilingual**: Handles French, English, and other languages
- **Domain Specific**: Trained on construction/technical text
- **Performance**: 768 dimensions, good balance of speed/accuracy
- **Open Source**: No API costs or rate limits

## Schema Design

### Materials Table
```sql
CREATE TABLE materials (
    id SERIAL PRIMARY KEY,
    material_name VARCHAR(255) NOT NULL,
    description TEXT,
    unit_price DECIMAL(10,2),
    unit VARCHAR(50),
    region VARCHAR(100),
    vendor VARCHAR(255),
    quality_score INTEGER,
    embedding vector(768),
    source_url TEXT,
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### Quotes Table
```sql
CREATE TABLE quotes (
    id UUID PRIMARY KEY,
    transcript TEXT,
    total_estimate DECIMAL(10,2),
    confidence_score DECIMAL(3,2),
    user_type VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW()
);
```

### Feedback Table
```sql
CREATE TABLE feedback (
    id SERIAL PRIMARY KEY,
    quote_id UUID REFERENCES quotes(id),
    user_type VARCHAR(50),
    verdict VARCHAR(50),
    comment TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

## Confidence & Margin Logic

### Confidence Scoring
1. **Semantic Similarity** (40%): Vector similarity score
2. **Regional Match** (25%): Geographic relevance
3. **Price Range** (20%): Historical price validation
4. **Vendor Reliability** (15%): Supplier trust score

### Margin Protection
- **Base Margin**: 25% on materials
- **Regional Adjustments**: ±10% based on market data
- **Quality Multipliers**: 1.1x for premium, 0.9x for economy
- **VAT Rates**: 10% (renovation), 20% (new build)

## Degradation & Fallback Logic

### Query Processing
1. **Primary**: Semantic search with BGE embeddings
2. **Fallback**: Keyword-based search with fuzzy matching
3. **Emergency**: Return most popular items in region

### Pricing Fallbacks
1. **Exact Match**: Use stored price
2. **Regional Average**: Calculate from similar materials
3. **National Average**: Fallback to country-wide pricing
4. **Manual Review**: Flag for human intervention

## Second-Order System Thinking

### 1. What breaks at 1M+ products and 10K daily queries?

**Performance Bottlenecks:**
- Vector similarity search becomes slow without proper indexing
- Database connection pooling limits
- Memory usage for large embedding matrices

**Solutions:**
- Implement HNSW indexing on pgvector
- Use connection pooling (pgBouncer)
- Implement caching layer with Redis
- Consider sharding by region

**Scalability Issues:**
- Single point of failure in database
- Embedding generation bottleneck
- Real-time price updates overwhelming system

**Solutions:**
- Database read replicas
- Async embedding generation with Celery
- Event-driven architecture for price updates

### 2. Tradeoffs: Accuracy vs Latency vs Confidence

**Accuracy vs Latency:**
- **High Accuracy**: Use larger embedding models (slower)
- **Low Latency**: Use smaller models (less accurate)
- **Solution**: Hybrid approach with model ensemble

**Confidence vs Speed:**
- **High Confidence**: Multiple validation checks (slower)
- **High Speed**: Single-pass processing (lower confidence)
- **Solution**: Confidence-based routing

**Real-world Impact:**
- Contractors need fast responses (<500ms)
- Pricing accuracy directly affects profit margins
- Confidence scores help with decision making

### 3. Learning and Improvement Over Time

**Feedback Integration:**
- Track quote acceptance/rejection rates
- Analyze feedback patterns by region/material
- Adjust confidence scoring based on historical accuracy

**Continuous Learning:**
- Retrain embeddings with new material data
- Update pricing models based on market changes
- A/B test different margin strategies

**Adaptive Systems:**
- Dynamic confidence thresholds
- Regional pricing adjustments
- Vendor reliability scoring updates

### 4. Real-time Supplier API Integration

**Challenges:**
- Rate limiting from suppliers
- Inconsistent API formats
- Real-time vs batch processing

**Architecture:**
- API gateway with rate limiting
- Standardized data transformation layer
- Event-driven updates with webhooks
- Fallback to cached data during outages

**Implementation:**
- Celery workers for async API calls
- Circuit breakers for API resilience
- Data validation and sanitization

### 5. Three Signals for Quote Rejection Improvement

**1. Material Selection Signals:**
- Which materials were rejected vs accepted
- Regional patterns in material preferences
- Quality vs price tradeoff analysis

**2. Pricing Accuracy Signals:**
- Gap between estimated and actual prices
- Regional pricing variations
- Seasonal price fluctuations

**3. User Behavior Signals:**
- Quote modification patterns
- Time-to-acceptance metrics
- User type preferences (contractor vs client)

## Bonus Features Implemented

- **Multi-language Support**: French/English query processing
- **Query Caching**: Redis-based response caching
- **Confidence Logging**: Detailed confidence vs accuracy tracking
- **Regional Pricing**: Dynamic multipliers based on location
- **Versioned Quotes**: Complete audit trail of pricing changes
- **JSON Schema Validation**: Comprehensive input/output validation

## Testing

### API Testing
```bash
# Test material search
curl "http://localhost:8000/material-price?query=waterproof%20glue&region=Paris"

# Test quote generation
curl -X POST "http://localhost:8000/generate-proposal" \
  -H "Content-Type: application/json" \
  -d '{"transcript": "Need waterproof glue for bathroom tiles"}'

# Test feedback
curl -X POST "http://localhost:8000/feedback" \
  -H "Content-Type: application/json" \
  -d '{"quote_id": "abc123", "verdict": "accepted", "comment": "Good price"}'
```

### Load Testing
```bash
# Install locust
pip install locust

# Run load test
locust -f tests/load_test.py
```

## Monitoring & Observability

- **Metrics**: Response times, confidence scores, error rates
- **Logging**: Structured logging with correlation IDs
- **Tracing**: Distributed tracing for request flows
- **Alerts**: SLA monitoring and alerting

## Deployment

### Docker
```bash
docker build -t donizo-pricing-engine .
docker run -p 8000:8000 donizo-pricing-engine
```

### Production Considerations
- Use managed PostgreSQL with pgvector
- Implement proper logging and monitoring
- Set up CI/CD pipelines
- Configure auto-scaling based on load
- Implement proper security measures

## License

MIT License - see LICENSE file for details.
# donizo-pricing-engine
