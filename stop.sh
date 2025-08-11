#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}🛑 Stopping Market Brief API server...${NC}"

# Find and kill the uvicorn process
echo "Stopping API server..."
pkill -f "uvicorn src.main:app" 2>/dev/null || true

echo -e "${GREEN}✅ API server stopped${NC}"