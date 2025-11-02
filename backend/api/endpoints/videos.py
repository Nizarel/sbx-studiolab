import json
import logging
import os
import re
import time
import traceback
from datetime import datetime
from typing import List, Optional
from urllib.parse import urlparse

from fastapi import (
    APIRouter,
    File,
    Form,
    HTTPException,
    Query,
    UploadFile,
    status,
    Depends,
)
from fastapi.responses import FileResponse

from backend.core import llm_client, sora_client, video_sas_token
from backend.core.analyze import VideoAnalyzer, VideoExtractor
from backend.core.config import settings
from backend.core.instructions import (
    analyze_video_system_message,
    filename_system_message,
    video_prompt_enhancement_system_message,
    video_title_system_message,
)
from backend.models.videos import (
    VideoFilenameGenerateRequest,
    VideoFilenameGenerateResponse,
    VideoTitleGenerateRequest,
    VideoTitleGenerateResponse,
    VideoAnalyzeRequest,
    VideoAnalyzeResponse,
    VideoGenerationJobResponse,
    VideoGenerationRequest,
    VideoGenerationWithAnalysisRequest,
    VideoGenerationWithAnalysisResponse,
    VideoPromptEnhancementRequest,
    VideoPromptEnhancementResponse,
    VideoRemixRequest,
    VideoRemixResponse,
)
from backend.core.cosmos_client import CosmosDBService


# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_cosmos_service() -> Optional[CosmosDBService]:
    """Dependency to get Cosmos DB service instance (optional)"""
    try:
        # Check if we have either managed identity or key-based auth configured
        if settings.AZURE_COSMOS_DB_ENDPOINT and (
            settings.USE_MANAGED_IDENTITY or settings.AZURE_COSMOS_DB_KEY
        ):
            return CosmosDBService()
        return None
    except Exception as e:
        import logging

        logger = logging.getLogger(__name__)
        logger.warning(f"Cosmos DB service unavailable: {e}")
        return None


# Log video directory setting
logger.info(f"Video directory: {settings.VIDEO_DIR}")

# Check if clients are available
if sora_client is None:
    logger.error(
        "Sora client is not available. API endpoints may not function properly."
    )
if llm_client is None:
    logger.error(
        "LLM client is not available. API endpoints may not function properly."
    )


router = APIRouter()

# --- /videos API Endpoints ---


@router.post("/jobs", response_model=VideoGenerationJobResponse)
async def create_video_generation_job(
    prompt: str = Form(...),
    n_variants: int = Form(1),
    seconds: int = Form(10),
    size: str = Form("1280x720"),
    folder_path: str = Form(""),
    analyze_video: bool = Form(False),
    # Optional remix video ID
    remix_video_id: Optional[str] = Form(None),
    # Optional single input reference image for Sora-2
    input_reference: Optional[UploadFile] = File(None)
):
    """
    Create video generation job with Sora-2.
    Supports optional single input reference image or remix from existing video.
    """
    try:
        # Ensure Sora client is available
        if sora_client is None:
            raise HTTPException(
                status_code=503,
                detail="Video generation service is currently unavailable. Please check your environment configuration.",
            )

        # Track optional input reference asset for later cleanup/use
        input_reference_path: str | None = None

        # Check if this is a remix request
        if remix_video_id:
            logger.info(f"Creating remix from video: {remix_video_id}")
            job = sora_client.remix_video(
                video_id=remix_video_id,
                prompt=prompt
            )
        # Process input reference image if provided
        elif input_reference:
            # Read image content
            image_content = await input_reference.read()

            # Validate file size (25MB limit)
            if len(image_content) > 25 * 1024 * 1024:
                raise HTTPException(400, "Input reference image exceeds 25MB limit")

            # Validate file type
            if not input_reference.content_type or not input_reference.content_type.startswith('image/'):
                raise HTTPException(400, "Input reference is not a valid image")

            # Save temporarily and get path for Sora-2 API
            import tempfile
            with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as temp_file:
                temp_file.write(image_content)
                input_reference_path = temp_file.name
        
        # Create job using appropriate method
        if input_reference_path:
            # Use input reference method for Sora-2
            job = sora_client.create_video_generation_job_with_images(
                prompt=prompt,
                image_path=input_reference_path,
                seconds=seconds,
                size=size,
                n_variants=n_variants
            )
        else:
            # Use text-only method
            job = sora_client.create_video_generation_job(
                prompt=prompt,
                seconds=seconds,
                size=size,
                n_variants=n_variants
            )
        
        # Create response with metadata
        response_data = {
            **job,
            "folder_path": folder_path,
            "analyze_video": analyze_video
        }
        
        return VideoGenerationJobResponse(**response_data)
        
    except Exception as e:
        logger.error(f"Error creating video job: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/jobs/{job_id}", response_model=VideoGenerationJobResponse)
def get_video_generation_job(job_id: str):
    try:
        # Ensure Sora client is available
        if sora_client is None:
            raise HTTPException(
                status_code=503,
                detail="Video generation service is currently unavailable. Please check your environment configuration.",
            )

        job = sora_client.get_video_generation_job(job_id)
        return VideoGenerationJobResponse(**job)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/jobs", response_model=List[VideoGenerationJobResponse])
def list_video_generation_jobs(limit: int = Query(50, ge=1, le=100)):
    try:
        # Ensure Sora client is available
        if sora_client is None:
            raise HTTPException(
                status_code=503,
                detail="Video generation service is currently unavailable. Please check your environment configuration.",
            )

        jobs = sora_client.list_video_generation_jobs(limit=limit)
        return [VideoGenerationJobResponse(**job) for job in jobs.get("data", [])]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/jobs/{job_id}")
def delete_video_generation_job(job_id: str):
    try:
        # Ensure Sora client is available
        if sora_client is None:
            raise HTTPException(
                status_code=503,
                detail="Video generation service is currently unavailable. Please check your environment configuration.",
            )

        status = sora_client.delete_video_generation_job(job_id)
        return {"deleted": status == 204, "job_id": job_id}
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/jobs/failed")
def delete_failed_video_generation_jobs():
    try:
        # Ensure Sora client is available
        if sora_client is None:
            raise HTTPException(
                status_code=503,
                detail="Video generation service is currently unavailable. Please check your environment configuration.",
            )

        jobs = sora_client.list_video_generation_jobs(limit=50)
        deleted = []
        for job in jobs.get("data", []):
            if job.get("status") == "failed":
                try:
                    sora_client.delete_video_generation_job(job["id"])
                    deleted.append(job["id"])
                except Exception:
                    pass
        return {"deleted_failed_jobs": deleted}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/generate-with-analysis/upload", response_model=VideoGenerationWithAnalysisResponse
)
async def create_video_generation_with_analysis_upload(
    # Unified form-based endpoint to support optional image uploads
    prompt: str = Form(...),
    n_variants: int = Form(1),
    seconds: int = Form(10),
    size: str = Form("1280x720"),
    analyze_video: bool = Form(True),
    folder_path: str = Form(""),
    metadata: Optional[str] = Form(None),
    input_reference: Optional[UploadFile] = File(None),
    cosmos_service: Optional[CosmosDBService] = Depends(get_cosmos_service),
):
    """
    Unified endpoint for Sora-2: create a video generation job (with optional input reference),
    wait for completion, optionally analyze, upload to gallery, and create metadata records.
    """
    import tempfile
    import requests
    from azure.storage.blob import ContentSettings
    from backend.core.azure_storage import AzureBlobStorageService

    try:
        logger.info(f"Cosmos DB service available: {cosmos_service is not None}")
        if sora_client is None:
            raise HTTPException(status_code=503, detail="Video generation service is currently unavailable.")
        if analyze_video and llm_client is None:
            raise HTTPException(status_code=503, detail="LLM service is currently unavailable for video analysis.")

        # Parse optional metadata JSON for folder or other decorations
        metadata_dict = None
        if metadata:
            try:
                metadata_dict = json.loads(metadata)
            except Exception:
                metadata_dict = None

        # Prefer explicit folder_path; fallback to metadata.folder
        selected_folder = folder_path or (metadata_dict.get("folder") if metadata_dict else "")

        # Prepare optional input reference image for Sora-2
        input_reference_path = None
        if input_reference:
            content = await input_reference.read()
            if len(content) > 25 * 1024 * 1024:
                raise HTTPException(400, "Input reference image exceeds 25MB limit")
            if not input_reference.content_type or not input_reference.content_type.startswith("image/"):
                raise HTTPException(400, "Input reference is not a valid image")
            
            # Save to temp file for Sora-2 API
            with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as temp_img:
                temp_img.write(content)
                input_reference_path = temp_img.name

        # Create job with or without input reference
        if input_reference_path:
            job = sora_client.create_video_generation_job_with_images(
                prompt=prompt,
                image_path=input_reference_path,
                seconds=seconds,
                size=size,
                n_variants=n_variants,
            )
        else:
            job = sora_client.create_video_generation_job(
                prompt=prompt,
                seconds=seconds,
                size=size,
                n_variants=n_variants,
            )

        job_response = VideoGenerationJobResponse(**job)
        logger.info(f"Created job {job_response.id}, waiting for completion...")

        # Poll job until completion
        max_wait_time = 300
        poll_interval = 5
        elapsed_time = 0
        while elapsed_time < max_wait_time:
            current_job = sora_client.get_video_generation_job(job_response.id)
            job_response = VideoGenerationJobResponse(**current_job)
            if job_response.status == "succeeded":
                logger.info(f"Job {job_response.id} completed successfully")
                break
            if job_response.status == "failed":
                raise HTTPException(status_code=500, detail=f"Video generation failed: {job_response.failure_reason}")
            time.sleep(poll_interval)
            elapsed_time += poll_interval

        if job_response.status != "succeeded":
            raise HTTPException(status_code=408, detail="Video generation timed out. Please try again.")

        analysis_results = None
        if analyze_video and job_response.generations:
            analysis_results = []
            for generation in job_response.generations:
                generation_id = generation.get("id")
                if not generation_id:
                    continue
                # Download generation video to temp
                with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp_file:
                    temp_file_path = temp_file.name
                try:
                    downloaded_path = sora_client.get_video_generation_video_content(
                        generation_id,
                        os.path.basename(temp_file_path),
                        os.path.dirname(temp_file_path),
                    )

                    # Extract frames and analyze
                    video_extractor = VideoExtractor(downloaded_path)
                    frames = video_extractor.extract_video_frames(interval=2)
                    video_analyzer = VideoAnalyzer(llm_client, settings.LLM_DEPLOYMENT)
                    insights = video_analyzer.video_chat(frames, system_message=analyze_video_system_message)

                    analysis_result = VideoAnalyzeResponse(
                        summary=insights.get("summary", ""),
                        products=insights.get("products", ""),
                        tags=insights.get("tags", []),
                        feedback=insights.get("feedback", ""),
                    )
                    analysis_results.append(analysis_result)

                    # Upload to gallery with metadata
                    azure_service = AzureBlobStorageService()
                    base_filename = generation.get("filename") or f"{re.sub(r'[^a-zA-Z0-9_\-]', '_', prompt.strip()[:50])}_{generation_id}.mp4"
                    final_filename = base_filename
                    normalized_folder = ""
                    if selected_folder and selected_folder != "root":
                        normalized_folder = azure_service.normalize_folder_path(selected_folder)
                        final_filename = f"{normalized_folder}{base_filename}"

                    container_client = azure_service.blob_service_client.get_container_client("videos")
                    blob_client = container_client.get_blob_client(final_filename)

                    # Build upload metadata
                    analysis_data = {
                        "summary": analysis_result.summary,
                        "products": analysis_result.products,
                        "tags": analysis_result.tags,
                        "feedback": analysis_result.feedback,
                        "analyzed_at": datetime.now().isoformat(),
                    }
                    
                    # Generate title from prompt
                    generated_title = _generate_title_from_prompt(prompt)
                    
                    upload_metadata = {
                        "generation_id": generation_id,
                        "prompt": prompt,
                        "title": generated_title,
                        "analysis": analysis_data,
                        "has_analysis": True,
                        "upload_date": datetime.now().isoformat(),
                    }
                    if selected_folder and selected_folder != "root":
                        upload_metadata["folder_path"] = normalized_folder

                    processed_metadata = {}
                    for k, v in upload_metadata.items():
                        if v is not None:
                            processed_metadata[k] = azure_service._preprocess_metadata_value(str(v))

                    with open(downloaded_path, "rb") as video_file:
                        blob_client.upload_blob(
                            data=video_file,
                            content_settings=ContentSettings(content_type="video/mp4"),
                            metadata=processed_metadata,
                            overwrite=True,
                        )

                    blob_url = blob_client.url

                    # Create Cosmos DB metadata record if available
                    if cosmos_service:
                        try:
                            asset_id = final_filename.split(".")[0].split("/")[-1]
                            video_info = os.stat(downloaded_path)
                            cosmos_metadata = {
                                "id": asset_id,
                                "media_type": "video",
                                "blob_name": final_filename,
                                "container": "videos",
                                "url": blob_url,
                                "filename": base_filename,
                                "size": video_info.st_size,
                                "content_type": "video/mp4",
                                "folder_path": normalized_folder,
                                "prompt": prompt,
                                "title": generated_title,
                                "model": "sora-2",
                                "generation_id": generation_id,
                                "analysis": analysis_data,
                                "has_analysis": True,
                                "duration": seconds,
                                "resolution": size,
                                "custom_metadata": {
                                    "n_variants": str(n_variants),
                                    "analyzed": "true",
                                    "job_id": job_response.id,
                                },
                            }
                            cosmos_service.create_asset_metadata(cosmos_metadata)
                        except Exception as cosmos_error:
                            logger.error(f"Failed to create Cosmos DB metadata: {cosmos_error}")

                finally:
                    try:
                        if os.path.exists(temp_file_path):
                            os.unlink(temp_file_path)
                        if "downloaded_path" in locals() and os.path.exists(downloaded_path):
                            os.unlink(downloaded_path)
                    except Exception:
                        pass

        return VideoGenerationWithAnalysisResponse(
            job=job_response,
            analysis_results=analysis_results,
            upload_results=None,
        )
    except Exception as e:
        logger.error(f"Error in unified upload endpoint: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/generate-with-analysis", response_model=VideoGenerationWithAnalysisResponse
)
def create_video_generation_with_analysis(
    req: VideoGenerationWithAnalysisRequest,
    cosmos_service: Optional[CosmosDBService] = Depends(get_cosmos_service),
):
    """
    Create a video generation job and optionally analyze the results
    Enhanced with Cosmos DB metadata storage
    """
    import tempfile
    import requests

    try:
        # Log service availability for debugging
        logger.info(f"Cosmos DB service available: {cosmos_service is not None}")
        logger.info(f"Cosmos DB config - Endpoint: {settings.AZURE_COSMOS_DB_ENDPOINT is not None}, "
                   f"Use Managed Identity: {settings.USE_MANAGED_IDENTITY}, "
                   f"Has Key: {settings.AZURE_COSMOS_DB_KEY is not None}")
        if cosmos_service:
            logger.info("Cosmos DB service initialized successfully for video generation")
        # Ensure required clients are available
        if sora_client is None:
            raise HTTPException(
                status_code=503,
                detail="Video generation service is currently unavailable.",
            )

        if req.analyze_video and llm_client is None:
            raise HTTPException(
                status_code=503,
                detail="LLM service is currently unavailable for video analysis.",
            )

        # Step 1: Create the video generation job with Sora-2
        logger.info(f"Creating Sora-2 video generation job with prompt: {req.prompt}")
        
        # Handle input reference if provided
        if req.input_reference:
            job = sora_client.create_video_generation_job_with_images(
                prompt=req.prompt,
                image_path=req.input_reference,
                seconds=req.seconds,
                size=req.size,
                n_variants=req.n_variants,
            )
        else:
            job = sora_client.create_video_generation_job(
                prompt=req.prompt,
                seconds=req.seconds,
                size=req.size,
                n_variants=req.n_variants,
            )

        job_response = VideoGenerationJobResponse(**job)
        logger.info(f"Created job {job_response.id}, returning immediately for async polling")

        # Return job immediately - frontend will poll for completion
        # Analysis will be done when the frontend fetches the completed job
        return VideoGenerationWithAnalysisResponse(
            job=job_response,
            analysis_results=None  # Will be populated when job completes
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in unified video generation with analysis: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/generations/{generation_id}/content", status_code=status.HTTP_200_OK)
def download_generation_content(
    generation_id: str,
    file_name: str,
    target_folder: Optional[str] = None,
    as_gif: bool = False,
):
    """
    Download video or GIF content for a specific generation.

    Args:
        generation_id: The ID of the generation
        file_name: Name to save the file as
        target_folder: Optional folder to save to (defaults to settings.VIDEO_DIR or 'gifs')
        as_gif: Whether to download as GIF instead of MP4

    Returns:
        FileResponse with the requested content
    """
    try:
        # Ensure Sora client is available
        if sora_client is None:
            raise HTTPException(
                status_code=503,
                detail="Video generation service is currently unavailable. Please check your environment configuration.",
            )

        # Use settings from config if target_folder not provided
        if not target_folder:
            target_folder = settings.VIDEO_DIR if not as_gif else "gifs"

        logger.info(
            f"Downloading {'GIF' if as_gif else 'video'} content for generation {generation_id}"
        )

        if as_gif:
            file_path = sora_client.get_video_generation_gif_content(
                generation_id, file_name, target_folder
            )
        else:
            file_path = sora_client.get_video_generation_video_content(
                generation_id, file_name, target_folder
            )

        # Verify the file was downloaded successfully
        if not os.path.isfile(file_path):
            raise FileNotFoundError(f"Downloaded file not found at {file_path}")

        logger.info(f"Successfully downloaded file. Returning: {file_path}")

        # Use FileResponse to return the file
        return FileResponse(
            path=file_path,
            filename=file_name,
            media_type="image/gif" if as_gif else "video/mp4",
        )

    except Exception as e:
        logger.error(f"Error downloading content: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error downloading content: {str(e)}",
        )


@router.post("/analyze", response_model=VideoAnalyzeResponse)
def analyze_video(req: VideoAnalyzeRequest):
    """
    Analyze a video by extracting frames and generating insights using an LLM.

    Args:
        video_path: Video blob name (e.g., 'my-video.mp4') or full URL. If blob name is provided, 
                   it will be downloaded using managed identity from the 'videos' container.

    Returns:
        Response containing summary, products, tags, and feedback generated by the LLM.
    """
    import tempfile

    try:
        video_path = req.video_path

        # Check if it's a blob name (no URL scheme) or a full Azure URL
        if video_path.startswith('http://') or video_path.startswith('https://'):
            # Extract blob name from URL
            # Pattern: https://<account>.blob.core.windows.net/<container>/<blob_name>
            pattern = r"^https://[a-z0-9]+\.blob\.core\.windows\.net/[a-z0-9]+/(.+?)(?:\?.*)?$"
            match = re.match(pattern, video_path)
            if match:
                blob_name = match.group(1)
            else:
                raise ValueError("Invalid Azure blob storage URL")
        else:
            # Assume it's just the blob name
            blob_name = video_path

        logger.info(f"Downloading video '{blob_name}' from Azure Blob Storage using managed identity")

        # Download video content using managed identity
        from backend.core.azure_storage import AzureBlobStorageService
        azure_storage_service = AzureBlobStorageService()
        video_content, content_type = azure_storage_service.get_asset_content(blob_name, 'videos')
        
        if video_content is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Video '{blob_name}' not found in videos container"
            )

        # Create a temporary file to store the downloaded video
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp_file:
            temp_file.write(video_content)
            temp_file_path = temp_file.name

        logger.info(f"Video downloaded to temporary file: {temp_file_path}")

        try:
            # extract frames from the video each 2 seconds using the local file
            video_extractor = VideoExtractor(temp_file_path)
            frames = video_extractor.extract_video_frames(interval=2)

            video_analyzer = VideoAnalyzer(llm_client, settings.LLM_DEPLOYMENT)
            insights = video_analyzer.video_chat(
                frames, system_message=analyze_video_system_message
            )
            summary = insights.get("summary")
            products = insights.get("products")
            tags = insights.get("tags")
            feedback = insights.get("feedback")

            return VideoAnalyzeResponse(
                summary=summary, products=products, tags=tags, feedback=feedback
            )

        finally:
            # Clean up the temporary file
            try:
                os.unlink(temp_file_path)
                logger.info(f"Cleaned up temporary file: {temp_file_path}")
            except Exception as cleanup_error:
                logger.warning(
                    f"Failed to clean up temporary file {temp_file_path}: {cleanup_error}"
                )

    except Exception as e:
        logger.error(f"Error analyzing video: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, detail="Error analyzing video. Please try again later."
        )


@router.post("/prompt/enhance", response_model=VideoPromptEnhancementResponse)
def enhance_video_prompt(req: VideoPromptEnhancementRequest):
    """
    Improves a given text to video prompt considering best practices for the video generation model.

    Args:
        original_prompt: Original text to video prompt.

    Returns:
        enhanced_prompt: Improved text to video prompt.
    """
    try:
        # Ensure LLM client is available
        if llm_client is None:
            raise HTTPException(
                status_code=503,
                detail="LLM service is currently unavailable. Please check your environment configuration.",
            )

        original_prompt = req.original_prompt
        # Call the LLM to enhance the prompt
        messages = [
            {"role": "system", "content": video_prompt_enhancement_system_message},
            {"role": "user", "content": original_prompt},
        ]
        response = llm_client.chat.completions.create(
            messages=messages,
            model=settings.LLM_DEPLOYMENT,
            response_format={"type": "json_object"},
        )
        enhanced_prompt = json.loads(response.choices[0].message.content).get("prompt")
        return VideoPromptEnhancementResponse(enhanced_prompt=enhanced_prompt)

    except Exception as e:
        logger.error(f"Error enhancing video prompt: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/filename/generate", response_model=VideoFilenameGenerateResponse)
def generate_video_filename(req: VideoFilenameGenerateRequest):
    """
    Creates a concise prefix for a file based on the text prompt used for creating the image or video.

    Args:
        prompt: Text prompt.
        gen_id: Optional generation ID to append for uniqueness.
        extension: Optional file extension to append (e.g., ".mp4").

    Returns:
        filename: Generated filename Example: "xbox_venice_beach_sunset_2023_12345.mp4"
    """

    try:
        # Ensure LLM client is available
        if llm_client is None:
            raise HTTPException(
                status_code=503,
                detail="LLM service is currently unavailable. Please check your environment configuration.",
            )

        # Validate prompt
        if not req.prompt or not req.prompt.strip():
            raise HTTPException(status_code=400, detail="Prompt must not be empty.")

        # Call the LLM to enhance the prompt
        messages = [
            {"role": "system", "content": filename_system_message},
            {"role": "user", "content": req.prompt},
        ]
        response = llm_client.chat.completions.create(
            messages=messages,
            model=settings.LLM_DEPLOYMENT,
            response_format={"type": "json_object"},
        )
        filename = json.loads(response.choices[0].message.content).get(
            "filename_prefix"
        )

        # Validate and sanitize filename
        if not filename or not filename.strip():
            raise HTTPException(
                status_code=500, detail="Failed to generate a valid filename prefix."
            )
        # Remove invalid characters for most filesystems
        filename = re.sub(r"[^a-zA-Z0-9_\-]", "_", filename.strip())

        # add generation id for uniqueness and extension if provided
        if req.gen_id:
            filename += f"_{req.gen_id}"
        if req.extension:
            ext = req.extension.lstrip(".")
            filename += f".{ext}"

        return VideoFilenameGenerateResponse(filename=filename)

    except Exception as e:
        logger.error(f"Error generating filename: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


def _generate_title_from_prompt(prompt: str) -> str:
    """
    Helper function to generate a video title from a prompt.
    Returns the generated title or falls back to prompt substring on error.
    
    Args:
        prompt: The video generation prompt
    
    Returns:
        str: Generated title or fallback
    """
    try:
        if not llm_client or not prompt or not prompt.strip():
            # Fallback to prompt-based title
            return prompt.strip()[:50] + ('...' if len(prompt.strip()) > 50 else '')
        
        messages = [
            {"role": "system", "content": video_title_system_message},
            {"role": "user", "content": prompt},
        ]
        response = llm_client.chat.completions.create(
            messages=messages,
            model=settings.LLM_DEPLOYMENT,
            response_format={"type": "json_object"},
            temperature=0.7,
        )
        
        title = json.loads(response.choices[0].message.content).get("title")
        
        if title and title.strip():
            return title.strip()
        else:
            # Fallback to prompt-based title
            return prompt.strip()[:50] + ('...' if len(prompt.strip()) > 50 else '')
            
    except Exception as e:
        logger.warning(f"Failed to generate title, using prompt: {str(e)}")
        # Fallback to prompt-based title
        return prompt.strip()[:50] + ('...' if len(prompt.strip()) > 50 else '')


@router.post("/title/generate", response_model=VideoTitleGenerateResponse)
def generate_video_title(req: VideoTitleGenerateRequest):
    """
    Generate an engaging title for a video based on its prompt.
    Uses GPT-5-nano for fast, creative title generation.
    
    Args:
        prompt: The video generation prompt
    
    Returns:
        title: Generated creative video title
    """
    try:
        # Ensure LLM client is available
        if llm_client is None:
            raise HTTPException(
                status_code=503,
                detail="LLM service is currently unavailable. Please check your environment configuration.",
            )

        # Validate prompt
        if not req.prompt or not req.prompt.strip():
            raise HTTPException(status_code=400, detail="Prompt must not be empty.")

        # Call the LLM to generate title
        messages = [
            {"role": "system", "content": video_title_system_message},
            {"role": "user", "content": req.prompt},
        ]
        response = llm_client.chat.completions.create(
            messages=messages,
            model=settings.LLM_DEPLOYMENT,
            response_format={"type": "json_object"},
            temperature=0.7,  # Slightly higher for creativity
        )
        
        title = json.loads(response.choices[0].message.content).get("title")

        # Validate title
        if not title or not title.strip():
            raise HTTPException(
                status_code=500, detail="Failed to generate a valid title."
            )

        return VideoTitleGenerateResponse(title=title.strip())
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating video title: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/remix", response_model=VideoRemixResponse)
async def create_remix_video_job(req: VideoRemixRequest):
    """
    Create a remix video generation job based on an existing video.
    Uses Sora-2's remix feature to apply targeted edits to a video.
    
    Args:
        req: VideoRemixRequest containing remix_video_id, prompt, seconds, size, n_variants
    
    Returns:
        VideoRemixResponse with job details and original video ID
    """
    try:
        # Ensure Sora client is available
        if sora_client is None:
            raise HTTPException(
                status_code=503,
                detail="Video generation service is currently unavailable. Please check your environment configuration.",
            )

        logger.info(f"Creating remix job for video {req.remix_video_id} with prompt: {req.prompt}")
        
        # Create remix job using Sora-2 remix feature
        job = sora_client.create_remix_video_job(
            remix_video_id=req.remix_video_id,
            prompt=req.prompt,
            seconds=req.seconds,
            size=req.size,
            n_variants=req.n_variants
        )
        
        job_response = VideoGenerationJobResponse(**job)
        
        return VideoRemixResponse(
            job=job_response,
            original_video_id=req.remix_video_id
        )
        
    except Exception as e:
        logger.error(f"Error creating remix job: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

