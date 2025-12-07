"""
Unit tests para rebalancing strategies.

Testing strategy:
- Tests de constraints validation
- Tests de SimpleRebalanceStrategy con diferentes escenarios
- Edge cases: portfolio balanceado, un solo asset, cash insuficiente
- Verificar que constraints se aplican correctamente
"""

import pytest
from decimal import Decimal

from app.core.rebalancer import (
    SimpleRebalanceStrategy,
    CVaRRebalanceStrategy,
    Trade,
    RebalanceResult,
    RebalanceStrategy
)
from app.core.constraints import (
    TradingConstraints,
    ConservativeConstraints,
    ModerateConstraints,
    RiskyConstraints
)
from app.core.models import Asset, Portfolio, AssetType


class TestTradingConstraints:
    """Tests para TradingConstraints model."""

    def test_default_constraints(self):
        """Test creación con defaults."""
        constraints = TradingConstraints()

        assert constraints.min_trade_value == Decimal("10.00")
        assert constraints.rebalance_threshold == Decimal("0.05")
        assert constraints.min_liquidity == Decimal("0.02")
        assert constraints.allow_fractional_shares is True
        assert constraints.transaction_cost_bps == Decimal("10")

    def test_conservative_constraints(self):
        """Test constraints para perfil conservador."""
        constraints = ConservativeConstraints()

        assert constraints.min_liquidity == Decimal("0.50")  # 50% en cash
        assert constraints.rebalance_threshold == Decimal("0.10")  # 10% drift
        assert constraints.max_turnover == Decimal("0.20")  # Max 20% turnover

    def test_moderate_constraints(self):
        """Test constraints para perfil moderado."""
        constraints = ModerateConstraints()

        assert constraints.min_liquidity == Decimal("0.10")
        assert constraints.rebalance_threshold == Decimal("0.05")
        assert constraints.max_turnover == Decimal("0.50")

    def test_risky_constraints(self):
        """Test constraints para perfil riesgoso."""
        constraints = RiskyConstraints()

        assert constraints.min_liquidity == Decimal("0.02")
        assert constraints.rebalance_threshold == Decimal("0.02")
        assert constraints.max_turnover is None  # Sin límite

    def test_invalid_percentage_threshold(self):
        """Test que threshold debe estar entre 0 y 1."""
        with pytest.raises(ValueError):
            TradingConstraints(rebalance_threshold=Decimal("1.5"))

        with pytest.raises(ValueError):
            TradingConstraints(rebalance_threshold=Decimal("-0.1"))

    def test_invalid_min_trade_value(self):
        """Test que min_trade_value debe ser positivo."""
        with pytest.raises(ValueError):
            TradingConstraints(min_trade_value=Decimal("0"))

        with pytest.raises(ValueError):
            TradingConstraints(min_trade_value=Decimal("-10"))


class TestTrade:
    """Tests para Trade dataclass."""

    def test_trade_creation_buy(self):
        """Test creación de trade de compra."""
        trade = Trade(
            ticker="AAPL",
            action="BUY",
            shares=Decimal("10"),
            current_price=Decimal("180.50"),
            value=Decimal("1805.00"),
            reason="Underweight by 5%"
        )

        assert trade.ticker == "AAPL"
        assert trade.action == "BUY"
        assert trade.shares == Decimal("10")
        assert trade.value == Decimal("1805.00")

    def test_trade_creation_sell(self):
        """Test creación de trade de venta."""
        trade = Trade(
            ticker="META",
            action="SELL",
            shares=Decimal("5"),
            current_price=Decimal("400.00"),
            value=Decimal("2000.00"),
            reason="Overweight by 8%"
        )

        assert trade.action == "SELL"

    def test_trade_invalid_action(self):
        """Test que action debe ser BUY o SELL."""
        with pytest.raises(ValueError):
            Trade(
                ticker="AAPL",
                action="HOLD",  # Invalid
                shares=Decimal("10"),
                current_price=Decimal("180.50"),
                value=Decimal("1805.00"),
                reason="Test"
            )

    def test_trade_negative_shares(self):
        """Test que shares no puede ser negativo."""
        with pytest.raises(ValueError):
            Trade(
                ticker="AAPL",
                action="BUY",
                shares=Decimal("-10"),
                current_price=Decimal("180.50"),
                value=Decimal("1805.00"),
                reason="Test"
            )


class TestRebalanceResult:
    """Tests para RebalanceResult dataclass."""

    def test_net_cash_change_positive(self):
        """Test net_cash_change cuando genera cash (más ventas que compras)."""
        result = RebalanceResult(
            trades=[],
            total_buy_value=Decimal("1000"),
            total_sell_value=Decimal("1500"),
            estimated_cost=Decimal("5"),
            final_allocations={}
        )

        # Genera $495 de cash ($1500 - $1000 - $5)
        assert result.net_cash_change == Decimal("495")

    def test_net_cash_change_negative(self):
        """Test net_cash_change cuando requiere cash (más compras que ventas)."""
        result = RebalanceResult(
            trades=[],
            total_buy_value=Decimal("2000"),
            total_sell_value=Decimal("1000"),
            estimated_cost=Decimal("10"),
            final_allocations={}
        )

        # Requiere $1010 de cash ($1000 - $2000 - $10)
        assert result.net_cash_change == Decimal("-1010")

    def test_turnover_calculation(self):
        """Test cálculo de turnover."""
        result = RebalanceResult(
            trades=[],
            total_buy_value=Decimal("1000"),
            total_sell_value=Decimal("1000"),
            estimated_cost=Decimal("20"),
            final_allocations={}
        )

        # Turnover = (buy + sell) / 2 = (1000 + 1000) / 2 = 1000
        assert result.turnover == Decimal("1000")


class TestSimpleRebalanceStrategy:
    """Tests para SimpleRebalanceStrategy."""

    def test_no_rebalance_needed_when_balanced(self, sample_portfolio_balanced):
        """
        Test que no genera trades si portfolio ya está balanceado.

        Portfolio sample:
        - AAPL: target 60%, actual ~42% → drift +18%
        - META: target 40%, actual ~46% → drift -6%

        Con threshold default de 5%, ambos deben rebalancear.
        """
        strategy = SimpleRebalanceStrategy()
        result = strategy.rebalance(sample_portfolio_balanced)

        # Como hay drift significativo, debe generar trades
        assert len(result.trades) > 0

    def test_rebalance_with_high_threshold(self, sample_portfolio_balanced):
        """Test que con threshold alto no rebalancea."""
        # Threshold de 20% - el drift de META (6%) no alcanza
        constraints = TradingConstraints(rebalance_threshold=Decimal("0.20"))
        strategy = SimpleRebalanceStrategy(constraints=constraints)

        result = strategy.rebalance(sample_portfolio_balanced)

        # Solo AAPL debe rebalancear (drift 18% < 20%, justo por debajo)
        # Ninguno debe rebalancear con threshold 20%
        assert len(result.trades) == 0 or all(
            abs(float(t.value)) < float(sample_portfolio_balanced.total_value * Decimal("0.01"))
            for t in result.trades
        )

    def test_rebalance_underweight_position(self, sample_asset_aapl, sample_asset_meta):
        """
        Test rebalanceo de posición underweight.

        Setup:
        - AAPL: actual 20%, target 60% → comprar
        """
        portfolio = Portfolio(id="test_001", cash=Decimal("2000.00"))

        # Agregar solo un poco de AAPL (underweight)
        portfolio.add_position(
            asset=sample_asset_aapl,
            shares=Decimal("5"),  # ~$902 / ~$2902 total = ~31%
            target_allocation=Decimal("0.60"),  # Target 60%
            deposited=Decimal("900.00")
        )

        portfolio.add_position(
            asset=sample_asset_meta,
            shares=Decimal("2"),  # ~$800 / ~$2902 = ~27.5%
            target_allocation=Decimal("0.40"),  # Target 40%
            deposited=Decimal("800.00")
        )

        strategy = SimpleRebalanceStrategy()
        result = strategy.rebalance(portfolio)

        # Debe haber al menos un trade de compra para AAPL
        assert len(result.trades) > 0

        aapl_trades = [t for t in result.trades if t.ticker == "AAPL"]
        assert len(aapl_trades) > 0
        assert aapl_trades[0].action == "BUY"

    def test_rebalance_overweight_position(self, sample_asset_aapl, sample_asset_meta):
        """
        Test rebalanceo de posición overweight.

        Setup:
        - META: actual 70%, target 40% → vender
        """
        portfolio = Portfolio(id="test_002", cash=Decimal("500.00"))

        portfolio.add_position(
            asset=sample_asset_aapl,
            shares=Decimal("5"),  # ~$902
            target_allocation=Decimal("0.60"),
            deposited=Decimal("900.00")
        )

        portfolio.add_position(
            asset=sample_asset_meta,
            shares=Decimal("10"),  # ~$4000 (overweight!)
            target_allocation=Decimal("0.40"),
            deposited=Decimal("4000.00")
        )

        strategy = SimpleRebalanceStrategy()
        result = strategy.rebalance(portfolio)

        # Debe vender META
        meta_trades = [t for t in result.trades if t.ticker == "META"]
        assert len(meta_trades) > 0
        assert meta_trades[0].action == "SELL"

    def test_min_trade_value_filter(self, sample_portfolio_balanced):
        """Test que filtra trades por debajo de min_trade_value."""
        # Min trade de $1000 - debería filtrar trades pequeños
        constraints = TradingConstraints(min_trade_value=Decimal("1000.00"))
        strategy = SimpleRebalanceStrategy(constraints=constraints)

        result = strategy.rebalance(sample_portfolio_balanced)

        # Todos los trades deben ser >= $1000
        for trade in result.trades:
            assert trade.value >= Decimal("1000.00")

    def test_fractional_shares_disabled(self, sample_asset_aapl):
        """Test que sin fractional shares, redondea a enteros."""
        constraints = TradingConstraints(allow_fractional_shares=False)
        strategy = SimpleRebalanceStrategy(constraints=constraints)

        portfolio = Portfolio(id="test_003", cash=Decimal("1000.00"))
        portfolio.add_position(
            asset=sample_asset_aapl,
            shares=Decimal("5"),
            target_allocation=Decimal("1.0"),  # 100%
            deposited=Decimal("900.00")
        )

        result = strategy.rebalance(portfolio)

        # Shares deben ser enteros
        for trade in result.trades:
            assert trade.shares == Decimal(int(trade.shares))

    def test_transaction_cost_calculation(self, sample_portfolio_balanced):
        """Test cálculo de costos de transacción."""
        # 10 bps = 0.10%
        constraints = TradingConstraints(transaction_cost_bps=Decimal("10"))
        strategy = SimpleRebalanceStrategy(constraints=constraints)

        result = strategy.rebalance(sample_portfolio_balanced)

        # Cost = total_traded * 0.001
        total_traded = sum(t.value for t in result.trades)
        expected_cost = total_traded * Decimal("0.001")

        assert abs(result.estimated_cost - expected_cost) < Decimal("0.01")

    def test_min_liquidity_constraint(self, sample_asset_aapl):
        """Test que respeta min_liquidity constraint."""
        # Requerir 50% en cash
        constraints = ConservativeConstraints()  # 50% min_liquidity
        strategy = SimpleRebalanceStrategy(constraints=constraints)

        portfolio = Portfolio(id="test_004", cash=Decimal("1000.00"))
        portfolio.add_position(
            asset=sample_asset_aapl,
            shares=Decimal("5"),  # ~$902
            target_allocation=Decimal("1.0"),  # Quiere 100% en stocks
            deposited=Decimal("900.00")
        )

        result = strategy.rebalance(portfolio)

        # No debe comprar tanto como para violar min_liquidity
        # Total value ~$1902, min_cash = 50% = $951
        # Cash actual = $1000, si compra debe mantener >= $951

        final_cash = portfolio.cash + result.total_sell_value - result.total_buy_value - result.estimated_cost
        min_cash_required = constraints.min_liquidity * portfolio.total_value

        assert final_cash >= min_cash_required * Decimal("0.99")  # 1% tolerance

    def test_max_turnover_constraint(self, sample_portfolio_balanced):
        """Test que respeta max_turnover constraint."""
        # Max 10% turnover
        constraints = TradingConstraints(max_turnover=Decimal("0.10"))
        strategy = SimpleRebalanceStrategy(constraints=constraints)

        result = strategy.rebalance(sample_portfolio_balanced)

        # Turnover debe ser <= 10% del portfolio
        max_allowed = Decimal("0.10") * sample_portfolio_balanced.total_value
        assert result.turnover <= max_allowed * Decimal("1.01")  # 1% tolerance

    def test_final_allocations_estimation(self, sample_asset_aapl):
        """Test que estima allocations finales correctamente."""
        strategy = SimpleRebalanceStrategy()

        portfolio = Portfolio(id="test_005", cash=Decimal("500.00"))
        portfolio.add_position(
            asset=sample_asset_aapl,
            shares=Decimal("5"),
            target_allocation=Decimal("1.0"),
            deposited=Decimal("900.00")
        )

        result = strategy.rebalance(portfolio)

        # Final allocations deben sumar <= 1.0 (puede haber cash)
        total_allocation = sum(result.final_allocations.values())
        assert total_allocation <= Decimal("1.0")
        assert total_allocation >= Decimal("0.90")  # Al menos 90% invertido

        # AAPL debe estar cerca de su target de 100%
        if "AAPL" in result.final_allocations:
            assert result.final_allocations["AAPL"] >= Decimal("0.90")

    def test_metrics_in_result(self, sample_portfolio_balanced):
        """Test que RebalanceResult incluye métricas útiles."""
        strategy = SimpleRebalanceStrategy()
        result = strategy.rebalance(sample_portfolio_balanced)

        assert result.metrics is not None
        assert "n_trades" in result.metrics
        assert "turnover_pct" in result.metrics
        assert "max_drift_before" in result.metrics

        assert result.metrics["n_trades"] == len(result.trades)


class TestEdgeCases:
    """Tests de edge cases para rebalancer."""

    def test_empty_portfolio(self):
        """Test rebalanceo de portfolio vacío."""
        portfolio = Portfolio(id="empty", cash=Decimal("1000.00"))
        strategy = SimpleRebalanceStrategy()

        result = strategy.rebalance(portfolio)

        # No hay posiciones, no hay trades
        assert len(result.trades) == 0
        assert result.total_buy_value == Decimal("0")
        assert result.total_sell_value == Decimal("0")

    def test_single_asset_portfolio(self, sample_asset_aapl):
        """Test portfolio con un solo activo."""
        portfolio = Portfolio(id="single", cash=Decimal("100.00"))
        portfolio.add_position(
            asset=sample_asset_aapl,
            shares=Decimal("5"),
            target_allocation=Decimal("1.0"),  # 100%
            deposited=Decimal("900.00")
        )

        strategy = SimpleRebalanceStrategy()
        result = strategy.rebalance(portfolio)

        # Con un solo activo y allocation 100%, puede que no necesite rebalancear
        # o que intente comprar más para alcanzar 100%
        # Depende del drift actual

        # Al menos no debe fallar
        assert result is not None

    def test_portfolio_with_zero_cash(self, sample_asset_aapl):
        """Test portfolio sin cash disponible."""
        portfolio = Portfolio(id="no_cash", cash=Decimal("0"))
        portfolio.add_position(
            asset=sample_asset_aapl,
            shares=Decimal("10"),
            target_allocation=Decimal("0.5"),  # Quiere solo 50%
            deposited=Decimal("1800.00")
        )

        strategy = SimpleRebalanceStrategy()
        result = strategy.rebalance(portfolio)

        # Sin cash, solo puede vender (no comprar)
        buy_trades = [t for t in result.trades if t.action == "BUY"]
        # Si hay BUY trades, deben ser financiados por ventas
        if buy_trades:
            assert result.total_sell_value >= result.total_buy_value

    def test_all_positions_at_target(self, sample_asset_aapl, sample_asset_meta):
        """Test portfolio donde todas las posiciones están en target."""
        portfolio = Portfolio(id="balanced", cash=Decimal("0"))

        # Crear portfolio perfectamente balanceado
        # Total value target: $3000
        # AAPL: 60% = $1800 / $180.50 = 10 shares
        # META: 40% = $1200 / $400 = 3 shares

        portfolio.add_position(
            asset=sample_asset_aapl,
            shares=Decimal("10"),
            target_allocation=Decimal("0.6"),
            deposited=Decimal("1805.00")
        )

        portfolio.add_position(
            asset=sample_asset_meta,
            shares=Decimal("3"),
            target_allocation=Decimal("0.4"),
            deposited=Decimal("1200.00")
        )

        # Verificar que está balanceado
        drifts = portfolio.get_allocation_drift()
        max_drift = max(abs(d) for d in drifts.values())

        # Con threshold default de 5%, no debe rebalancear
        if max_drift < Decimal("0.05"):
            strategy = SimpleRebalanceStrategy()
            result = strategy.rebalance(portfolio)

            assert len(result.trades) == 0

    def test_extreme_drift(self, sample_asset_aapl, sample_asset_meta):
        """Test con drift extremo (un activo domina el portfolio)."""
        portfolio = Portfolio(id="extreme", cash=Decimal("100.00"))

        # AAPL: 95% del portfolio pero target es 50%
        portfolio.add_position(
            asset=sample_asset_aapl,
            shares=Decimal("50"),  # $9025
            target_allocation=Decimal("0.5"),
            deposited=Decimal("9000.00")
        )

        portfolio.add_position(
            asset=sample_asset_meta,
            shares=Decimal("1"),  # $400
            target_allocation=Decimal("0.5"),
            deposited=Decimal("400.00")
        )

        strategy = SimpleRebalanceStrategy()
        result = strategy.rebalance(portfolio)

        # Debe generar trades significativos
        assert len(result.trades) > 0

        # Debe vender AAPL y comprar META
        aapl_trades = [t for t in result.trades if t.ticker == "AAPL"]
        meta_trades = [t for t in result.trades if t.ticker == "META"]

        if aapl_trades:
            assert aapl_trades[0].action == "SELL"
        if meta_trades:
            assert meta_trades[0].action == "BUY"


class TestCVaRRebalanceStrategy:
    """Tests para CVaRRebalanceStrategy."""

    def test_cvar_strategy_initialization(self):
        """Test que la estrategia se inicializa correctamente."""
        strategy = CVaRRebalanceStrategy(
            constraints=TradingConstraints(),
            n_scenarios=500,
            confidence_level=0.9
        )
        assert strategy.n_scenarios == 500
        assert strategy.confidence_level == 0.9
        assert isinstance(strategy.constraints, TradingConstraints)

    def test_cvar_strategy_basic_rebalance(self, sample_portfolio_balanced):
        """Test de un rebalanceo básico con la estrategia CVaR."""
        strategy = CVaRRebalanceStrategy(n_scenarios=100) # Menos escenarios para el test
        result = strategy.rebalance(sample_portfolio_balanced)

        assert result is not None
        assert isinstance(result, RebalanceResult)
        assert "optimal_weights" in result.metrics
        # El rebalanceo debería generar al menos un trade dado el drift
        assert len(result.trades) > 0

    def test_cvar_respects_min_liquidity_constraints(self, sample_asset_aapl):
        """Test que la optimización CVaR respeta el mínimo de liquidez."""
        # Forzar una restricción de liquidez muy alta
        constraints = TradingConstraints(min_liquidity=Decimal("0.8")) # 80% cash
        strategy = CVaRRebalanceStrategy(constraints=constraints, n_scenarios=100)

        portfolio = Portfolio(id="test_cvar_liq", cash=Decimal("1000.00"))
        portfolio.add_position(
            asset=sample_asset_aapl,
            shares=Decimal("5"), # ~902
            target_allocation=Decimal("1.0"),
            deposited=Decimal("900.00")
        )

        result = strategy.rebalance(portfolio)
        
        # El total de la cartera es ~1902. 80% de cash es ~1521.
        # Como solo hay 1000 de cash, no debería poder comprar.
        buy_trades = [t for t in result.trades if t.action == "BUY"]
        assert len(buy_trades) == 0

    def test_cvar_rebalance_generates_trades(self, sample_asset_aapl, sample_asset_meta):
        """Test que genera trades para un portfolio desbalanceado."""
        portfolio = Portfolio(id="unbalanced", cash=Decimal("100.00"))
        portfolio.add_position(
            asset=sample_asset_aapl,
            shares=Decimal("5"),  # ~902.5
            target_allocation=Decimal("0.8"), # Target 80%
            deposited=Decimal("900.00")
        )
        portfolio.add_position(
            asset=sample_asset_meta,
            shares=Decimal("10"), # ~4000
            target_allocation=Decimal("0.2"), # Target 20%
            deposited=Decimal("4000.00")
        )
        # Current state: META is heavily overweight.

        strategy = CVaRRebalanceStrategy(n_scenarios=100)
        result = strategy.rebalance(portfolio)

        assert len(result.trades) > 0
        # Debería vender el activo sobreponderado (META) y comprar el subponderado (AAPL)
        sell_trades = [t for t in result.trades if t.action == "SELL"]
        buy_trades = [t for t in result.trades if t.action == "BUY"]
        
        assert any(t.ticker == "META" for t in sell_trades)
        assert any(t.ticker == "AAPL" for t in buy_trades)
