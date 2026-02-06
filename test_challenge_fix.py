"""
Test script for Meta AI Challenge Page Fix

This script tests the new challenge page handling functionality.
"""

import logging
import sys

# Enable detailed logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

from metaai_api import MetaAI
from metaai_api.utils import detect_challenge_page, handle_meta_ai_challenge


def test_challenge_detection():
    """Test challenge page detection"""
    print("\n" + "="*60)
    print("TEST 1: Challenge Page Detection")
    print("="*60)
    
    # Sample challenge page HTML
    challenge_html = """
    <html>
    <head><title>Meta AI</title></head>
    <body>
    <script>
    (function() {
      if (document.readyState !== 'loading') {
        executeChallenge();
      } else {
        document.addEventListener('DOMContentLoaded', executeChallenge);
      }
      function executeChallenge() {
        fetch('/__rd_verify_Q_6hBQNNDi-1czYs7Nd1c4_mFtaBbjTDFEM0u4U3Khqa0diOCQ?challenge=3', {
          method: 'POST',
        })
        .finally(() => window.location.reload());
      }
    })();
    </script>
    </body>
    </html>
    """
    
    challenge_url = detect_challenge_page(challenge_html)
    if challenge_url:
        print(f"✅ PASS: Challenge detected")
        print(f"   Challenge URL: {challenge_url}")
    else:
        print("❌ FAIL: Challenge not detected")
        return False
    
    # Test normal page (no challenge)
    normal_html = """
    <html>
    <script>
    var config = {"LSD":[],"token":"AVq1234567890"};
    </script>
    </html>
    """
    
    challenge_url = detect_challenge_page(normal_html)
    if challenge_url is None:
        print("✅ PASS: Normal page correctly identified (no challenge)")
    else:
        print("❌ FAIL: False positive - detected challenge in normal page")
        return False
    
    return True


def test_extract_value():
    """Test improved extract_value function"""
    print("\n" + "="*60)
    print("TEST 2: Extract Value Function")
    print("="*60)
    
    from metaai_api.utils import extract_value
    
    # Test successful extraction
    html = 'Some text "LSD",[],{"token":"AVq1234567890"} more text'
    result = extract_value(html, start_str='"LSD",[],{"token":"', end_str='"')
    
    if result == "AVq1234567890":
        print(f"✅ PASS: Token extracted correctly: {result}")
    else:
        print(f"❌ FAIL: Expected 'AVq1234567890', got '{result}'")
        return False
    
    # Test missing pattern (should return empty string, not crash)
    html = 'Some text without the pattern'
    result = extract_value(html, start_str='"LSD",[],{"token":"', end_str='"')
    
    if result == "":
        print("✅ PASS: Missing pattern handled gracefully (empty string)")
    else:
        print(f"❌ FAIL: Expected empty string, got '{result}'")
        return False
    
    return True


def test_manual_token_provision():
    """Test manual token provision"""
    print("\n" + "="*60)
    print("TEST 3: Manual Token Provision")
    print("="*60)
    
    try:
        # Test that manual tokens are accepted and stored
        cookies = {
            "datr": "test_datr",
            "abra_sess": "test_abra_sess",
            "abra_csrf": "test_csrf"
        }
        
        ai = MetaAI(
            cookies=cookies,
            lsd="manual_lsd_token",
            fb_dtsg="manual_fb_dtsg_token"
        )
        
        # Check if tokens were set correctly
        if ai.cookies.get("lsd") == "manual_lsd_token":
            print("✅ PASS: lsd token set correctly")
        else:
            print(f"❌ FAIL: lsd token not set. Got: {ai.cookies.get('lsd')}")
            return False
        
        if ai.cookies.get("fb_dtsg") == "manual_fb_dtsg_token":
            print("✅ PASS: fb_dtsg token set correctly")
        else:
            print(f"❌ FAIL: fb_dtsg token not set. Got: {ai.cookies.get('fb_dtsg')}")
            return False
        
        print("✅ PASS: Manual token provision works correctly")
        return True
        
    except Exception as e:
        print(f"❌ FAIL: Exception occurred: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_constructor_parameters():
    """Test that new constructor parameters don't break existing code"""
    print("\n" + "="*60)
    print("TEST 4: Backward Compatibility")
    print("="*60)
    
    try:
        # Test old-style initialization (should still work)
        cookies = {
            "datr": "test_datr",
            "abra_sess": "test_abra_sess",
            "lsd": "existing_lsd",
            "fb_dtsg": "existing_fb_dtsg",
            "abra_csrf": "test_csrf"
        }
        
        ai = MetaAI(cookies=cookies)
        
        if ai.cookies.get("lsd") == "existing_lsd":
            print("✅ PASS: Existing cookies preserved")
        else:
            print(f"❌ FAIL: Cookie not preserved. Got: {ai.cookies.get('lsd')}")
            return False
        
        # Test that manual tokens override existing ones
        ai2 = MetaAI(
            cookies=cookies,
            lsd="override_lsd"
        )
        
        if ai2.cookies.get("lsd") == "override_lsd":
            print("✅ PASS: Manual tokens override existing cookies")
        else:
            print(f"❌ FAIL: Token not overridden. Got: {ai2.cookies.get('lsd')}")
            return False
        
        print("✅ PASS: Backward compatibility maintained")
        return True
        
    except Exception as e:
        print(f"❌ FAIL: Exception occurred: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("META AI CHALLENGE PAGE FIX - TEST SUITE")
    print("="*60)
    
    tests = [
        ("Challenge Detection", test_challenge_detection),
        ("Extract Value", test_extract_value),
        ("Manual Token Provision", test_manual_token_provision),
        ("Backward Compatibility", test_constructor_parameters),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n❌ {test_name} - EXCEPTION: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print("\n" + "-"*60)
    print(f"Total: {passed}/{total} tests passed")
    print("="*60)
    
    if passed == total:
        print("\n🎉 All tests passed! Challenge page fix is working correctly.")
        return 0
    else:
        print(f"\n⚠️ {total - passed} test(s) failed. Please review the output above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
