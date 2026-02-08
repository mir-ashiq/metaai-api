"""
Image Generation API
Extracted from Meta AI network captures
"""

import requests
import json
import uuid


class ImageGenerator:
    """
    Image generator based on Meta AI GraphQL API patterns
    """
    
    ENDPOINT = "https://www.meta.ai/api/graphql"
    # Note: doc_id needs to be extracted from actual image generation captures
    DOC_ID = "<to_be_determined>"
    OPERATION = "TEXT_TO_IMAGE"
    
    def __init__(self, session=None):
        """
        Initialize image generator
        
        Args:
            session: Optional requests session with cookies/auth
        """
        self.session = session or requests.Session()
        
    def generate_image(self, prompt, num_images=4, aspect_ratio="1:1", 
                      conversation_id=None, **kwargs):
        """
        Generate images from text prompt
        
        Args:
            prompt: Text prompt describing the image
            num_images: Number of images to generate (default: 4)
            aspect_ratio: Aspect ratio (default: "1:1")
            conversation_id: Optional conversation UUID
            **kwargs: Additional parameters
            
        Returns:
            Response from API
        """
        # Generate required UUIDs
        conversation_id = conversation_id or str(uuid.uuid4())
        user_message_id = str(uuid.uuid4())
        assistant_message_id = str(uuid.uuid4())
        turn_id = str(uuid.uuid4())
        prompt_session_id = kwargs.get('prompt_session_id', str(uuid.uuid4()))
        
        # Build request payload
        payload = {
            "doc_id": self.DOC_ID,
            "variables": {
                "conversationId": conversation_id,
                "content": f"Imagine {prompt}",
                "userMessageId": user_message_id,
                "assistantMessageId": assistant_message_id,
                "userUniqueMessageId": str(kwargs.get('user_unique_message_id', 
                                          self._generate_unique_id())),
                "turnId": turn_id,
                "spaceId": None,
                "mode": "create",
                "rewriteOptions": None,
                "attachments": None,
                "mentions": None,
                "clippyIp": None,
                "isNewConversation": kwargs.get('is_new_conversation', True),
                "imagineOperationRequest": {
                    "operation": self.OPERATION,
                    "textToImageParams": {
                        "prompt": prompt,
                        "numImages": num_images,
                        "aspectRatio": aspect_ratio
                    }
                },
                "qplJoinId": None,
                "clientTimezone": kwargs.get('timezone', "UTC"),
                "developerOverridesForMessage": None,
                "clientLatitude": None,
                "clientLongitude": None,
                "devicePixelRatio": kwargs.get('device_pixel_ratio', 1.0),
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
        }
        
        # Set headers
        headers = {
            "Accept": "multipart/mixed, application/json",
            "Content-Type": "application/json",
            "Origin": "https://www.meta.ai",
            "Referer": "https://www.meta.ai/",
            "User-Agent": kwargs.get('user_agent', self._default_user_agent())
        }
        
        # Make request
        response = self.session.post(
            self.ENDPOINT,
            json=payload,
            headers=headers
        )
        
        return response
    
    @staticmethod
    def _generate_unique_id():
        """Generate a unique message ID (13-digit number)"""
        import time
        return int(time.time() * 1000000) % (10**13)
    
    @staticmethod
    def _default_user_agent():
        """Default user agent string"""
        return "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36"


# Example usage
if __name__ == "__main__":
    generator = ImageGenerator()
    
    # Example: Generate images
    prompt = "a beautiful sunset over mountains"
    print(f"Generating images for prompt: {prompt}")
    
    response = generator.generate_image(prompt, num_images=4)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text[:500]}...")
