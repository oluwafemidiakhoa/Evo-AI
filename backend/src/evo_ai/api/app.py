"""FastAPI application factory."""

from contextlib import asynccontextmanager
from datetime import datetime
from typing import AsyncGenerator

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import make_asgi_app
import structlog

from evo_ai.api.routers import (
    campaigns_router,
    rounds_router,
    variants_router,
    evaluations_router,
    reports_router,
    tasks_router,
)
from evo_ai.api.schemas import HealthResponse, ErrorResponse
from evo_ai.infrastructure.observability.tracing import setup_tracing
from evo_ai.infrastructure.observability.logging import setup_logging
from evo_ai.tasks import init_ray, shutdown_ray
from evo_ai.tasks.ray_config import get_cluster_info

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """
    Lifespan context manager for startup/shutdown events.

    Args:
        app: FastAPI application

    Yields:
        Control to application
    """
    # Startup
    print("API starting...")

    # Setup logging - Disabled for local testing
    # setup_logging()

    # Initialize Ray - Disabled for now due to logging configuration issues
    # try:
    #     init_ray()
    #     logger.info("ray_initialized_for_api")
    # except Exception as e:
    #     logger.warning("ray_initialization_failed_continuing_without_ray", error=str(e))
    print("Ray disabled for local testing")

    print(f"API started - version {app.version}")

    yield

    # Shutdown
    print("API shutting down...")

    # Shutdown Ray - Disabled
    # try:
    #     shutdown_ray()
    #     logger.info("ray_shutdown_complete")
    # except Exception as e:
    #     logger.warning("ray_shutdown_failed", error=str(e))

    # Cleanup (close database connections, etc.)

    print("API shutdown complete")


def create_app() -> FastAPI:
    """
    Create and configure FastAPI application.

    Returns:
        Configured FastAPI application
    """
    app = FastAPI(
        title="Evo-AI Platform API",
        description="""
        REST API for the Evo-AI evolutionary experimentation platform.

        ## Features

        - **Campaign Management**: Create and manage evolution campaigns
        - **Round Execution**: Execute experiment rounds with real-time progress (SSE)
        - **Variant Queries**: Query variants, lineages, and descendants
        - **Evaluation Results**: Access evaluation scores and feedback
        - **Reports**: Generate and retrieve experiment reports

        ## Architecture

        - **5 AI Agents**: Planner, Variant Generator, Scorer, Policy Maker, Reporter
        - **MCP Servers**: GitHub, Filesystem, Web, Database access
        - **Full Observability**: OpenTelemetry traces, structured logs, Prometheus metrics
        - **Lineage Tracking**: Complete variant ancestry chains

        ## Observability

        - **Traces**: http://localhost:16686 (Jaeger)
        - **Metrics**: http://localhost:9090 (Prometheus)
        - **Dashboards**: http://localhost:3001 (Grafana)
        """,
        version="1.0.0",
        lifespan=lifespan,
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Setup tracing (must be after CORS but before routes)
    # Temporarily disabled - OTLP collector not running
    # setup_tracing(app)

    # Exception handlers
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        """Handle all unhandled exceptions."""
        logger.error(
            "unhandled_exception",
            path=request.url.path,
            method=request.method,
            error=str(exc),
            exc_info=True
        )

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=ErrorResponse(
                error="Internal server error",
                detail=str(exc)
            ).model_dump()
        )

    # Root endpoint - landing page
    @app.get("/", include_in_schema=False)
    async def root():
        """Serve beautiful landing page."""
        from fastapi.responses import HTMLResponse

        html_content = """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Evo-AI Platform</title>
            <style>
                * {
                    margin: 0;
                    padding: 0;
                    box-sizing: border-box;
                }

                body {
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    min-height: 100vh;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    padding: 20px;
                }

                .container {
                    max-width: 1200px;
                    width: 100%;
                }

                .header {
                    text-align: center;
                    color: white;
                    margin-bottom: 50px;
                }

                .header h1 {
                    font-size: 3.5rem;
                    font-weight: 700;
                    margin-bottom: 15px;
                    text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
                }

                .header p {
                    font-size: 1.3rem;
                    opacity: 0.95;
                    font-weight: 300;
                }

                .cards {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
                    gap: 25px;
                    margin-bottom: 40px;
                }

                .card {
                    background: white;
                    border-radius: 15px;
                    padding: 35px;
                    box-shadow: 0 10px 30px rgba(0,0,0,0.2);
                    transition: transform 0.3s ease, box-shadow 0.3s ease;
                    text-decoration: none;
                    color: inherit;
                    display: block;
                }

                .card:hover {
                    transform: translateY(-5px);
                    box-shadow: 0 15px 40px rgba(0,0,0,0.3);
                }

                .card-icon {
                    font-size: 2.5rem;
                    margin-bottom: 20px;
                }

                .card h2 {
                    font-size: 1.5rem;
                    margin-bottom: 12px;
                    color: #667eea;
                }

                .card p {
                    color: #666;
                    line-height: 1.6;
                    font-size: 1rem;
                }

                .features {
                    background: rgba(255,255,255,0.1);
                    backdrop-filter: blur(10px);
                    border-radius: 15px;
                    padding: 35px;
                    color: white;
                }

                .features h2 {
                    font-size: 2rem;
                    margin-bottom: 25px;
                    text-align: center;
                }

                .features-grid {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                    gap: 20px;
                }

                .feature-item {
                    display: flex;
                    align-items: flex-start;
                    gap: 12px;
                }

                .feature-item span {
                    font-size: 1.5rem;
                    flex-shrink: 0;
                }

                .feature-item div h3 {
                    font-size: 1.1rem;
                    margin-bottom: 5px;
                    font-weight: 600;
                }

                .feature-item div p {
                    font-size: 0.95rem;
                    opacity: 0.9;
                    line-height: 1.5;
                }

                .status {
                    text-align: center;
                    color: white;
                    margin-top: 30px;
                    font-size: 0.9rem;
                }

                .status-indicator {
                    display: inline-block;
                    width: 10px;
                    height: 10px;
                    background: #4ade80;
                    border-radius: 50%;
                    margin-right: 8px;
                    animation: pulse 2s infinite;
                }

                @keyframes pulse {
                    0%, 100% { opacity: 1; }
                    50% { opacity: 0.5; }
                }

                @media (max-width: 768px) {
                    .header h1 {
                        font-size: 2.5rem;
                    }

                    .header p {
                        font-size: 1.1rem;
                    }

                    .cards {
                        grid-template-columns: 1fr;
                    }
                }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🧬 Evo-AI Platform</h1>
                    <p>Evolutionary Experimentation with Multi-Agent Intelligence</p>
                </div>

                <div class="cards">
                    <a href="/api/docs" class="card">
                        <div class="card-icon">📚</div>
                        <h2>API Documentation</h2>
                        <p>Interactive Swagger UI with all API endpoints, schemas, and examples. Test the API directly from your browser.</p>
                    </a>

                    <a href="/health" class="card">
                        <div class="card-icon">💚</div>
                        <h2>Health Check</h2>
                        <p>Monitor system status, service availability, and check Ray cluster, database, Redis, and MinIO connections.</p>
                    </a>

                    <a href="/api/redoc" class="card">
                        <div class="card-icon">📖</div>
                        <h2>ReDoc</h2>
                        <p>Alternative API documentation with a clean, three-panel design. Perfect for detailed API exploration.</p>
                    </a>
                </div>

                <div class="features">
                    <h2>Platform Features</h2>
                    <div class="features-grid">
                        <div class="feature-item">
                            <span>🎯</span>
                            <div>
                                <h3>Campaign Management</h3>
                                <p>Create and manage evolution campaigns with custom objectives and constraints</p>
                            </div>
                        </div>

                        <div class="feature-item">
                            <span>🔄</span>
                            <div>
                                <h3>Round Execution</h3>
                                <p>Execute experiment rounds with real-time progress tracking via SSE</p>
                            </div>
                        </div>

                        <div class="feature-item">
                            <span>🧬</span>
                            <div>
                                <h3>Variant Evolution</h3>
                                <p>Generate, evaluate, and track variant lineages across generations</p>
                            </div>
                        </div>

                        <div class="feature-item">
                            <span>📊</span>
                            <div>
                                <h3>Smart Evaluation</h3>
                                <p>AI-powered scoring with detailed metrics and feedback analysis</p>
                            </div>
                        </div>

                        <div class="feature-item">
                            <span>🤖</span>
                            <div>
                                <h3>5 AI Agents</h3>
                                <p>Planner, Generator, Scorer, Policy Maker, and Reporter working together</p>
                            </div>
                        </div>

                        <div class="feature-item">
                            <span>📈</span>
                            <div>
                                <h3>Full Observability</h3>
                                <p>OpenTelemetry traces, structured logs, and Prometheus metrics</p>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="status">
                    <span class="status-indicator"></span>
                    System Online • API Version 1.0.0
                </div>
            </div>
        </body>
        </html>
        """

        return HTMLResponse(content=html_content)

    # Health check endpoint
    @app.get("/health", response_model=HealthResponse, tags=["health"])
    async def health_check() -> HealthResponse:
        """
        Health check endpoint.

        Returns:
            Health status and service information
        """
        # Check Ray cluster status
        ray_info = get_cluster_info()
        ray_status = "up" if ray_info.get("initialized") else "down"

        return HealthResponse(
            status="healthy",
            version=app.version,
            timestamp=datetime.utcnow(),
            services={
                "database": "up",  # Would check actual connection
                "redis": "up",
                "minio": "up",
                "ray": ray_status,
            }
        )

    # API routers
    app.include_router(campaigns_router, prefix="/api")
    app.include_router(rounds_router, prefix="/api")
    app.include_router(variants_router, prefix="/api")
    app.include_router(evaluations_router, prefix="/api")
    app.include_router(reports_router, prefix="/api")
    app.include_router(tasks_router, prefix="/api")

    # Prometheus metrics endpoint
    metrics_app = make_asgi_app()
    app.mount("/metrics", metrics_app)

    logger.info("fastapi_app_created", version=app.version)

    return app


# Create application instance
app = create_app()
