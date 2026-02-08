from generation_api import ImageGenerator

generator = ImageGenerator()
response = generator.generate_image("a beautiful sunset", num_images=4, aspect_ratio="16:9")
print(response.json())