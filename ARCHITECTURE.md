# Project Architecture - Meta AI Python SDK

## 📁 Directory Structure

```
meta-ai-python/
│
├── .github/
│   ├── workflows/
│   │   ├── ci.yml              # Continuous Integration
│   │   └── python-publish.yml  # PyPI publishing
│   └── README.md               # GitHub repository info
│
├── src/meta_ai_api/
│   ├── __init__.py            # Package initialization and exports
│   ├── main.py                # Core MetaAI class (chat, video, images)
│   ├── video_generation.py    # VideoGenerator class
│   ├── client.py              # Animation/video client utilities
│   ├── utils.py               # Helper functions
│   └── exceptions.py          # Custom exceptions
│
├── examples/
│   ├── simple_example.py      # Quick start guide
│   ├── video_generation.py    # Comprehensive video examples
│   └── test_example.py        # Testing and validation
│
├── .gitignore                 # Git ignore patterns
├── CHANGELOG.md               # Version history and changes
├── CONTRIBUTING.md            # Contribution guidelines
├── LICENSE                    # MIT License
├── pyproject.toml             # Modern Python project metadata
├── QUICK_REFERENCE.md         # Fast lookup guide
├── README.md                  # Main documentation
├── requirements.txt           # Python dependencies
├── setup.cfg                  # Setup configuration
├── setup.py                   # Package installation script
└── VIDEO_GENERATION_README.md # Video generation guide
```

## 🏗️ Architecture Overview

### Core Components

#### 1. **MetaAI Class** (`main.py`)

The main interface for all Meta AI interactions.

**Responsibilities:**

- User authentication and token management
- Chat message handling (streaming and non-streaming)
- Image generation integration
- Video generation orchestration
- Cookie management and auto-token fetching
- Session management and proxy support

**Key Methods:**

- `__init__()` - Initialize with optional FB credentials or cookies
- `prompt()` - Send chat messages, get responses
- `generate_video()` - Generate videos from text prompts
- `_fetch_missing_tokens()` - Auto-fetch lsd/fb_dtsg tokens
- `get_access_token()` - Obtain Meta AI access token
- `get_cookies()` - Extract cookies from Meta AI page

#### 2. **VideoGenerator Class** (`video_generation.py`)

Specialized class for video generation with advanced control.

**Responsibilities:**

- Video generation request construction
- Token extraction and management
- URL polling and video retrieval
- Dynamic header building
- Response parsing and validation

**Key Methods:**

- `generate_video()` - Main video generation orchestration
- `create_video_generation_request()` - Send generation request
- `fetch_video_urls()` - Poll for video completion
- `get_lsd_and_dtsg()` - Static method for token fetching
- `quick_generate()` - One-liner video generation
- `build_headers()` - Dynamic header construction

#### 3. **Utilities** (`utils.py`)

Helper functions used across the package.

**Functions:**

- `extract_value()` - Parse specific values from HTML/text
- `format_response()` - Format API responses
- `generate_offline_threading_id()` - Generate unique IDs
- `get_session()` - Create HTTP session
- `get_fb_session()` - Facebook authentication

#### 4. **Client** (`client.py`)

Animation and video-specific client functionality.

**Functions:**

- `send_animate_request()` - Send animation requests
- Helper methods for video processing

#### 5. **Exceptions** (`exceptions.py`)

Custom exception classes for error handling.

**Classes:**

- `FacebookRegionBlocked` - Region blocking error
- Other Meta AI-specific exceptions

## 🔄 Data Flow

### Chat Request Flow

```
User → MetaAI.prompt()
    ↓
Cookie/Token Check
    ↓
Request Construction
    ↓
Meta AI GraphQL API
    ↓
Response Parsing
    ↓
Return Formatted Data
```

### Video Generation Flow

```
User → MetaAI.generate_video()
    ↓
VideoGenerator Initialization
    ↓
Auto-fetch Tokens (if needed)
    ↓
Build Request Headers
    ↓
Send Video Generation Request
    ↓
Wait (configurable delay)
    ↓
Poll for Video URLs (retry loop)
    ↓
Extract & Return URLs
```

## 🔐 Authentication Patterns

### 1. **Guest Mode** (No Authentication)

- Used for basic chat
- Auto-generates access token
- Limited to text-based interactions

### 2. **Cookie Authentication**

- Required for video generation
- Uses browser cookies (datr, abra_sess, etc.)
- Auto-fetches lsd and fb_dtsg tokens

### 3. **Facebook Authentication**

- Required for image generation
- Uses FB email/password
- Highest rate limits

## 🌐 API Endpoints

### Meta AI GraphQL API

**Base URL:** `https://www.meta.ai/api/graphql/`

**Operations:**

- `useAbraAcceptTOSForTempUserMutation` - Get access token
- `useAbraSendMessageMutation` - Send chat messages
- `AbraSearchPluginDialogQuery` - Fetch sources
- `useKadabraSendMessageMutation` - Generate videos (doc_id: 25290947477183545)
- `KadabraPromptRootQuery` - Fetch video URLs (doc_id: 25290569913909283)

## 📦 Package Management

### Installation Methods

1. **PyPI (Recommended)**

```bash
pip install metaai_api
```

2. **From Source**

```bash
git clone https://github.com/meta-ai-sdk/meta-ai-python.git
cd meta-ai-python
pip install -e .
```

3. **With Development Dependencies**

```bash
pip install -e ".[dev]"
```

### Dependencies

**Core:**

- `requests` - HTTP client
- `requests-html` - HTML parsing and sessions
- `lxml-html-clean` - HTML sanitization
- `beautifulsoup4` - Additional HTML parsing

**Development:**

- `pytest` - Testing framework
- `black` - Code formatting
- `flake8` - Linting
- `mypy` - Type checking

## 🧪 Testing Strategy

### Current Status

- Manual testing via examples
- Integration tests through example scripts

### Future Plans

- Unit tests for all core functions
- Integration tests for API interactions
- Mock tests for external dependencies
- CI/CD pipeline validation
- Code coverage tracking (target: >80%)

## 🚀 Deployment Pipeline

### GitHub Actions Workflows

1. **CI (Continuous Integration)**

   - Runs on: Push to main/develop, Pull Requests
   - Tests: Python 3.7-3.12, Ubuntu/Windows/macOS
   - Checks: Linting, formatting, type checking
   - Examples: Compilation verification

2. **PyPI Publishing**
   - Trigger: New GitHub release
   - Process: Build → Test → Publish
   - Target: PyPI public repository

## 🔒 Security Considerations

1. **Cookie Handling**

   - Never log full cookie values
   - Store securely (environment variables)
   - Refresh regularly (24-48 hours)

2. **Token Management**

   - Auto-fetch mechanism reduces manual handling
   - Tokens stored only in memory
   - No persistent storage

3. **API Rate Limiting**
   - Respect Meta's usage policies
   - Implement backoff strategies
   - Future: Built-in rate limiting

## 📈 Performance Optimization

### Current Optimizations

- Session reuse for multiple requests
- Efficient JSON parsing
- Minimal memory footprint

### Future Improvements

- Async/await support
- Connection pooling
- Response caching
- Batch request processing

## 🔄 Version Management

**Current Version:** 2.0.0

**Versioning Scheme:** Semantic Versioning (SemVer)

- **Major:** Breaking changes
- **Minor:** New features (backward compatible)
- **Patch:** Bug fixes

## 📝 Documentation Strategy

### User Documentation

- README.md - Main guide
- VIDEO_GENERATION_README.md - Specialized guide
- QUICK_REFERENCE.md - Fast lookup
- Examples - Practical code samples

### Developer Documentation

- CONTRIBUTING.md - Contribution guide
- ARCHITECTURE.md - This file
- Inline docstrings - Code documentation
- Type hints - Function signatures

## 🎯 Roadmap

### v2.1.0 (Next Release)

- [ ] Async/await support
- [ ] Video download functionality
- [ ] Batch video generation
- [ ] Unit test suite

### v2.2.0

- [ ] Rate limiting
- [ ] Retry logic
- [ ] Video quality selection
- [ ] Progress callbacks

### v3.0.0

- [ ] Major API redesign (if needed)
- [ ] Advanced video editing
- [ ] Template system
- [ ] Plugin architecture

## 🤝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

**Key Areas for Contribution:**

1. Testing infrastructure
2. Performance optimization
3. New features from roadmap
4. Documentation improvements
5. Bug fixes

---

**Meta AI Python SDK** - Built with ❤️ for developers
