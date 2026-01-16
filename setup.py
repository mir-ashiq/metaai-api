import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="metaai-sdk",
    version="2.2.1",
    author="Ashiq Hussain Mir",
    author_email="imseldrith@gmail.com",
    description="Feature-rich Python SDK for Meta AI - Chat, Image & Video Generation powered by Llama 3",
    keywords="metaai, meta-ai, llama3, ai, llm, video-generation, image-generation, chatbot, conversational-ai",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/mir-ashiq/metaai-api",
    project_urls={
        "Documentation": "https://github.com/mir-ashiq/metaai-api/blob/main/README.md",
        "Bug Reports": "https://github.com/mir-ashiq/metaai-api/issues",
        "Source Code": "https://github.com/mir-ashiq/metaai-api",
        "Changelog": "https://github.com/mir-ashiq/metaai-api/blob/main/CHANGELOG.md",
    },
    package_dir={"": "src"},
    packages=setuptools.find_packages(where="src"),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3 :: Only",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
    extras_require={
        "dev": ["check-manifest", "pytest", "black", "flake8"],
        "api": [
            "fastapi>=0.95.2,<0.96.0",
            "uvicorn[standard]>=0.22.0,<0.24.0",
            "python-multipart>=0.0.6",
            "python-dotenv>=1.0.0",
        ],
    },
    install_requires=[
        "requests>=2.31.0",
        "requests-html>=0.10.0",
        "lxml-html-clean>=0.1.1",
        "beautifulsoup4>=4.9.0",
    ],
)
