# Retriv Integration Deployment Guide

## Overview

This guide covers the deployment of the Retriv hybrid search integration to the production MCP Brain Service running at https://brain.ft.tc.

## What is Retriv?

Retriv is a hybrid search library that combines:
- **BM25** (keyword-based search) - catches exact word matches
- **Dense embeddings** (semantic search) - understands meaning and context

This provides better search results than semantic search alone, especially for queries like "Aladdin's vest in scene 3" where both exact keywords and semantic understanding matter.

## Pre-Deployment Checklist

### 1. Verify Current System Status

```bash
# Check PM2 status
pm2 list

# Check brain-api is running
pm2 info brain-api

# Check current logs
pm2 logs brain-api --lines 50
```

### 2. Backup Current State

```bash
# Backup current service
cd /var/www/movie-generation-platform/services/mcp-brain-service
cp -r . ../mcp-brain-service-backup-$(date +%Y%m%d-%H%M%S)

# Note current PM2 configuration
pm2 save
```

### 3. Review Changes

Files modified/added:
- ✅ `requirements.txt` - Added retriv>=0.2.4 and test dependencies
- ✅ `src/services/retriv_service.py` - New Retriv service wrapper
- ✅ `tests/unit/test_retriv_service.py` - Unit tests
- ✅ `tests/integration/test_retriv_integration.py` - Integration tests
- ✅ `test_retriv_setup.sh` - Test automation script

## Deployment Steps

### Step 1: Run Pre-Deployment Tests

```bash
cd /var/www/movie-generation-platform/services/mcp-brain-service

# Make test script executable
chmod +x test_retriv_setup.sh

# Run comprehensive tests
./test_retriv_setup.sh
```

**Expected Output:**
- ✓ Python version check
- ✓ Virtual environment created/activated
- ✓ Dependencies installed
- ✓ Retriv imported successfully
- ✓ Unit tests passed
- ✓ Integration tests passed (or skipped if retriv has issues)
- ✓ Quick functionality test passed

**If tests fail:**
- Review error messages
- Check Python version (should be 3.11+)
- Verify network connectivity for package downloads
- Check disk space for model downloads

### Step 2: Install Dependencies in Production

```bash
cd /var/www/movie-generation-platform/services/mcp-brain-service

# Activate virtual environment (if using one)
source venv/bin/activate

# Install new dependencies
pip install -r requirements.txt

# Verify installation
python3 -c "import retriv; print('Retriv version:', retriv.__version__)"
```

### Step 3: Test in Staging (if available)

If you have a staging environment:

```bash
# Start service in test mode
python3 src/main.py --test-mode

# Run integration tests against running service
pytest tests/integration/ -v
```

### Step 4: Deploy to Production

```bash
# Restart the brain-api service
pm2 restart brain-api

# Monitor logs for any errors
pm2 logs brain-api --lines 100

# Check service health
curl https://brain.ft.tc/health
```

### Step 5: Verify Deployment

```bash
# Check PM2 status
pm2 list

# Verify brain-api is online
pm2 info brain-api

# Check for errors in logs
pm2 logs brain-api --err --lines 50

# Test basic functionality
curl https://brain.ft.tc/health
```

### Step 6: Smoke Tests

Run these manual tests to verify the service is working:

```bash
# Test 1: Service health
curl https://brain.ft.tc/health

# Test 2: Basic search (if you have a test endpoint)
# curl -X POST https://brain.ft.tc/search \
#   -H "Content-Type: application/json" \
#   -d '{"query": "test", "project_id": "test_proj"}'
```

## Post-Deployment Monitoring

### Monitor for 24 Hours

```bash
# Watch logs in real-time
pm2 logs brain-api

# Check memory usage
pm2 monit

# Check for errors
pm2 logs brain-api --err
```

### Key Metrics to Watch

1. **Service Status**: Should remain "online"
2. **Memory Usage**: May increase slightly due to Retriv models
3. **Response Times**: Should remain similar or improve
4. **Error Rate**: Should not increase

### Expected Behavior

- Service starts normally
- No import errors for retriv
- Retriv initializes on first use (lazy loading)
- Search results may improve for keyword-heavy queries

## Rollback Plan

If issues occur, rollback immediately:

```bash
# Stop current service
pm2 stop brain-api

# Restore backup
cd /var/www/movie-generation-platform/services
rm -rf mcp-brain-service
cp -r mcp-brain-service-backup-YYYYMMDD-HHMMSS mcp-brain-service

# Restart service
pm2 restart brain-api

# Verify rollback
pm2 logs brain-api --lines 50
```

## Troubleshooting

### Issue: Retriv fails to import

**Symptoms:**
```
ImportError: No module named 'retriv'
```

**Solution:**
```bash
# Ensure you're in the correct virtual environment
source venv/bin/activate

# Reinstall retriv
pip install retriv>=0.2.4

# Verify installation
python3 -c "import retriv; print(retriv.__version__)"
```

### Issue: Service fails to start

**Symptoms:**
```
pm2 status shows "errored" or "stopped"
```

**Solution:**
```bash
# Check error logs
pm2 logs brain-api --err --lines 100

# Try starting manually to see full error
cd /var/www/movie-generation-platform/services/mcp-brain-service
python3 src/main.py

# If it's a retriv issue, the service will gracefully degrade
# (Retriv is optional and won't crash the service)
```

### Issue: High memory usage

**Symptoms:**
```
Memory usage increases significantly after deployment
```

**Solution:**
- Retriv downloads sentence-transformers models (~80MB)
- This is normal and expected
- Models are cached after first download
- Monitor with: `pm2 monit`

### Issue: Search not using Retriv

**Symptoms:**
```
Search results haven't improved
```

**Solution:**
- Retriv initializes lazily (on first use)
- Check logs for "Retriv service initialized"
- Verify documents are being indexed
- Check service stats: `service.get_stats()`

## Testing in Production

### Manual Test Script

```python
# test_retriv_production.py
import asyncio
from src.services.retriv_service import get_retriv_service

async def test_production():
    service = get_retriv_service()
    await service.initialize()
    
    # Check stats
    stats = service.get_stats()
    print(f"Retriv Stats: {stats}")
    
    # Test search (if you have indexed data)
    results = await service.search("test query", top_k=5)
    print(f"Search returned {len(results)} results")

asyncio.run(test_production())
```

Run with:
```bash
cd /var/www/movie-generation-platform/services/mcp-brain-service
source venv/bin/activate
python3 test_retriv_production.py
```

## Performance Expectations

### Before Retriv (Semantic Only)
- Query: "Aladdin's vest in scene 3"
- May miss exact keywords like "vest" or "scene 3"
- Relies purely on semantic similarity

### After Retriv (Hybrid)
- Query: "Aladdin's vest in scene 3"
- BM25 catches: "Aladdin", "vest", "scene", "3"
- Embeddings catch: semantic meaning
- Combined score provides better ranking

### Resource Usage
- **Disk**: +80MB for sentence-transformers model
- **Memory**: +100-200MB during indexing
- **CPU**: Slight increase during search (negligible)
- **Startup**: +2-3 seconds for model loading (lazy)

## Next Steps After Deployment

1. **Monitor for 24 hours** - Watch logs and metrics
2. **Collect feedback** - Note any improvements in search quality
3. **Optimize if needed** - Adjust Retriv parameters based on usage
4. **Document learnings** - Update this guide with production insights

## Support

If you encounter issues:

1. Check logs: `pm2 logs brain-api`
2. Review this guide's troubleshooting section
3. Test with: `./test_retriv_setup.sh`
4. Rollback if necessary (see Rollback Plan above)

## Success Criteria

Deployment is successful when:
- ✅ Service starts without errors
- ✅ PM2 shows "online" status
- ✅ No import errors in logs
- ✅ Health endpoint responds
- ✅ Memory usage is stable
- ✅ Search functionality works
- ✅ No increase in error rate

## Maintenance

### Regular Checks
- Weekly: Review logs for Retriv-related warnings
- Monthly: Check index size and performance
- Quarterly: Review and optimize Retriv configuration

### Updates
- Monitor retriv package for updates
- Test updates in staging before production
- Keep this deployment guide updated

