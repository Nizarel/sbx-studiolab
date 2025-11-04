#!/usr/bin/env python3
"""
Example script demonstrating YouTube video publishing integration

This script shows how to:
1. Generate a video using Sora
2. Publish the video to YouTube
3. Check the video status

Prerequisites:
- Backend server running (uvicorn backend.main:app)
- YouTube OAuth credentials configured
- Video in Azure Blob Storage
"""

import requests
import json
import time

# Backend API base URL
BASE_URL = "http://localhost:8000/api/v1"


def check_health():
    """Check if backend and social media services are available"""
    print("🔍 Checking service health...")
    
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"✅ Backend health: {response.json()}")
        
        response = requests.get(f"{BASE_URL}/social-media/health")
        health = response.json()
        print(f"✅ Social media health: {json.dumps(health, indent=2)}")
        
        if health['youtube']['configured']:
            print("✅ YouTube service is configured and ready")
        else:
            print("⚠️  YouTube service is not configured. Set up OAuth credentials first.")
            
        return health['youtube']['configured']
        
    except Exception as e:
        print(f"❌ Error checking health: {e}")
        return False


def publish_to_youtube(video_blob_name, title, description=None, tags=None):
    """
    Publish a video to YouTube
    
    Args:
        video_blob_name: Name of the video file in Azure Blob Storage (e.g., "my-video.mp4")
        title: Video title
        description: Video description (optional)
        tags: List of tags (optional)
    
    Returns:
        dict: Response with video_id and video_url
    """
    print(f"\n📤 Publishing video to YouTube...")
    print(f"   Video: {video_blob_name}")
    print(f"   Title: {title}")
    
    payload = {
        "video_blob_name": video_blob_name,
        "title": title,
        "description": description or f"Video generated and published automatically",
        "tags": tags or ["ai-generated", "sora"],
        "privacy_status": "unlisted",
        "category_id": "22",
        "made_for_kids": False
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/social-media/youtube",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Video published successfully!")
            print(f"   Video ID: {result['video_id']}")
            print(f"   URL: {result['video_url']}")
            return result
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"   {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error publishing video: {e}")
        return None


def main():
    """Main demo flow"""
    print("=" * 60)
    print("  YouTube Video Publishing Demo")
    print("=" * 60)
    
    youtube_ready = check_health()
    
    if not youtube_ready:
        print("\n⚠️  YouTube service is not configured.")
        print("See SOCIAL_MEDIA_PUBLISHING.md for setup instructions.")
        return
    
    video_blob_name = input("\n📹 Enter video blob name: ").strip()
    if not video_blob_name:
        print("❌ Video blob name is required")
        return
    
    title = input("📝 Enter video title: ").strip() or "My AI-Generated Video"
    
    result = publish_to_youtube(video_blob_name=video_blob_name, title=title)
    
    if result:
        print(f"\n🎉 Success! Your video is now on YouTube!")
        print(f"🔗 Watch it here: {result['video_url']}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Demo cancelled by user")
