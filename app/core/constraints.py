"""
Trading constraints para rebalanceo de portfolios.

Constraints típicos en inversión real:
- Minimum trade size (lot sizes)
- Rebalance thresholds (no rebalancear cambios pequeños)
- Maximum turnover (límite de rotación)
- Minimum liquidity (mantener % en cash)
- Maximum position size (diversificación)
"""

from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field, field_validator


class TradingConstraints(BaseModel):
    """
    Constraints de trading para rebalanceo.

    Alineado con prácticas de Fintual:
    - Mantener mínimo 50% en liquidez para goals muy conservadores
    - Evitar trades muy pequeños (costo de transacción)
    - Threshold para evitar micro-ajustes
    """

    min_trade_value: Decimal = Field(
        default=Decimal("10.00"),
        description="Valor mínimo de un trade (evitar micro-trades)"
    )

    rebalance_threshold: Decimal = Field(
        default=Decimal("0.05"),
        description="Threshold para rebalancear (5% drift = rebalancear)"
    )

    max_turnover: Optional[Decimal] = Field(
        default=None,
        description="Máximo % del portfolio a rotar en un rebalance (None = sin límite)"
    )

    min_liquidity: Decimal = Field(
        default=Decimal("0.02"),
        description="Mínimo % de cash a mantener (2% default para emergencias)"
    )

    max_position_size: Optional[Decimal] = Field(
        default=None,
        description="Máximo % que puede representar una posición (diversificación)"
    )

    allow_fractional_shares: bool = Field(
        default=True,
        description="Si permite comprar fracciones de acciones (Fintual sí permite)"
    )

    transaction_cost_bps: Decimal = Field(
        default=Decimal("10"),
        description="Costo de transacción en basis points (0.10% default)"
    )

    @field_validator('rebalance_threshold', 'min_liquidity')
    @classmethod
    def validate_percentage(cls, v: Decimal, info) -> Decimal:
        """Validar que porcentajes estén entre 0 y 1."""
        if not 0 <= v <= 1:
            raise ValueError(f"{info.field_name} debe estar entre 0 y 1, got {v}")
        return v

    @field_validator('max_turnover', 'max_position_size')
    @classmethod
    def validate_optional_percentage(cls, v: Optional[Decimal], info) -> Optional[Decimal]:
        """Validar porcentajes opcionales."""
        if v is not None and not 0 <= v <= 1:
            raise ValueError(f"{info.field_name} debe estar entre 0 y 1, got {v}")
        return v

    @field_validator('min_trade_value')
    @classmethod
    def validate_positive(cls, v: Decimal) -> Decimal:
        """Validar que valores sean positivos."""
        if v <= 0:
            raise ValueError(f"min_trade_value debe ser > 0, got {v}")
        return v

    @field_validator('transaction_cost_bps')
    @classmethod
    def validate_bps(cls, v: Decimal) -> Decimal:
        """Validar que basis points sean razonables."""
        if not 0 <= v <= 1000:  # 0-10%
            raise ValueError(f"transaction_cost_bps debe estar entre 0 y 1000, got {v}")
        return v


class ConservativeConstraints(TradingConstraints):
    """
    Constraints para perfiles conservadores (Conservative Clooney).

    - 50% mínimo en liquidez
    - Threshold alto (evitar muchos trades)
    - Turnover bajo
    """
    min_liquidity: Decimal = Field(default=Decimal("0.50"))
    rebalance_threshold: Decimal = Field(default=Decimal("0.10"))  # 10% drift
    max_turnover: Decimal = Field(default=Decimal("0.20"))  # Max 20% rotación


class ModerateConstraints(TradingConstraints):
    """
    Constraints para perfiles moderados (Moderate Pitt).

    - 10% mínimo en liquidez
    - Threshold medio
    - Turnover medio
    """
    min_liquidity: Decimal = Field(default=Decimal("0.10"))
    rebalance_threshold: Decimal = Field(default=Decimal("0.05"))  # 5% drift
    max_turnover: Decimal = Field(default=Decimal("0.50"))  # Max 50% rotación


class RiskyConstraints(TradingConstraints):
    """
    Constraints para perfiles riesgosos (Risky Norris).

    - 2% mínimo en liquidez (solo emergencias)
    - Threshold bajo (rebalancear frecuente)
    - Sin límite de turnover
    """
    min_liquidity: Decimal = Field(default=Decimal("0.02"))
    rebalance_threshold: Decimal = Field(default=Decimal("0.02"))  # 2% drift
    max_turnover: Optional[Decimal] = Field(default=None)  # Sin límite
