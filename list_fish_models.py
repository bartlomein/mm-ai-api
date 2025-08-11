#!/usr/bin/env python3
"""
List all available Fish Audio voice models
"""

import os
import asyncio
from dotenv import load_dotenv
from fish_audio_sdk import Session

# Load environment variables
load_dotenv()

async def list_voice_models():
    """List all available Fish Audio voice models"""
    
    fish_api_key = os.getenv("FISH_API_KEY")
    if not fish_api_key:
        print("❌ FISH_API_KEY not found in .env")
        return
    
    print("🐟 Fish Audio Voice Models")
    print("=" * 60)
    
    try:
        # Initialize session
        session = Session(fish_api_key)
        
        # List all models
        print("Fetching available models...")
        models = list(session.list_models())
        
        if not models:
            print("\n📭 No models found.")
            print("\nYou can:")
            print("1. Visit https://fish.audio to browse public voices")
            print("2. Create your own voice model using the Fish Audio API")
            print("3. Use the playground to find voice IDs")
            return
        
        print(f"\n✅ Found {len(models)} voice models:\n")
        
        # Display models in a formatted way
        for i, model in enumerate(models, 1):
            # Handle different response formats
            if hasattr(model, 'id'):
                model_id = model.id
                title = getattr(model, 'title', 'Untitled')
                description = getattr(model, 'description', '')
            elif isinstance(model, dict):
                model_id = model.get('id', model.get('_id', 'Unknown'))
                title = model.get('title', 'Untitled')
                description = model.get('description', '')
            else:
                # If it's a tuple or other format, try to extract info
                print(f"{i}. Model data: {model}")
                print("-" * 40)
                continue
                
            print(f"{i}. Model ID: {model_id}")
            print(f"   Title: {title}")
            if description:
                print(f"   Description: {description}")
            print("-" * 40)
        
        print("\n💡 How to use a model:")
        print("1. Copy the Model ID you want to use")
        print("2. Add it to your .env file:")
        print("   FISH_MODEL_ID=<paste_model_id_here>")
        print("3. Run your script and it will use that voice consistently")
        
    except Exception as e:
        print(f"❌ Error listing models: {str(e)}")
        print("\n🌐 Alternative: Visit Fish Audio Playground")
        print("Go to https://fish.audio to browse and test voices")
        print("You can find model IDs in the playground interface")

if __name__ == "__main__":
    print("🚀 Fish Audio Model Lister")
    print("=" * 60)
    asyncio.run(list_voice_models())