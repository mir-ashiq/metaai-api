"""
Analyze debug response files to understand the raw JSON structure.
This helps us see EXACTLY what Meta AI is returning.
"""

import json
import os
import re
from pathlib import Path

DEBUG_DIR = Path("debug_responses")

def analyze_response_file(filepath):
    """Analyze a single debug response file."""
    print(f"\n{'='*80}")
    print(f"FILE: {filepath.name}")
    print(f"{'='*80}")
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Try to parse as JSON
        try:
            data = json.loads(content)
            print(f"✓ Valid JSON ({len(content)} characters)")
            
            # Look for video-related keys
            video_keys = []
            def find_video_keys(obj, path=""):
                if isinstance(obj, dict):
                    for key, value in obj.items():
                        current_path = f"{path}.{key}" if path else key
                        if 'video' in key.lower() or 'url' in key.lower():
                            video_keys.append((current_path, type(value).__name__, str(value)[:100]))
                        find_video_keys(value, current_path)
                elif isinstance(obj, list):
                    for idx, item in enumerate(obj):
                        find_video_keys(item, f"{path}[{idx}]")
            
            find_video_keys(data)
            
            if video_keys:
                print(f"\nFound {len(video_keys)} video-related keys:")
                for path, vtype, sample in video_keys:
                    print(f"  • {path} ({vtype})")
                    if vtype == 'str' and ('http' in sample or '.mp4' in sample):
                        print(f"    URL: {sample}")
            
            # Look for URLs in the raw text
            urls = re.findall(r'https?://[^\s\'"]+\.mp4[^\s\'"]*', content)
            if urls:
                print(f"\nFound {len(urls)} .mp4 URLs via regex:")
                for idx, url in enumerate(urls[:5], 1):  # Show first 5
                    print(f"  {idx}. {url[:80]}...")
            
            # Look for video identifiers
            video_ids = re.findall(r'/v/[a-zA-Z0-9_-]+|/t6/[a-zA-Z0-9_-]+', content)
            if video_ids:
                print(f"\nFound {len(video_ids)} video identifier paths:")
                for vid_id in set(video_ids[:5]):
                    print(f"  • {vid_id}")
            
        except json.JSONDecodeError as e:
            print(f"✗ Invalid JSON: {e}")
            print(f"\nFirst 500 characters:")
            print(content[:500])
    
    except Exception as e:
        print(f"✗ Error reading file: {e}")

def main():
    print("\n" + "="*80)
    print("DEBUG RESPONSE ANALYZER")
    print("="*80)
    
    if not DEBUG_DIR.exists():
        print(f"\n✗ Directory not found: {DEBUG_DIR}")
        return
    
    response_files = sorted(DEBUG_DIR.glob("response_*.txt"))
    
    if not response_files:
        print(f"\n✗ No response files found in {DEBUG_DIR}")
        return
    
    print(f"\nFound {len(response_files)} debug response files")
    
    for filepath in response_files:
        analyze_response_file(filepath)
    
    print("\n" + "="*80)
    print("ANALYSIS COMPLETE")
    print("="*80)
    print("\nThis shows the EXACT structure of Meta AI responses.")
    print("Use this to understand what fields contain video URLs.\n")

if __name__ == "__main__":
    main()
