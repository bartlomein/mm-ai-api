#!/usr/bin/env python3
"""
Test different Fish Audio voices with sample text
"""

import os
import asyncio
from dotenv import load_dotenv
from fish_audio_sdk import Session, TTSRequest
from datetime import datetime

# Load environment variables
load_dotenv()

# Sample text for testing voices
SAMPLE_TEXT = """
Good morning! This is a test of the Fish Audio text-to-speech system. 
Today's market update shows strong gains in technology stocks, 
with the S&P five hundred up two percent. 
This voice sample helps you evaluate the quality and tone for your audio briefings.
"""

async def test_voice(session, model_id=None, model_name="Default"):
    """Test a specific voice model"""
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    if model_id:
        filename = f"test_voice_{model_id}_{timestamp}.mp3"
        print(f"\n🎤 Testing voice: {model_name} (ID: {model_id})")
        request = TTSRequest(
            text=SAMPLE_TEXT,
            reference_id=model_id
        )
    else:
        filename = f"test_voice_default_{timestamp}.mp3"
        print(f"\n🎤 Testing default Fish Audio voice")
        request = TTSRequest(text=SAMPLE_TEXT)
    
    try:
        print("   Generating audio...")
        audio_data = b""
        chunk_count = 0
        
        async for chunk in session.tts.awaitable(request):
            audio_data += chunk
            chunk_count += 1
            if chunk_count % 5 == 0:
                print(f"   Received {chunk_count} chunks...")
        
        # Save audio file
        with open(filename, 'wb') as f:
            f.write(audio_data)
        
        print(f"   ✅ Audio saved to: {filename}")
        print(f"   File size: {len(audio_data) / 1024:.1f} KB")
        return filename
        
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        return None

async def main():
    """Main function to test voices"""
    
    fish_api_key = os.getenv("FISH_API_KEY")
    if not fish_api_key:
        print("❌ FISH_API_KEY not found in .env")
        return
    
    print("🐟 Fish Audio Voice Tester")
    print("=" * 60)
    
    # Initialize session
    session = Session(fish_api_key)
    
    # Test default voice first
    print("\n1️⃣ Testing default voice (no model ID specified)")
    await test_voice(session)
    
    # Check if user has set a specific model
    user_model_id = os.getenv("FISH_MODEL_ID")
    if user_model_id:
        print(f"\n2️⃣ Testing your configured model from .env")
        await test_voice(session, user_model_id, "Your configured model")
    
    # List and test available models
    try:
        print("\n3️⃣ Checking for available models...")
        models = list(session.list_models())
        
        if models:
            print(f"Found {len(models)} models. Testing first 3...")
            for i, model in enumerate(models[:3], 1):
                await test_voice(session, model.id, model.title)
        else:
            print("No custom models found in your account.")
            
    except Exception as e:
        print(f"Could not list models: {e}")
    
    # Popular public model IDs (if known)
    # These are example IDs - replace with actual public model IDs from Fish Audio
    print("\n4️⃣ Testing public voices (if available)")
    print("\n💡 Tip: Visit https://fish.audio to find public voice model IDs")
    print("   You can browse voices and copy their IDs from the playground")
    
    # If you find public model IDs, you can test them like this:
    # public_models = [
    #     ("model_id_here", "Voice Name"),
    # ]
    # for model_id, name in public_models:
    #     await test_voice(session, model_id, name)
    
    print("\n" + "=" * 60)
    print("✅ Voice testing complete!")
    print("\nNext steps:")
    print("1. Listen to the generated MP3 files")
    print("2. Choose your favorite voice")
    print("3. Add to .env: FISH_MODEL_ID=<chosen_model_id>")
    print("4. All future generations will use that voice")

if __name__ == "__main__":
    asyncio.run(main())