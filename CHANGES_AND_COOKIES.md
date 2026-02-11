# Meta AI API - Changes Summary & Cookie Requirements

> ⚠️ **OUTDATED DOCUMENT - FOR HISTORICAL REFERENCE ONLY**
>
> This document describes the old cookie requirements from earlier versions.
>
> **Current simplified requirements (as of latest version):**
>
> - Only **3 cookies** needed: `datr`, `abra_sess`, `ecto_1_sess`
> - No tokens (lsd/fb_dtsg) required
> - No dpr, wd, ps_l, ps_n needed
>
> See [README.md](README.md) or [QUICK_START.md](QUICK_START.md) for current setup instructions.

---

## 📝 Summary of Changes Made (Historical)

### File: `src/metaai_api/generation.py`

#### Change 1: Updated Document ID (Line 21)

```python
# BEFORE:
DOC_ID = "904075722675ba2c1a7b333d4c525a1b"

# AFTER:
DOC_ID = "83c79c30d655e0ae6f20af0e129101e2"
```

**Reason:** Old doc_id was outdated. New ID extracted from curl.json (your working browser session).

---

#### Change 2: Image Generation Headers (Lines 151-170)

```python
# BEFORE:
headers = {
    "Accept": "multipart/mixed, application/json",
    "Referer": f"https://www.meta.ai/prompt/{conversation_id}",
    # ... basic headers only
}

# AFTER:
headers = {
    "Accept": "text/event-stream",  # Changed for SSE
    "Referer": "https://www.meta.ai/",  # Simplified
    "Baggage": "sentry-environment=production...",  # Added
    "Priority": "u=1, i",  # Added
    "Sentry-Trace": "...",  # Added
    "Sec-Ch-Prefers-Color-Scheme": "dark",  # Added
    # ... all other headers
}
```

**Reason:** Meta AI expects SSE (Server-Sent Events) streaming with specific tracking headers.

---

#### Change 3: Video Generation Headers (Lines 215-234)

**Same changes as image generation** - both use identical header structure.

---

#### Change 4: Response Parser (Lines 275-280)

```python
# BEFORE:
if 'multipart/mixed' in content_type:
    return self._parse_multipart_response(response)
else:
    return response.json()

# AFTER:
if 'multipart/mixed' in content_type:
    return self._parse_multipart_response(response)
elif 'text/event-stream' in content_type:
    return self._parse_sse_response(response)  # New handler
else:
    return response.json()
```

**Reason:** Added support for SSE streaming responses.

---

#### Change 5: New SSE Parser Method (Lines 337-410)

**Added complete `_parse_sse_response()` method** that:

- Parses Server-Sent Events (SSE) format
- Extracts image/video URLs from streaming data
- Tracks `streamingState` (STREAMING → DONE)
- Returns structured response with images/videos arrays

---

### File: `.env`

#### Updated Cookie Values:

```bash
# CRITICAL - Session token from curl.json line 224
META_AI_ECTO_1_SESS=76fd2c4f-691c-4bfa-9c67-813afdd60262.v1%3A...

# REQUIRED - Portal settings
META_AI_PS_L=1
META_AI_PS_N=1

# Updated JavaScript datr from curl.json
META_AI_JS_DATR=4ciKaQmCIB0wlG3ymlljb5Tw

# Updated window dimensions
META_AI_WD=759x732

# All other cookies remain from curl.json
```

---

## 🍪 Cookie Requirements

### ✅ **10 Required Cookies**

| #   | Cookie Name      | Example Value                                   | Source         | Critical?  |
| --- | ---------------- | ----------------------------------------------- | -------------- | ---------- |
| 1   | **ecto_1_sess**  | `76fd2c4f-691c-4bfa-9c67-813afdd60262.v1%3A...` | curl.json L224 | ⭐ **YES** |
| 2   | **ps_l**         | `1`                                             | curl.json      | ⭐ **YES** |
| 3   | **ps_n**         | `1`                                             | curl.json      | ⭐ **YES** |
| 4   | **datr**         | `-5pnaePoirB_Y94nHinFXSBj`                      | curl.json      | ✅ Yes     |
| 5   | **abra_sess**    | `FrKF8dSY%2FfECFloYDm9yLVZKdW5VVVJVak13F...`    | curl.json      | ✅ Yes     |
| 6   | **dpr**          | `1.25`                                          | curl.json      | ✅ Yes     |
| 7   | **wd**           | `759x732`                                       | curl.json      | ✅ Yes     |
| 8   | **\_js_datr**    | `4ciKaQmCIB0wlG3ymlljb5Tw`                      | curl.json L375 | ✅ Yes     |
| 9   | **abra_csrf**    | Your value                                      | curl.json      | ✅ Yes     |
| 10  | **rd_challenge** | `Q_6hBQOr5mQFfxRtS-a2odnir2-pgv...`             | curl.json      | ✅ Yes     |

---

## 🔑 Cookie Descriptions

### 1. **ecto_1_sess** (MOST CRITICAL) ⭐

- **Purpose:** Main session authentication token
- **Format:** UUID + encrypted session data
- **Location:** curl.json line 224 (used during successful media operations)
- **Expires:** Yes (requires periodic refresh from browser)
- **Impact:** Without this, you get 403 Forbidden or "Access token required" errors

### 2. **ps_l** & **ps_n** (REQUIRED FOR GENERATION) ⭐

- **Purpose:** Portal/service level flags
- **Values:** Both set to `1`
- **Impact:** Without these, image/video generation fails silently

### 3. **datr** (Device Tracking)

- **Purpose:** Device authentication token
- **Format:** Base64-like string
- **Persistence:** Long-lived, rarely changes
- **Impact:** Basic session validation

### 4. **abra_sess** (Abra Session)

- **Purpose:** Additional session layer for Meta AI (Abra project)
- **Format:** URL-encoded encrypted data
- **Impact:** Required for API access

### 5. **dpr** (Device Pixel Ratio)

- **Purpose:** Screen resolution indicator
- **Common Values:** 1, 1.25, 1.5, 2, etc.
- **Impact:** Affects image quality/generation

### 6. **wd** (Window Dimensions)

- **Purpose:** Browser window size
- **Format:** `{width}x{height}` (e.g., `759x732`)
- **Impact:** May affect aspect ratio/generation

### 7. **\_js_datr** (JavaScript DATR)

- **Purpose:** JavaScript-set device token
- **Found:** In HTML response (curl.json line 375)
- **Impact:** Additional device validation

### 8. **abra_csrf** (CSRF Token)

- **Purpose:** Cross-Site Request Forgery protection
- **Impact:** Security validation

### 9. **rd_challenge** (Rate Limit Challenge)

- **Purpose:** Rate limiting/bot detection bypass
- **Changes:** Can be updated by challenge responses
- **Impact:** Prevents rate limit blocks

---

## 📊 Cookie Extraction from curl.json

### Where to Find Each Cookie:

```bash
# Line 82 - Original ecto_1_sess (older, may not work)
ecto_1_sess=76fd2c4f-691c-4bfa-9c67-813afdd60262.v1%3A9A0vyfY3q3hlAN3pZ...

# Line 224 - Working ecto_1_sess ⭐ (USE THIS ONE)
ecto_1_sess=76fd2c4f-691c-4bfa-9c67-813afdd60262.v1%3ATSDWCviJdyy4Ql491qg...

# Line 375 - JavaScript datr in HTML response
"_js_datr":{"value":"4ciKaQmCIB0wlG3ymlljb5Tw"...}

# Cookie string format (lines 82, 224):
-b 'datr=...; abra_sess=...; ps_l=1; ps_n=1; dpr=1.25; rd_challenge=...; wd=759x732; ecto_1_sess=...'
```

---

## 🔄 Cookie Lifecycle

### When to Refresh Cookies:

1. **ecto_1_sess expires** → Get 403 Forbidden
   - **Solution:** Capture new curl.json from browser network tab
2. **rd_challenge updated** → After challenge responses
   - **Solution:** API may return new rd_challenge in Set-Cookie header
3. **Session timeout** → After long inactivity
   - **Solution:** Re-login to Meta AI in browser, capture new session

---

## ✅ Verification Checklist

Before running tests, verify:

- [ ] `.env` file exists with all 10 cookies
- [ ] `ecto_1_sess` is from curl.json **line 224** (not line 82)
- [ ] `ps_l=1` and `ps_n=1` are set
- [ ] `_js_datr` matches value from curl.json line 375
- [ ] All cookies are URL-encoded properly (no spaces)
- [ ] DOC_ID in generation.py is `83c79c30d655e0ae6f20af0e129101e2`

---

## 🎯 Quick Test

Verify cookies are loaded:

```bash
python -c "from metaai_api import MetaAI; ai = MetaAI(); print(f'Cookies: {len(ai.session.cookies)}')"
```

Expected output: `Cookies: 10`

---

## 🐛 Troubleshooting

| Error                   | Cause                    | Solution                               |
| ----------------------- | ------------------------ | -------------------------------------- |
| 403 Forbidden           | Bad ecto_1_sess          | Use line 224 from curl.json            |
| "Access token required" | Wrong ecto_1_sess timing | Use later timestamp from curl.json     |
| 400 Bad Request         | Missing ps_l/ps_n        | Add to .env                            |
| Empty response          | Wrong DOC_ID             | Use `83c79c30d655e0ae6f20af0e129101e2` |
| JSON parse error        | Wrong Accept header      | Use `text/event-stream`                |

---

## 📌 Summary

**Total Changes:** 5 modifications across 2 files  
**Critical Cookie:** ecto_1_sess from curl.json line 224  
**Minimum Required:** 10 cookies  
**New Feature:** SSE streaming response parser  
**Status:** ✅ Image generation working, 🎬 Video generation testing now
