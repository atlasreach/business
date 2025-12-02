# Instagram Scraper API - Complete Data Structures

Based on the examples provided, the Apify Instagram scraper returns 3 different types of data:

## 1. PROFILE Data
```json
{
  "id": "6622284809",
  "username": "avengers",
  "fullName": "Avengers: Endgame",
  "biography": "Marvel Studios' \"Avengers​: Endgame" is now playing in theaters.",
  "externalUrl": "http://www.fandango.com/avengersendgame",
  "externalUrlShimmed": "https://l.instagram.com/...",
  "followersCount": 8212505,
  "followsCount": 4,
  "hasChannel": false,
  "highlightReelCount": 3,
  "isBusinessAccount": true,
  "joinedRecently": false,
  "businessCategoryName": "Content & Apps",
  "private": false,
  "verified": true,
  "profilePicUrl": "...",
  "profilePicUrlHD": "...",
  "facebookPage": null,
  "igtvVideoCount": 5,
  "postsCount": 274,
  "latestIgtvVideos": [...],
  "latestPosts": [...],
  "following": [],
  "followedBy": []
}
```

### Key Profile Fields We're Missing:
- ✅ **followersCount** - Follower count
- ✅ **followsCount** - Following count
- ✅ **biography** - Bio text
- ✅ **externalUrl** - Link in bio
- ✅ **postsCount** - Total posts
- ✅ **verified** - Verification status
- ✅ **isBusinessAccount** - Business account flag
- ✅ **businessCategoryName** - Business category
- ✅ **highlightReelCount** - Story highlights count
- ✅ **igtvVideoCount** - IGTV count
- ✅ **profilePicUrlHD** - High-res profile pic

---

## 2. POST Data (with Video Views!)
```json
{
  "type": "Video",
  "shortCode": "Bw7jACTn3tC",
  "caption": "...",
  "commentsCount": 1045,
  "dimensionsHeight": 750,
  "dimensionsWidth": 750,
  "displayUrl": "...",
  "likesCount": 142707,
  "videoViewCount": 482810,  // ⭐ THIS IS WHAT WE'RE MISSING!
  "timestamp": "2019-05-01T18:44:12.000Z",
  "locationName": null
}
```

### Key Post Fields We're Missing:
- ✅ **videoViewCount** - Video/Reel view count (CRITICAL!)
- ✅ **videoDuration** - Video length in seconds
- ✅ **locationName** - Location tag

---

## 3. COMMENT Data
```json
{
  "id": "17900515570488496",
  "postId": "BwrsO1Bho2N",
  "text": "When is Tesla going to make boats?...",
  "position": 1,
  "timestamp": "2020-06-07T12:54:20.000Z",
  "ownerId": "5319127183",
  "ownerIsVerified": false,
  "ownerUsername": "mauricepaoletti",
  "ownerProfilePicUrl": "..."
}
```

### Comment Fields:
- postId
- text
- position (order)
- timestamp
- owner info (id, username, verified, profile pic)

---

## Current API Issues

### What We Got (18 posts from @ivyirelandx):
- ✅ Basic post data
- ✅ Images/carousels/videos
- ✅ Likes count
- ✅ Comments count
- ✅ Latest comments (nested)
- ✅ Tagged users
- ❌ **NO videoViewCount** (critical missing data!)
- ❌ **NO profile metadata** (followers, bio, etc.)
- ❌ **Only got 18 posts** (might have way more)

### Why Only 18 Posts?
The API might be limited by:
1. Default result limit (need to set `resultsLimit` parameter)
2. Rate limiting
3. Scraping depth configuration
4. Need different `resultsType` parameter

---

## Required API Parameters to Test

```json
{
  "directUrls": ["https://www.instagram.com/ivyirelandx/"],
  "resultsType": "posts",          // or "details" for profile data?
  "resultsLimit": 100,              // increase post limit
  "searchType": "user",
  "searchLimit": 100,
  "includeVideoDetails": true,      // might enable videoViewCount
  "scrapePostComments": true,       // get all comments
  "scrapePostLikes": false,         // might slow things down
  "maxRequestRetries": 3
}
```

---

## Database Schema Updates Needed

### Add to `profiles` table:
```sql
followers_count INTEGER
following_count INTEGER
biography TEXT
external_url TEXT
posts_count INTEGER
is_verified BOOLEAN
is_business_account BOOLEAN
business_category_name TEXT
highlight_reel_count INTEGER
igtv_video_count INTEGER
profile_pic_url_hd TEXT
is_private BOOLEAN
```

### Add to `posts` table:
```sql
video_view_count INTEGER  -- CRITICAL for reels/videos!
video_duration DECIMAL    -- Duration in seconds
location_name TEXT        -- Location tag
```

---

## Next Steps

1. **Find correct API parameters** to get:
   - Profile metadata (followers, bio, etc.)
   - Video view counts
   - All posts (not just 18)

2. **Test different endpoints:**
   - Profile scraping endpoint
   - Post scraping endpoint with video details
   - Comment scraping endpoint

3. **Check Apify documentation** for:
   - Complete input schema
   - Available result types
   - Pagination options
