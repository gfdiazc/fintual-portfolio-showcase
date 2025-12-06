"""
Financial metrics and risk calculations.

Alineado con Fintual:
- CVaR (Conditional Value-at-Risk) como medida de riesgo principal
- Monte Carlo sampling para robustez
- Métricas core: Balance, Depositado Neto, Ganado

Filosofía: CVaR es una medida de riesgo "coherente" matemáticamente,
superior a volatilidad o VaR para capturar tail risk.
"""

import numpy as np
from decimal import Decimal
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass


@dataclass
class RiskMetrics:
    """
    Conjunto de métricas de riesgo para un portfolio.

    Alineado con Fintual:
    - CVaR como medida principal
    - Volatilidad como secundaria
    - Métricas de downside risk
    """
    cvar: float  # Conditional Value-at-Risk
    var: float  # Value-at-Risk
    volatility: float  # Desviación estándar anualizada
    downside_deviation: float  # Solo volatilidad negativa
    max_drawdown: float  # Máxima caída desde peak
    sharpe_ratio: Optional[float] = None  # Sharpe (secundario)
    sortino_ratio: Optional[float] = None  # Sortino (downside risk)


class CVaRCalculator:
    """
    Calculadora de CVaR (Conditional Value-at-Risk).

    CVaR (Expected Shortfall) mide el nivel de pérdida promedio
    en los peores escenarios (tail risk).

    Ventajas sobre VaR:
    - Medida de riesgo "coherente" (cumple propiedades matemáticas deseables)
    - Captura la magnitud de pérdidas extremas, no solo su probabilidad
    - Base de la estrategia de optimización de Fintual

    References:
    - Rockafellar & Uryasev (2000): "Optimization of CVaR"
    - Fintual research on CVaR-based portfolio optimization
    """

    def __init__(self, confidence_level: float = 0.95):
        """
        Args:
            confidence_level: Nivel de confianza (α). Default 0.95 (95%)
                             CVaR_0.95 = promedio del 5% peores retornos
        """
        if not 0 < confidence_level < 1:
            raise ValueError(f"confidence_level debe estar entre 0 y 1, got {confidence_level}")

        self.confidence_level = confidence_level
        self.alpha = 1 - confidence_level  # Percentil de pérdidas

    def calculate_cvar(self, returns: np.ndarray) -> float:
        """
        Calcula CVaR (Conditional Value-at-Risk) de una serie de retornos.

        CVaR_α = E[X | X ≤ VaR_α]
        Es decir, el promedio de pérdidas que exceden el VaR.

        Args:
            returns: Array de retornos (pueden ser históricos o simulados)

        Returns:
            CVaR como valor absoluto (positivo indica pérdida esperada)

        Example:
            >>> returns = np.array([0.01, -0.02, 0.03, -0.05, 0.02])
            >>> calc = CVaRCalculator(confidence_level=0.95)
            >>> cvar = calc.calculate_cvar(returns)
            >>> # CVaR captura las pérdidas en el 5% peor de casos
        """
        if len(returns) == 0:
            raise ValueError("Returns array no puede estar vacío")

        # Ordenar retornos de menor a mayor (peores pérdidas primero)
        sorted_returns = np.sort(returns)

        # Calcular cuántos retornos están en el α% tail
        n_tail = max(1, int(np.ceil(self.alpha * len(sorted_returns))))

        # CVaR = promedio de los n_tail peores retornos
        tail_losses = sorted_returns[:n_tail]
        cvar = np.mean(tail_losses)

        # Retornar como valor absoluto (pérdida positiva)
        return abs(float(cvar))

    def calculate_var(self, returns: np.ndarray) -> float:
        """
        Calcula VaR (Value-at-Risk) al nivel de confianza especificado.

        VaR_α = percentil α de la distribución de pérdidas.

        Args:
            returns: Array de retornos

        Returns:
            VaR como valor absoluto
        """
        if len(returns) == 0:
            raise ValueError("Returns array no puede estar vacío")

        # Ordenar y tomar el percentil correspondiente
        sorted_returns = np.sort(returns)
        var_index = max(0, int(np.ceil(self.alpha * len(sorted_returns))) - 1)
        var = sorted_returns[var_index]

        return abs(float(var))


class MonteCarloSimulator:
    """
    Simulador Monte Carlo para generar escenarios de retornos.

    Usado por Fintual para:
    1. Generar escenarios sintéticos de mercado
    2. Estimar distribución de retornos futuros
    3. Calcular CVaR en múltiples escenarios

    Mejora sobre supuestos de normalidad (Markowitz clásico):
    - No asume distribución normal de retornos
    - Captura fat tails y asimetría
    - Más robusto para optimización
    """

    def __init__(self, n_scenarios: int = 1000, random_seed: Optional[int] = None):
        """
        Args:
            n_scenarios: Número de escenarios a simular
            random_seed: Semilla para reproducibilidad (opcional)
        """
        self.n_scenarios = n_scenarios
        if random_seed is not None:
            np.random.seed(random_seed)

    def simulate_returns(
        self,
        mean_return: float,
        volatility: float,
        n_periods: int = 252,
        distribution: str = "normal"
    ) -> np.ndarray:
        """
        Simula retornos usando Monte Carlo.

        Args:
            mean_return: Retorno esperado anualizado
            volatility: Volatilidad anualizada (desviación estándar)
            n_periods: Períodos a simular (default 252 = días de trading)
            distribution: "normal" o "student_t" (fat tails)

        Returns:
            Array de shape (n_scenarios, n_periods) con retornos simulados
        """
        if distribution == "normal":
            # Distribución normal (modelo clásico)
            daily_return = mean_return / n_periods
            daily_vol = volatility / np.sqrt(n_periods)

            returns = np.random.normal(
                loc=daily_return,
                scale=daily_vol,
                size=(self.n_scenarios, n_periods)
            )

        elif distribution == "student_t":
            # Student-t distribution (fat tails más realistas)
            df = 5  # Grados de libertad (menor = colas más gordas)
            daily_return = mean_return / n_periods
            daily_vol = volatility / np.sqrt(n_periods)

            # Ajustar escala para student-t
            scale = daily_vol * np.sqrt((df - 2) / df)

            returns = np.random.standard_t(df, size=(self.n_scenarios, n_periods))
            returns = daily_return + scale * returns

        else:
            raise ValueError(f"Distribution '{distribution}' no soportada")

        return returns

    def simulate_portfolio_returns(
        self,
        weights: np.ndarray,
        expected_returns: np.ndarray,
        cov_matrix: np.ndarray,
        n_periods: int = 252
    ) -> np.ndarray:
        """
        Simula retornos de un portfolio multi-activo.

        Usa muestreo de distribución multivariada para capturar
        correlaciones entre activos.

        Args:
            weights: Pesos del portfolio (array de tamaño n_assets)
            expected_returns: Retornos esperados anualizados (array n_assets)
            cov_matrix: Matriz de covarianza (n_assets x n_assets)
            n_periods: Períodos a simular

        Returns:
            Array de retornos del portfolio (n_scenarios,)
        """
        n_assets = len(weights)

        # Validaciones
        if len(expected_returns) != n_assets:
            raise ValueError("expected_returns debe tener mismo tamaño que weights")
        if cov_matrix.shape != (n_assets, n_assets):
            raise ValueError(f"cov_matrix debe ser {n_assets}x{n_assets}")
        if not np.isclose(np.sum(weights), 1.0):
            raise ValueError(f"Weights deben sumar 1.0, sum={np.sum(weights)}")

        # Convertir a retornos diarios
        daily_returns = expected_returns / n_periods
        daily_cov = cov_matrix / n_periods

        # Simular retornos multivariados
        portfolio_returns = []

        for _ in range(self.n_scenarios):
            # Generar retornos de cada activo (multivariados)
            asset_returns = np.random.multivariate_normal(
                mean=daily_returns,
                cov=daily_cov,
                size=n_periods
            )

            # Calcular retorno del portfolio en cada período
            period_returns = asset_returns @ weights

            # Retorno acumulado del escenario
            cumulative_return = np.prod(1 + period_returns) - 1
            portfolio_returns.append(cumulative_return)

        return np.array(portfolio_returns)


class PortfolioMetrics:
    """
    Calculadora de métricas financieras de portfolios.

    Métricas clave de Fintual:
    - CVaR (principal)
    - Sharpe ratio (secundario)
    - Sortino ratio (downside risk)
    - Max drawdown
    - Volatilidad
    """

    @staticmethod
    def calculate_sharpe_ratio(
        returns: np.ndarray,
        risk_free_rate: float = 0.02
    ) -> float:
        """
        Sharpe Ratio = (E[R] - Rf) / σ

        Mide retorno ajustado por riesgo total (volatilidad).

        Args:
            returns: Retornos diarios
            risk_free_rate: Tasa libre de riesgo anualizada

        Returns:
            Sharpe ratio anualizado
        """
        if len(returns) == 0:
            return 0.0

        # Convertir risk-free rate a diario
        daily_rf = risk_free_rate / 252

        # Calcular excess returns
        excess_returns = returns - daily_rf

        std_excess = np.std(excess_returns)

        # Si volatilidad es 0 o casi 0, retornar 0
        if std_excess < 1e-10:
            return 0.0

        # Sharpe anualizado
        sharpe = np.mean(excess_returns) / std_excess * np.sqrt(252)
        return float(sharpe)

    @staticmethod
    def calculate_sortino_ratio(
        returns: np.ndarray,
        risk_free_rate: float = 0.02
    ) -> float:
        """
        Sortino Ratio = (E[R] - Rf) / downside_deviation

        Similar a Sharpe pero solo penaliza volatilidad negativa.
        Más apropiado que Sharpe para inversores con aversión a pérdidas.

        Args:
            returns: Retornos diarios
            risk_free_rate: Tasa libre de riesgo anualizada

        Returns:
            Sortino ratio anualizado
        """
        if len(returns) == 0:
            return 0.0

        daily_rf = risk_free_rate / 252
        excess_returns = returns - daily_rf

        # Solo considerar retornos negativos para downside deviation
        downside_returns = excess_returns[excess_returns < 0]

        if len(downside_returns) == 0:
            downside_deviation = 0.0
        else:
            downside_deviation = np.std(downside_returns)

        if downside_deviation == 0:
            return 0.0

        sortino = np.mean(excess_returns) / downside_deviation * np.sqrt(252)
        return float(sortino)

    @staticmethod
    def calculate_max_drawdown(cumulative_returns: np.ndarray) -> float:
        """
        Maximum Drawdown: máxima caída desde peak histórico.

        Mide el peor escenario de pérdida que experimentó el portfolio.

        Args:
            cumulative_returns: Retornos acumulados (ej: [1.0, 1.1, 1.05, 1.15])

        Returns:
            Max drawdown como valor absoluto (0.2 = -20% pérdida)
        """
        if len(cumulative_returns) == 0:
            return 0.0

        # Running maximum (peak hasta ahora)
        running_max = np.maximum.accumulate(cumulative_returns)

        # Drawdown en cada punto
        drawdown = (cumulative_returns - running_max) / running_max

        # Máximo drawdown (valor más negativo)
        max_dd = np.min(drawdown)

        return abs(float(max_dd))

    @staticmethod
    def calculate_volatility(returns: np.ndarray, annualize: bool = True) -> float:
        """
        Volatilidad (desviación estándar de retornos).

        Nota: Fintual usa CVaR como medida principal de riesgo,
        pero volatilidad sigue siendo útil para comparaciones.

        Args:
            returns: Retornos diarios
            annualize: Si True, anualiza multiplicando por sqrt(252)

        Returns:
            Volatilidad (anualizada si annualize=True)
        """
        if len(returns) == 0:
            return 0.0

        vol = np.std(returns)

        if annualize:
            vol *= np.sqrt(252)

        return float(vol)

    @staticmethod
    def calculate_all_metrics(
        returns: np.ndarray,
        confidence_level: float = 0.95,
        risk_free_rate: float = 0.02
    ) -> RiskMetrics:
        """
        Calcula todas las métricas de riesgo de un portfolio.

        Args:
            returns: Retornos diarios
            confidence_level: Para CVaR (default 0.95)
            risk_free_rate: Tasa libre de riesgo anualizada

        Returns:
            RiskMetrics con todas las métricas calculadas
        """
        if len(returns) == 0:
            return RiskMetrics(
                cvar=0.0,
                var=0.0,
                volatility=0.0,
                downside_deviation=0.0,
                max_drawdown=0.0,
                sharpe_ratio=0.0,
                sortino_ratio=0.0
            )

        # CVaR y VaR (métricas principales de Fintual)
        cvar_calc = CVaRCalculator(confidence_level=confidence_level)
        cvar = cvar_calc.calculate_cvar(returns)
        var = cvar_calc.calculate_var(returns)

        # Volatilidad
        volatility = PortfolioMetrics.calculate_volatility(returns)

        # Downside deviation
        downside_returns = returns[returns < 0]
        if len(downside_returns) > 0:
            downside_deviation = float(np.std(downside_returns) * np.sqrt(252))
        else:
            downside_deviation = 0.0

        # Max drawdown
        cumulative_returns = np.cumprod(1 + returns)
        max_drawdown = PortfolioMetrics.calculate_max_drawdown(cumulative_returns)

        # Sharpe y Sortino
        sharpe = PortfolioMetrics.calculate_sharpe_ratio(returns, risk_free_rate)
        sortino = PortfolioMetrics.calculate_sortino_ratio(returns, risk_free_rate)

        return RiskMetrics(
            cvar=cvar,
            var=var,
            volatility=volatility,
            downside_deviation=downside_deviation,
            max_drawdown=max_drawdown,
            sharpe_ratio=sharpe,
            sortino_ratio=sortino
        )


def calculate_portfolio_cvar_monte_carlo(
    weights: np.ndarray,
    expected_returns: np.ndarray,
    cov_matrix: np.ndarray,
    confidence_level: float = 0.95,
    n_scenarios: int = 1000,
    n_periods: int = 252
) -> Tuple[float, np.ndarray]:
    """
    Calcula CVaR de un portfolio usando Monte Carlo simulation.

    Este es el método usado por Fintual para optimización de portfolios.

    Ventajas:
    - No asume normalidad de retornos
    - Más robusto que métodos analíticos
    - Captura efectos de correlación y fat tails

    Args:
        weights: Pesos del portfolio (deben sumar 1)
        expected_returns: Retornos esperados anualizados de cada activo
        cov_matrix: Matriz de covarianza de retornos
        confidence_level: Nivel de confianza para CVaR (default 0.95)
        n_scenarios: Número de escenarios Monte Carlo
        n_periods: Horizonte de simulación en días

    Returns:
        Tuple de (cvar, simulated_returns)
        - cvar: CVaR del portfolio
        - simulated_returns: Array con todos los retornos simulados

    Example:
        >>> weights = np.array([0.6, 0.4])
        >>> expected_returns = np.array([0.08, 0.10])
        >>> cov_matrix = np.array([[0.04, 0.01], [0.01, 0.06]])
        >>> cvar, returns = calculate_portfolio_cvar_monte_carlo(
        ...     weights, expected_returns, cov_matrix
        ... )
        >>> print(f"Portfolio CVaR: {cvar:.4f}")
    """
    # Simular retornos del portfolio
    simulator = MonteCarloSimulator(n_scenarios=n_scenarios)
    simulated_returns = simulator.simulate_portfolio_returns(
        weights=weights,
        expected_returns=expected_returns,
        cov_matrix=cov_matrix,
        n_periods=n_periods
    )

    # Calcular CVaR de los retornos simulados
    cvar_calc = CVaRCalculator(confidence_level=confidence_level)
    cvar = cvar_calc.calculate_cvar(simulated_returns)

    return cvar, simulated_returns
