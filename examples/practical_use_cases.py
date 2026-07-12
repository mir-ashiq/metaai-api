"""
Practical Example: Product Photography Enhancement Pipeline

⚠️ NOTE: This example uses chat/analysis features which are currently unavailable.
For working examples, see:
- simple_example.py - Image/video generation
- image_upload_example.py - Image upload
- video_generation.py - Video generation

This example demonstrates the intended workflow (when chat becomes available):
1. Upload a product photo
2. Analyze the image (requires chat - currently unavailable)
3. Generate improved versions in different styles
4. Create promotional videos
"""

from typing import Dict, Any
from metaai_api import MetaAI
import json


def product_photography_pipeline():
    """
    Complete pipeline for enhancing product photography using Meta AI.
    
    Note: Image analysis via chat is currently unavailable.
    Use generate_image_new() and generate_video_new() for generation only.
    """
    
    print("=" * 70)
    print("Product Photography Enhancement Pipeline")
    print("=" * 70)
    
    # Initialize with only 3 required cookies
    ai = MetaAI(cookies={
        "datr": "your_datr_cookie",
        "abra_sess": "your_abra_sess_cookie",
        "ecto_1_sess": "your_ecto_1_sess_cookie"
    })
    
    # Step 1: Upload product image
    print("\n[Step 1] Uploading product image...")
    product_image = "product_photo.jpg"
    upload_result = ai.upload_image(product_image)
    
    if not upload_result["success"]:
        print(f"✗ Upload failed: {upload_result['error']}")
        return
    
    media_id = upload_result["media_id"]
    print(f"✓ Product image uploaded: {media_id}")
    
    # Step 2: Get AI analysis of the product
    print("\n[Step 2] Analyzing product image...")
    analysis = cast(Dict[str, Any], ai.prompt(
        message="Describe this product in detail. What is it, what are its key features, and what mood does it convey?",
        media_ids=[media_id],
        stream=False
    ))
    print(f"✓ Analysis: {analysis['message'][:200]}...")
    
    # Step 3: Generate lifestyle variations
    print("\n[Step 3] Generating lifestyle variations...")
    
    styles = [
        "modern minimalist lifestyle setting",
        "cozy home environment",
        "professional studio lighting",
        "outdoor natural setting"
    ]
    
    generated_images = []
    
    for style in styles:
        print(f"\n  Generating: {style}...")
        response = cast(Dict[str, Any], ai.prompt(
            message=f"Create a similar product image in a {style}",
            media_ids=[media_id],
            stream=False
        ))
        
        if response.get('media'):
            for media in response['media']:
                if media['type'] == 'IMAGE':
                    generated_images.append({
                        'style': style,
                        'url': media['url']
                    })
                    print(f"  ✓ Generated: {media['url']}")
    
    print(f"\n✓ Generated {len(generated_images)} variations")
    
    # Step 4: Create promotional videos
    print("\n[Step 4] Creating promotional videos...")
    
    video_prompts = [
        "generate video of this product rotating 360 degrees",
        "generate video of this product with zoom in effect",
        "generate video showcasing this product with elegant movement"
    ]
    
    generated_videos = []
    
    for prompt in video_prompts:
        print(f"\n  Creating: {prompt}...")
        response = cast(Dict[str, Any], ai.prompt(
            message=prompt,
            media_ids=[media_id],
            stream=False
        ))
        
        if response.get('media'):
            for media in response['media']:
                if media['type'] == 'VIDEO':
                    generated_videos.append({
                        'prompt': prompt,
                        'url': media['url']
                    })
                    print(f"  ✓ Video created: {media['url']}")
    
    print(f"\n✓ Generated {len(generated_videos)} videos")
    
    # Step 5: Summary report
    print("\n" + "=" * 70)
    print("Pipeline Complete - Summary Report")
    print("=" * 70)
    
    report = {
        "original_image": product_image,
        "media_id": media_id,
        "analysis": analysis['message'],
        "generated_images": generated_images,
        "generated_videos": generated_videos
    }
    
    print(f"\nOriginal Image: {product_image}")
    print(f"Media ID: {media_id}")
    print(f"\nGenerated Assets:")
    print(f"  - {len(generated_images)} image variations")
    print(f"  - {len(generated_videos)} promotional videos")
    
    # Save report
    with open("product_enhancement_report.json", "w") as f:
        json.dump(report, f, indent=2)
    print(f"\n✓ Report saved to: product_enhancement_report.json")
    
    return report


def batch_product_processing():
    """
    Process multiple products in batch.
    """
    
    print("\n" + "=" * 70)
    print("Batch Product Processing")
    print("=" * 70)
    
    ai = MetaAI(cookies={
        "datr": "your_datr_cookie",
        "abra_sess": "your_abra_sess_cookie",
    })
    
    products = [
        "product1.jpg",
        "product2.jpg",
        "product3.jpg"
    ]
    
    results = []
    
    for i, product_image in enumerate(products, 1):
        print(f"\n[Product {i}/{len(products)}] Processing {product_image}...")
        
        # Upload
        upload_result = ai.upload_image(product_image)
        if not upload_result["success"]:
            print(f"  ✗ Failed: {upload_result['error']}")
            continue
        
        media_id = upload_result["media_id"]
        print(f"  ✓ Uploaded: {media_id}")
        
        # Quick analysis
        analysis = cast(Dict[str, Any], ai.prompt(
            message="Briefly describe this product in one sentence",
            media_ids=[media_id],
            stream=False
        ))
        
        # Generate one variation
        variation = cast(Dict[str, Any], ai.prompt(
            message="Create a similar product image in professional studio lighting",
            media_ids=[media_id],
            stream=False
        ))
        
        results.append({
            "original": product_image,
            "media_id": media_id,
            "description": analysis['message'],
            "variation_media": variation.get('media', [])
        })
        
        print(f"  ✓ Description: {analysis['message'][:80]}...")
    
    print(f"\n✓ Processed {len(results)}/{len(products)} products")
    
    # Save batch report
    with open("batch_processing_report.json", "w") as f:
        json.dump(results, f, indent=2)
    print(f"✓ Batch report saved")
    
    return results


def interactive_product_refinement():
    """
    Interactive refinement workflow.
    """
    
    print("\n" + "=" * 70)
    print("Interactive Product Refinement")
    print("=" * 70)
    
    ai = MetaAI(cookies={
        "datr": "your_datr_cookie",
        "abra_sess": "your_abra_sess_cookie",
    })
    
    # Upload base image
    print("\nUpload base product image...")
    upload_result = ai.upload_image("product_base.jpg")
    
    if not upload_result["success"]:
        print(f"✗ Upload failed: {upload_result['error']}")
        return
    
    current_media_id = upload_result["media_id"]
    print(f"✓ Base image uploaded: {current_media_id}")
    
    # Iterative refinement
    refinements = [
        "Improve the lighting to be more dramatic",
        "Add a subtle shadow effect",
        "Make the colors more vibrant",
        "Add a slight blur to the background"
    ]
    
    print("\nApplying refinements...")
    for i, refinement in enumerate(refinements, 1):
        print(f"\n[Refinement {i}] {refinement}")
        
        response = cast(Dict[str, Any], ai.prompt(
            message=f"Using this image, {refinement.lower()}",
            media_ids=[current_media_id],
            new_conversation=False,  # Keep context
            stream=False
        ))
        
        if response.get('media'):
            print(f"  ✓ Refined version generated")
            # In a real scenario, you'd download this image and upload it again
            # to get a new media_id for further refinement
            # current_media_id = new_upload_result["media_id"]
        else:
            print(f"  Note: {response['message'][:100]}...")
    
    print("\n✓ Refinement process complete")


if __name__ == "__main__":
    print("\n")
    print("╔" + "═" * 68 + "╗")
    print("║" + " " * 15 + "Practical Use Case Examples" + " " * 25 + "║")
    print("╚" + "═" * 68 + "╝")
    
    print("\nChoose an example to run:")
    print("1. Complete Product Photography Pipeline")
    print("2. Batch Product Processing")
    print("3. Interactive Product Refinement")
    print("\nNote: Update cookies before running!")
    
    # Uncomment to run:
    # product_photography_pipeline()
    # batch_product_processing()
    # interactive_product_refinement()
    
    print("\n" + "=" * 70)
    print("Example Code Structure")
    print("=" * 70)
    print("""
These examples demonstrate:

1. Product Photography Pipeline
   - Upload → Analyze → Generate variations → Create videos
   - Multiple style variations
   - Automated video creation
   - Report generation

2. Batch Processing
   - Process multiple products efficiently
   - Consistent workflow across products
   - Structured output

3. Interactive Refinement
   - Iterative improvement workflow
   - Context preservation
   - Step-by-step enhancements

Key Patterns:
✓ Always check upload success
✓ Store media_ids for reuse
✓ Use specific, descriptive prompts
✓ Handle media response properly
✓ Save results for later use
    """)
