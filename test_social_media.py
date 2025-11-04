"""
Test suite for social media publishing functionality
Tests YouTube, TikTok, and Facebook video publishing features
"""
import os
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import pytest

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from backend.models.social_media import (
    YouTubePublishRequest,
    TikTokPublishRequest,
    FacebookPublishRequest,
    SocialMediaPublishRequest,
    PublishResponse,
    SocialMediaPlatform,
    VideoPrivacyStatus,
)


class TestSocialMediaModels:
    """Test Pydantic models for social media publishing"""
    
    def test_youtube_publish_request(self):
        """Test YouTube publish request model"""
        request = YouTubePublishRequest(
            video_blob_name="test_video.mp4",
            title="Test Video",
            description="A test video description",
            tags=["test", "demo"],
            category_id="22",
            privacy_status=VideoPrivacyStatus.UNLISTED,
            made_for_kids=False
        )
        
        assert request.video_blob_name == "test_video.mp4"
        assert request.title == "Test Video"
        assert request.description == "A test video description"
        assert request.tags == ["test", "demo"]
        assert request.category_id == "22"
        assert request.privacy_status == VideoPrivacyStatus.UNLISTED
        assert request.made_for_kids is False
    
    def test_youtube_request_defaults(self):
        """Test YouTube request with default values"""
        request = YouTubePublishRequest(
            video_blob_name="test.mp4",
            title="Test"
        )
        
        assert request.tags == []
        assert request.category_id == "22"
        assert request.privacy_status == VideoPrivacyStatus.UNLISTED
        assert request.made_for_kids is False
    
    def test_tiktok_publish_request(self):
        """Test TikTok publish request model"""
        request = TikTokPublishRequest(
            video_blob_name="test_video.mp4",
            title="Test TikTok",
            privacy_level="PUBLIC_TO_EVERYONE",
            disable_comment=False,
            disable_duet=True,
            disable_stitch=True
        )
        
        assert request.video_blob_name == "test_video.mp4"
        assert request.title == "Test TikTok"
        assert request.privacy_level == "PUBLIC_TO_EVERYONE"
        assert request.disable_comment is False
        assert request.disable_duet is True
        assert request.disable_stitch is True
    
    def test_facebook_publish_request(self):
        """Test Facebook publish request model"""
        request = FacebookPublishRequest(
            video_blob_name="test_video.mp4",
            title="Test Facebook Video",
            description="Facebook video description",
            privacy={"value": "PUBLIC"}
        )
        
        assert request.video_blob_name == "test_video.mp4"
        assert request.title == "Test Facebook Video"
        assert request.description == "Facebook video description"
        assert request.privacy == {"value": "PUBLIC"}
    
    def test_unified_publish_request(self):
        """Test unified social media publish request"""
        request = SocialMediaPublishRequest(
            platform=SocialMediaPlatform.YOUTUBE,
            video_blob_name="test.mp4",
            title="Test Video",
            description="Test description",
            tags=["test"],
            privacy_status=VideoPrivacyStatus.PUBLIC,
            platform_specific_options={"category_id": "20"}
        )
        
        assert request.platform == SocialMediaPlatform.YOUTUBE
        assert request.video_blob_name == "test.mp4"
        assert request.title == "Test Video"
        assert request.platform_specific_options["category_id"] == "20"
    
    def test_publish_response(self):
        """Test publish response model"""
        response = PublishResponse(
            success=True,
            platform=SocialMediaPlatform.YOUTUBE,
            video_id="abc123",
            video_url="https://youtube.com/watch?v=abc123",
            message="Upload successful",
            details={"views": 0}
        )
        
        assert response.success is True
        assert response.platform == SocialMediaPlatform.YOUTUBE
        assert response.video_id == "abc123"
        assert "youtube.com" in response.video_url
        assert response.message == "Upload successful"
    
    def test_privacy_status_enum(self):
        """Test VideoPrivacyStatus enum values"""
        assert VideoPrivacyStatus.PUBLIC.value == "public"
        assert VideoPrivacyStatus.PRIVATE.value == "private"
        assert VideoPrivacyStatus.UNLISTED.value == "unlisted"
    
    def test_platform_enum(self):
        """Test SocialMediaPlatform enum values"""
        assert SocialMediaPlatform.YOUTUBE.value == "youtube"
        assert SocialMediaPlatform.TIKTOK.value == "tiktok"
        assert SocialMediaPlatform.FACEBOOK.value == "facebook"


class TestYouTubeService:
    """Test YouTube service functionality"""
    
    def test_youtube_service_initialization(self):
        """Test YouTube service can be initialized"""
        # Skip if google libraries not available
        try:
            from backend.core.youtube_service import YouTubeService
        except ImportError:
            pytest.skip("YouTube service dependencies not installed")
        
        service = YouTubeService(
            client_secrets_file="test_secrets.json",
            credentials_file="test_creds.json"
        )
        
        assert service.client_secrets_file == "test_secrets.json"
        assert service.credentials_file == "test_creds.json"
        assert service._initialized is False
    
    def test_youtube_upload_validation(self):
        """Test YouTube upload validates inputs"""
        # Skip if google libraries not available
        try:
            from backend.core.youtube_service import YouTubeService
        except ImportError:
            pytest.skip("YouTube service dependencies not installed")
        
        service = YouTubeService()
        
        # Test that upload requires valid file
        with pytest.raises((FileNotFoundError, Exception, RuntimeError)):
            service.upload_video(
                video_path="/nonexistent/video.mp4",
                title="Test Video"
            )


class TestSocialMediaEndpoints:
    """Test social media API endpoints"""
    
    def test_youtube_endpoint_requires_service(self):
        """Test that YouTube endpoint requires service configuration"""
        # This test ensures the endpoint handles missing service gracefully
        from backend.api.endpoints.social_media import get_youtube_service
        
        # When YouTube is not configured, should return None
        service = get_youtube_service()
        # Service may be None or an instance depending on configuration
        assert service is None or hasattr(service, 'upload_video')
    
    @pytest.mark.asyncio
    async def test_publish_endpoint_routing(self):
        """Test unified publish endpoint routes to correct platform"""
        from backend.api.endpoints.social_media import publish_to_platform
        from fastapi import HTTPException
        
        request = SocialMediaPublishRequest(
            platform=SocialMediaPlatform.TIKTOK,
            video_blob_name="test.mp4",
            title="Test"
        )
        
        # TikTok should raise not implemented
        with pytest.raises(HTTPException) as exc_info:
            await publish_to_platform(request, youtube_service=None)
        
        assert exc_info.value.status_code == 501
    
    @pytest.mark.asyncio
    async def test_facebook_not_implemented(self):
        """Test Facebook endpoint returns not implemented"""
        from backend.api.endpoints.social_media import publish_to_facebook
        from fastapi import HTTPException
        
        request = FacebookPublishRequest(
            video_blob_name="test.mp4",
            title="Test"
        )
        
        with pytest.raises(HTTPException) as exc_info:
            await publish_to_facebook(request)
        
        assert exc_info.value.status_code == 501
        assert "not yet implemented" in exc_info.value.detail.lower()


class TestIntegration:
    """Integration tests for social media publishing"""
    
    def test_models_serialization(self):
        """Test that models can be serialized to JSON"""
        request = YouTubePublishRequest(
            video_blob_name="test.mp4",
            title="Test Video",
            tags=["test"]
        )
        
        # Should be able to convert to dict
        request_dict = request.model_dump()
        assert request_dict["video_blob_name"] == "test.mp4"
        assert request_dict["title"] == "Test Video"
        assert request_dict["tags"] == ["test"]
    
    def test_end_to_end_request_response(self):
        """Test complete request/response flow"""
        # Create request
        request = YouTubePublishRequest(
            video_blob_name="sample.mp4",
            title="Sample Video",
            description="Test description",
            tags=["sample", "test"],
            privacy_status=VideoPrivacyStatus.UNLISTED
        )
        
        # Simulate response
        response = PublishResponse(
            success=True,
            platform=SocialMediaPlatform.YOUTUBE,
            video_id="test123",
            video_url="https://youtube.com/watch?v=test123",
            message="Success"
        )
        
        assert request.video_blob_name == "sample.mp4"
        assert response.success is True
        assert response.platform == SocialMediaPlatform.YOUTUBE


def test_import_models():
    """Test that all models can be imported"""
    from backend.models.social_media import (
        YouTubePublishRequest,
        TikTokPublishRequest,
        FacebookPublishRequest,
        SocialMediaPublishRequest,
        PublishResponse,
        PublishStatus,
        SocialMediaPlatform,
        VideoPrivacyStatus,
    )
    
    # All imports should succeed
    assert YouTubePublishRequest is not None
    assert TikTokPublishRequest is not None
    assert FacebookPublishRequest is not None
    assert SocialMediaPublishRequest is not None
    assert PublishResponse is not None
    assert PublishStatus is not None


def test_import_service():
    """Test that YouTube service can be imported"""
    try:
        from backend.core.youtube_service import YouTubeService
        assert YouTubeService is not None
    except ImportError:
        pytest.skip("Backend dependencies not installed")


def test_import_endpoints():
    """Test that social media endpoints can be imported"""
    try:
        from backend.api.endpoints.social_media import router
        assert router is not None
    except ImportError:
        pytest.skip("Backend dependencies not installed")


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "-s"])
