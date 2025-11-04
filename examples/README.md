# Examples

This directory contains example scripts demonstrating how to use various features of the Visionary Lab application.

## YouTube Video Publishing

**File**: `youtube_publish_demo.py`

Demonstrates how to publish videos to YouTube using the social media publishing API.

### Usage

```bash
# Make sure the backend is running
cd backend
uvicorn main:app --reload

# In another terminal, run the example
python examples/youtube_publish_demo.py
```

### Prerequisites

1. Backend server running on http://localhost:8000
2. YouTube OAuth credentials configured (see SOCIAL_MEDIA_PUBLISHING.md)
3. A video file uploaded to Azure Blob Storage

### What it does

1. Checks health of backend and YouTube services
2. Prompts for video blob name and title
3. Publishes the video to YouTube
4. Returns the YouTube video URL

## More Examples Coming Soon

- TikTok video publishing
- Facebook video publishing
- Batch video publishing
- Video analytics
