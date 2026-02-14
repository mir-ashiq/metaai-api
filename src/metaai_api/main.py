import json
import logging
import os
import time
import urllib.parse
import uuid
from pathlib import Path
from typing import Dict, List, Generator, Iterator, Optional, Union, Any

import requests
from dotenv import load_dotenv
from requests_html import HTMLSession

from metaai_api.utils import (
    generate_offline_threading_id,
    extract_value,
    format_response,
    detect_challenge_page,
    handle_meta_ai_challenge,
)

from metaai_api.utils import get_fb_session, get_session

from metaai_api.exceptions import FacebookRegionBlocked
from metaai_api.image_upload import ImageUploader
from metaai_api.generation import GenerationAPI

MAX_RETRIES = 3


class MetaAI:
    """
    A class to interact with Meta AI for image and video generation.
    
    WORKING FEATURES:
    - generate_image_new(): Generate AI images with custom orientations
    - generate_video_new(): Create AI videos from text prompts
    - upload_image(): Upload images for generation/editing
    
    UNAVAILABLE FEATURES:
    - prompt() / ask(): Chat functionality (requires problematic lsd/fb_dtsg tokens)
    - Streaming chat responses
    - Real-time data queries
    
    Authentication: Uses cookie-based auth only (datr, abra_sess, ecto_1_sess)
    """

    def __init__(
        self, 
        fb_email: Optional[str] = None, 
        fb_password: Optional[str] = None, 
        cookies: Optional[dict] = None, 
        proxy: Optional[dict] = None
    ):
        # Load .env file from workspace root
        env_path = Path(__file__).parent.parent.parent / ".env"
        if env_path.exists():
            load_dotenv(env_path)
            logging.info(f"Loaded .env from: {env_path}")
        
        self.session = get_session()
        self.session.headers.update(
            {
                "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            }
        )
        self.access_token = None
        self.fb_email = fb_email
        self.fb_password = fb_password
        self.proxy = proxy

        self.is_authed = (fb_password is not None and fb_email is not None) or cookies is not None
        
        # Try loading cookies from .env first if no cookies passed
        env_cookies = self._load_cookies_from_env()
        if env_cookies:
            self.cookies = env_cookies
            logging.info("✅ Loaded cookies from .env file (cookie-based auth only)")
            self.is_authed = True
        elif cookies is not None:
            self.cookies = cookies
            logging.info("Using provided cookies (cookie-based auth only)")
        else:
            self.cookies = self.get_cookies()
            logging.info("Fetched cookies from Meta AI website")
            # Update is_authed if we successfully got cookies
            if self.cookies:
                self.is_authed = True
            
        self.external_conversation_id = None
        self.offline_threading_id = None
        
        # Extract access token from page HTML (needed for image upload OAuth)
        if self.cookies:
            self.access_token = self.extract_access_token_from_page()
            if not self.access_token:
                logging.warning("⚠️ Could not extract accessToken from page. Image upload may fail.")
        
        # Initialize Generation API
        self.generation_api = GenerationAPI(session=self.session, cookies=self.cookies)

    def _load_cookies_from_env(self) -> Optional[Dict[str, str]]:
        """
        Load cookies from environment variables (META_AI_* prefix).
        
        CRITICAL: ecto_1_sess is the primary session token and must be present.
        
        Environment variables expected:
        - META_AI_DATR: Required - Device identifier cookie
        - META_AI_ABRA_SESS: Required - Session cookie
        - META_AI_ECTO_1_SESS: Critical - Session state token (MOST IMPORTANT)
        - META_AI_DPR: Optional - Device pixel ratio
        - META_AI_WD: Optional - Window dimensions
        - META_AI_JS_DATR: Optional - JavaScript datr
        - META_AI_ABRA_CSRF: Optional - CSRF token
        - META_AI_PS_L: Optional - Page state (usually 1)
        - META_AI_PS_N: Optional - Page state (usually 1)
        - META_AI_RD_CHALLENGE: Optional - Challenge cookie
        
        Returns:
            dict or None: Cookie dictionary if at least required cookies are found, None otherwise
        """
        required_cookies = {
            "datr": os.getenv("META_AI_DATR"),
            "abra_sess": os.getenv("META_AI_ABRA_SESS"),
        }
        
        # Check if required cookies are present
        if not (required_cookies["datr"] and required_cookies["abra_sess"]):
            return None
        
        # Build complete cookie dict with required cookies
        cookies = {
            "datr": required_cookies["datr"],
            "abra_sess": required_cookies["abra_sess"],
        }
        
        # Add critical session cookie (MOST IMPORTANT)
        ecto_session = os.getenv("META_AI_ECTO_1_SESS")
        if ecto_session:
            cookies["ecto_1_sess"] = ecto_session
            logging.debug("Critical ecto_1_sess cookie loaded")
        else:
            logging.warning("META_AI_ECTO_1_SESS not found - API may return empty responses")
        
        # Add optional cookies if present
        optional_cookies = {
            "dpr": os.getenv("META_AI_DPR"),
            "wd": os.getenv("META_AI_WD"),
            "_js_datr": os.getenv("META_AI_JS_DATR"),
            "abra_csrf": os.getenv("META_AI_ABRA_CSRF"),
            "rd_challenge": os.getenv("META_AI_RD_CHALLENGE"),
            "ps_l": os.getenv("META_AI_PS_L"),
            "ps_n": os.getenv("META_AI_PS_N"),
        }
        
        for key, value in optional_cookies.items():
            if value:
                cookies[key] = value
        
        logging.info(f"Cookies loaded from .env: {list(cookies.keys())}")
        return cookies

    def extract_access_token_from_page(self) -> Optional[str]:
        """
        Extract the accessToken from meta.ai page HTML.
        This is the actual OAuth token needed for image upload, NOT the ecto_1_sess cookie.
        
        Returns:
            str: The accessToken in format "ecto1:..." or None if extraction fails
        """
        try:
            import re
            
            # Fetch meta.ai page with cookies
            cookie_header = self.get_cookie_header()
            headers = {
                "cookie": cookie_header,
                "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                              "(KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36"
            }
            
            response = self.session.get("https://meta.ai", headers=headers)
            response.raise_for_status()
            
            # Extract accessToken from page HTML using regex (handles escaped quotes)
            # Pattern matches: \"accessToken\":\"ecto1:...\" (escaped in HTML)
            pattern = r'accessToken\\":\\"(ecto1:[^"\\]+)'
            match = re.search(pattern, response.text)
            
            if match:
                access_token = match.group(1)
                logging.info(f"✅ Extracted accessToken from page (length: {len(access_token)} chars)")
                return access_token
            else:
                logging.warning("⚠️ accessToken not found in page HTML using regex pattern")
                return None
                
        except Exception as e:
            logging.error(f"❌ Failed to extract accessToken from page: {e}")
            return None

    def get_cookies_dict(self) -> Dict[str, str]:
        """
        Get cookies as a dictionary.
        
        Returns:
            dict: Cookie dictionary
        """
        return self.cookies.copy() if self.cookies else {}

    def get_cookie_header(self) -> str:
        """
        Get cookies formatted as a Cookie header string.
        
        Returns:
            str: Cookie header value (e.g., "datr=abc; abra_sess=def; ...")
        """
        if not self.cookies:
            return ""
        return "; ".join([f"{k}={v}" for k, v in self.cookies.items()])

    def _handle_expired_session(self, error_msg: str = ""):
        """
        Handle expired ecto_1_sess cookie and provide user guidance.
        
        Args:
            error_msg (str): Optional error message from the API response
        """
        logging.error("="*70)
        logging.error("❌ Cookie Expired: ecto_1_sess needs to be refreshed")
        logging.error("="*70)
        logging.error("")
        logging.error("Your session cookie (ecto_1_sess) has expired.")
        logging.error("")
        logging.error("To get fresh cookies, choose one of these methods:")
        logging.error("")
        logging.error("METHOD 1 (Automatic - Recommended):")
        logging.error("   Run: python auto_refresh_cookies.py")
        logging.error("   This will open a browser, let you log in, and extract cookies automatically.")
        logging.error("")
        logging.error("METHOD 2 (Manual - Quick):")
        logging.error("   1. Open https://meta.ai in your browser and log in")
        logging.error("   2. Open DevTools (F12) → Network tab")
        logging.error("   3. Generate an image or perform any action")
        logging.error("   4. Right-click the 'graphql' request → Copy → Copy as cURL")
        logging.error("   5. Save to curl.json")
        logging.error("   6. Run: python refresh_cookies.py")
        logging.error("")
        logging.error("="*70)
        
        if error_msg:
            logging.debug(f"API Error: {error_msg}")

    def _check_response_for_auth_error(self, response: requests.Response) -> bool:
        """
        Check if API response indicates expired/invalid authentication.
        
        Args:
            response: requests Response object
            
        Returns:
            bool: True if authentication error detected, False otherwise
        """
        # Check for 403 Forbidden
        if response.status_code == 403:
            self._handle_expired_session("403 Forbidden - session expired")
            return True
        
        # Check response content for auth errors
        try:
            if response.text:
                error_indicators = [
                    "Access token required",
                    "authentication",
                    "unauthorized",
                    "invalid session",
                    "session expired"
                ]
                
                response_lower = response.text.lower()
                for indicator in error_indicators:
                    if indicator in response_lower:
                        self._handle_expired_session(f"Auth error detected: {indicator}")
                        return True
        except:
            pass
        
        return False

    # DEPRECATED: Token fetching removed - chat functionality unavailable
    # Image and video generation use cookie-based authentication only
    def _fetch_missing_tokens(self, max_retries: int = 3):
        """
        DEPRECATED: This method is no longer used.
        
        Token fetching (lsd/fb_dtsg) has been removed as it causes authentication
        challenges and is not needed for working features (image/video generation).
        Chat functionality that requires these tokens is currently unavailable.
        """
        logging.warning("Token fetching is deprecated and disabled. Use cookie-based auth only.")
        logging.warning("Chat operations are not supported. Use generate_image_new() or generate_video_new() instead.")

    def get_access_token(self) -> str:
        """
        DEPRECATED: Retrieves an access token using Meta's authentication API.
        
        NOTE: Non-authenticated temporary access is currently unavailable.
        Use cookie-based authentication instead with generate_image_new() or generate_video_new().

        Returns:
            str: A valid access token (if already cached), otherwise raises an error.
        """
        
        logging.warning("get_access_token() is deprecated. Non-authenticated access is unavailable.")
        logging.warning("Use cookie-based authentication with generate_image_new() or generate_video_new().")

        if self.access_token:
            return self.access_token

        # Legacy code kept for compatibility - will fail without proper cookies
        url = "https://www.meta.ai/api/graphql/"
        payload = {
            "lsd": self.cookies.get("lsd", ""),  # Safe access - won't crash if missing
            "fb_api_caller_class": "RelayModern",
            "fb_api_req_friendly_name": "useAbraAcceptTOSForTempUserMutation",
            "variables": {
                "dob": "1999-01-01",
                "icebreaker_type": "TEXT",
                "__relay_internal__pv__WebPixelRatiorelayprovider": 1,
            },
            "doc_id": "7604648749596940",
        }
        payload = urllib.parse.urlencode(payload)  # noqa
        headers = {
            "content-type": "application/x-www-form-urlencoded",
            "cookie": f'_js_datr={self.cookies.get("_js_datr", "")}; '
            f'abra_csrf={self.cookies.get("abra_csrf", "")}; datr={self.cookies.get("datr", "")};',
            "sec-fetch-site": "same-origin",
            "x-fb-friendly-name": "useAbraAcceptTOSForTempUserMutation",
        }

        response = self.session.post(url, headers=headers, data=payload)

        try:
            auth_json = response.json()
        except json.JSONDecodeError:
            raise FacebookRegionBlocked(
                "Unable to receive a valid response from Meta AI. This is likely due to your region being blocked. "
                "Try manually accessing https://www.meta.ai/ to confirm."
            )

        access_token = auth_json["data"]["xab_abra_accept_terms_of_service"][
            "new_temp_user_auth"
        ]["access_token"]

        # Need to sleep for a bit, for some reason the API doesn't like it when we send request too quickly
        # (maybe Meta needs to register Cookies on their side?)
        time.sleep(1)

        return access_token

    def prompt(
        self,
        message: str,
        stream: bool = False,
        attempts: int = 0,
        new_conversation: bool = False,
        images: Optional[list] = None,
        media_ids: Optional[list] = None,
        attachment_metadata: Optional[Dict[str, Any]] = None,
        is_image_generation: bool = False,
        orientation: Optional[str] = None,
    ) -> Union[Dict, Generator[Dict, None, None]]:
        """
        DEPRECATED: Chat functionality is currently unavailable.
        
        Chat operations require lsd/fb_dtsg tokens which cause authentication challenges.
        Use the working image and video generation methods instead:
        - generate_image_new() for AI image generation
        - generate_video_new() for AI video generation
        
        This method is kept for API compatibility but will not work for chat operations.
        It may still be used internally for legacy image generation flows.

        Args:
            message (str): The message to send.
            stream (bool): Whether to stream the response or not. Defaults to False.
            attempts (int): The number of attempts to retry if an error occurs. Defaults to 0.
            new_conversation (bool): Whether to start a new conversation or not. Defaults to False.
            images (list): List of image URLs to animate (for video generation). Defaults to None.
            media_ids (list): List of media IDs from uploaded images to include in the prompt. Defaults to None.
            attachment_metadata (dict): Optional dict with 'file_size' (int) and 'mime_type' (str). Defaults to None.
            is_image_generation (bool): Whether this is for image generation (vs chat). Defaults to False.
            orientation (str): Image orientation for generation. Valid values: "LANDSCAPE", "VERTICAL", "SQUARE". Defaults to "VERTICAL".

        Returns:
            dict: A dictionary containing the response message and sources.

        Raises:
            Exception: If unable to obtain a valid response after several attempts.
        """
        if not self.is_authed:
            self.access_token = self.get_access_token()
            auth_payload = {"access_token": self.access_token}
            url = "https://graph.meta.ai/graphql?locale=user"

        else:
            # Chat functionality is currently unavailable
            # This requires lsd/fb_dtsg tokens which cause authentication issues
            logging.warning("Chat operations are not supported - use image/video generation instead")
            auth_payload = {
                "fb_dtsg": "",
                "lsd": "",
            }
            url = "https://www.meta.ai/api/graphql/"

        if not self.external_conversation_id or new_conversation:
            external_id = str(uuid.uuid4())
            self.external_conversation_id = external_id
        
        # Handle video generation with images
        flash_video_input = {"images": []}
        if images:
            flash_video_input = {"images": images}
        
        # Handle uploaded media attachments
        attachments_v2 = []
        if media_ids:
            attachments_v2 = [str(mid) for mid in media_ids]
        
        # Generate offline threading IDs
        offline_threading_id = generate_offline_threading_id()
        bot_offline_threading_id = str(int(offline_threading_id) + 1)
        thread_session_id = str(uuid.uuid4())
        
        # Determine entrypoint based on context
        if images:
            # Video generation with images uses CHAT
            entrypoint = "KADABRA__CHAT__UNIFIED_INPUT_BAR"
        elif media_ids or orientation:
            # Image generation with orientation OR uploaded images uses DISCOVER
            entrypoint = "KADABRA__DISCOVER__UNIFIED_INPUT_BAR"
        else:
            entrypoint = "ABRA__CHAT__TEXT"
        
        # Set friendly name based on entrypoint
        friendly_name = "useKadabraSendMessageMutation" if entrypoint.startswith("KADABRA") else "useAbraSendMessageMutation"
        
        # Build variables dictionary
        is_kadabra = entrypoint.startswith("KADABRA")
        
        if is_kadabra:
            # Full Kadabra variables for image generation
            variables = {
                "message": {"sensitive_string_value": message},
                "externalConversationId": self.external_conversation_id,
                "offlineThreadingId": offline_threading_id,
                "threadSessionId": thread_session_id,
                "isNewConversation": new_conversation or not self.offline_threading_id,
                "suggestedPromptIndex": None,
                "promptPrefix": None,
                "entrypoint": entrypoint,
                "attachments": [],
                "attachmentsV2": attachments_v2,
                "activeMediaSets": [],
                "activeCardVersions": [],
                "activeArtifactVersion": None,
                "userUploadEditModeInput": None,
                "reelComposeInput": None,
                "qplJoinId": uuid.uuid4().hex[:17],
                "sourceRemixPostId": None,
                "gkPlannerOrReasoningEnabled": True,
                "selectedModel": "BASIC_OPTION",
                "conversationMode": None,
                "selectedAgentType": "PLANNER",
                "agentSettings": None,
                "conversationStarterId": None,
                "promptType": None,
                "artifactRewriteOptions": None,
                "imagineOperationRequest": None,
                "imagineClientOptions": {"orientation": str(orientation).upper() if orientation else "VERTICAL"},
                "spaceId": None,
                "sparkSnapshotId": None,
                "topicPageId": None,
                "includeSpace": False,
                "storybookId": None,
                "messagePersistentInput": {
                    "attachment_size": attachment_metadata.get('file_size') if attachment_metadata else None,
                    "attachment_type": attachment_metadata.get('mime_type') if attachment_metadata else None,
                    "bot_message_offline_threading_id": bot_offline_threading_id,
                    "conversation_mode": None,
                    "external_conversation_id": self.external_conversation_id,
                    "is_new_conversation": new_conversation or not self.offline_threading_id,
                    "meta_ai_entry_point": entrypoint,
                    "offline_threading_id": offline_threading_id,
                    "prompt_id": None,
                    "prompt_session_id": thread_session_id,
                },
                "alakazam_enabled": True,
                "skipInFlightMessageWithParams": None,
                "__relay_internal__pv__KadabraSocialSearchEnabledrelayprovider": False,
                "__relay_internal__pv__KadabraZeitgeistEnabledrelayprovider": False,
                "__relay_internal__pv__alakazam_enabledrelayprovider": True,
                "__relay_internal__pv__sp_kadabra_survey_invitationrelayprovider": True,
                "__relay_internal__pv__enable_kadabra_partial_resultsrelayprovider": False,
                "__relay_internal__pv__AbraArtifactsEnabledrelayprovider": True,
                "__relay_internal__pv__KadabraMemoryEnabledrelayprovider": False,
                "__relay_internal__pv__AbraPlannerEnabledrelayprovider": True,
                "__relay_internal__pv__AbraWidgetsEnabledrelayprovider": False,
                "__relay_internal__pv__KadabraDeepResearchEnabledrelayprovider": False,
                "__relay_internal__pv__KadabraThinkHarderEnabledrelayprovider": False,
                "__relay_internal__pv__KadabraVergeEnabledrelayprovider": False,
                "__relay_internal__pv__KadabraSpacesEnabledrelayprovider": False,
                "__relay_internal__pv__KadabraProductSearchEnabledrelayprovider": False,
                "__relay_internal__pv__KadabraAreServiceEnabledrelayprovider": False,
                "__relay_internal__pv__kadabra_render_reasoning_response_statesrelayprovider": True,
                "__relay_internal__pv__kadabra_reasoning_cotrelayprovider": False,
                "__relay_internal__pv__AbraSearchInlineReferencesEnabledrelayprovider": True,
                "__relay_internal__pv__AbraComposedTextWidgetsrelayprovider": True,
                "__relay_internal__pv__KadabraNewCitationsEnabledrelayprovider": True,
                "__relay_internal__pv__WebPixelRatiorelayprovider": 1,
                "__relay_internal__pv__KadabraVideoDeliveryRequestrelayprovider": {
                    "dash_manifest_requests": [{}],
                    "progressive_url_requests": [{"quality": "HD"}, {"quality": "SD"}]
                },
                "__relay_internal__pv__KadabraWidgetsRedesignEnabledrelayprovider": False,
                "__relay_internal__pv__kadabra_enable_send_message_retryrelayprovider": True,
                "__relay_internal__pv__KadabraEmailCalendarIntegrationrelayprovider": False,
                "__relay_internal__pv__ClippyUIrelayprovider": False,
                "__relay_internal__pv__kadabra_reels_connect_featuresrelayprovider": False,
                "__relay_internal__pv__AbraBugNubrelayprovider": False,
                "__relay_internal__pv__AbraRedteamingrelayprovider": False,
                "__relay_internal__pv__AbraDebugDevOnlyrelayprovider": False,
                "__relay_internal__pv__kadabra_enable_open_in_editor_message_actionrelayprovider": True,
                "__relay_internal__pv__BloksDeviceContextrelayprovider": {"pixel_ratio": 1},
                "__relay_internal__pv__AbraThreadsEnabledrelayprovider": False,
                "__relay_internal__pv__kadabra_story_builder_enabledrelayprovider": False,
                "__relay_internal__pv__kadabra_imagine_canvas_enable_dev_settingsrelayprovider": False,
                "__relay_internal__pv__kadabra_create_media_deletionrelayprovider": False,
                "__relay_internal__pv__kadabra_moodboardrelayprovider": False,
                "__relay_internal__pv__AbraArtifactDragImagineFromConversationrelayprovider": True,
                "__relay_internal__pv__kadabra_media_item_renderer_heightrelayprovider": 545,
                "__relay_internal__pv__kadabra_media_item_renderer_widthrelayprovider": 620,
                "__relay_internal__pv__AbraQPDocUploadNuxTriggerNamerelayprovider": "meta_dot_ai_abra_web_doc_upload_nux_tour",
                "__relay_internal__pv__AbraSurfaceNuxIDrelayprovider": "12177",
                "__relay_internal__pv__KadabraConversationRenamingrelayprovider": True,
                "__relay_internal__pv__AbraIsLoggedOutrelayprovider": not self.is_authed,
                "__relay_internal__pv__KadabraCanvasDisplayHeaderV2relayprovider": False,
                "__relay_internal__pv__AbraArtifactEditorDebugModerelayprovider": False,
                "__relay_internal__pv__AbraArtifactEditorDownloadHTMLEnabledrelayprovider": False,
                "__relay_internal__pv__kadabra_create_row_hover_optionsrelayprovider": False,
                "__relay_internal__pv__kadabra_media_info_pillsrelayprovider": True,
                "__relay_internal__pv__KadabraConcordInternalProfileBadgeEnabledrelayprovider": False,
                "__relay_internal__pv__KadabraSocialGraphrelayprovider": True,
            }
        else:
            # Simpler Abra variables for chat
            variables = {
                "message": {"sensitive_string_value": message},
                "externalConversationId": self.external_conversation_id,
                "offlineThreadingId": offline_threading_id,
                "suggestedPromptIndex": None,
                "flashVideoRecapInput": flash_video_input,
                "flashPreviewInput": None,
                "promptPrefix": None,
                "entrypoint": entrypoint,
                "attachments": [],
                "attachmentsV2": attachments_v2,
                "messagePersistentInput": {
                    "attachment_size": attachment_metadata.get('file_size') if attachment_metadata else None,
                    "attachment_type": attachment_metadata.get('mime_type') if attachment_metadata else None,
                    "external_conversation_id": self.external_conversation_id,
                    "offline_threading_id": offline_threading_id,
                    "meta_ai_entry_point": entrypoint,
                } if media_ids else None,
                "icebreaker_type": "TEXT",
                "__relay_internal__pv__AbraDebugDevOnlyrelayprovider": False,
                "__relay_internal__pv__WebPixelRatiorelayprovider": 1,
            }
        
        payload = {
            **auth_payload,
            "fb_api_caller_class": "RelayModern",
            "fb_api_req_friendly_name": friendly_name,
            "variables": json.dumps(variables),
            "server_timestamps": "true",
            "doc_id": "24895882500088854" if is_kadabra else "7783822248314888",
        }
        payload = urllib.parse.urlencode(payload)  # noqa
        headers = {
            "content-type": "application/x-www-form-urlencoded",
            "x-fb-friendly-name": friendly_name,
        }
        # Add lsd header for authenticated requests
        if self.cookies.get("lsd"):
            headers["x-fb-lsd"] = self.cookies["lsd"]
        if self.is_authed and "abra_sess" in self.cookies:
            headers["cookie"] = f'abra_sess={self.cookies["abra_sess"]}'
            # Recreate the session to avoid cookie leakage when user is authenticated
            self.session = requests.Session()
            if self.proxy:
                self.session.proxies = self.proxy

        response = self.session.post(url, headers=headers, data=payload, stream=stream)
        
        # Check for authentication errors (expired ecto_1_sess)
        if self._check_response_for_auth_error(response):
            raise Exception("Authentication failed - please refresh cookies using auto_refresh_cookies.py or refresh_cookies.py")
        
        if not stream:
            raw_response = response.text
            last_streamed_response = self.extract_last_response(raw_response)
            if not last_streamed_response:
                return self.retry(message, stream=stream, attempts=attempts, new_conversation=new_conversation, images=images, media_ids=media_ids, attachment_metadata=attachment_metadata, is_image_generation=is_image_generation, orientation=orientation)

            extracted_data = self.extract_data(last_streamed_response)
            return extracted_data

        else:
            lines = response.iter_lines()
            is_error = json.loads(next(lines))
            if len(is_error.get("errors", [])) > 0:
                return self.retry(message, stream=stream, attempts=attempts, new_conversation=new_conversation, images=images, media_ids=media_ids, attachment_metadata=attachment_metadata, is_image_generation=is_image_generation, orientation=orientation)
            return self.stream_response(lines)

    def retry(self, message: str, stream: bool = False, attempts: int = 0, new_conversation: bool = False, images: Optional[list] = None, media_ids: Optional[list] = None, attachment_metadata: Optional[Dict[str, Any]] = None, is_image_generation: bool = False, orientation: Optional[str] = None):
        """
        Retries the prompt function if an error occurs.
        """
        if attempts <= MAX_RETRIES:
            logging.warning(
                f"Was unable to obtain a valid response from Meta AI. Retrying... Attempt {attempts + 1}/{MAX_RETRIES}."
            )
            time.sleep(3)
            return self.prompt(message, stream=stream, attempts=attempts + 1, new_conversation=new_conversation, images=images, media_ids=media_ids, attachment_metadata=attachment_metadata, is_image_generation=is_image_generation, orientation=orientation)
        else:
            raise Exception(
                "Unable to obtain a valid response from Meta AI. Try again later."
            )

    def extract_last_response(self, response: str) -> Optional[Dict]:
        """
        Extracts the last response from the Meta AI API.
        Handles both Abra and Kadabra response structures.

        Args:
            response (str): The response to extract the last response from.

        Returns:
            dict: A dictionary containing the last response.
        """
        last_streamed_response = None
        all_responses = []
        
        for line in response.split("\n"):
            try:
                json_line = json.loads(line)
            except json.JSONDecodeError:
                continue

            # Store all valid JSON responses
            all_responses.append(json_line)
            
            bot_response_message = (
                json_line.get("data", {})
                .get("node", {})
                .get("bot_response_message", {})
            )
            
            if not bot_response_message:
                # Try alternative structure for Kadabra
                bot_response_message = (
                    json_line.get("data", {})
                    .get("message", {})
                )
            
            chat_id = bot_response_message.get("id")
            if chat_id:
                try:
                    external_conversation_id, offline_threading_id, _ = chat_id.split("_")
                    self.external_conversation_id = external_conversation_id
                    self.offline_threading_id = offline_threading_id
                except:
                    pass

            streaming_state = bot_response_message.get("streaming_state")
            if streaming_state == "OVERALL_DONE":
                last_streamed_response = json_line
        
        # If no OVERALL_DONE found, use the last non-empty response
        if not last_streamed_response and all_responses:
            # Find last response with actual content
            for resp in reversed(all_responses):
                if resp.get("data", {}).get("node", {}).get("bot_response_message", {}):
                    last_streamed_response = resp
                    break
                elif resp.get("data", {}).get("message", {}):
                    # Kadabra structure
                    last_streamed_response = resp
                    break

        return last_streamed_response

    def stream_response(self, lines: Iterator[str]):
        """
        Streams the response from the Meta AI API.

        Args:
            lines (Iterator[str]): The lines to stream.

        Yields:
            dict: A dictionary containing the response message and sources.
        """
        for line in lines:
            if line:
                json_line = json.loads(line)
                extracted_data = self.extract_data(json_line)
                if not extracted_data.get("message"):
                    continue
                yield extracted_data

    def extract_data(self, json_line: dict):
        """
        Extract data and sources from a parsed JSON line.
        Handles both Abra and Kadabra response structures.

        Args:
            json_line (dict): Parsed JSON line.

        Returns:
            Tuple (str, list): Response message and list of sources.
        """
        # Try standard Abra structure first
        bot_response_message = (
            json_line.get("data", {}).get("node", {}).get("bot_response_message", {})
        )
        
        # If empty, try Kadabra structure
        if not bot_response_message:
            bot_response_message = json_line.get("data", {}).get("message", {})
        
        response = format_response(response=json_line)
        fetch_id = bot_response_message.get("fetch_id")
        sources = self.fetch_sources(fetch_id) if fetch_id else []
        medias = self.extract_media(bot_response_message)
        
        return {"message": response, "sources": sources, "media": medias}

    @staticmethod
    def extract_media(json_line: dict) -> List[Dict]:
        """
        Extract media from a parsed JSON line.
        Supports images from imagine_card and videos from various fields.

        Args:
            json_line (dict): Parsed JSON line.

        Returns:
            list: A list of dictionaries containing the extracted media.
        """
        medias = []
        
        # Extract images from content.imagine.session (has full URLs)
        # This is the primary location with complete media information
        content = json_line.get("content", {})
        imagine = content.get("imagine", {})
        session = imagine.get("session", {})
        media_sets = session.get("media_sets", [])
        
        if media_sets:
            # Found full imagine data with URIs
            for media_set in media_sets:
                imagine_media = media_set.get("imagine_media", [])
                for media in imagine_media:
                    # Try multiple possible URL fields
                    url = (media.get("uri") or 
                           media.get("image_uri") or 
                           media.get("maybe_image_uri") or
                           media.get("url"))
                    if url:  # Only add if URL is found
                        medias.append(
                            {
                                "url": url,
                                "type": media.get("media_type"),
                                "prompt": media.get("prompt"),
                            }
                        )
        else:
            # Fallback: Try imagine_card.session (may not have full URLs)
            imagine_card = json_line.get("imagine_card", {})
            if imagine_card:
                session = imagine_card.get("session", {})
                media_sets = session.get("media_sets", []) if session else []
                for media_set in media_sets:
                    imagine_media = media_set.get("imagine_media", [])
                    for media in imagine_media:
                        url = (media.get("uri") or 
                               media.get("image_uri") or 
                               media.get("maybe_image_uri") or
                               media.get("url"))
                        if url:
                            medias.append(
                                {
                                    "url": url,
                                    "type": media.get("media_type"),
                                    "prompt": media.get("prompt"),
                                }
                            )
        
        # Extract from image_attachments (may contain both images and videos)
        image_attachments = json_line.get("image_attachments", [])
        if isinstance(image_attachments, list):
            for attachment in image_attachments:
                if isinstance(attachment, dict):
                    # Check for video URLs
                    uri = attachment.get("uri") or attachment.get("url")
                    if uri:
                        media_type = "VIDEO" if ".mp4" in uri.lower() or ".m4v" in uri.lower() else "IMAGE"
                        medias.append(
                            {
                                "url": uri,
                                "type": media_type,
                                "prompt": attachment.get("prompt"),
                            }
                        )
        
        # Extract videos from video_generation field (if present)
        video_generation = json_line.get("video_generation", {})
        if isinstance(video_generation, dict):
            video_media_sets = video_generation.get("media_sets", [])
            for media_set in video_media_sets:
                video_media = media_set.get("video_media", [])
                for media in video_media:
                    uri = media.get("uri")
                    if uri:  # Only add if URI is not null
                        medias.append(
                            {
                                "url": uri,
                                "type": "VIDEO",
                                "prompt": media.get("prompt"),
                            }
                        )
        
        # Extract from direct video fields
        for possible_video_field in ["video_media", "generated_video", "reels"]:
            field_data = json_line.get(possible_video_field)
            if field_data:
                if isinstance(field_data, list):
                    for item in field_data:
                        if isinstance(item, dict) and ("uri" in item or "url" in item):
                            url = item.get("uri") or item.get("url")
                            if url:  # Only add if URL is not null
                                medias.append(
                                    {
                                        "url": url,
                                        "type": "VIDEO",
                                        "prompt": item.get("prompt"),
                                    }
                                )
        
        return medias

    def get_cookies(self) -> dict:
        """
        Extracts necessary cookies from the Meta AI main page.
        Handles challenge pages automatically.

        Returns:
            dict: A dictionary containing essential cookies.
        """
        session = HTMLSession()
        headers = {}
        fb_session = None
        if self.fb_email is not None and self.fb_password is not None:
            fb_session = get_fb_session(self.fb_email, self.fb_password)
            headers = {"cookie": f"abra_sess={fb_session['abra_sess']}"}
        
        response = session.get(
            "https://meta.ai",
            headers=headers,
        )
        
        # Check for challenge page
        challenge_url = detect_challenge_page(response.text)
        if challenge_url:
            logging.warning("⚠️  Meta AI returned a challenge page during get_cookies. Attempting to handle it...")
            cookies_dict = {}
            if fb_session:
                cookies_dict = {"abra_sess": fb_session["abra_sess"]}
            if handle_meta_ai_challenge(session, challenge_url=challenge_url, cookies_dict=cookies_dict):
                # Retry after handling challenge
                logging.info("🔄 Re-fetching cookies after challenge resolution...")
                response = session.get("https://meta.ai", headers=headers)
                # Save the rd_challenge cookie if it was extracted
                if "rd_challenge" in cookies_dict:
                    logging.info(f"[COOKIES] Saving rd_challenge: {cookies_dict['rd_challenge'][:50]}...")
            else:
                logging.error("❌ Failed to handle challenge page in get_cookies.")
        
        cookies = {
            "_js_datr": extract_value(
                response.text, start_str='_js_datr":{"value":"', end_str='",'
            ),
            "datr": extract_value(
                response.text, start_str='datr":{"value":"', end_str='",'
            ),
            "lsd": extract_value(
                response.text, start_str='"LSD",[],{"token":"', end_str='"}'
            ),
            "fb_dtsg": extract_value(
                response.text, start_str='DTSGInitData",[],{"token":"', end_str='"'
            ),
        }

        # Add rd_challenge if it was extracted from challenge handling
        if challenge_url and "rd_challenge" in cookies_dict:
            cookies["rd_challenge"] = cookies_dict["rd_challenge"]

        if len(headers) > 0 and fb_session is not None:
            cookies["abra_sess"] = fb_session["abra_sess"]
        else:
            cookies["abra_csrf"] = extract_value(
                response.text, start_str='abra_csrf":{"value":"', end_str='",'
            )
        return cookies

    def fetch_sources(self, fetch_id: str) -> List[Dict]:
        """
        Fetches sources from the Meta AI API based on the given query.

        Args:
            fetch_id (str): The fetch ID to use for the query.

        Returns:
            list: A list of dictionaries containing the fetched sources.
        """

        url = "https://graph.meta.ai/graphql?locale=user"
        payload = {
            "access_token": self.access_token,
            "fb_api_caller_class": "RelayModern",
            "fb_api_req_friendly_name": "AbraSearchPluginDialogQuery",
            "variables": json.dumps({"abraMessageFetchID": fetch_id}),
            "server_timestamps": "true",
            "doc_id": "6946734308765963",
        }

        payload = urllib.parse.urlencode(payload)  # noqa

        # Build cookie string with rd_challenge if present
        cookie_parts = [
            "dpr=2",
            f'abra_csrf={self.cookies.get("abra_csrf")}',
            f'datr={self.cookies.get("datr")}',
            "ps_n=1",
            "ps_l=1"
        ]
        if "rd_challenge" in self.cookies:
            cookie_parts.append(f'rd_challenge={self.cookies.get("rd_challenge")}')
        
        headers = {
            "authority": "graph.meta.ai",
            "accept-language": "en-US,en;q=0.9,fr-FR;q=0.8,fr;q=0.7",
            "content-type": "application/x-www-form-urlencoded",
            "cookie": "; ".join(cookie_parts),
            "x-fb-friendly-name": "AbraSearchPluginDialogQuery",
        }

        response = self.session.post(url, headers=headers, data=payload)
        response_json = response.json()
        message = response_json.get("data", {}).get("message", {})
        search_results = (
            (response_json.get("data", {}).get("message", {}).get("searchResults"))
            if message
            else None
        )
        if search_results is None:
            return []

        references = search_results["references"]
        return references

    def generate_image_new(
        self,
        prompt: str,
        orientation: str = "VERTICAL",
        num_images: int = 1,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate images using new API (based on captured network requests).
        
        Args:
            prompt: Text description of the image to generate
            orientation: Image orientation - "VERTICAL", "HORIZONTAL", or "SQUARE"
            num_images: Number of images to generate (default: 1)
            **kwargs: Additional parameters
            
        Returns:
            Dictionary with response data and extracted image URLs
            
        Example:
            >>> ai = MetaAI(cookies={"datr": "...", "abra_sess": "..."})
            >>> result = ai.generate_image_new("Astronaut in space", orientation="VERTICAL")
            >>> if result.get('success'):
            >>>     for url in result.get('image_urls', []):
            >>>         print(f"Image URL: {url}")
        """
        try:
            response = self.generation_api.generate_image(
                prompt=prompt,
                orientation=orientation,
                num_images=num_images,
                **kwargs
            )
            
            # Extract image URLs
            image_urls = response.get('images') or self.generation_api.extract_media_urls(response)
            if image_urls and isinstance(image_urls[0], dict):
                image_urls = [img.get('url') for img in image_urls if img.get('url')]
            
            return {
                "success": True,
                "prompt": prompt,
                "orientation": orientation,
                "num_images": num_images,
                "image_urls": image_urls,
                "response": response
            }
        except Exception as e:
            logging.error(f"Error generating images: {e}")
            return {
                "success": False,
                "error": str(e),
                "prompt": prompt
            }

    def generate_video_new(
        self,
        prompt: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate video using new API (based on captured network requests).
        
        Args:
            prompt: Text description of the video to generate
            **kwargs: Additional parameters
            
        Returns:
            Dictionary with response data and extracted video URLs
            
        Example:
            >>> ai = MetaAI(cookies={"datr": "...", "abra_sess": "..."})
            >>> result = ai.generate_video_new("Astronaut in space")
            >>> if result.get('success'):
            >>>     for url in result.get('video_urls', []):
            >>>         print(f"Video URL: {url}")
        """
        try:
            response = self.generation_api.generate_video(
                prompt=prompt,
                **kwargs
            )
            
            # Extract video URLs
            video_urls = response.get('videos') or self.generation_api.extract_media_urls(response)
            if video_urls and isinstance(video_urls[0], dict):
                video_urls = [vid.get('url') for vid in video_urls if vid.get('url')]
            
            return {
                "success": True,
                "prompt": prompt,
                "video_urls": video_urls,
                "response": response
            }
        except Exception as e:
            logging.error(f"Error generating video: {e}")
            return {
                "success": False,
                "error": str(e),
                "prompt": prompt
            }

    def generate_video(
        self,
        prompt: str,
        media_ids: Optional[list] = None,
        attachment_metadata: Optional[Dict[str, Any]] = None,
        orientation: Optional[str] = None,
        wait_before_poll: int = 10,
        max_attempts: int = 30,
        wait_seconds: int = 5,
        verbose: bool = True
    ) -> Dict:
        """
        DEPRECATED: Use generate_video_new() instead for better reliability.
        
        Generate a video from a text prompt using Meta AI.
        Uses cookie-based authentication.

        Args:
            prompt: Text prompt for video generation
            media_ids: Optional list of media IDs from uploaded images
            attachment_metadata: Optional dict with 'file_size' (int) and 'mime_type' (str)
            orientation: Video orientation. Valid values: "LANDSCAPE", "VERTICAL", "SQUARE". Defaults to None.
            wait_before_poll: Seconds to wait before starting to poll (default: 10)
            max_attempts: Maximum polling attempts (default: 30)
            wait_seconds: Seconds between polling attempts (default: 5)
            verbose: Whether to print status messages (default: True)

        Returns:
            Dictionary with success status, conversation_id, prompt, video_urls, and timestamp

        Example:
            ai = MetaAI(cookies={"datr": "...", "abra_sess": "..."})
            result = ai.generate_video(
                "Generate a video of a sunset",
                media_ids=["1234567890"],
                attachment_metadata={'file_size': 3310, 'mime_type': 'image/jpeg'}
            )
            if result["success"]:
                print(f"Video URLs: {result['video_urls']}")
        """
        from metaai_api.video_generation import VideoGenerator
        
        # Convert cookies dict to string format if needed
        if isinstance(self.cookies, dict):
            cookies_str = "; ".join([f"{k}={v}" for k, v in self.cookies.items() if v])
        else:
            cookies_str = str(self.cookies)
        
        # Use VideoGenerator for video generation
        video_gen = VideoGenerator(cookies_str=cookies_str)
        
        # Try to use existing conversation if we have one
        conv_id = self.external_conversation_id if hasattr(self, 'external_conversation_id') else None
        
        return video_gen.generate_video(
            prompt=prompt,
            media_ids=media_ids,
            attachment_metadata=attachment_metadata,
            orientation=orientation,
            conversation_id=conv_id,
            wait_before_poll=wait_before_poll,
            max_attempts=max_attempts,
            wait_seconds=wait_seconds,
            verbose=verbose
        )

    def upload_image(self, file_path: str) -> Dict[str, Any]:
        """
        Upload an image to Meta AI for use in conversations, image generation, or video creation.
        
        Args:
            file_path: Path to the local image file to upload
            
        Returns:
            Dictionary containing:
                - success: bool - Whether the upload succeeded
                - media_id: str - The uploaded image's media ID (use this in prompts)
                - upload_session_id: str - Unique upload session ID
                - file_name: str - Original filename
                - file_size: int - File size in bytes
                - mime_type: str - MIME type of the image
                - error: str - Error message if upload failed
                
        Example:
            >>> ai = MetaAI(cookies={"datr": "...", "abra_sess": "...", "ecto_1_sess": "..."})
            >>> result = ai.upload_image("path/to/image.jpg")
            >>> if result["success"]:
            >>>     print(f"Media ID: {result['media_id']}")
            >>>     # Use media_id in subsequent prompts for image analysis/generation
        """
        # Initialize uploader with session, cookies, and access token
        uploader = ImageUploader(self.session, self.cookies, self.access_token)
        
        # Perform upload
        result = uploader.upload_image(file_path=file_path)
        
        # Ensure we always return a dict
        if result is None:
            return {
                "success": False,
                "error": "Upload failed with no response"
            }
        
        return result


if __name__ == "__main__":
    meta = MetaAI()
    resp = meta.prompt("What was the Warriors score last game?", stream=False)
    print(resp)
