"""
Sora-2 Backend Testing Script
Tests the upgraded Sora-2 API integration with OpenAI SDK
"""

import os
import sys
import time
import json
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = Path(__file__).parent / ".env"
if env_path.exists():
    load_dotenv(env_path)
    print(f"✓ Loaded environment variables from {env_path}")
else:
    print(f"⚠ No .env file found at {env_path}")
    print("  Using system environment variables only")

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from backend.core.sora import Sora
from backend.models.videos import (
    VideoGenerationRequest,
    VideoRemixRequest,
)


def print_section(title):
    """Print a formatted section header"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def print_result(test_name, success, details=""):
    """Print test result"""
    status = "✅ PASS" if success else "❌ FAIL"
    print(f"{status} - {test_name}")
    if details:
        print(f"   {details}")


def test_sora_client_initialization():
    """Test 1: Verify Sora-2 client initialization"""
    print_section("Test 1: Sora-2 Client Initialization")
    
    try:
        # Get environment variables (using correct names from .env.example)
        resource_name = os.getenv("SORA_AOAI_RESOURCE")
        deployment_name = os.getenv("SORA_DEPLOYMENT")
        api_key = os.getenv("SORA_AOAI_API_KEY")
        
        if not all([resource_name, deployment_name, api_key]):
            print_result(
                "Environment variables check",
                False,
                f"Missing env vars. Found: SORA_AOAI_RESOURCE={bool(resource_name)}, SORA_DEPLOYMENT={bool(deployment_name)}, SORA_AOAI_API_KEY={bool(api_key)}"
            )
            print("\nPlease ensure you have a .env file with:")
            print("  - SORA_AOAI_RESOURCE")
            print("  - SORA_DEPLOYMENT")
            print("  - SORA_AOAI_API_KEY")
            return None
        
        print_result(
            "Environment variables check",
            True,
            f"Resource: {resource_name}, Deployment: {deployment_name}"
        )
        
        # Initialize Sora client
        sora = Sora(
            resource_name=resource_name,
            deployment_name=deployment_name,
            api_key=api_key,
            api_version="2025-01-01-preview"
        )
        
        print_result(
            "Sora-2 client initialization",
            True,
            f"Client initialized with OpenAI SDK v{sora.api_version}"
        )
        
        # Verify client attributes
        has_client = hasattr(sora, 'client')
        has_videos_api = hasattr(sora.client, 'videos') if has_client else False
        
        print_result(
            "OpenAI client structure",
            has_client and has_videos_api,
            f"Has client: {has_client}, Has videos API: {has_videos_api}"
        )
        
        return sora
        
    except Exception as e:
        print_result("Sora-2 client initialization", False, str(e))
        return None


def test_create_video_job(sora):
    """Test 2: Create a video generation job with Sora-2 parameters"""
    print_section("Test 2: Create Video Generation Job")
    
    if not sora:
        print_result("Skipped", False, "No Sora client available")
        return None
    
    try:
        # Test with Sora-2 parameters
        prompt = "A serene sunset over a calm ocean, with gentle waves"
        seconds = 8
        size = "1280x720"
        n_variants = 1
        
        print(f"Creating job with:")
        print(f"  - Prompt: {prompt}")
        print(f"  - Duration: {seconds} seconds")
        print(f"  - Resolution: {size}")
        print(f"  - Variants: {n_variants}")
        
        job = sora.create_video_generation_job(
            prompt=prompt,
            seconds=seconds,
            size=size,
            n_variants=n_variants
        )
        
        print_result(
            "Video generation job creation",
            True,
            f"Job ID: {job.get('id', 'N/A')}"
        )
        
        # Verify response structure
        has_id = 'id' in job
        has_status = 'status' in job
        
        print_result(
            "Response structure",
            has_id and has_status,
            f"Has ID: {has_id}, Has status: {has_status}, Status: {job.get('status', 'N/A')}"
        )
        
        print(f"\nFull response:")
        print(json.dumps(job, indent=2))
        
        return job
        
    except Exception as e:
        print_result("Video generation job creation", False, str(e))
        import traceback
        print(traceback.format_exc())
        return None


def test_get_job_status(sora, job):
    """Test 3: Retrieve job status"""
    print_section("Test 3: Retrieve Job Status")
    
    if not sora or not job:
        print_result("Skipped", False, "No Sora client or job available")
        return None
    
    try:
        job_id = job.get('id')
        print(f"Retrieving status for job: {job_id}")
        
        job_status = sora.get_video_generation_job(job_id)
        
        print_result(
            "Job status retrieval",
            True,
            f"Status: {job_status.get('status', 'N/A')}"
        )
        
        print(f"\nJob details:")
        print(json.dumps(job_status, indent=2))
        
        return job_status
        
    except Exception as e:
        print_result("Job status retrieval", False, str(e))
        import traceback
        print(traceback.format_exc())
        return None


def test_list_jobs(sora):
    """Test 4: List video generation jobs"""
    print_section("Test 4: List Video Generation Jobs")
    
    if not sora:
        print_result("Skipped", False, "No Sora client available")
        return
    
    try:
        print("Listing recent jobs (limit: 5)...")
        
        jobs_response = sora.list_video_generation_jobs(limit=5)
        
        jobs_data = jobs_response.get('data', [])
        
        print_result(
            "List jobs",
            True,
            f"Found {len(jobs_data)} jobs"
        )
        
        if jobs_data:
            print("\nRecent jobs:")
            for i, job in enumerate(jobs_data[:3], 1):
                print(f"  {i}. Job {job.get('id', 'N/A')} - Status: {job.get('status', 'N/A')}")
        
    except Exception as e:
        print_result("List jobs", False, str(e))
        import traceback
        print(traceback.format_exc())


def test_video_with_input_reference(sora):
    """Test 5: Create video with input reference image"""
    print_section("Test 5: Create Video with Input Reference")
    
    if not sora:
        print_result("Skipped", False, "No Sora client available")
        return None
    
    # Check if test image exists
    test_image_path = Path(__file__).parent / "backend" / "static" / "images" / "test_image.jpg"
    
    if not test_image_path.exists():
        print_result(
            "Test image check",
            False,
            f"Test image not found at {test_image_path}. Skipping this test."
        )
        return None
    
    try:
        prompt = "Transform this image into a cinematic video with smooth camera movement"
        seconds = 4
        size = "1280x720"
        
        print(f"Creating job with input reference:")
        print(f"  - Image: {test_image_path.name}")
        print(f"  - Prompt: {prompt}")
        print(f"  - Duration: {seconds} seconds")
        
        job = sora.create_video_generation_job_with_images(
            prompt=prompt,
            image_path=str(test_image_path),
            seconds=seconds,
            size=size,
            n_variants=1
        )
        
        print_result(
            "Video with input reference",
            True,
            f"Job ID: {job.get('id', 'N/A')}"
        )
        
        return job
        
    except Exception as e:
        print_result("Video with input reference", False, str(e))
        import traceback
        print(traceback.format_exc())
        return None


def test_remix_feature(sora, existing_job):
    """Test 6: Create a remix job"""
    print_section("Test 6: Remix Feature")
    
    if not sora:
        print_result("Skipped", False, "No Sora client available")
        return None
    
    if not existing_job or not existing_job.get('id'):
        print_result(
            "Skipped",
            False,
            "No existing job available for remix. Need a completed video first."
        )
        return None
    
    try:
        remix_video_id = existing_job.get('id')
        prompt = "Change the lighting to golden hour, add dramatic clouds"
        seconds = 8
        size = "1280x720"
        
        print(f"Creating remix job:")
        print(f"  - Original video ID: {remix_video_id}")
        print(f"  - Remix prompt: {prompt}")
        print(f"  - Duration: {seconds} seconds")
        
        remix_job = sora.create_remix_video_job(
            remix_video_id=remix_video_id,
            prompt=prompt,
            seconds=seconds,
            size=size,
            n_variants=1
        )
        
        print_result(
            "Remix job creation",
            True,
            f"Remix Job ID: {remix_job.get('id', 'N/A')}"
        )
        
        print(f"\nRemix job details:")
        print(json.dumps(remix_job, indent=2))
        
        return remix_job
        
    except Exception as e:
        print_result("Remix job creation", False, str(e))
        import traceback
        print(traceback.format_exc())
        return None


def test_pydantic_models():
    """Test 7: Verify Pydantic models for Sora-2"""
    print_section("Test 7: Pydantic Models Validation")
    
    try:
        # Test VideoGenerationRequest
        video_request = VideoGenerationRequest(
            prompt="A beautiful landscape",
            seconds=12,
            size="1792x1024",
            n_variants=2
        )
        
        print_result(
            "VideoGenerationRequest model",
            True,
            f"seconds={video_request.seconds}, size={video_request.size}"
        )
        
        # Test VideoRemixRequest
        remix_request = VideoRemixRequest(
            remix_video_id="test-video-123",
            prompt="Make it night time",
            seconds=8,
            size="1280x720",
            n_variants=1
        )
        
        print_result(
            "VideoRemixRequest model",
            True,
            f"remix_video_id={remix_request.remix_video_id}, seconds={remix_request.seconds}"
        )
        
        # Test that old parameters are removed
        try:
            from backend.models.videos import VideoGenerationRequest
            test_request = VideoGenerationRequest(
                prompt="Test",
                n_seconds=10,  # Old parameter
                height=720,    # Old parameter
                width=1280     # Old parameter
            )
            print_result(
                "Old parameters rejected",
                False,
                "Old parameters (n_seconds, height, width) should not be accepted"
            )
        except Exception:
            print_result(
                "Old parameters rejected",
                True,
                "Old parameters correctly rejected by Pydantic"
            )
        
    except Exception as e:
        print_result("Pydantic models validation", False, str(e))


def main():
    """Main test execution"""
    print("\n")
    print("╔" + "═" * 58 + "╗")
    print("║" + " " * 58 + "║")
    print("║" + "  SORA-2 BACKEND TESTING SUITE".center(58) + "║")
    print("║" + " " * 58 + "║")
    print("╚" + "═" * 58 + "╝")
    
    # Run tests
    sora = test_sora_client_initialization()
    test_pydantic_models()
    
    job = test_create_video_job(sora)
    test_get_job_status(sora, job)
    test_list_jobs(sora)
    
    # Optional tests (may fail if no test image or completed video)
    test_video_with_input_reference(sora)
    test_remix_feature(sora, job)
    
    # Summary
    print_section("Test Summary")
    print("""
    Core tests completed! 
    
    Next steps:
    1. If you see ✅ for core tests, the backend is working correctly
    2. Wait for a video to complete, then test download functionality
    3. Test the remix feature with a completed video ID
    4. Move on to frontend integration testing
    
    Note: Some tests may be skipped if prerequisites aren't met.
    """)


if __name__ == "__main__":
    main()
