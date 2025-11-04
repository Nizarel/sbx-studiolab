# Social Media Publishing Integration

This feature enables publishing generated videos to social media platforms including YouTube, TikTok, and Facebook.

## Overview

The social media publishing integration provides a unified API for uploading videos from Azure Blob Storage to various social media platforms. Currently, YouTube integration is fully implemented with OAuth 2.0 authentication. TikTok and Facebook integrations are planned for future releases.

## Features

- **YouTube Integration**: Full support for uploading videos to YouTube with customizable metadata
- **Unified API**: Single endpoint for publishing to multiple platforms
- **Azure Storage Integration**: Seamlessly downloads videos from Azure Blob Storage
- **Privacy Controls**: Configure video privacy settings (public, unlisted, private)
- **Metadata Management**: Set titles, descriptions, tags, and categories

## Architecture

### Components

1. **Models** (`backend/models/social_media.py`):
   - `YouTubePublishRequest`: Request model for YouTube uploads
   - `TikTokPublishRequest`: Request model for TikTok uploads (coming soon)
   - `FacebookPublishRequest`: Request model for Facebook uploads (coming soon)
   - `SocialMediaPublishRequest`: Unified request model
   - `PublishResponse`: Response model with upload details

2. **Services** (`backend/core/youtube_service.py`):
   - `YouTubeService`: Handles YouTube API integration and video uploads

3. **API Endpoints** (`backend/api/endpoints/social_media.py`):
   - `POST /api/v1/social-media/youtube`: Publish to YouTube
   - `POST /api/v1/social-media/tiktok`: Publish to TikTok (coming soon)
   - `POST /api/v1/social-media/facebook`: Publish to Facebook (coming soon)
   - `POST /api/v1/social-media/publish`: Unified publishing endpoint
   - `GET /api/v1/social-media/youtube/status/{video_id}`: Get YouTube video status
   - `GET /api/v1/social-media/health`: Check service health

## YouTube Setup

### Prerequisites

1. **Google Cloud Project**:
   - Create a project in [Google Cloud Console](https://console.cloud.google.com/)
   - Enable YouTube Data API v3

2. **OAuth 2.0 Credentials**:
   - Go to APIs & Services → Credentials
   - Create OAuth 2.0 Client ID (Desktop application)
   - Download the client secrets JSON file

3. **Configure Environment**:
   ```bash
   # Optional: Custom paths for OAuth credentials
   YOUTUBE_CLIENT_SECRETS_FILE=path/to/client_secrets.json
   YOUTUBE_CREDENTIALS_FILE=path/to/youtube_credentials.json
   ```

### First-Time Authorization

On first use, the YouTube service will:
1. Open a browser for user authorization
2. Request permission to upload videos
3. Save credentials for future use

This is a one-time setup per deployment environment.

## Usage Examples

### Python API

```python
from backend.models.social_media import (
    YouTubePublishRequest,
    VideoPrivacyStatus
)

# Create request
request = YouTubePublishRequest(
    video_blob_name="my-video.mp4",
    title="My Amazing Video",
    description="Check out this awesome content!",
    tags=["tutorial", "demo", "ai-generated"],
    privacy_status=VideoPrivacyStatus.UNLISTED,
    category_id="22",  # People & Blogs
    made_for_kids=False
)

# Publish to YouTube
response = await publish_to_youtube(request)

print(f"Video URL: {response.video_url}")
print(f"Video ID: {response.video_id}")
```

### REST API

```bash
# Publish to YouTube
curl -X POST "http://localhost:8000/api/v1/social-media/youtube" \
  -H "Content-Type: application/json" \
  -d '{
    "video_blob_name": "sample-video.mp4",
    "title": "My Video Title",
    "description": "Video description here",
    "tags": ["ai", "video", "demo"],
    "privacy_status": "unlisted",
    "category_id": "22",
    "made_for_kids": false
  }'

# Check video status
curl "http://localhost:8000/api/v1/social-media/youtube/status/VIDEO_ID"

# Health check
curl "http://localhost:8000/api/v1/social-media/health"
```

### Unified Publishing Endpoint

```bash
curl -X POST "http://localhost:8000/api/v1/social-media/publish" \
  -H "Content-Type: application/json" \
  -d '{
    "platform": "youtube",
    "video_blob_name": "sample-video.mp4",
    "title": "My Video",
    "description": "Description",
    "tags": ["tag1", "tag2"],
    "privacy_status": "unlisted",
    "platform_specific_options": {
      "category_id": "20",
      "made_for_kids": false
    }
  }'
```

## YouTube Categories

Common YouTube category IDs:
- `1`: Film & Animation
- `2`: Autos & Vehicles
- `10`: Music
- `15`: Pets & Animals
- `17`: Sports
- `19`: Travel & Events
- `20`: Gaming
- `22`: People & Blogs (default)
- `23`: Comedy
- `24`: Entertainment
- `25`: News & Politics
- `26`: Howto & Style
- `27`: Education
- `28`: Science & Technology

## Privacy Settings

- **PUBLIC**: Visible to everyone, appears in search results
- **UNLISTED**: Only accessible via direct link
- **PRIVATE**: Only visible to you and users you specify

## Error Handling

The API provides detailed error messages for common issues:

- `503 Service Unavailable`: YouTube service not configured
- `404 Not Found`: Video not found in Azure Storage
- `500 Internal Server Error`: Upload failed (check logs for details)
- `501 Not Implemented`: Platform not yet supported (TikTok, Facebook)

## Testing

Run the test suite:

```bash
# Run all social media tests
pytest test_social_media.py -v

# Run specific test class
pytest test_social_media.py::TestYouTubeService -v

# Run with coverage
pytest test_social_media.py --cov=backend.core.youtube_service --cov=backend.api.endpoints.social_media
```

## Security Considerations

1. **OAuth Credentials**: Never commit `client_secrets.json` or `youtube_credentials.json` to version control
2. **Scopes**: Only requests minimum required permissions (upload scope)
3. **Token Storage**: Credentials are stored locally and refreshed automatically
4. **Environment Variables**: Use environment variables for configuration

## Future Enhancements

### TikTok Integration
- TikTok Developer API support
- Content posting API integration
- Privacy and sharing settings

### Facebook Integration
- Facebook Graph API integration
- Video upload to Facebook Pages
- Instagram video publishing (via Facebook API)

### Additional Features
- Scheduled publishing
- Batch uploads
- Publishing analytics
- Automatic caption generation
- Thumbnail selection
- Publishing history tracking

## Troubleshooting

### Common Issues

**Issue**: "YouTube service is not configured"
- **Solution**: Ensure OAuth credentials are properly set up and authorization is complete

**Issue**: "Video not found in Azure Storage"
- **Solution**: Verify the video blob name is correct and exists in the 'videos' container

**Issue**: OAuth authorization window doesn't open
- **Solution**: Check that you're running in an environment with browser access, or use token-based auth

**Issue**: Upload fails with quota error
- **Solution**: YouTube API has daily quota limits. Check your quota in Google Cloud Console

## API Reference

For complete API documentation, visit the interactive API docs at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Dependencies

Required packages (automatically installed with the project):
- `google-auth-oauthlib>=1.2.0`: OAuth 2.0 authentication
- `google-api-python-client>=2.108.0`: YouTube Data API client

## Contributing

When adding support for new platforms:

1. Create request/response models in `backend/models/social_media.py`
2. Implement service class in `backend/core/[platform]_service.py`
3. Add endpoints in `backend/api/endpoints/social_media.py`
4. Write tests in `test_social_media.py`
5. Update this documentation

## License

This feature is part of the Visionary Lab project and follows the same license terms.
