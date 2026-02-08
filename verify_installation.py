"""
SDK Verification Test - No API Calls
Just verifies the SDK is properly installed and structured
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

print("\n" + "="*70)
print("  META AI SDK - INSTALLATION VERIFICATION")
print("="*70 + "\n")

# Test 1: Package metadata
print("1. Package Information:")
print("-" * 70)
try:
    import metaai_api
    print(f"   ✅ Package imported successfully")
    print(f"   📦 Version: {metaai_api.__version__}")
    print(f"   👤 Author: {metaai_api.__author__}")
    print(f"   📄 License: {metaai_api.__license__}")
    print(f"   🔗 URL: {metaai_api.__url__}")
except Exception as e:
    print(f"   ❌ Failed: {e}")

# Test 2: Core dependencies
print("\n2. Core Dependencies:")
print("-" * 70)
deps = {
    'requests': 'HTTP library',
    'requests_html': 'HTML parsing',
    'bs4': 'BeautifulSoup4',
    'lxml_html_clean': 'HTML cleaner'
}

all_deps_ok = True
for module, desc in deps.items():
    try:
        __import__(module)
        print(f"   ✅ {module:20} ({desc})")
    except ImportError:
        print(f"   ❌ {module:20} ({desc}) - NOT INSTALLED")
        all_deps_ok = False

# Test 3: Main classes availability
print("\n3. Main SDK Classes:")
print("-" * 70)
try:
    from metaai_api import MetaAI, VideoGenerator, ImageUploader
    print(f"   ✅ MetaAI class")
    print(f"   ✅ VideoGenerator class")
    print(f"   ✅ ImageUploader class")
    classes_ok = True
except Exception as e:
    print(f"   ❌ Failed to import classes: {e}")
    classes_ok = False

# Test 4: File structure
print("\n4. Core Files:")
print("-" * 70)
src_dir = os.path.join('src', 'metaai_api')
core_files = [
    '__init__.py',
    'main.py',
    'client.py', 
    'video_generation.py',
    'image_upload.py',
    'api_server.py',
    'utils.py'
]

files_ok = True
for file in core_files:
    path = os.path.join(src_dir, file)
    if os.path.exists(path):
        size = os.path.getsize(path)
        print(f"   ✅ {file:25} ({size:>6,} bytes)")
    else:
        print(f"   ❌ {file:25} (MISSING)")
        files_ok = False

# Test 5: Examples
print("\n5. Example Scripts:")
print("-" * 70)
examples_dir = 'examples'
if os.path.exists(examples_dir):
    examples = [f for f in os.listdir(examples_dir) if f.endswith('.py')]
    print(f"   ✅ Found {len(examples)} example scripts:")
    for ex in examples[:5]:  # Show first 5
        print(f"      • {ex}")
    if len(examples) > 5:
        print(f"      ... and {len(examples) - 5} more")
else:
    print(f"   ⚠️  Examples directory not found")

# Summary
print("\n" + "="*70)
print("  VERIFICATION SUMMARY")
print("="*70 + "\n")

if all_deps_ok and classes_ok and files_ok:
    print("  ✅ SDK IS PROPERLY INSTALLED AND READY TO USE!\n")
    print("  Available Features:")
    print("     • Chat with Meta AI (Llama 3)")
    print("     • Generate AI images")
    print("     • Create AI videos")
    print("     • Upload and analyze images")
    print("\n  Quick Start:")
    print("     from metaai_api import MetaAI")
    print("     ai = MetaAI()")
    print("     response = ai.prompt('Hello!')")
    print("\n  See examples/ directory for more usage examples.")
elif classes_ok and files_ok:
    print("  ⚠️  SDK INSTALLED BUT MISSING SOME DEPENDENCIES")
    print("     Run: pip install -r requirements.txt")
else:
    print("  ❌ SDK INSTALLATION INCOMPLETE")
    print("     Please reinstall: pip install -e .")

print("\n" + "="*70 + "\n")

# API Testing Note  
print("📝 NOTE: API functionality testing requires:")
print("   - Internet connection")
print("   - Valid cookies from meta.ai (for some features)")
print("   - Ability to handle Meta AI's challenge pages")
print("\n   For API testing, try running:")
print("   python examples/simple_example.py\n")
