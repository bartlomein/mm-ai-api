#!/usr/bin/env python3
"""
Generate audio from an existing text file
"""

import os
import sys
import asyncio
from pathlib import Path
from dotenv import load_dotenv

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from services.audio_service import AudioService

# Load environment variables
load_dotenv()

async def generate_audio_from_file(text_file: str, output_file: str = None):
    """Generate audio from a text file"""
    
    # Read the text file
    with open(text_file, 'r') as f:
        text = f.read()
    
    # Remove any metadata at the end (after ---)
    if '---' in text:
        text = text.split('---')[0].strip()
    
    print(f"📖 Read {len(text.split())} words from {text_file}")
    
    # Generate output filename if not provided
    if not output_file:
        base_name = Path(text_file).stem
        output_file = f"{base_name}.mp3"
    
    # Initialize audio service
    audio_service = AudioService()
    
    print(f"🎙️ Generating audio... (this may take 3-5 minutes)")
    
    # Generate audio
    success = await audio_service.generate_audio(
        text,
        output_file,
        tier="premium"
    )
    
    if success:
        print(f"✅ Audio saved to: {output_file}")
        print(f"📍 Full path: {os.path.abspath(output_file)}")
    else:
        print("❌ Audio generation failed")
    
    return success

async def main():
    if len(sys.argv) < 2:
        print("Usage: python generate_audio_from_text.py <text_file> [output_file]")
        print("\nExample:")
        print("  python generate_audio_from_text.py morning_premium_briefing_20250813_191000.txt")
        sys.exit(1)
    
    text_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    if not os.path.exists(text_file):
        print(f"❌ File not found: {text_file}")
        sys.exit(1)
    
    await generate_audio_from_file(text_file, output_file)

if __name__ == "__main__":
    asyncio.run(main())