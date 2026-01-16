"""
Enable comprehensive debug logging for Meta AI API troubleshooting.
Run this before starting the server to see detailed logs.
"""

import logging
import sys

# Configure root logger
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('meta_ai_debug.log', mode='w')
    ]
)

# Set specific loggers to DEBUG
logging.getLogger('metaai_api').setLevel(logging.DEBUG)
logging.getLogger('metaai_api.video_generation').setLevel(logging.DEBUG)
logging.getLogger('metaai_api.api_server').setLevel(logging.DEBUG)
logging.getLogger('uvicorn').setLevel(logging.INFO)

print("=" * 70)
print("DEBUG LOGGING ENABLED")
print("=" * 70)
print("Log output:")
print("  - Console: stdout (colored)")
print("  - File: meta_ai_debug.log")
print("=" * 70)
print()
