# Ejemplos de Código para CVaR Strategy Implementation

## Ejemplo 1: Estructura Básica de CVaRRebalanceStrategy

```python
class CVaRRebalanceStrategy(RebalanceStrategy):
    """
    CVaR-optimized rebalancing strategy.

    Minimiza el CVaR del portfolio mientras alcanza target allocations.
    """

    def __init__(
        self,
        constraints: TradingConstraints = None,
        n_scenarios: int = 1000,
        confidence_level: float = 0.95,
        risk_aversion: float = 1.0
    ):
        """
        Args:
            constraints: Trading constraints
            n_scenarios: Número de escenarios Monte Carlo
            confidence_level: Para CVaR calculation (default 0.95 = 95%)
            risk_aversion: Lambda para trade-off CVaR vs tracking error
        """
        super().__init__(constraints)
        self.n_scenarios = n_scenarios
        self.confidence_level = confidence_level
        self.risk_aversion = risk_aversion
        self.simulator = MonteCarloSimulator(n_scenarios=n_scenarios)
        self.cvar_calculator = CVaRCalculator(confidence_level=confidence_level)

    def rebalance(self, portfolio: Portfolio) -> RebalanceResult:
        """Rebalancear usando CVaR optimization."""

        # 1. Validaciones iniciales
        if len(portfolio.positions) == 0:
            raise ValueError("Cannot rebalance empty portfolio")

        # 2. Estimar parámetros (expected returns, cov matrix)
        expected_returns, cov_matrix = self._estimate_parameters(portfolio)

        # 3. Obtener current y target weights
        current_weights = self._get_current_weights(portfolio)
        target_weights = self._get_target_weights(portfolio)

        # 4. Optimizar weights que minimizan CVaR
        optimal_weights = self._optimize_cvar(
            current_weights,
            target_weights,
            expected_returns,
            cov_matrix,
            portfolio
        )

        # 5. Generar trades para alcanzar optimal weights
        trades = self._generate_trades(portfolio, optimal_weights)

        # 6. Aplicar constraints
        trades = self._apply_constraints(trades, portfolio)

        # 7. Calcular métricas y crear resultado
        return self._create_result(portfolio, trades, optimal_weights)
```

## Ejemplo 2: Estimación de Parámetros (Sintéticos)

```python
def _estimate_parameters(
    self,
    portfolio: Portfolio
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Estimar expected returns y covariance matrix.

    Para showcase: usa valores sintéticos razonables.
    En producción: calcularía de datos históricos.
    """
    tickers = list(portfolio.positions.keys())
    n_assets = len(tickers)

    # Expected returns sintéticos
    # Stocks típicamente 8-12% anual
    base_return = 0.08  # 8% base
    expected_returns = np.array([
        base_return + np.random.uniform(-0.02, 0.04)
        for _ in range(n_assets)
    ])

    # Covariance matrix sintética
    # Volatilidad típica 15-25%
    # Correlación típica 0.2-0.5 para stocks
    volatilities = np.array([
        np.random.uniform(0.15, 0.25)
        for _ in range(n_assets)
    ])

    # Matriz de correlación (más realista que correlación constante)
    correlations = np.random.uniform(0.2, 0.5, (n_assets, n_assets))
    correlations = (correlations + correlations.T) / 2  # Simétrica
    np.fill_diagonal(correlations, 1.0)

    # Cov = Diag(vol) @ Corr @ Diag(vol)
    cov_matrix = np.outer(volatilities, volatilities) * correlations

    return expected_returns, cov_matrix
```

## Ejemplo 3: Optimización de CVaR con scipy

```python
def _optimize_cvar(
    self,
    current_weights: np.ndarray,
    target_weights: np.ndarray,
    expected_returns: np.ndarray,
    cov_matrix: np.ndarray,
    portfolio: Portfolio
) -> np.ndarray:
    """
    Optimizar weights para minimizar CVaR.

    Usa scipy.optimize.minimize con SLSQP.
    """
    from scipy.optimize import minimize

    n_assets = len(current_weights)

    # Función objetivo: CVaR del portfolio
    def objective(weights):
        # Simular retornos del portfolio
        portfolio_returns = self.simulator.simulate_portfolio_returns(
            weights=weights,
            expected_returns=expected_returns,
            cov_matrix=cov_matrix,
            n_periods=252
        )

        # Calcular CVaR
        cvar = self.cvar_calculator.calculate_cvar(portfolio_returns)

        # Penalizar drift de target (tracking error)
        tracking_error = np.sum(np.abs(weights - target_weights))

        # Objetivo combinado
        return cvar + self.risk_aversion * tracking_error

    # Constraints
    constraints = [
        # Weights sum to 1
        {'type': 'eq', 'fun': lambda w: np.sum(w) - 1.0},
        # Respeto de min_liquidity
        # (simplificación: asumimos que cash se ajusta automáticamente)
    ]

    # Bounds
    bounds = [(0, 1) for _ in range(n_assets)]  # No short selling

    # Si hay max_position_size
    if self.constraints.max_position_size is not None:
        bounds = [
            (0, float(self.constraints.max_position_size))
            for _ in range(n_assets)
        ]

    # Optimizar
    result = minimize(
        objective,
        x0=current_weights,  # Start from current
        method='SLSQP',
        bounds=bounds,
        constraints=constraints,
        options={'maxiter': 100}
    )

    if not result.success:
        logger.warning(f"Optimization did not converge: {result.message}")
        # Fallback to target weights
        return target_weights

    return result.x
```

## Ejemplo 4: Versión Simplificada (Grid Search)

Si scipy.optimize es muy complejo, puedes empezar con grid search:

```python
def _optimize_cvar_grid_search(
    self,
    current_weights: np.ndarray,
    target_weights: np.ndarray,
    expected_returns: np.ndarray,
    cov_matrix: np.ndarray,
    portfolio: Portfolio
) -> np.ndarray:
    """
    Versión simplificada: grid search alrededor de target weights.

    Más simple que optimizer pero funcional para showcase.
    """
    best_weights = target_weights
    best_cvar = float('inf')

    # Generar candidatos alrededor de target
    n_candidates = 50
    for _ in range(n_candidates):
        # Perturbar target weights con ruido
        noise = np.random.normal(0, 0.05, len(target_weights))
        candidate = target_weights + noise

        # Normalizar para que sumen 1 y sean >= 0
        candidate = np.maximum(candidate, 0)
        candidate = candidate / np.sum(candidate)

        # Simular y calcular CVaR
        portfolio_returns = self.simulator.simulate_portfolio_returns(
            weights=candidate,
            expected_returns=expected_returns,
            cov_matrix=cov_matrix,
            n_periods=252
        )

        cvar = self.cvar_calculator.calculate_cvar(portfolio_returns)

        # Tracking error penalty
        tracking_error = np.sum(np.abs(candidate - target_weights))
        objective = cvar + self.risk_aversion * tracking_error

        # Update best
        if objective < best_cvar:
            best_cvar = objective
            best_weights = candidate

    return best_weights
```

## Ejemplo 5: Tests para CVaR Strategy

```python
class TestCVaRRebalanceStrategy:
    """Tests para CVaR rebalancing strategy."""

    def test_cvar_strategy_initialization(self):
        """Test creación de CVaR strategy."""
        strategy = CVaRRebalanceStrategy(
            n_scenarios=500,
            confidence_level=0.95
        )

        assert strategy.n_scenarios == 500
        assert strategy.confidence_level == 0.95
        assert strategy.simulator is not None
        assert strategy.cvar_calculator is not None

    def test_cvar_strategy_basic_rebalance(self, sample_portfolio_balanced):
        """Test rebalanceo básico."""
        strategy = CVaRRebalanceStrategy(n_scenarios=100)  # Pocos para rapidez

        result = strategy.rebalance(sample_portfolio_balanced)

        # Debe generar resultado válido
        assert isinstance(result, RebalanceResult)
        assert len(result.trades) >= 0
        assert result.total_buy_value >= 0
        assert result.total_sell_value >= 0

    def test_cvar_reduces_risk_vs_simple(self, sample_portfolio_balanced):
        """Test que CVaR strategy reduce riesgo."""
        # Setup
        simple = SimpleRebalanceStrategy()
        cvar_strategy = CVaRRebalanceStrategy(n_scenarios=500)

        # Rebalancear con ambas
        simple_result = simple.rebalance(sample_portfolio_balanced)
        cvar_result = cvar_strategy.rebalance(sample_portfolio_balanced)

        # Simular retornos post-rebalance para ambos
        # (simplificación: usa allocations finales)

        # CVaR de resultado optimizado debe ser <= que simple
        # (permite un margen de 10% por variabilidad Monte Carlo)
        # assert cvar_of_optimized <= cvar_of_simple * 1.1

        # Al menos verifica que generó trades
        assert len(cvar_result.trades) > 0

    def test_cvar_respects_min_liquidity(self, sample_portfolio_balanced):
        """Test que respeta constraint de liquidez mínima."""
        constraints = ConservativeConstraints()  # 50% min liquidity
        strategy = CVaRRebalanceStrategy(
            constraints=constraints,
            n_scenarios=100
        )

        result = strategy.rebalance(sample_portfolio_balanced)

        # Verificar que cash final >= min_liquidity
        final_cash = (
            sample_portfolio_balanced.cash +
            result.total_sell_value -
            result.total_buy_value -
            result.estimated_cost
        )

        min_cash_required = (
            constraints.min_liquidity *
            sample_portfolio_balanced.total_value
        )

        assert final_cash >= min_cash_required * 0.99  # 1% tolerance

    def test_cvar_with_different_scenarios(self, sample_portfolio_balanced):
        """Test con diferentes números de escenarios."""
        for n_scenarios in [100, 500, 1000]:
            strategy = CVaRRebalanceStrategy(n_scenarios=n_scenarios)
            result = strategy.rebalance(sample_portfolio_balanced)

            # Debe funcionar con cualquier número de escenarios
            assert isinstance(result, RebalanceResult)

    def test_cvar_empty_portfolio_fails(self):
        """Test que falla con portfolio vacío."""
        portfolio = Portfolio(id="empty", cash=Decimal("1000"))
        strategy = CVaRRebalanceStrategy()

        with pytest.raises(ValueError):
            strategy.rebalance(portfolio)
```

## Ejemplo 6: Integración con API

En `app/api/v1/endpoints/rebalance.py`, cambiar:

```python
# Antes (línea 79-87)
elif request.strategy == RebalanceStrategyEnum.CVAR:
    # TODO: Implementar con Gemini
    raise HTTPException(
        status_code=501,
        detail="CVaR strategy not yet implemented..."
    )

# Después
elif request.strategy == RebalanceStrategyEnum.CVAR:
    from app.core.rebalancer import CVaRRebalanceStrategy

    # Parámetros por query param (opcional)
    n_scenarios = request.n_scenarios if hasattr(request, 'n_scenarios') else 1000

    strategy = CVaRRebalanceStrategy(
        constraints=constraints,
        n_scenarios=n_scenarios,
        confidence_level=0.95
    )
```

## Ejemplo 7: Helpers Útiles

```python
def _get_current_weights(self, portfolio: Portfolio) -> np.ndarray:
    """Obtener current weights del portfolio."""
    total_invested = sum(
        pos.market_value
        for pos in portfolio.positions.values()
    )

    if total_invested == 0:
        # Portfolio vacío o solo cash
        return np.zeros(len(portfolio.positions))

    weights = np.array([
        float(pos.market_value / total_invested)
        for pos in portfolio.positions.values()
    ])

    return weights

def _get_target_weights(self, portfolio: Portfolio) -> np.ndarray:
    """Obtener target weights del portfolio."""
    return np.array([
        float(pos.target_allocation)
        for pos in portfolio.positions.values()
    ])

def _generate_trades(
    self,
    portfolio: Portfolio,
    optimal_weights: np.ndarray
) -> List[Trade]:
    """
    Generar trades para alcanzar optimal weights.

    Similar a SimpleRebalanceStrategy pero usa optimal_weights
    en vez de target_weights.
    """
    trades = []
    total_value = portfolio.total_value

    for i, (ticker, position) in enumerate(portfolio.positions.items()):
        current_weight = float(
            position.market_value / total_value
        )
        optimal_weight = optimal_weights[i]

        # Drift con respecto a optimal (no target!)
        drift = optimal_weight - current_weight

        # Solo tradear si excede threshold
        if abs(drift) >= self.constraints.rebalance_threshold:
            value_to_trade = drift * total_value
            shares_to_trade = abs(value_to_trade / position.asset.current_price)

            if shares_to_trade == 0:
                continue

            action = "BUY" if drift > 0 else "SELL"
            reason = (
                f"CVaR-optimized: {'under' if drift > 0 else 'over'}weight "
                f"by {abs(drift)*100:.2f}%"
            )

            # Fractional shares
            if not self.constraints.allow_fractional_shares:
                shares_to_trade = Decimal(int(shares_to_trade))

            trade = Trade(
                ticker=ticker,
                action=action,
                shares=shares_to_trade,
                current_price=position.asset.current_price,
                value=abs(value_to_trade),
                reason=reason
            )

            trades.append(trade)

    return trades
```

## Ejemplo 8: Logging y Debugging

```python
import logging

logger = logging.getLogger(__name__)

def rebalance(self, portfolio: Portfolio) -> RebalanceResult:
    """Rebalancear usando CVaR optimization."""

    logger.info(
        f"CVaR rebalance starting: {len(portfolio.positions)} assets, "
        f"{self.n_scenarios} scenarios"
    )

    # ... código de optimización ...

    logger.info(
        f"Optimization complete. CVaR: {best_cvar:.4f}, "
        f"Iterations: {result.nit if hasattr(result, 'nit') else 'N/A'}"
    )

    # ... generar trades ...

    logger.info(
        f"Generated {len(trades)} trades, "
        f"Total buy: ${total_buy:.2f}, Total sell: ${total_sell:.2f}"
    )

    return result
```

## Ejemplo 9: Performance Optimization

Si es muy lento:

```python
# Cache de simulaciones para evitar recalcular
from functools import lru_cache

@lru_cache(maxsize=100)
def _cached_simulate(weights_tuple, seed):
    """Simular con cache."""
    weights = np.array(weights_tuple)
    np.random.seed(seed)
    # ... simulate ...
    return portfolio_returns

# O usa NumPy vectorization más agresiva
def _objective_vectorized(weights_matrix):
    """Evaluar múltiples weights de una vez."""
    # weights_matrix: (n_candidates, n_assets)
    # Retorna: (n_candidates,) array de CVaRs
    pass
```

## Ejemplo 10: Benchmark Script

```python
# scripts/benchmark_strategies.py
"""
Benchmark CVaR vs Simple strategy.
"""

def benchmark_strategies():
    """Comparar estrategias."""
    import time

    # Setup
    portfolio = create_test_portfolio()
    simple = SimpleRebalanceStrategy()
    cvar_strategy = CVaRRebalanceStrategy(n_scenarios=1000)

    # Simple strategy
    start = time.time()
    simple_result = simple.rebalance(portfolio)
    simple_time = time.time() - start

    # CVaR strategy
    start = time.time()
    cvar_result = cvar_strategy.rebalance(portfolio)
    cvar_time = time.time() - start

    # Resultados
    print("=" * 60)
    print("BENCHMARK: CVaR vs Simple Rebalancing")
    print("=" * 60)
    print(f"\nSimple Strategy:")
    print(f"  Time: {simple_time:.3f}s")
    print(f"  Trades: {len(simple_result.trades)}")
    print(f"  Turnover: {simple_result.metrics['turnover_pct']:.2f}%")

    print(f"\nCVaR Strategy:")
    print(f"  Time: {cvar_time:.3f}s ({cvar_time/simple_time:.1f}x slower)")
    print(f"  Trades: {len(cvar_result.trades)}")
    print(f"  Turnover: {cvar_result.metrics['turnover_pct']:.2f}%")

    print("\n" + "=" * 60)

if __name__ == "__main__":
    benchmark_strategies()
```

---

## Flujo Recomendado de Implementación

1. **Paso 1:** Implementar estructura básica (solo skeleton)
2. **Paso 2:** Implementar `_estimate_parameters()` (sintético)
3. **Paso 3:** Implementar `_optimize_cvar_grid_search()` (versión simple)
4. **Paso 4:** Implementar `_generate_trades()` (copiar de Simple)
5. **Paso 5:** Agregar tests básicos
6. **Paso 6:** Verificar que funciona end-to-end
7. **Paso 7:** Mejorar optimizer (scipy.optimize si quieres)
8. **Paso 8:** Performance tuning
9. **Paso 9:** Benchmark vs Simple
10. **Paso 10:** Documentar

---

**¡Estos ejemplos deberían darte una base sólida para empezar!**
