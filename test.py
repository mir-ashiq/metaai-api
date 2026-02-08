from metaai_api import MetaAI

# Initialize
ai = MetaAI()

# Chat
response = ai.prompt("Hello, how are you?")

# Generate images
response = ai.prompt("a beautiful sunset")

# Generate videos (requires cookies)
from metaai_api import VideoGenerator
gen = VideoGenerator(cookies_str="your_cookies")
result = gen.generate_video("ocean waves")