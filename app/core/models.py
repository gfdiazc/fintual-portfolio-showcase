"""
Core domain models para el sistema de gestión de portfolios.

Nomenclatura alineada con Fintual:
- Goal: Objetivo de inversión del usuario (lo que Fintual llama "goals")
- Portfolio: Composición interna de activos
- Asset: Activo financiero individual (similar a conceptual_asset de Fintual)

Filosofía: Máxima sofisticación técnica en el backend, máxima simplicidad en la UX.
"""

from decimal import Decimal
from typing import Dict, Optional
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, field_validator, computed_field


class AssetType(str, Enum):
    """Tipos de activos soportados."""
    STOCK = "stock"
    BOND = "bond"
    FUND = "fund"
    ETF = "etf"


class Asset(BaseModel):
    """
    Representa un activo financiero individual.

    Inspirado en conceptual_asset y real_asset de Fintual API.
    Principio SOLID: Single Responsibility - solo maneja datos del activo.
    """
    ticker: str = Field(..., description="Símbolo del activo (ej: AAPL, VTI)")
    name: str = Field(default="", description="Nombre completo del activo")
    asset_type: AssetType = Field(default=AssetType.STOCK, description="Tipo de activo")
    current_price: Decimal = Field(..., gt=0, description="Precio actual de mercado (NAV)")
    last_updated: datetime = Field(default_factory=datetime.now)
    currency: str = Field(default="USD", description="Moneda del activo")

    @field_validator('ticker')
    @classmethod
    def validate_ticker(cls, v: str) -> str:
        """Normaliza ticker a mayúsculas."""
        return v.upper().strip()

    class Config:
        frozen = False  # Permite actualización de precio
        json_schema_extra = {
            "example": {
                "ticker": "AAPL",
                "name": "Apple Inc.",
                "asset_type": "stock",
                "current_price": 180.50,
                "currency": "USD"
            }
        }


class Position(BaseModel):
    """
    Representa una posición (tenencia) dentro del portfolio.

    Incluye tanto la tenencia actual (shares) como la allocation objetivo.
    """
    asset: Asset
    shares: Decimal = Field(..., ge=0, description="Cantidad de activos poseídos")
    target_allocation: Decimal = Field(
        ..., ge=0, le=1,
        description="Porcentaje objetivo del portfolio (0-1). Ej: 0.6 = 60%"
    )
    deposited: Decimal = Field(
        default=Decimal(0), ge=0,
        description="Monto depositado originalmente en esta posición (para tracking)"
    )

    @computed_field
    @property
    def market_value(self) -> Decimal:
        """
        Valor de mercado actual de la posición.
        Similar al cálculo de NAV en Fintual.
        """
        return self.shares * self.asset.current_price

    class Config:
        json_schema_extra = {
            "example": {
                "asset": {
                    "ticker": "AAPL",
                    "name": "Apple Inc.",
                    "asset_type": "stock",
                    "current_price": 180.50,
                    "currency": "USD"
                },
                "shares": 10,
                "target_allocation": 0.6,
                "deposited": 1750.00
            }
        }


class Portfolio(BaseModel):
    """
    Portfolio interno: composición de activos.

    Representa la estructura interna de inversiones.
    No es lo que el usuario ve directamente (eso es Goal).

    Métricas clave (estilo Fintual):
    - total_value: Balance actual
    - total_deposited: Depositado Neto
    - total_earned: Ganado (Balance - Depositado Neto)
    """
    id: str = Field(..., description="Identificador único del portfolio")
    positions: Dict[str, Position] = Field(
        default_factory=dict,
        description="Posiciones indexadas por ticker"
    )
    cash: Decimal = Field(default=Decimal(0), ge=0, description="Efectivo disponible")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    @computed_field
    @property
    def total_value(self) -> Decimal:
        """
        Balance: Valor total del portfolio incluyendo cash.
        Equivalente a NAV en Fintual.
        """
        positions_value = sum(pos.market_value for pos in self.positions.values())
        return positions_value + self.cash

    @computed_field
    @property
    def total_deposited(self) -> Decimal:
        """
        Depositado Neto: Total depositado en el portfolio.
        Métrica core de Fintual.
        """
        return sum(pos.deposited for pos in self.positions.values()) + self.cash

    @computed_field
    @property
    def total_earned(self) -> Decimal:
        """
        Ganado: Ganancia/pérdida total.
        Métrica core de Fintual: Balance - Depositado Neto.
        """
        return self.total_value - self.total_deposited

    def get_current_allocation(self, ticker: str) -> Decimal:
        """
        Calcula allocation actual de un ticker.

        Returns:
            Decimal entre 0 y 1 (porcentaje del portfolio)
        """
        if self.total_value == 0:
            return Decimal(0)

        position = self.positions.get(ticker)
        if not position:
            return Decimal(0)

        return position.market_value / self.total_value

    def get_current_allocations(self) -> Dict[str, Decimal]:
        """
        Calcula la asignación actual de todos los tickers en el portafolio.

        Returns:
            Un diccionario con ticker -> asignación actual (Decimal).
        """
        allocations = {}
        if self.total_value == 0:
            return {ticker: Decimal(0) for ticker in self.positions}

        for ticker in self.positions.keys():
            allocations[ticker] = self.get_current_allocation(ticker)
        return allocations

    def add_position(
        self,
        asset: Asset,
        shares: Decimal,
        target_allocation: Decimal,
        deposited: Decimal = Decimal(0)
    ) -> None:
        """
        Agrega o actualiza una posición en el portfolio.

        Args:
            asset: Activo a agregar
            shares: Cantidad de activos
            target_allocation: Porcentaje objetivo (0-1)
            deposited: Monto depositado originalmente
        """
        self.positions[asset.ticker] = Position(
            asset=asset,
            shares=shares,
            target_allocation=target_allocation,
            deposited=deposited
        )
        self.updated_at = datetime.now()

    def validate_allocations(self) -> bool:
        """
        Valida que target allocations sumen <= 1 (100%).

        Returns:
            True si allocations son válidas
        """
        total = sum(pos.target_allocation for pos in self.positions.values())
        return total <= Decimal(1)

    def get_allocation_drift(self) -> Dict[str, Decimal]:
        """
        Calcula el drift (desviación) entre allocation actual y objetivo.

        Returns:
            Dict con ticker -> drift (positivo = comprar, negativo = vender)
        """
        drifts = {}
        for ticker, position in self.positions.items():
            current = self.get_current_allocation(ticker)
            target = position.target_allocation
            drifts[ticker] = target - current
        return drifts

    def get_current_allocations_as_array(self) -> 'np.ndarray':
        """
        Returns current portfolio allocations as a NumPy array.
        The order of the array is consistent with self.positions.keys().
        """
        import numpy as np
        allocations = [self.get_current_allocation(ticker) for ticker in self.positions.keys()]
        return np.array([float(a) for a in allocations])

    def get_target_allocations_as_array(self) -> 'np.ndarray':
        """
        Returns target portfolio allocations as a NumPy array.
        The order of the array is consistent with self.positions.keys().
        """
        import numpy as np
        allocations = [p.target_allocation for p in self.positions.values()]
        return np.array([float(a) for a in allocations])


    class Config:
        json_schema_extra = {
            "example": {
                "id": "port_123",
                "positions": {
                    "AAPL": {
                        "asset": {"ticker": "AAPL", "current_price": 180.50},
                        "shares": 10,
                        "target_allocation": 0.6,
                        "deposited": 1750.00
                    }
                },
                "cash": 500.00
            }
        }


class RiskProfile(str, Enum):
    """
    Perfiles de riesgo estilo Fintual.

    Nomenclatura lúdica inspirada en fondos de Fintual:
    - Risky Norris: Más arriesgado
    - Moderate Pitt: Moderado
    - Conservative Clooney: Conservador
    - Very Conservative Streep: Muy conservador
    """
    VERY_CONSERVATIVE = "very_conservative"  # Very Conservative Streep
    CONSERVATIVE = "conservative"  # Conservative Clooney
    MODERATE = "moderate"  # Moderate Pitt
    RISKY = "risky"  # Risky Norris


class GoalType(str, Enum):
    """Tipos de objetivos de inversión."""
    RETIREMENT = "retirement"  # Jubilación
    SAVINGS = "savings"  # Ahorro general
    VACATION = "vacation"  # Vacaciones
    HOUSE = "house"  # Compra de casa
    EDUCATION = "education"  # Educación
    EMERGENCY = "emergency"  # Fondo de emergencia
    OTHER = "other"  # Otro objetivo


class Goal(BaseModel):
    """
    Goal: Objetivo de inversión del usuario.

    Concepto principal en Fintual - cada usuario puede tener múltiples goals.
    Cada goal tiene su propio portfolio, riesgo y plazo.

    Esta es la abstracción que ve el usuario (UX simple).
    Internamente contiene un Portfolio (complejidad oculta).

    Filosofía Fintual: Simplicidad externa, sofisticación interna.
    """
    id: str = Field(..., description="Identificador único del goal")
    name: str = Field(..., description="Nombre del objetivo (ej: 'Jubilación 2050')")
    goal_type: GoalType = Field(..., description="Tipo de objetivo")
    risk_profile: RiskProfile = Field(..., description="Perfil de riesgo del goal")
    portfolio: Portfolio = Field(..., description="Portfolio interno (sofisticación oculta)")
    target_amount: Optional[Decimal] = Field(
        default=None, gt=0,
        description="Monto objetivo a alcanzar (opcional)"
    )
    target_date: Optional[datetime] = Field(
        default=None,
        description="Fecha objetivo para alcanzar la meta (opcional)"
    )
    created_at: datetime = Field(default_factory=datetime.now)

    # Métricas simplificadas para UX (estilo Fintual)
    @computed_field
    @property
    def balance(self) -> Decimal:
        """Balance: Valor actual del goal (lo que el usuario ve primero)."""
        return self.portfolio.total_value

    @computed_field
    @property
    def depositado_neto(self) -> Decimal:
        """Depositado Neto: Total depositado por el usuario."""
        return self.portfolio.total_deposited

    @computed_field
    @property
    def ganado(self) -> Decimal:
        """Ganado: Ganancia o pérdida total (Balance - Depositado Neto)."""
        return self.portfolio.total_earned

    @computed_field
    @property
    def progress_percentage(self) -> Optional[Decimal]:
        """
        Porcentaje de progreso hacia la meta (si existe target_amount).

        Returns:
            Porcentaje entre 0 y 100, o None si no hay target_amount
        """
        if not self.target_amount or self.target_amount == 0:
            return None
        return (self.balance / self.target_amount) * Decimal(100)

    class Config:
        json_schema_extra = {
            "example": {
                "id": "goal_456",
                "name": "Jubilación 2050",
                "goal_type": "retirement",
                "risk_profile": "moderate",
                "target_amount": 100000.00,
                "portfolio": {
                    "id": "port_123",
                    "positions": {},
                    "cash": 5000.00
                }
            }
        }
