"""
Social Media Publishing API Endpoints
Handles publishing videos to YouTube, TikTok, and Facebook
"""
import logging
import os
import tempfile
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.responses import JSONResponse

from backend.models.social_media import (
    YouTubePublishRequest,
    TikTokPublishRequest,
    FacebookPublishRequest,
    SocialMediaPublishRequest,
    PublishResponse,
    SocialMediaPlatform,
    VideoPrivacyStatus,
)
from backend.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()


def get_youtube_service():
    """Dependency to get YouTube service instance"""
    try:
        from backend.core.youtube_service import YouTubeService
        return YouTubeService()
    except Exception as e:
        logger.warning(f"YouTube service unavailable: {e}")
        return None


@router.post("/youtube", response_model=PublishResponse)
async def publish_to_youtube(
    request: YouTubePublishRequest,
    youtube_service=Depends(get_youtube_service)
):
    """
    Publish a video to YouTube
    
    This endpoint:
    1. Downloads the video from Azure Blob Storage
    2. Uploads it to YouTube using OAuth credentials
    3. Returns the YouTube video ID and URL
    
    Prerequisites:
    - YouTube Data API v3 enabled in Google Cloud
    - OAuth 2.0 credentials configured (client_secrets.json)
    - User authorization completed
    
    Args:
        request: YouTube publish request with video details
        
    Returns:
        PublishResponse with video ID and URL
    """
    if not youtube_service:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="YouTube service is not configured. Please set up OAuth credentials."
        )
    
    try:
        # Download video from Azure Blob Storage
        from backend.core.azure_storage import AzureBlobStorageService
        
        logger.info(f"Downloading video {request.video_blob_name} from Azure Storage")
        azure_service = AzureBlobStorageService()
        
        video_content, content_type = azure_service.get_asset_content(
            request.video_blob_name,
            'videos'
        )
        
        if not video_content:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Video not found: {request.video_blob_name}"
            )
        
        # Save to temporary file for YouTube upload
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp_file:
            temp_file.write(video_content)
            temp_file_path = temp_file.name
        
        try:
            # Upload to YouTube
            logger.info(f"Uploading to YouTube: {request.title}")
            result = youtube_service.upload_video(
                video_path=temp_file_path,
                title=request.title,
                description=request.description,
                tags=request.tags,
                category_id=request.category_id,
                privacy_status=request.privacy_status.value,
                made_for_kids=request.made_for_kids
            )
            
            return PublishResponse(
                success=True,
                platform=SocialMediaPlatform.YOUTUBE,
                video_id=result['video_id'],
                video_url=result['video_url'],
                message="Video successfully published to YouTube",
                details={
                    'title': result['title'],
                    'privacy_status': result['privacy_status'],
                    'uploaded_at': result['uploaded_at']
                }
            )
            
        finally:
            # Clean up temporary file
            try:
                os.unlink(temp_file_path)
            except Exception as e:
                logger.warning(f"Failed to delete temp file: {e}")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"YouTube publish failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to publish to YouTube: {str(e)}"
        )


@router.post("/tiktok", response_model=PublishResponse)
async def publish_to_tiktok(request: TikTokPublishRequest):
    """
    Publish a video to TikTok
    
    Note: TikTok API integration requires:
    - TikTok Developer account
    - App registration and approval
    - User authorization
    
    This endpoint is a placeholder for future TikTok integration.
    
    Args:
        request: TikTok publish request
        
    Returns:
        PublishResponse
    """
    # TikTok integration placeholder
    # TODO: Implement TikTok API integration
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="TikTok publishing is not yet implemented. Coming soon!"
    )


@router.post("/facebook", response_model=PublishResponse)
async def publish_to_facebook(request: FacebookPublishRequest):
    """
    Publish a video to Facebook
    
    Note: Facebook Graph API integration requires:
    - Facebook Developer account
    - App registration
    - User access token with publish permissions
    
    This endpoint is a placeholder for future Facebook integration.
    
    Args:
        request: Facebook publish request
        
    Returns:
        PublishResponse
    """
    # Facebook integration placeholder
    # TODO: Implement Facebook Graph API integration
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Facebook publishing is not yet implemented. Coming soon!"
    )


@router.post("/publish", response_model=PublishResponse)
async def publish_to_platform(
    request: SocialMediaPublishRequest,
    youtube_service=Depends(get_youtube_service)
):
    """
    Unified endpoint to publish a video to any social media platform
    
    Routes to the appropriate platform-specific handler based on the platform field.
    
    Args:
        request: Unified publish request
        
    Returns:
        PublishResponse with platform-specific details
    """
    if request.platform == SocialMediaPlatform.YOUTUBE:
        platform_opts = request.platform_specific_options or {}
        youtube_request = YouTubePublishRequest(
            video_blob_name=request.video_blob_name,
            title=request.title,
            description=request.description,
            tags=request.tags,
            privacy_status=request.privacy_status,
            category_id=platform_opts.get('category_id', '22'),
            made_for_kids=platform_opts.get('made_for_kids', False)
        )
        return await publish_to_youtube(youtube_request, youtube_service)
    
    elif request.platform == SocialMediaPlatform.TIKTOK:
        platform_opts = request.platform_specific_options or {}
        tiktok_request = TikTokPublishRequest(
            video_blob_name=request.video_blob_name,
            title=request.title,
            privacy_level=platform_opts.get('privacy_level', 'SELF_ONLY')
        )
        return await publish_to_tiktok(tiktok_request)
    
    elif request.platform == SocialMediaPlatform.FACEBOOK:
        facebook_request = FacebookPublishRequest(
            video_blob_name=request.video_blob_name,
            title=request.title,
            description=request.description
        )
        return await publish_to_facebook(facebook_request)
    
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported platform: {request.platform}"
        )


@router.get("/youtube/status/{video_id}")
async def get_youtube_video_status(
    video_id: str,
    youtube_service=Depends(get_youtube_service)
):
    """
    Get status and details of a YouTube video
    
    Args:
        video_id: YouTube video ID
        
    Returns:
        Video details including status, views, etc.
    """
    if not youtube_service:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="YouTube service is not configured"
        )
    
    try:
        details = youtube_service.get_video_details(video_id)
        return JSONResponse(
            content={
                'video_id': video_id,
                'title': details['snippet']['title'],
                'description': details['snippet']['description'],
                'privacy_status': details['status']['privacyStatus'],
                'views': details['statistics'].get('viewCount', 0),
                'likes': details['statistics'].get('likeCount', 0),
                'comments': details['statistics'].get('commentCount', 0),
                'url': f"https://www.youtube.com/watch?v={video_id}"
            }
        )
    except Exception as e:
        logger.error(f"Failed to get YouTube video status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get video status: {str(e)}"
        )


@router.get("/health")
async def social_media_health_check(youtube_service=Depends(get_youtube_service)):
    """
    Check health and configuration status of social media services
    
    Returns:
        Status of each platform integration
    """
    return {
        "youtube": {
            "configured": youtube_service is not None,
            "status": "ready" if youtube_service else "not_configured"
        },
        "tiktok": {
            "configured": False,
            "status": "not_implemented"
        },
        "facebook": {
            "configured": False,
            "status": "not_implemented"
        }
    }
