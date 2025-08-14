#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo "🚀 Starting MarketMotion Backend..."
echo "=================================="

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}🔧 Creating virtual environment...${NC}"
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install/update dependencies
echo -e "${YELLOW}📦 Installing dependencies...${NC}"
pip install -q -r requirements.txt

# Check if .env file exists
if [ ! -f .env ]; then
    echo -e "${YELLOW}⚠️  No .env file found. Creating from template...${NC}"
    cp .env.example .env
    echo -e "${RED}❗ Please edit .env and add your API keys${NC}"
fi

# Check TTS configuration
echo -e "${YELLOW}🔍 Checking TTS configuration...${NC}"
if grep -q "FISH_API_KEY=.*[^=]" .env 2>/dev/null; then
    echo -e "${GREEN}✅ Fish Audio configured${NC}"
elif grep -q "OPENAI_API_KEY=.*[^=]" .env 2>/dev/null; then
    echo -e "${GREEN}✅ OpenAI TTS configured${NC}"
else
    echo -e "${RED}⚠️  No TTS service configured. Please add FISH_API_KEY or OPENAI_API_KEY to .env${NC}"
fi

# Start the API server
echo -e "${GREEN}✅ Starting API server...${NC}"
echo "=================================="
echo -e "${GREEN}API: http://localhost:8000${NC}"
echo -e "${GREEN}Docs: http://localhost:8000/docs${NC}"
echo -e "${GREEN}Health: http://localhost:8000/api/health${NC}"
echo "=================================="
echo "Press Ctrl+C to stop the server"
echo ""

# Run the server
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000