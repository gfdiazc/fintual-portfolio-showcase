"""
Unit tests para core models.

Testing strategy (alineado con rigor de Fintual):
- High coverage (90%+)
- Edge cases incluidos
- Tests de validación Pydantic
- Tests de computed fields
"""

import pytest
from decimal import Decimal
from datetime import datetime
from pydantic import ValidationError

from app.core.models import (
    Asset, AssetType, Position, Portfolio, Goal,
    RiskProfile, GoalType
)


class TestAsset:
    """Tests para Asset model."""

    def test_asset_creation_valid(self):
        """Test creación de asset válido."""
        asset = Asset(
            ticker="AAPL",
            name="Apple Inc.",
            asset_type=AssetType.STOCK,
            current_price=Decimal("180.50")
        )

        assert asset.ticker == "AAPL"
        assert asset.name == "Apple Inc."
        assert asset.current_price == Decimal("180.50")
        assert asset.currency == "USD"  # Default

    def test_ticker_normalization(self):
        """Test que ticker se normaliza a mayúsculas."""
        asset = Asset(ticker="aapl", current_price=Decimal("180.50"))
        assert asset.ticker == "AAPL"

        asset2 = Asset(ticker="  meta  ", current_price=Decimal("400.00"))
        assert asset2.ticker == "META"

    def test_asset_invalid_price(self):
        """Test que precio debe ser > 0."""
        with pytest.raises(ValidationError):
            Asset(ticker="AAPL", current_price=Decimal("0"))

        with pytest.raises(ValidationError):
            Asset(ticker="AAPL", current_price=Decimal("-10"))

    def test_asset_can_update_price(self):
        """Test que precio puede actualizarse (not frozen)."""
        asset = Asset(ticker="AAPL", current_price=Decimal("180.00"))
        asset.current_price = Decimal("185.00")
        assert asset.current_price == Decimal("185.00")


class TestPosition:
    """Tests para Position model."""

    def test_position_creation(self, sample_asset_aapl):
        """Test creación de posición válida."""
        position = Position(
            asset=sample_asset_aapl,
            shares=Decimal("10"),
            target_allocation=Decimal("0.6"),
            deposited=Decimal("1750.00")
        )

        assert position.shares == Decimal("10")
        assert position.target_allocation == Decimal("0.6")

    def test_market_value_calculation(self, sample_asset_aapl):
        """Test cálculo de market value."""
        position = Position(
            asset=sample_asset_aapl,
            shares=Decimal("10"),
            target_allocation=Decimal("0.6")
        )

        # 10 shares * $180.50 = $1,805
        expected_value = Decimal("1805.00")
        assert position.market_value == expected_value

    def test_position_invalid_allocation(self, sample_asset_aapl):
        """Test que allocation debe estar entre 0 y 1."""
        # Allocation > 1
        with pytest.raises(ValidationError):
            Position(
                asset=sample_asset_aapl,
                shares=Decimal("10"),
                target_allocation=Decimal("1.5")
            )

        # Allocation < 0
        with pytest.raises(ValidationError):
            Position(
                asset=sample_asset_aapl,
                shares=Decimal("10"),
                target_allocation=Decimal("-0.1")
            )

    def test_position_negative_shares(self, sample_asset_aapl):
        """Test que shares no puede ser negativo."""
        with pytest.raises(ValidationError):
            Position(
                asset=sample_asset_aapl,
                shares=Decimal("-5"),
                target_allocation=Decimal("0.6")
            )


class TestPortfolio:
    """Tests para Portfolio model."""

    def test_portfolio_creation_empty(self):
        """Test creación de portfolio vacío."""
        portfolio = Portfolio(id="test_001", cash=Decimal("1000.00"))

        assert portfolio.id == "test_001"
        assert portfolio.cash == Decimal("1000.00")
        assert len(portfolio.positions) == 0
        assert portfolio.total_value == Decimal("1000.00")

    def test_portfolio_total_value(self, sample_portfolio_balanced):
        """
        Test cálculo de total_value (Balance).

        AAPL: 10 * $180.50 = $1,805
        META: 5 * $400.00 = $2,000
        Cash: $500
        Total: $4,305
        """
        assert sample_portfolio_balanced.total_value == Decimal("4305.00")

    def test_portfolio_total_deposited(self, sample_portfolio_balanced):
        """
        Test cálculo de total_deposited (Depositado Neto).

        AAPL deposited: $1,750
        META deposited: $1,950
        Cash: $500
        Total: $4,200
        """
        assert sample_portfolio_balanced.total_deposited == Decimal("4200.00")

    def test_portfolio_total_earned(self, sample_portfolio_balanced):
        """
        Test cálculo de total_earned (Ganado).

        Ganado = Balance - Depositado Neto
        = $4,305 - $4,200 = $105
        """
        assert sample_portfolio_balanced.total_earned == Decimal("105.00")

    def test_add_position(self, sample_asset_aapl):
        """Test agregar posición al portfolio."""
        portfolio = Portfolio(id="test_002")

        portfolio.add_position(
            asset=sample_asset_aapl,
            shares=Decimal("5"),
            target_allocation=Decimal("0.5")
        )

        assert "AAPL" in portfolio.positions
        assert portfolio.positions["AAPL"].shares == Decimal("5")

    def test_get_current_allocation(self, sample_portfolio_balanced):
        """
        Test cálculo de allocation actual.

        AAPL value: $1,805 / $4,305 = ~41.9%
        META value: $2,000 / $4,305 = ~46.5%
        """
        aapl_allocation = sample_portfolio_balanced.get_current_allocation("AAPL")
        meta_allocation = sample_portfolio_balanced.get_current_allocation("META")

        # Check aproximadamente (0.419)
        assert abs(aapl_allocation - Decimal("0.419")) < Decimal("0.001")
        # Check aproximadamente (0.465)
        assert abs(meta_allocation - Decimal("0.465")) < Decimal("0.001")

    def test_get_current_allocation_empty_portfolio(self, empty_portfolio):
        """Test allocation en portfolio vacío retorna 0."""
        allocation = empty_portfolio.get_current_allocation("AAPL")
        assert allocation == Decimal("0")

    def test_get_current_allocation_nonexistent_ticker(self, sample_portfolio_balanced):
        """Test allocation de ticker inexistente retorna 0."""
        allocation = sample_portfolio_balanced.get_current_allocation("TSLA")
        assert allocation == Decimal("0")

    def test_validate_allocations_valid(self, sample_portfolio_balanced):
        """Test validación de allocations válidas (sum = 1.0)."""
        assert sample_portfolio_balanced.validate_allocations() is True

    def test_validate_allocations_invalid(self, sample_asset_aapl, sample_asset_meta):
        """Test validación falla si allocations suman > 1."""
        portfolio = Portfolio(id="test_003")

        portfolio.add_position(
            asset=sample_asset_aapl,
            shares=Decimal("10"),
            target_allocation=Decimal("0.7")  # 70%
        )

        portfolio.add_position(
            asset=sample_asset_meta,
            shares=Decimal("5"),
            target_allocation=Decimal("0.5")  # 50%
        )

        # Sum = 1.2 > 1.0
        assert portfolio.validate_allocations() is False

    def test_get_allocation_drift(self, sample_portfolio_balanced):
        """
        Test cálculo de drift (desviación).

        AAPL:
        - Current: ~41.9%
        - Target: 60%
        - Drift: +18.1% (necesita comprar)

        META:
        - Current: ~46.5%
        - Target: 40%
        - Drift: -6.5% (necesita vender)
        """
        drifts = sample_portfolio_balanced.get_allocation_drift()

        # AAPL drift positivo (comprar)
        assert drifts["AAPL"] > 0
        assert abs(drifts["AAPL"] - Decimal("0.181")) < Decimal("0.001")

        # META drift negativo (vender)
        assert drifts["META"] < 0
        assert abs(drifts["META"] - Decimal("-0.065")) < Decimal("0.001")


class TestGoal:
    """Tests para Goal model."""

    def test_goal_creation(self, sample_portfolio_balanced):
        """Test creación de goal válido."""
        goal = Goal(
            id="goal_001",
            name="Vacaciones 2025",
            goal_type=GoalType.VACATION,
            risk_profile=RiskProfile.CONSERVATIVE,
            portfolio=sample_portfolio_balanced,
            target_amount=Decimal("10000.00")
        )

        assert goal.name == "Vacaciones 2025"
        assert goal.goal_type == GoalType.VACATION
        assert goal.risk_profile == RiskProfile.CONSERVATIVE

    def test_goal_balance_metric(self, sample_goal_retirement):
        """Test métrica Balance (value actual)."""
        # Balance = total_value del portfolio
        assert sample_goal_retirement.balance == Decimal("4305.00")

    def test_goal_depositado_neto_metric(self, sample_goal_retirement):
        """Test métrica Depositado Neto."""
        # Depositado Neto = total_deposited del portfolio
        assert sample_goal_retirement.depositado_neto == Decimal("4200.00")

    def test_goal_ganado_metric(self, sample_goal_retirement):
        """Test métrica Ganado (Balance - Depositado Neto)."""
        # Ganado = $4,305 - $4,200 = $105
        assert sample_goal_retirement.ganado == Decimal("105.00")

    def test_goal_progress_percentage(self, sample_goal_retirement):
        """
        Test cálculo de progreso hacia meta.

        Balance: $4,305
        Target: $100,000
        Progress: 4.305%
        """
        progress = sample_goal_retirement.progress_percentage

        assert progress is not None
        expected = Decimal("4.305")
        assert abs(progress - expected) < Decimal("0.001")

    def test_goal_progress_percentage_no_target(self, sample_portfolio_balanced):
        """Test progress_percentage es None si no hay target_amount."""
        goal = Goal(
            id="goal_002",
            name="Ahorro General",
            goal_type=GoalType.SAVINGS,
            risk_profile=RiskProfile.MODERATE,
            portfolio=sample_portfolio_balanced
            # No target_amount
        )

        assert goal.progress_percentage is None

    def test_goal_progress_percentage_over_100(self, empty_portfolio):
        """Test progress_percentage cuando se supera la meta."""
        goal = Goal(
            id="goal_003",
            name="Meta Pequeña",
            goal_type=GoalType.SAVINGS,
            risk_profile=RiskProfile.CONSERVATIVE,
            portfolio=empty_portfolio,  # $1,000 cash
            target_amount=Decimal("500.00")
        )

        # Progress = $1,000 / $500 * 100 = 200%
        assert goal.progress_percentage == Decimal("200.00")


class TestEdgeCases:
    """Tests de edge cases importantes."""

    def test_portfolio_with_single_stock(self, sample_asset_aapl):
        """Test portfolio con un solo stock."""
        portfolio = Portfolio(id="single_stock")
        portfolio.add_position(
            asset=sample_asset_aapl,
            shares=Decimal("1"),
            target_allocation=Decimal("1.0")  # 100%
        )

        assert len(portfolio.positions) == 1
        assert portfolio.total_value == Decimal("180.50")
        assert portfolio.validate_allocations() is True

    def test_portfolio_zero_cash(self, sample_asset_aapl):
        """Test portfolio sin cash."""
        portfolio = Portfolio(id="no_cash", cash=Decimal("0"))
        portfolio.add_position(
            asset=sample_asset_aapl,
            shares=Decimal("5"),
            target_allocation=Decimal("1.0")
        )

        assert portfolio.cash == Decimal("0")
        assert portfolio.total_value == Decimal("902.50")  # 5 * 180.50

    def test_goal_with_negative_earned(self, sample_asset_aapl):
        """Test goal con pérdida (ganado negativo)."""
        portfolio = Portfolio(id="loss_portfolio")
        portfolio.add_position(
            asset=sample_asset_aapl,
            shares=Decimal("10"),
            target_allocation=Decimal("1.0"),
            deposited=Decimal("2000.00")  # Depositó más de lo que vale ahora
        )

        goal = Goal(
            id="loss_goal",
            name="Goal con Pérdida",
            goal_type=GoalType.SAVINGS,
            risk_profile=RiskProfile.RISKY,
            portfolio=portfolio
        )

        # Balance: $1,805, Depositado: $2,000
        # Ganado: -$195
        assert goal.ganado == Decimal("-195.00")
        assert goal.ganado < 0  # Pérdida

    def test_update_existing_position(self, sample_portfolio_balanced, sample_asset_aapl):
        """Test actualizar posición existente."""
        # Actualizar AAPL con nuevos valores
        sample_portfolio_balanced.add_position(
            asset=sample_asset_aapl,
            shares=Decimal("20"),  # Duplicar shares
            target_allocation=Decimal("0.7"),  # Nuevo target
            deposited=Decimal("3500.00")  # Nuevo deposited
        )

        aapl_position = sample_portfolio_balanced.positions["AAPL"]
        assert aapl_position.shares == Decimal("20")
        assert aapl_position.target_allocation == Decimal("0.7")
