#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}🛑 Stopping Market Brief services...${NC}"

# Stop Kokoro container
echo "Stopping Kokoro TTS..."
docker-compose stop kokoro

# Find and kill the uvicorn process
echo "Stopping API server..."
pkill -f "uvicorn src.main:app" 2>/dev/null || true

echo -e "${GREEN}✅ All services stopped${NC}"