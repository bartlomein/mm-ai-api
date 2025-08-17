#!/usr/bin/env python3
"""
Test script to demonstrate audio stitching functionality
"""

# Fix for Python 3.13+ compatibility
try:
    import audioop
except ModuleNotFoundError:
    import audioop_lts as audioop
    import sys
    sys.modules['audioop'] = audioop

from pydub import AudioSegment
import os
import glob

def stitch_intro_to_audio(audio_file, intro_file="intro1.mp3"):
    """
    Add intro to any audio file
    """
    if not os.path.exists(intro_file):
        print(f"❌ Intro file '{intro_file}' not found")
        return None
    
    if not os.path.exists(audio_file):
        print(f"❌ Audio file '{audio_file}' not found")
        return None
    
    print(f"🎵 Processing: {audio_file}")
    print(f"   Loading intro: {intro_file}")
    
    # Load audio files
    intro = AudioSegment.from_mp3(intro_file)
    main_audio = AudioSegment.from_mp3(audio_file)
    
    # Combine
    combined = intro + main_audio
    
    # Create output filename
    base_name = os.path.splitext(audio_file)[0]
    output_file = f"{base_name}_with_intro.mp3"
    
    # Export
    combined.export(output_file, format="mp3")
    
    print(f"✅ Created: {output_file}")
    print(f"   Intro: {len(intro)/1000:.1f}s")
    print(f"   Main: {len(main_audio)/1000:.1f}s")
    print(f"   Total: {len(combined)/1000:.1f}s")
    
    return output_file

if __name__ == "__main__":
    # Find most recent audio file
    audio_files = glob.glob("premium_morning_audio_*.mp3")
    
    # Filter out files that already have intro
    audio_files = [f for f in audio_files if "_with_intro" not in f]
    
    if audio_files:
        # Sort by modification time and get the most recent
        audio_files.sort(key=os.path.getmtime, reverse=True)
        latest_audio = audio_files[0]
        
        print(f"Found audio file: {latest_audio}")
        stitch_intro_to_audio(latest_audio)
    else:
        print("No audio files found. Generate a briefing first!")