from pydantic import BaseModel, Field
from typing import Optional, Dict, List
from enum import Enum


class SocialMediaPlatform(str, Enum):
    """Supported social media platforms"""
    YOUTUBE = "youtube"
    TIKTOK = "tiktok"
    FACEBOOK = "facebook"


class VideoPrivacyStatus(str, Enum):
    """Video privacy status options"""
    PUBLIC = "public"
    PRIVATE = "private"
    UNLISTED = "unlisted"


class YouTubePublishRequest(BaseModel):
    """Request model for publishing video to YouTube"""
    video_blob_name: str = Field(..., description="Name of the video blob in Azure Storage")
    title: str = Field(..., description="Video title")
    description: Optional[str] = Field(None, description="Video description")
    tags: Optional[List[str]] = Field(default_factory=list, description="Video tags")
    category_id: Optional[str] = Field("22", description="YouTube category ID (default: 22 for People & Blogs)")
    privacy_status: VideoPrivacyStatus = Field(VideoPrivacyStatus.UNLISTED, description="Privacy status")
    made_for_kids: bool = Field(False, description="Whether the video is made for kids")


class TikTokPublishRequest(BaseModel):
    """Request model for publishing video to TikTok"""
    video_blob_name: str = Field(..., description="Name of the video blob in Azure Storage")
    title: str = Field(..., description="Video title/caption")
    privacy_level: str = Field("SELF_ONLY", description="Privacy level: PUBLIC_TO_EVERYONE, MUTUAL_FOLLOW_FRIENDS, SELF_ONLY")
    disable_comment: bool = Field(False, description="Disable comments")
    disable_duet: bool = Field(False, description="Disable duet")
    disable_stitch: bool = Field(False, description="Disable stitch")


class FacebookPublishRequest(BaseModel):
    """Request model for publishing video to Facebook"""
    video_blob_name: str = Field(..., description="Name of the video blob in Azure Storage")
    title: str = Field(..., description="Video title")
    description: Optional[str] = Field(None, description="Video description")
    privacy: Dict[str, str] = Field(
        default_factory=lambda: {"value": "SELF"},
        description="Privacy settings for the video"
    )


class SocialMediaPublishRequest(BaseModel):
    """Unified request model for publishing to any social media platform"""
    platform: SocialMediaPlatform = Field(..., description="Target social media platform")
    video_blob_name: str = Field(..., description="Name of the video blob in Azure Storage")
    title: str = Field(..., description="Video title")
    description: Optional[str] = Field(None, description="Video description")
    tags: Optional[List[str]] = Field(default_factory=list, description="Video tags")
    privacy_status: VideoPrivacyStatus = Field(VideoPrivacyStatus.UNLISTED, description="Privacy status")
    platform_specific_options: Optional[Dict] = Field(None, description="Platform-specific options")


class PublishResponse(BaseModel):
    """Response model for social media publishing"""
    success: bool = Field(..., description="Whether the publish was successful")
    platform: SocialMediaPlatform = Field(..., description="Platform where video was published")
    video_id: Optional[str] = Field(None, description="Platform-specific video ID")
    video_url: Optional[str] = Field(None, description="URL to the published video")
    message: Optional[str] = Field(None, description="Success or error message")
    details: Optional[Dict] = Field(None, description="Additional platform-specific details")


class PublishStatus(BaseModel):
    """Model for tracking publish status"""
    video_blob_name: str = Field(..., description="Name of the video blob")
    platform: SocialMediaPlatform = Field(..., description="Target platform")
    status: str = Field(..., description="Current status: pending, processing, completed, failed")
    video_id: Optional[str] = Field(None, description="Platform-specific video ID")
    video_url: Optional[str] = Field(None, description="URL to the published video")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    created_at: Optional[str] = Field(None, description="ISO timestamp when publish started")
    completed_at: Optional[str] = Field(None, description="ISO timestamp when publish completed")
