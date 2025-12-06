"""
Portfolio rebalancing strategies.

Implementa Strategy Pattern para diferentes enfoques de rebalanceo:
- SimpleRebalanceStrategy: Algoritmo baseline sin optimización
- CVaRRebalanceStrategy: Optimización basada en CVaR (TODO - Gemini task)
- TaxEfficientStrategy: Tax-loss harvesting (TODO - bonus)

Filosofía de Fintual:
- Rebalanceo discrecional (portfolio manager ajusta)
- CVaR como medida de riesgo
- Transparencia en decisiones
"""

from abc import ABC, abstractmethod
from decimal import Decimal
from typing import Dict, List, Tuple
from dataclasses import dataclass

from app.core.models import Portfolio, Asset
from app.core.constraints import TradingConstraints


@dataclass
class Trade:
    """
    Representa un trade de rebalanceo.

    Attributes:
        ticker: Símbolo del activo
        action: "BUY" o "SELL"
        shares: Cantidad de acciones (positivo)
        current_price: Precio actual del activo
        value: Valor total del trade (shares * price)
        reason: Razón del trade (para transparencia)
    """
    ticker: str
    action: str  # "BUY" or "SELL"
    shares: Decimal
    current_price: Decimal
    value: Decimal
    reason: str

    def __post_init__(self):
        """Validar que action sea válido."""
        if self.action not in ["BUY", "SELL"]:
            raise ValueError(f"Action debe ser 'BUY' o 'SELL', got {self.action}")
        if self.shares < 0:
            raise ValueError(f"Shares debe ser positivo, got {self.shares}")


@dataclass
class RebalanceResult:
    """
    Resultado de un rebalanceo.

    Attributes:
        trades: Lista de trades a ejecutar
        total_buy_value: Valor total de compras
        total_sell_value: Valor total de ventas
        estimated_cost: Costo estimado de transacciones
        final_allocations: Allocations finales esperadas después del rebalance
        metrics: Métricas adicionales (opcional)
    """
    trades: List[Trade]
    total_buy_value: Decimal
    total_sell_value: Decimal
    estimated_cost: Decimal
    final_allocations: Dict[str, Decimal]
    metrics: Dict[str, float] = None

    @property
    def net_cash_change(self) -> Decimal:
        """Cambio neto en cash (negativo = necesita cash, positivo = genera cash)."""
        return self.total_sell_value - self.total_buy_value - self.estimated_cost

    @property
    def turnover(self) -> Decimal:
        """Turnover del portfolio (% rotado)."""
        # Turnover = (total_buy + total_sell) / 2
        return (self.total_buy_value + self.total_sell_value) / 2


class RebalanceStrategy(ABC):
    """
    Abstract base class para estrategias de rebalanceo.

    Strategy Pattern: permite intercambiar algoritmos sin cambiar código cliente.
    """

    def __init__(self, constraints: TradingConstraints = None):
        """
        Args:
            constraints: Trading constraints a aplicar (usa defaults si None)
        """
        self.constraints = constraints or TradingConstraints()

    @abstractmethod
    def rebalance(self, portfolio: Portfolio) -> RebalanceResult:
        """
        Calcula trades necesarios para rebalancear portfolio a target allocations.

        Args:
            portfolio: Portfolio a rebalancear

        Returns:
            RebalanceResult con trades y métricas
        """
        pass

    def _calculate_drift(self, portfolio: Portfolio) -> Dict[str, Decimal]:
        """
        Calcula drift (desviación) de cada posición.

        Returns:
            Dict {ticker: drift} donde drift = target - current
            Positivo = necesita comprar, Negativo = necesita vender
        """
        return portfolio.get_allocation_drift()

    def _apply_constraints(
        self,
        trades: List[Trade],
        portfolio: Portfolio
    ) -> List[Trade]:
        """
        Aplica constraints a lista de trades.

        - Filtra trades por debajo de min_trade_value
        - Verifica que no exceda max_turnover
        - Asegura min_liquidity

        Args:
            trades: Lista original de trades
            portfolio: Portfolio actual

        Returns:
            Lista filtrada de trades
        """
        filtered_trades = []

        for trade in trades:
            # Filtrar trades muy pequeños
            if trade.value >= self.constraints.min_trade_value:
                filtered_trades.append(trade)

        # Verificar max_turnover si está definido
        if self.constraints.max_turnover is not None:
            total_turnover = sum(t.value for t in filtered_trades)
            max_allowed = self.constraints.max_turnover * portfolio.total_value

            if total_turnover > max_allowed:
                # Escalar trades proporcionalmente
                scale_factor = max_allowed / total_turnover
                filtered_trades = [
                    Trade(
                        ticker=t.ticker,
                        action=t.action,
                        shares=t.shares * scale_factor,
                        current_price=t.current_price,
                        value=t.value * scale_factor,
                        reason=f"{t.reason} (scaled by turnover constraint)"
                    )
                    for t in filtered_trades
                ]

        return filtered_trades

    def _calculate_transaction_cost(self, trades: List[Trade]) -> Decimal:
        """
        Calcula costo estimado de transacciones.

        Cost = sum(trade.value * transaction_cost_bps / 10000)

        Args:
            trades: Lista de trades

        Returns:
            Costo total estimado
        """
        total_value = sum(t.value for t in trades)
        # Basis points a decimal (10 bps = 0.10%)
        cost_rate = self.constraints.transaction_cost_bps / Decimal("10000")
        return total_value * cost_rate


class SimpleRebalanceStrategy(RebalanceStrategy):
    """
    Estrategia simple de rebalanceo (baseline).

    Algoritmo:
    1. Calcular drift (target - current) para cada posición
    2. Si drift > threshold, generar trade
    3. Comprar/vender para alcanzar target allocation
    4. Aplicar constraints (min trade size, max turnover, etc)

    Esta es la estrategia baseline contra la cual compararemos CVaR optimization.

    Ventajas:
    - Simple de entender
    - Rápido de ejecutar
    - Transparente

    Desventajas:
    - No considera costos de transacción en optimización
    - No optimiza para CVaR
    - Puede generar muchos trades pequeños
    """

    def rebalance(self, portfolio: Portfolio) -> RebalanceResult:
        """
        Rebalancea portfolio usando algoritmo simple.

        Steps:
        1. Calcular drift para cada posición
        2. Generar trades donde |drift| > threshold
        3. Ajustar para mantener min_liquidity
        4. Aplicar constraints
        5. Calcular allocations finales

        Args:
            portfolio: Portfolio a rebalancear

        Returns:
            RebalanceResult con trades necesarios
        """
        trades: List[Trade] = []
        drifts = self._calculate_drift(portfolio)

        # Calcular valor total del portfolio (para conversión drift → shares)
        total_value = portfolio.total_value

        # Step 1: Generar trades basados en drift
        for ticker, drift in drifts.items():
            # Solo rebalancear si drift excede threshold
            if abs(drift) >= self.constraints.rebalance_threshold:
                position = portfolio.positions[ticker]
                asset = position.asset

                # Calcular valor a comprar/vender
                # drift = (target - current) en porcentaje
                # value_to_trade = drift * total_value
                value_to_trade = drift * total_value

                # Convertir a shares
                shares_to_trade = abs(value_to_trade / asset.current_price)

                # No trades de 0 shares
                if shares_to_trade == 0:
                    continue

                # Determinar acción
                if drift > 0:
                    action = "BUY"
                    reason = f"Underweight by {float(drift)*100:.2f}%"
                else:
                    action = "SELL"
                    reason = f"Overweight by {float(abs(drift))*100:.2f}%"

                # Aplicar fractional shares constraint
                if not self.constraints.allow_fractional_shares:
                    shares_to_trade = Decimal(int(shares_to_trade))

                trade = Trade(
                    ticker=ticker,
                    action=action,
                    shares=shares_to_trade,
                    current_price=asset.current_price,
                    value=abs(value_to_trade),
                    reason=reason
                )

                trades.append(trade)

        # Step 2: Aplicar constraints
        trades = self._apply_constraints(trades, portfolio)

        # Step 3: Calcular totales
        total_buy = sum(t.value for t in trades if t.action == "BUY")
        total_sell = sum(t.value for t in trades if t.action == "SELL")
        estimated_cost = self._calculate_transaction_cost(trades)

        # Step 4: Verificar min_liquidity constraint
        # Cash después de trades = cash_actual + sell - buy - costs
        final_cash = portfolio.cash + total_sell - total_buy - estimated_cost
        min_cash_required = self.constraints.min_liquidity * total_value

        if final_cash < min_cash_required:
            # Necesitamos mantener más cash - reducir compras o aumentar ventas
            cash_deficit = min_cash_required - final_cash

            # Estrategia simple: reducir compras proporcionalmente
            if total_buy > 0:
                reduction_factor = max(Decimal("0"), (total_buy - cash_deficit) / total_buy)
                adjusted_trades = []
                for t in trades:
                    if t.action == "BUY":
                        adjusted_shares = t.shares * reduction_factor
                        # Aplicar fractional shares constraint después de ajuste
                        if not self.constraints.allow_fractional_shares:
                            adjusted_shares = Decimal(int(adjusted_shares))
                        adjusted_trades.append(Trade(
                            ticker=t.ticker,
                            action=t.action,
                            shares=adjusted_shares,
                            current_price=t.current_price,
                            value=adjusted_shares * t.current_price,
                            reason=f"{t.reason} (adjusted for liquidity)"
                        ))
                    else:
                        adjusted_trades.append(t)
                trades = adjusted_trades

                # Recalcular totales
                total_buy = sum(t.value for t in trades if t.action == "BUY")
                total_sell = sum(t.value for t in trades if t.action == "SELL")
                estimated_cost = self._calculate_transaction_cost(trades)

        # Step 5: Calcular allocations finales (estimadas)
        final_allocations = self._estimate_final_allocations(portfolio, trades)

        return RebalanceResult(
            trades=trades,
            total_buy_value=total_buy,
            total_sell_value=total_sell,
            estimated_cost=estimated_cost,
            final_allocations=final_allocations,
            metrics={
                "n_trades": len(trades),
                "turnover_pct": float(sum(t.value for t in trades) / total_value * 100),
                "max_drift_before": float(max(abs(d) for d in drifts.values())) if drifts else 0.0,
            }
        )

    def _estimate_final_allocations(
        self,
        portfolio: Portfolio,
        trades: List[Trade]
    ) -> Dict[str, Decimal]:
        """
        Estima allocations finales después de ejecutar trades.

        Args:
            portfolio: Portfolio actual
            trades: Lista de trades a ejecutar

        Returns:
            Dict {ticker: final_allocation}
        """
        # Crear copia de las posiciones actuales
        final_positions = {
            ticker: pos.shares
            for ticker, pos in portfolio.positions.items()
        }

        # Aplicar trades
        for trade in trades:
            if trade.action == "BUY":
                if trade.ticker in final_positions:
                    final_positions[trade.ticker] += trade.shares
                else:
                    final_positions[trade.ticker] = trade.shares
            else:  # SELL
                if trade.ticker in final_positions:
                    final_positions[trade.ticker] -= trade.shares
                    if final_positions[trade.ticker] <= 0:
                        del final_positions[trade.ticker]

        # Calcular cash final después de trades
        total_buy = sum(t.value for t in trades if t.action == "BUY")
        total_sell = sum(t.value for t in trades if t.action == "SELL")
        transaction_cost = self._calculate_transaction_cost(trades)
        final_cash = portfolio.cash + total_sell - total_buy - transaction_cost

        # Calcular total value final
        total_value_final = final_cash
        for ticker, shares in final_positions.items():
            price = portfolio.positions[ticker].asset.current_price
            total_value_final += shares * price

        # Calcular allocations (solo para posiciones, no incluir cash en allocations)
        final_allocations = {}
        for ticker, shares in final_positions.items():
            price = portfolio.positions[ticker].asset.current_price
            value = shares * price
            final_allocations[ticker] = value / total_value_final if total_value_final > 0 else Decimal("0")

        return final_allocations
