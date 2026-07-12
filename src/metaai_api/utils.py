"""Utility functions for metaai_api."""
from __future__ import annotations

import os
import logging

DEFAULT_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36 Edg/150.0.0.0"
)

# GraphQL doc_ids (discovered in Meta's web JS)
WARMUP_MUTATION_DOC_ID = "e7f802582dbfed8e181b012e010993eb"
FETCH_CARD_MEDIA_DOC_ID = "344570a4b8110dd9848829731d35c74a"

# DGW connection constants
DGW_APP_ID = "1522763855472543"
DGW_APP_VERSION = "1.0.0"
DGW_AUTH_TYPE = "15:0"
DGW_VERSION = "5"
DGW_UUID = "0"
DGW_TIER = "prod"
DGW_APP_ORIGIN = "meta.ai"

# Media URL filtering
MEDIA_DOMAINS = ("scontent", "metaaiusercontent", "video")
STATIC_PATTERNS = ("rsrc.php", "static.xx.fbcdn", "/rsrc/", "/y_/")

logger = logging.getLogger(__name__)


def get_cookies_from_env() -> dict:
    """Load cookies from environment variables."""
    datr = os.getenv("META_AI_DATR")
    ecto = os.getenv("META_AI_ECTO_1_SESS")
    if not datr or not ecto:
        return {}
    cookies = {"datr": datr, "ecto_1_sess": ecto}
    abra = os.getenv("META_AI_ABRA_SESS")
    if abra:
        cookies["abra_sess"] = abra
    return cookies


def is_media_url(url: str) -> bool:
    """Check if a URL is a generated media URL (not a static asset)."""
    if not url:
        return False
    if any(p in url for p in STATIC_PATTERNS):
        return False
    return any(d in url for d in MEDIA_DOMAINS)
