"""
Meta AI Video Generation Module - Fixed Based on HAR Analysis
Implements the CORRECT video generation workflow discovered from HAR file analysis
"""

import requests
import json
import time
import uuid
import logging
from typing import Dict, List, Optional, Any
from requests_html import HTMLSession
from metaai_api.utils import extract_value

logger = logging.getLogger(__name__)


class VideoGeneratorFixed:
    """
    Fixed video generator based on actual HAR file analysis.
    Uses correct doc_ids, request formats, and SSE handling.
    """

    GRAPHQL_URL = 'https://www.meta.ai/api/graphql/'
    
    # Correct doc_ids from HAR analysis
    VIDEO_CARD_DOC_ID = "666834feb70769370072c294c87ebd23"
    VIDEO_GENERATE_DOC_ID = "a3d873304cb1411ba7f056e47060ad1d"
    VIDEO_FETCH_DOC_ID = "10b7bd5aa8b7537e573e49d701a5b21b"

    def __init__(
        self,
        cookies_str: Optional[str] = None,
        cookies_dict: Optional[Dict[str, str]] = None
    ):
        """
        Initialize the VideoGenerator.
        
        Args:
            cookies_str: Cookie string in format "key=value; key=value"
            cookies_dict: Pre-parsed cookies dictionary
        """
        if cookies_dict:
            self.cookies = cookies_dict
            self.cookies_str = "; ".join([f"{k}={v}" for k, v in cookies_dict.items()])
        elif cookies_str:
            self.cookies = self._parse_cookies(cookies_str)
            self.cookies_str = cookies_str
        else:
            raise ValueError("Either cookies_str or cookies_dict must be provided")

        # Auto-fetch tokens
        try:
            tokens = self.get_lsd_and_dtsg(self.cookies_str)
            self.lsd = tokens['lsd']
            self.fb_dtsg = tokens['fb_dtsg']
            logger.info(f"[VIDEO] Tokens fetched: lsd={self.lsd[:20]}..., fb_dtsg={self.fb_dtsg[:20]}...")
        except Exception as e:
            raise ValueError(f"Failed to auto-fetch tokens: {e}")

    @staticmethod
    def _parse_cookies(cookie_str: str) -> Dict[str, str]:
        """Parse cookie string into dictionary"""
        cookies = {}
        for item in cookie_str.split('; '):
            if '=' in item:
                key, value = item.split('=', 1)
                cookies[key] = value
        return cookies

    @staticmethod
    def get_lsd_and_dtsg(cookies_str: str) -> Dict[str, str]:
        """Extract lsd and fb_dtsg from Meta AI page"""
        session = HTMLSession()
        headers = {"cookie": cookies_str}
        response = session.get("https://meta.ai", headers=headers)
        
        lsd = extract_value(response.text, start_str='"LSD",[],{"token":"', end_str='"')
        fb_dtsg = extract_value(response.text, start_str='DTSGInitData",[],{"token":"', end_str='"')
        
        return {"lsd": lsd, "fb_dtsg": fb_dtsg}

    def build_common_headers(self) -> Dict[str, str]:
        """Build common headers for all requests"""
        return {
            'accept': '*/*',
            'accept-language': 'en-US,en;q=0.9',
            'content-type': 'application/x-www-form-urlencoded',
            'origin': 'https://www.meta.ai',
            'referer': 'https://www.meta.ai/',
            'sec-ch-ua': '"Brave";v="141", "Not?A_Brand";v="8", "Chromium";v="141"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36',
            'x-asbd-id': '359341',
            'x-fb-lsd': self.lsd,
        }

    def build_common_data(self) -> Dict[str, str]:
        """Build common data fields for all requests"""
        spin_t = str(int(time.time()))
        return {
            'av': '813590375178585',
            '__user': '0',
            '__a': '1',
            '__req': 'q',
            '__hs': '20413.HYP:kadabra_pkg.2.1...0',
            'dpr': '1',
            '__ccg': 'GOOD',
            '__rev': '1030219547',
            '__s': 'q59jx4:9bnqdw:3ats33',
            '__hsi': '7575127759957881428',
            '__dyn': '7xeUjG1mxu1syUqxemh0no6u5U4e2C1vzEdE98K360CEbo1nEhw2nVEtwMw6ywaq221FwpUO0n24oaEnxO0Bo7O2l0Fwqo31w9O1lwlE-U2zxe2GewbS361qw82dUlwhE-15wmo423-0j52oS0Io5d0bS1LBwNwKG0WE8oC1IwGw-wlUcE2-G2O7E5y1rwa211wo84y1iwfe1aw',
            '__csr': '',
            '__comet_req': '72',
            'fb_dtsg': self.fb_dtsg,
            'jazoest': '25499',
            'lsd': self.lsd,
            '__spin_r': '1030219547',
            '__spin_b': 'trunk',
            '__spin_t': spin_t,
            '__jssesw': '1',
        }

    def query_video_card(self, card_id: str = "1557264142232231", verbose: bool = True) -> Dict:
        """
        Step 1: Query VIDEO_CARD to initialize video generation context.
        This step is REQUIRED before video generation.
        
        Args:
            card_id: Video card ID (default from HAR analysis)
            verbose: Whether to print status messages
            
        Returns:
            Response dictionary with card configuration
        """
        if verbose:
            logger.info(f"[VIDEO] Step 1: Querying VIDEO_CARD (id: {card_id})...")
        
        variables = {
            "cardId": card_id,
            "cardType": "VIDEO_CARD"
        }
        
        data = self.build_common_data()
        data.update({
            'fb_api_caller_class': 'RelayModern',
            'fb_api_req_friendly_name': 'VideoCardQuery',
            'server_timestamps': 'true',
            'variables': json.dumps(variables),
            'doc_id': self.VIDEO_CARD_DOC_ID,
        })
        
        try:
            response = requests.post(
                self.GRAPHQL_URL,
                cookies=self.cookies,
                headers=self.build_common_headers(),
                data=data,
                timeout=30
            )
            
            if response.status_code == 200:
                if verbose:
                    logger.info(f"[VIDEO] ✓ VIDEO_CARD query successful")
                return response.json()
            else:
                logger.error(f"[VIDEO] ✗ VIDEO_CARD query failed: {response.status_code}")
                logger.debug(f"[VIDEO] Response: {response.text[:500]}")
                return {}
                
        except Exception as e:
            logger.error(f"[VIDEO] ✗ VIDEO_CARD query error: {e}")
            return {}

    def generate_videos_with_prompt(
        self,
        prompt: str,
        conversation_id: Optional[str] = None,
        verbose: bool = True
    ) -> Optional[Dict]:
        """
        Step 2: Generate videos from text prompt using Server-Sent Events.
        Returns dict with conversation_id and mediaIds for later fetching.
        
        Args:
            prompt: Text prompt for video generation
            conversation_id: Optional existing conversation ID
            verbose: Whether to print status messages
            
        Returns:
            Dict with {"conversation_id": str, "media_ids": List[str]} if successful, None otherwise
        """
        if conversation_id is None:
            conversation_id = str(uuid.uuid4())
        
        if verbose:
            logger.info(f"[VIDEO] Step 2: Generating videos for prompt: '{prompt}'")
            logger.info(f"[VIDEO] Conversation ID: {conversation_id}")
        
        variables = {
            "message": {"sensitive_string_value": prompt},
            "externalConversationId": conversation_id,
            "isNewConversation": True,
            "imagineClientOptions": {"orientation": "VERTICAL"},
        }
        
        data = self.build_common_data()
        data.update({
            'fb_api_caller_class': 'RelayModern',
            'fb_api_req_friendly_name': 'useKadabraSendMessageMutation',
            'server_timestamps': 'true',
            'variables': json.dumps(variables),
            'doc_id': self.VIDEO_GENERATE_DOC_ID,
        })
        
        try:
            response = requests.post(
                self.GRAPHQL_URL,
                cookies=self.cookies,
                headers=self.build_common_headers(),
                data=data,
                timeout=30
            )
            
            if response.status_code == 200:
                # Log complete response for debugging
                if verbose:
                    logger.info(f"[VIDEO] Response length: {len(response.text)} chars")
                    logger.info(f"[VIDEO] Complete response:\n{response.text}")
                
                # Parse SSE response to extract mediaIds
                media_ids = self._parse_sse_media_ids(response.text, verbose)
                
                if verbose:
                    logger.info(f"[VIDEO] ✓ Video generation request sent successfully")
                    if media_ids:
                        logger.info(f"[VIDEO] ✓ Extracted {len(media_ids)} mediaId(s): {media_ids}")
                    else:
                        logger.warning(f"[VIDEO] ⚠ No mediaIds found in response (might still be processing)")
                
                return {
                    "conversation_id": conversation_id,
                    "media_ids": media_ids  # May be empty if still processing
                }
            else:
                logger.error(f"[VIDEO] ✗ Video generation failed: {response.status_code}")
                logger.debug(f"[VIDEO] Response: {response.text[:500]}")
                return None
                
        except Exception as e:
            logger.error(f"[VIDEO] ✗ Video generation error: {e}")
            return None
    
    @staticmethod
    def _parse_sse_media_ids(sse_text: str, verbose: bool = False) -> List[str]:
        """
        Parse Server-Sent Events response to extract mediaIds.
        
        Expected format:
        data: {"type":"media_generated","mediaIds":["123","456","789"],"conversationId":"..."}
        
        Args:
            sse_text: Raw SSE response text
            verbose: Whether to print debug info
            
        Returns:
            List of mediaIds
        """
        media_ids = []
        
        if verbose:
            logger.info(f"[VIDEO] Parsing SSE response ({len(sse_text)} chars)")
        
        # Parse SSE format: "data: {json}\n\n"
        lines = sse_text.split('\n')
        if verbose:
            logger.info(f"[VIDEO] Found {len(lines)} lines in SSE response")
        
        for idx, line in enumerate(lines):
            line = line.strip()
            if line.startswith('data: '):
                if verbose:
                    logger.info(f"[VIDEO] Line {idx}: {line}")
                try:
                    json_str = line[6:]  # Remove "data: " prefix
                    data = json.loads(json_str)
                    
                    if verbose:
                        logger.info(f"[VIDEO] Parsed JSON type: {data.get('type')}")
                   
                    if data.get("type") == "media_generated":
                        ids = data.get("mediaIds", [])
                        if ids:
                            media_ids.extend(ids)
                            if verbose:
                                logger.info(f"[VIDEO] Found mediaIds in SSE: {ids}")
                except json.JSONDecodeError:
                    continue
        
        return media_ids

    def fetch_video_metadata(
        self,
        media_id: str,
        verbose: bool = True,
        debug: bool = False
    ) -> List[str]:
        """
        Step 3: Fetch video metadata using mediaId (NOT conversation ID!).
        
        Args:
            media_id: The mediaId from generation response (not conversation_id!)
            verbose: Whether to print status messages
            debug: Whether to print debug info including response
            
        Returns:
            List of video URLs
        """
        if verbose:
            logger.info(f"[VIDEO] Step 3: Fetching video for mediaId: {media_id}")
        
        variables = {
            "mediaId": media_id,
            "__relay_internal__pv__KadabraVideoDeliveryRequestrelayprovider": {
                "dash_manifest_requests": [{}],
                "progressive_url_requests": [{"quality": "HD"}, {"quality": "SD"}]
            }
        }
        
        data = self.build_common_data()
        data.update({
            'fb_api_caller_class': 'RelayModern',
            'fb_api_req_friendly_name': 'KadabraPromptRootQuery',
            'server_timestamps': 'true',
            'variables': json.dumps(variables),
            'doc_id': self.VIDEO_FETCH_DOC_ID,
        })
        
        try:
            response = requests.post(
                self.GRAPHQL_URL,
                cookies=self.cookies,
                headers=self.build_common_headers(),
                data=data,
                timeout=30
            )
            
            if response.status_code == 200:
                # Debug: Show complete response
                if debug:
                    logger.info(f"[VIDEO] DEBUG - Response length: {len(response.text)} chars")
                    logger.info(f"[VIDEO] DEBUG - Complete response:\n{response.text}")
                
                video_urls = self._extract_video_urls_from_response(response.text, verbose, debug)
                if video_urls:
                    if verbose:
                        logger.info(f"[VIDEO] ✓ Found {len(video_urls)} video URL(s)")
                elif debug:
                    logger.warning(f"[VIDEO] No URLs extracted. Response length: {len(response.text)} chars")
                return video_urls
            else:
                logger.error(f"[VIDEO] ✗ Fetch failed: {response.status_code}")
                if debug:
                    logger.error(f"[VIDEO] Response: {response.text[:500]}")
                return []
                
        except Exception as e:
            logger.error(f"[VIDEO] ✗ Fetch error: {e}")
            if debug:
                import traceback
                logger.error(traceback.format_exc())
            return []

    @staticmethod
    def _extract_video_urls_from_response(response_text: str, verbose: bool = False, debug: bool = False) -> List[str]:
        """
        Extract video URLs from Meta AI GraphQL response.
        Uses the CORRECT structure from HAR analysis.
        """
        urls: List[str] = []

        try:
            data = json.loads(response_text)
            
            if debug:
                logger.info(f"[VIDEO] DEBUG - Parsed JSON. Top-level keys: {list(data.keys())}")
            
            # Correct path from HAR analysis
            data_obj = data.get("data", {})
            if debug:
                logger.info(f"[VIDEO] DEBUG - data keys: {list(data_obj.keys())}")
            
            fetch_post = data_obj.get("xfb_genai_fetch_post") or data_obj.get("xab_abra__xfb_genai_fetch_post") or {}
            
            if not fetch_post and debug:
                logger.info(f"[VIDEO] DEBUG - No fetch_post found. data keys: {list(data_obj.keys())}")
            
            messages = fetch_post.get("messages", {}).get("edges", [])
            if debug:
                logger.info(f"[VIDEO] DEBUG - Found {len(messages)} message edges")
            
            for edge in messages:
                node = edge.get("node", {})
                content = node.get("content", {})
                imagine_video = content.get("imagine_video") or {}
                
                if not imagine_video:
                    continue

                # Extract from videos.nodes[]
                videos = imagine_video.get("videos", {}).get("nodes", [])
                for video in videos:
                    uri = video.get("video_url") or video.get("uri")
                    if uri:
                        urls.append(uri)
                    
                    # Try videoDeliveryResponseResult.progressive_urls[]
                    delivery = video.get("videoDeliveryResponseResult") or {}
                    prog = delivery.get("progressive_urls", [])
                    for p in prog:
                        pu = p.get("progressive_url")
                        if pu:
                            urls.append(pu)

                # Extract from single video object
                single_video = imagine_video.get("video") or {}
                if isinstance(single_video, dict) and single_video:
                    uri = single_video.get("video_url") or single_video.get("uri")
                    if uri:
                        urls.append(uri)
                    
                    delivery = single_video.get("videoDeliveryResponseResult") or {}
                    prog = delivery.get("progressive_urls", [])
                    for p in prog:
                        pu = p.get("progressive_url")
                        if pu:
                            urls.append(pu)

        except json.JSONDecodeError:
            # Fallback to regex
            import re
            urls = re.findall(r'https?://[^\s"\'<>]+fbcdn[^\s"\'<>]+\.mp4[^\s"\'<>]*', response_text)

        # Deduplicate
        seen = set()
        unique_urls = []
        for u in urls:
            if u and u not in seen:
                seen.add(u)
                unique_urls.append(u)
        
        return unique_urls

    def generate_video(
        self,
        prompt: str,
        wait_before_poll: int = 10,
        max_attempts: int = 30,
        wait_seconds: int = 5,
        verbose: bool = True
    ) -> Dict:
        """
        Complete video generation workflow.
        
        Args:
            prompt: Text prompt for video generation
            wait_before_poll: Seconds to wait before polling
            max_attempts: Maximum polling attempts
            wait_seconds: Seconds between polling attempts
            verbose: Whether to print status messages
            
        Returns:
            Dictionary with success status, conversation_id, prompt, and video_urls
        """
        if verbose:
            logger.info(f"\n{'='*60}")
            logger.info(f"[VIDEO] Starting video generation workflow")
            logger.info(f"[VIDEO] Prompt: '{prompt}'")
            logger.info(f"{'='*60}\n")
        
        # Step 1: Query VIDEO_CARD
        card_result = self.query_video_card(verbose=verbose)
        if not card_result:
            logger.warning("[VIDEO] VIDEO_CARD query failed, continuing anyway...")
        
        # Step 2: Generate videos
        gen_result = self.generate_videos_with_prompt(
            prompt=prompt,
            verbose=verbose
        )
        
        if not gen_result:
            return {
                "success": False,
                "error": "Failed to start video generation",
                "prompt": prompt
            }
        
        conversation_id = gen_result["conversation_id"]
        media_ids = gen_result.get("media_ids", [])
        
        # Step 3: Wait before polling/fetching
        if verbose:
            if media_ids:
                logger.info(f"[VIDEO] Got {len(media_ids)} mediaId(s), waiting {wait_before_poll}s before fetching...")
            else:
                logger.info(f"[VIDEO] No mediaIds yet, will poll for them...")
        
        if not media_ids:
            # Poll to get mediaIds
            time.sleep(wait_before_poll)
            if verbose:
                logger.info(f"[VIDEO] Polling for mediaIds...")
            
            for attempt in range(1, min(10, max_attempts) + 1):
                gen_result = self.generate_videos_with_prompt(
                    prompt=prompt,
                    conversation_id=conversation_id,
                    verbose=False
                )
                
                if gen_result and gen_result.get("media_ids"):
                    media_ids = gen_result["media_ids"]
                    if verbose:
                        logger.info(f"[VIDEO] Got {len(media_ids)} mediaId(s) on attempt {attempt}!")
                    break
                
                if attempt < min(10, max_attempts):
                    time.sleep(wait_seconds)
        
        if not media_ids:
            logger.error(f"[VIDEO] Failed to get mediaIds after polling")
            return {
                "success": False,
                "error": "Failed to get mediaIds",
                "conversation_id": conversation_id,
                "prompt": prompt
            }
        
        # Step 4: Fetch videos using mediaIds
        time.sleep(wait_before_poll)
        video_urls = []
        
        for idx, media_id in enumerate(media_ids, 1):
            if verbose:
                logger.info(f"[VIDEO] Fetching video {idx}/{len(media_ids)} (mediaId: {media_id})...")
            
            urls = self.fetch_video_metadata(
                media_id=media_id,
                verbose=verbose,
                debug=(idx == 1)  # Debug first one only
            )
            video_urls.extend(urls)
        
        result = {
            "success": len(video_urls) > 0,
            "conversation_id": conversation_id,
            "media_ids": media_ids,
            "prompt": prompt,
            "video_urls": video_urls,
            "timestamp": time.time()
        }
        
        if video_urls and verbose:
            logger.info(f"\n{'='*60}")
            logger.info(f"[VIDEO] \u2713 SUCCESS! Found {len(video_urls)} video URL(s)")
            logger.info(f"{'='*60}\n")
        elif verbose:
            logger.error(f"\n{'='*60}")
            logger.error(f"[VIDEO] \u2717 FAILED - No videos found")
            logger.error(f"{'='*60}\n")
        
        return result

    @classmethod
    def quick_generate(
        cls,
        cookies_str: str,
        prompt: str,
        verbose: bool = True
    ) -> Dict:
        """
        Convenience method to generate a video with minimal setup.
        
        Args:
            cookies_str: Cookie string
            prompt: Text prompt for video generation
            verbose: Whether to print status messages
            
        Returns:
            Dictionary with success status and video URLs
        """
        generator = cls(cookies_str=cookies_str)
        return generator.generate_video(prompt=prompt, verbose=verbose)
