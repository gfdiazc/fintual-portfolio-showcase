"""
Pydantic schemas para Rebalance API.

Schemas para solicitar y responder operaciones de rebalanceo.
"""

from decimal import Decimal
from typing import Optional, Dict, List
from pydantic import BaseModel, Field
from enum import Enum


class RebalanceStrategyEnum(str, Enum):
    """Estrategias de rebalanceo disponibles."""
    SIMPLE = "simple"
    CVAR = "cvar"  # TODO: implementar con Gemini
    TAX_EFFICIENT = "tax_efficient"  # TODO: bonus feature


class ConstraintsRequest(BaseModel):
    """
    Constraints de trading para rebalanceo (opcional).

    Si no se proveen, se usan defaults basados en risk_profile del goal.
    """
    min_trade_value: Optional[Decimal] = Field(None, ge=0, description="Valor mínimo de trade")
    rebalance_threshold: Optional[Decimal] = Field(None, ge=0, le=1, description="Threshold para rebalancear")
    max_turnover: Optional[Decimal] = Field(None, ge=0, le=1, description="Máximo turnover permitido")
    min_liquidity: Optional[Decimal] = Field(None, ge=0, le=1, description="Mínimo % en cash")
    allow_fractional_shares: Optional[bool] = Field(None, description="Permitir fracciones de acciones")


class RebalanceRequest(BaseModel):
    """Schema para solicitar rebalanceo de un goal."""
    strategy: RebalanceStrategyEnum = Field(
        default=RebalanceStrategyEnum.SIMPLE,
        description="Estrategia de rebalanceo a usar"
    )
    constraints: Optional[ConstraintsRequest] = Field(
        None,
        description="Constraints personalizados (usa defaults del risk profile si no se proveen)"
    )
    dry_run: bool = Field(
        default=True,
        description="Si True, solo simula (no ejecuta trades). Default True para seguridad."
    )


class TradeResponse(BaseModel):
    """Schema de respuesta para un trade individual."""
    ticker: str
    action: str  # "BUY" or "SELL"
    shares: Decimal
    current_price: Decimal
    value: Decimal
    reason: str

    class Config:
        from_attributes = True


class RebalanceResponse(BaseModel):
    """
    Schema de respuesta para operación de rebalanceo.

    Incluye:
    - Lista de trades a ejecutar
    - Métricas del rebalanceo (costos, turnover, etc)
    - Allocations finales esperadas
    """
    goal_id: str
    strategy_used: str
    dry_run: bool

    # Trades generados
    trades: List[TradeResponse]
    total_trades: int

    # Financials
    total_buy_value: Decimal
    total_sell_value: Decimal
    estimated_cost: Decimal
    net_cash_change: Decimal

    # Metrics
    turnover: Decimal = Field(..., description="Total value rotado")
    turnover_pct: float = Field(..., description="% del portfolio rotado")

    # Allocations
    current_allocations: Dict[str, Decimal] = Field(..., description="Allocations antes del rebalance")
    target_allocations: Dict[str, Decimal] = Field(..., description="Allocations objetivo")
    final_allocations: Dict[str, Decimal] = Field(..., description="Allocations después del rebalance")

    # Drift metrics
    max_drift_before: float = Field(..., description="Máximo drift antes del rebalance")
    max_drift_after: Optional[float] = Field(None, description="Máximo drift después (estimado)")

    # Mensaje para usuario
    message: str = Field(..., description="Mensaje explicativo del resultado")

    class Config:
        from_attributes = True
