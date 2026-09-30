"""HippoGrid Main FastAPI Application Entrypoint."""
import sys
from pathlib import Path

# Ensure project root is always in sys.path
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.core.config import get_settings
from backend.api.health import router as health_router
from backend.api.data_quality import router as data_quality_router
from backend.api.sch import router as sch_router
from backend.api.forecast import router as forecast_router
from backend.api.simulate import router as simulate_router
from backend.api.plan import router as plan_router
from backend.api.stress import router as stress_router
from backend.api.feedback import router as feedback_router
from backend.api.continuity import router as continuity_router
from backend.api.federated import router as federated_router

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("hippogrid.main")

settings = get_settings()


from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting {settings.PROJECT_NAME} backend in {settings.ENVIRONMENT} mode.")
    logger.info(f"Tagline: {settings.TAGLINE}")
    yield
    logger.info(f"Shutting down {settings.PROJECT_NAME} backend.")


def create_application() -> FastAPI:
    """Instantiate and configure the FastAPI application."""
    app = FastAPI(
        title=settings.PROJECT_NAME,
        description="Healthcare Infrastructure & Primary-care Planning Optimization Grid (Service-continuity Assurance Twin)",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # CORS Middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include API Routers
    app.include_router(health_router)
    app.include_router(data_quality_router)
    app.include_router(sch_router)
    app.include_router(forecast_router)
    app.include_router(simulate_router)
    app.include_router(plan_router)
    app.include_router(stress_router)
    app.include_router(feedback_router)
    app.include_router(continuity_router)
    app.include_router(federated_router)

    return app


app = create_application()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "backend.main:app",
        host=settings.BACKEND_HOST,
        port=settings.BACKEND_PORT,
        reload=True,
    )
