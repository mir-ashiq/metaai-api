"""
Real-World Integration Test for Meta AI Challenge Page Fix

This script helps you:
1. Extract cookies from your browser
2. Test token fetching with real Meta AI
3. Verify challenge page handling works
4. Test actual API calls

Follow the prompts to complete the test.
"""

import logging
import sys
from typing import Dict, Optional

# Enable detailed logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def print_banner(text: str):
    """Print a formatted banner"""
    print("\n" + "="*70)
    print(f"  {text}")
    print("="*70)

def print_step(step_num: int, text: str):
    """Print a step header"""
    print(f"\n📋 STEP {step_num}: {text}")
    print("-"*70)

def get_user_input(prompt: str, default: str = "") -> str:
    """Get input from user with optional default"""
    if default:
        user_input = input(f"{prompt} [{default}]: ").strip()
        return user_input if user_input else default
    return input(f"{prompt}: ").strip()

def extract_cookies_from_user() -> Dict[str, str]:
    """Guide user through extracting cookies from browser"""
    print_banner("COOKIE EXTRACTION GUIDE")
    
    print("""
To get your Meta AI cookies:

1. Open your browser and go to: https://www.meta.ai
2. Log in if you haven't already
3. Press F12 to open Developer Tools
4. Go to the 'Application' tab (Chrome) or 'Storage' tab (Firefox)
5. In the left sidebar, expand 'Cookies' and click on 'https://www.meta.ai'
6. Find and copy these cookie values:
   - datr
   - abra_sess
   - abra_csrf (optional but recommended)
   - dpr (optional, usually '1' or '1.25')
   - wd (optional, your window dimensions like '1536x730')

Ready to enter your cookies? (You'll paste them one by one)
""")
    
    input("Press Enter when ready to continue...")
    
    print_step(1, "Enter Required Cookies")
    
    cookies = {}
    
    # Required cookies
    cookies['datr'] = get_user_input("Enter 'datr' cookie value")
    if not cookies['datr']:
        print("❌ ERROR: 'datr' cookie is required!")
        sys.exit(1)
    
    cookies['abra_sess'] = get_user_input("Enter 'abra_sess' cookie value")
    if not cookies['abra_sess']:
        print("❌ ERROR: 'abra_sess' cookie is required!")
        sys.exit(1)
    
    # Optional cookies
    print("\n📋 Optional cookies (press Enter to skip):")
    cookies['abra_csrf'] = get_user_input("Enter 'abra_csrf' cookie value (recommended)", "")
    cookies['dpr'] = get_user_input("Enter 'dpr' cookie value", "1.25")
    cookies['wd'] = get_user_input("Enter 'wd' cookie value", "1536x730")
    
    # Clean up empty values
    cookies = {k: v for k, v in cookies.items() if v}
    
    print("\n✅ Cookies collected:")
    for key in cookies.keys():
        print(f"   - {key}: {'*' * 20}")
    
    return cookies

def test_token_fetching(cookies: Dict[str, str]) -> bool:
    """Test automatic token fetching with challenge handling"""
    print_banner("TEST 1: Automatic Token Fetching")
    
    try:
        from metaai_api import MetaAI
        
        print("\n🔄 Initializing MetaAI with your cookies...")
        print("   This will attempt to auto-fetch lsd and fb_dtsg tokens")
        print("   Challenge pages will be handled automatically\n")
        
        ai = MetaAI(cookies=cookies)
        
        print("\n📊 Results:")
        if 'lsd' in ai.cookies and ai.cookies['lsd']:
            print(f"   ✅ lsd token: {ai.cookies['lsd'][:20]}...")
        else:
            print("   ⚠️  lsd token: Not fetched")
        
        if 'fb_dtsg' in ai.cookies and ai.cookies['fb_dtsg']:
            print(f"   ✅ fb_dtsg token: {ai.cookies['fb_dtsg'][:20]}...")
        else:
            print("   ⚠️  fb_dtsg token: Not fetched")
        
        has_tokens = bool(ai.cookies.get('lsd') and ai.cookies.get('fb_dtsg'))
        
        if has_tokens:
            print("\n✅ SUCCESS: Tokens fetched successfully!")
            return True
        else:
            print("\n⚠️  WARNING: Tokens not fully fetched")
            print("   This might be due to challenge page or rate limiting")
            return False
            
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_manual_token_provision(cookies: Dict[str, str]) -> bool:
    """Test manual token provision"""
    print_banner("TEST 2: Manual Token Provision")
    
    print("""
Let's test providing tokens manually (bypass auto-fetch).

To get tokens manually:
1. Stay on https://www.meta.ai with DevTools open
2. Right-click on the page and select 'View Page Source' (Ctrl+U)
3. Press Ctrl+F to search

For 'lsd' token:
   - Search for: "LSD",[],{"token":"
   - Copy the value between the quotes
   - Example: "LSD",[],{"token":"AVqXXXX"} → copy AVqXXXX

For 'fb_dtsg' token:
   - Search for: DTSGInitData",[],{"token":"
   - Copy the value between the quotes
   - Example: "token":"ABCD:XYZ:123"} → copy ABCD:XYZ:123
""")
    
    choice = get_user_input("\nDo you want to test manual token provision? (y/n)", "n")
    
    if choice.lower() != 'y':
        print("⏭️  Skipping manual token test")
        return True
    
    lsd = get_user_input("Enter 'lsd' token")
    fb_dtsg = get_user_input("Enter 'fb_dtsg' token")
    
    if not lsd or not fb_dtsg:
        print("⏭️  Skipping - tokens not provided")
        return True
    
    try:
        from metaai_api import MetaAI
        
        print("\n🔄 Initializing MetaAI with manual tokens...")
        ai = MetaAI(
            cookies=cookies,
            lsd=lsd,
            fb_dtsg=fb_dtsg
        )
        
        print("\n📊 Results:")
        print(f"   ✅ lsd token set: {ai.cookies['lsd'][:20]}...")
        print(f"   ✅ fb_dtsg token set: {ai.cookies['fb_dtsg'][:20]}...")
        
        print("\n✅ SUCCESS: Manual tokens set correctly!")
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        return False

def test_real_api_call(cookies: Dict[str, str]) -> bool:
    """Test a real API call to Meta AI"""
    print_banner("TEST 3: Real API Call")
    
    choice = get_user_input("\nDo you want to test a real API call? (y/n)", "y")
    
    if choice.lower() != 'y':
        print("⏭️  Skipping API call test")
        return True
    
    try:
        from metaai_api import MetaAI
        
        print("\n🔄 Initializing MetaAI...")
        ai = MetaAI(cookies=cookies)
        
        # Test simple prompt
        test_message = "What is 2+2? Reply with just the number."
        print(f"\n📝 Sending test message: '{test_message}'")
        print("   This may take a few seconds...")
        
        response: Dict = ai.prompt(test_message, stream=False)  # type: ignore
        
        print("\n📊 Response:")
        print(f"   Message: {response.get('message', 'No message')[:200]}")
        
        if response.get('message'):
            print("\n✅ SUCCESS: API call worked!")
            return True
        else:
            print("\n⚠️  WARNING: Got response but no message")
            return False
            
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

def save_cookies_to_env(cookies: Dict[str, str]):
    """Offer to save cookies to .env file"""
    print_banner("SAVE CONFIGURATION")
    
    choice = get_user_input("\nDo you want to save cookies to .env file for API server? (y/n)", "y")
    
    if choice.lower() != 'y':
        print("⏭️  Not saving to .env")
        return
    
    env_content = "# Meta AI API Cookie Configuration\n"
    env_content += "# Generated by real_world_test.py\n\n"
    env_content += "# Required cookies\n"
    env_content += f"META_AI_DATR={cookies.get('datr', '')}\n"
    env_content += f"META_AI_ABRA_SESS={cookies.get('abra_sess', '')}\n"
    env_content += f"META_AI_DPR={cookies.get('dpr', '1.25')}\n"
    env_content += f"META_AI_WD={cookies.get('wd', '1536x730')}\n\n"
    
    if 'abra_csrf' in cookies:
        env_content += "# Optional cookies\n"
        env_content += f"META_AI_ABRA_CSRF={cookies['abra_csrf']}\n\n"
    
    env_content += "# Refresh interval in seconds (default: 3600 = 1 hour)\n"
    env_content += "META_AI_REFRESH_INTERVAL_SECONDS=3600\n"
    
    try:
        with open('.env', 'w') as f:
            f.write(env_content)
        print("\n✅ SUCCESS: Cookies saved to .env file")
        print("   You can now start the API server with: python -m uvicorn metaai_api.api_server:app --host 0.0.0.0 --port 8000")
    except Exception as e:
        print(f"\n❌ ERROR: Failed to save .env file - {e}")

def main():
    """Main test flow"""
    print_banner("REAL-WORLD META AI INTEGRATION TEST")
    print("""
This script will test the Meta AI Challenge Page Fix with real cookies
from your browser and verify everything works end-to-end.

You will need:
✓ A browser with Meta AI logged in (https://www.meta.ai)
✓ Access to browser Developer Tools (F12)
✓ A few minutes to complete the tests

Let's get started!
""")
    
    input("Press Enter to begin...")
    
    # Step 1: Extract cookies
    cookies = extract_cookies_from_user()
    
    # Step 2: Test automatic token fetching
    test1_passed = test_token_fetching(cookies)
    
    # Step 3: Test manual token provision
    test2_passed = test_manual_token_provision(cookies)
    
    # Step 4: Test real API call
    test3_passed = test_real_api_call(cookies)
    
    # Step 5: Save configuration
    if test1_passed or test3_passed:
        save_cookies_to_env(cookies)
    
    # Final summary
    print_banner("TEST SUMMARY")
    
    results = {
        "Automatic Token Fetching": test1_passed,
        "Manual Token Provision": test2_passed,
        "Real API Call": test3_passed,
    }
    
    print("\n📊 Results:")
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"   {status}: {test_name}")
    
    total_passed = sum(results.values())
    total_tests = len(results)
    
    print(f"\n📈 Total: {total_passed}/{total_tests} tests passed")
    
    if total_passed == total_tests:
        print("\n🎉 All tests passed! Your Meta AI integration is working perfectly!")
    elif total_passed > 0:
        print("\n⚠️  Some tests passed. Review the output above for details.")
    else:
        print("\n❌ Tests failed. This might be due to:")
        print("   - Incorrect cookies")
        print("   - Meta AI rate limiting")
        print("   - Challenge page issues")
        print("   - Network connectivity")
    
    print("\n" + "="*70)
    print("For more information, see:")
    print("   - QUICK_FIX_GUIDE.md")
    print("   - CHALLENGE_PAGE_FIX.md")
    print("   - examples/manual_token_example.py")
    print("="*70 + "\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
