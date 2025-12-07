"""
API v1 router.

Agrupa todos los endpoints de la versión 1 de la API.
"""

from fastapi import APIRouter

from app.api.v1.endpoints import goals, rebalance

api_router = APIRouter()

# Incluir routers de endpoints
api_router.include_router(goals.router, prefix="/goals", tags=["Goals"])
api_router.include_router(rebalance.router, prefix="/rebalance", tags=["Rebalance"])
