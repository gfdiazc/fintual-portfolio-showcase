"""
Goals endpoints - CRUD operations para Goals.

Alineado con Fintual:
- Goals como abstracción principal (no portfolios directamente)
- Métricas: Balance, Depositado Neto, Ganado
- Risk profile determina constraints de rebalanceo
"""

from typing import List
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, status, Query
import logging

from app.api.v1.schemas.goal import (
    GoalCreate,
    GoalUpdate,
    GoalResponse,
    GoalListResponse,
    PositionCreate,
    PortfolioResponse,
    PositionResponse,
    AssetResponse
)
from app.services.goal_service import GoalService, get_goal_service
from app.core.models import Goal

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================================================
# Helper functions para conversión Goal -> GoalResponse
# ============================================================================

def _goal_to_response(goal: Goal) -> GoalResponse:
    """Convertir Goal de dominio a GoalResponse."""

    # Convertir positions
    positions_response = {}
    for ticker, position in goal.portfolio.positions.items():
        current_allocation = goal.portfolio.get_current_allocation(ticker)
        positions_response[ticker] = PositionResponse(
            ticker=position.asset.ticker,
            shares=position.shares,
            target_allocation=position.target_allocation,
            deposited=position.deposited,
            market_value=position.market_value,
            current_allocation=current_allocation
        )

    # Crear portfolio response
    portfolio_response = PortfolioResponse(
        id=goal.portfolio.id,
        cash=goal.portfolio.cash,
        total_value=goal.portfolio.total_value,
        total_deposited=goal.portfolio.total_deposited,
        total_earned=goal.portfolio.total_earned,
        positions=positions_response
    )

    # Crear goal response
    return GoalResponse(
        id=goal.id,
        name=goal.name,
        goal_type=goal.goal_type,
        risk_profile=goal.risk_profile,
        target_amount=goal.target_amount,
        target_date=goal.target_date,
        balance=goal.balance,
        depositado_neto=goal.depositado_neto,
        ganado=goal.ganado,
        progress_percentage=goal.progress_percentage,
        portfolio=portfolio_response
    )


# ============================================================================
# CRUD Endpoints
# ============================================================================

@router.post(
    "/",
    response_model=GoalResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear un nuevo Goal",
    description="""
    Crea un nuevo Goal (meta de inversión).

    El Goal incluye:
    - Nombre y tipo (retirement, savings, vacation, etc)
    - Perfil de riesgo (determina constraints de rebalanceo)
    - Monto y fecha objetivo (opcionales)
    - Cash inicial

    Retorna el Goal creado con su portfolio vacío.
    """
)
async def create_goal(
    goal_create: GoalCreate,
    service: GoalService = Depends(get_goal_service)
) -> GoalResponse:
    """Crear un nuevo Goal."""
    try:
        goal = service.create_goal(goal_create)
        logger.info(f"Goal created: {goal.id} - {goal.name}")
        return _goal_to_response(goal)
    except ValueError as e:
        logger.error(f"Error creating goal: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/",
    response_model=GoalListResponse,
    summary="Listar todos los Goals",
    description="Retorna lista de todos los goals del usuario."
)
async def list_goals(
    service: GoalService = Depends(get_goal_service)
) -> GoalListResponse:
    """Listar todos los goals."""
    goals = service.list_goals()
    goals_response = [_goal_to_response(g) for g in goals]

    return GoalListResponse(
        goals=goals_response,
        total=len(goals_response)
    )


@router.get(
    "/{goal_id}",
    response_model=GoalResponse,
    summary="Obtener un Goal por ID",
    description="""
    Retorna un Goal específico con todas sus métricas:
    - Balance (valor actual)
    - Depositado Neto (total depositado)
    - Ganado (balance - depositado)
    - Progreso hacia meta (si hay target_amount)
    - Portfolio con todas las posiciones
    """
)
async def get_goal(
    goal_id: str,
    service: GoalService = Depends(get_goal_service)
) -> GoalResponse:
    """Obtener un goal por ID."""
    try:
        goal = service.get_goal(goal_id)
        return _goal_to_response(goal)
    except KeyError:
        raise HTTPException(
            status_code=404,
            detail=f"Goal {goal_id} not found"
        )


@router.put(
    "/{goal_id}",
    response_model=GoalResponse,
    summary="Actualizar un Goal",
    description="Actualiza nombre, target_amount o target_date de un Goal."
)
async def update_goal(
    goal_id: str,
    goal_update: GoalUpdate,
    service: GoalService = Depends(get_goal_service)
) -> GoalResponse:
    """Actualizar un goal."""
    try:
        goal = service.update_goal(goal_id, goal_update)
        logger.info(f"Goal updated: {goal_id}")
        return _goal_to_response(goal)
    except KeyError:
        raise HTTPException(
            status_code=404,
            detail=f"Goal {goal_id} not found"
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete(
    "/{goal_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar un Goal",
    description="Elimina un Goal y su portfolio asociado."
)
async def delete_goal(
    goal_id: str,
    service: GoalService = Depends(get_goal_service)
):
    """Eliminar un goal."""
    try:
        service.delete_goal(goal_id)
        logger.info(f"Goal deleted: {goal_id}")
        return None
    except KeyError:
        raise HTTPException(
            status_code=404,
            detail=f"Goal {goal_id} not found"
        )


# ============================================================================
# Portfolio Management Endpoints
# ============================================================================

@router.post(
    "/{goal_id}/positions",
    response_model=GoalResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Agregar posición al Goal",
    description="""
    Agrega una posición (asset + shares) al portfolio del Goal.

    Si el asset ya existe en el portfolio, actualiza la posición.
    El target_allocation debe estar entre 0 y 1 (porcentaje).
    """
)
async def add_position_to_goal(
    goal_id: str,
    position_create: PositionCreate,
    service: GoalService = Depends(get_goal_service)
) -> GoalResponse:
    """Agregar posición a un goal."""
    try:
        goal = service.add_position_to_goal(goal_id, position_create)
        logger.info(f"Position added to goal {goal_id}: {position_create.ticker}")
        return _goal_to_response(goal)
    except KeyError:
        raise HTTPException(
            status_code=404,
            detail=f"Goal {goal_id} not found"
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/{goal_id}/deposit",
    response_model=GoalResponse,
    summary="Depositar cash al Goal",
    description="Agrega cash al portfolio del Goal (simula un depósito)."
)
async def deposit_to_goal(
    goal_id: str,
    amount: Decimal = Query(..., gt=0, description="Monto a depositar"),
    service: GoalService = Depends(get_goal_service)
) -> GoalResponse:
    """Depositar cash a un goal."""
    try:
        goal = service.add_cash_to_goal(goal_id, amount)
        logger.info(f"Deposited {amount} to goal {goal_id}")
        return _goal_to_response(goal)
    except KeyError:
        raise HTTPException(
            status_code=404,
            detail=f"Goal {goal_id} not found"
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/{goal_id}/withdraw",
    response_model=GoalResponse,
    summary="Retirar cash del Goal",
    description="Retira cash del portfolio del Goal."
)
async def withdraw_from_goal(
    goal_id: str,
    amount: Decimal = Query(..., gt=0, description="Monto a retirar"),
    service: GoalService = Depends(get_goal_service)
) -> GoalResponse:
    """Retirar cash de un goal."""
    try:
        goal = service.withdraw_cash_from_goal(goal_id, amount)
        logger.info(f"Withdrawn {amount} from goal {goal_id}")
        return _goal_to_response(goal)
    except KeyError:
        raise HTTPException(
            status_code=404,
            detail=f"Goal {goal_id} not found"
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/{goal_id}/validate",
    response_model=dict,
    summary="Validar allocations del Goal",
    description="""
    Valida que las target allocations del portfolio sumen <= 1.0.

    Retorna:
    - valid: True/False
    - total_allocation: Suma de allocations
    - message: Mensaje explicativo
    """
)
async def validate_goal_allocations(
    goal_id: str,
    service: GoalService = Depends(get_goal_service)
):
    """Validar allocations de un goal."""
    try:
        goal = service.get_goal(goal_id)
        is_valid = service.validate_allocations(goal_id)

        total_allocation = sum(
            pos.target_allocation
            for pos in goal.portfolio.positions.values()
        )

        return {
            "goal_id": goal_id,
            "valid": is_valid,
            "total_allocation": float(total_allocation),
            "message": (
                "Allocations are valid" if is_valid
                else f"Allocations sum to {total_allocation}, must be <= 1.0"
            )
        }
    except KeyError:
        raise HTTPException(
            status_code=404,
            detail=f"Goal {goal_id} not found"
        )
