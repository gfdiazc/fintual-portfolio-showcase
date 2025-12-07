"""
Pydantic schemas para Goals API.

Separación entre modelos de dominio (app.core.models) y schemas de API:
- Request schemas: validación de input del usuario
- Response schemas: serialización de respuestas
- Alineado con nomenclatura Fintual
"""

from decimal import Decimal
from typing import Optional, Dict
from datetime import datetime
from pydantic import BaseModel, Field

from app.core.models import GoalType, RiskProfile, AssetType


# ============================================================================
# Asset Schemas
# ============================================================================

class AssetCreate(BaseModel):
    """Schema para crear un asset."""
    ticker: str = Field(..., description="Símbolo del activo (ej: AAPL)")
    name: Optional[str] = Field(None, description="Nombre del activo")
    asset_type: AssetType = Field(default=AssetType.STOCK)
    current_price: Decimal = Field(..., gt=0, description="Precio actual")
    currency: str = Field(default="USD")


class AssetResponse(BaseModel):
    """Schema de respuesta para asset."""
    ticker: str
    name: str
    asset_type: AssetType
    current_price: Decimal
    currency: str
    last_updated: datetime

    class Config:
        from_attributes = True  # Pydantic 2.x (antes orm_mode)


# ============================================================================
# Position Schemas
# ============================================================================

class PositionCreate(BaseModel):
    """Schema para agregar posición a portfolio."""
    ticker: str = Field(..., description="Ticker del activo")
    shares: Decimal = Field(..., gt=0, description="Cantidad de acciones")
    target_allocation: Decimal = Field(..., ge=0, le=1, description="Allocation objetivo (0-1)")
    deposited: Decimal = Field(default=Decimal("0"), ge=0, description="Monto depositado")
    asset: AssetCreate


class PositionResponse(BaseModel):
    """Schema de respuesta para posición."""
    ticker: str
    shares: Decimal
    target_allocation: Decimal
    deposited: Decimal
    market_value: Decimal
    current_allocation: Optional[Decimal] = None

    class Config:
        from_attributes = True


# ============================================================================
# Portfolio Schemas
# ============================================================================

class PortfolioResponse(BaseModel):
    """Schema de respuesta para portfolio."""
    id: str
    cash: Decimal
    total_value: Decimal
    total_deposited: Decimal
    total_earned: Decimal
    positions: Dict[str, PositionResponse]

    class Config:
        from_attributes = True


# ============================================================================
# Goal Schemas (Principal abstracción de Fintual)
# ============================================================================

class GoalCreate(BaseModel):
    """
    Schema para crear un Goal.

    Alineado con Fintual:
    - Goals son la abstracción principal (no portfolios)
    - Risk profile determina constraints de rebalanceo
    """
    name: str = Field(..., min_length=1, max_length=100, description="Nombre del goal")
    goal_type: GoalType = Field(..., description="Tipo de goal (retirement, savings, etc)")
    risk_profile: RiskProfile = Field(..., description="Perfil de riesgo (conservative, moderate, risky)")
    initial_cash: Decimal = Field(default=Decimal("0"), ge=0, description="Cash inicial")
    target_amount: Optional[Decimal] = Field(None, gt=0, description="Meta de ahorro (opcional)")
    target_date: Optional[datetime] = Field(None, description="Fecha objetivo (opcional)")


class GoalUpdate(BaseModel):
    """Schema para actualizar un Goal."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    target_amount: Optional[Decimal] = Field(None, gt=0)
    target_date: Optional[datetime] = None


class GoalResponse(BaseModel):
    """
    Schema de respuesta para Goal.

    Incluye métricas clave de Fintual:
    - Balance (valor actual)
    - Depositado Neto (total depositado)
    - Ganado (balance - depositado)
    """
    id: str
    name: str
    goal_type: GoalType
    risk_profile: RiskProfile
    target_amount: Optional[Decimal]
    target_date: Optional[datetime]

    # Métricas principales (alineadas con Fintual)
    balance: Decimal = Field(..., description="Valor actual del goal")
    depositado_neto: Decimal = Field(..., description="Total depositado")
    ganado: Decimal = Field(..., description="Ganancia/pérdida (balance - depositado)")
    progress_percentage: Optional[Decimal] = Field(None, description="% de progreso hacia meta")

    # Portfolio subyacente
    portfolio: PortfolioResponse

    class Config:
        from_attributes = True


class GoalListResponse(BaseModel):
    """Schema para lista de goals."""
    goals: list[GoalResponse]
    total: int
