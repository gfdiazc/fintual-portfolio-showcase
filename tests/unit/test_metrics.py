"""
Unit tests para metrics (CVaR, Monte Carlo, etc).

Testing strategy:
- Tests de CVaR calculation
- Tests de Monte Carlo simulation
- Tests de métricas financieras (Sharpe, Sortino, etc)
- Validación contra casos conocidos
"""

import pytest
import numpy as np
from decimal import Decimal

from app.core.metrics import (
    CVaRCalculator,
    MonteCarloSimulator,
    PortfolioMetrics,
    RiskMetrics,
    calculate_portfolio_cvar_monte_carlo
)


class TestCVaRCalculator:
    """Tests para CVaR calculation."""

    def test_cvar_calculator_initialization(self):
        """Test creación de CVaR calculator."""
        calc = CVaRCalculator(confidence_level=0.95)
        assert calc.confidence_level == 0.95
        assert abs(calc.alpha - 0.05) < 1e-10  # Floating point precision

    def test_cvar_calculator_invalid_confidence(self):
        """Test que confidence_level debe estar entre 0 y 1."""
        with pytest.raises(ValueError):
            CVaRCalculator(confidence_level=0)

        with pytest.raises(ValueError):
            CVaRCalculator(confidence_level=1.5)

    def test_calculate_cvar_simple(self):
        """Test cálculo de CVaR con datos simples."""
        calc = CVaRCalculator(confidence_level=0.95)

        # 100 retornos: 5% peores = 5 retornos
        # Crear 95 retornos positivos y 5 negativos
        positive_returns = np.array([0.01] * 95)
        negative_returns = np.array([-0.10, -0.08, -0.06, -0.04, -0.02])
        returns = np.concatenate([positive_returns, negative_returns])

        cvar = calc.calculate_cvar(returns)

        # CVaR = promedio de los 5 peores = (-0.10 -0.08 -0.06 -0.04 -0.02)/5 = -0.06
        # Verificar que CVaR está en rango razonable
        assert 0.04 < cvar < 0.07

    def test_calculate_cvar_normal_distribution(self):
        """Test CVaR con distribución normal conocida."""
        np.random.seed(42)
        calc = CVaRCalculator(confidence_level=0.95)

        # Generar retornos normales: mean=0.001, std=0.02
        returns = np.random.normal(loc=0.001, scale=0.02, size=10000)

        cvar = calc.calculate_cvar(returns)

        # Para distribución normal, CVaR_0.95 ≈ mean - 2.06 * std
        # = 0.001 - 2.06 * 0.02 ≈ -0.040
        expected_cvar = abs(0.001 - 2.06 * 0.02)

        # Tolerancia para variación Monte Carlo
        assert abs(cvar - expected_cvar) < 0.01

    def test_calculate_var(self):
        """Test cálculo de VaR."""
        calc = CVaRCalculator(confidence_level=0.95)

        # 100 retornos: VaR_0.95 = percentil 5%
        positive_returns = np.array([0.01] * 95)
        negative_returns = np.array([-0.10, -0.08, -0.06, -0.04, -0.02])
        returns = np.concatenate([positive_returns, negative_returns])

        var = calc.calculate_var(returns)

        # VaR debería estar en el 5% tail
        assert 0.005 < var < 0.03

    def test_cvar_empty_array(self):
        """Test que CVaR falla con array vacío."""
        calc = CVaRCalculator()

        with pytest.raises(ValueError):
            calc.calculate_cvar(np.array([]))


class TestMonteCarloSimulator:
    """Tests para Monte Carlo simulation."""

    def test_simulator_initialization(self):
        """Test creación de simulator."""
        sim = MonteCarloSimulator(n_scenarios=1000, random_seed=42)
        assert sim.n_scenarios == 1000

    def test_simulate_returns_normal(self):
        """Test simulación de retornos normales."""
        sim = MonteCarloSimulator(n_scenarios=100, random_seed=42)

        returns = sim.simulate_returns(
            mean_return=0.08,  # 8% anual
            volatility=0.15,   # 15% vol
            n_periods=252,
            distribution="normal"
        )

        # Shape correcto
        assert returns.shape == (100, 252)

        # Mean aproximado (puede variar por Monte Carlo)
        mean_daily = np.mean(returns)
        expected_mean_daily = 0.08 / 252

        # Tolerancia amplia para variación Monte Carlo
        assert abs(mean_daily - expected_mean_daily) < 0.01

    def test_simulate_returns_student_t(self):
        """Test simulación con Student-t (fat tails)."""
        sim = MonteCarloSimulator(n_scenarios=100, random_seed=42)

        returns = sim.simulate_returns(
            mean_return=0.08,
            volatility=0.15,
            n_periods=252,
            distribution="student_t"
        )

        assert returns.shape == (100, 252)

        # Student-t debe tener fat tails (mayor kurtosis)
        kurtosis = np.mean((returns - np.mean(returns))**4) / np.var(returns)**2
        # Kurtosis > 3 indica fat tails
        assert kurtosis > 3

    def test_simulate_returns_invalid_distribution(self):
        """Test que distribución inválida falla."""
        sim = MonteCarloSimulator(n_scenarios=100)

        with pytest.raises(ValueError):
            sim.simulate_returns(
                mean_return=0.08,
                volatility=0.15,
                distribution="invalid"
            )

    def test_simulate_portfolio_returns(self):
        """Test simulación de portfolio multi-activo."""
        sim = MonteCarloSimulator(n_scenarios=100, random_seed=42)

        # Portfolio 60/40
        weights = np.array([0.6, 0.4])
        expected_returns = np.array([0.08, 0.10])  # 8%, 10%
        cov_matrix = np.array([
            [0.04, 0.01],  # var(asset1)=0.04, cov=0.01
            [0.01, 0.06]   # cov=0.01, var(asset2)=0.06
        ])

        portfolio_returns = sim.simulate_portfolio_returns(
            weights=weights,
            expected_returns=expected_returns,
            cov_matrix=cov_matrix,
            n_periods=252
        )

        # Shape correcto
        assert portfolio_returns.shape == (100,)

        # Portfolio return esperado ≈ 0.6*0.08 + 0.4*0.10 = 0.088
        mean_return = np.mean(portfolio_returns)
        expected_return = 0.088

        # Tolerancia amplia
        assert abs(mean_return - expected_return) < 0.05

    def test_simulate_portfolio_invalid_weights(self):
        """Test que weights deben sumar 1."""
        sim = MonteCarloSimulator(n_scenarios=10)

        weights = np.array([0.7, 0.5])  # Sum = 1.2
        expected_returns = np.array([0.08, 0.10])
        cov_matrix = np.array([[0.04, 0.01], [0.01, 0.06]])

        with pytest.raises(ValueError):
            sim.simulate_portfolio_returns(
                weights, expected_returns, cov_matrix
            )

    def test_simulate_portfolio_dimension_mismatch(self):
        """Test que dimensiones deben coincidir."""
        sim = MonteCarloSimulator(n_scenarios=10)

        weights = np.array([0.6, 0.4])
        expected_returns = np.array([0.08, 0.10, 0.09])  # 3 elementos!
        cov_matrix = np.array([[0.04, 0.01], [0.01, 0.06]])

        with pytest.raises(ValueError):
            sim.simulate_portfolio_returns(
                weights, expected_returns, cov_matrix
            )


class TestPortfolioMetrics:
    """Tests para portfolio metrics."""

    def test_sharpe_ratio_positive(self):
        """Test Sharpe ratio con retornos positivos."""
        np.random.seed(42)

        # Retornos con mean positivo
        returns = np.random.normal(loc=0.001, scale=0.01, size=252)

        sharpe = PortfolioMetrics.calculate_sharpe_ratio(
            returns, risk_free_rate=0.02
        )

        # Sharpe debe ser razonable (no NaN, no infinito)
        assert not np.isnan(sharpe)
        assert not np.isinf(sharpe)

    def test_sharpe_ratio_zero_volatility(self):
        """Test Sharpe con volatilidad cero retorna 0."""
        # Retornos constantes (vol = 0)
        returns = np.array([0.001] * 100)

        sharpe = PortfolioMetrics.calculate_sharpe_ratio(returns)

        assert sharpe == 0.0

    def test_sortino_ratio(self):
        """Test Sortino ratio (solo downside risk)."""
        # Mix de retornos positivos y negativos
        returns = np.array([
            0.02, 0.01, -0.01, 0.03, -0.02,
            0.01, 0.02, -0.01, 0.01, 0.02
        ])

        sortino = PortfolioMetrics.calculate_sortino_ratio(
            returns, risk_free_rate=0.02
        )

        # Sortino debería ser > 0 si mean > rf
        assert not np.isnan(sortino)

    def test_max_drawdown_calculation(self):
        """Test cálculo de maximum drawdown."""
        # Simular crash de -50%
        cumulative_returns = np.array([
            1.0, 1.1, 1.2, 1.3, 1.2,  # Sube
            0.6, 0.7, 0.8, 0.9, 1.0   # Crash -50%, luego recupera
        ])

        mdd = PortfolioMetrics.calculate_max_drawdown(cumulative_returns)

        # Max drawdown = (0.6 - 1.3) / 1.3 ≈ -0.538 → 0.538
        expected_mdd = abs((0.6 - 1.3) / 1.3)

        assert abs(mdd - expected_mdd) < 0.01

    def test_max_drawdown_no_losses(self):
        """Test drawdown con solo ganancias."""
        cumulative_returns = np.array([1.0, 1.1, 1.2, 1.3, 1.4])

        mdd = PortfolioMetrics.calculate_max_drawdown(cumulative_returns)

        # No debería haber drawdown
        assert mdd == 0.0

    def test_volatility_calculation(self):
        """Test cálculo de volatilidad."""
        np.random.seed(42)
        returns = np.random.normal(loc=0.0, scale=0.02, size=252)

        vol = PortfolioMetrics.calculate_volatility(returns, annualize=True)

        # Vol anualizada ≈ 0.02 * sqrt(252) ≈ 0.317
        expected_vol = 0.02 * np.sqrt(252)

        assert abs(vol - expected_vol) < 0.05

    def test_volatility_not_annualized(self):
        """Test volatilidad sin anualizar."""
        np.random.seed(42)
        returns = np.random.normal(loc=0.0, scale=0.02, size=252)

        vol = PortfolioMetrics.calculate_volatility(returns, annualize=False)

        # Vol diaria ≈ 0.02
        assert abs(vol - 0.02) < 0.01

    def test_calculate_all_metrics(self):
        """Test cálculo de todas las métricas juntas."""
        np.random.seed(42)
        returns = np.random.normal(loc=0.001, scale=0.02, size=252)

        metrics = PortfolioMetrics.calculate_all_metrics(
            returns, confidence_level=0.95, risk_free_rate=0.02
        )

        # Verificar que todas las métricas están presentes
        assert isinstance(metrics, RiskMetrics)
        assert metrics.cvar >= 0
        assert metrics.var >= 0
        assert metrics.volatility >= 0
        assert metrics.downside_deviation >= 0
        assert metrics.max_drawdown >= 0
        assert metrics.sharpe_ratio is not None
        assert metrics.sortino_ratio is not None

        # CVaR debe ser >= VaR (propiedad matemática)
        assert metrics.cvar >= metrics.var

    def test_calculate_all_metrics_empty(self):
        """Test métricas con array vacío."""
        metrics = PortfolioMetrics.calculate_all_metrics(np.array([]))

        # Todas las métricas deben ser 0
        assert metrics.cvar == 0.0
        assert metrics.var == 0.0
        assert metrics.volatility == 0.0


class TestPortfolioCVaRMonteCarlo:
    """Tests para función integrada de CVaR con Monte Carlo."""

    def test_calculate_portfolio_cvar_monte_carlo(self):
        """Test cálculo completo de CVaR con Monte Carlo."""
        # Portfolio 60/40
        weights = np.array([0.6, 0.4])
        expected_returns = np.array([0.08, 0.10])
        cov_matrix = np.array([
            [0.04, 0.01],
            [0.01, 0.06]
        ])

        cvar, simulated_returns = calculate_portfolio_cvar_monte_carlo(
            weights=weights,
            expected_returns=expected_returns,
            cov_matrix=cov_matrix,
            confidence_level=0.95,
            n_scenarios=1000,
            n_periods=252
        )

        # CVaR debe ser positivo
        assert cvar >= 0

        # Simulated returns debe tener 1000 escenarios
        assert len(simulated_returns) == 1000

        # CVaR debe ser razonable (no demasiado grande)
        # Para portfolio con vol ~20%, CVaR_0.95 debería ser < 50%
        assert cvar < 0.5

    def test_cvar_monte_carlo_different_confidence_levels(self):
        """Test CVaR con diferentes niveles de confianza."""
        weights = np.array([0.5, 0.5])
        expected_returns = np.array([0.08, 0.10])
        cov_matrix = np.array([[0.04, 0.01], [0.01, 0.06]])

        # CVaR_0.95 (5% tail)
        cvar_95, _ = calculate_portfolio_cvar_monte_carlo(
            weights, expected_returns, cov_matrix,
            confidence_level=0.95,
            n_scenarios=1000
        )

        # CVaR_0.99 (1% tail)
        cvar_99, _ = calculate_portfolio_cvar_monte_carlo(
            weights, expected_returns, cov_matrix,
            confidence_level=0.99,
            n_scenarios=1000
        )

        # CVaR_0.99 debe ser mayor (peores escenarios)
        assert cvar_99 > cvar_95

    def test_cvar_monte_carlo_reproducibility(self):
        """Test que resultados son reproducibles con seed."""
        weights = np.array([0.5, 0.5])
        expected_returns = np.array([0.08, 0.10])
        cov_matrix = np.array([[0.04, 0.01], [0.01, 0.06]])

        # Dos corridas con mismo seed deberían dar mismo resultado
        np.random.seed(42)
        cvar1, _ = calculate_portfolio_cvar_monte_carlo(
            weights, expected_returns, cov_matrix, n_scenarios=100
        )

        np.random.seed(42)
        cvar2, _ = calculate_portfolio_cvar_monte_carlo(
            weights, expected_returns, cov_matrix, n_scenarios=100
        )

        assert cvar1 == cvar2


class TestEdgeCases:
    """Tests de edge cases para métricas."""

    def test_cvar_all_positive_returns(self):
        """Test CVaR con solo retornos positivos."""
        calc = CVaRCalculator(confidence_level=0.95)
        returns = np.array([0.01, 0.02, 0.03, 0.04, 0.05] * 20)

        cvar = calc.calculate_cvar(returns)

        # CVaR debería ser muy pequeño (casi 0)
        assert cvar < 0.02

    def test_cvar_all_negative_returns(self):
        """Test CVaR con solo retornos negativos."""
        calc = CVaRCalculator(confidence_level=0.95)
        returns = np.array([-0.01, -0.02, -0.03, -0.04, -0.05] * 20)

        cvar = calc.calculate_cvar(returns)

        # CVaR debería ser grande (promedio de pérdidas)
        assert cvar > 0.04

    def test_metrics_with_extreme_volatility(self):
        """Test métricas con volatilidad extrema."""
        # Retornos muy volátiles
        returns = np.array([0.1, -0.1, 0.15, -0.15, 0.2, -0.2] * 40)

        metrics = PortfolioMetrics.calculate_all_metrics(returns)

        # Volatilidad debe ser alta
        assert metrics.volatility > 1.0

        # CVaR también debe ser significativo
        assert metrics.cvar > 0.1
