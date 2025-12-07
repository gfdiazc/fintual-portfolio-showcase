# Gemini Task: CVaR-Optimized Rebalancing Strategy

## 📋 Contexto del Proyecto

Estás trabajando en **Fintual Portfolio Showcase**, un sistema avanzado de rebalanceo de portfolios para postulación a Software Engineer en Fintual.

**Ya implementado por Claude Code:**
- ✅ Core models (Goal, Portfolio, Asset, Position)
- ✅ CVaR Risk Metrics con Monte Carlo sampling
- ✅ SimpleRebalanceStrategy (baseline algorithm)
- ✅ FastAPI con Goals y Rebalance endpoints
- ✅ 87 tests pasando

**Tu tarea:** Implementar `CVaRRebalanceStrategy` - optimización avanzada de rebalanceo usando CVaR + Monte Carlo.

---

## 🎯 Objetivo de la Tarea

Implementar una estrategia de rebalanceo que **minimiza el CVaR del portfolio** (riesgo de pérdidas extremas) mientras alcanza las target allocations.

### ¿Por qué CVaR?

Fintual usa CVaR (Conditional Value-at-Risk) como medida principal de riesgo porque:
1. **Coherente matemáticamente** - Cumple propiedades deseables (subaditividad, monotonicidad)
2. **Captura tail risk** - Mide magnitud de pérdidas extremas, no solo probabilidad
3. **Mejor para optimización** - Problemas convexos vs no-convexos con VaR

**Referencia de Fintual:** Según research (docs/notebook_lm_research/02_technical_architecture.md), Fintual usa CVaR + Monte Carlo para optimización de portfolios.

---

## 📂 Archivos Relevantes

### Para leer y entender:

1. **`app/core/metrics.py`** (líneas 38-123)
   - `CVaRCalculator` - Ya implementado
   - `calculate_cvar(returns)` - Calcula CVaR de una serie de retornos
   - `MonteCarloSimulator` - Ya implementado
   - `simulate_portfolio_returns()` - Simula escenarios de portfolio

2. **`app/core/rebalancer.py`** (líneas 75-389)
   - `RebalanceStrategy` - Clase abstracta base
   - `SimpleRebalanceStrategy` - Baseline para comparar
   - `Trade`, `RebalanceResult` - Modelos de datos
   - Métodos helper: `_calculate_drift()`, `_apply_constraints()`, `_calculate_transaction_cost()`

3. **`app/core/constraints.py`**
   - `TradingConstraints` - Constraints configurables
   - `ConservativeConstraints`, `ModerateConstraints`, `RiskyConstraints`

4. **`tests/unit/test_rebalancer.py`** (líneas 200-440)
   - Tests de SimpleRebalanceStrategy
   - Edge cases a cubrir
   - Fixtures disponibles en `tests/conftest.py`

### Para modificar:

1. **`app/core/rebalancer.py`**
   - Agregar clase `CVaRRebalanceStrategy(RebalanceStrategy)`

2. **`tests/unit/test_rebalancer.py`**
   - Agregar `TestCVaRRebalanceStrategy` class con tests

3. **`app/api/v1/endpoints/rebalance.py`** (línea 79-87)
   - Descomentar/implementar el case de CVaR strategy

---

## 🔬 Especificación Técnica

### Clase a Implementar

```python
class CVaRRebalanceStrategy(RebalanceStrategy):
    """
    Estrategia de rebalanceo optimizada con CVaR + Monte Carlo.

    Algoritmo:
    1. Simular N escenarios de retornos futuros (Monte Carlo)
    2. Para cada escenario, calcular retorno del portfolio
    3. Calcular CVaR de la distribución de retornos
    4. Optimizar trades para minimizar CVaR
       sujeto a:
       - Alcanzar target allocations (o cerca)
       - Respetar constraints (min_trade_value, max_turnover, min_liquidity)
       - Minimizar costos de transacción

    Ventajas vs SimpleRebalanceStrategy:
    - Considera riesgo (CVaR) no solo drift
    - Optimiza trade-off entre alcanzar target y minimizar riesgo
    - Más robusto en mercados volátiles
    """

    def __init__(
        self,
        constraints: TradingConstraints = None,
        n_scenarios: int = 1000,
        confidence_level: float = 0.95
    ):
        super().__init__(constraints)
        self.n_scenarios = n_scenarios
        self.confidence_level = confidence_level
        self.simulator = MonteCarloSimulator(n_scenarios=n_scenarios)
        self.cvar_calculator = CVaRCalculator(confidence_level=confidence_level)

    def rebalance(self, portfolio: Portfolio) -> RebalanceResult:
        """
        Rebalancear usando optimización CVaR.

        Steps:
        1. Estimar expected returns y cov_matrix de assets
        2. Simular escenarios de retornos con Monte Carlo
        3. Optimizar weights que minimizan CVaR
        4. Generar trades para alcanzar optimal weights
        5. Aplicar constraints
        6. Retornar resultado
        """
        # TODO: Implementar
        pass
```

### Función de Optimización

El problema de optimización es:

```
minimize: CVaR_α(portfolio_returns)

subject to:
- sum(weights) = 1
- weights >= 0  (no short selling)
- weights <= max_position_size (si está definido)
- |weight - target| <= tracking_error_tolerance
- transaction_costs <= max_cost
```

**Herramientas sugeridas:**
- `scipy.optimize.minimize` - Para optimización
- O `cvxpy` si quieres formularlo como problema convexo

**Nota importante:** No necesitas implementar el optimizador CVaR desde cero. Puedes:
1. Simular retornos del portfolio para diferentes sets de weights
2. Calcular CVaR de cada distribución de retornos
3. Usar optimizer para encontrar weights que minimizan CVaR

---

## 🧪 Tests Requeridos

Agregar en `tests/unit/test_rebalancer.py`:

```python
class TestCVaRRebalanceStrategy:
    """Tests para CVaR-optimized rebalancing."""

    def test_cvar_strategy_initialization(self):
        """Test creación de CVaR strategy."""
        # Verificar que se inicializa con n_scenarios y confidence_level

    def test_cvar_reduces_tail_risk(self, sample_portfolio_balanced):
        """Test que CVaR strategy reduce riesgo vs Simple strategy."""
        # Comparar CVaR del resultado vs baseline

    def test_cvar_respects_constraints(self, sample_portfolio_balanced):
        """Test que respeta constraints."""
        # Verificar min_liquidity, max_turnover, etc

    def test_cvar_with_different_scenarios(self):
        """Test con diferentes números de escenarios."""
        # Verificar que más escenarios = más estable

    def test_cvar_vs_simple_comparison(self, sample_portfolio_balanced):
        """Benchmark: CVaR vs Simple strategy."""
        # Generar reporte comparativo
```

**Mínimo:** 5-8 tests que cubran casos principales y edge cases.

---

## 📊 Expected Returns y Covariance Matrix

Para simular retornos futuros, necesitas estimar:

1. **Expected returns** de cada asset
   - **Simplificación para showcase:** Puedes usar retornos históricos asumidos
   - Ejemplo: AAPL = 8% anual, META = 10% anual
   - O usar un simple momentum: `expected_return = mean(last_N_returns)`

2. **Covariance matrix** entre assets
   - **Simplificación:** Puedes asumir una cov_matrix sintética
   - O calcular de retornos históricos si tienes data

**Recomendación:** Para este showcase, usa valores sintéticos razonables. No necesitas integrar con Yahoo Finance aún.

Ejemplo:
```python
def _estimate_parameters(self, portfolio: Portfolio):
    """Estimar expected returns y cov matrix (sintético para showcase)."""
    tickers = list(portfolio.positions.keys())
    n_assets = len(tickers)

    # Expected returns sintéticos (8-10% anual es razonable para stocks)
    expected_returns = np.array([0.08 + 0.02 * i for i in range(n_assets)])

    # Cov matrix sintética (vol ~15-20%, correlación ~0.3)
    vol = 0.15
    corr = 0.3
    cov_matrix = np.full((n_assets, n_assets), vol**2 * corr)
    np.fill_diagonal(cov_matrix, vol**2)

    return expected_returns, cov_matrix
```

---

## ⚡ Performance Targets

**Objetivo de performance:**
- Rebalanceo de 10 stocks: < 2 segundos
- Rebalanceo de 50 stocks: < 10 segundos
- 1000 escenarios Monte Carlo es razonable

Si es muy lento:
- Reduce n_scenarios a 500
- O usa NumPy vectorization más agresiva
- O considera usar Numba JIT (bonus!)

**Benchmark vs SimpleRebalanceStrategy:**
Debe ser más lento (por Monte Carlo) pero no >10x más lento.

---

## 🎯 Criterios de Éxito

**Mínimo viable:**
1. ✅ Clase `CVaRRebalanceStrategy` implementada
2. ✅ Hereda de `RebalanceStrategy` correctamente
3. ✅ Método `rebalance()` retorna `RebalanceResult` válido
4. ✅ Genera trades que reducen drift
5. ✅ Al menos 5 tests pasando
6. ✅ No rompe tests existentes (87 tests siguen pasando)

**Deseable:**
7. ✅ CVaR del resultado es menor que SimpleRebalanceStrategy
8. ✅ Respeta constraints (min_liquidity, max_turnover)
9. ✅ Performance razonable (< 2s para 10 stocks)
10. ✅ Documentación clara en docstrings
11. ✅ Integrado con API (endpoint funcional)

**Bonus (si tienes tiempo):**
- Benchmark detallado vs SimpleRebalanceStrategy
- Gráficos comparativos (CVaR, turnover, costos)
- Configuración de risk_aversion parameter
- Tests de convergencia del optimizer

---

## 🚫 Lo que NO debes hacer

1. **No cambies** la arquitectura existente (Strategy pattern, etc)
2. **No modifiques** `SimpleRebalanceStrategy` (es baseline para comparar)
3. **No rompas** tests existentes
4. **No agregues** dependencias nuevas sin justificación (scipy/cvxpy están ok)
5. **No implementes** conexión con Yahoo Finance (usa datos sintéticos)
6. **No te preocupes** por tax-loss harvesting (eso es otra estrategia)

---

## 📖 Contexto de Fintual

### Filosofía de Optimización de Fintual

Según research (docs/notebook_lm_research/02_technical_architecture.md):

1. **Dos métodos de optimización:**
   - Markowitz + Monte Carlo sampling
   - CVaR + Monte Carlo (problema lineal de gran tamaño)

2. **No predicen mercado:**
   - Inversión pasiva, indexada
   - No market timing
   - No selección activa de acciones

3. **CVaR como medida de riesgo:**
   - Superior a volatilidad
   - Captura tail risk
   - Matemáticamente coherente

4. **IA en optimización:**
   - +2% retorno anual en 2024
   - Optimización de composición de portfolios

**Tu implementación debe alinearse con esta filosofía.**

---

## 🛠️ Recursos Disponibles

### Código existente que puedes reutilizar:

1. `CVaRCalculator.calculate_cvar(returns)` - Calcula CVaR
2. `MonteCarloSimulator.simulate_portfolio_returns()` - Simula escenarios
3. `SimpleRebalanceStrategy._apply_constraints()` - Aplica constraints
4. `SimpleRebalanceStrategy._calculate_transaction_cost()` - Calcula costos

### Tests helpers:

- `tests/conftest.py` - Fixtures: `sample_portfolio_balanced`, `sample_asset_aapl`, etc
- `tests/unit/test_metrics.py` - Tests de CVaR y Monte Carlo (para referencia)

### Referencias académicas (si necesitas):

- Rockafellar & Uryasev (2000): "Optimization of CVaR"
- Markowitz Modern Portfolio Theory
- Fintual blog posts sobre CVaR

---

## 📝 Entregables

1. **Código:**
   - `app/core/rebalancer.py` - Clase `CVaRRebalanceStrategy`
   - `tests/unit/test_rebalancer.py` - Tests de CVaR strategy
   - `app/api/v1/endpoints/rebalance.py` - Integración con API

2. **Documentación:**
   - Docstrings claros en la clase y métodos
   - Comentarios explicando decisiones de optimización
   - `docs/llm_conversations/gemini/01_cvar_implementation.md` - Conversación documentada

3. **Validación:**
   - Todos los tests pasando (87 + nuevos)
   - Benchmark vs SimpleRebalanceStrategy
   - API endpoint funcional

---

## 🚀 Cómo Empezar

### Paso 1: Entender el código existente
```bash
# Leer implementación de CVaR
cat app/core/metrics.py | grep -A 50 "class CVaRCalculator"

# Leer SimpleRebalanceStrategy
cat app/core/rebalancer.py | grep -A 200 "class SimpleRebalanceStrategy"

# Ver tests existentes
cat tests/unit/test_rebalancer.py | grep -A 30 "class TestSimpleRebalanceStrategy"
```

### Paso 2: Implementar versión simple
Empieza con un algoritmo simple que:
1. Usa SimpleRebalanceStrategy para generar trades iniciales
2. Simula retornos del portfolio resultante
3. Calcula CVaR
4. Retorna resultado

### Paso 3: Agregar optimización
Una vez que lo básico funciona:
1. Implementa loop de optimización
2. Prueba diferentes sets de weights
3. Elige el que minimiza CVaR

### Paso 4: Tests y refinamiento
1. Agregar tests
2. Benchmarking
3. Optimizar performance si es necesario

---

## ❓ Preguntas Frecuentes

**Q: ¿Debo usar cvxpy o scipy.optimize?**
A: Cualquiera está bien. cvxpy es más declarativo, scipy.optimize más flexible. Usa el que prefieras.

**Q: ¿Cómo obtengo expected returns y cov_matrix?**
A: Para showcase, usa valores sintéticos razonables (ejemplo arriba). No integres con Yahoo Finance aún.

**Q: ¿Cuántos escenarios Monte Carlo debo usar?**
A: Empieza con 1000. Si es muy lento, reduce a 500. Si es muy rápido, sube a 5000.

**Q: ¿El optimizer debe ser global o local?**
A: Local está bien (scipy SLSQP). Global (scipy differential_evolution) es bonus.

**Q: ¿Qué pasa si el optimizer no converge?**
A: Fallback a SimpleRebalanceStrategy y loggear warning.

**Q: ¿Debo implementar todos los bonus?**
A: No. Enfócate en mínimo viable primero. Bonus solo si tienes tiempo.

---

## 🎯 Métrica de Éxito Final

**Tu implementación es exitosa si:**

```python
# Test de aceptación
def test_acceptance_cvar_strategy():
    """Test de aceptación final."""
    portfolio = create_sample_portfolio()  # Con drift significativo

    simple_strategy = SimpleRebalanceStrategy()
    cvar_strategy = CVaRRebalanceStrategy(n_scenarios=1000)

    simple_result = simple_strategy.rebalance(portfolio)
    cvar_result = cvar_strategy.rebalance(portfolio)

    # 1. Ambos generan trades válidos
    assert len(simple_result.trades) > 0
    assert len(cvar_result.trades) > 0

    # 2. CVaR strategy reduce riesgo (CVaR menor o igual)
    # (Simular retornos post-rebalance y comparar CVaR)
    simple_cvar = simulate_and_calculate_cvar(simple_result)
    optimized_cvar = simulate_and_calculate_cvar(cvar_result)
    assert optimized_cvar <= simple_cvar * 1.1  # Max 10% peor

    # 3. Performance razonable
    assert cvar_result.execution_time < 5.0  # < 5 segundos

    # 4. Respeta constraints
    assert cvar_result.respects_constraints()
```

Si este test pasa, la implementación es exitosa. 🎉

---

## 🤝 Soporte

Si tienes dudas durante la implementación:
1. Revisa el código existente (especialmente CVaRCalculator y MonteCarloSimulator)
2. Mira tests de SimpleRebalanceStrategy como referencia
3. Usa print() / logging para debugging
4. Documenta tus decisiones en docstrings

**Recuerda:** No necesitas perfección. Necesitas una implementación funcional que demuestre comprensión de CVaR optimization.

---

## ✅ Checklist Final

Antes de considerar la tarea completa:

- [ ] `CVaRRebalanceStrategy` class implementada
- [ ] Método `rebalance()` funcional
- [ ] Al menos 5 tests pasando
- [ ] Tests existentes no rotos (87 siguen pasando)
- [ ] Integrado con API endpoint
- [ ] Documentación en docstrings
- [ ] Benchmark vs SimpleRebalanceStrategy
- [ ] Conversación documentada en `docs/llm_conversations/gemini/`

---

**¡Buena suerte con la implementación! 🚀**

Si tienes preguntas, documéntalas en tu conversación para transparencia con Fintual.
