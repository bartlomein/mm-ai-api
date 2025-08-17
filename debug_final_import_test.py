#!/usr/bin/env python3
"""
Final test of the import path difference
"""
import asyncio
import sys
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

async def debug_final_import_test():
    project_root = Path(__file__).parent

    print("=== Test 1: Working import path (src/ in path, import services.X) ===")
    sys.path.insert(0, str(project_root / "src"))

    from services.newsapiai_service import NewsAPIAIService as WorkingService

    working_service = WorkingService()

    print(f"Working service API key: {'✓' if working_service.api_key else '✗'}")
    print(f"Working service base_url: {working_service.base_url}")

    # Test a simple call
    result1 = await working_service.search_articles(
        keyword="world",
        max_articles=3,
        sort_by="date"
    )

    print(f"Working service result: {len(result1.get('articles', []))} articles")

    print("\n=== Test 2: Evening script import path (project root in path, import src.services.X) ===")

    # Clear the module cache completely
    import importlib
    modules_to_clear = [key for key in sys.modules.keys() if 'newsapiai' in key]
    for module in modules_to_clear:
        del sys.modules[module]

    # Clear sys.path and add project root (like evening script)
    while str(project_root / "src") in sys.path:
        sys.path.remove(str(project_root / "src"))

    sys.path.insert(0, str(project_root))

    from src.services.newsapiai_service import NewsAPIAIService as EveningService

    evening_service = EveningService()

    print(f"Evening service API key: {'✓' if evening_service.api_key else '✗'}")
    print(f"Evening service base_url: {evening_service.base_url}")

    # Test the exact same call
    result2 = await evening_service.search_articles(
        keyword="world",
        max_articles=3,
        sort_by="date"
    )

    print(f"Evening service result: {len(result2.get('articles', []))} articles")

    print(f"\n=== Comparison ===")
    print(f"Working: {len(result1.get('articles', []))} articles")
    print(f"Evening: {len(result2.get('articles', []))} articles")
    print(f"Same result? {len(result1.get('articles', [])) == len(result2.get('articles', []))}")

if __name__ == "__main__":
    asyncio.run(debug_final_import_test())