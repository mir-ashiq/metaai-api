import logging
import random
import re
import time
from typing import Dict, Optional

from requests_html import HTMLSession
import requests
from bs4 import BeautifulSoup

from metaai_api.exceptions import FacebookInvalidCredentialsException


def generate_offline_threading_id() -> str:
    """
    Generates an offline threading ID.

    Returns:
        str: The generated offline threading ID.
    """
    # Maximum value for a 64-bit integer in Python
    max_int = (1 << 64) - 1
    mask22_bits = (1 << 22) - 1

    # Function to get the current timestamp in milliseconds
    def get_current_timestamp():
        return int(time.time() * 1000)

    # Function to generate a random 64-bit integer
    def get_random_64bit_int():
        return random.getrandbits(64)

    # Combine timestamp and random value
    def combine_and_mask(timestamp, random_value):
        shifted_timestamp = timestamp << 22
        masked_random = random_value & mask22_bits
        return (shifted_timestamp | masked_random) & max_int

    timestamp = get_current_timestamp()
    random_value = get_random_64bit_int()
    threading_id = combine_and_mask(timestamp, random_value)

    return str(threading_id)


def extract_value(text: str, start_str: str, end_str: str) -> str:
    """
    Helper function to extract a specific value from the given text using a key.

    Args:
        text (str): The text from which to extract the value.
        start_str (str): The starting key.
        end_str (str): The ending key.

    Returns:
        str: The extracted value.
    """
    start = text.find(start_str)
    if start == -1:
        return ""
    start += len(start_str)
    end = text.find(end_str, start)
    if end == -1:
        return ""
    return text[start:end]


def detect_challenge_page(html_text: str) -> Optional[str]:
    """
    Detect if Meta AI returned a challenge/verification page.
    
    Args:
        html_text (str): The HTML response text.
    
    Returns:
        Optional[str]: The challenge verification URL if found, None otherwise.
    """
    # Check for challenge page indicators
    if "executeChallenge" in html_text or "__rd_verify" in html_text:
        # Extract the verification URL using regex
        match = re.search(r"fetch\('(/__rd_verify[^']+)'", html_text)
        if match:
            return match.group(1)
    return None


def handle_meta_ai_challenge(session: requests.Session, base_url: str = "https://meta.ai", 
                             challenge_url: Optional[str] = None, cookies_dict: Optional[dict] = None,
                             max_retries: int = 3) -> bool:
    """
    Handle Meta AI challenge page by making the verification POST request.
    
    Args:
        session (requests.Session): The requests session to use.
        base_url (str): The base URL for Meta AI.
        challenge_url (Optional[str]): The challenge verification URL.
        cookies_dict (Optional[dict]): Cookies to include in the request.
        max_retries (int): Maximum number of retry attempts.
    
    Returns:
        bool: True if challenge was handled successfully, False otherwise.
    """
    if not challenge_url:
        logging.warning("❌ Challenge handling failed: No challenge URL provided")
        return False
    
    logging.warning(f"[CHALLENGE] Starting challenge handler with URL: {challenge_url}")
    full_url = f"{base_url}{challenge_url}"
    logging.warning(f"[CHALLENGE] Full URL: {full_url}")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": base_url,
        "Origin": base_url,
    }
    
    if cookies_dict:
        cookies_str = "; ".join([f"{k}={v}" for k, v in cookies_dict.items() if v])
        headers["Cookie"] = cookies_str
        logging.warning(f"[CHALLENGE] Using cookies: {list(cookies_dict.keys())}")
    
    try:
        for attempt in range(max_retries):
            logging.warning(f"[CHALLENGE] Attempt {attempt + 1}/{max_retries} - Sending verification request...")
            response = session.post(full_url, headers=headers, timeout=10)
            logging.warning(f"[CHALLENGE] Response status: {response.status_code}")
            logging.warning(f"[CHALLENGE] Response headers: {dict(response.headers)}")
            logging.warning(f"[CHALLENGE] Response cookies: {[c.name for c in response.cookies]}")
            
            if response.status_code == 200:
                # Extract rd_challenge cookie from response if present
                rd_challenge = None
                for cookie in response.cookies:
                    if cookie.name == "rd_challenge":
                        rd_challenge = cookie.value
                        if cookies_dict is not None:
                            cookies_dict["rd_challenge"] = rd_challenge
                        logging.warning(f"[CHALLENGE] ✓ Extracted rd_challenge cookie: {rd_challenge[:50]}...")
                        break
                
                if not rd_challenge:
                    logging.warning("[CHALLENGE] ⚠️ No rd_challenge cookie found in response")
                
                logging.warning("✅ Challenge handled successfully!")
                # Wait a moment for the challenge to process
                time.sleep(2)
                return True
            else:
                logging.warning(f"[CHALLENGE] HTTP {response.status_code} - Retrying...")
            
            time.sleep(1)
        
        logging.error(f"❌ Failed to handle challenge after {max_retries} attempts.")
        return False
    except Exception as e:
        logging.error(f"❌ Error handling Meta AI challenge: {e}")
        return False


def format_response(response: dict) -> str:
    """
    Formats the response from Meta AI to remove unnecessary characters.
    Handles both Abra and Kadabra response structures.

    Args:
        response (dict): The dictionary containing the response to format.

    Returns:
        str: The formatted response.
    """
    text = ""
    
    # Try to get bot_response_message
    bot_response = (
        response.get("data", {})
        .get("node", {})
        .get("bot_response_message", {})
    )
    
    # Try standard composed_text structure (Abra)
    content_list = bot_response.get("composed_text", {}).get("content", [])
    
    if content_list:
        for content in content_list:
            if isinstance(content, dict) and "text" in content:
                text += content["text"] + "\n"
    else:
        # Try multi-step response structure (agent responses with uploaded images)
        content = bot_response.get("content", {})
        if content:
            agent_steps = content.get("agent_steps", [])
            if agent_steps:
                for step in agent_steps:
                    composed_text = step.get("composed_text", {})
                    step_content = composed_text.get("content", [])
                    for item in step_content:
                        if isinstance(item, dict) and "text" in item:
                            text += item["text"] + "\n"
        
        # If still no text, try alternative structures for Kadabra responses
        if not text:
            # Check for direct text field
            if "text" in bot_response:
                text = bot_response["text"]
            # Check for streaming_text
            elif "streaming_text" in bot_response:
                text = bot_response["streaming_text"]
            # Check for message field
            elif "message" in bot_response:
                msg = bot_response["message"]
                if isinstance(msg, str):
                    text = msg
                elif isinstance(msg, dict) and "text" in msg:
                    text = msg["text"]
    
    return text.strip()


# Function to perform the login
def get_fb_session(email, password, proxies=None):
    login_url = "https://www.facebook.com/login/?next"
    headers = {
        "authority": "mbasic.facebook.com",
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "accept-language": "en-US,en;q=0.9",
        "sec-ch-ua": '"Chromium";v="122", "Not(A:Brand";v="24", "Google Chrome";v="122"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"macOS"',
        "sec-fetch-dest": "document",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "none",
        "sec-fetch-user": "?1",
        "upgrade-insecure-requests": "1",
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    }
    # Send the GET request
    response = requests.get(login_url, headers=headers, proxies=proxies)
    soup = BeautifulSoup(response.text, "html.parser")

    # Parse necessary parameters from the login form
    lsd_input = soup.find("input", {"name": "lsd"})
    jazoest_input = soup.find("input", {"name": "jazoest"})
    
    if not lsd_input or not jazoest_input:
        raise FacebookInvalidCredentialsException(
            "Could not find login form parameters. Facebook may have changed their login page."
        )
    
    lsd = lsd_input["value"]  # type: ignore
    jazoest = jazoest_input["value"]  # type: ignore

    # Define the URL and body for the POST request to submit the login form
    post_url = "https://www.facebook.com/login/?next"
    data = {
        "lsd": lsd,
        "jazoest": jazoest,
        "login_source": "comet_headerless_login",
        "email": email,
        "pass": password,
        "login": "1",
        "next": None,
    }

    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:132.0) Gecko/20100101 Firefox/132.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": None,
        "Referer": "https://www.facebook.com/",
        "Content-Type": "application/x-www-form-urlencoded",
        "Origin": "https://www.facebook.com",
        "DNT": "1",
        "Sec-GPC": "1",
        "Connection": "keep-alive",
        "cookie": f"datr={response.cookies.get('datr')};",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-User": "?1",
        "Priority": "u=0, i",
    }

    from requests import cookies

    # Send the POST request
    session = requests.session()
    jar = cookies.RequestsCookieJar()
    session.proxies = proxies  # type: ignore
    session.cookies = jar

    result = session.post(post_url, headers=headers, data=data)
    if "sb" not in jar or "xs" not in jar:
        raise FacebookInvalidCredentialsException(
            "Was not able to login to Facebook. Please check your credentials. "
            "You may also have been rate limited. Try to connect to Facebook manually."
        )

    cookies = {
        **result.cookies.get_dict(),
        "sb": jar["sb"],
        "xs": jar["xs"],
        "fr": jar["fr"],
        "c_user": jar["c_user"],
    }

    response_login = {
        "cookies": cookies,
        "headers": result.headers,
        "response": response.text,
    }
    meta_ai_cookies = get_cookies()

    url = "https://www.meta.ai/state/"

    payload = f'__a=1&lsd={meta_ai_cookies["lsd"]}'
    
    # Build cookie string with rd_challenge if present
    cookie_parts = [
        "ps_n=1",
        "ps_l=1",
        "dpr=2",
        f'_js_datr={meta_ai_cookies["_js_datr"]}',
        f'abra_csrf={meta_ai_cookies["abra_csrf"]}',
        f'datr={meta_ai_cookies["datr"]}'
    ]
    if "rd_challenge" in meta_ai_cookies:
        cookie_parts.append(f'rd_challenge={meta_ai_cookies["rd_challenge"]}')
    
    headers = {
        "authority": "www.meta.ai",
        "accept": "*/*",
        "accept-language": "en-US,en;q=0.9",
        "cache-control": "no-cache",
        "content-type": "application/x-www-form-urlencoded",
        "cookie": "; ".join(cookie_parts),
        "origin": "https://www.meta.ai",
        "pragma": "no-cache",
        "referer": "https://www.meta.ai/",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    }

    response = requests.request(
        "POST", url, headers=headers, data=payload, proxies=proxies
    )

    state = extract_value(response.text, start_str='"state":"', end_str='"')

    url = f"https://www.facebook.com/oidc/?app_id=1358015658191005&scope=openid%20linking&response_type=code&redirect_uri=https%3A%2F%2Fwww.meta.ai%2Fauth%2F&no_universal_links=1&deoia=1&state={state}"
    payload = {}
    
    # Build cookie string with rd_challenge if present
    fb_cookie_parts = [
        f"datr={response_login['cookies']['datr']}",
        f"sb={response_login['cookies']['sb']}",
        f"c_user={response_login['cookies']['c_user']}",
        f"xs={response_login['cookies']['xs']}",
        f"fr={response_login['cookies']['fr']}",
        f"abra_csrf={meta_ai_cookies['abra_csrf']}"
    ]
    if "rd_challenge" in meta_ai_cookies:
        fb_cookie_parts.append(f"rd_challenge={meta_ai_cookies['rd_challenge']}")
    
    headers = {
        "authority": "www.facebook.com",
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "accept-language": "en-US,en;q=0.9",
        "cache-control": "no-cache",
        "cookie": "; ".join(fb_cookie_parts),
        "sec-fetch-dest": "document",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "cross-site",
        "sec-fetch-user": "?1",
        "upgrade-insecure-requests": "1",
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    }
    session = requests.session()
    session.proxies = proxies  # type: ignore
    response = session.get(url, headers=headers, data=payload, allow_redirects=False)

    next_url = response.headers["Location"]

    url = next_url

    payload = {}
    
    # Build cookie string with rd_challenge if present
    final_cookie_parts = [
        "dpr=2",
        f'abra_csrf={meta_ai_cookies["abra_csrf"]}',
        f'datr={meta_ai_cookies["_js_datr"]}'
    ]
    if "rd_challenge" in meta_ai_cookies:
        final_cookie_parts.append(f'rd_challenge={meta_ai_cookies["rd_challenge"]}')
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:125.0) Gecko/20100101 Firefox/125.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "Referer": "https://www.meta.ai/",
        "Connection": "keep-alive",
        "Cookie": "; ".join(final_cookie_parts),
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "cross-site",
        "Sec-Fetch-User": "?1",
        "TE": "trailers",
    }
    session.get(url, headers=headers, data=payload)
    cookies = session.cookies.get_dict()
    if "abra_sess" not in cookies:
        raise FacebookInvalidCredentialsException(
            "Was not able to login to Facebook. Please check your credentials. "
            "You may also have been rate limited. Try to connect to Facebook manually."
        )
    logging.info("Successfully logged in to Facebook.")
    return cookies


def get_cookies() -> dict:
    """
    Extracts necessary cookies from the Meta AI main page.

    Returns:
        dict: A dictionary containing essential cookies.
    """
    session = HTMLSession()
    response = session.get("https://meta.ai")
    cookies = {
        "_js_datr": extract_value(
            response.text, start_str='_js_datr":{"value":"', end_str='",'
        ),
        "abra_csrf": extract_value(
            response.text, start_str='abra_csrf":{"value":"', end_str='",'
        ),
        "datr": extract_value(
            response.text, start_str='datr":{"value":"', end_str='",'
        ),
        "lsd": extract_value(
            response.text, start_str='"LSD",[],{"token":"', end_str='"}'
        ),
    }
    
    # Extract rd_challenge cookie if present (used for challenge verification)
    if "rd_challenge" in response.cookies:
        cookies["rd_challenge"] = response.cookies.get("rd_challenge")
    
    return cookies


def get_session(
    proxy: Optional[Dict] = None, test_url: str = "https://api.ipify.org/?format=json"
) -> requests.Session:
    """
    Get a session with the proxy set.

    Args:
        proxy (Dict): The proxy to use
        test_url (str): A test site from which we check that the proxy is installed correctly.

    Returns:
        requests.Session: A session with the proxy set.
    """
    session = requests.Session()
    if not proxy:
        return session
    response = session.get(test_url, proxies=proxy, timeout=10)
    if response.status_code == 200:
        session.proxies = proxy
        return session
    else:
        raise Exception("Proxy is not working.")
