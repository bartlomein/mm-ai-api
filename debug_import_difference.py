#!/usr/bin/env python3
"""
Debug the import difference between working and non-working versions
"""
import asyncio
import os
import sys
from pathlib import Path

# CRITICAL: Load environment variables BEFORE any imports
from dotenv import load_dotenv
load_dotenv()

print("=== Testing WORKING import path ===")
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

from services.newsapiai_service import NewsAPIAIService as WorkingService

# Clear the module cache to test the other import
import importlib
if 'services.newsapiai_service' in sys.modules:
    del sys.modules['services.newsapiai_service']

print("=== Testing EVENING SCRIPT import path ===")
sys.path.insert(0, str(project_root))

from src.services.newsapiai_service import NewsAPIAIService as EveningService

print(f"Working service class: {WorkingService}")
print(f"Evening service class: {EveningService}")
print(f"Are they the same class? {WorkingService is EveningService}")

# Check their file locations
import inspect
print(f"Working service file: {inspect.getfile(WorkingService)}")
print(f"Evening service file: {inspect.getfile(EveningService)}")

# Test both
async def test_both():
    print("\n=== Testing working service ===")
    working_service = WorkingService()
    
    # Check API key
    print(f"Working service API key length: {len(working_service.api_key) if working_service.api_key else 'None'}")
    
    result1 = await working_service.search_articles(
        keyword="world",
        max_articles=5,
        sort_by="date"
    )
    print(f"Working service result: {len(result1.get('articles', []))} articles")
    
    print("\n=== Testing evening service ===")
    evening_service = EveningService()
    
    # Check API key
    print(f"Evening service API key length: {len(evening_service.api_key) if evening_service.api_key else 'None'}")
    
    result2 = await evening_service.search_articles(
        keyword="world",
        max_articles=5,
        sort_by="date"
    )
    print(f"Evening service result: {len(result2.get('articles', []))} articles")

if __name__ == "__main__":
    asyncio.run(test_both())