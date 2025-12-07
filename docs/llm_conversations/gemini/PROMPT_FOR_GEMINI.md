# Prompt para Copiar a Gemini

Copia y pega esto directamente en tu consola de Gemini:

---

Hola Gemini! Necesito tu ayuda para implementar una estrategia avanzada de rebalanceo de portfolios usando CVaR (Conditional Value-at-Risk) + Monte Carlo optimization.

## Contexto

Estoy trabajando en **Fintual Portfolio Showcase**, un sistema de rebalanceo de portfolios para postular a Software Engineer en Fintual (fintech chilena).

**Ya tengo implementado:**
- ✅ Core models (Goal, Portfolio, Asset, Position)
- ✅ CVaRCalculator y MonteCarloSimulator (app/core/metrics.py)
- ✅ SimpleRebalanceStrategy (baseline - app/core/rebalancer.py)
- ✅ FastAPI con endpoints de Goals y Rebalance
- ✅ 87 tests pasando

**Tu tarea:** Implementar `CVaRRebalanceStrategy` - una estrategia que optimiza el rebalanceo minimizando el CVaR del portfolio.

## Archivos a Revisar Primero

Por favor lee estos archivos para entender la arquitectura:

1. `app/core/metrics.py` - Especialmente:
   - `CVaRCalculator` (línea 38-123)
   - `MonteCarloSimulator` (línea 125-252)

2. `app/core/rebalancer.py` - Especialmente:
   - `RebalanceStrategy` (clase abstracta, línea 75-156)
   - `SimpleRebalanceStrategy` (implementación baseline, línea 159-389)

3. `app/core/constraints.py` - Trading constraints

4. `tests/unit/test_rebalancer.py` - Tests existentes como referencia

## Lo que Necesito que Implementes

### 1. Clase `CVaRRebalanceStrategy`

Ubicación: `app/core/rebalancer.py` (agregar al final del archivo)

```python
class CVaRRebalanceStrategy(RebalanceStrategy):
    """
    CVaR-optimized rebalancing strategy.

    Algoritmo:
    1. Estimar expected returns y cov_matrix (sintéticos para showcase)
    2. Simular N escenarios de retornos del portfolio (Monte Carlo)
    3. Optimizar weights que minimizan CVaR
    4. Generar trades para alcanzar optimal weights
    5. Aplicar constraints
    """

    def __init__(
        self,
        constraints: TradingConstraints = None,
        n_scenarios: int = 1000,
        confidence_level: float = 0.95
    ):
        # TODO: Implementar
        pass

    def rebalance(self, portfolio: Portfolio) -> RebalanceResult:
        # TODO: Implementar
        pass
```

**Métodos helper que necesitarás:**
- `_estimate_parameters()` - Genera expected_returns y cov_matrix sintéticos
- `_optimize_cvar()` - Optimiza weights para minimizar CVaR
- `_generate_trades()` - Convierte optimal weights en trades

### 2. Tests

Ubicación: `tests/unit/test_rebalancer.py` (agregar al final)

Agregar `class TestCVaRRebalanceStrategy` con al menos:
- `test_cvar_strategy_initialization()`
- `test_cvar_strategy_basic_rebalance()`
- `test_cvar_respects_constraints()`
- `test_cvar_vs_simple_comparison()` (benchmark)
- Tests de edge cases

### 3. Integración con API

Ubicación: `app/api/v1/endpoints/rebalance.py` (línea 79-87)

Cambiar el case de CVaR strategy de:
```python
elif request.strategy == RebalanceStrategyEnum.CVAR:
    raise HTTPException(status_code=501, detail="Not implemented...")
```

A:
```python
elif request.strategy == RebalanceStrategyEnum.CVAR:
    from app.core.rebalancer import CVaRRebalanceStrategy
    strategy = CVaRRebalanceStrategy(constraints=constraints)
```

## Detalles Técnicos Importantes

### Expected Returns y Covariance Matrix

Para este showcase, usa valores **sintéticos** (no integres con Yahoo Finance):

```python
def _estimate_parameters(self, portfolio):
    """Sintético para showcase."""
    n_assets = len(portfolio.positions)

    # Expected returns: 8-12% anual es razonable para stocks
    expected_returns = np.array([0.08 + 0.02*i for i in range(n_assets)])

    # Cov matrix: vol ~15%, correlación ~0.3
    vol = 0.15
    corr = 0.3
    cov_matrix = np.full((n_assets, n_assets), vol**2 * corr)
    np.fill_diagonal(cov_matrix, vol**2)

    return expected_returns, cov_matrix
```

### Optimización de CVaR

Dos enfoques posibles (elige el que prefieras):

**Opción A: scipy.optimize.minimize (más robusto)**
```python
from scipy.optimize import minimize

def objective(weights):
    # Simular retornos
    returns = self.simulator.simulate_portfolio_returns(
        weights, expected_returns, cov_matrix, n_periods=252
    )
    # Calcular CVaR
    cvar = self.cvar_calculator.calculate_cvar(returns)
    # Penalizar drift de target
    tracking_error = np.sum(np.abs(weights - target_weights))
    return cvar + risk_aversion * tracking_error

result = minimize(objective, x0=current_weights, method='SLSQP', ...)
```

**Opción B: Grid search (más simple, ok para showcase)**
```python
best_weights = target_weights
best_cvar = float('inf')

for _ in range(50):  # 50 candidatos
    # Perturbar target weights
    candidate = target_weights + np.random.normal(0, 0.05, n_assets)
    candidate = np.maximum(candidate, 0)
    candidate /= np.sum(candidate)

    # Evaluar CVaR
    returns = simulate(candidate)
    cvar = calculate_cvar(returns)

    if cvar < best_cvar:
        best_cvar = cvar
        best_weights = candidate
```

### Reutiliza Código Existente

Puedes copiar/adaptar de `SimpleRebalanceStrategy`:
- `_apply_constraints()` - Ya implementado en clase base
- `_calculate_transaction_cost()` - Ya implementado
- `_estimate_final_allocations()` - Puedes reutilizar

## Criterios de Éxito

Tu implementación es exitosa si:

1. ✅ Todos los tests pasan (87 existentes + nuevos)
2. ✅ `CVaRRebalanceStrategy` genera `RebalanceResult` válido
3. ✅ API endpoint `/rebalance/{goal_id}` funciona con `strategy=cvar`
4. ✅ Performance razonable (< 5 segundos para 10 stocks con 1000 escenarios)
5. ✅ Código bien documentado (docstrings claros)

## Restricciones

- **NO cambies** la arquitectura existente (Strategy pattern, etc)
- **NO modifiques** SimpleRebalanceStrategy (es baseline)
- **NO agregues** dependencias nuevas (scipy/cvxpy están ok)
- **NO uses** datos reales de Yahoo Finance (valores sintéticos)

## Recursos de Ayuda

He preparado dos documentos con ejemplos:

1. `docs/llm_conversations/gemini/00_GEMINI_TASK_BRIEF.md` - Especificación completa
2. `docs/llm_conversations/gemini/01_CODE_EXAMPLES.md` - Ejemplos de código

Por favor léelos para más detalles.

## Pregunta Inicial

Antes de empezar, ¿puedes confirmar que:
1. ¿Entiendes la arquitectura existente (Strategy pattern)?
2. ¿Tienes claro qué es CVaR y por qué lo usamos?
3. ¿Prefieres usar scipy.optimize o grid search para la optimización?

Una vez confirmes, empezaremos con la implementación paso a paso.

**¡Gracias por tu ayuda!** 🚀
