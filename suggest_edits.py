#!/usr/bin/env python3
"""
Generate AI-safe variation suggestions for Instagram carousels using Grok-2-Vision
"""
import os
import json
import requests
import argparse
from dotenv import load_dotenv

load_dotenv('.env.local')

GROK_API_KEY = os.getenv('GROK_API_KEY')
GROK_API_URL = "https://api.x.ai/v1/chat/completions"

SYSTEM_PROMPT = """You are helping generate AI-safe variations of an Instagram influencer named Blondie.
We are recreating each carousel with only subtle stylistic changes so the resulting content feels inspired by the original but does not duplicate it.
Do NOT change the pose, body shape, skin tone, hairstyle, lighting, or composition.
ONLY propose small, realistic changes to:
- outfit color or outfit style
- background (location/environment)

The variations must remain believable and consistent.
Provide output ONLY in the JSON structure requested."""


def build_user_prompt(post_id, caption, image_urls):
    """Build the user prompt for Grok"""

    urls_list = "\n".join([f"{i+1}. {url}" for i, url in enumerate(image_urls)])

    prompt = f"""Here is a carousel from the source influencer account "Blondie."

Caption:
{caption}

Image URLs:
{urls_list}

Please output exactly this structure:

{{
  "post_id": "{post_id}",
  "original_caption": "{caption}",
  "persona_variants": [
    {{
      "persona": "A1",
      "background_change": "...",
      "outfit_change": "...",
      "why": "...",
      "caption_options": ["...", "...", "..."]
    }},
    {{
      "persona": "A2",
      "background_change": "...",
      "outfit_change": "...",
      "why": "...",
      "caption_options": ["...", "...", "..."]
    }},
    {{
      "persona": "B",
      "background_change": "...",
      "outfit_change": "...",
      "why": "...",
      "caption_options": ["...", "...", "..."]
    }}
  ]
}}

No additional text.
Fill everything with meaningful suggestions.
Keep changes subtle and believable.
Do NOT alter pose, identity, or physical features.
For each persona, provide 3 different caption options that match the background/outfit variation."""

    return prompt


def call_grok_vision(post_id, caption, image_urls):
    """Call Grok-2-Vision API with carousel data"""

    if not GROK_API_KEY:
        raise ValueError("GROK_API_KEY not found in environment")

    # Build messages with image URLs
    content = [{"type": "text", "text": build_user_prompt(post_id, caption, image_urls)}]

    # Add images to content
    for url in image_urls[:3]:  # Limit to first 3 images to avoid token limits
        content.append({
            "type": "image_url",
            "image_url": {"url": url}
        })

    payload = {
        "model": "grok-2-vision-1212",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": content}
        ],
        "temperature": 0.7,
        "max_tokens": 2000
    }

    headers = {
        "Authorization": f"Bearer {GROK_API_KEY}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(GROK_API_URL, json=payload, headers=headers, timeout=60)
        response.raise_for_status()

        result = response.json()
        message = result['choices'][0]['message']['content']

        # Try to parse JSON from response
        # Grok sometimes wraps in markdown code blocks
        if "```json" in message:
            message = message.split("```json")[1].split("```")[0].strip()
        elif "```" in message:
            message = message.split("```")[1].split("```")[0].strip()

        return json.loads(message)

    except requests.exceptions.RequestException as e:
        print(f"❌ API request failed: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response: {e.response.text[:500]}")
        return None
    except json.JSONDecodeError as e:
        print(f"❌ Failed to parse Grok response as JSON: {e}")
        print(f"Response was: {message[:500]}")
        return None


def process_carousels(input_file, output_file, limit=2):
    """Process carousels and generate variation suggestions"""

    print(f"📂 Loading scrape data from: {input_file}")

    with open(input_file, 'r') as f:
        data = json.load(f)

    # Filter for carousels only
    carousels = [p for p in data if p.get('type') == 'Sidecar']
    print(f"📊 Found {len(carousels)} carousels")

    if limit:
        carousels = carousels[:limit]
        print(f"🔬 Testing with first {limit} carousels")

    results = []

    for i, carousel in enumerate(carousels, 1):
        post_id = carousel.get('id')
        caption = carousel.get('caption', '')

        # Extract image URLs from child posts
        image_urls = []
        for child in carousel.get('childPosts', []):
            if child.get('type') == 'Image':
                image_urls.append(child.get('displayUrl'))

        # If no child posts, try main displayUrl
        if not image_urls and carousel.get('displayUrl'):
            image_urls = [carousel.get('displayUrl')]

        print(f"\n{'='*60}")
        print(f"Processing carousel {i}/{len(carousels)}")
        print(f"Post ID: {post_id}")
        print(f"Caption: {caption[:80]}...")
        print(f"Images: {len(image_urls)}")
        print(f"{'='*60}")

        # Call Grok API
        print("🤖 Calling Grok-2-Vision API...")
        suggestion = call_grok_vision(post_id, caption, image_urls)

        if suggestion:
            results.append(suggestion)
            print("✅ Got suggestions!")
        else:
            print("⚠️  Failed to get suggestions for this carousel")

    # Save results
    print(f"\n💾 Saving results to: {output_file}")
    os.makedirs(os.path.dirname(output_file) if os.path.dirname(output_file) else '.', exist_ok=True)

    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"✅ Done! Processed {len(results)}/{len(carousels)} carousels")
    print(f"📄 Output saved to: {output_file}")


def main():
    parser = argparse.ArgumentParser(description='Generate AI variation suggestions for Instagram carousels')
    parser.add_argument('--input', required=True, help='Input JSON file from scraper')
    parser.add_argument('--output', default='output/edit_suggestions_TEST.json', help='Output JSON file')
    parser.add_argument('--limit', type=int, default=2, help='Number of carousels to process (default: 2)')

    args = parser.parse_args()

    process_carousels(args.input, args.output, args.limit)


if __name__ == "__main__":
    main()
