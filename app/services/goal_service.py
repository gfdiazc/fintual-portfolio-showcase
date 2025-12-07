"""
Goal service - Business logic para gestión de Goals.

En producción esto conectaría con una DB real (PostgreSQL, etc).
Para este showcase usamos almacenamiento in-memory.
"""

from typing import Dict, List, Optional
from decimal import Decimal
import uuid

from app.core.models import Goal, Portfolio, Asset, Position, GoalType, RiskProfile
from app.api.v1.schemas.goal import GoalCreate, GoalUpdate, PositionCreate


class GoalService:
    """
    Servicio para gestión de Goals.

    Responsabilidades:
    - CRUD de goals
    - Validación de reglas de negocio
    - Coordinación entre Goal y Portfolio
    """

    def __init__(self):
        """Inicializar servicio con storage in-memory."""
        self._goals: Dict[str, Goal] = {}
        self._assets: Dict[str, Asset] = {}  # Cache de assets

    def create_goal(self, goal_create: GoalCreate) -> Goal:
        """
        Crear un nuevo Goal.

        Args:
            goal_create: Datos para crear el goal

        Returns:
            Goal creado

        Raises:
            ValueError: Si ya existe un goal con ese nombre
        """
        # Generar ID único
        goal_id = f"goal_{uuid.uuid4().hex[:8]}"

        # Crear portfolio vacío
        portfolio = Portfolio(
            id=f"port_{uuid.uuid4().hex[:8]}",
            cash=goal_create.initial_cash
        )

        # Crear goal
        goal = Goal(
            id=goal_id,
            name=goal_create.name,
            goal_type=goal_create.goal_type,
            risk_profile=goal_create.risk_profile,
            portfolio=portfolio,
            target_amount=goal_create.target_amount,
            target_date=goal_create.target_date
        )

        # Guardar
        self._goals[goal_id] = goal

        return goal

    def get_goal(self, goal_id: str) -> Goal:
        """
        Obtener un Goal por ID.

        Args:
            goal_id: ID del goal

        Returns:
            Goal encontrado

        Raises:
            KeyError: Si el goal no existe
        """
        if goal_id not in self._goals:
            raise KeyError(f"Goal {goal_id} not found")

        return self._goals[goal_id]

    def list_goals(self) -> List[Goal]:
        """
        Listar todos los goals.

        Returns:
            Lista de todos los goals
        """
        return list(self._goals.values())

    def update_goal(self, goal_id: str, goal_update: GoalUpdate) -> Goal:
        """
        Actualizar un Goal.

        Args:
            goal_id: ID del goal a actualizar
            goal_update: Datos a actualizar

        Returns:
            Goal actualizado

        Raises:
            KeyError: Si el goal no existe
        """
        goal = self.get_goal(goal_id)

        # Actualizar campos si están presentes
        if goal_update.name is not None:
            goal.name = goal_update.name
        if goal_update.target_amount is not None:
            goal.target_amount = goal_update.target_amount
        if goal_update.target_date is not None:
            goal.target_date = goal_update.target_date

        return goal

    def delete_goal(self, goal_id: str) -> None:
        """
        Eliminar un Goal.

        Args:
            goal_id: ID del goal a eliminar

        Raises:
            KeyError: Si el goal no existe
        """
        if goal_id not in self._goals:
            raise KeyError(f"Goal {goal_id} not found")

        del self._goals[goal_id]

    def add_position_to_goal(
        self,
        goal_id: str,
        position_create: PositionCreate
    ) -> Goal:
        """
        Agregar una posición al portfolio de un goal.

        Args:
            goal_id: ID del goal
            position_create: Datos de la posición a crear

        Returns:
            Goal actualizado

        Raises:
            KeyError: Si el goal no existe
            ValueError: Si las validaciones fallan
        """
        goal = self.get_goal(goal_id)

        # Crear o obtener asset
        ticker = position_create.ticker.upper()
        if ticker in self._assets:
            asset = self._assets[ticker]
            # Actualizar precio si cambió
            asset.current_price = position_create.asset.current_price
        else:
            # Crear nuevo asset
            asset = Asset(
                ticker=ticker,
                name=position_create.asset.name or ticker,
                asset_type=position_create.asset.asset_type,
                current_price=position_create.asset.current_price,
                currency=position_create.asset.currency
            )
            self._assets[ticker] = asset

        # Agregar posición al portfolio
        goal.portfolio.add_position(
            asset=asset,
            shares=position_create.shares,
            target_allocation=position_create.target_allocation,
            deposited=position_create.deposited
        )

        return goal

    def add_cash_to_goal(self, goal_id: str, amount: Decimal) -> Goal:
        """
        Agregar cash a un goal (depósito).

        Args:
            goal_id: ID del goal
            amount: Monto a agregar

        Returns:
            Goal actualizado

        Raises:
            KeyError: Si el goal no existe
            ValueError: Si amount <= 0
        """
        if amount <= 0:
            raise ValueError("Amount must be positive")

        goal = self.get_goal(goal_id)
        goal.portfolio.cash += amount

        return goal

    def withdraw_cash_from_goal(self, goal_id: str, amount: Decimal) -> Goal:
        """
        Retirar cash de un goal.

        Args:
            goal_id: ID del goal
            amount: Monto a retirar

        Returns:
            Goal actualizado

        Raises:
            KeyError: Si el goal no existe
            ValueError: Si amount <= 0 o excede cash disponible
        """
        if amount <= 0:
            raise ValueError("Amount must be positive")

        goal = self.get_goal(goal_id)

        if goal.portfolio.cash < amount:
            raise ValueError(
                f"Insufficient cash. Available: {goal.portfolio.cash}, "
                f"requested: {amount}"
            )

        goal.portfolio.cash -= amount

        return goal

    def validate_allocations(self, goal_id: str) -> bool:
        """
        Validar que las allocations del goal suman <= 1.0.

        Args:
            goal_id: ID del goal

        Returns:
            True si válido, False si no

        Raises:
            KeyError: Si el goal no existe
        """
        goal = self.get_goal(goal_id)
        return goal.portfolio.validate_allocations()


# Singleton instance
_goal_service = GoalService()


def get_goal_service() -> GoalService:
    """
    Dependency injection para GoalService.

    En FastAPI se usa como:
    def endpoint(service: GoalService = Depends(get_goal_service)):
        ...
    """
    return _goal_service
