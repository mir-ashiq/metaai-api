"""Quick test for video generation with fixed URL extraction."""
import requests
import json
import time

API_URL = "http://localhost:8000"
IMAGE_PATH = r"C:\Users\spike\Downloads\meta-ai-api-main\ChatGPT Image Jan 14, 2026, 06_59_02 PM.png"

print("\n" + "="*80)
print("QUICK VIDEO GENERATION TEST")
print("="*80)

# Step 1: Upload image
print("\n[1/3] Uploading image...")
with open(IMAGE_PATH, 'rb') as f:
    upload_response = requests.post(f"{API_URL}/upload", files={'file': f})

if upload_response.status_code != 200:
    print(f"✗ Upload failed: {upload_response.text}")
    exit(1)

upload_result = upload_response.json()
media_id = upload_result['media_id']
file_size = upload_result['file_size']
mime_type = upload_result['mime_type']

print(f"✓ Uploaded - Media ID: {media_id}")

# Step 2: Submit async video job
print("\n[2/3] Submitting async video job...")

payload = {
    "prompt": "generate a cinematic video with smooth camera movement",
    "media_ids": [media_id],
    "attachment_metadata": {
        "file_size": file_size,
        "mime_type": mime_type
    },
    "wait_before_poll": 10,
    "max_attempts": 30,
    "wait_seconds": 5,
    "verbose": False
}

job_response = requests.post(
    f"{API_URL}/video/async",
    headers={"Content-Type": "application/json"},
    data=json.dumps(payload)
)

if job_response.status_code != 200:
    print(f"✗ Job submission failed: {job_response.text}")
    exit(1)

job_result = job_response.json()
job_id = job_result['job_id']
print(f"✓ Job submitted - Job ID: {job_id}")

# Step 3: Poll job status
print("\n[3/3] Polling job status...")
print(f"Will poll up to 20 times (every 3 seconds)...\n")

max_polls = 20
for poll_num in range(1, max_polls + 1):
    time.sleep(3)
    
    print(f"Poll #{poll_num}/{max_polls}...", end=" ")
    
    status_response = requests.get(f"{API_URL}/video/jobs/{job_id}")
    
    if status_response.status_code != 200:
        print(f"✗ Failed to get status")
        continue
    
    job_status = status_response.json()
    current_status = job_status['status']
    
    print(f"Status: {current_status}")
    
    if current_status == 'succeeded':
        print("\n" + "="*80)
        print("✓✓✓ JOB SUCCEEDED ✓✓✓")
        print("="*80)
        
        result = job_status.get('result', {})
        video_urls = result.get('video_urls', [])
        
        print(f"\nSuccess Flag: {result.get('success')}")
        print(f"Conversation ID: {result.get('conversation_id')}")
        print(f"Video URLs Count: {len(video_urls)}")
        
        if video_urls:
            print(f"\n✓✓✓ FOUND {len(video_urls)} VIDEO URL(S)! ✓✓✓")
            for idx, url in enumerate(video_urls, 1):
                print(f"\nVideo {idx}:")
                print(f"  URL: {url}")
                print(f"  Length: {len(url)} chars")
                print(f"  Has .mp4: {'.mp4' in url}")
                print(f"  Has fbcdn: {'fbcdn' in url}")
        else:
            print("\n✗✗✗ NO VIDEO URLs FOUND ✗✗✗")
            print("Check meta_ai_debug.log for extraction details")
        
        print(f"\nFull Result:")
        print(json.dumps(job_status, indent=2))
        break
        
    elif current_status == 'failed':
        print("\n" + "="*80)
        print("✗✗✗ JOB FAILED ✗✗✗")
        print("="*80)
        error = job_status.get('error', 'Unknown error')
        print(f"Error: {error}")
        print(f"\nFull Result:")
        print(json.dumps(job_status, indent=2))
        break
else:
    print(f"\n⚠ Reached max polls. Check manually: GET {API_URL}/video/jobs/{job_id}")

print("\n" + "="*80)
print("TEST COMPLETE - Check meta_ai_debug.log for detailed extraction logs")
print("="*80)
