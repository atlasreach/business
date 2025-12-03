#!/usr/bin/env python3
"""
Download Instagram images and upload them to Supabase Storage
Updates the database with new Supabase Storage URLs
"""
from supabase import create_client, Client
from dotenv import load_dotenv
import os
import requests
from io import BytesIO
import time

load_dotenv('.env.local')

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

STORAGE_BUCKET = 'carousel-images'

def create_storage_bucket():
    """Create storage bucket if it doesn't exist"""
    try:
        # Try to create bucket
        supabase.storage.create_bucket(
            STORAGE_BUCKET,
            options={
                'public': True,
                'fileSizeLimit': 10485760  # 10MB
            }
        )
        print(f"✓ Created storage bucket: {STORAGE_BUCKET}")
    except Exception as e:
        if 'already exists' in str(e).lower():
            print(f"✓ Storage bucket already exists: {STORAGE_BUCKET}")
        else:
            print(f"⚠️  Bucket creation note: {e}")

def download_and_upload_images():
    """Download Instagram images and upload to Supabase Storage"""

    print("🔧 Starting image download and upload process...\n")

    # Create bucket first
    create_storage_bucket()
    print()

    # Get all images that don't have local_path set
    result = supabase.table('carousel_images').select('*').is_('local_path', 'null').execute()
    images = result.data

    print(f"📸 Found {len(images)} images to process\n")

    success_count = 0
    error_count = 0

    for i, image in enumerate(images, 1):
        image_id = image['id']
        image_url = image['image_url']
        carousel_id = image['carousel_id']
        image_order = image['image_order']

        print(f"[{i}/{len(images)}] Processing image {image_id[:8]}...")

        try:
            # Download image from Instagram
            print(f"  ⬇️  Downloading from Instagram...")
            response = requests.get(image_url, timeout=30)
            response.raise_for_status()

            # Get file extension from URL or default to jpg
            if '.jpg' in image_url:
                ext = 'jpg'
            elif '.png' in image_url:
                ext = 'png'
            else:
                ext = 'jpg'

            # Create filename
            filename = f"{carousel_id}/{image_order}.{ext}"

            # Upload to Supabase Storage
            print(f"  ⬆️  Uploading to Supabase Storage...")
            supabase.storage.from_(STORAGE_BUCKET).upload(
                filename,
                response.content,
                file_options={
                    'content-type': f'image/{ext}',
                    'upsert': 'true'
                }
            )

            # Get public URL
            public_url = supabase.storage.from_(STORAGE_BUCKET).get_public_url(filename)

            # Update database with new URL
            supabase.table('carousel_images').update({
                'local_path': public_url
            }).eq('id', image_id).execute()

            print(f"  ✅ Success! Stored at: {filename}")
            success_count += 1

            # Small delay to avoid rate limiting
            time.sleep(0.5)

        except Exception as e:
            print(f"  ❌ Error: {e}")
            error_count += 1

        print()

    print(f"{'='*60}")
    print(f"✅ Upload complete!")
    print(f"  - Success: {success_count}")
    print(f"  - Errors: {error_count}")
    print(f"{'='*60}")

    return success_count

if __name__ == "__main__":
    download_and_upload_images()
