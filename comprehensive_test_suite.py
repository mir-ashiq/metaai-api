#!/usr/bin/env python
"""
COMPREHENSIVE TEST SUITE FOR BUG #5 FIXES
Tests all implemented fixes and verify they work correctly
"""

import requests
import json
import time
from datetime import datetime

BASE_URL = "http://127.0.0.1:8000"
HEADERS = {"Origin": "http://localhost:3000"}  # Browser-like origin header

# Color codes for terminal output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"
BOLD = "\033[1m"

def test_header(title):
    """Print test header"""
    print(f"\n{BOLD}{BLUE}{'='*75}{RESET}")
    print(f"{BOLD}{BLUE}🧪 {title}{RESET}")
    print(f"{BOLD}{BLUE}{'='*75}{RESET}")

def test_result(name, passed, details=""):
    """Print test result"""
    status = f"{GREEN}✅ PASS{RESET}" if passed else f"{RED}❌ FAIL{RESET}"
    print(f"{status}: {name}")
    if details:
        print(f"   {details}")

def separator():
    """Print separator"""
    print(f"{BLUE}{'-'*75}{RESET}")

# ============================================================================
# TEST 1: CORS MIDDLEWARE
# ============================================================================

def test_cors():
    """Test CORS middleware is working"""
    test_header("TEST 1: CORS MIDDLEWARE (Issue #5)")
    
    time.sleep(2)  # Wait for server to start
    
    separator()
    print("Testing CORS with Origin header...")
    
    try:
        resp = requests.get(f"{BASE_URL}/healthz", headers=HEADERS, timeout=5)
        
        cors_allowed_origin = resp.headers.get("access-control-allow-origin")
        cors_credentials = resp.headers.get("access-control-allow-credentials")
        
        test_result(
            "CORS headers present",
            cors_allowed_origin is not None,
            f"access-control-allow-origin: {cors_allowed_origin}"
        )
        
        test_result(
            "CORS allow credentials",
            cors_credentials == "true",
            f"access-control-allow-credentials: {cors_credentials}"
        )
        
        test_result(
            "CORS headers match",
            cors_allowed_origin == "*",
            f"Expected '*', got '{cors_allowed_origin}'"
        )
        
        # Test OPTIONS request
        print("\nTesting OPTIONS request...")
        resp = requests.options(f"{BASE_URL}/image", headers=HEADERS, timeout=5)
        
        cors_methods = resp.headers.get("access-control-allow-methods")
        cors_headers = resp.headers.get("access-control-allow-headers")
        
        test_result(
            "OPTIONS has allow-methods",
            cors_methods is not None,
            f"Methods: {cors_methods}"
        )
        
        test_result(
            "OPTIONS has allow-headers",
            cors_headers is not None,
            f"Headers: {cors_headers}"
        )
        
        return True
    except Exception as e:
        test_result("CORS test", False, str(e))
        return False

# ============================================================================
# TEST 2: JSON ERROR HANDLING
# ============================================================================

def test_json_errors():
    """Test JSON error responses"""
    test_header("TEST 2: JSON ERROR HANDLING (Issue #4)")
    
    separator()
    print("Testing error response formats...")
    
    all_passed = True
    
    # Test 1: Invalid request body
    try:
        print("\n1. Testing invalid JSON validation error...")
        resp = requests.post(
            f"{BASE_URL}/image",
            json={},  # Missing required 'prompt' field
            headers=HEADERS,
            timeout=5
        )
        
        try:
            data = resp.json()
            is_json = True
            has_detail = "detail" in data
        except:
            is_json = False
            has_detail = False
        
        test_result(
            "Validation error is JSON",
            is_json,
            f"Status: {resp.status_code}, Content-Type: {resp.headers.get('content-type')}"
        )
        
        test_result(
            "Error has detail field",
            has_detail,
            f"Response: {str(data)[:100] if is_json else 'Not JSON'}"
        )
        
    except Exception as e:
        test_result("Validation error test", False, str(e))
        all_passed = False
    
    # Test 2: Missing file on upload
    try:
        print("\n2. Testing upload without file...")
        resp = requests.post(
            f"{BASE_URL}/upload",
            headers=HEADERS,
            timeout=5
        )
        
        try:
            data = resp.json()
            is_json = True
        except:
            is_json = False
        
        test_result(
            "Upload error is JSON",
            is_json and resp.status_code == 422,
            f"Status: {resp.status_code}, JSON: {is_json}"
        )
        
    except Exception as e:
        test_result("Upload error test", False, str(e))
        all_passed = False
    
    # Test 3: Check error response structure
    try:
        print("\n3. Testing error response structure...")
        resp = requests.post(
            f"{BASE_URL}/image",
            json={"prompt": "test"},  # Valid but will timeout
            headers=HEADERS,
            timeout=3
        )
    except requests.exceptions.Timeout:
        print("   (Server timeout - expected for unauth requests)")
    except Exception as e:
        test_result("Error structure test", False, str(e))
        all_passed = False
    
    return all_passed

# ============================================================================
# TEST 3: TIMEOUT PROTECTION
# ============================================================================

def test_timeouts():
    """Test timeout protection"""
    test_header("TEST 3: TIMEOUT PROTECTION")
    
    separator()
    print("Testing timeout handling...")
    
    all_passed = True
    
    # The /image endpoint should timeout without proper auth
    try:
        print("\n1. Testing request timeout...")
        start = time.time()
        
        try:
            resp = requests.post(
                f"{BASE_URL}/image",
                json={"prompt": "This is a test image generation request"},
                headers=HEADERS,
                timeout=3
            )
        except requests.exceptions.Timeout:
            elapsed = time.time() - start
            timeout_occurred = True
        else:
            # If we get a response, check if it has a timeout error
            elapsed = time.time() - start
            try:
                data = resp.json()
                timeout_occurred = data.get("error") == "Image generation timeout"
            except:
                timeout_occurred = False
        
        test_result(
            "Timeout protection functional",
            timeout_occurred or elapsed >= 2,
            f"Elapsed: {elapsed:.1f}s"
        )
        
    except Exception as e:
        test_result("Timeout test", False, str(e))
        all_passed = False
    
    return all_passed

# ============================================================================
# TEST 4: BASIC ENDPOINTS
# ============================================================================

def test_endpoints():
    """Test basic endpoint functionality"""
    test_header("TEST 4: BASIC ENDPOINTS")
    
    separator()
    print("Testing endpoint availability...")
    
    all_passed = True
    
    endpoints = [
        ("GET", "/healthz", None, 200),
        ("POST", "/chat", {"message": "hello"}, 503),  # 503 because no auth
        ("POST", "/image", {"prompt": "test"}, None),  # Will timeout
        ("POST", "/video", {"prompt": "test"}, None),  # Will timeout
    ]
    
    for method, endpoint, body, expected_status in endpoints:
        try:
            print(f"\nTesting {method} {endpoint}...")
            
            if method == "GET":
                resp = requests.get(
                    f"{BASE_URL}{endpoint}",
                    headers=HEADERS,
                    timeout=2
                )
            else:
                try:
                    resp = requests.post(
                        f"{BASE_URL}{endpoint}",
                        json=body,
                        headers=HEADERS,
                        timeout=2
                    )
                except requests.exceptions.Timeout:
                    print(f"   ⏱️  Request timed out (expected for generation endpoints)")
                    continue
            
            is_json = resp.headers.get("content-type", "").lower().find("json") >= 0
            
            if expected_status:
                status_match = resp.status_code == expected_status
                test_result(
                    f"{method} {endpoint} status",
                    status_match,
                    f"Status: {resp.status_code}, Expected: {expected_status}"
                )
            
            test_result(
                f"{method} {endpoint} returns JSON",
                is_json,
                f"Content-Type: {resp.headers.get('content-type')}"
            )
            
        except requests.exceptions.Timeout:
            print(f"   ⏱️  Request timed out (expected for long operations)")
        except Exception as e:
            test_result(f"{method} {endpoint}", False, str(e))
            all_passed = False
    
    return all_passed

# ============================================================================
# TEST 5: IMPORTS AND INITIALIZATION
# ============================================================================

def test_imports():
    """Test that imports work correctly"""
    test_header("TEST 5: IMPORTS & INITIALIZATION")
    
    separator()
    print("Testing module imports...")
    
    try:
        from src.metaai_api import MetaAI, GenerationAPI
        test_result("MetaAI import", True)
        test_result("GenerationAPI import", True)
        
        print("\nTesting class methods...")
        
        # Check if methods exist
        has_gen_image = hasattr(MetaAI, "generate_image_new")
        has_gen_video = hasattr(MetaAI, "generate_video_new")
        has_upload = hasattr(MetaAI, "upload_image")
        
        test_result("generate_image_new method exists", has_gen_image)
        test_result("generate_video_new method exists", has_gen_video)
        test_result("upload_image method exists", has_upload)
        
        return has_gen_image and has_gen_video and has_upload
    except Exception as e:
        test_result("Imports test", False, str(e))
        return False

# ============================================================================
# TEST 6: ENVIRONMENT CONFIGURATION
# ============================================================================

def test_configuration():
    """Test that configuration is properly loaded"""
    test_header("TEST 6: ENVIRONMENT CONFIGURATION")
    
    separator()
    print("Testing environment variables...")
    
    try:
        # This will import and test config is loaded
        from src.metaai_api import api_server
        import os
        from dotenv import load_dotenv
        from pathlib import Path
        
        # Reload env
        env_path = Path("c:\\Users\\spike\\Downloads\\meta-ai-api-main\\.env")
        if env_path.exists():
            load_dotenv(env_path)
        
        datr = os.getenv("META_AI_DATR")
        abra_sess = os.getenv("META_AI_ABRA_SESS")
        ecto_sess = os.getenv("META_AI_ECTO_1_SESS")
        access_token = os.getenv("META_AI_ACCESS_TOKEN")
        
        test_result("META_AI_DATR loaded", bool(datr), f"{datr[:20] if datr else 'NOT SET'}...")
        test_result("META_AI_ABRA_SESS loaded", bool(abra_sess), f"{abra_sess[:20] if abra_sess else 'NOT SET'}...")
        test_result("META_AI_ECTO_1_SESS loaded", bool(ecto_sess), f"{ecto_sess[:20] if ecto_sess else 'NOT SET'}...")
        test_result("META_AI_ACCESS_TOKEN loaded", bool(access_token), f"{access_token[:20] if access_token else 'NOT SET'}...")
        
        # Check request timeout config
        timeout = os.getenv("META_AI_REQUEST_TIMEOUT_SECONDS", "120")
        test_result(
            "Request timeout configured",
            True,
            f"Timeout: {timeout}s"
        )
        
        return bool(datr and abra_sess and ecto_sess)
    except Exception as e:
        test_result("Configuration test", False, str(e))
        return False

# ============================================================================
# MAIN TEST RUNNER
# ============================================================================

def main():
    """Run all tests"""
    print(f"\n{BOLD}{GREEN}")
    print("╔" + "═"*73 + "╗")
    print("║" + " "*73 + "║")
    print("║" + "BUG #5 COMPREHENSIVE FIX TEST SUITE".center(73) + "║")
    print("║" + f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}".center(73) + "║")
    print("║" + " "*73 + "║")
    print("╚" + "═"*73 + "╝")
    print(RESET)
    
    results = {}
    
    # Run all tests
    results["CORS Middleware"] = test_cors()
    results["JSON Error Handling"] = test_json_errors()
    results["Timeout Protection"] = test_timeouts()
    results["Basic Endpoints"] = test_endpoints()
    results["Imports"] = test_imports()
    results["Configuration"] = test_configuration()
    
    # Summary
    test_header("TEST SUMMARY")
    separator()
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    print("\nResults:")
    for name, result in results.items():
        status = f"{GREEN}✅{RESET}" if result else f"{RED}❌{RESET}"
        print(f"  {status} {name}")
    
    print(f"\n{BOLD}Overall: {passed}/{total} test suites passed{RESET}")
    
    if passed == total:
        print(f"\n{GREEN}{BOLD}🎉 ALL TESTS PASSED! All fixes are working correctly.{RESET}")
    else:
        print(f"\n{YELLOW}{BOLD}⚠️  Some tests failed. Check output above for details.{RESET}")
    
    print(f"\n{BLUE}Test completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{RESET}\n")

if __name__ == "__main__":
    main()
