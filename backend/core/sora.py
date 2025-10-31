from openai import AzureOpenAI
import os
import logging
import json
import io
from typing import List, Optional

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Sora:
    def __init__(self, resource_name, deployment_name, api_key, api_version="2025-01-01-preview"):
        self.resource_name = resource_name
        self.deployment_name = deployment_name
        self.api_key = api_key
        self.api_version = api_version
        
        # Initialize OpenAI client for Sora-2
        self.client = AzureOpenAI(
            api_key=api_key,
            api_version=api_version,
            azure_endpoint=f"https://{resource_name}.openai.azure.com"
        )
        
        logger.info(
            f"Initialized Sora-2 client with resource: {resource_name}, deployment: {deployment_name}")

    def create_video_generation_job(self, prompt, seconds, size, n_variants=1):
        """
        Create a video generation job with Sora-2.
        
        Args:
            prompt: Text prompt for video generation
            seconds: Duration in seconds (4, 8, or 12)
            size: Video resolution ("720x1280", "1280x720", "1024x1792", "1792x1024")
            n_variants: Number of video variants to generate (default 1)
        """
        logger.info(f"Creating Sora-2 video generation job with prompt: {prompt[:50]}...")
        
        response = self.client.videos.create(
            model=self.deployment_name,
            prompt=prompt,
            seconds=seconds,
            size=size,
            n=n_variants
        )
        
        return response.model_dump()

    def create_video_generation_job_with_images(self, prompt, image_path, seconds, size, n_variants=1):
        """
        Create video generation job with single input reference image for Sora-2.
        Sora-2 uses a single input_reference instead of multiple images.
        
        Args:
            prompt: Text prompt for video generation
            image_path: Path to the input reference image
            seconds: Duration in seconds (4, 8, or 12)
            size: Video resolution ("720x1280", "1280x720", "1024x1792", "1792x1024")
            n_variants: Number of video variants to generate (default 1)
        """
        logger.info(f"Creating Sora-2 video job with input reference and prompt: {prompt[:50]}...")
        
        response = self.client.videos.create(
            model=self.deployment_name,
            prompt=prompt,
            seconds=seconds,
            size=size,
            n=n_variants,
            input_reference=image_path
        )
        
        return response.model_dump()

    def get_video_generation_job(self, job_id):
        """
        Retrieve the status and details of a video generation job.
        
        Args:
            job_id: The video generation job ID
        """
        logger.info(f"Getting Sora-2 video generation job: {job_id}")
        response = self.client.videos.retrieve(job_id)
        return response.model_dump()

    def delete_video_generation_job(self, job_id):
        """
        Delete a video generation job.
        
        Args:
            job_id: The video generation job ID
        """
        logger.info(f"Deleting Sora-2 video generation job: {job_id}")
        response = self.client.videos.delete(job_id)
        return response.deleted

    def list_video_generation_jobs(self, before=None, after=None, limit=10):
        """
        List video generation jobs.
        
        Args:
            before: Cursor for pagination (before this ID)
            after: Cursor for pagination (after this ID)
            limit: Maximum number of results (default 10)
        """
        logger.info(f"Listing Sora-2 video generation jobs with limit: {limit}")
        response = self.client.videos.list(
            limit=limit,
            before=before,
            after=after
        )
        return response.model_dump()

    def get_video_generation_video_content(self, generation_id, file_name, target_folder='videos'):
        """
        Download the video content for a given generation as an MP4 file to the local folder.

        Args:
            generation_id (str): The generation ID.
            file_name (str): The filename to save the video as (include .mp4 extension).
            target_folder (str): The folder to save the video to (default: 'videos').

        Returns:
            str: The path to the downloaded file.
        """
        # Create directory if it doesn't exist
        os.makedirs(target_folder, exist_ok=True)

        file_path = os.path.join(target_folder, file_name)

        logger.info(f"Downloading Sora-2 video content for generation {generation_id} to {file_path}")

        # Download video content using OpenAI SDK
        content = self.client.videos.download_content(generation_id, variant="video")
        
        with open(file_path, 'wb') as f:
            f.write(content)

        logger.info(f"Successfully downloaded video to {file_path}")
        return file_path
    
    def create_remix_video_job(self, remix_video_id, prompt, seconds, size, n_variants=1):
        """
        Create a remix video generation job based on an existing video.
        
        Args:
            remix_video_id: ID of the video to remix
            prompt: Text prompt describing the desired changes
            seconds: Duration in seconds (4, 8, or 12)
            size: Video resolution ("720x1280", "1280x720", "1024x1792", "1792x1024")
            n_variants: Number of video variants to generate (default 1)
        """
        logger.info(f"Creating Sora-2 remix job for video {remix_video_id} with prompt: {prompt[:50]}...")
        
        response = self.client.videos.create(
            model=self.deployment_name,
            prompt=prompt,
            seconds=seconds,
            size=size,
            n=n_variants,
            remix_video_id=remix_video_id
        )
        
        return response.model_dump()
