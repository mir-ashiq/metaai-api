# Contributing to Meta AI Python SDK

First off, thank you for considering contributing to Meta AI Python SDK! 🎉

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [How to Contribute](#how-to-contribute)
- [Pull Request Process](#pull-request-process)
- [Coding Standards](#coding-standards)
- [Testing](#testing)

## 📜 Code of Conduct

This project and everyone participating in it is governed by our commitment to providing a welcoming and inclusive environment. Please be respectful and constructive in all interactions.

## 🚀 Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/YOUR-USERNAME/metaai-api.git
   cd metaai-api
   ```
3. **Create a branch** for your contribution:
   ```bash
   git checkout -b feature/your-feature-name
   ```

## 💻 Development Setup

### Prerequisites

- Python 3.7 or higher
- pip or poetry for package management
- Git for version control

### Install Dependencies

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install package in development mode
pip install -e .

# Install development dependencies
pip install -e ".[dev]"
```

### Project Structure

```
metaai-api/
├── src/metaai_api/
│   ├── __init__.py
│   ├── main.py              # Core MetaAI class
│   ├── video_generation.py  # Video generation
│   ├── utils.py
│   ├── exceptions.py
│   └── client.py
├── examples/
├── tests/                   # Unit tests (coming soon)
├── README.md
└── setup.py
```

## 🤝 How to Contribute

### Reporting Bugs

- **Search existing issues** first to avoid duplicates
- Use the **bug report template** when creating a new issue
- Include:
  - Python version
  - Package version
  - Minimal code to reproduce the issue
  - Expected vs actual behavior
  - Error messages/stack traces

### Suggesting Features

- **Search existing issues** for similar suggestions
- Use the **feature request template**
- Describe:
  - The problem your feature solves
  - Proposed solution
  - Alternative solutions considered
  - Use cases and examples

### Code Contributions

We welcome contributions in these areas:

1. **Bug fixes** - Fix reported issues
2. **New features** - Implement from roadmap or new ideas
3. **Documentation** - Improve guides, docstrings, examples
4. **Tests** - Add unit tests, integration tests
5. **Performance** - Optimize existing functionality
6. **Examples** - Add practical usage examples

## 🔄 Pull Request Process

1. **Update your fork**:

   ```bash
   git remote add upstream https://github.com/mir-ashiq/metaai-api.git
   git fetch upstream
   git merge upstream/main
   ```

2. **Make your changes**:
   - Write clean, readable code
   - Follow existing code style
   - Add docstrings to new functions/classes
   - Update documentation if needed

3. **Test your changes**:

   ```bash
   # Run examples
   python examples/simple_example.py

   # Test with different Python versions if possible
   ```

4. **Commit your changes**:

   ```bash
   git add .
   git commit -m "feat: add video quality selection"
   ```

   Use conventional commits:
   - `feat:` - New feature
   - `fix:` - Bug fix
   - `docs:` - Documentation changes
   - `refactor:` - Code refactoring
   - `test:` - Adding tests
   - `chore:` - Maintenance tasks

5. **Push to your fork**:

   ```bash
   git push origin feature/your-feature-name
   ```

6. **Create Pull Request**:
   - Go to the original repository
   - Click "New Pull Request"
   - Select your fork and branch
   - Fill in the PR template
   - Link related issues

### PR Review Process

- Maintainers will review your PR within a few days
- Address any requested changes
- Once approved, your PR will be merged!

## 📏 Coding Standards

### Python Style Guide

- Follow **PEP 8** style guide
- Use **type hints** where appropriate
- Maximum line length: **100 characters**
- Use **descriptive variable names**

### Code Formatting

```bash
# Format with black (recommended)
pip install black
black src/

# Check with flake8
pip install flake8
flake8 src/
```

### Documentation

- Add **docstrings** to all public functions/classes
- Use **Google-style** docstrings:

```python
def generate_video(prompt: str, wait_before_poll: int = 10) -> Dict:
    """
    Generate a video from a text prompt.

    Args:
        prompt: Text description for video generation
        wait_before_poll: Seconds to wait before polling

    Returns:
        Dictionary with success status and video URLs

    Raises:
        ValueError: If prompt is empty

    Example:
        >>> ai = MetaAI(cookies=cookies)
        >>> result = ai.generate_video("sunset")
    """
```

## 🧪 Testing

### Running Tests

```bash
# Run all tests (when available)
pytest tests/

# Run specific test file
pytest tests/test_video_generation.py

# Run with coverage
pytest --cov=metaai_api tests/
```

### Writing Tests

- Add tests for new features
- Ensure existing tests pass
- Aim for high code coverage
- Use meaningful test names

```python
def test_video_generation_with_valid_prompt():
    """Test video generation with a valid prompt."""
    ai = MetaAI(cookies=test_cookies)
    result = ai.generate_video("test prompt")
    assert result["success"] is True
```

## 📝 Documentation Updates

When adding features, update:

- **README.md** - If it changes core usage
- **CHANGELOG.md** - Add entry under "Unreleased"
- **VIDEO_GENERATION_README.md** - For video-related features
- **Docstrings** - In code
- **Examples** - Add practical examples

## 🎯 Priority Areas

We're especially interested in contributions for:

- [ ] Unit tests and test coverage
- [ ] Async/await support
- [ ] Video download functionality
- [ ] Batch processing capabilities
- [ ] Rate limiting and retry logic
- [ ] Performance optimizations
- [ ] Additional examples and tutorials
- [ ] Documentation improvements

## 💡 Questions?

- **General questions**: Open a GitHub Discussion
- **Bug reports**: Create an issue with bug template
- **Feature requests**: Create an issue with feature template
- **Security issues**: Email imseldrith@gmail.com

## 🌟 Recognition

Contributors will be:

- Listed in CHANGELOG.md for their contributions
- Acknowledged in release notes
- Added to CONTRIBUTORS.md (coming soon)

## 📄 License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

**Thank you for making Meta AI Python SDK better!** 🚀
