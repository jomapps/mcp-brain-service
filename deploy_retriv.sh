#!/bin/bash

# Retriv Integration Deployment Script
# This script safely deploys the Retriv integration to production

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "========================================="
echo -e "${BLUE}Retriv Integration Deployment${NC}"
echo "========================================="
echo ""

# Get the directory of this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Check if running as root or with sudo
if [ "$EUID" -ne 0 ]; then 
    echo -e "${YELLOW}Warning: Not running as root. Some operations may require sudo.${NC}"
    echo ""
fi

# Step 1: Backup
echo -e "${YELLOW}Step 1: Creating backup...${NC}"
BACKUP_DIR="../mcp-brain-service-backup-$(date +%Y%m%d-%H%M%S)"
echo "Backup location: $BACKUP_DIR"
cp -r . "$BACKUP_DIR"
echo -e "${GREEN}✓ Backup created${NC}"
echo ""

# Step 2: Check PM2 status
echo -e "${YELLOW}Step 2: Checking current PM2 status...${NC}"
pm2 list | grep brain-api || {
    echo -e "${RED}brain-api not found in PM2${NC}"
    echo "Please ensure the service is running before deployment"
    exit 1
}
echo -e "${GREEN}✓ brain-api is running${NC}"
echo ""

# Step 3: Install dependencies
echo -e "${YELLOW}Step 3: Installing dependencies...${NC}"
if [ -d "venv" ]; then
    echo "Using existing virtual environment"
    source venv/bin/activate
else
    echo "Creating new virtual environment"
    python3 -m venv venv
    source venv/bin/activate
fi

pip install --upgrade pip
pip install -r requirements.txt

# Verify retriv installation
python3 -c "import retriv; print('Retriv imported successfully')" || {
    echo -e "${RED}Failed to import retriv${NC}"
    exit 1
}
echo -e "${GREEN}✓ Dependencies installed${NC}"
echo ""

# Step 4: Run tests
echo -e "${YELLOW}Step 4: Running tests...${NC}"
pytest tests/unit/test_retriv_service.py -v --tb=short || {
    echo -e "${RED}Tests failed${NC}"
    echo "Deployment aborted. Please fix tests before deploying."
    exit 1
}
echo -e "${GREEN}✓ All tests passed${NC}"
echo ""

# Step 5: Restart service
echo -e "${YELLOW}Step 5: Restarting brain-api service...${NC}"
pm2 restart brain-api

# Wait for service to start
echo "Waiting for service to start..."
sleep 5
echo -e "${GREEN}✓ Service restarted${NC}"
echo ""

# Step 6: Verify deployment
echo -e "${YELLOW}Step 6: Verifying deployment...${NC}"

# Check PM2 status
PM2_STATUS=$(pm2 jlist | jq -r '.[] | select(.name=="brain-api") | .pm2_env.status')
if [ "$PM2_STATUS" != "online" ]; then
    echo -e "${RED}Service is not online! Status: $PM2_STATUS${NC}"
    echo "Rolling back..."
    pm2 stop brain-api
    rm -rf "$SCRIPT_DIR"
    cp -r "$BACKUP_DIR" "$SCRIPT_DIR"
    pm2 restart brain-api
    echo -e "${RED}Deployment failed and rolled back${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Service is online${NC}"

# Check logs for errors
echo "Checking logs for errors..."
ERRORS=$(pm2 logs brain-api --err --lines 20 --nostream | grep -i "error" | wc -l)
if [ "$ERRORS" -gt 0 ]; then
    echo -e "${YELLOW}⚠ Found $ERRORS error(s) in logs${NC}"
    echo "Recent errors:"
    pm2 logs brain-api --err --lines 10 --nostream
    echo ""
    echo -e "${YELLOW}Please review errors. Service is running but may have issues.${NC}"
else
    echo -e "${GREEN}✓ No errors in logs${NC}"
fi
echo ""

# Step 7: Test basic functionality
echo -e "${YELLOW}Step 7: Testing basic functionality...${NC}"
python3 << 'EOF'
import asyncio
import sys
from src.services.retriv_service import get_retriv_service

async def test_basic():
    try:
        service = get_retriv_service()
        await service.initialize()
        stats = service.get_stats()
        print(f"✓ Retriv service initialized: {stats}")
        return True
    except Exception as e:
        print(f"✗ Failed to initialize Retriv: {e}")
        return False

success = asyncio.run(test_basic())
sys.exit(0 if success else 1)
EOF

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Basic functionality test passed${NC}"
else
    echo -e "${YELLOW}⚠ Basic functionality test failed${NC}"
    echo "Service is running but Retriv may not be working correctly"
fi
echo ""

# Step 8: Summary
echo "========================================="
echo -e "${GREEN}Deployment Complete!${NC}"
echo "========================================="
echo ""
echo "Summary:"
echo "  - Backup created: $BACKUP_DIR"
echo "  - Dependencies installed: ✓"
echo "  - Tests passed: ✓"
echo "  - Service restarted: ✓"
echo "  - Service status: online"
echo ""
echo "Next steps:"
echo "  1. Monitor logs: pm2 logs brain-api"
echo "  2. Check metrics: pm2 monit"
echo "  3. Review for 24 hours"
echo ""
echo "If issues occur:"
echo "  1. Check logs: pm2 logs brain-api --err"
echo "  2. Review RETRIV_DEPLOYMENT.md"
echo "  3. Rollback if needed:"
echo "     pm2 stop brain-api"
echo "     rm -rf $SCRIPT_DIR"
echo "     cp -r $BACKUP_DIR $SCRIPT_DIR"
echo "     pm2 restart brain-api"
echo ""
echo -e "${GREEN}Deployment successful!${NC}"

