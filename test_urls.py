#!/usr/bin/env python3
"""Test if Instagram image URLs are still accessible"""
from supabase import create_client
from dotenv import load_dotenv
import os
import requests

load_dotenv('.env.local')

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Get first 3 image URLs
result = supabase.table('carousel_images').select('image_url').limit(3).execute()

print("Testing Instagram image URLs...\n")

for i, img in enumerate(result.data, 1):
    url = img['image_url']
    print(f"{i}. Testing URL: {url[:80]}...")

    try:
        response = requests.head(url, timeout=10)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print(f"   ✓ OK")
        else:
            print(f"   ✗ BROKEN")
    except Exception as e:
        print(f"   ✗ ERROR: {e}")
    print()
