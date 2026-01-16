"""
Image upload functionality for Meta AI API.
Handles uploading images to Meta AI's rupload service.
"""

import os
import uuid
import mimetypes
from typing import Dict, Any, Optional


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
        fb_dtsg: str,
        jazoest: str,
        lsd: str,
        rev: str = "1032041898",
        s: str = "",
        hsi: str = "",
    ) -> Optional[Dict[str, Any]]:
        """
        Upload an image to Meta AI using the rupload protocol.
        
        Args:
            file_path: Path to the image file
            fb_dtsg: Facebook DTSG token from session
            jazoest: Jazoest token from session
            lsd: LSD token from session
            rev: Revision parameter (optional)
            s: Session parameter (optional)
            hsi: HSI parameter (optional)
            
        Returns:
            Dictionary containing:
                - success: bool
                - media_id: str (if successful)
                - upload_session_id: str
                - file_name: str
                - file_size: int
                - mime_type: str
                - error: str (if failed)
        """
        try:
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
            
            # Generate unique upload session ID
            upload_session_id = str(uuid.uuid4())
            
            # Read file data
            with open(file_path, 'rb') as f:
                file_data = f.read()
            
            # Construct URL
            url = self.UPLOAD_URL.format(upload_session_id=upload_session_id)
            
            # Common params used across requests
            params = {
                '__user': '0',
                '__a': '1',
                '__req': '12',
                '__hs': '20468.HYP:kadabra_pkg.2.1...0',
                'dpr': '1',
                '__ccg': 'GOOD',
                '__rev': rev,
                '__s': s,
                '__hsi': hsi,
                '__dyn': '7xeUjG1mxu1syUqxemh0no6u5U4e2C1vzEdE98K360CEbo1nEhw2nVEtwMw6ywaq221FwpUO0n24oaEnxO0Bo7O2l0Fwqo31w9O1lwlE-U2zxe2GewbS361qw82dUlwhE-15wmo423-0j52oS0Io5d0bS1LBwNwKG0WE8oC1IwGw-wlUcE2-G2O7E5y1rwGwto461wwi85a0YU4G1Jw',
                '__csr': 'g8YD5FTazFYJRlIyZcJ5FaWVuGWhaW8pWAhlTB8BVEydBhuazU98jxTDwpUWeJ0Tw05RAw6x4cXwHgbEUM0P4w1Cu2yQ0kQWxh11APwd2rC5j4gpx50K2UOgE6G9xd06QK0q20hu0VoWU1fo1i40xo2yJ0eK0uq8ymaDgdEn80zk0YC1o2UGkMn6jw7hw70Zw6twppn88jAKP0qrBka1K540JE2ZwjU50w0thwi82Ew0rFrxy0nO0jul7CgcK8Aw6QK2S19w5-w0N3gsye5VA',
                'fb_dtsg': fb_dtsg,
                'jazoest': jazoest,
                'lsd': lsd,
            }
            
            # Step 1: GET handshake (check if session exists)
            get_headers = {
                'accept': '*/*',
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36 Edg/143.0.0.0',
            }
            
            # Perform GET check (mimics browser behavior)
            self.session.get(url, params=params, cookies=self.cookies, headers=get_headers)
            
            # Step 2: POST upload
            post_headers = {
                'accept': '*/*',
                'accept-language': 'en-US,en;q=0.9',
                'desired_upload_handler': 'genai_document',
                'is_abra_user': 'true',
                'offset': '0',  # Starting at the beginning of the file
                'origin': 'https://www.meta.ai',
                'referer': 'https://www.meta.ai/',
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36 Edg/143.0.0.0',
                'x-entity-length': str(file_size),
                'x-entity-name': filename,
                'x-entity-type': mime_type,
                'content-type': 'application/x-www-form-urlencoded',
            }
            
            response = self.session.post(
                url,
                params=params,
                cookies=self.cookies,
                headers=post_headers,
                data=file_data,
            )
            
            response.raise_for_status()
            
            # Parse response
            result = response.json()
            
            # Check if media_id is in the response
            if 'media_id' in result:
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
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Error uploading image: {str(e)}"
            }
