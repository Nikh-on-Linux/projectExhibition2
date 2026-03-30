import pytest
import pytest_asyncio
import logging
from httpx import AsyncClient, ASGITransport

from main import app


pytest_plugins = ("pytest_asyncio",)

# Suppress HuggingFace background thread logging errors
logging.getLogger("transformers.safetensors_conversion").setLevel(logging.ERROR)
logging.getLogger("huggingface_hub").setLevel(logging.WARNING)


@pytest_asyncio.fixture
async def async_client():
    """Async HTTP client for testing FastAPI app"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
