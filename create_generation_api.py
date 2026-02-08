import os
import json

# Create the generation_api directory
os.makedirs('generation_api', exist_ok=True)

# Analysis of network.json - Video Generation Request
video_request_pattern = {
    "endpoint": "https://www.meta.ai/api/graphql",
    "method": "POST",
    "doc_id": "904075722675ba2c1a7b333d4c525a1b",
    "operation": "TEXT_TO_VIDEO",
    "request_structure": {
        "doc_id": "904075722675ba2c1a7b333d4c525a1b",
        "variables": {
            "conversationId": "<uuid>",
            "content": "Animate <prompt>",
            "userMessageId": "<uuid>",
            "assistantMessageId": "<uuid>",
            "userUniqueMessageId": "<number>",
            "turnId": "<uuid>",
            "spaceId": None,
            "mode": "create",
            "rewriteOptions": None,
            "attachments": None,
            "mentions": None,
            "clippyIp": None,
            "isNewConversation": True,
            "imagineOperationRequest": {
                "operation": "TEXT_TO_VIDEO",
                "textToImageParams": {
                    "prompt": "<video_prompt>"
                }
            },
            "qplJoinId": None,
            "clientTimezone": "Asia/Calcutta",
            "developerOverridesForMessage": None,
            "clientLatitude": None,
            "clientLongitude": None,
            "devicePixelRatio": 1.25,
            "entryPoint": None,
            "promptSessionId": "<uuid>",
            "promptType": None,
            "conversationStarterId": None,
            "userAgent": "<user_agent_string>",
            "currentBranchPath": None,
            "promptEditType": "new_message",
            "userLocale": "en-US",
            "userEventId": None
        }
    },
    "headers": {
        "accept": "multipart/mixed, application/json",
        "content-type": "application/json",
        "origin": "https://www.meta.ai",
        "referer": "https://www.meta.ai/prompt/<conversation_id>",
        "user-agent": "Mozilla/5.0 ..."
    },
    "example": {
        "prompt": "astronaut in space",
        "content": "Animate astronaut in space"
    }
}

# Image Generation Request Pattern (inferred structure)
image_request_pattern = {
    "endpoint": "https://www.meta.ai/api/graphql",
    "method": "POST",
    "doc_id": "<to_be_determined>",
    "operation": "TEXT_TO_IMAGE",
    "request_structure": {
        "doc_id": "<doc_id>",
        "variables": {
            "conversationId": "<uuid>",
            "content": "Imagine <prompt>",
            "userMessageId": "<uuid>",
            "assistantMessageId": "<uuid>",
            "userUniqueMessageId": "<number>",
            "turnId": "<uuid>",
            "spaceId": None,
            "mode": "create",
            "imagineOperationRequest": {
                "operation": "TEXT_TO_IMAGE",
                "textToImageParams": {
                    "prompt": "<image_prompt>",
                    "numImages": 4,
                    "aspectRatio": "1:1"
                }
            },
            "isNewConversation": True,
            "promptSessionId": "<uuid>",
            "promptEditType": "new_message",
            "userLocale": "en-US"
        }
    },
    "headers": {
        "accept": "multipart/mixed, application/json",
        "content-type": "application/json",
        "origin": "https://www.meta.ai",
        "referer": "https://www.meta.ai/",
        "user-agent": "Mozilla/5.0 ..."
    }
}

# Save API patterns
api_patterns = {
    "video_generation": video_request_pattern,
    "image_generation": image_request_pattern
}

with open('generation_api/api_patterns.json', 'w', encoding='utf-8') as f:
    json.dump(api_patterns, f, indent=2)

# Create video_generation.py
video_gen_code = '''"""
Video Generation API
Extracted from Meta AI network captures
"""

import requests
import json
import uuid


class VideoGenerator:
    """
    Video generator based on Meta AI GraphQL API patterns
    """
    
    ENDPOINT = "https://www.meta.ai/api/graphql"
    DOC_ID = "904075722675ba2c1a7b333d4c525a1b"
    OPERATION = "TEXT_TO_VIDEO"
    
    def __init__(self, session=None):
        """
        Initialize video generator
        
        Args:
            session: Optional requests session with cookies/auth
        """
        self.session = session or requests.Session()
        
    def generate_video(self, prompt, conversation_id=None, **kwargs):
        """
        Generate video from text prompt
        
        Args:
            prompt: Text prompt describing the video
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
                "content": f"Animate {prompt}",
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
                        "prompt": prompt
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
            "Referer": f"https://www.meta.ai/prompt/{conversation_id}",
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
    generator = VideoGenerator()
    
    # Example: Generate a video
    prompt = "astronaut in space"
    print(f"Generating video for prompt: {prompt}")
    
    response = generator.generate_video(prompt)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text[:500]}...")
'''

with open('generation_api/video_generation.py', 'w', encoding='utf-8') as f:
    f.write(video_gen_code)

# Create image_generation.py
image_gen_code = '''"""
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
'''

with open('generation_api/image_generation.py', 'w', encoding='utf-8') as f:
    f.write(image_gen_code)

# Create __init__.py
init_code = '''"""
Meta AI Generation API - Image and Video Generation
Extracted from network captures
"""

from .video_generation import VideoGenerator
from .image_generation import ImageGenerator

__all__ = ['VideoGenerator', 'ImageGenerator']
'''

with open('generation_api/__init__.py', 'w', encoding='utf-8') as f:
    f.write(init_code)

# Create README.md
readme_content = '''# Generation API

This directory contains extracted API patterns for Meta AI image and video generation based on network capture analysis.

## Contents

- `video_generation.py` - Video generation API patterns and implementation
- `image_generation.py` - Image generation API patterns and implementation
- `api_patterns.json` - Raw API patterns extracted from network captures

## API Endpoint

Main GraphQL endpoint: `https://www.meta.ai/api/graphql`

## Operations

### Video Generation
- Operation: `TEXT_TO_VIDEO`
- Doc ID: `904075722675ba2c1a7b333d4c525a1b`
- Example prompt: "astronaut in space"
- Content format: "Animate {prompt}"

### Image Generation
- Operation: `TEXT_TO_IMAGE`
- Doc ID: (needs to be extracted from actual image generation captures)
- Content format: "Imagine {prompt}"
- Parameters:
  - `numImages`: Number of images to generate (default: 4)
  - `aspectRatio`: Image aspect ratio (default: "1:1")

## Usage

### Video Generation

```python
from generation_api import VideoGenerator

generator = VideoGenerator()
response = generator.generate_video("astronaut in space")
print(response.json())
```

### Image Generation

```python
from generation_api import ImageGenerator

generator = ImageGenerator()
response = generator.generate_image("a beautiful sunset", num_images=4, aspect_ratio="16:9")
print(response.json())
```

## Request Structure

Both image and video generation use similar request structures with the following key fields:

- `doc_id`: GraphQL document ID
- `variables.conversationId`: UUID for the conversation
- `variables.content`: Text content with "Imagine" or "Animate" prefix
- `variables.imagineOperationRequest`: Contains the operation type and parameters
  - `operation`: "TEXT_TO_IMAGE" or "TEXT_TO_VIDEO"
  - `textToImageParams.prompt`: The actual generation prompt

## Headers

Required headers:
- `Accept`: "multipart/mixed, application/json"
- `Content-Type`: "application/json"
- `Origin`: "https://www.meta.ai"
- `Referer`: Meta AI URL
- `User-Agent`: Browser user agent string

## Notes

- Authentication/cookies may be required for actual API calls
- The image generation `doc_id` needs to be extracted from actual captures
- Response format is multipart/mixed or JSON depending on the operation
'''

with open('generation_api/README.md', 'w', encoding='utf-8') as f:
    f.write(readme_content)

print("✅ Created generation_api directory structure:")
print("  - __init__.py")
print("  - video_generation.py")
print("  - image_generation.py")
print("  - api_patterns.json")
print("  - README.md")
print("\nAll files created successfully!")
