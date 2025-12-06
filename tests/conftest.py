"""
Pytest configuration and shared fixtures.
"""

import pytest
from decimal import Decimal
from datetime import datetime, timedelta
from app.core.models import Asset, AssetType, Position, Portfolio, Goal, RiskProfile, GoalType


@pytest.fixture
def sample_asset_aapl():
    """Sample Apple stock asset."""
    return Asset(
        ticker="AAPL",
        name="Apple Inc.",
        asset_type=AssetType.STOCK,
        current_price=Decimal("180.50"),
        currency="USD"
    )


@pytest.fixture
def sample_asset_meta():
    """Sample Meta stock asset."""
    return Asset(
        ticker="META",
        name="Meta Platforms Inc.",
        asset_type=AssetType.STOCK,
        current_price=Decimal("400.00"),
        currency="USD"
    )


@pytest.fixture
def sample_position_aapl(sample_asset_aapl):
    """Sample position in AAPL."""
    return Position(
        asset=sample_asset_aapl,
        shares=Decimal("10"),
        target_allocation=Decimal("0.6"),
        deposited=Decimal("1750.00")
    )


@pytest.fixture
def sample_position_meta(sample_asset_meta):
    """Sample position in META."""
    return Position(
        asset=sample_asset_meta,
        shares=Decimal("5"),
        target_allocation=Decimal("0.4"),
        deposited=Decimal("1950.00")
    )


@pytest.fixture
def sample_portfolio_balanced(sample_asset_aapl, sample_asset_meta):
    """
    Sample balanced portfolio with 60/40 allocation.

    AAPL: 10 shares @ $180.50 = $1,805 (target 60%)
    META: 5 shares @ $400.00 = $2,000 (target 40%)
    Cash: $500
    Total: $4,305
    """
    portfolio = Portfolio(id="port_test_001", cash=Decimal("500.00"))

    portfolio.add_position(
        asset=sample_asset_aapl,
        shares=Decimal("10"),
        target_allocation=Decimal("0.6"),
        deposited=Decimal("1750.00")
    )

    portfolio.add_position(
        asset=sample_asset_meta,
        shares=Decimal("5"),
        target_allocation=Decimal("0.4"),
        deposited=Decimal("1950.00")
    )

    return portfolio


@pytest.fixture
def sample_goal_retirement(sample_portfolio_balanced):
    """Sample retirement goal."""
    return Goal(
        id="goal_test_001",
        name="Jubilación 2050",
        goal_type=GoalType.RETIREMENT,
        risk_profile=RiskProfile.MODERATE,
        portfolio=sample_portfolio_balanced,
        target_amount=Decimal("100000.00"),
        target_date=datetime.now() + timedelta(days=365 * 25)  # 25 years
    )


@pytest.fixture
def empty_portfolio():
    """Empty portfolio with only cash."""
    return Portfolio(id="port_empty", cash=Decimal("1000.00"))
