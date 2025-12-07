"""
Rebalance endpoints - Operaciones de rebalanceo de portfolios.

Permite ejecutar diferentes estrategias de rebalanceo:
- Simple: Baseline algorithm
- CVaR: CVaR-optimized (TODO - Gemini task)
- Tax-Efficient: Tax-loss harvesting (TODO - bonus)
"""

from fastapi import APIRouter, Depends, HTTPException, Path
import logging

from app.api.v1.schemas.rebalance import (
    RebalanceRequest,
    RebalanceResponse,
    RebalanceStrategyEnum,
    TradeResponse
)
from app.services.goal_service import GoalService, get_goal_service
from app.core.rebalancer import SimpleRebalanceStrategy
from app.core.constraints import (
    TradingConstraints,
    ConservativeConstraints,
    ModerateConstraints,
    RiskyConstraints
)
from app.core.models import RiskProfile

logger = logging.getLogger(__name__)

router = APIRouter()


def _get_constraints_for_risk_profile(risk_profile: RiskProfile) -> TradingConstraints:
    """
    Obtener constraints default basados en risk profile.

    Alineado con Fintual:
    - Conservative: 50% min liquidity, alto threshold
    - Moderate: 10% min liquidity, threshold medio
    - Risky: 2% min liquidity, threshold bajo
    """
    if risk_profile == RiskProfile.VERY_CONSERVATIVE or risk_profile == RiskProfile.CONSERVATIVE:
        return ConservativeConstraints()
    elif risk_profile == RiskProfile.MODERATE:
        return ModerateConstraints()
    else:  # RISKY, VERY_RISKY
        return RiskyConstraints()


def _create_constraints_from_request(
    base_constraints: TradingConstraints,
    request_constraints: dict
) -> TradingConstraints:
    """
    Crear constraints personalizados merge con defaults.

    Si el request especifica constraints, los usa.
    Si no, usa los defaults del risk profile.
    """
    if request_constraints is None:
        return base_constraints

    # Merge: request overrides defaults
    params = {}
    for field in TradingConstraints.model_fields:
        request_value = getattr(request_constraints, field, None)
        if request_value is not None:
            params[field] = request_value
        else:
            params[field] = getattr(base_constraints, field)

    return TradingConstraints(**params)


@router.post(
    "/{goal_id}",
    response_model=RebalanceResponse,
    summary="Rebalancear un Goal",
    description="""
    Ejecuta rebalanceo del portfolio de un Goal para alcanzar target allocations.

    **Estrategias disponibles:**
    - `simple`: Algoritmo baseline (compra/vende según drift)
    - `cvar`: CVaR-optimized con Monte Carlo (TODO - Gemini task)
    - `tax_efficient`: Tax-loss harvesting (TODO - bonus)

    **Constraints:**
    Si no se especifican, usa defaults del risk_profile:
    - Conservative: 50% min liquidez, 10% threshold
    - Moderate: 10% min liquidez, 5% threshold
    - Risky: 2% min liquidez, 2% threshold

    **Dry Run:**
    Por default `dry_run=True` (solo simula, no ejecuta).
    Para ejecutar trades reales, set `dry_run=False`.

    **Retorna:**
    - Lista de trades a ejecutar
    - Métricas: costos, turnover, drift
    - Allocations: current, target, final (estimadas)
    """
)
async def rebalance_goal(
    goal_id: str = Path(..., description="ID del goal a rebalancear"),
    request: RebalanceRequest = ...,
    service: GoalService = Depends(get_goal_service)
) -> RebalanceResponse:
    """Rebalancear un goal."""

    # 1. Obtener goal
    try:
        goal = service.get_goal(goal_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Goal {goal_id} not found")

    # 2. Validar que hay posiciones
    if len(goal.portfolio.positions) == 0:
        raise HTTPException(
            status_code=400,
            detail="Cannot rebalance: portfolio has no positions"
        )

    # 3. Determinar constraints
    base_constraints = _get_constraints_for_risk_profile(goal.risk_profile)
    constraints = _create_constraints_from_request(base_constraints, request.constraints)

    logger.info(
        f"Rebalancing goal {goal_id} with strategy={request.strategy}, "
        f"dry_run={request.dry_run}, constraints={constraints}"
    )

    # 4. Seleccionar estrategia
    if request.strategy == RebalanceStrategyEnum.SIMPLE:
        strategy = SimpleRebalanceStrategy(constraints=constraints)
    elif request.strategy == RebalanceStrategyEnum.CVAR:
        # TODO: Implementar con Gemini
        raise HTTPException(
            status_code=501,
            detail="CVaR strategy not yet implemented. Use 'simple' for now. "
                   "CVaR optimization coming soon with Gemini!"
        )
    elif request.strategy == RebalanceStrategyEnum.TAX_EFFICIENT:
        # TODO: Bonus feature
        raise HTTPException(
            status_code=501,
            detail="Tax-efficient strategy not yet implemented"
        )
    else:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown strategy: {request.strategy}"
        )

    # 5. Ejecutar rebalanceo
    try:
        result = strategy.rebalance(goal.portfolio)
    except Exception as e:
        logger.exception("Error during rebalance", exc_info=e)
        raise HTTPException(
            status_code=500,
            detail=f"Rebalance failed: {str(e)}"
        )

    # 6. Calcular allocations actuales y target
    current_allocations = {
        ticker: goal.portfolio.get_current_allocation(ticker)
        for ticker in goal.portfolio.positions.keys()
    }

    target_allocations = {
        ticker: pos.target_allocation
        for ticker, pos in goal.portfolio.positions.items()
    }

    # 7. Calcular drift después del rebalance (estimado)
    max_drift_after = None
    if result.final_allocations:
        drifts_after = {
            ticker: abs(result.final_allocations.get(ticker, 0) - target_allocations[ticker])
            for ticker in target_allocations
        }
        max_drift_after = float(max(drifts_after.values())) if drifts_after else 0.0

    # 8. Convertir trades a response
    trades_response = [
        TradeResponse(
            ticker=trade.ticker,
            action=trade.action,
            shares=trade.shares,
            current_price=trade.current_price,
            value=trade.value,
            reason=trade.reason
        )
        for trade in result.trades
    ]

    # 9. Generar mensaje para usuario
    if len(result.trades) == 0:
        message = "✅ Portfolio ya está balanceado. No se requieren trades."
    elif request.dry_run:
        message = (
            f"🔍 Simulación completa. Se generaron {len(result.trades)} trades. "
            f"Total a comprar: ${result.total_buy_value}, "
            f"Total a vender: ${result.total_sell_value}. "
            f"Set dry_run=False para ejecutar."
        )
    else:
        message = (
            f"✅ Rebalanceo ejecutado. {len(result.trades)} trades realizados. "
            f"Turnover: {result.metrics['turnover_pct']:.2f}%. "
            f"Costo estimado: ${result.estimated_cost}."
        )

    # 10. Crear response
    return RebalanceResponse(
        goal_id=goal_id,
        strategy_used=request.strategy.value,
        dry_run=request.dry_run,
        trades=trades_response,
        total_trades=len(trades_response),
        total_buy_value=result.total_buy_value,
        total_sell_value=result.total_sell_value,
        estimated_cost=result.estimated_cost,
        net_cash_change=result.net_cash_change,
        turnover=result.turnover,
        turnover_pct=result.metrics.get("turnover_pct", 0.0),
        current_allocations=current_allocations,
        target_allocations=target_allocations,
        final_allocations=result.final_allocations,
        max_drift_before=result.metrics.get("max_drift_before", 0.0),
        max_drift_after=max_drift_after,
        message=message
    )
