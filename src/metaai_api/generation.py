"""
Image and Video Generation API for Meta AI
Based on captured network requests from meta.ai
"""

import json
import logging
import time
import uuid
from typing import Dict, List, Optional, Any, Generator

import requests

from .html_scraper import MetaAIHTMLScraper


class GenerationAPI:
    """
    Image and Video Generation API based on Meta AI GraphQL patterns
    """
    
    ENDPOINT = "https://www.meta.ai/api/graphql"
    # ✅ UPDATED March 25, 2026 - Fresh working doc_id from browser capture
    DOC_ID = "d4e29678d29dc9703db0df437793864c"  # ✅ WORKING (March 2026) - TEXT_TO_IMAGE & TEXT_TO_VIDEO
    EXTEND_VIDEO_DOC_ID = "865d6fe804a7ea98fbce7e562b1d61ce"  # EXTEND_VIDEO mutation from HAR
    IMAGE_DOC_ID = "d4e29678d29dc9703db0df437793864c"  # ✅ Working image generation (fresh from browser)
    IMAGE_DOC_ID_ALT = "83c79c30d655e0ae6f20af0e129101e2"  # Fallback (archived)
    FETCH_CONVERSATION_DOC_ID = "9f7f4e20336400df0ea882b6131d2dd6"  # Fetch full conversation
    FETCH_MEDIA_DOC_ID = "10b7bd5aa8b7537e573e49d701a5b21b"  # Fetch video/image by media ID
    POLL_MEDIA_DOC_ID = "335a1ff137a82e22e0a9724d4bf70b6f"  # Poll individual media ID for video status
    DEFAULT_TIMEOUT = 60  # seconds - increased for image generation which can take time
    
    def __init__(self, session: Optional[requests.Session] = None, cookies: Optional[Dict] = None):
        """
        Initialize Generation API
        
        Args:
            session: Optional requests session
            cookies: Optional cookies dictionary
        """
        self.session = session or requests.Session()
        if cookies:
            self.session.cookies.update(cookies)
        
        self.logger = logging.getLogger(__name__)
        
        # Initialize HTML scraper for extracting video URLs from pages
        self.html_scraper = MetaAIHTMLScraper(self.session)
    
    def _generate_unique_id(self) -> int:
        """Generate a unique message ID (13-digit number)"""
        return int(time.time() * 1000000) % (10**13)
    
    def _default_user_agent(self) -> str:
        """Default user agent string"""
        return "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36 Edg/144.0.0.0"

    def _normalize_media_id(self, media_id: Any) -> Optional[str]:
        """Normalize media IDs and drop transient placeholders such as pending:* tokens."""
        value = str(media_id).strip()
        if not value or value.startswith("pending:"):
            return None
        return value

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
            self.logger.error("="*70)
            self.logger.error("❌ Cookie Expired: ecto_1_sess needs to be refreshed")
            self.logger.error("="*70)
            self.logger.error("Run: python auto_refresh_cookies.py")
            self.logger.error("Or:  python refresh_cookies.py")
            self.logger.error("="*70)
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
                        self.logger.error(f"❌ Authentication error: {indicator}")
                        self.logger.error("Run: python auto_refresh_cookies.py to refresh cookies")
                        return True
        except:
            pass
        
        return False

    def _normalize_orientation(self, orientation: Optional[str]) -> str:
        """Normalize orientation values to API-supported enums."""
        if not orientation:
            return "VERTICAL"

        normalized = str(orientation).upper().strip()
        if normalized == "HORIZONTAL":
            return "LANDSCAPE"

        return normalized
    
    def _build_base_variables(
        self, 
        prompt: str, 
        operation: str,
        content_prefix: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Build base variables for GraphQL request
        
        Args:
            prompt: Generation prompt
            operation: Operation type (TEXT_TO_IMAGE or TEXT_TO_VIDEO)
            content_prefix: Prefix for content ("Imagine" or "Animate")
            **kwargs: Additional parameters
            
        Returns:
            Variables dictionary
        """
        conversation_id = kwargs.get('conversation_id') or str(uuid.uuid4())
        user_message_id = str(uuid.uuid4())
        assistant_message_id = str(uuid.uuid4())
        turn_id = str(uuid.uuid4())
        prompt_session_id = kwargs.get('prompt_session_id', str(uuid.uuid4()))
        
        content = f"{content_prefix} {prompt}".strip() if content_prefix else prompt

        # Handle uploaded media attachments
        attachments_v2 = []
        media_ids = kwargs.get('media_ids')
        if media_ids:
            attachments_v2 = [str(mid) for mid in media_ids]

        # Determine operation type based on operation and media_ids presence
        is_image_to_image = operation == "TEXT_TO_IMAGE" and media_ids and len(media_ids) > 0
        is_image_to_video = operation == "TEXT_TO_VIDEO" and media_ids and len(media_ids) > 0
        is_extend_video = operation == "EXTEND_VIDEO"
        
        # Build imagineOperationRequest based on operation type
        if is_image_to_image:
            # Use imageToImageParams for image-to-image generation
            num_media = kwargs.get('num_images', 4)
            imagine_request = {
                "operation": "IMAGE_TO_IMAGE",
                "imageToImageParams": {
                    "sourceMediaEntId": str(media_ids[0]),
                    "instruction": prompt,
                    "imageSource": "USER_UPLOADED",
                    "imageUploadType": "GENAI_UPLOADED_FILE",
                    "mediaType": "UPLOADED_IMAGE",
                    "numMedia": num_media
                }
            }
        elif is_image_to_video:
            # Use imageToVideoParams for image-to-video generation
            imagine_request = {
                "operation": "IMAGE_TO_VIDEO",
                "imageToVideoParams": {
                    "sourceMediaEntId": str(media_ids[0]),
                    "prompt": prompt,
                    "numMedia": 1
                }
            }
        elif is_extend_video:
            source_media_id = kwargs.get('extend_source_media_id')
            source_media_url = kwargs.get('extend_source_media_url')
            if not source_media_id:
                raise ValueError("extend_source_media_id is required for EXTEND_VIDEO")

            imagine_request = {
                "operation": "EXTEND_VIDEO",
                "extendVideoParams": {
                    "sourceMediaEntId": str(source_media_id),
                    "sourceMediaUrl": source_media_url,
                    "numMedia": 1,
                }
            }
        else:
            # Use textToImageParams or textToVideoParams for text-based generation
            if operation == "TEXT_TO_VIDEO":
                imagine_request = {
                    "operation": operation,
                    "textToVideoParams": {
                        "prompt": prompt
                    }
                }
            else:
                imagine_request = {
                    "operation": operation,
                    "textToImageParams": {
                        "prompt": prompt
                    }
                }

        variables = {
            "conversationId": conversation_id,
            "content": content,
            "userMessageId": user_message_id,
            "assistantMessageId": assistant_message_id,
            "userUniqueMessageId": str(kwargs.get('user_unique_message_id', self._generate_unique_id())),
            "turnId": turn_id,
            "mode": None if is_extend_video else "create",
            "rewriteOptions": None,
            "attachments": None,
            "attachmentsV2": attachments_v2,
            "mentions": None,
            "clippyIp": None,
            "isNewConversation": kwargs.get('is_new_conversation', True),
            "imagineOperationRequest": imagine_request,
            "qplJoinId": None,
            "clientTimezone": kwargs.get('timezone', "UTC"),
            "developerOverridesForMessage": None,
            "clientLatitude": None,
            "clientLongitude": None,
            "devicePixelRatio": kwargs.get('device_pixel_ratio', 1.25),
            "entryPoint": kwargs.get('entry_point', None if not is_extend_video else "KADABRA__IMAGINE_UNIFIED_CANVAS"),
            "promptSessionId": prompt_session_id,
            "promptType": None,
            "conversationStarterId": None,
            "userAgent": kwargs.get('user_agent', self._default_user_agent()),
            "currentBranchPath": kwargs.get('current_branch_path', None if not is_extend_video else "2"),
            "promptEditType": "new_message",
            "userLocale": kwargs.get('locale', "en-US"),
            "userEventId": None,
            "requestedToolCall": None,
        }
        
        return variables

    def _extract_source_media_url(self, media_data: Dict[str, Any], media_id: str) -> Optional[str]:
        """Extract source media URL from a fetch_media_by_id response."""
        try:
            data = media_data.get('data', {})

            create_route = data.get('createRouteMedia', {})
            route_id = create_route.get('id')
            if not route_id or str(route_id) == str(media_id):
                candidate = create_route.get('url') or create_route.get('fallbackUrl')
                if candidate:
                    return candidate

            edges = data.get('mediaLibraryFeed', {}).get('edges', [])
            for edge in edges:
                node = edge.get('node', {})
                for video in node.get('videos', []):
                    if str(video.get('id')) == str(media_id):
                        candidate = video.get('url') or video.get('fallbackUrl')
                        if candidate:
                            return candidate
        except Exception as exc:
            self.logger.debug(f"Unable to extract source media URL for {media_id}: {exc}")

        return None
    
    def generate_image(
        self, 
        prompt: str,
        orientation: str = "VERTICAL",
        num_images: int = 1,
        fetch_urls: bool = True,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate images from text prompt
        
        Args:
            prompt: Text prompt describing the image
            orientation: Image orientation (VERTICAL, LANDSCAPE, SQUARE). HORIZONTAL is accepted as alias for LANDSCAPE.
            num_images: Number of images to generate (default: 1)
            **kwargs: Additional parameters
            
        Returns:
            Response from API
        """
        self.logger.info(f"Generating image with prompt: {prompt}")
        
        variables = self._build_base_variables(
            prompt=prompt,
            operation="TEXT_TO_IMAGE",
            content_prefix="",
            **kwargs
        )
        
        # Add image-specific parameters
        # Check if we're doing image-to-image generation
        media_ids = kwargs.get('media_ids')
        is_image_to_image = media_ids and len(media_ids) > 0
        
        if is_image_to_image:
            # For image-to-image, orientation is not in imageToImageParams
            # numMedia is already set in _build_base_variables
            self.logger.info(f"Using IMAGE_TO_IMAGE operation with source media: {media_ids[0]}")
        else:
            # For text-to-image, add orientation to textToImageParams
            variables["imagineOperationRequest"]["textToImageParams"]["orientation"] = self._normalize_orientation(orientation)
            if num_images > 1:
                self.logger.warning("num_images > 1 is not supported by this endpoint; generating a single image")
        
        payload = {
            "doc_id": self.IMAGE_DOC_ID,  # Using latest doc_id from bash-curl.json (March 2026)
            "variables": variables
        }
        
        conversation_id = variables["conversationId"]
        headers = {
            "Accept": "text/event-stream",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "en-US,en;q=0.9",
            "Baggage": "sentry-environment=production,sentry-release=9325c294e118b82669ecf8f28353672eb76d1e14,sentry-public_key=2cb2a7b32f5c43f4e020eb1ef6dfc066,sentry-trace_id=02f3fcc3375aece921c1c6289495b904,sentry-org_id=4509963614355457,sentry-sampled=false,sentry-sample_rand=0.6497181742593875,sentry-sample_rate=0.001",
            "Content-Type": "application/json",
            "Origin": "https://www.meta.ai",
            "Priority": "u=1, i",
            "Referer": "https://www.meta.ai/",
            "Sec-Ch-Prefers-Color-Scheme": "dark",
            "Sec-Ch-Ua": '"Not(A:Brand";v="8", "Chromium";v="144", "Microsoft Edge";v="144"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Windows"',
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "Sentry-Trace": "02f3fcc3375aece921c1c6289495b904-bda44fc7e92d0b23-0",
            "User-Agent": kwargs.get('user_agent', self._default_user_agent())
        }
        
        self.logger.debug(f"Image gen request - Endpoint: {self.ENDPOINT}, Sessions cookies: {list(self.session.cookies.keys())}")
        
        # Use tuple timeout (connect, read) for better control
        timeout = (10, self.DEFAULT_TIMEOUT)  # 10s to connect, DEFAULT_TIMEOUT to read
        
        response = self.session.post(
            self.ENDPOINT,
            json=payload,
            headers=headers,
            timeout=timeout
        )

        # Check for authentication errors
        if self._check_response_for_auth_error(response):
            raise Exception("Authentication failed - please refresh cookies using auto_refresh_cookies.py")

        if response.status_code == 400 and payload["doc_id"] == self.IMAGE_DOC_ID:
            self.logger.warning("Image gen returned 400; retrying with alternate image doc_id")
            payload["doc_id"] = self.IMAGE_DOC_ID_ALT
            response = self.session.post(
                self.ENDPOINT,
                json=payload,
                headers=headers,
                timeout=timeout
            )

        self.logger.info(f"Image gen response - Status: {response.status_code}, Length: {len(response.text)}, Content-Type: {response.headers.get('Content-Type', 'N/A')}")

        if response.status_code >= 400:
            self.logger.error("Image gen failed: %s", response.text[:500])
            response.raise_for_status()

        response.raise_for_status()
        result = self._parse_response(response)

        # Check if we already have image URLs from the SSE stream
        has_urls = result.get('images') and len(result.get('images', [])) > 0
        
        if fetch_urls and result.get('image_objects'):
            image_ids = [img.get('id') for img in result['image_objects'] if img.get('id')]
            conversation_id = result.get('conversation_id')

            if has_urls:
                self.logger.info(f"✅ {len(result['images'])} image URLs already available from SSE stream - skipping polling")
            elif image_ids:
                self.logger.info(f"⏳ No URLs in SSE stream - fetching URLs for {len(image_ids)} images via polling...")

                # Increased to 30 attempts (~90s total) for better reliability
                max_attempts = kwargs.pop('max_attempts', 30)
                wait_seconds = kwargs.pop('wait_seconds', 3)

                images = self.fetch_image_urls_by_media_id(
                    image_ids=image_ids,
                    conversation_id=conversation_id,
                    max_attempts=max_attempts,
                    wait_seconds=wait_seconds
                )

                if images:
                    result['image_objects'] = images
                    result['images'] = [img.get('url') for img in images if isinstance(img, dict) and img.get('url')]
                    self.logger.info(f"Successfully fetched {len(result['images'])} image URLs")
                else:
                    self.logger.warning("No image URLs retrieved - images may still be processing")
            else:
                self.logger.warning("No image IDs found in generation response")

        return result
    
    def generate_video(
        self, 
        prompt: str,
        fetch_urls: bool = True,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate video from text prompt
        
        Args:
            prompt: Text prompt describing the video
            fetch_urls: If True, automatically fetch video URLs after generation (default: True)
            **kwargs: Additional parameters
            
        Returns:
            Response from API with video data and URLs (if fetch_urls=True)
        """
        self.logger.info(f"Generating video with prompt: {prompt}")
        
        variables = self._build_base_variables(
            prompt=prompt,
            operation="TEXT_TO_VIDEO",
            content_prefix="Animate",
            **kwargs
        )
        
        payload = {
            "doc_id": self.DOC_ID,
            "variables": variables
        }
        
        conversation_id = variables["conversationId"]
        headers = {
            "Accept": "text/event-stream",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "en-US,en;q=0.9",
            "Baggage": "sentry-environment=production,sentry-release=9325c294e118b82669ecf8f28353672eb76d1e14,sentry-public_key=2cb2a7b32f5c43f4e020eb1ef6dfc066,sentry-trace_id=02f3fcc3375aece921c1c6289495b904,sentry-org_id=4509963614355457,sentry-sampled=false,sentry-sample_rand=0.6497181742593875,sentry-sample_rate=0.001",
            "Content-Type": "application/json",
            "Origin": "https://www.meta.ai",
            "Priority": "u=1, i",
            "Referer": "https://www.meta.ai/",
            "Sec-Ch-Prefers-Color-Scheme": "dark",
            "Sec-Ch-Ua": '"Not(A:Brand";v="8", "Chromium";v="144", "Microsoft Edge";v="144"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Windows"',
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "Sentry-Trace": "02f3fcc3375aece921c1c6289495b904-bda44fc7e92d0b23-0",
            "User-Agent": kwargs.get('user_agent', self._default_user_agent())
        }
        
        self.logger.debug(f"Video gen request - Endpoint: {self.ENDPOINT}, Sessions cookies: {list(self.session.cookies.keys())}")
        
        # Use tuple timeout (connect, read) for better control
        timeout = (10, self.DEFAULT_TIMEOUT)  # 10s to connect, DEFAULT_TIMEOUT to read
        
        response = self.session.post(
            self.ENDPOINT,
            json=payload,
            headers=headers,
            timeout=timeout
        )
        
        # Check for authentication errors
        if self._check_response_for_auth_error(response):
            raise Exception("Authentication failed - please refresh cookies using auto_refresh_cookies.py")
        
        self.logger.info(f"Video gen response - Status: {response.status_code}, Length: {len(response.text)}, Content-Type: {response.headers.get('Content-Type', 'N/A')}")
        
        response.raise_for_status()
        result = self._parse_response(response)
        
        if result.get('video_objects'):
            # Preserve media IDs so callers can reuse them for later extend-video flows
            video_ids = [v['id'] for v in result['video_objects'] if 'id' in v]
            if video_ids:
                result['media_ids'] = video_ids

        # If fetch_urls is enabled and we have video IDs, fetch video URLs
        if fetch_urls and result.get('video_objects'):
            # Extract video IDs from video_objects
            video_ids = [v['id'] for v in result['video_objects'] if 'id' in v]
            conversation_id = result.get('conversation_id')
            
            if video_ids:
                self.logger.info(f"Fetching URLs for {len(video_ids)} videos...")
                
                # Extract max_attempts and wait_seconds from kwargs if present
                # Increased to 24 attempts (120s total) to accommodate 50-60s video generation times
                max_attempts = kwargs.pop('max_attempts', 24)
                wait_seconds = kwargs.pop('wait_seconds', 5)
                
                # Fetch video URLs using media ID approach
                videos = self.fetch_video_urls_by_media_id(
                    video_ids=video_ids,
                    conversation_id=conversation_id,
                    max_attempts=max_attempts,
                    wait_seconds=wait_seconds
                )
                
                # Add fetched videos to result
                if videos:
                    result['videos'] = videos
                    self.logger.info(f"Successfully fetched {len(videos)} video URLs")
                else:
                    self.logger.warning("No video URLs retrieved - videos may still be processing")
            else:
                self.logger.warning("No video IDs found in generation response")
        
        return result

    def extend_video(
        self,
        media_id: str,
        source_media_url: Optional[str] = None,
        conversation_id: Optional[str] = None,
        fetch_urls: bool = True,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Extend an existing generated video using source media ID.

        Args:
            media_id: Source media ID to extend
            source_media_url: Optional source media URL (auto-resolved when omitted)
            conversation_id: Optional existing conversation ID
            fetch_urls: If True, fetch final extended video URLs
            **kwargs: Additional request options

        Returns:
            Parsed response dictionary with media_ids and videos when available
        """
        if not media_id:
            raise ValueError("media_id is required")

        self.logger.info(f"Extending video for media_id: {media_id}")

        # Resolve source URL when not provided
        resolved_source_url = source_media_url
        if not resolved_source_url:
            media_data = self.fetch_media_by_id(media_id, conversation_id=conversation_id)
            resolved_source_url = self._extract_source_media_url(media_data, media_id)

        variables = self._build_base_variables(
            prompt="Extend",
            operation="EXTEND_VIDEO",
            content_prefix="",
            conversation_id=conversation_id or str(uuid.uuid4()),
            is_new_conversation=False,
            extend_source_media_id=media_id,
            extend_source_media_url=resolved_source_url,
            entry_point=kwargs.get('entry_point', "KADABRA__IMAGINE_UNIFIED_CANVAS"),
            current_branch_path=kwargs.get('current_branch_path', "2"),
            **kwargs
        )

        payload = {
            "doc_id": self.EXTEND_VIDEO_DOC_ID,
            "variables": variables,
        }

        headers = {
            "Accept": "text/event-stream",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "en-US,en;q=0.9",
            "Content-Type": "application/json",
            "Origin": "https://www.meta.ai",
            "Priority": "u=1, i",
            "Referer": f"https://www.meta.ai/create/{media_id}",
            "Sec-Ch-Prefers-Color-Scheme": "dark",
            "Sec-Ch-Ua": '"Not(A:Brand";v="8", "Chromium";v="144", "Microsoft Edge";v="144"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Windows"',
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "User-Agent": kwargs.get('user_agent', self._default_user_agent()),
        }

        timeout = (10, self.DEFAULT_TIMEOUT)
        response = self.session.post(
            self.ENDPOINT,
            json=payload,
            headers=headers,
            timeout=timeout,
        )

        if self._check_response_for_auth_error(response):
            raise Exception("Authentication failed - please refresh cookies using auto_refresh_cookies.py")

        response.raise_for_status()
        result = self._parse_response(response)

        # Keep source context for callers
        result['source_media_id'] = str(media_id)
        result['source_media_url'] = resolved_source_url

        media_ids = []
        for video in result.get('video_objects', []):
            vid = self._normalize_media_id(video.get('id'))
            if vid and vid not in media_ids:
                media_ids.append(vid)

        if not media_ids:
            extracted_ids = []
            for mid in self._extract_media_ids_from_response(result):
                normalized = self._normalize_media_id(mid)
                if normalized and normalized not in extracted_ids:
                    extracted_ids.append(normalized)
            media_ids = extracted_ids

        result['media_ids'] = media_ids

        if fetch_urls and media_ids:
            max_attempts = kwargs.pop('max_attempts', 24)
            wait_seconds = kwargs.pop('wait_seconds', 5)
            videos = self.fetch_video_urls_by_media_id(
                video_ids=media_ids,
                conversation_id=result.get('conversation_id') or conversation_id,
                max_attempts=max_attempts,
                wait_seconds=wait_seconds,
            )
            if videos:
                result['videos'] = videos

        return result
    
    def _parse_response(self, response: requests.Response) -> Dict[str, Any]:
        """
        Parse response from Meta AI API
        
        Args:
            response: Response object
            
        Returns:
            Parsed response data
        """
        # Log response details for debugging
        self.logger.debug(f"Response Status Code: {response.status_code}")
        self.logger.debug(f"Response Headers: {response.headers}")
        self.logger.debug(f"Response Length: {len(response.text)}")
        
        # Handle empty responses
        if not response.text or response.status_code >= 400:
            error_msg = f"API returned status {response.status_code}"
            if not response.text:
                error_msg += ": Empty response body"
            else:
                error_msg += f": {response.text[:200]}"
            self.logger.warning(error_msg)
            return {"error": error_msg, "status_code": response.status_code}
        
        content_type = response.headers.get('Content-Type', '')
        
        if 'multipart/mixed' in content_type:
            return self._parse_multipart_response(response)
        elif 'text/event-stream' in content_type:
            return self._parse_sse_response(response)
        else:
            try:
                return response.json()
            except Exception as e:
                self.logger.error(f"Failed to parse JSON response: {e}")
                self.logger.debug(f"Response text: {response.text[:500]}")
                return {"error": f"JSON parse failed: {str(e)}", "raw_response": response.text[:500]}
    
    def _parse_multipart_response(self, response: requests.Response) -> Dict[str, Any]:
        """
        Parse multipart/mixed response
        
        Args:
            response: Response object
            
        Returns:
            Parsed data
        """
        # Extract boundary from content-type
        content_type = response.headers.get('Content-Type', '')
        boundary = None
        
        if 'boundary=' in content_type:
            boundary = content_type.split('boundary=')[1].split(';')[0].strip()
        
        if not boundary:
            return response.json()
        
        # Split response by boundary
        parts = response.text.split(f'--{boundary}')
        
        result = {
            'parts': [],
            'data': None
        }
        
        for part in parts:
            if not part.strip() or part.strip() == '--':
                continue
            
            # Try to extract JSON from this part
            if 'Content-Type: application/json' in part or '{' in part:
                try:
                    # Find JSON content
                    json_start = part.find('{')
                    if json_start != -1:
                        json_str = part[json_start:].strip()
                        parsed = json.loads(json_str)
                        result['parts'].append(parsed)
                        
                        # Keep first valid data
                        if result['data'] is None and parsed.get('data'):
                            result['data'] = parsed
                except json.JSONDecodeError:
                    continue
        
        return result if result['data'] else response.json()
    
    def _parse_sse_response(self, response: requests.Response) -> Dict[str, Any]:
        """
        Parse Server-Sent Events (SSE) response for streaming image/video generation
        
        Args:
            response: Response object with text/event-stream content
            
        Returns:
            Parsed response with images/videos, conversation_id, and streaming state
        """
        result = {
            "status_code": response.status_code,
            "streaming_state": None,
            "images": [],
            "videos": [],
            "image_objects": [],
            "video_objects": [],  # Full video objects with IDs and sourceMedia
            "conversation_id": None,
            "message": None,
            "events": []
        }
        
        try:
            lines = response.text.split('\n')
            current_event = None
            event_count = 0
            
            for line in lines:
                line = line.strip()
                
                if not line:
                    continue
                
                if line.startswith('event:'):
                    current_event = line.split(':', 1)[1].strip()
                    event_count += 1
                    continue
                
                if line.startswith('data:'):
                    data_str = line.split(':', 1)[1].strip()
                    try:
                        data = json.loads(data_str)
                        result['events'].append(data)
                        
                        # Extract main message data
                        if 'data' in data and 'sendMessageStream' in data['data']:
                            msg = data['data']['sendMessageStream']
                            result['streaming_state'] = msg.get('streamingState', 'UNKNOWN')
                            
                            # Extract conversation ID
                            if msg.get('conversationId') and not result['conversation_id']:
                                result['conversation_id'] = msg['conversationId']
                            
                            # Extract images (now with better logging)
                            if 'images' in msg and msg['images']:
                                for img in msg['images']:
                                    img_url = img.get('url')
                                    img_id = img.get('id', 'unknown')
                                    
                                    if img_url:
                                        if img_url not in result['images']:
                                            result['images'].append(img_url)
                                            self.logger.debug(f"Found image URL in SSE event {event_count} for ID {img_id}: {img_url[:80]}...")
                                    else:
                                        self.logger.debug(f"Image in SSE event {event_count} has null URL (ID: {img_id}) - still processing")

                                    if img not in result['image_objects']:
                                        result['image_objects'].append(img)
                            
                            # Extract videos (URLs and full objects)
                            if 'videos' in msg and msg['videos']:
                                for vid in msg['videos']:
                                    vid_url = vid.get('url')
                                    vid_id = vid.get('id')
                                    
                                    # Store video URL if present
                                    if vid_url and vid_url not in result['videos']:
                                        result['videos'].append(vid_url)
                                    
                                    # Store full video object (includes ID, sourceMedia, etc.)
                                    if vid not in result['video_objects']:
                                        result['video_objects'].append(vid)
                            
                            # Extract message text
                            if 'message' in msg:
                                result['message'] = msg['message']
                    
                    except json.JSONDecodeError as e:
                        self.logger.debug(f"Could not parse SSE data line: {data_str[:100]}")
                        continue
            
            self.logger.info(f"SSE parse complete - Events: {event_count}, State: {result['streaming_state']}, Images: {len(result['images'])} URLs found, Image Objects: {len(result['image_objects'])}, Videos: {len(result['videos'])}, Conv ID: {result['conversation_id']}")
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to parse SSE response: {e}")
            return {
                "error": f"SSE parse failed: {str(e)}",
                "raw_response": response.text[:500],
                "status_code": response.status_code
            }
    
    def fetch_conversation(
        self,
        conversation_id: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Fetch conversation by ID to retrieve populated video/image URLs
        
        This is used after video generation to get the actual video URLs, which are
        null in the initial SSE stream but populated after video processing completes.
        
        Args:
            conversation_id: Conversation ID from initial generation
            **kwargs: Additional parameters
            
        Returns:
            Response from API with conversation data including video URLs
        """
        self.logger.info(f"Fetching conversation: {conversation_id}")
        
        payload = {
            "doc_id": self.FETCH_CONVERSATION_DOC_ID,
            "variables": {
                "id": conversation_id,
                "artifactId": None,
                "includeArtifact": False,
                "includeMessageList": True  # Must be True to get messages with video IDs
            }
        }
        
        headers = {
            "Accept": "multipart/mixed, application/json",
            "Accept-Encoding": "gzip, deflate",
            "Accept-Language": "en-US,en;q=0.9",
            "Baggage": "sentry-environment=production,sentry-release=9325c294e118b82669ecf8f28353672eb76d1e14,sentry-public_key=2cb2a7b32f5c43f4e020eb1ef6dfc066,sentry-trace_id=02f3fcc3375aece921c1c6289495b904,sentry-org_id=4509963614355457,sentry-sampled=false,sentry-sample_rand=0.6497181742593875,sentry-sample_rate=0.001",
            "Content-Type": "application/json",
            "Origin": "https://www.meta.ai",
            "Priority": "u=1, i",
            "Referer": "https://www.meta.ai/",
            "Sec-Ch-Prefers-Color-Scheme": "dark",
            "Sec-Ch-Ua": '"Not(A:Brand";v="8", "Chromium";v="144", "Microsoft Edge";v="144"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Windows"',
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "Sentry-Trace": "02f3fcc3375aece921c1c6289495b904-b496b9aa50a6f452-0",
            "User-Agent": kwargs.get('user_agent', self._default_user_agent())
        }
        
        try:
            # Use tuple timeout (connect, read) for better control
            timeout = (10, self.DEFAULT_TIMEOUT)
            response = self.session.post(
                self.ENDPOINT,
                json=payload,
                headers=headers,
                timeout=timeout
            )
            response.raise_for_status()
            
            # Parse JSON response
            data = response.json()
            self.logger.debug(f"Fetch conversation response: {len(str(data))} chars")
            return data
            
        except Exception as e:
            self.logger.error(f"Error fetching conversation: {e}")
            return {"error": str(e)}
    
    def fetch_media_by_id(
        self,
        media_id: str,
        conversation_id: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Fetch media (video/image) by ID to get the actual URL.
        
        This query returns:
        - data.createRouteMedia: The specific media item queried
        - data.mediaLibraryFeed: A feed of all recent media items
        
        Args:
            media_id: The media ID from initial generation (e.g., "920162721188016")
            conversation_id: Optional conversation ID for referer header
            **kwargs: Additional parameters
            
        Returns:
            Response with media data including URL
        """
        self.logger.info(f"Fetching media by ID: {media_id}")
        
        payload = {
            "doc_id": self.FETCH_MEDIA_DOC_ID,
            "variables": {
                "mediaId": media_id,
                "mediaIdIsNull": False,
                "first": 10,
                "after": None
            }
        }
        
        # Build referer with conversation ID if available
        referer = f"https://www.meta.ai/prompt/{conversation_id}" if conversation_id else "https://www.meta.ai/"
        
        headers = {
            "Accept": "multipart/mixed, application/json",
            "Accept-Encoding": "gzip, deflate",
            "Accept-Language": "en-US,en;q=0.9",
            "Baggage": "sentry-environment=production,sentry-release=9325c294e118b82669ecf8f28353672eb76d1e14,sentry-public_key=2cb2a7b32f5c43f4e020eb1ef6dfc066,sentry-trace_id=02f3fcc3375aece921c1c6289495b904,sentry-org_id=4509963614355457,sentry-sampled=false,sentry-sample_rand=0.6497181742593875,sentry-sample_rate=0.001",
            "Content-Type": "application/json",
            "Origin": "https://www.meta.ai",
            "Priority": "u=1, i",
            "Referer": referer,
            "Sec-Ch-Prefers-Color-Scheme": "dark",
            "Sec-Ch-Ua": '"Not(A:Brand";v="8", "Chromium";v="144", "Microsoft Edge";v="144"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Windows"',
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "Sentry-Trace": "02f3fcc3375aece921c1c6289495b904-ba2efbf2c86f8840-0",
            "User-Agent": self._default_user_agent()
        }
        
        try:
            # Use tuple timeout (connect, read) for better control
            timeout = (10, self.DEFAULT_TIMEOUT)
            response = self.session.post(
                "https://www.meta.ai/api/graphql",
                json=payload,
                headers=headers,
                timeout=timeout
            )
            response.raise_for_status()
            
            # Try to parse JSON
            try:
                data = response.json()
                self.logger.debug(f"Fetch media response: {len(str(data))} chars")
                return data
            except json.JSONDecodeError:
                # Fallback: try multipart/mixed parsing
                text = response.text
                parts = text.split("\r\n\r\n")
                for part in parts:
                    part = part.strip()
                    if part.startswith("{") and part.endswith("}"):
                        try:
                            data = json.loads(part)
                            self.logger.debug("Fetch media response parsed from multipart")
                            return data
                        except json.JSONDecodeError:
                            continue

                self.logger.error("Failed to parse media response as JSON or multipart")
                return {
                    "error": "JSON decode failed and no JSON part found",
                    "response_text": text[:500],
                    "status_code": response.status_code
                }
            
        except Exception as e:
            self.logger.error(f"Error fetching media by ID: {e}")
            return {"error": str(e)}
    
    def fetch_video_urls_by_media_id(
        self,
        video_ids: List[str],
        conversation_id: Optional[str] = None,
        max_attempts: int = 24,
        wait_seconds: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Fetch video URLs using media IDs with retry logic.
        
        Makes a single request using any video ID, which returns a mediaLibraryFeed
        containing all recent videos with their URLs.
        
        Args:
            video_ids: List of video IDs from generation
            conversation_id: Optional conversation ID for proper headers
            max_attempts: Maximum polling attempts (default: 24 = ~120s)
            wait_seconds: Base seconds between attempts (adaptive polling: 3s initially, 5s later)
            
        Returns:
            List of video dictionaries with URLs, IDs, thumbnails, etc.
        """
        if not video_ids:
            return []
        
        requested_ids = []
        for raw_id in video_ids:
            normalized = self._normalize_media_id(raw_id)
            if normalized and normalized not in requested_ids:
                requested_ids.append(normalized)

        if not requested_ids:
            self.logger.info("No resolved media IDs available yet (only pending placeholders)")
            return []

        self.logger.info(f"Fetching video URLs for {len(requested_ids)} videos (max {max_attempts} attempts)")
        
        videos = []  # Initialize to prevent unbound variable error
        for attempt in range(1, max_attempts + 1):
            try:
                # Use the first video ID to fetch media (response includes all recent media)
                data = self.fetch_media_by_id(requested_ids[0], conversation_id=conversation_id)
                
                if 'error' in data:
                    self.logger.warning(f"Attempt {attempt}/{max_attempts}: {data['error']}")
                    if attempt < max_attempts:
                        # Adaptive polling: faster for first 10 attempts (30s), then slower
                        adaptive_wait = 3 if attempt <= 10 else wait_seconds
                        time.sleep(adaptive_wait)
                    continue
                
                # Extract videos from createRouteMedia and mediaLibraryFeed
                videos = []
                seen_ids = set()
                create_route_media = data.get('data', {}).get('createRouteMedia', {})
                if create_route_media:
                    route_id = self._normalize_media_id(create_route_media.get('id'))
                    route_url = create_route_media.get('url') or create_route_media.get('fallbackUrl')
                    source_media = create_route_media.get('sourceMedia')
                    source_image_url = source_media.get('url') if isinstance(source_media, dict) else None
                    if route_id in requested_ids and route_url and route_id not in seen_ids:
                        videos.append({
                            'id': route_id,
                            'url': route_url,
                            'thumbnail': create_route_media.get('thumbnail'),
                            'prompt': create_route_media.get('prompt'),
                            'width': create_route_media.get('width'),
                            'height': create_route_media.get('height'),
                            'orientation': create_route_media.get('orientation'),
                            'fallbackUrl': create_route_media.get('fallbackUrl'),
                            'downloadableFileName': create_route_media.get('downloadableFileName'),
                            'source_image_url': source_image_url
                        })
                        seen_ids.add(route_id)
                media_feed = data.get('data', {}).get('mediaLibraryFeed', {})
                edges = media_feed.get('edges', [])
                
                for edge in edges:
                    node = edge.get('node', {})
                    node_videos = node.get('videos', [])
                    
                    for video in node_videos:
                        video_id = self._normalize_media_id(video.get('id'))
                        video_url = video.get('url')
                        
                        # Check if this is one of our requested videos and has a URL
                        if video_id in requested_ids and video_url and video_id not in seen_ids:
                            source_media = video.get('sourceMedia')
                            source_image_url = source_media.get('url') if isinstance(source_media, dict) else None
                            videos.append({
                                'id': video_id,
                                'url': video_url,
                                'thumbnail': video.get('thumbnail'),
                                'prompt': video.get('prompt'),
                                'width': video.get('width'),
                                'height': video.get('height'),
                                'orientation': video.get('orientation'),
                                'fallbackUrl': video.get('fallbackUrl'),
                                'downloadableFileName': video.get('downloadableFileName'),
                                'source_image_url': source_image_url
                            })
                            seen_ids.add(video_id)
                
                # Check if we found all videos with URLs
                videos_found = len(videos)
                videos_requested = len(requested_ids)
                
                if videos_found == videos_requested:
                    self.logger.info(f"Found all {videos_found} videos with URLs on attempt {attempt}")
                    return videos
                elif videos_found > 0:
                    self.logger.info(f"Found {videos_found}/{videos_requested} videos on attempt {attempt}")
                else:
                    self.logger.info(f"Attempt {attempt}/{max_attempts}: Videos not ready yet")
                
                if attempt < max_attempts:
                    # Adaptive polling: faster for first 10 attempts (30s), then slower
                    adaptive_wait = 3 if attempt <= 10 else wait_seconds
                    self.logger.info(f"Waiting {adaptive_wait}s before retry...")
                    time.sleep(adaptive_wait)
                
            except Exception as e:
                self.logger.warning(f"Attempt {attempt}/{max_attempts} failed: {e}")
                if attempt < max_attempts:
                    # Adaptive polling: faster for first 10 attempts (30s), then slower
                    adaptive_wait = 3 if attempt <= 10 else wait_seconds
                    time.sleep(adaptive_wait)
        
        if videos:
            self.logger.info(
                f"Returning partial video URLs ({len(videos)}/{len(requested_ids)}) after {max_attempts} attempts"
            )
        else:
            self.logger.warning(f"Video URLs not available after {max_attempts} attempts")
        return videos if 'videos' in locals() else []

    def fetch_image_urls_by_media_id(
        self,
        image_ids: List[str],
        conversation_id: Optional[str] = None,
        max_attempts: int = 30,
        wait_seconds: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Fetch image URLs using media IDs with retry logic.

        Makes a single request using any image ID, which returns a mediaLibraryFeed
        containing all recent images with their URLs.

        Args:
            image_ids: List of image IDs from generation
            conversation_id: Optional conversation ID for proper headers
            max_attempts: Maximum polling attempts (default: 30 = ~90s with adaptive backoff)
            wait_seconds: Base seconds between attempts (adaptive: 2s → 3s → 4.5s)

        Returns:
            List of image dictionaries with URLs, IDs, thumbnails, etc.
        """
        if not image_ids:
            return []

        self.logger.info(f"Fetching image URLs for {len(image_ids)} images (max {max_attempts} attempts, {wait_seconds}s interval)")

        images = []  # Initialize to prevent unbound variable error
        for attempt in range(1, max_attempts + 1):
            try:
                data = self.fetch_media_by_id(image_ids[0], conversation_id=conversation_id)
                if not isinstance(data, dict):
                    self.logger.warning("Attempt %s/%s: media response is not a dict", attempt, max_attempts)
                    if attempt < max_attempts:
                        # Adaptive: 2s (fast) → 3s (medium) → 4.5s (slower)
                        delay = 2 if attempt <= 8 else (3 if attempt <= 18 else 4.5)
                        time.sleep(delay)
                    continue

                if 'error' in data:
                    self.logger.warning(f"Attempt {attempt}/{max_attempts}: {data['error']}")
                    if attempt < max_attempts:
                        # Adaptive: 2s (fast) → 3s (medium) → 4.5s (slower)
                        delay = 2 if attempt <= 8 else (3 if attempt <= 18 else 4.5)
                        time.sleep(delay)
                    continue

                images = []
                seen_ids = set()
                data_root = data.get('data') or {}
                if not isinstance(data_root, dict):
                    self.logger.warning("Attempt %s/%s: media response missing data field", attempt, max_attempts)
                    if attempt < max_attempts:
                        # Adaptive: 2s (fast) → 3s (medium) → 4.5s (slower)
                        delay = 2 if attempt <= 8 else (3 if attempt <= 18 else 4.5)
                        time.sleep(delay)
                    continue

                create_route_media = data_root.get('createRouteMedia')
                if not isinstance(create_route_media, dict):
                    create_route_media = {}
                if create_route_media:
                    route_id = create_route_media.get('id')
                    route_url = create_route_media.get('url') or create_route_media.get('fallbackUrl')
                    source_media = create_route_media.get('sourceMedia')
                    source_image_url = source_media.get('url') if isinstance(source_media, dict) else None
                    if route_id in image_ids and route_url and route_id not in seen_ids:
                        images.append({
                            'id': route_id,
                            'url': route_url,
                            'thumbnail': create_route_media.get('thumbnail'),
                            'prompt': create_route_media.get('prompt'),
                            'width': create_route_media.get('width'),
                            'height': create_route_media.get('height'),
                            'orientation': create_route_media.get('orientation'),
                            'fallbackUrl': create_route_media.get('fallbackUrl'),
                            'downloadableFileName': create_route_media.get('downloadableFileName'),
                            'source_image_url': source_image_url
                        })
                        seen_ids.add(route_id)

                media_feed = data_root.get('mediaLibraryFeed')
                if not isinstance(media_feed, dict):
                    media_feed = {}
                edges = media_feed.get('edges', [])
                if not isinstance(edges, list):
                    edges = []
                for edge in edges:
                    if not isinstance(edge, dict):
                        continue
                    node = edge.get('node') or {}
                    if not isinstance(node, dict):
                        continue
                    node_images = node.get('images', [])
                    if not isinstance(node_images, list):
                        continue

                    for image in node_images:
                        if not isinstance(image, dict):
                            continue
                        image_id = image.get('id')
                        image_url = image.get('url')
                        source_media = image.get('sourceMedia')
                        source_image_url = source_media.get('url') if isinstance(source_media, dict) else None

                        if image_id in image_ids and image_url and image_id not in seen_ids:
                            images.append({
                                'id': image_id,
                                'url': image_url,
                                'thumbnail': image.get('thumbnail'),
                                'prompt': image.get('prompt'),
                                'width': image.get('width'),
                                'height': image.get('height'),
                                'orientation': image.get('orientation'),
                                'fallbackUrl': image.get('fallbackUrl'),
                                'downloadableFileName': image.get('downloadableFileName'),
                                'source_image_url': source_image_url
                            })
                            seen_ids.add(image_id)

                images_found = len(images)
                images_requested = len(image_ids)

                if images_found == images_requested:
                    self.logger.info(f"Found all {images_found} images with URLs on attempt {attempt}")
                    return images
                elif images_found > 0:
                    self.logger.info(f"Found {images_found}/{images_requested} images on attempt {attempt}")
                else:
                    self.logger.info(f"Attempt {attempt}/{max_attempts}: Images not ready yet")

                if attempt < max_attempts:
                    # Adaptive polling: 2s (fast) → 3s (medium) → 4.5s (slower)
                    delay = 2 if attempt <= 8 else (3 if attempt <= 18 else 4.5)
                    self.logger.info(f"Waiting {delay:.1f}s before retry...")
                    time.sleep(delay)

            except Exception as e:
                self.logger.warning(f"Attempt {attempt}/{max_attempts} failed: {e}")
                if attempt < max_attempts:
                    # Adaptive polling: 2s (fast) → 3s (medium) → 4.5s (slower)
                    delay = 2 if attempt <= 8 else (3 if attempt <= 18 else 4.5)
                    time.sleep(delay)

        images_found = len(images) if 'images' in locals() else 0
        if images_found > 0:
            self.logger.warning(f"Only {images_found}/{len(image_ids)} image URLs available after {max_attempts} attempts")
        else:
            self.logger.warning(f"No image URLs available after {max_attempts} attempts (~{max_attempts * wait_seconds}s). Images may still be processing.")
        return images if 'images' in locals() else []
    
    def fetch_video_urls(
        self,
        conversation_id: str,
        max_attempts: int = 20,
        wait_seconds: int = 2,
        **kwargs
    ) -> List[str]:
        """
        Fetch video URLs from conversation with retry logic
        
        Videos may take 20-60 seconds to process after initial generation.
        This method polls the conversation until video URLs are populated.
        
        Args:
            conversation_id: Conversation ID from video generation
            max_attempts: Maximum polling attempts (default: 20 = ~40s)
            wait_seconds: Seconds between attempts (default: 2)
            **kwargs: Additional parameters
            
        Returns:
            List of video URLs (may be empty if videos still processing)
        """
        self.logger.info(f"Fetching video URLs for conversation {conversation_id} (max {max_attempts} attempts)")
        
        for attempt in range(max_attempts):
            try:
                conv_data = self.fetch_conversation(conversation_id, **kwargs)
                
                if 'error' in conv_data:
                    self.logger.warning(f"Attempt {attempt + 1}/{max_attempts}: Error fetching conversation: {conv_data['error']}")
                    delay = min(wait_seconds * (1 if attempt <= 5 else 1.5 if attempt <= 12 else 2), 5)
                    time.sleep(delay)
                    continue
                
                # Extract video URLs from conversation
                videos = self._extract_videos_from_conversation(conv_data)
                
                if videos:
                    self.logger.info(f"Found {len(videos)} video URLs on attempt {attempt + 1}")
                    return videos
                
                delay = min(wait_seconds * (1 if attempt <= 5 else 1.5 if attempt <= 12 else 2), 5)
                self.logger.info(f"Attempt {attempt + 1}/{max_attempts}: Videos not ready yet, waiting {delay:.1f}s...")
                time.sleep(delay)
                
            except Exception as e:
                self.logger.warning(f"Attempt {attempt + 1}/{max_attempts} failed: {e}")
                if attempt < max_attempts - 1:
                    delay = min(wait_seconds * (1 if attempt <= 5 else 1.5 if attempt <= 12 else 2), 5)
                    time.sleep(delay)
        
        self.logger.warning(f"Video URLs not available after {max_attempts} attempts")
        return []
    
    def _extract_videos_from_conversation(self, conv_data: Dict[str, Any]) -> List[str]:
        """
        Extract video URLs from conversation response
        
        Args:
            conv_data: Conversation data from fetch_conversation
            
        Returns:
            List of video URLs
        """
        video_urls = []
        
        try:
            # Navigate to conversation messages
            conversation = conv_data.get('data', {}).get('conversation', {})
            messages = conversation.get('messages', {}).get('edges', [])
            
            for edge in messages:
                node = edge.get('node', {})
                
                # Check if this is an assistant message with videos
                if node.get('__typename') == 'AssistantMessage':
                    videos = node.get('videos', [])
                    
                    for video in videos:
                        url = video.get('url')
                        if url and url not in video_urls:
                            video_urls.append(url)
            
            self.logger.debug(f"Extracted {len(video_urls)} video URLs from conversation")
            
        except Exception as e:
            self.logger.warning(f"Error extracting videos from conversation: {e}")
        
        return video_urls
    
    def poll_for_video_ids(
        self,
        conversation_id: str,
        max_attempts: int = 15,
        wait_seconds: int = 3
    ) -> List[str]:
        """
        Poll conversation to get video IDs and construct Meta AI URLs.
        
        NEW APPROACH (March 11, 2026):
        1. Fetch conversation to get media IDs
        2. Poll individual media IDs for video status
        3. Construct Meta AI URLs when ready
        
        Videos are viewable at: https://www.meta.ai/create/{media_id}
        
        Args:
            conversation_id: Conversation ID from video generation
            max_attempts: Maximum polling attempts (default: 15 = ~45s)
            wait_seconds: Seconds between attempts (default: 3)
            
        Returns:
            List of Meta AI URLs (https://www.meta.ai/create/{id})
        """
        self.logger.info(f"Polling for video IDs in conversation {conversation_id}")
        
        for attempt in range(1, max_attempts + 1):
            try:
                conv_data = self.fetch_conversation(conversation_id)
                
                if 'error' in conv_data or conv_data.get('data', {}).get('warmupConversation'):
                    self.logger.debug(f"Attempt {attempt}/{max_attempts}: Conversation warming up...")
                    time.sleep(wait_seconds)
                    continue
                
                # Extract video IDs from conversation
                video_ids = self._extract_video_ids_from_conversation(conv_data)
                
                if video_ids:
                    self.logger.info(f"Found {len(video_ids)} media IDs, polling individually...")
                    
                    # Poll each media ID individually to check video status
                    ready_videos = []
                    for media_id in video_ids:
                        media_data = self.poll_media_by_id(media_id)
                        
                        # Check if video is ready (has URL or is complete)
                        if media_data and not media_data.get('error'):
                            # Media exists, construct Meta AI URL
                            ready_videos.append(f"https://www.meta.ai/create/{media_id}")
                            self.logger.debug(f"Media {media_id} is ready")
                    
                    if ready_videos:
                        self.logger.info(f"Found {len(ready_videos)} ready videos on attempt {attempt}")
                        return ready_videos
                    else:
                        self.logger.debug(f"Attempt {attempt}/{max_attempts}: Media IDs found but videos not ready yet")
                else:
                    self.logger.debug(f"Attempt {attempt}/{max_attempts}: Video IDs not ready yet")
                
                if attempt < max_attempts:
                    time.sleep(wait_seconds)
                
            except Exception as e:
                self.logger.warning(f"Attempt {attempt}/{max_attempts} failed: {e}")
                if attempt < max_attempts:
                    time.sleep(wait_seconds)
        
        self.logger.warning(f"Video IDs not available after {max_attempts} attempts (~{max_attempts * wait_seconds}s)")
        return []
    
    def _extract_video_ids_from_conversation(self, conv_data: Dict[str, Any]) -> List[str]:
        """
        Extract video IDs from conversation response.
        
        Args:
            conv_data: Conversation data from fetch_conversation
            
        Returns:
            List of video media IDs
        """
        video_ids = []
        
        try:
            # Navigate to conversation messages
            conversation = conv_data.get('data', {}).get('conversation')
            if not conversation:
                self.logger.debug("Conversation is null or not ready yet")
                return []
                
            messages = conversation.get('messages', {}).get('edges', [])
            
            for edge in messages:
                node = edge.get('node', {})
                
                # Check if this is an assistant message with videos
                if node.get('__typename') == 'AssistantMessage':
                    videos = node.get('videos', [])
                    
                    for video in videos:
                        vid_id = video.get('id')
                        if vid_id and vid_id not in video_ids:
                            video_ids.append(vid_id)
                            self.logger.debug(f"Found video ID: {vid_id}")
            
        except Exception as e:
            self.logger.warning(f"Error extracting video IDs from conversation: {e}")
        
        return video_ids
    
    def _extract_media_ids_from_response(self, response_data: Dict[str, Any]) -> List[str]:
        """
        Extract media IDs from initial video generation response.
        
        Args:
            response_data: Response from generate_video containing events
            
        Returns:
            List of media IDs
        """
        media_ids = []
        
        try:
            # Check if we have events in the response
            events = response_data.get('events', [])
            
            for event in events:
                data = event.get('data', {})
                stream = data.get('sendMessageStream', {})
                
                # Look for videos in the stream
                videos = stream.get('videos', [])
                for video in videos:
                    media_id = video.get('id')
                    if media_id and media_id not in media_ids:
                        media_ids.append(media_id)
                        self.logger.debug(f"Found media ID in response: {media_id}")
        
        except Exception as e:
            self.logger.warning(f"Error extracting media IDs from response: {e}")
        
        return media_ids
    
    def poll_media_by_id(self, media_id: str) -> Dict[str, Any]:
        """
        Poll individual media ID to check video status.
        Uses doc_id 335a1ff137a82e22e0a9724d4bf70b6f from HAR analysis.
        
        Args:
            media_id: Media ID to poll
            
        Returns:
            Response data for the media
        """
        self.logger.debug(f"Polling media ID: {media_id}")
        
        payload = {
            "doc_id": self.POLL_MEDIA_DOC_ID,
            "variables": {
                "mediaId": media_id,
                "mediaIdIsNull": False
            }
        }
        
        headers = {
            "Accept": "multipart/mixed, application/json",
            "Accept-Encoding": "gzip, deflate",
            "Accept-Language": "en-US,en;q=0.9",
            "Content-Type": "application/json",
            "Origin": "https://www.meta.ai",
            "Referer": "https://www.meta.ai/",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        
        try:
            response = self.session.post(
                self.ENDPOINT,
                json=payload,
                headers=headers,
                timeout=self.DEFAULT_TIMEOUT
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                self.logger.warning(f"Failed to poll media {media_id}: {response.status_code}")
                return {"error": f"HTTP {response.status_code}"}
                
        except Exception as e:
            self.logger.error(f"Error polling media {media_id}: {e}")
            return {"error": str(e)}
    
    def fetch_video_urls_from_html(
        self,
        conversation_id: str,
        max_attempts: int = 12,
        wait_seconds: int = 5
    ) -> List[str]:
        """
        Fetch video URLs by scraping the Meta AI conversation page HTML.
        This is an alternative method that extracts video URLs directly from
        the rendered HTML page instead of using the GraphQL API.
        
        Args:
            conversation_id: The conversation UUID
            max_attempts: Maximum number of retry attempts (default: 12)
            wait_seconds: Seconds to wait between attempts (default: 5)
            
        Returns:
            List of video URLs
        """
        self.logger.info(f"Fetching video URLs via HTML scraping for conversation {conversation_id}")
        
        videos = self.html_scraper.fetch_video_urls_from_page(
            conversation_id=conversation_id,
            max_attempts=max_attempts,
            wait_seconds=wait_seconds
        )
        
        # Extract just the URLs
        urls = [v['url'] for v in videos if 'url' in v]
        
        return urls
    
    def extract_media_urls(self, response_data: Dict[str, Any]) -> List[str]:
        """
        Extract media URLs (images or videos) from response
        
        Args:
            response_data: Response data from API
            
        Returns:
            List of media URLs
        """
        urls = []
        
        # Handle multipart response
        if 'data' in response_data and isinstance(response_data['data'], dict):
            data = response_data['data']
        elif 'parts' in response_data:
            # Find data in parts
            for part in response_data['parts']:
                if part.get('data'):
                    data = part['data']
                    break
            else:
                return urls
        else:
            data = response_data
        
        # Extract from messages
        try:
            # Try multiple possible message paths
            messages = []
            
            # Try xfb_imagine_send_message (image generation)
            if 'xfb_imagine_send_message' in data:
                messages = data.get('xfb_imagine_send_message', {}).get('messages', {}).get('edges', [])
            
            # Try xfb_kadabra_send_message (video generation)
            if not messages and 'xfb_kadabra_send_message' in data:
                messages = data.get('xfb_kadabra_send_message', {}).get('messages', {}).get('edges', [])
            
            # Try fetched media path (xfb_genai_fetch_post)
            if not messages and 'xfb_genai_fetch_post' in data:
                messages = data.get('xfb_genai_fetch_post', {}).get('messages', {}).get('edges', [])
            
            # Try with abra prefix variations
            if not messages:
                for key in data.keys():
                    if 'message' in key.lower():
                        key_data = data[key]
                        if isinstance(key_data, dict):
                            msg_data = key_data.get('messages', {}).get('edges', [])
                            if msg_data:
                                messages = msg_data
                                break
            
            # Extract URLs from messages
            for edge in messages:
                if not isinstance(edge, dict):
                    continue
                    
                node = edge.get('node')
                if not isinstance(node, dict):
                    continue
                    
                content = node.get('content')
                if not isinstance(content, dict):
                    continue
                
                # Try image imagine
                imagine_media = content.get('imagine_media')
                if isinstance(imagine_media, dict):
                    images_data = imagine_media.get('images')
                    if isinstance(images_data, dict):
                        images = images_data.get('nodes', [])
                        if isinstance(images, list):
                            for img in images:
                                if isinstance(img, dict):
                                    url = img.get('uri') or img.get('url')
                                    if url:
                                        urls.append(url)
                
                # Try video imagine
                imagine_video = content.get('imagine_video')
                if isinstance(imagine_video, dict):
                    # Handle both 'videos' (plural) and 'video' (singular)
                    videos = []
                    videos_data = imagine_video.get('videos')
                    if isinstance(videos_data, dict):
                        videos = videos_data.get('nodes', [])
                    
                    if not videos:
                        video_single = imagine_video.get('video')
                        if isinstance(video_single, dict):
                            videos = [video_single]
                    
                    if isinstance(videos, list):
                        for video in videos:
                            if not isinstance(video, dict):
                                continue
                                
                            uri = video.get('video_url') or video.get('uri')
                            if uri:
                                urls.append(uri)
                            
                            # Check for delivery response
                            delivery = video.get('videoDeliveryResponseResult')
                            if isinstance(delivery, dict):
                                prog = delivery.get('progressive_urls', [])
                                if isinstance(prog, list):
                                    for p in prog:
                                        if isinstance(p, dict):
                                            pu = p.get('progressive_url')
                                            if pu:
                                                urls.append(pu)
        except Exception as e:
            self.logger.error(f"Error extracting media URLs: {e}")
        
        # Deduplicate while preserving order
        seen = set()
        unique_urls = []
        for u in urls:
            if u not in seen:
                seen.add(u)
                unique_urls.append(u)
        
        return unique_urls
    
    def fetch_media_status(
        self, 
        media_id: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Fetch media status and details by media ID.
        Used for polling video/image generation status.
        
        Args:
            media_id: The media ID to fetch
            **kwargs: Additional parameters
            
        Returns:
            Response from API with media details
        """
        self.logger.info(f"Fetching media status for ID: {media_id}")
        
        variables = {
            "mediaId": media_id,
            "mediaIdIsNull": False,
            "first": 10,
            "after": None
        }
        
        payload = {
            "doc_id": self.FETCH_MEDIA_DOC_ID,
            "variables": variables
        }
        
        headers = {
            "Accept": "multipart/mixed, application/json",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "en-US,en;q=0.9",
            "Content-Type": "application/json",
            "Origin": "https://www.meta.ai",
            "Referer": "https://www.meta.ai/",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "User-Agent": kwargs.get('user_agent', self._default_user_agent())
        }
        
        try:
            # Use tuple timeout (connect, read) for better control
            timeout = (10, self.DEFAULT_TIMEOUT)
            response = self.session.post(
                self.ENDPOINT,
                json=payload,
                headers=headers,
                timeout=timeout
            )
            response.raise_for_status()
            return self._parse_response(response)
        except Exception as e:
            self.logger.error(f"Error fetching media status: {e}")
            return {"error": str(e)}

    def poll_media_completion(
        self,
        media_id: str,
        max_attempts: int = 30,
        wait_seconds: int = 5,
        **kwargs
    ) -> Optional[Dict[str, Any]]:
        """
        Poll for media completion, retrying until media is ready.
        
        Args:
            media_id: The media ID to poll
            max_attempts: Maximum number of polling attempts
            wait_seconds: Seconds to wait between attempts
            **kwargs: Additional parameters
            
        Returns:
            Completed media data or None if timeout
        """
        self.logger.info(f"Polling media {media_id} (max {max_attempts} attempts)...")
        
        for attempt in range(max_attempts):
            try:
                response = self.fetch_media_status(media_id, **kwargs)
                
                # Check if media is ready
                if self._is_media_ready(response):
                    self.logger.info(f"Media {media_id} is ready!")
                    return response
                
                self.logger.info(f"Attempt {attempt + 1}/{max_attempts}: Media not ready yet, waiting {wait_seconds}s...")
                time.sleep(wait_seconds)
                
            except Exception as e:
                self.logger.warning(f"Poll attempt {attempt + 1} failed: {e}")
                if attempt < max_attempts - 1:
                    time.sleep(wait_seconds)
        
        self.logger.warning(f"Media {media_id} not ready after {max_attempts} attempts")
        return None

    def _is_media_ready(self, response_data: Dict[str, Any]) -> bool:
        """
        Check if media in response is ready/complete.
        
        Args:
            response_data: Response from fetch_media_status
            
        Returns:
            True if media is ready, False otherwise
        """
        try:
            # Extract media status from response
            if 'error' in response_data:
                return False
            
            # Check for status field
            status = response_data.get('status') or response_data.get('media_status')
            if status in ['ready', 'READY', 'complete', 'COMPLETE']:
                return True
            
            # Check for URLs (indicates completion)
            urls = self.extract_media_urls(response_data)
            if urls:
                return True
            
            # Check nested structures
            data = response_data.get('data', {})
            if isinstance(data, dict) and len(str(data)) > 100:
                # Has substantial data, likely ready
                return True
                
            return False
        except Exception as e:
            self.logger.warning(f"Error checking media readiness: {e}")
            return False