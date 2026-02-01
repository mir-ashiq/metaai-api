"""
Test script for video generation with different orientations
"""
from metaai_api import MetaAI
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_video_orientation(ai, prompt, orientation):
    """Test video generation with specific orientation"""
    print(f"\n{'='*60}")
    print(f"Testing {orientation} orientation for VIDEO")
    print(f"Prompt: {prompt}")
    print(f"{'='*60}")
    
    try:
        response = ai.generate_video(
            prompt=prompt,
            orientation=orientation,
            wait_before_poll=10,
            max_attempts=30,
            wait_seconds=5,
            verbose=True
        )
        
        if response.get('success'):
            print(f"\n✓ Video generated successfully!")
            print(f"  Conversation ID: {response.get('conversation_id')}")
            print(f"  Video URLs: {len(response.get('video_urls', []))} video(s)")
            for i, url in enumerate(response.get('video_urls', []), 1):
                print(f"    {i}. {url}")
        else:
            print(f"\n✗ Video generation failed")
            if response.get('error'):
                print(f"  Error: {response.get('error')}")
            
        return response
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        return None

if __name__ == "__main__":
    # Initialize Meta AI with credentials from .env
    print("Initializing Meta AI...")
    
    # Load cookies from environment variables
    cookies = {
        "datr": os.getenv("META_AI_DATR", ""),
        "abra_sess": os.getenv("META_AI_ABRA_SESS", ""),
        "dpr": os.getenv("META_AI_DPR", "2"),
        "wd": os.getenv("META_AI_WD", "1920x969"),
        "_js_datr": os.getenv("META_AI_JS_DATR", ""),
        "abra_csrf": os.getenv("META_AI_ABRA_CSRF", ""),
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
                f.write("META_AI_DPR=2\n")
                f.write("META_AI_WD=1920x969\n")
            print("✓ Created .env file. Please update it with your cookies.\n")
        exit(1)
    
    print("✓ Loaded credentials from .env")
    ai = MetaAI(cookies=cookies)
    
    # Test prompts for different orientations
    tests = [
        {
            "prompt": "generate a video of astronaut floating in space with stars",
            "orientation": "LANDSCAPE"
        },
        {
            "prompt": "generate a video of waterfall flowing down in a vertical motion",
            "orientation": "VERTICAL"
        },
        {
            "prompt": "generate a video of spinning geometric cube animation",
            "orientation": "SQUARE"
        }
    ]
    
    # Run tests
    results = []
    for test in tests:
        result = test_video_orientation(
            ai, 
            test["prompt"], 
            test["orientation"]
        )
        results.append({
            "orientation": test["orientation"],
            "success": result is not None and result.get('success', False),
            "video_count": len(result.get('video_urls', [])) if result else 0
        })
        
        # Wait a bit between requests
        import time
        time.sleep(5)
    
    # Summary
    print(f"\n{'='*60}")
    print("VIDEO GENERATION TEST SUMMARY")
    print(f"{'='*60}")
    for r in results:
        status = "✓ PASS" if r["success"] else "✗ FAIL"
        print(f"{r['orientation']:12} - {status} ({r['video_count']} video(s))")
    print(f"{'='*60}\n")
