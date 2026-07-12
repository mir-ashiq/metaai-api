# Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Development Setup

```bash
git clone https://github.com/mir-ashiq/metaai-api.git
cd metaai-api
pip install -e ".[dev,api,browser]"
agent-browser install
```

## Testing

```bash
pytest
```

## Code Style

- Use `black` for formatting
- Use `flake8` for linting
- Add type hints to all public functions
- Add docstrings to all public classes and methods

## Reporting Issues

When reporting an issue, please include:
- Python version
- OS
- Error message/traceback
- Steps to reproduce
- Whether you're using the SDK or API server
