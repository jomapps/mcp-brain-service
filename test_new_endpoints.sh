#!/bin/bash

# Test script for new batch endpoints
# Usage: ./test_new_endpoints.sh

set -e

API_KEY="ae6e18cb408bc7128f23585casdlaelwlekoqdsldsa"
BASE_URL="http://localhost:8002/api/v1"

echo "========================================="
echo "Testing Brain Service Batch Endpoints"
echo "========================================="
echo ""

# Test 1: Batch Node Creation
echo "1. Testing POST /api/v1/nodes/batch"
echo "-----------------------------------"
curl -X POST "$BASE_URL/nodes/batch" \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "nodes": [
      {
        "type": "GatherItem",
        "content": "Test story content about a hero journey",
        "projectId": "507f1f77bcf86cd799439011",
        "properties": {
          "department": "story",
          "isAutomated": true,
          "iteration": 1
        }
      },
      {
        "type": "GatherItem",
        "content": "Test character description of the protagonist",
        "projectId": "507f1f77bcf86cd799439011",
        "properties": {
          "department": "character",
          "isAutomated": true
        }
      }
    ]
  }' | jq .

echo ""
echo ""

# Test 2: Duplicate Search
echo "2. Testing POST /api/v1/search/duplicates"
echo "-----------------------------------"
curl -X POST "$BASE_URL/search/duplicates" \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Test story content about a hero journey",
    "projectId": "507f1f77bcf86cd799439011",
    "threshold": 0.85,
    "limit": 5
  }' | jq .

echo ""
echo ""

# Test 3: Department Context
echo "3. Testing GET /api/v1/context/department"
echo "-----------------------------------"
curl -X GET "$BASE_URL/context/department?projectId=507f1f77bcf86cd799439011&department=character&previousDepartments=story&limit=10" \
  -H "Authorization: Bearer $API_KEY" | jq .

echo ""
echo ""

# Test 4: Coverage Analysis
echo "4. Testing POST /api/v1/analyze/coverage"
echo "-----------------------------------"
curl -X POST "$BASE_URL/analyze/coverage" \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "projectId": "507f1f77bcf86cd799439011",
    "department": "story",
    "gatherItems": [
      {
        "content": "Plot overview: The story follows a hero on a transformative journey",
        "summary": "Main plot structure"
      },
      {
        "content": "Character development: The protagonist grows through challenges and setbacks",
        "summary": "Character arc"
      },
      {
        "content": "Thematic elements: Explores themes of redemption and sacrifice",
        "summary": "Core themes"
      }
    ],
    "departmentDescription": "Story department handles narrative structure, plot development, pacing, and thematic elements"
  }' | jq .

echo ""
echo ""
echo "========================================="
echo "All tests completed!"
echo "========================================="

