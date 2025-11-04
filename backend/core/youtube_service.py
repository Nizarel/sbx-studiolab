"""
YouTube API Integration Service
Handles video uploads to YouTube using OAuth 2.0 credentials
"""
import os
import logging
from typing import Optional, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class YouTubeService:
    """
    Service for uploading videos to YouTube.
    Uses Google's YouTube Data API v3.
    
    Prerequisites:
    - Google Cloud project with YouTube Data API v3 enabled
    - OAuth 2.0 credentials (client_secrets.json)
    - User authorization token
    
    Environment Variables:
    - YOUTUBE_CLIENT_SECRETS_FILE: Path to OAuth client secrets JSON file
    - YOUTUBE_CREDENTIALS_FILE: Path to stored user credentials
    """
    
    def __init__(
        self,
        client_secrets_file: Optional[str] = None,
        credentials_file: Optional[str] = None
    ):
        """
        Initialize YouTube service
        
        Args:
            client_secrets_file: Path to OAuth client secrets JSON
            credentials_file: Path to stored credentials
        """
        self.client_secrets_file = client_secrets_file or os.getenv(
            "YOUTUBE_CLIENT_SECRETS_FILE",
            "client_secrets.json"
        )
        self.credentials_file = credentials_file or os.getenv(
            "YOUTUBE_CREDENTIALS_FILE",
            "youtube_credentials.json"
        )
        self.youtube = None
        self._initialized = False
        
        # Defer initialization until needed to allow service to exist
        # even if credentials aren't configured yet
        
    def _initialize(self):
        """
        Lazy initialization of YouTube API client.
        Only called when upload is attempted.
        """
        if self._initialized:
            return
            
        try:
            from google.oauth2.credentials import Credentials
            from google_auth_oauthlib.flow import InstalledAppFlow
            from googleapiclient.discovery import build
            from google.auth.transport.requests import Request
            import json
            
            SCOPES = ['https://www.googleapis.com/auth/youtube.upload']
            
            creds = None
            
            # Load existing credentials if available
            if os.path.exists(self.credentials_file):
                try:
                    with open(self.credentials_file, 'r') as token:
                        creds_data = json.load(token)
                        creds = Credentials.from_authorized_user_info(creds_data, SCOPES)
                except Exception as e:
                    logger.warning(f"Failed to load credentials: {e}")
            
            # If credentials don't exist or are invalid, get new ones
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    try:
                        creds.refresh(Request())
                    except Exception as e:
                        logger.error(f"Failed to refresh credentials: {e}")
                        creds = None
                
                if not creds:
                    if not os.path.exists(self.client_secrets_file):
                        raise FileNotFoundError(
                            f"YouTube client secrets file not found at {self.client_secrets_file}. "
                            "Please configure OAuth 2.0 credentials."
                        )
                    
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.client_secrets_file, SCOPES
                    )
                    creds = flow.run_local_server(port=0)
                
                # Save credentials for future use
                with open(self.credentials_file, 'w') as token:
                    token.write(creds.to_json())
            
            # Build YouTube API client
            self.youtube = build('youtube', 'v3', credentials=creds)
            self._initialized = True
            logger.info("YouTube service initialized successfully")
            
        except ImportError as e:
            raise ImportError(
                "YouTube integration requires google-auth-oauthlib and google-api-python-client. "
                "Install with: pip install google-auth-oauthlib google-api-python-client"
            ) from e
    
    def upload_video(
        self,
        video_path: str,
        title: str,
        description: Optional[str] = None,
        tags: Optional[list] = None,
        category_id: str = "22",
        privacy_status: str = "unlisted",
        made_for_kids: bool = False
    ) -> Dict[str, Any]:
        """
        Upload a video to YouTube
        
        Args:
            video_path: Local path to video file
            title: Video title (max 100 chars)
            description: Video description (max 5000 chars)
            tags: List of tags (max 500 chars total)
            category_id: YouTube category ID (default: 22 = People & Blogs)
            privacy_status: 'public', 'private', or 'unlisted'
            made_for_kids: Whether video is made for kids
            
        Returns:
            Dict containing video_id, video_url, and upload details
            
        Raises:
            Exception: If upload fails
        """
        # Initialize if not already done
        self._initialize()
        
        if not self.youtube:
            raise RuntimeError("YouTube service not properly initialized")
        
        try:
            from googleapiclient.http import MediaFileUpload
            
            # Validate file exists
            if not os.path.exists(video_path):
                raise FileNotFoundError(f"Video file not found: {video_path}")
            
            # Prepare video metadata
            body = {
                'snippet': {
                    'title': title[:100],  # YouTube max title length
                    'description': description[:5000] if description else '',
                    'tags': tags if tags else [],  # YouTube will validate tag limits
                    'categoryId': category_id
                },
                'status': {
                    'privacyStatus': privacy_status.lower(),
                    'selfDeclaredMadeForKids': made_for_kids
                }
            }
            
            # Create media upload
            media = MediaFileUpload(
                video_path,
                chunksize=-1,  # Upload in a single request
                resumable=True,
                mimetype='video/*'
            )
            
            # Execute upload
            logger.info(f"Starting YouTube upload: {title}")
            request = self.youtube.videos().insert(
                part='snippet,status',
                body=body,
                media_body=media
            )
            
            response = request.execute()
            
            video_id = response.get('id')
            video_url = f"https://www.youtube.com/watch?v={video_id}"
            
            logger.info(f"Upload successful. Video ID: {video_id}")
            
            return {
                'success': True,
                'video_id': video_id,
                'video_url': video_url,
                'title': title,
                'privacy_status': privacy_status,
                'uploaded_at': datetime.now().isoformat(),
                'response': response
            }
            
        except Exception as e:
            logger.error(f"YouTube upload failed: {str(e)}")
            raise Exception(f"YouTube upload failed: {str(e)}") from e
    
    def get_video_details(self, video_id: str) -> Dict[str, Any]:
        """
        Get details about an uploaded video
        
        Args:
            video_id: YouTube video ID
            
        Returns:
            Dict containing video details
        """
        self._initialize()
        
        try:
            request = self.youtube.videos().list(
                part='snippet,status,contentDetails,statistics',
                id=video_id
            )
            response = request.execute()
            
            if not response.get('items'):
                raise ValueError(f"Video not found: {video_id}")
            
            return response['items'][0]
            
        except Exception as e:
            logger.error(f"Failed to get video details: {str(e)}")
            raise
    
    def update_video_metadata(
        self,
        video_id: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
        tags: Optional[list] = None,
        privacy_status: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update metadata for an existing video
        
        Args:
            video_id: YouTube video ID
            title: New title (optional)
            description: New description (optional)
            tags: New tags (optional)
            privacy_status: New privacy status (optional)
            
        Returns:
            Updated video details
        """
        self._initialize()
        
        try:
            # Get current video details
            current = self.get_video_details(video_id)
            
            # Prepare update body
            body = {
                'id': video_id,
                'snippet': current['snippet']
            }
            
            # Update fields if provided
            if title:
                body['snippet']['title'] = title[:100]
            if description is not None:
                body['snippet']['description'] = description[:5000]
            if tags is not None:
                body['snippet']['tags'] = tags  # YouTube will validate tag limits
            
            # Update privacy if provided
            if privacy_status:
                body['status'] = current.get('status', {})
                body['status']['privacyStatus'] = privacy_status.lower()
            
            # Execute update
            request = self.youtube.videos().update(
                part='snippet' + (',status' if privacy_status else ''),
                body=body
            )
            response = request.execute()
            
            logger.info(f"Updated video metadata: {video_id}")
            return response
            
        except Exception as e:
            logger.error(f"Failed to update video metadata: {str(e)}")
            raise
    
    def delete_video(self, video_id: str) -> bool:
        """
        Delete a video from YouTube
        
        Args:
            video_id: YouTube video ID
            
        Returns:
            True if successful
        """
        self._initialize()
        
        try:
            self.youtube.videos().delete(id=video_id).execute()
            logger.info(f"Deleted video: {video_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete video: {str(e)}")
            raise
