# Generation API

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
