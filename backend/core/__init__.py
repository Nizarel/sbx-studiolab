import logging
from openai import AzureOpenAI, OpenAI
from .config import settings
from .sora import Sora
from .gpt_image import GPTImageClient
import json
from datetime import datetime, timedelta, timezone
from azure.storage.blob import generate_container_sas, ContainerSasPermissions

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Sora client
try:
    sora_client = Sora(
        resource_name=settings.SORA_AOAI_RESOURCE,
        deployment_name=settings.SORA_DEPLOYMENT,
        api_key=settings.SORA_AOAI_API_KEY
    )
    logger.info(
        f"Initialized Sora client with resource: {settings.SORA_AOAI_RESOURCE}")
except Exception as e:
    logger.error(f"Failed to initialize Sora client: {str(e)}")
    sora_client = None

# Initialize GPT-Image-1 client
try:
    # Use Azure OpenAI for image generation if configured, otherwise use OpenAI
    if settings.MODEL_PROVIDER == "azure" and settings.IMAGEGEN_AOAI_RESOURCE and settings.IMAGEGEN_AOAI_API_KEY:
        dalle_client = GPTImageClient(
            api_key=settings.IMAGEGEN_AOAI_API_KEY,
            provider="azure"
        )
        logger.info(f"Initialized GPT-Image-1 client using Azure OpenAI: {settings.IMAGEGEN_AOAI_RESOURCE}")
    elif settings.OPENAI_API_KEY:
        dalle_client = GPTImageClient(
            api_key=settings.OPENAI_API_KEY,
            organization_id=settings.OPENAI_ORG_ID if settings.OPENAI_ORG_ID else None,
            provider="openai"
        )
        logger.info("Initialized GPT-Image-1 client using OpenAI API.")
    else:
        raise ValueError("No image generation credentials configured")
except Exception as e:
    logger.error(f"Failed to initialize GPT-Image-1 client: {str(e)}")
    dalle_client = None

# Initialize LLM client
try:
    llm_client = AzureOpenAI(
        azure_endpoint=f"https://{settings.LLM_AOAI_RESOURCE}.openai.azure.com/",
        api_key=settings.LLM_AOAI_API_KEY,
        # TODO: make configurable. Video generation uses 2025-02-15-preview (does not work with LLM)
        api_version="2025-01-01-preview"
    )
    logger.info(
        f"Initialized LLM client with resource: {settings.LLM_AOAI_RESOURCE}")
except Exception as e:
    logger.error(f"Failed to initialize LLM client: {str(e)}")
    llm_client = None

# Generate blob SAS tokens using managed identity or account key
# TODO: Migrate to user delegation SAS tokens with managed identity
try:
    if settings.AZURE_STORAGE_ACCOUNT_KEY:
        video_sas_token = generate_container_sas(
            account_name=settings.AZURE_STORAGE_ACCOUNT_NAME,
            container_name=settings.AZURE_BLOB_VIDEO_CONTAINER,
            account_key=settings.AZURE_STORAGE_ACCOUNT_KEY,
            permission=ContainerSasPermissions(read=True, list=True),
            expiry=datetime.now(timezone.utc) + timedelta(hours=4),
        )
        logger.info("Generated SAS token for video container.")
    else:
        logger.warning("Storage account key not available - SAS tokens disabled. Use managed identity for storage access.")
        video_sas_token = None
except Exception as e:
    logger.error(f"Failed to generate SAS token for video container: {str(e)}")
    video_sas_token = None

try:
    if settings.AZURE_STORAGE_ACCOUNT_KEY:
        image_sas_token = generate_container_sas(
            account_name=settings.AZURE_STORAGE_ACCOUNT_NAME,
            container_name=settings.AZURE_BLOB_IMAGE_CONTAINER,
            account_key=settings.AZURE_STORAGE_ACCOUNT_KEY,
            permission=ContainerSasPermissions(read=True, list=True),
            expiry=datetime.now(timezone.utc) + timedelta(hours=4),
        )
        logger.info("Generated SAS token for image container.")
    else:
        logger.warning("Storage account key not available - SAS tokens disabled. Use managed identity for storage access.")
        image_sas_token = None
except Exception as e:
    logger.error(f"Failed to generate SAS token for image container: {str(e)}")
    image_sas_token = None
