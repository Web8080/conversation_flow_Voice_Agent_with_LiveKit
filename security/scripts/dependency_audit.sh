#!/bin/bash

# Dependency Security Audit Script
# Scans both Python and Node.js dependencies for vulnerabilities

set -e

echo "🔒 Running Dependency Security Audit"
echo "===================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

EXIT_CODE=0

# Check Python dependencies
echo "📦 Checking Python Dependencies..."
echo "-----------------------------------"
if [ -f "backend/requirements.txt" ]; then
    cd backend
    
    # Check if pip-audit is installed
    if ! command -v pip-audit &> /dev/null; then
        echo -e "${YELLOW}⚠️  pip-audit not found. Installing...${NC}"
        pip install pip-audit
    fi
    
    if pip-audit --requirement requirements.txt --format json > /tmp/pip-audit.json 2>&1; then
        VULN_COUNT=$(cat /tmp/pip-audit.json | grep -c '"id"' || echo "0")
        if [ "$VULN_COUNT" -gt 0 ]; then
            echo -e "${RED}❌ Found $VULN_COUNT vulnerabilities${NC}"
            cat /tmp/pip-audit.json | jq '.' 2>/dev/null || cat /tmp/pip-audit.json
            EXIT_CODE=1
        else
            echo -e "${GREEN}✅ No vulnerabilities found${NC}"
        fi
    else
        echo -e "${RED}❌ pip-audit failed${NC}"
        cat /tmp/pip-audit.json
        EXIT_CODE=1
    fi
    
    cd ..
else
    echo -e "${YELLOW}⚠️  backend/requirements.txt not found${NC}"
fi

echo ""
echo "📦 Checking Node.js Dependencies..."
echo "-----------------------------------"
if [ -f "frontend/package.json" ]; then
    cd frontend
    
    if npm audit --json > /tmp/npm-audit.json 2>&1; then
        VULN_COUNT=$(cat /tmp/npm-audit.json | jq '.metadata.vulnerabilities.total // 0' 2>/dev/null || echo "0")
        if [ "$VULN_COUNT" -gt 0 ]; then
            echo -e "${RED}❌ Found $VULN_COUNT vulnerabilities${NC}"
            npm audit
            EXIT_CODE=1
        else
            echo -e "${GREEN}✅ No vulnerabilities found${NC}"
        fi
    else
        echo -e "${RED}❌ npm audit failed${NC}"
        EXIT_CODE=1
    fi
    
    cd ..
else
    echo -e "${YELLOW}⚠️  frontend/package.json not found${NC}"
fi

echo ""
echo "===================================="
if [ $EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✅ All dependency checks passed${NC}"
else
    echo -e "${RED}❌ Security vulnerabilities found${NC}"
    echo "Please review and fix vulnerabilities before deployment"
fi

exit $EXIT_CODE


