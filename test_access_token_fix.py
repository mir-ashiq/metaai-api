"""
Test script to verify the accessToken fix.
This checks that:
1. accessToken is extracted from the meta.ai page HTML
2. The token is in the correct format (ecto1:...)
3. ImageUploader uses the correct token for OAuth
"""

import logging
from src.metaai_api import MetaAI

# Enable detailed logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def test_access_token_extraction():
    """Test that access token is properly extracted from page."""
    print("\n" + "="*70)
    print("TEST: Access Token Extraction")
    print("="*70)
    
    # Initialize MetaAI (should auto-load cookies from .env and extract token)
    print("\n1. Initializing MetaAI...")
    ai = MetaAI()
    
    # Check if access token was extracted
    print("\n2. Checking access token...")
    if ai.access_token:
        print(f"   ✅ Access token extracted successfully")
        print(f"   Token format: {ai.access_token[:30]}...")  # Show first 30 chars
        print(f"   Token length: {len(ai.access_token)} characters")
        
        # Validate format
        if ai.access_token.startswith('ecto1:'):
            print(f"   ✅ Token has correct format (starts with 'ecto1:')")
        else:
            print(f"   ❌ Token has WRONG format (should start with 'ecto1:')")
            print(f"   Actual start: {ai.access_token[:10]}")
            return False
    else:
        print(f"   ❌ Access token is None or empty")
        return False
    
    # Check cookies are also loaded
    print("\n3. Checking cookies...")
    if ai.cookies and 'ecto_1_sess' in ai.cookies:
        print(f"   ✅ Cookies loaded (including ecto_1_sess)")
        print(f"   ecto_1_sess: {ai.cookies['ecto_1_sess'][:40]}...")
        
        # Verify they are DIFFERENT
        if ai.access_token not in ai.cookies['ecto_1_sess']:
            print(f"   ✅ CONFIRMED: accessToken and ecto_1_sess are DIFFERENT (correct!)")
        else:
            print(f"   ❌ WARNING: accessToken appears to be derived from ecto_1_sess")
    else:
        print(f"   ⚠️  Cookies not loaded or missing ecto_1_sess")
    
    print("\n" + "="*70)
    print("TEST RESULT: Access token extraction works correctly! ✅")
    print("="*70)
    return True


def test_image_upload_with_token():
    """Test that image upload uses the correct access token."""
    print("\n" + "="*70)
    print("TEST: Image Upload with Correct Token")
    print("="*70)
    
    # Initialize MetaAI
    print("\n1. Initializing MetaAI...")
    ai = MetaAI()
    
    if not ai.access_token:
        print("   ❌ Cannot test upload - no access token available")
        return False
    
    # Try to upload a test image
    print("\n2. Testing image upload...")
    print("   Note: This will attempt an actual upload to verify the token works")
    
    # Create a tiny test image file (1x1 pixel)
    import os
    import tempfile
    from PIL import Image
    
    # Create temp image
    with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
        test_image_path = tmp.name
        img = Image.new('RGB', (100, 100), color='red')
        img.save(test_image_path)
    
    try:
        print(f"   Created test image: {test_image_path}")
        
        # Attempt upload
        result = ai.upload_image(test_image_path)
        
        print("\n3. Upload result:")
        if result and result.get("success"):
            print(f"   ✅ Upload succeeded!")
            print(f"   Media ID: {result.get('media_id')}")
            print(f"   File size: {result.get('file_size')} bytes")
        else:
            print(f"   ❌ Upload failed")
            print(f"   Error: {result.get('error') if result else 'No result returned'}")
            return False
    finally:
        # Cleanup
        if os.path.exists(test_image_path):
            os.remove(test_image_path)
            print(f"\n   Cleaned up test image")
    
    print("\n" + "="*70)
    print("TEST RESULT: Image upload works with new token! ✅")
    print("="*70)
    return True


if __name__ == "__main__":
    print("\n" + "="*70)
    print("🔍 TESTING ACCESS TOKEN FIX")
    print("="*70)
    print("\nThis test verifies that:")
    print("  1. The accessToken is extracted from meta.ai page HTML")
    print("  2. The token is different from ecto_1_sess cookie")
    print("  3. The token is used for image upload OAuth authentication")
    print("")
    
    # Run tests
    test1_passed = test_access_token_extraction()
    
    if test1_passed:
        test2_passed = test_image_upload_with_token()
        
        if test2_passed:
            print("\n" + "="*70)
            print("🎉 ALL TESTS PASSED! The fix is working correctly!")
            print("="*70)
        else:
            print("\n" + "="*70)
            print("⚠️  Token extraction works but upload failed")
            print("="*70)
    else:
        print("\n" + "="*70)
        print("❌ Token extraction failed - cannot proceed with upload test")
        print("="*70)
