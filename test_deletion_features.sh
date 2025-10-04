#!/bin/bash

# Test script for deletion and validation features
# Tests:
# 1. Content validation (prevents invalid data)
# 2. DELETE endpoint (removes specific nodes)
# 3. Cleanup script (bulk deletion)

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
API_URL="${API_URL:-http://localhost:8000}"
API_KEY="${BRAIN_SERVICE_API_KEY:-ae6e18cb408bc7128f23585casdlaelwlekoqdsldsa}"
PROJECT_ID="test-deletion-$(date +%s)"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Testing Deletion & Validation Features${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo "API URL: $API_URL"
echo "Project ID: $PROJECT_ID"
echo ""

# Function to make API calls
api_call() {
    local method=$1
    local endpoint=$2
    local data=$3
    
    if [ "$method" = "GET" ] || [ "$method" = "DELETE" ]; then
        curl -s -X "$method" \
            -H "Authorization: Bearer $API_KEY" \
            -H "Content-Type: application/json" \
            "$API_URL$endpoint"
    else
        curl -s -X "$method" \
            -H "Authorization: Bearer $API_KEY" \
            -H "Content-Type: application/json" \
            -d "$data" \
            "$API_URL$endpoint"
    fi
}

# Test counter
TESTS_PASSED=0
TESTS_FAILED=0

# Test function
run_test() {
    local test_name=$1
    local test_command=$2
    
    echo -e "${YELLOW}Testing: $test_name${NC}"
    
    if eval "$test_command"; then
        echo -e "${GREEN}✅ PASSED: $test_name${NC}"
        ((TESTS_PASSED++))
    else
        echo -e "${RED}❌ FAILED: $test_name${NC}"
        ((TESTS_FAILED++))
    fi
    echo ""
}

# ============================================================================
# TEST 1: Content Validation - Empty Content
# ============================================================================
test_empty_content() {
    echo "  Attempting to create node with empty content..."
    
    response=$(api_call POST "/api/v1/nodes" '{
        "type": "test",
        "content": "",
        "projectId": "'"$PROJECT_ID"'",
        "properties": {}
    }')
    
    # Should return 400 error
    if echo "$response" | grep -q "validation_failed"; then
        echo "  Response: $response"
        return 0
    else
        echo "  Unexpected response: $response"
        return 1
    fi
}

run_test "Validation: Empty content rejected" test_empty_content

# ============================================================================
# TEST 2: Content Validation - Error Message
# ============================================================================
test_error_message() {
    echo "  Attempting to create node with error message..."
    
    response=$(api_call POST "/api/v1/nodes" '{
        "type": "test",
        "content": "Error: No user message found",
        "projectId": "'"$PROJECT_ID"'",
        "properties": {}
    }')
    
    # Should return 400 error
    if echo "$response" | grep -q "validation_failed"; then
        echo "  Response: $response"
        return 0
    else
        echo "  Unexpected response: $response"
        return 1
    fi
}

run_test "Validation: Error message rejected" test_error_message

# ============================================================================
# TEST 3: Content Validation - Too Short
# ============================================================================
test_short_content() {
    echo "  Attempting to create node with short content..."
    
    response=$(api_call POST "/api/v1/nodes" '{
        "type": "test",
        "content": "short",
        "projectId": "'"$PROJECT_ID"'",
        "properties": {}
    }')
    
    # Should return 400 error
    if echo "$response" | grep -q "validation_failed"; then
        echo "  Response: $response"
        return 0
    else
        echo "  Unexpected response: $response"
        return 1
    fi
}

run_test "Validation: Short content rejected" test_short_content

# ============================================================================
# TEST 4: Content Validation - Valid Content Accepted
# ============================================================================
test_valid_content() {
    echo "  Creating node with valid content..."
    
    response=$(api_call POST "/api/v1/nodes" '{
        "type": "test",
        "content": "This is a valid test node with sufficient content length",
        "projectId": "'"$PROJECT_ID"'",
        "properties": {"test": "true"}
    }')
    
    # Should succeed and return node ID
    if echo "$response" | grep -q '"id"'; then
        VALID_NODE_ID=$(echo "$response" | grep -o '"id":"[^"]*"' | cut -d'"' -f4)
        echo "  Created node ID: $VALID_NODE_ID"
        return 0
    else
        echo "  Unexpected response: $response"
        return 1
    fi
}

run_test "Validation: Valid content accepted" test_valid_content

# ============================================================================
# TEST 5: DELETE Endpoint - Delete Valid Node
# ============================================================================
test_delete_node() {
    if [ -z "$VALID_NODE_ID" ]; then
        echo "  Skipping: No valid node ID available"
        return 1
    fi
    
    echo "  Deleting node ID: $VALID_NODE_ID"
    
    response=$(api_call DELETE "/api/v1/nodes/$VALID_NODE_ID?project_id=$PROJECT_ID" "")
    
    # Should succeed
    if echo "$response" | grep -q '"status":"success"'; then
        echo "  Response: $response"
        return 0
    else
        echo "  Unexpected response: $response"
        return 1
    fi
}

run_test "DELETE: Successfully delete node" test_delete_node

# ============================================================================
# TEST 6: DELETE Endpoint - Node Not Found
# ============================================================================
test_delete_nonexistent() {
    echo "  Attempting to delete non-existent node..."
    
    response=$(api_call DELETE "/api/v1/nodes/nonexistent-id-12345?project_id=$PROJECT_ID" "")
    
    # Should return 404
    if echo "$response" | grep -q "node_not_found"; then
        echo "  Response: $response"
        return 0
    else
        echo "  Unexpected response: $response"
        return 1
    fi
}

run_test "DELETE: Non-existent node returns 404" test_delete_nonexistent

# ============================================================================
# TEST 7: Cleanup Script - Dry Run
# ============================================================================
test_cleanup_dry_run() {
    echo "  Running cleanup script in dry-run mode..."
    
    if python scripts/cleanup_invalid_nodes.py --dry-run --project-id "$PROJECT_ID" 2>&1 | grep -q "Dry run completed"; then
        return 0
    else
        echo "  Cleanup script failed or not found"
        return 1
    fi
}

run_test "Cleanup Script: Dry run executes" test_cleanup_dry_run

# ============================================================================
# TEST 8: Cleanup Script - List Projects
# ============================================================================
test_cleanup_list_projects() {
    echo "  Listing projects with cleanup script..."
    
    if python scripts/cleanup_invalid_nodes.py --list-projects 2>&1 | grep -q "PROJECT STATISTICS"; then
        return 0
    else
        echo "  Failed to list projects"
        return 1
    fi
}

run_test "Cleanup Script: List projects" test_cleanup_list_projects

# ============================================================================
# TEST 9: Integration Test - Create Invalid, Verify Rejected, Create Valid, Delete
# ============================================================================
test_full_workflow() {
    echo "  Running full workflow test..."
    
    # Try to create invalid node
    invalid_response=$(api_call POST "/api/v1/nodes" '{
        "type": "test",
        "content": "Error: Invalid data",
        "projectId": "'"$PROJECT_ID"'",
        "properties": {}
    }')
    
    if ! echo "$invalid_response" | grep -q "validation_failed"; then
        echo "  Failed: Invalid content was not rejected"
        return 1
    fi
    
    # Create valid node
    valid_response=$(api_call POST "/api/v1/nodes" '{
        "type": "test",
        "content": "This is a valid workflow test node with good content",
        "projectId": "'"$PROJECT_ID"'",
        "properties": {"workflow": "test"}
    }')
    
    if ! echo "$valid_response" | grep -q '"id"'; then
        echo "  Failed: Valid content was rejected"
        return 1
    fi
    
    workflow_node_id=$(echo "$valid_response" | grep -o '"id":"[^"]*"' | cut -d'"' -f4)
    echo "  Created workflow node: $workflow_node_id"
    
    # Delete the node
    delete_response=$(api_call DELETE "/api/v1/nodes/$workflow_node_id?project_id=$PROJECT_ID" "")
    
    if ! echo "$delete_response" | grep -q '"status":"success"'; then
        echo "  Failed: Could not delete node"
        return 1
    fi
    
    echo "  Full workflow completed successfully"
    return 0
}

run_test "Integration: Full workflow (reject invalid, create valid, delete)" test_full_workflow

# ============================================================================
# Summary
# ============================================================================
echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Test Summary${NC}"
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}Passed: $TESTS_PASSED${NC}"
echo -e "${RED}Failed: $TESTS_FAILED${NC}"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ All tests passed!${NC}"
    exit 0
else
    echo -e "${RED}❌ Some tests failed${NC}"
    exit 1
fi

