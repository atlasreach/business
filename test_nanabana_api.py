#!/usr/bin/env python3
"""
Test WaveSpeed NanaBanana Pro API with a sample image
"""
from dotenv import load_dotenv
from supabase import create_client
import os
import requests
import json
import time

load_dotenv('.env.local')

WAVESPEED_API_KEY = os.getenv('WAVESPEED_API_KEY')
WAVESPEED_API_URL = os.getenv('WAVESPEED_API_URL')

# Get one test image from Supabase
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

print("🧪 Testing WaveSpeed NanaBanana Pro API\n")
print("="*60)

# Get a test image
result = supabase.table('carousel_images').select('*').not_.is_('local_path', 'null').limit(1).execute()
if not result.data:
    print("❌ No images found in database")
    exit(1)

test_image = result.data[0]
image_url = test_image['local_path']

print(f"Test Image URL: {image_url[:80]}...")
print(f"API Endpoint: {WAVESPEED_API_URL}")
print("="*60)

# Test prompt
test_prompt = "A woman wearing a red dress, standing on a beach at sunset with palm trees in the background"

print(f"\nTest Prompt: {test_prompt}\n")

# Build request payload (with corrected structure)
payload = {
    "prompt": test_prompt,
    "images": [image_url],
    "aspect_ratio": "1:1",
    "resolution": "1k",  # Using 1k for faster/cheaper testing
    "output_format": "jpeg",
    "enable_sync_mode": True,  # IMPORTANT: Wait for completion
    "enable_base64_output": False
}

headers = {
    "Authorization": f"Bearer {WAVESPEED_API_KEY}",
    "Content-Type": "application/json"
}

print("📤 Sending request to NanaBanana Pro API...")
print(f"Payload: {json.dumps(payload, indent=2)}\n")

try:
    # Make API request
    response = requests.post(
        WAVESPEED_API_URL,
        json=payload,
        headers=headers,
        timeout=120  # 2 minutes timeout for sync mode
    )

    print(f"Response Status Code: {response.status_code}")
    print(f"Response Headers: {dict(response.headers)}\n")

    response.raise_for_status()

    result = response.json()

    print("="*60)
    print("📥 API Response:")
    print(json.dumps(result, indent=2))
    print("="*60)

    # Parse response
    if 'data' in result:
        data = result['data']

        print("\n✅ Request successful!")
        print(f"Status: {data.get('status')}")
        print(f"Request ID: {data.get('id')}")

        if 'outputs' in data and data['outputs']:
            print(f"\n🖼️  Generated Image URL:")
            print(data['outputs'][0])

            # Check if NSFW
            if data.get('has_nsfw_contents'):
                print(f"\n⚠️  NSFW Detection: {data.get('has_nsfw_contents')}")

            # Show timing
            if 'timings' in data:
                inference_time = data['timings'].get('inference', 0) / 1000
                print(f"\n⏱️  Processing time: {inference_time:.2f} seconds")
        else:
            print(f"\n⚠️  No output images in response")
            print(f"Full data: {data}")
    else:
        print("\n❌ Unexpected response format:")
        print(json.dumps(result, indent=2))

except requests.exceptions.Timeout:
    print("\n❌ Request timed out after 120 seconds")
    print("The API may be taking longer than expected or sync mode may not be working")

except requests.exceptions.HTTPError as e:
    print(f"\n❌ HTTP Error: {e}")
    print(f"Response text: {response.text}")

except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
