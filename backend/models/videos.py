from pydantic import BaseModel, Field
from typing import List, Optional, Dict

# Models used by video API endpoints


class VideoPromptEnhancementRequest(BaseModel):
    """Request model for enhancing video generation prompts"""
    original_prompt: str = Field(...,
                                 description="Prompt to enhance for video generation")


class VideoPromptEnhancementResponse(BaseModel):
    """Response model for enhanced video generation prompts"""
    enhanced_prompt: str = Field(...,
                                 description="Enhanced prompt for video generation")


class VideoGenerationRequest(BaseModel):
    """Request model for generating videos using Sora-2"""
    prompt: str = Field(...,
                        description="Prompt describing the video to generate")
    n_variants: int = Field(
        1, description="Number of video variants to generate")
    seconds: int = Field(10, description="Length of the video in seconds (4, 8, or 12)")
    size: str = Field("1280x720", description="Video resolution (720x1280, 1280x720, 1024x1792, 1792x1024)")
    input_reference: Optional[str] = Field(
        None, description="Path to input reference image for video generation")
    remix_video_id: Optional[str] = Field(
        None, description="ID of video to remix (for remix feature)")


class VideoGenerationJobResponse(BaseModel):
    """Response model for a video generation job"""
    id: str = Field(..., description="Job ID")
    status: str = Field(..., description="Current status of the job (queued, in_progress, completed, failed, cancelled)")
    prompt: Optional[str] = Field(None, description="Original prompt used for generation")
    n_variants: Optional[int] = Field(None, description="Number of video variants requested")
    seconds: Optional[int] = Field(None, description="Length of the video in seconds")
    size: Optional[str] = Field(None, description="Video resolution")
    generations: Optional[list] = Field(
        None, description="List of generated videos")
    created_at: Optional[int] = Field(
        None, description="Unix timestamp of creation time")
    finished_at: Optional[int] = Field(
        None, description="Unix timestamp of completion time")
    failure_reason: Optional[str] = Field(
        None, description="Reason for failure if job failed")


class VideoAnalyzeRequest(BaseModel):
    """Request model for analyzing video content"""
    video_path: str = Field(...,
                            description="Path to the video file on Azure Blob Storage. Supports a full URL with or without a SAS token.")


class VideoAnalyzeResponse(BaseModel):
    """Response model for video analysis results"""
    summary: str = Field(..., description="Summary of the video content")
    products: str = Field(..., description="Products identified in the video")
    tags: List[str] = Field(...,
                            description="List of metadata tags for the video")
    feedback: str = Field(...,
                          description="Feedback on the video quality/content")


class VideoFilenameGenerateRequest(BaseModel):
    """Request model for generating a filename based on content"""
    prompt: str = Field(...,
                        description="Prompt describing the content to name")
    gen_id: Optional[str] = Field(
        None, description="Video generation id for unique naming"
    )
    extension: Optional[str] = Field(
        None, description="File extension for the generated filename, e.g., .mp4"
    )


class VideoFilenameGenerateResponse(BaseModel):
    """Response model for filename generation"""
    filename: str = Field(..., description="Generated filename")


class VideoTitleGenerateRequest(BaseModel):
    """Request model for generating a video title"""
    prompt: str = Field(..., description="Prompt describing the video content")


class VideoTitleGenerateResponse(BaseModel):
    """Response model for video title generation"""
    title: str = Field(..., description="Generated video title")


class VideoGenerationWithAnalysisRequest(BaseModel):
    """Request model for generating videos with optional analysis"""
    prompt: str = Field(...,
                        description="Prompt describing the video to generate")
    n_variants: int = Field(
        1, description="Number of video variants to generate")
    seconds: int = Field(10, description="Length of the video in seconds (4, 8, or 12)")
    size: str = Field("1280x720", description="Video resolution (720x1280, 1280x720, 1024x1792, 1792x1024)")
    input_reference: Optional[str] = Field(
        None, description="Path to input reference image")
    analyze_video: bool = Field(
        False, description="Whether to analyze the generated videos")
    metadata: Optional[Dict[str, str]] = Field(
        None, description="Additional metadata for the job")


class VideoGenerationWithAnalysisResponse(BaseModel):
    """Response model for video generation with analysis"""
    job: VideoGenerationJobResponse = Field(...,
                                            description="Video generation job details")
    analysis_results: Optional[List[VideoAnalyzeResponse]] = Field(
        None, description="Analysis results for each generated video (if analysis was requested)")
    upload_results: Optional[List[Dict[str, str]]] = Field(
        None, description="Upload results for each video to gallery")


class VideoRemixRequest(BaseModel):
    """Request model for remixing an existing video"""
    remix_video_id: str = Field(...,
                                description="ID of the video to remix")
    prompt: str = Field(...,
                        description="Prompt describing the desired changes")
    n_variants: int = Field(
        1, description="Number of remix variants to generate")
    seconds: int = Field(10, description="Length of the remix video in seconds (4, 8, or 12)")
    size: str = Field("1280x720", description="Video resolution (720x1280, 1280x720, 1024x1792, 1792x1024)")


class VideoRemixResponse(BaseModel):
    """Response model for video remix job"""
    job: VideoGenerationJobResponse = Field(...,
                                            description="Remix job details")
    original_video_id: str = Field(...,
                                   description="ID of the original video that was remixed")
