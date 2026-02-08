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


class GenerationAPI:
    """
    Image and Video Generation API based on Meta AI GraphQL patterns
    """
    
    ENDPOINT = "https://www.meta.ai/api/graphql"
    DOC_ID = "904075722675ba2c1a7b333d4c525a1b"
    
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
    
    def _generate_unique_id(self) -> int:
        """Generate a unique message ID (13-digit number)"""
        return int(time.time() * 1000000) % (10**13)
    
    def _default_user_agent(self) -> str:
        """Default user agent string"""
        return "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36 Edg/144.0.0.0"
    
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
        
        variables = {
            "conversationId": conversation_id,
            "content": f"{content_prefix} {prompt}",
            "userMessageId": user_message_id,
            "assistantMessageId": assistant_message_id,
            "userUniqueMessageId": str(kwargs.get('user_unique_message_id', self._generate_unique_id())),
            "turnId": turn_id,
            "spaceId": None,
            "mode": "create",
            "rewriteOptions": None,
            "attachments": None,
            "mentions": None,
            "clippyIp": None,
            "isNewConversation": kwargs.get('is_new_conversation', True),
            "imagineOperationRequest": {
                "operation": operation,
                "textToImageParams": {
                    "prompt": prompt
                }
            },
            "qplJoinId": None,
            "clientTimezone": kwargs.get('timezone', "UTC"),
            "developerOverridesForMessage": None,
            "clientLatitude": None,
            "clientLongitude": None,
            "devicePixelRatio": kwargs.get('device_pixel_ratio', 1.25),
            "entryPoint": None,
            "promptSessionId": prompt_session_id,
            "promptType": None,
            "conversationStarterId": None,
            "userAgent": kwargs.get('user_agent', self._default_user_agent()),
            "currentBranchPath": None,
            "promptEditType": "new_message",
            "userLocale": kwargs.get('locale', "en-US"),
            "userEventId": None
        }
        
        return variables
    
    def generate_image(
        self, 
        prompt: str,
        orientation: str = "VERTICAL",
        num_images: int = 1,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate images from text prompt
        
        Args:
            prompt: Text prompt describing the image
            orientation: Image orientation (VERTICAL, HORIZONTAL, SQUARE)
            num_images: Number of images to generate (default: 1)
            **kwargs: Additional parameters
            
        Returns:
            Response from API
        """
        self.logger.info(f"Generating image with prompt: {prompt}")
        
        variables = self._build_base_variables(
            prompt=prompt,
            operation="TEXT_TO_IMAGE",
            content_prefix="Imagine",
            **kwargs
        )
        
        # Add image-specific parameters
        variables["imagineOperationRequest"]["textToImageParams"]["orientation"] = orientation
        if num_images > 1:
            variables["imagineOperationRequest"]["textToImageParams"]["numImages"] = num_images
        
        payload = {
            "doc_id": self.DOC_ID,
            "variables": variables
        }
        
        conversation_id = variables["conversationId"]
        headers = {
            "Accept": "multipart/mixed, application/json",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "en-US,en;q=0.9",
            "Content-Type": "application/json",
            "Origin": "https://www.meta.ai",
            "Referer": f"https://www.meta.ai/prompt/{conversation_id}",
            "Sec-Ch-Ua": '"Not(A:Brand";v="8", "Chromium";v="144", "Microsoft Edge";v="144"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Windows"',
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "User-Agent": kwargs.get('user_agent', self._default_user_agent())
        }
        
        response = self.session.post(
            self.ENDPOINT,
            json=payload,
            headers=headers
        )
        
        response.raise_for_status()
        return self._parse_response(response)
    
    def generate_video(
        self, 
        prompt: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate video from text prompt
        
        Args:
            prompt: Text prompt describing the video
            **kwargs: Additional parameters
            
        Returns:
            Response from API
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
            "Accept": "multipart/mixed, application/json",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "en-US,en;q=0.9",
            "Content-Type": "application/json",
            "Origin": "https://www.meta.ai",
            "Referer": f"https://www.meta.ai/prompt/{conversation_id}",
            "Sec-Ch-Ua": '"Not(A:Brand";v="8", "Chromium";v="144", "Microsoft Edge";v="144"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Windows"',
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "User-Agent": kwargs.get('user_agent', self._default_user_agent())
        }
        
        response = self.session.post(
            self.ENDPOINT,
            json=payload,
            headers=headers
        )
        
        response.raise_for_status()
        return self._parse_response(response)
    
    def _parse_response(self, response: requests.Response) -> Dict[str, Any]:
        """
        Parse response from Meta AI API
        
        Args:
            response: Response object
            
        Returns:
            Parsed response data
        """
        content_type = response.headers.get('Content-Type', '')
        
        if 'multipart/mixed' in content_type:
            return self._parse_multipart_response(response)
        else:
            return response.json()
    
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
            messages = (data.get('data', {})
                       .get('xfb_imagine_send_message', {})
                       .get('messages', {})
                       .get('edges', []))
            
            for edge in messages:
                node = edge.get('node', {})
                content = node.get('content', {})
                
                # Try image imagine
                imagine_media = content.get('imagine_media') or {}
                images = imagine_media.get('images', {}).get('nodes', [])
                for img in images:
                    url = img.get('uri') or img.get('url')
                    if url:
                        urls.append(url)
                
                # Try video imagine
                imagine_video = content.get('imagine_video') or {}
                videos = imagine_video.get('videos', {}).get('nodes', [])
                for video in videos:
                    uri = video.get('video_url') or video.get('uri')
                    if uri:
                        urls.append(uri)
                    
                    # Check for delivery response
                    delivery = video.get('videoDeliveryResponseResult') or {}
                    prog = delivery.get('progressive_urls', [])
                    for p in prog:
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
