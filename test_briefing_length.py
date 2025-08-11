#!/usr/bin/env python3
"""
Test script to verify briefing length
"""

import os
import glob
from datetime import datetime

def check_briefing_files():
    """Check the length of recent briefing files"""
    
    # Find recent briefing text files
    briefing_files = glob.glob("briefing_*.txt")
    
    if not briefing_files:
        print("No briefing files found. Run ./generate_briefing.py first")
        return
    
    # Sort by modification time
    briefing_files.sort(key=os.path.getmtime, reverse=True)
    
    print("📊 Briefing File Analysis")
    print("=" * 60)
    
    for i, file_path in enumerate(briefing_files[:5], 1):  # Check last 5 files
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Calculate metrics
        char_count = len(content)
        word_count = len(content.split())
        estimated_duration = word_count / 150  # 150 words per minute
        
        # Get file modification time
        mod_time = datetime.fromtimestamp(os.path.getmtime(file_path))
        
        print(f"\n{i}. {file_path}")
        print(f"   Modified: {mod_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"   Characters: {char_count:,}")
        print(f"   Words: {word_count}")
        print(f"   Estimated duration: {estimated_duration:.1f} minutes")
        
        # Check if it's a proper 5-minute briefing
        if word_count < 700:
            print(f"   ⚠️  TOO SHORT! Need 750-850 words for 5 minutes")
        elif word_count > 900:
            print(f"   ⚠️  TOO LONG! Target is 750-850 words")
        else:
            print(f"   ✅ Good length for 5-minute briefing!")
        
        # Show first 200 characters
        print(f"   Preview: {content[:200]}...")
    
    print("\n" + "=" * 60)
    print("Target: 750-850 words for 5-minute briefing")
    print("If briefings are too short, the prompt needs adjustment")

if __name__ == "__main__":
    check_briefing_files()