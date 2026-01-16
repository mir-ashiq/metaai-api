"""
Comprehensive debug test for async video generation with full tracing.
This script will show EXACTLY what's happening at each step.
"""

import requests
import json
import time
import logging

# Enable detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - [%(levelname)s] %(message)s',
)

logger = logging.getLogger(__name__)

API_URL = "http://localhost:8000"
IMAGE_PATH = r"C:\Users\spike\Downloads\meta-ai-api-main\ChatGPT Image Jan 14, 2026, 06_59_02 PM.png"

def test_async_video_generation():
    """Test async video generation with comprehensive debugging."""
    
    print("\n" + "=" * 80)
    print("COMPREHENSIVE DEBUG TEST - ASYNC VIDEO GENERATION")
    print("=" * 80)
    
    # Step 1: Upload image
    logger.info("STEP 1: Uploading image...")
    with open(IMAGE_PATH, 'rb') as f:
        upload_response = requests.post(f"{API_URL}/upload", files={'file': f})
    
    if upload_response.status_code != 200:
        logger.error(f"Upload failed: {upload_response.text}")
        return
    
    upload_result = upload_response.json()
    media_id = upload_result['media_id']
    file_size = upload_result['file_size']
    mime_type = upload_result['mime_type']
    
    logger.info(f"✓ Upload successful")
    logger.info(f"  Media ID: {media_id}")
    logger.info(f"  File Size: {file_size}")
    logger.info(f"  MIME Type: {mime_type}")
    
    # Step 2: Submit async video job
    logger.info("\nSTEP 2: Submitting async video job...")
    
    payload = {
        "prompt": "generate a video with cinematic zoom effect",
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
    
    logger.debug(f"Payload: {json.dumps(payload, indent=2)}")
    
    job_response = requests.post(
        f"{API_URL}/video/async",
        headers={"Content-Type": "application/json"},
        data=json.dumps(payload)
    )
    
    if job_response.status_code != 200:
        logger.error(f"Job submission failed: {job_response.text}")
        return
    
    job_result = job_response.json()
    job_id = job_result['job_id']
    initial_status = job_result['status']
    
    logger.info(f"✓ Job submitted")
    logger.info(f"  Job ID: {job_id}")
    logger.info(f"  Initial Status: {initial_status}")
    
    # Step 3: Poll job status
    logger.info("\nSTEP 3: Polling job status...")
    
    max_polls = 20
    poll_interval = 3
    
    for poll_num in range(1, max_polls + 1):
        time.sleep(poll_interval)
        
        logger.info(f"\n--- POLL #{poll_num}/{max_polls} ---")
        
        status_response = requests.get(f"{API_URL}/video/jobs/{job_id}")
        
        if status_response.status_code != 200:
            logger.error(f"Failed to get job status: {status_response.text}")
            break
        
        job_status = status_response.json()
        current_status = job_status['status']
        
        logger.info(f"Status: {current_status}")
        logger.info(f"Created: {job_status['created_at']}")
        logger.info(f"Updated: {job_status['updated_at']}")
        
        if current_status == 'succeeded':
            logger.info("\n✓✓✓ JOB SUCCEEDED ✓✓✓")
            result = job_status.get('result', {})
            
            logger.info("\nResult Details:")
            logger.info(f"  Success Flag: {result.get('success')}")
            logger.info(f"  Conversation ID: {result.get('conversation_id')}")
            logger.info(f"  Prompt: {result.get('prompt')}")
            logger.info(f"  Timestamp: {result.get('timestamp')}")
            
            video_urls = result.get('video_urls', [])
            logger.info(f"\n  Video URLs Count: {len(video_urls)}")
            
            if video_urls:
                for idx, url in enumerate(video_urls, 1):
                    logger.info(f"\n  VIDEO {idx}:")
                    logger.info(f"    Full URL: {url}")
                    logger.info(f"    Length: {len(url)} characters")
                    logger.info(f"    Has .mp4: {'.mp4' in url}")
                    logger.info(f"    Has fbcdn: {'fbcdn' in url}")
                    logger.info(f"    Has /v/: {'/v/' in url}")
                    logger.info(f"    Has /t6/: {'/t6/' in url}")
            else:
                logger.warning("\n  ⚠ NO VIDEO URLs FOUND!")
                logger.warning("  This means URL extraction failed even though generation succeeded")
            
            logger.debug(f"\nFull Job Status JSON:\n{json.dumps(job_status, indent=2)}")
            break
            
        elif current_status == 'failed':
            logger.error("\n✗✗✗ JOB FAILED ✗✗✗")
            error = job_status.get('error', 'Unknown error')
            logger.error(f"Error: {error}")
            logger.debug(f"\nFull Job Status JSON:\n{json.dumps(job_status, indent=2)}")
            break
            
        elif current_status in ['pending', 'running']:
            logger.info(f"⏳ Job still {current_status}... waiting {poll_interval}s")
        else:
            logger.warning(f"Unknown status: {current_status}")
    else:
        logger.warning(f"\n⚠ Reached max polls ({max_polls}). Job may still be processing.")
        logger.info(f"Check manually: GET {API_URL}/video/jobs/{job_id}")
    
    print("\n" + "=" * 80)
    print("DEBUG TEST COMPLETE")
    print("=" * 80)
    print("\nCheck meta_ai_debug.log for server-side logs")
    print()

if __name__ == "__main__":
    try:
        test_async_video_generation()
    except KeyboardInterrupt:
        logger.info("\n\nTest interrupted by user")
    except Exception as e:
        logger.error(f"\n\nTest failed with exception: {e}", exc_info=True)
