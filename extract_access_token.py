#!/usr/bin/env python3
"""
Extract access token from Meta AI for adding to .env file.

This script helps you get your access token without running the full server.
Once extracted, add it to your .env file as:

META_AI_ACCESS_TOKEN=ecto1:your_token_here

This avoids rate limiting issues when running the API server.
"""

from metaai_api import MetaAI
import sys

def main():
    print("=" * 70)
    print("Meta AI Access Token Extractor")
    print("=" * 70)
    print()
    print("This will fetch meta.ai and extract your OAuth access token.")
    print("Make sure your cookies are set in .env file first!")
    print()
    
    try:
        print("Initializing MetaAI client...")
        ai = MetaAI()
        
        if not ai.access_token:
            print()
            print("❌ FAILED: Could not extract access token")
            print()
            print("Possible reasons:")
            print("  1. Rate limited (wait 1-3 hours and try again)")
            print("  2. Invalid cookies in .env file")
            print("  3. Network/connection issue")
            print()
            return 1
        
        print()
        print("✅ SUCCESS: Access token extracted!")
        print()
        print("=" * 70)
        print("Add this line to your .env file:")
        print("=" * 70)
        print()
        print(f"META_AI_ACCESS_TOKEN={ai.access_token}")
        print()
        print("=" * 70)
        print()
        print("After adding to .env, restart your API server.")
        print("The token will be loaded from .env without hitting meta.ai")
        print()
        return 0
        
    except Exception as e:
        print()
        print(f"❌ ERROR: {e}")
        print()
        print("Make sure your .env file has valid cookies:")
        print("  - META_AI_DATR")
        print("  - META_AI_ABRA_SESS")
        print("  - META_AI_ECTO_1_SESS")
        print()
        return 1

if __name__ == "__main__":
    sys.exit(main())
