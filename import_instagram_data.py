#!/usr/bin/env python3
"""
Import Instagram JSON data into Supabase database
Reads instagram_ivyirelandx_data.json and populates the tables
"""
from supabase import create_client, Client
from dotenv import load_dotenv
from datetime import datetime
import os
import json

load_dotenv('.env.local')

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

def import_instagram_data(json_file):
    """Import Instagram data from JSON file to Supabase"""

    # Initialize Supabase client
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

    print(f"📂 Loading data from {json_file}...")

    # Load JSON data
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Filter for carousels only (type = 'Sidecar')
    carousels = [p for p in data if p.get('type') == 'Sidecar']

    print(f"🎠 Found {len(carousels)} carousels to import\n")

    imported_count = 0
    skipped_count = 0

    for i, post in enumerate(carousels, 1):
        post_id = post.get('id')
        username = post.get('ownerUsername')

        print(f"[{i}/{len(carousels)}] Processing carousel {post_id}...")

        try:
            # Check if carousel already exists
            existing = supabase.table('instagram_carousels').select('id').eq('post_id', post_id).execute()

            if existing.data:
                print(f"  ⏭️  Skipped (already exists)")
                skipped_count += 1
                continue

            # Parse timestamp
            posted_at = None
            if post.get('timestamp'):
                try:
                    posted_at = datetime.fromisoformat(post.get('timestamp').replace('Z', '+00:00')).isoformat()
                except:
                    pass

            # Count images in carousel
            child_posts = post.get('childPosts', [])
            image_count = sum(1 for child in child_posts if child.get('type') == 'Image')

            # Insert carousel
            carousel_data = {
                'post_id': post_id,
                'username': username,
                'caption': post.get('caption', ''),
                'likes_count': post.get('likesCount', 0),
                'comments_count': post.get('commentsCount', 0),
                'posted_at': posted_at,
                'image_count': image_count,
                'raw_data': post
            }

            result = supabase.table('instagram_carousels').insert(carousel_data).execute()
            carousel_db_id = result.data[0]['id']

            print(f"  ✓ Carousel created (DB ID: {carousel_db_id[:8]}...)")

            # Insert carousel images
            images_inserted = 0
            for order, child in enumerate(child_posts, 1):
                if child.get('type') == 'Image':
                    image_data = {
                        'carousel_id': carousel_db_id,
                        'image_url': child.get('displayUrl'),
                        'image_order': order,
                        'width': child.get('width'),
                        'height': child.get('height')
                    }

                    supabase.table('carousel_images').insert(image_data).execute()
                    images_inserted += 1

            print(f"  ✓ {images_inserted} images added")
            imported_count += 1

        except Exception as e:
            print(f"  ❌ Error: {e}")
            continue

    print(f"\n{'='*60}")
    print(f"✅ Import complete!")
    print(f"  - Imported: {imported_count} carousels")
    print(f"  - Skipped: {skipped_count} (already in database)")
    print(f"  - Total in database: {imported_count + skipped_count}")
    print(f"{'='*60}")

    return imported_count

if __name__ == "__main__":
    import sys

    # Get filename from command line or use default
    if len(sys.argv) > 1:
        filename = sys.argv[1]
    else:
        filename = 'instagram_ivyirelandx_data.json'

    import_instagram_data(filename)
