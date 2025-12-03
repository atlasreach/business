#!/usr/bin/env python3
"""
Fetch Instagram profile data using Apify Instagram Scraper API
"""
import os
import json
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env.local')

APIFY_API_TOKEN = os.getenv('APIFY_API_TOKEN')
APIFY_API_URL = os.getenv('APIFY_API_URL')

def fetch_instagram_profile(username):
    """
    Fetch Instagram profile data using Apify API

    Args:
        username: Instagram username (without @)
    """
    profile_url = f"https://www.instagram.com/{username}/"

    # API request payload - MAXIMUM DATA COLLECTION
    payload = {
        # Target profile
        "directUrls": [profile_url],

        # Results configuration
        "resultsType": "posts",
        "resultsLimit": 300,
        "searchType": "user",
        "searchLimit": 1,

        # Profile data
        "addParentData": True,

        # Comments - COMPREHENSIVE
        "scrapePostComments": True,
        "maxComments": 1000,
        "scrapeCommentLikes": True,
        "scrapeCommentReplies": True,

        # Additional metadata
        "scrapeTaggedUsers": True,
        "scrapeHashtags": True,
        "scrapeMentions": True,

        # Video/Reel specific - ENHANCED
        "includeVideoDetails": True,
        "scrapeReels": True,                 # Explicitly scrape reels
        "scrapeVideos": True,                # Scrape videos

        # Performance
        "maxRequestRetries": 5
    }

    # Headers
    headers = {
        'Content-Type': 'application/json'
    }

    # Full URL with token
    url = f"{APIFY_API_URL}?token={APIFY_API_TOKEN}"

    print(f"🔍 Fetching COMPREHENSIVE Instagram data for @{username}...")
    print(f"📍 Profile URL: {profile_url}")
    print(f"📦 Fetching: Up to 300 posts + 1000 comments per post")
    print(f"⏳ Please wait, this may take 2-5 MINUTES due to comment scraping...")

    try:
        # Make API request (long timeout for comprehensive scraping)
        response = requests.post(url, json=payload, headers=headers, timeout=600)
        response.raise_for_status()

        # Parse response
        data = response.json()

        # FILTER: Only keep posts OWNED by target user (not tagged/co-authored)
        if isinstance(data, list):
            original_count = len(data)
            data = [p for p in data if p.get('ownerUsername') == username]
            filtered_count = original_count - len(data)
            if filtered_count > 0:
                print(f"\n🗑️  Filtered out {filtered_count} tagged/co-authored posts")

        # Save results
        output_file = f"instagram_{username}_data.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        print(f"\n✅ Success! Data saved to: {output_file}")
        print(f"📊 Total items fetched: {len(data) if isinstance(data, list) else 1}")

        # Print comprehensive summary
        if isinstance(data, list) and len(data) > 0:
            print(f"\n📋 Comprehensive Data Summary:")

            # Profile info
            first_item = data[0]
            print(f"   Profile: @{first_item.get('ownerUsername', 'Unknown')}")
            if 'followersCount' in first_item:
                print(f"   - Followers: {first_item.get('followersCount', 0):,}")
            if 'followsCount' in first_item:
                print(f"   - Following: {first_item.get('followsCount', 0):,}")
            if 'postsCount' in first_item:
                print(f"   - Total Posts: {first_item.get('postsCount', 0):,}")

            # Posts fetched
            print(f"\n   Posts Fetched: {len(data)}")

            # Engagement stats
            total_likes = sum(p.get('likesCount', 0) for p in data)
            total_comments_count = sum(p.get('commentsCount', 0) for p in data)
            comments_fetched = sum(len(p.get('latestComments', [])) for p in data)
            videos = [p for p in data if p.get('videoViewCount')]
            total_views = sum(p.get('videoViewCount', 0) for p in videos)

            print(f"   - Total Likes: {total_likes:,}")
            print(f"   - Total Comments (reported): {total_comments_count:,}")
            print(f"   - Comments Actually Fetched: {comments_fetched:,}")
            if videos:
                print(f"   - Videos with Views: {len(videos)}")
                print(f"   - Total Video Views: {total_views:,}")

        return data

    except requests.exceptions.Timeout:
        print("\n❌ Error: Request timed out. The API might be taking longer than expected.")
        print("   Try running the script again or increase the timeout value.")
        return None

    except requests.exceptions.RequestException as e:
        print(f"\n❌ Error making API request: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"   Response status: {e.response.status_code}")
            print(f"   Response body: {e.response.text[:500]}")
        return None

    except json.JSONDecodeError as e:
        print(f"\n❌ Error parsing JSON response: {e}")
        return None

    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        return None

if __name__ == "__main__":
    # Fetch data for madison.moorgan
    username = "madison.moorgan"
    result = fetch_instagram_profile(username)

    if result:
        print(f"\n🎉 Done! You can now view the data in instagram_{username}_data.json")
    else:
        print("\n⚠️  Failed to fetch data. Please check the error messages above.")
