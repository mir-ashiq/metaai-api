"""
Test script for image and video generation using captured network patterns.
"""
import os
import sys
import logging
from dotenv import load_dotenv

# Setup path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from metaai_api import MetaAI

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def load_cookies_from_env():
    """Load cookies from .env file"""
    load_dotenv()
    
    cookies = {}
    
    # Load required cookies
    required_cookies = {
        'datr': 'META_AI_DATR',
        'abra_sess': 'META_AI_ABRA_SESS',
        'dpr': 'META_AI_DPR',
        'wd': 'META_AI_WD'
    }
    
    # Load optional cookies for generation
    optional_cookies = {
        'c_user': 'META_AI_C_USER',
        'xs': 'META_AI_XS',
        'fr': 'META_AI_FR'
    }
    
    # Check for required cookies
    missing = []
    for cookie_name, env_var in required_cookies.items():
        value = os.getenv(env_var)
        if value and value != f'your_{cookie_name}_cookie_value':
            cookies[cookie_name] = value
        else:
            missing.append(env_var)
    
    if missing:
        print(f"\n⚠️  Missing required environment variables: {', '.join(missing)}")
        print("Please copy .env.example to .env and add your Meta AI cookies.")
        print("\nHow to get cookies:")
        print("1. Open browser and go to https://meta.ai")
        print("2. Open Developer Tools (F12)")
        print("3. Go to Application/Storage > Cookies > https://meta.ai")
        print("4. Copy the values for: datr, abra_sess, dpr, wd")
        return None
    
    # Load optional cookies
    for cookie_name, env_var in optional_cookies.items():
        value = os.getenv(env_var)
        if value and value != f'your_{cookie_name}_value':
            cookies[cookie_name] = value
    
    return cookies


def test_image_generation(ai):
    """Test image generation"""
    print("\n" + "="*60)
    print("Testing Image Generation")
    print("="*60)
    
    prompt = "Astronaut in space"
    print(f"\nGenerating images with prompt: '{prompt}'")
    
    result = ai.generate_image_new(
        prompt=prompt,
        orientation="VERTICAL",
        num_images=1
    )
    
    if result.get('success'):
        print(f"✅ Success! Generated {len(result.get('image_urls', []))} image(s)")
        for i, url in enumerate(result.get('image_urls', []), 1):
            print(f"   Image {i}: {url[:80]}...")
    else:
        print(f"❌ Failed: {result.get('error', 'Unknown error')}")
    
    return result


def test_video_generation(ai):
    """Test video generation"""
    print("\n" + "="*60)
    print("Testing Video Generation")
    print("="*60)
    
    prompt = "Astronaut in space"
    print(f"\nGenerating video with prompt: '{prompt}'")
    
    result = ai.generate_video_new(
        prompt=prompt
    )
    
    if result.get('success'):
        print(f"✅ Success! Generated {len(result.get('video_urls', []))} video(s)")
        for i, url in enumerate(result.get('video_urls', []), 1):
            print(f"   Video {i}: {url[:80]}...")
    else:
        print(f"❌ Failed: {result.get('error', 'Unknown error')}")
    
    return result


def main():
    """Main test function"""
    print("\n🤖 Meta AI Generation API Test")
    print("="*60)
    
    # Load cookies from .env
    print("\nLoading cookies from .env file...")
    cookies = load_cookies_from_env()
    
    if not cookies:
        sys.exit(1)
    
    print(f"✅ Loaded {len(cookies)} cookies")
    print(f"   Cookie keys: {', '.join(cookies.keys())}")
    
    # Initialize MetaAI
    print("\nInitializing Meta AI client...")
    try:
        ai = MetaAI(cookies=cookies)
        print("✅ Meta AI client initialized")
    except Exception as e:
        print(f"❌ Failed to initialize: {e}")
        sys.exit(1)
    
    # Test image generation
    image_result = test_image_generation(ai)
    
    # Test video generation
    video_result = test_video_generation(ai)
    
    # Summary
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)
    print(f"Image Generation: {'✅ Success' if image_result.get('success') else '❌ Failed'}")
    print(f"Video Generation: {'✅ Success' if video_result.get('success') else '❌ Failed'}")
    print()


if __name__ == "__main__":
    main()
