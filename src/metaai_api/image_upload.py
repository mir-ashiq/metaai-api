"""
Image upload functionality for Meta AI API.
Handles uploading images to Meta AI's rupload service.
"""

import os
import uuid
import mimetypes
import logging
import json
from typing import Dict, Any, Optional
from urllib.parse import quote, unquote

logger = logging.getLogger(__name__)

class ImageUploader:
    """Handles image upload to Meta AI using the rupload protocol."""
    
    UPLOAD_URL = "https://rupload.meta.ai/gen_ai_document_gen_ai_tenant/{upload_session_id}"
    
    def __init__(self, session, cookies: Dict[str, str]):
        """
        Initialize ImageUploader with a requests session.
        
        Args:
            session: Requests session with cookies and headers
            cookies: Dictionary of cookies including datr, abra_sess, etc.
        """
        self.session = session
        self.cookies = cookies
    
    def upload_image(
        self,
        file_path: str,
        max_retries: int = 3
    ) -> Optional[Dict[str, Any]]:
        """
        Upload an image to Meta AI using the rupload protocol with OAuth authentication.
        
        Args:
            file_path: Path to the image file
            max_retries: Maximum number of retry attempts for retriable errors (default: 3)
            
        Returns:
            Dictionary containing:
                - success: bool - Whether the upload succeeded
                - media_id: str - The uploaded image's media ID (use this in prompts)
                - upload_session_id: str - Unique upload session ID
                - file_name: str - Original filename
                - file_size: int - File size in bytes
                - mime_type: str - MIME type of the image
                - error: str - Error message if upload failed
        """
        # Extract ecto_1_sess for OAuth authentication
        ecto_1_sess = self.cookies.get('ecto_1_sess')
        if not ecto_1_sess:
            return {
                "success": False,
                "error": "Missing ecto_1_sess cookie required for OAuth authentication. Please ensure cookies are properly set."
            }
        
        # URL-decode the ecto_1_sess value (it may contain %3A for :, etc.)
        ecto_1_sess_decoded = unquote(ecto_1_sess)
        
        # Validate file exists
        if not os.path.exists(file_path):
            return {
                "success": False,
                "error": f"File not found at {file_path}"
            }
        
        filename = os.path.basename(file_path)
        file_size = os.path.getsize(file_path)
        
        # Detect MIME type
        mime_type, _ = mimetypes.guess_type(file_path)
        if not mime_type:
            # Default to image/jpeg if detection fails
            mime_type = "image/jpeg"
        
        # Validate it's an image
        if not mime_type.startswith('image/'):
            return {
                "success": False,
                "error": f"Invalid file type: {mime_type}. Only image files are supported."
            }
        
        # Read file data once
        with open(file_path, 'rb') as f:
            file_data = f.read()
        
        # Retry loop for handling temporary failures
        import requests
        import time
        
        for attempt in range(1, max_retries + 1):
            try:
                # Generate unique upload session ID for each attempt
                upload_session_id = str(uuid.uuid4())
                
                # Construct URL
                url = self.UPLOAD_URL.format(upload_session_id=upload_session_id)
                
                # Build headers with OAuth authentication (matching working curl)
                headers = {
                    'accept': '*/*',
                    'accept-language': 'en-US,en;q=0.5',
                    'authorization': f'OAuth ecto1:{ecto_1_sess_decoded}',  # OAuth header with decoded ecto_1_sess
                    'desired_upload_handler': 'genai_document',
                    'ecto_auth_token': 'true',
                    'is_abra_user': 'true',
                    'offset': '0',
                    'origin': 'https://meta.ai',
                    'referer': 'https://meta.ai/',
                    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36',
                    'x-entity-length': str(file_size),
                    'x-entity-name': quote(filename, safe=''),  # URL-encode filename
                    'x-entity-type': mime_type,
                }
                
                logger.info(f"Uploading {filename} ({file_size} bytes, {mime_type}) - attempt {attempt}/{max_retries}")
                if attempt == 1:
                    logger.info(f"Using OAuth with ecto_1_sess: {ecto_1_sess_decoded[:50]}...")
                
                # Create a fresh session without cookies to avoid conflicts with OAuth header
                upload_session = requests.Session()
                
                # POST upload using OAuth authentication only (no cookies)
                response = upload_session.post(
                    url,
                    headers=headers,
                    data=file_data,
                    timeout=30
                )
                
                logger.info(f"Upload response status: {response.status_code}")
                
                # Handle 412 Precondition Failed (AuthorizationFailedError)
                if response.status_code == 412:
                    try:
                        error_data = response.json()
                        debug_info = error_data.get('debug_info', {})
                        is_retriable = debug_info.get('retriable', False)
                        error_type = debug_info.get('type', 'Unknown')
                        error_message = debug_info.get('message', 'Unknown error')
                        
                        logger.error(f"Upload failed: {response.text[:500]}")
                        
                        if is_retriable and attempt < max_retries:
                            wait_time = 2 ** (attempt - 1)  # Exponential backoff: 1s, 2s, 4s
                            logger.warning(f"{error_type}: {error_message}. Retrying in {wait_time}s... (attempt {attempt}/{max_retries})")
                            time.sleep(wait_time)
                            continue
                        else:
                            return {
                                "success": False,
                                "error": f"Upload failed after {attempt} attempts: {error_type} - {error_message}. The ecto_1_sess cookie may be expired or invalid. Please refresh cookies.",
                                "error_type": error_type,
                                "response": error_data
                            }
                    except json.JSONDecodeError:
                        logger.error(f"Could not parse 412 error response: {response.text[:200]}")
                        if attempt < max_retries:
                            wait_time = 2 ** (attempt - 1)
                            logger.warning(f"Retrying in {wait_time}s... (attempt {attempt}/{max_retries})")
                            time.sleep(wait_time)
                            continue
                        else:
                            return {
                                "success": False,
                                "error": f"Upload failed with 412 error after {attempt} attempts. Please refresh ecto_1_sess cookie."
                            }
                
                # Handle other non-200 status codes
                if response.status_code != 200:
                    logger.error(f"Upload failed: {response.text[:500]}")
                    
                    # For 5xx errors, retry
                    if 500 <= response.status_code < 600 and attempt < max_retries:
                        wait_time = 2 ** (attempt - 1)
                        logger.warning(f"Server error {response.status_code}. Retrying in {wait_time}s... (attempt {attempt}/{max_retries})")
                        time.sleep(wait_time)
                        continue
                    
                    response.raise_for_status()
                
                # Parse response
                result = response.json()
                
                # Check if media_id is in the response
                if 'media_id' in result:
                    logger.info(f"Upload successful! media_id: {result['media_id']}")
                    return {
                        "success": True,
                        "media_id": result['media_id'],
                        "upload_session_id": upload_session_id,
                        "file_name": filename,
                        "file_size": file_size,
                        "mime_type": mime_type,
                        "response": result
                    }
                else:
                    return {
                        "success": False,
                        "error": f"Upload succeeded but no media_id returned: {result}",
                        "upload_session_id": upload_session_id,
                        "response": result
                    }
                
            except requests.exceptions.Timeout:
                logger.error(f"Upload timeout on attempt {attempt}/{max_retries}")
                if attempt < max_retries:
                    wait_time = 2 ** (attempt - 1)
                    logger.warning(f"Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                else:
                    return {
                        "success": False,
                        "error": f"Upload timeout after {max_retries} attempts"
                    }
            except Exception as e:
                logger.error(f"Error uploading image on attempt {attempt}/{max_retries}: {e}")
                if attempt < max_retries:
                    wait_time = 2 ** (attempt - 1)
                    logger.warning(f"Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                else:
                    return {
                        "success": False,
                        "error": f"Error uploading image after {max_retries} attempts: {str(e)}"
                    }
        
        # Should never reach here, but just in case
        return {
            "success": False,
            "error": f"Upload failed after {max_retries} attempts"
        }

    @staticmethod
    def extract_media_id_from_response(response_data: Dict[str, Any]) -> Optional[str]:
        """
        Extract media_id from upload response, searching through nested structures.
        
        Args:
            response_data: Response dictionary from upload API
        
        Returns:
            Media ID if found, None otherwise
        """
        # Check direct media_id field
        if 'media_id' in response_data:
            media_id = response_data.get('media_id')
            if media_id:
                logger.info(f"Found media_id: {media_id}")
                return media_id
        
        # Search through nested structures
        def search_for_media_id(obj, depth=0):
            if depth > 10:  # Prevent infinite recursion
                return None
                
            if isinstance(obj, dict):
                # Check common field names for media IDs
                for key in ['mediaId', 'media_id', 'id', 'uploadId', 'entityId']:
                    if key in obj and obj[key]:
                        return obj[key]
                
                # Recursively search dict values
                for value in obj.values():
                    result = search_for_media_id(value, depth + 1)
                    if result:
                        return result
            elif isinstance(obj, list):
                # Search through list items
                for item in obj:
                    result = search_for_media_id(item, depth + 1)
                    if result:
                        return result
            
            return None
        
        media_id = search_for_media_id(response_data)
        if media_id:
            logger.info(f"Extracted media_id from nested response: {media_id}")
            return media_id
        
        return None

    @staticmethod
    def parse_upload_response(response_text: str) -> Dict[str, Any]:
        """
        Parse upload response, handling various formats (JSON, form-encoded, etc.).
        
        Args:
            response_text: Raw response text from upload endpoint
        
        Returns:
            Parsed response as dictionary
        """
        if not response_text:
            return {}
        
        # Try JSON first
        try:
            return json.loads(response_text)
        except json.JSONDecodeError:
            logger.warning("Response is not JSON, attempting to parse as form-encoded")
        
        # Try form-encoded format
        try:
            result = {}
            for pair in response_text.split('&'):
                if '=' in pair:
                    key, value = pair.split('=', 1)
                    result[key] = value
            return result if result else {}
        except Exception as e:
            logger.warning(f"Failed to parse response as form-encoded: {e}")
            return {}
