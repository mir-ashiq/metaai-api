# Changelog

All notable changes to Meta AI Python SDK will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
