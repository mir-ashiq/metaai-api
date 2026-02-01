"""
Test script for image generation with different orientations
"""
from metaai_api import MetaAI
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_orientation(ai, prompt, orientation):
    """Test image generation with specific orientation"""
    print(f"\n{'='*60}")
    print(f"Testing {orientation} orientation")
    print(f"Prompt: {prompt}")
    print(f"{'='*60}")
    
    try:
        response = ai.prompt(prompt, orientation=orientation)
        
        print(f"\nMessage: {response.get('message', 'No message')[:100]}...")
        
        if response.get('media'):
            print(f"\n✓ Generated {len(response['media'])} image(s):")
            for i, media in enumerate(response['media'], 1):
                print(f"  {i}. URL: {media.get('url', 'No URL')}...")
                print(f"     Type: {media.get('type', 'Unknown')}")
                if media.get('prompt'):
                    print(f"     Prompt: {media.get('prompt')}")
        else:
            print("\n✗ No media generated")
            
        return response
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    # Initialize Meta AI with credentials from .env
    print("Initializing Meta AI...")
    
    # Load cookies from environment variables
    cookies = {
        "datr": os.getenv("META_AI_DATR", ""),
        "abra_sess": os.getenv("META_AI_ABRA_SESS", ""),
        "dpr": os.getenv("META_AI_DPR", "1"),
        "wd": os.getenv("META_AI_WD", "1920x969"),
    }
    
    # Check if cookies are provided
    if not cookies["datr"] or not cookies["abra_sess"]:
        print("\n⚠️  WARNING: META_AI_DATR and META_AI_ABRA_SESS not found in .env file")
        print("Creating .env file with example values...")
        print("Please update .env with your actual cookies from meta.ai")
        
        # Create .env file if it doesn't exist
        if not os.path.exists(".env"):
            with open(".env", "w") as f:
                f.write("# Meta AI Authentication Cookies\n")
                f.write("# Get these from your browser after logging into meta.ai\n")
                f.write("META_AI_DATR=your_datr_cookie_here\n")
                f.write("META_AI_ABRA_SESS=your_abra_sess_cookie_here\n")
                f.write("META_AI_DPR=1\n")
                f.write("META_AI_WD=1920x969\n")
            print("✓ Created .env file. Please update it with your cookies.\n")
        
        # Initialize without auth (may have limited functionality)
        ai = MetaAI()
    else:
        print("✓ Loaded credentials from .env")
        ai = MetaAI(cookies=cookies)
    
    # Test prompts for different orientations
    tests = [
        {
            "prompt": "astronaut riding a horse on mars",
            "orientation": "LANDSCAPE"
        },
        {
            "prompt": "tall waterfall cascading down a cliff",
            "orientation": "VERTICAL"
        },
        {
            "prompt": "centered mandala pattern with vibrant colors",
            "orientation": "SQUARE"
        }
    ]
    
    # Run tests
    import time
    results = []
    for test in tests:
        result = test_orientation(
            ai, 
            test["prompt"], 
            test["orientation"]
        )
        results.append({
            "orientation": test["orientation"],
            "success": result is not None and result.get('media') is not None,
            "media_count": len(result.get('media', [])) if result else 0
        })
        
        # Wait a bit between requests
        time.sleep(2)
    
    # Summary
    print(f"\n{'='*60}")
    print("TEST SUMMARY")
    print(f"{'='*60}")
    for r in results:
        status = "✓ PASS" if r["success"] else "✗ FAIL"
        print(f"{r['orientation']} - {status} ({r['media_count']} media)")
    print(f"{'='*60}\n")
