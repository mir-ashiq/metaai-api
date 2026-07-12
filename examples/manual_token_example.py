"""
DEPRECATED EXAMPLE

This example is no longer applicable. Manual token provision (lsd/fb_dtsg)
has been removed from the library.

The Meta AI API now uses cookie-based authentication only:
- datr
- abra_sess
- ecto_1_sess (optional but recommended)

For working examples, see:
- simple_example.py - Basic image/video generation
- image_upload_example.py - Image upload functionality
- video_generation.py - Video generation examples

Chat functionality requiring tokens is currently unavailable.
Use generate_image_new() and generate_video_new() instead.
"""

print("⚠️  DEPRECATED: This example is no longer applicable.")
print("\nManual token provision has been removed.")
print("Use cookie-based authentication instead with generate_image_new() or generate_video_new().")
print("\nSee simple_example.py for a working example.")
response: Dict = ai.prompt("Hello, Meta AI!", stream=False)  # type: ignore
print(f"Response: {response['message']}\n")


# ============================================================================
# Option 2: Manually provide lsd and fb_dtsg tokens
# ============================================================================
print("\nOption 2: Manual token provision\n" + "="*50)

# If automatic fetching fails, you can manually extract tokens from browser
# and provide them directly:

# 1. Open https://www.meta.ai in your browser
# 2. Open Developer Tools (F12)
# 3. Go to Console tab
# 4. Type: document.cookie
# 5. Extract lsd token from the page source:
#    - View page source (Ctrl+U)
#    - Search for: "LSD",[],{"token":"
#    - Copy the token value
# 6. Extract fb_dtsg token:
#    - Search for: DTSGInitData",[],{"token":"
#    - Copy the token value

cookies_with_manual_tokens = {
    "datr": "your_datr_cookie",
    "abra_sess": "your_abra_sess_cookie", 
    "dpr": "1.25",
    "wd": "1536x730",
    "abra_csrf": "your_abra_csrf_cookie"
}

# Provide tokens explicitly
ai_manual = MetaAI(
    cookies=cookies_with_manual_tokens,
    lsd="your_manually_extracted_lsd_token",
    fb_dtsg="your_manually_extracted_fb_dtsg_token"
)

response: Dict = ai_manual.prompt("What can you help me with?", stream=False)  # type: ignore
print(f"Response: {response['message']}\n")


# ============================================================================
# Option 3: Using with Facebook login (auto-handles challenges)
# ============================================================================
print("\nOption 3: Facebook login with auto-challenge handling\n" + "="*50)

# If you have Facebook credentials, the library will authenticate
# and automatically handle any challenge pages
ai_fb = MetaAI(
    fb_email="your_email@example.com",
    fb_password="your_password"
)

response: Dict = ai_fb.prompt("Tell me a fun fact", stream=False)  # type: ignore
print(f"Response: {response['message']}\n")


# ============================================================================
# Extracting tokens from browser (detailed guide)
# ============================================================================
print("\n" + "="*50)
print("HOW TO EXTRACT TOKENS FROM BROWSER")
print("="*50)
print("""
1. Open https://www.meta.ai in your browser and log in

2. Extract cookies:
   - Press F12 to open Developer Tools
   - Go to Application/Storage tab
   - Click on Cookies > https://www.meta.ai
   - Copy these cookie values:
     * datr
     * abra_sess
     * dpr
     * wd
     * abra_csrf

3. Extract lsd token:
   - Right-click on page and select "View Page Source" (Ctrl+U)
   - Press Ctrl+F and search for: "LSD",[],{"token":"
   - Copy the value between the quotes
   - Example: "LSD",[],{"token":"AVq1234567890"}
             Copy: AVq1234567890

4. Extract fb_dtsg token:
   - In the same page source, search for: DTSGInitData",[],{"token":"
   - Copy the value between the quotes
   - Example: DTSGInitData",[],{"token":"ABCD:EFGH:1234567890"}
             Copy: ABCD:EFGH:1234567890

5. Use the extracted values in your code:

   cookies = {
       "datr": "<your_datr>",
       "abra_sess": "<your_abra_sess>",
       "dpr": "1.25",
       "wd": "1536x730",
       "abra_csrf": "<your_abra_csrf>"
   }
   
   ai = MetaAI(
       cookies=cookies,
       lsd="<your_lsd_token>",
       fb_dtsg="<your_fb_dtsg_token>"
   )

Note: Tokens may expire after some time. If you get errors, extract fresh tokens.
""")


# ============================================================================
# Troubleshooting
# ============================================================================
print("\n" + "="*50)
print("TROUBLESHOOTING")
print("="*50)
print("""
If you encounter errors:

1. Enable logging to see detailed information:
   
   import logging
   logging.basicConfig(level=logging.INFO)

2. Check if challenge handling is working:
   - Look for log messages about "Meta AI challenge page"
   - The library will automatically retry with challenge handling

3. Try manual token provision if automatic fetching fails

4. Ensure your cookies are fresh (extracted within the last few hours)

5. If using a proxy, make sure it's working correctly

6. Try accessing https://www.meta.ai directly in your browser
   to ensure you're not blocked or rate-limited
""")
