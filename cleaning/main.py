import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from routes.status import router as status_router
from routes.clean import router as clean_router
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
    logger.info(f"Cleaning service starting on port {PORT}")
    yield
    # Shutdown
    logger.info("Cleaning service shutting down")


# Create FastAPI app
app = FastAPI(
    title="Data Cleaning Service",
    description="Microservice for cleaning and normalizing raw Reddit posts for emotion analysis",
    version="1.0.0",
    lifespan=lifespan,
)

# Register routers
app.include_router(status_router)
app.include_router(clean_router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=PORT,
        reload=False,
    )
