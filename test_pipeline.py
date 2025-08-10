#!/usr/bin/env python3
"""
Quick test script to verify the pipeline works
"""

import asyncio
import httpx
import json
import sys

async def test_kokoro():
    """Test Kokoro TTS directly"""
    print("Testing Kokoro TTS...")
    
    url = "http://localhost:8880/v1/audio/speech"
    payload = {
        "model": "kokoro",
        "input": "Testing Kokoro text to speech. The market is up today!",
        "voice": "af_bella",
        "response_format": "mp3"
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, timeout=30.0)
            if response.status_code == 200:
                with open("test_kokoro_direct.mp3", "wb") as f:
                    f.write(response.content)
                print("✅ Kokoro TTS working! Audio saved to test_kokoro_direct.mp3")
                return True
            else:
                print(f"❌ Kokoro error: {response.status_code}")
                return False
    except Exception as e:
        print(f"❌ Cannot connect to Kokoro: {e}")
        print("   Run './kokoro.sh start' first")
        return False

async def test_pipeline():
    """Test the full pipeline"""
    print("\nTesting full pipeline...")
    
    url = "http://localhost:8000/api/test/generate"
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, timeout=60.0)
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "success":
                    print(f"✅ Pipeline working!")
                    print(f"   - Briefing ID: {data.get('id')}")
                    print(f"   - Duration: {data.get('duration_seconds')} seconds")
                    print(f"   - Articles processed: {data.get('articles_processed')}")
                    print(f"   - Audio URL: {data.get('audio_url')}")
                    return True
                else:
                    print(f"❌ Pipeline error: {data.get('error')}")
                    return False
            else:
                print(f"❌ API error: {response.status_code}")
                return False
    except Exception as e:
        print(f"❌ Cannot connect to API: {e}")
        print("   Run './run.sh' to start the API server")
        return False

async def test_personalized():
    """Test personalized briefing"""
    print("\nTesting personalized briefing...")
    
    url = "http://localhost:8000/api/test/generate-personalized"
    payload = {"tickers": ["AAPL", "GOOGL"]}
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, timeout=60.0)
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "success":
                    print(f"✅ Personalized briefing working!")
                    print(f"   - Tickers: {', '.join(data.get('tickers', []))}")
                    print(f"   - Duration: {data.get('duration_seconds')} seconds")
                    return True
                else:
                    print(f"❌ Error: {data.get('error')}")
                    return False
            else:
                print(f"❌ API error: {response.status_code}")
                return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

async def main():
    print("=" * 50)
    print("Market Brief Pipeline Test")
    print("=" * 50)
    
    # Test Kokoro first
    kokoro_ok = await test_kokoro()
    if not kokoro_ok:
        print("\n⚠️ Fix Kokoro first: ./kokoro.sh start")
        sys.exit(1)
    
    # Test full pipeline
    pipeline_ok = await test_pipeline()
    if not pipeline_ok:
        print("\n⚠️ Check your API keys in .env file")
        sys.exit(1)
    
    # Test personalized
    await test_personalized()
    
    print("\n" + "=" * 50)
    print("✅ All tests passed! Your pipeline is ready.")
    print("=" * 50)

if __name__ == "__main__":
    asyncio.run(main())