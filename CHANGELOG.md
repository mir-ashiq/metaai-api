# Changelog

All notable changes to Meta AI Python SDK will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.1.0] - 2026-01-16

### 🎉 Image Upload & Enhanced Features

Major update adding comprehensive image upload support with analysis, generation, and video creation capabilities.

### Added

- 📤 **Image Upload Support** - Upload images for AI processing

  - New `upload_image()` method in `MetaAI` class
  - `ImageUploader` class using Meta's rupload protocol
  - UUID-based upload session management
  - Automatic MIME type detection and file size tracking
  - Returns `media_id` for use in subsequent operations

- 🔍 **Image Analysis** - Analyze and describe uploaded images

  - Chat endpoint now accepts `media_ids` parameter
  - Support for `attachment_metadata` (file_size, mime_type)
  - Multi-step agent response parsing for detailed descriptions
  - Entrypoint routing (KADABRA**DISCOVER**UNIFIED_INPUT_BAR)

- 🎨 **Similar Image Generation** - Create variations of uploaded images

  - Generate similar images in different styles
  - Extract URLs from `content.imagine.session.media_sets`
  - Support for 4 simultaneous image generations
  - Fallback URL field checking (uri, image_uri, maybe_image_uri, url)

- 🎬 **Video from Images** - Animate uploaded static images

  - Video generation now accepts uploaded image media_ids
  - Full `attachment_metadata` support
  - Integration with existing `VideoGenerator` class

- 🔧 **Response Parser Enhancements**

  - Enhanced `format_response()` for multi-step agent responses
  - Updated `extract_media()` with primary/fallback location checking
  - Improved `extract_data()` with Kadabra structure support
  - Added support for `XFBAbraMessageMultiStepResponseContent`

- 📚 **Comprehensive Documentation**

  - Complete image upload guide (`IMAGE_UPLOAD_README.md`)
  - Updated quick usage guide (`QUICK_USAGE.md`)
  - New complete workflow example (`examples/image_workflow_complete.py`)
  - API reference with all three use cases
  - Working curl and Python examples

- 🧪 **Testing & Validation**
  - Comprehensive test suite (`test_endpoints.py`)
  - End-to-end workflow validation
  - All features tested and confirmed working

### Changed

- ♻️ Enhanced `MetaAI.prompt()` to support image attachments
- 🔄 Updated `MetaAI.generate_video()` with image support
- 📖 Updated main README with image upload section
- 🏗️ Refactored response parsing for better structure handling
- 🎯 Improved entrypoint selection logic (ABRA vs KADABRA)

### Fixed

- 🐛 Fixed empty responses for chat with uploaded images
- 🐛 Fixed None URLs in image generation responses
- 🐛 Fixed response parsing for Kadabra structures
- 🐛 Fixed media extraction from nested content structures

### Technical Details

- Uses Meta's rupload protocol for image uploads
- Proper GraphQL mutation selection (useKadabraSendMessageMutation)
- Correct doc_id routing (34429318783334028 for Kadabra)
- messagePersistentInput with attachment_size (bytes) and attachment_type (MIME)
- Multi-path response parsing (Abra and Kadabra structures)

## [2.0.0] - 2025-11-22

### 🎉 Initial Release

First stable release of the Meta AI Python SDK with comprehensive features for Meta AI interaction.

### Added

- 🎬 **Video Generation Support** - Generate AI videos from text prompts

  - New `generate_video()` method in `MetaAI` class
  - `VideoGenerator` class for advanced video generation control
  - Automatic token fetching (lsd, fb_dtsg) from cookies
  - Video URL polling with configurable timeout
  - Support for multiple video qualities (HD/SD)

- 🔐 **Automatic Token Management**

  - Auto-fetch missing `lsd` and `fb_dtsg` tokens from Meta AI
  - No manual token configuration required
  - Seamless integration with existing cookie authentication

- 📚 **Enhanced Documentation**

  - Complete video generation guide (`VIDEO_GENERATION_README.md`)
  - API reference with detailed parameters
  - Multiple usage examples
  - Troubleshooting section
  - Migration guide from old code

- 📦 **Clean Project Structure**
  - Organized examples directory
  - Clear separation of concerns
  - Removed temporary/test files
  - Added `.gitignore` for clean repository

### Changed

- ♻️ Refactored `MetaAI.__init__()` to support automatic token fetching
- 📖 Updated main README with video generation section
- 🏗️ Improved project structure for better maintainability

### Examples

- `examples/simple_example.py` - Basic chat and video generation
- `examples/video_generation.py` - Comprehensive video examples
- `examples/test_example.py` - Testing and validation

### Technical Details

- Video generation uses GraphQL API with multipart/form-data
- Dynamic header construction for different request types
- Recursive JSON parsing for video URL extraction
- Configurable polling mechanism (max_attempts, wait_seconds)

---

## [1.x.x] - Previous Versions

### Features

- Chat with Meta AI (Llama 3)
- Image generation (FB authenticated users)
- Real-time internet-connected responses
- Source citation
- Streaming support
- Conversation continuity
- Proxy support

---

## Future Enhancements

### Planned Features

- [ ] Video download functionality
- [ ] Batch video generation
- [ ] Video quality selection
- [ ] Advanced filtering for video URLs
- [ ] Async/await support for video generation
- [ ] Rate limiting and retry logic
- [ ] Video generation progress callbacks
- [ ] Custom video orientation (landscape/portrait/square)
- [ ] Video duration control
- [ ] Style presets for video generation

### Under Consideration

- [ ] Video editing capabilities
- [ ] Frame extraction from generated videos
- [ ] Video concatenation
- [ ] Audio generation integration
- [ ] Video template support

---

## Migration Guide

### From v1.x to v2.0

**Video Generation** (NEW):

```python
# New in v2.0
from metaai_api import MetaAI

ai = MetaAI(cookies=cookies)
result = ai.generate_video("Generate a video of a sunset")
```

**Token Management** (IMPROVED):

```python
# Old way (manual)
cookies = {
    "datr": "...",
    "lsd": "...",      # Had to provide manually
    "fb_dtsg": "..."   # Had to provide manually
}

# New way (automatic)
cookies = {
    "datr": "...",
    "abra_sess": "..."
    # lsd and fb_dtsg auto-fetched!
}
```

**Backward Compatibility**:
All existing v1.x features remain fully compatible. No breaking changes to chat or image generation APIs.

---

## Contributing

We welcome contributions! Areas of interest:

- Video generation enhancements
- Performance optimizations
- Additional features from roadmap
- Bug fixes
- Documentation improvements

---

## License

MIT License - See LICENSE file for details

---

**Meta AI Python SDK** - Built with ❤️ for developers
