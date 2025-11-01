from openai import OpenAI
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
        
        # Initialize OpenAI client for Sora-2 with Azure endpoint
        # Note: Must use base OpenAI class (not AzureOpenAI) for videos API support
        azure_endpoint = f"https://{resource_name}.openai.azure.com"
        self.client = OpenAI(
            api_key=api_key,
            base_url=f"{azure_endpoint}/openai/v1/",
            default_headers={"api-key": api_key}
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
            n_variants: Number of video variants to generate (ignored - not supported in SDK)
        """
        logger.info(f"Creating Sora-2 video generation job with prompt: {prompt[:50]}...")
        
        response = self.client.videos.create(
            model=self.deployment_name,
            prompt=prompt,
            seconds=str(seconds),  # Must be string: '4', '8', or '12'
            size=size
        )
        
        response_dict = response.model_dump()
        logger.info(f"Created Sora-2 job {response_dict.get('id')} with initial status: {response_dict.get('status')}")
        return response_dict

    def create_video_generation_job_with_images(self, prompt, image_path, seconds, size, n_variants=1):
        """
        Create video generation job with single input reference image for Sora-2.
        Sora-2 uses a single input_reference instead of multiple images.
        
        Args:
            prompt: Text prompt for video generation
            image_path: Path to the input reference image
            seconds: Duration in seconds (4, 8, or 12)
            size: Video resolution ("720x1280", "1280x720", "1024x1792", "1792x1024")
            n_variants: Number of video variants to generate (ignored - not supported in SDK)
        """
        logger.info(f"Creating Sora-2 video job with input reference and prompt: {prompt[:50]}...")
        
        response = self.client.videos.create(
            model=self.deployment_name,
            prompt=prompt,
            seconds=str(seconds),  # Must be string: '4', '8', or '12'
            size=size,
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
        response_dict = response.model_dump()
        logger.info(f"Sora-2 job {job_id} status: {response_dict.get('status')}, generations: {len(response_dict.get('generations') or [])}")
        return response_dict

    def delete_video_generation_job(self, job_id):
        """
        Delete a video generation job.
        
        Args:
            job_id: The video generation job ID
        """
        logger.info(f"Deleting Sora-2 video generation job: {job_id}")
        response = self.client.videos.delete(job_id)
        return response.deleted

    def remix_video(self, video_id, prompt):
        """
        Create a remix of an existing video with modifications.
        Reuses the original video's structure and continuity while applying changes.
        
        Args:
            video_id: The ID of the completed video to remix
            prompt: New prompt describing the changes to make
        
        Returns:
            Dict containing the new video generation job details
        """
        logger.info(f"Creating remix of video {video_id} with prompt: {prompt[:50]}...")
        
        # Use the remix endpoint: POST /videos/{video_id}/remix
        response = self.client.post(
            f"/videos/{video_id}/remix",
            body={"prompt": prompt},
            cast_to=object
        )
        
        logger.info(f"Created remix job from video {video_id}")
        return response

    def list_video_generation_jobs(self, before=None, after=None, limit=10):
        """
        List video generation jobs.
        
        Args:
            before: Cursor for pagination (not supported in current SDK)
            after: Cursor for pagination (not supported in current SDK)
            limit: Maximum number of results (default 10)
        """
        logger.info(f"Listing Sora-2 video generation jobs with limit: {limit}")
        response = self.client.videos.list(
            limit=limit
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
        # The response is a streaming object, we need to read it
        response = self.client.videos.download_content(generation_id, variant="video")
        
        with open(file_path, 'wb') as f:
            # Read the streaming response content
            f.write(response.read())

        logger.info(f"Successfully downloaded video to {file_path}")
        return file_path
    
    def create_remix_video_job(self, remix_video_id, prompt, seconds, size, n_variants=1):
        """
        Create a remix video generation job based on an existing video.
        Note: remix_video_id parameter is not yet supported in OpenAI SDK 2.6.1
        This will create a new video based on the prompt without remix functionality.
        
        Args:
            remix_video_id: ID of the video to remix (currently ignored)
            prompt: Text prompt describing the desired changes
            seconds: Duration in seconds (4, 8, or 12)
            size: Video resolution ("720x1280", "1280x720", "1024x1792", "1792x1024")
            n_variants: Number of video variants to generate (ignored - not supported in SDK)
        """
        logger.info(f"Creating Sora-2 video job (remix not yet supported in SDK) with prompt: {prompt[:50]}...")
        
        # Note: remix_video_id is not supported yet, so we create a regular video
        response = self.client.videos.create(
            model=self.deployment_name,
            prompt=prompt,
            seconds=str(seconds),  # Must be string: '4', '8', or '12'
            size=size
        )
        
        return response.model_dump()
