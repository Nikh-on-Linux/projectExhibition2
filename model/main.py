import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from routes.status import router as status_router
from routes.analyze import router as analyze_router
from config import PORT

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle events"""
    # Startup
    logger.info(f"Model service starting on port {PORT}")
    yield
    # Shutdown
    logger.info("Model service shutting down")


# Create FastAPI app
app = FastAPI(
    title="Emotion Analysis Service",
    description="Microservice for emotion classification on cleaned posts",
    version="1.0.0",
    lifespan=lifespan,
)

# Register routers
app.include_router(status_router)
app.include_router(analyze_router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=PORT,
        reload=False,
    )
