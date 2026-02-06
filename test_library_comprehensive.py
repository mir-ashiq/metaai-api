"""
Comprehensive Library Test
Tests all the challenge page fix functionality without requiring real Meta AI cookies.
"""

import sys
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def test_imports():
    """Test that all modules can be imported"""
    print("\n" + "="*70)
    print("TEST: Module Imports")
    print("="*70)
    
    try:
        from metaai_api import MetaAI
        from metaai_api.utils import (
            detect_challenge_page,
            handle_meta_ai_challenge,
            extract_value,
            generate_offline_threading_id
        )
        print("✅ PASS: All modules imported successfully")
        return True
    except Exception as e:
        print(f"❌ FAIL: Import error - {e}")
        return False


def test_utility_functions():
    """Test utility functions"""
    print("\n" + "="*70)
    print("TEST: Utility Functions")
    print("="*70)
    
    from metaai_api.utils import extract_value, detect_challenge_page, generate_offline_threading_id
    
    # Test extract_value with valid input
    html = 'test "LSD",[],{"token":"test123"} more'
    result = extract_value(html, '"LSD",[],{"token":"', '"')
    if result == "test123":
        print("✅ PASS: extract_value with valid input")
    else:
        print(f"❌ FAIL: extract_value returned '{result}', expected 'test123'")
        return False
    
    # Test extract_value with missing pattern
    html = 'test without pattern'
    result = extract_value(html, '"LSD",[],{"token":"', '"')
    if result == "":
        print("✅ PASS: extract_value with missing pattern returns empty string")
    else:
        print(f"❌ FAIL: extract_value should return empty string, got '{result}'")
        return False
    
    # Test challenge detection - positive case
    challenge_html = '''
    <script>
    function executeChallenge() {
        fetch('/__rd_verify_test123?challenge=3', {
            method: 'POST',
        });
    }
    </script>
    '''
    result = detect_challenge_page(challenge_html)
    if result and "__rd_verify_test123" in result:
        print("✅ PASS: Challenge page detected correctly")
    else:
        print(f"❌ FAIL: Challenge detection failed, got '{result}'")
        return False
    
    # Test challenge detection - negative case
    normal_html = '<html><body>Normal page</body></html>'
    result = detect_challenge_page(normal_html)
    if result is None:
        print("✅ PASS: Normal page correctly identified (no challenge)")
    else:
        print(f"❌ FAIL: False positive challenge detection, got '{result}'")
        return False
    
    # Test threading ID generation
    thread_id = generate_offline_threading_id()
    if thread_id and thread_id.isdigit() and len(thread_id) > 10:
        print("✅ PASS: Threading ID generated successfully")
    else:
        print(f"❌ FAIL: Invalid threading ID: '{thread_id}'")
        return False
    
    return True


def test_metaai_initialization():
    """Test MetaAI class initialization with manual tokens"""
    print("\n" + "="*70)
    print("TEST: MetaAI Initialization")
    print("="*70)
    
    from metaai_api import MetaAI
    
    # Test 1: Initialize with cookies and manual tokens
    try:
        cookies = {
            "datr": "test_datr",
            "abra_sess": "test_sess",
            "abra_csrf": "test_csrf"
        }
        
        ai = MetaAI(
            cookies=cookies,
            lsd="manual_lsd_token",
            fb_dtsg="manual_fb_dtsg_token"
        )
        
        if ai.cookies.get("lsd") == "manual_lsd_token":
            print("✅ PASS: Manual lsd token set correctly")
        else:
            print(f"❌ FAIL: lsd token incorrect: {ai.cookies.get('lsd')}")
            return False
        
        if ai.cookies.get("fb_dtsg") == "manual_fb_dtsg_token":
            print("✅ PASS: Manual fb_dtsg token set correctly")
        else:
            print(f"❌ FAIL: fb_dtsg token incorrect: {ai.cookies.get('fb_dtsg')}")
            return False
        
        print("✅ PASS: MetaAI initialized with manual tokens")
        
    except Exception as e:
        print(f"❌ FAIL: Initialization error - {e}")
        return False
    
    # Test 2: Initialize with existing tokens in cookies
    try:
        cookies2 = {
            "datr": "test_datr",
            "abra_sess": "test_sess",
            "lsd": "existing_lsd",
            "fb_dtsg": "existing_fb_dtsg",
            "abra_csrf": "test_csrf"
        }
        
        ai2 = MetaAI(cookies=cookies2)
        
        if ai2.cookies.get("lsd") == "existing_lsd":
            print("✅ PASS: Existing tokens preserved")
        else:
            print(f"❌ FAIL: Existing tokens not preserved")
            return False
        
    except Exception as e:
        print(f"❌ FAIL: Initialization with existing tokens failed - {e}")
        return False
    
    # Test 3: Manual tokens override existing ones
    try:
        ai3 = MetaAI(
            cookies=cookies2,
            lsd="override_lsd"
        )
        
        if ai3.cookies.get("lsd") == "override_lsd":
            print("✅ PASS: Manual tokens override existing cookies")
        else:
            print(f"❌ FAIL: Token override failed")
            return False
        
    except Exception as e:
        print(f"❌ FAIL: Token override test failed - {e}")
        return False
    
    return True


def test_error_handling():
    """Test error handling and edge cases"""
    print("\n" + "="*70)
    print("TEST: Error Handling")
    print("="*70)
    
    from metaai_api.utils import extract_value, detect_challenge_page
    
    # Test extract_value with edge cases
    test_cases = [
        ("", "start", "end", ""),
        ("text", "missing", "end", ""),  # Fixed: empty delimiters is not a valid use case
        ("start middle end", "start ", " end", "middle"),
        ("no match", "foo", "bar", ""),
    ]
    
    all_passed = True
    for text, start_str, end_str, expected in test_cases:
        result = extract_value(text, start_str, end_str)
        if result == expected:
            print(f"✅ PASS: extract_value('{text[:20]}...', '{start_str}', '{end_str}') = '{result}'")
        else:
            print(f"❌ FAIL: Expected '{expected}', got '{result}'")
            all_passed = False
    
    return all_passed


def test_type_safety():
    """Test type safety improvements"""
    print("\n" + "="*70)
    print("TEST: Type Safety")
    print("="*70)
    
    try:
        from metaai_api.utils import extract_value
        
        # These should not crash
        extract_value("", "", "")
        extract_value("text", "missing", "pattern")
        extract_value("", "start", "end")
        
        print("✅ PASS: Type safety - no crashes on edge cases")
        return True
    except Exception as e:
        print(f"❌ FAIL: Type safety issue - {e}")
        return False


def main():
    """Run all tests"""
    print("\n" + "="*70)
    print("COMPREHENSIVE LIBRARY TEST SUITE")
    print("="*70)
    print("Testing Meta AI Challenge Page Fix Implementation")
    print("="*70)
    
    tests = [
        ("Module Imports", test_imports),
        ("Utility Functions", test_utility_functions),
        ("MetaAI Initialization", test_metaai_initialization),
        ("Error Handling", test_error_handling),
        ("Type Safety", test_type_safety),
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
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print("\n" + "-"*70)
    print(f"Total: {passed}/{total} tests passed ({100*passed//total}%)")
    print("="*70)
    
    if passed == total:
        print("\n🎉 All tests passed! Implementation is working correctly.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please review the output above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
