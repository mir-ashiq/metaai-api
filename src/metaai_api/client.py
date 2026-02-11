import json
import logging
from typing import Dict, List, Optional

import requests

logger = logging.getLogger(__name__)


def _parse_cookie_header(raw_cookie: str) -> Dict[str, str]:
    """Parse cookie string into dictionary."""
    parts = [p.strip() for p in raw_cookie.split(";") if p.strip()]
    cookies: Dict[str, str] = {}
    for part in parts:
        if "=" not in part:
            continue
        name, value = part.split("=", 1)
        cookies[name.strip()] = value.strip()
    return cookies


def send_animate_request(
    user_cookie_header: str, 
    prompt: str,
    fb_dtsg: Optional[str] = None,
    lsd: Optional[str] = None,
    jazoest: Optional[str] = None
) -> Dict:
    """
    Send a prompt to Meta AI's animate endpoint using provided cookies.
    
    Args:
        user_cookie_header: Cookie header string (e.g., "datr=...; abra_sess=...")
        prompt: Text prompt for animation/video generation
        fb_dtsg: Optional Facebook DTSG token. If not provided, uses placeholder.
        lsd: Optional LSD token. If not provided, uses placeholder.
        jazoest: Optional jazoest token. If not provided, uses placeholder.
    
    Returns:
        Response JSON from Meta AI API
    """
    cookies = _parse_cookie_header(user_cookie_header)
    
    # Use provided tokens or fallback to placeholders
    fb_dtsg = fb_dtsg or "NAfs8i5CfuTxSgY049krPWfh6MLk1zW--f6qnzvqgeEaPvOWcpH_esA:2:1763623145"
    lsd = lsd or "MMUBfnMuJ_zHq68M_QsA9p"
    jazoest = jazoest or "25561"
    
    logger.info(f"Sending animate request with prompt: {prompt[:50]}...")

    headers = {
        "accept": "*/*",
        "accept-language": "en-US,en;q=0.5",
        "content-type": "multipart/form-data; boundary=----WebKitFormBoundarybkOB5PgK5hbMvG6A",
        "origin": "https://www.meta.ai",
        "priority": "u=1, i",
        "referer": "https://www.meta.ai/",
        "sec-ch-ua": '"Brave";v="141", "Not?A_Brand";v="8", "Chromium";v="141"',
        "sec-ch-ua-full-version-list": '"Brave";v="141.0.0.0", "Not?A_Brand";v="8.0.0.0", "Chromium";v="141.0.0.0"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-model": '""',
        "sec-ch-ua-platform": '"Windows"',
        "sec-ch-ua-platform-version": '"19.0.0"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "sec-gpc": "1",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36",
        "x-asbd-id": "359341",
        "x-fb-lsd": lsd,
        "cookie": user_cookie_header,
    }

    params = {
        "fb_dtsg": fb_dtsg,
        "jazoest": jazoest,
        "lsd": lsd,
    }

    variables = json.dumps({"message": {"sensitive_string_value": prompt}})

    data = {
        "av": (None, "813590375178585"),
        "__user": (None, "0"),
        "__a": (None, "1"),
        "__req": (None, "1b"),
        "__hs": (None, "20412.HYP:kadabra_pkg.2.1...0"),
        "dpr": (None, "1"),
        "__ccg": (None, "GOOD"),
        "__rev": (None, "1030167105"),
        "__s": (None, "pfvlzb:j08r3n:u2o3ge"),
        "__hsi": (None, "7574782986293208112"),
        "__dyn": (None, "7xeUjG1mxu1syUqxemh0no6u5U4e2C1vzEdE98K360CEbo19oe8hw2nVEtwMw6ywaq221FwpUO0n24oaEnxO0Bo7O2l0Fwqo31w9O1lwlE-U2zxe2GewbS361qw82dUlwhE-15wmo423-0j52oS0Io5d0bS1LBwNwKG0WE8oC1IwGw-wlUcE2-G2O7E5y1rwa211wo84y1ix-0QU4G"),
        "__csr": (None, ""),
        "__hsdp": (None, ""),
        "__hblp": (None, ""),
        "__sjsp": (None, ""),
        "__comet_req": (None, "72"),
        "fb_dtsg": (None, fb_dtsg),
        "jazoest": (None, jazoest),
        "lsd": (None, lsd),
        "__spin_r": (None, "1030167105"),
        "__spin_b": (None, "trunk"),
        "__spin_t": (None, "1763641598"),
        "__jssesw": (None, "1"),
        "__crn": (None, "comet.kadabra.KadabraPromptRoute"),
        "fb_api_caller_class": (None, "RelayModern"),
        "fb_api_req_friendly_name": (None, "useKadabraSendMessageMutation"),
        "server_timestamps": (None, "true"),
        "variables": (None, variables),
        "doc_id": (None, "26069859009269605"),
    }

    try:
        response = requests.post(
            "https://www.meta.ai/api/graphql/",
            params=params,
            cookies=cookies,
            headers=headers,
            data=data,
        )
        response.raise_for_status()
        logger.info("Animate request sent successfully")
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Error sending animate request: {e}")
        raise


def extract_video_urls_from_fetch_response(fetch_response: Dict) -> List[str]:
    urls: List[str] = []

    data = fetch_response.get("data", {})
    fetch_post = data.get("xfb_genai_fetch_post") or data.get("xab_abra__xfb_genai_fetch_post") or {}

    messages = fetch_post.get("messages", {}).get("edges", [])
    for edge in messages:
        node = edge.get("node", {})
        content = node.get("content", {})
        imagine_video = content.get("imagine_video") or {}

        videos = imagine_video.get("videos", {}).get("nodes", [])
        for video in videos:
            uri = video.get("video_url") or video.get("uri")
            if uri:
                urls.append(uri)
            delivery = video.get("videoDeliveryResponseResult") or {}
            prog = delivery.get("progressive_urls", [])
            for p in prog:
                pu = p.get("progressive_url")
                if pu:
                    urls.append(pu)

        single_video = imagine_video.get("video") or {}
        if isinstance(single_video, dict):
            uri = single_video.get("video_url") or single_video.get("uri")
            if uri:
                urls.append(uri)
            delivery = single_video.get("videoDeliveryResponseResult") or {}
            prog = delivery.get("progressive_urls", [])
            for p in prog:
                pu = p.get("progressive_url")
                if pu:
                    urls.append(pu)

    # Deduplicate while preserving order
    seen = set()
    unique_urls: List[str] = []
    for u in urls:
        if u not in seen:
            seen.add(u)
            unique_urls.append(u)
    return unique_urls

