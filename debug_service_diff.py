#!/usr/bin/env python3
"""
Compare the two different service instances to find the exact difference
"""
import asyncio
import os
import sys
from pathlib import Path

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

print("=== Comparing Working vs Evening Service Instances ===")

# Import both versions
project_root = Path(__file__).parent

# Working version
sys.path.insert(0, str(project_root / "src"))
from services.newsapiai_service import NewsAPIAIService as WorkingService

# Clear and import evening version
import importlib
for module in list(sys.modules.keys()):
    if 'newsapiai_service' in module:
        del sys.modules[module]

sys.path.insert(0, str(project_root))
from src.services.newsapiai_service import NewsAPIAIService as EveningService

def compare_services():
    print("\n=== Creating service instances ===")
    
    working = WorkingService()
    evening = EveningService()
    
    print(f"Working service API key: {'✓' if working.api_key else '✗'} (len: {len(working.api_key) if working.api_key else 0})")
    print(f"Evening service API key: {'✓' if evening.api_key else '✗'} (len: {len(evening.api_key) if evening.api_key else 0})")
    
    print(f"Working service base_url: {working.base_url}")
    print(f"Evening service base_url: {evening.base_url}")
    
    # Check if they have the same methods
    working_methods = [m for m in dir(working) if not m.startswith('_')]
    evening_methods = [m for m in dir(evening) if not m.startswith('_')]
    
    print(f"Working methods: {len(working_methods)}")
    print(f"Evening methods: {len(evening_methods)}")
    print(f"Methods match: {set(working_methods) == set(evening_methods)}")
    
    if set(working_methods) != set(evening_methods):
        print(f"Working only: {set(working_methods) - set(evening_methods)}")
        print(f"Evening only: {set(evening_methods) - set(working_methods)}")

async def compare_api_calls():
    print("\n=== Testing API calls ===")
    
    working = WorkingService()
    evening = EveningService()
    
    # Test the exact same call on both
    print("Testing working service...")
    try:
        result1 = await working.search_articles(
            keyword="test",
            max_articles=1,
            sort_by="date"
        )
        print(f"Working result: {len(result1.get('articles', []))} articles")
        print(f"Working metadata: {result1.get('metadata', {})}")
    except Exception as e:
        print(f"Working service error: {e}")
    
    print("\nTesting evening service...")
    try:
        result2 = await evening.search_articles(
            keyword="test",
            max_articles=1,
            sort_by="date"
        )
        print(f"Evening result: {len(result2.get('articles', []))} articles")
        print(f"Evening metadata: {result2.get('metadata', {})}")
    except Exception as e:
        print(f"Evening service error: {e}")

if __name__ == "__main__":
    compare_services()
    asyncio.run(compare_api_calls())