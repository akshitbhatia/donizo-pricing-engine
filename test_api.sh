#!/bin/bash

# Smart Semantic Pricing Engine - API Test Script
# This script tests all the main API endpoints

BASE_URL="http://localhost:8000"

echo "Testing Smart Semantic Pricing Engine API"
echo "============================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to test endpoint
test_endpoint() {
    local method=$1
    local endpoint=$2
    local data=$3
    local description=$4
    
    echo -e "\n${YELLOW}Testing: $description${NC}"
    echo "Endpoint: $method $endpoint"
    
    if [ "$method" = "GET" ]; then
        response=$(curl -s -w "\n%{http_code}" "$BASE_URL$endpoint")
    else
        response=$(curl -s -w "\n%{http_code}" -X "$method" \
            -H "Content-Type: application/json" \
            -d "$data" "$BASE_URL$endpoint")
    fi
    
    # Extract status code (last line)
    status_code=$(echo "$response" | tail -n1)
    # Extract response body (all lines except last)
    body=$(echo "$response" | head -n -1)
    
    if [ "$status_code" -eq 200 ] || [ "$status_code" -eq 201 ]; then
        echo -e "${GREEN}Success (HTTP $status_code)${NC}"
        echo "Response: $body" | jq '.' 2>/dev/null || echo "Response: $body"
    else
        echo -e "${RED}Failed (HTTP $status_code)${NC}"
        echo "Response: $body"
    fi
}

# Test 1: Health Check
test_endpoint "GET" "/" "" "Health Check"

# Test 2: Detailed Health Check
test_endpoint "GET" "/health" "" "Detailed Health Check"

# Test 3: Material Search - Basic
test_endpoint "GET" "/material-price?query=waterproof%20glue&limit=3" "" "Material Search - Waterproof Glue"

# Test 4: Material Search - French Query
test_endpoint "GET" "/material-price?query=colle%20carrelage%20salle%20de%20bain&region=Paris&limit=2" "" "Material Search - French Query"

# Test 5: Material Search - With Filters
test_endpoint "GET" "/material-price?query=tiles&region=Île-de-France&unit=€/m²&quality_score=7&limit=5" "" "Material Search - With Filters"

# Test 6: Quote Generation - Basic
test_endpoint "POST" "/generate-proposal" '{
    "transcript": "Need waterproof glue for bathroom tiles and white paint for the walls",
    "user_type": "contractor",
    "region": "Paris"
}' "Quote Generation - Basic"

# Test 7: Quote Generation - French Transcript
test_endpoint "POST" "/generate-proposal" '{
    "transcript": "J'\''ai besoin de colle pour carrelage salle de bain et peinture blanche pour les murs",
    "user_type": "contractor",
    "region": "Marseille",
    "project_type": "renovation"
}' "Quote Generation - French Transcript"

# Test 8: Quote Generation - Complex Project
test_endpoint "POST" "/generate-proposal" '{
    "transcript": "Complete bathroom renovation: tiles, adhesive, paint, plumbing fixtures, and electrical work",
    "user_type": "architect",
    "region": "Provence-Alpes-Côte d'\''Azur",
    "project_type": "renovation"
}' "Quote Generation - Complex Project"

# Test 9: Feedback Submission (requires a valid quote_id)
echo -e "\n${YELLOW}Testing: Feedback Submission${NC}"
echo "Note: This requires a valid quote_id from a previous quote generation"

# Generate a quote first to get quote_id
quote_response=$(curl -s -X POST \
    -H "Content-Type: application/json" \
    -d '{
        "transcript": "Need waterproof glue for bathroom tiles",
        "user_type": "contractor"
    }' "$BASE_URL/generate-proposal")

quote_id=$(echo "$quote_response" | jq -r '.quote_id' 2>/dev/null)

if [ "$quote_id" != "null" ] && [ "$quote_id" != "" ]; then
    test_endpoint "POST" "/feedback" "{
        \"quote_id\": \"$quote_id\",
        \"user_type\": \"contractor\",
        \"verdict\": \"accepted\",
        \"comment\": \"Good price and materials\"
    }" "Feedback Submission - Accepted"
    
    test_endpoint "POST" "/feedback" "{
        \"quote_id\": \"$quote_id\",
        \"user_type\": \"client\",
        \"verdict\": \"overpriced\",
        \"comment\": \"Materials seem expensive for this region\"
    }" "Feedback Submission - Overpriced"
else
    echo -e "${RED}Could not generate quote for feedback testing${NC}"
fi

# Test 10: Error Cases
echo -e "\n${YELLOW}Testing Error Cases${NC}"

# Empty query
test_endpoint "GET" "/material-price?query=" "" "Error Case - Empty Query"

# Invalid limit
test_endpoint "GET" "/material-price?query=tiles&limit=25" "" "Error Case - Invalid Limit"

# Empty transcript
test_endpoint "POST" "/generate-proposal" '{
    "transcript": "",
    "user_type": "contractor"
}' "Error Case - Empty Transcript"

# Invalid user type
test_endpoint "POST" "/generate-proposal" '{
    "transcript": "Need waterproof glue for bathroom tiles",
    "user_type": "invalid_type"
}' "Error Case - Invalid User Type"

# Non-existent endpoint
test_endpoint "GET" "/nonexistent-endpoint" "" "Error Case - Non-existent Endpoint"

# Performance Test
echo -e "\n${YELLOW}Performance Test - Concurrent Requests${NC}"
echo "Testing 10 concurrent material searches..."

# Start background processes
for i in {1..10}; do
    (curl -s "$BASE_URL/material-price?query=tiles&limit=1" > /dev/null && echo "Request $i completed") &
done

# Wait for all background processes to complete
wait
echo -e "${GREEN}All concurrent requests completed${NC}"

# Summary
echo -e "\n${GREEN}API Testing Complete!${NC}"
echo "============================================="
echo "All endpoints have been tested."
echo "Check the output above for any failures."
echo ""
echo "To run the application:"
echo "  uvicorn app.main:app --reload"
echo ""
echo "To run with Docker:"
echo "  docker-compose up"
echo ""
echo "API Documentation:"
echo "  $BASE_URL/docs"
