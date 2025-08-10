#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo "🚀 Starting Market Brief Backend..."
echo "=================================="

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker is not running. Please start Docker first.${NC}"
    exit 1
fi

# Start Kokoro TTS container
echo -e "${YELLOW}📢 Starting Kokoro TTS...${NC}"
docker-compose up -d kokoro

# Wait for Kokoro to be ready
echo "Waiting for Kokoro to initialize..."
sleep 5

# Check if Kokoro is healthy
if curl -f http://localhost:8880/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Kokoro TTS is running${NC}"
else
    echo -e "${YELLOW}⚠️  Kokoro might still be starting. Continuing...${NC}"
fi

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

# Start the API server
echo -e "${GREEN}✅ Starting API server...${NC}"
echo "=================================="
echo -e "${GREEN}API: http://localhost:8000${NC}"
echo -e "${GREEN}Kokoro TTS: http://localhost:8880${NC}"
echo -e "${GREEN}Docs: http://localhost:8000/docs${NC}"
echo "=================================="
echo "Press Ctrl+C to stop all services"
echo ""

# Trap Ctrl+C and cleanup
trap cleanup INT

cleanup() {
    echo -e "\n${YELLOW}Shutting down...${NC}"
    echo "Stopping Kokoro TTS..."
    docker-compose stop kokoro
    echo -e "${GREEN}✅ All services stopped${NC}"
    exit 0
}

# Run the server
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000