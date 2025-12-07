"""
FastAPI application para Fintual Portfolio Showcase.

Arquitectura:
- API versioning (v1)
- CORS enabled para frontend
- Swagger docs automático
- Logging configurado
- Error handling global

Alineado con Fintual:
- Goals como abstracción principal
- Métricas: Balance, Depositado, Ganado
- CVaR en métricas de riesgo
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
from datetime import datetime

from app.api.v1.router import api_router

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Crear app FastAPI
app = FastAPI(
    title="Fintual Portfolio Showcase API",
    description="""
    Sistema avanzado de rebalanceo de portfolios con CVaR Risk Metrics.

    Características:
    - **Goals**: Gestión de metas de inversión (alineado con Fintual)
    - **Rebalanceo**: Múltiples estrategias (Simple, CVaR-optimized)
    - **Métricas**: CVaR, Sharpe, Sortino, Max Drawdown
    - **Constraints**: Trading constraints configurables por perfil de riesgo

    Desarrollado por: Gonzalo Díaz
    Postulación: Software Engineer @ Fintual
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# CORS middleware (permitir frontend local)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # React dev server
        "http://localhost:5173",  # Vite dev server
        "https://fintual.cl",     # Fintual (si integran)
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception handlers
@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    """Handler para ValueError (validaciones de negocio)."""
    logger.error(f"ValueError: {exc}")
    return JSONResponse(
        status_code=400,
        content={"detail": str(exc), "type": "ValueError"}
    )


@app.exception_handler(KeyError)
async def key_error_handler(request: Request, exc: KeyError):
    """Handler para KeyError (resource not found)."""
    logger.error(f"KeyError: {exc}")
    return JSONResponse(
        status_code=404,
        content={"detail": f"Resource not found: {exc}", "type": "KeyError"}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handler genérico para errores no manejados."""
    logger.exception("Unhandled exception", exc_info=exc)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "type": type(exc).__name__,
            "message": str(exc)
        }
    )


# Incluir routers
app.include_router(api_router, prefix="/api/v1")


# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint.

    Útil para:
    - Kubernetes liveness/readiness probes
    - Monitoring
    - Verificar que API está up
    """
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "service": "fintual-portfolio-showcase"
    }


# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """
    Root endpoint con información de la API.
    """
    return {
        "message": "Fintual Portfolio Showcase API",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc",
        "health": "/health",
        "api": "/api/v1",
        "developer": "Gonzalo Díaz",
        "github": "https://github.com/gfdiazc/fintual-portfolio-showcase"
    }


# Startup event
@app.on_event("startup")
async def startup_event():
    """Log de inicio de aplicación."""
    logger.info("🚀 Fintual Portfolio Showcase API starting up...")
    logger.info("📊 CVaR-based portfolio optimization enabled")
    logger.info("📖 Swagger docs: http://localhost:8000/docs")


# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Log de cierre de aplicación."""
    logger.info("👋 Fintual Portfolio Showcase API shutting down...")
