# Fintual Portfolio Showcase

> Sistema avanzado de rebalanceo de portfolios con CVaR Risk Metrics - Showcase técnico para Fintual

[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/downloads/)
[![Tests](https://img.shields.io/badge/tests-91%20passing-brightgreen.svg)](tests/)
[![Coverage](https://img.shields.io/badge/coverage-92%25%2B-brightgreen.svg)](tests/)
[![Code Style: Black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

## 🎯 Problema

Los inversionistas necesitan mantener sus portfolios alineados con sus objetivos de riesgo/retorno a medida que los mercados fluctúan. El rebalanceo manual es tedioso, propenso a errores, y a menudo subóptimo. Fintual necesita soluciones técnicamente sofisticadas que sean simples de usar.

## 💡 Solución

Sistema de rebalanceo de portfolios que:
- **Usa CVaR** (Conditional Value-at-Risk) como medida de riesgo principal - matemáticamente coherente vs volatilidad
- **Optimización Monte Carlo** - No asume normalidad de retornos, más robusto que métodos analíticos
- **Métricas alineadas con Fintual**: Balance, Depositado Neto, Ganado
- **Múltiples estrategias**: Simple (baseline), CVaR-optimizada con scipy.optimize, Tax-efficient (roadmap)
- **Testing riguroso**: 90%+ coverage, edge cases incluidos

## 🏗️ Arquitectura

### Stack Principal
- **Python 3.11** - Type hints, performance mejorado
- **FastAPI** - API REST moderna y rápida
- **Pydantic 2.x** - Validación de datos robusta
- **NumPy/SciPy** - Cálculos numéricos optimizados
- **cvxpy** - Optimización convexa
- **Numba** - Compilación JIT para performance crítica

### Componentes Core

```
app/
├── core/
│   ├── models.py              # Goal, Portfolio, Asset (nomenclatura Fintual)
│   ├── metrics.py             # CVaR, Monte Carlo, Sharpe/Sortino
│   ├── rebalancer.py          # Estrategias de rebalanceo
│   ├── optimizer.py           # CVaR + Monte Carlo optimization
│   └── fast_metrics.py        # XIRR optimizado con Numba
├── api/v1/
│   ├── endpoints/goals.py     # CRUD de Goals (alineado con Fintual)
│   └── schemas/               # Pydantic models
└── services/
    ├── fintual_api_service.py # Integración con API de Fintual
    └── market_data_service.py # Yahoo Finance + cache
```

## 📊 CVaR Risk Metrics

### ¿Por qué CVaR y no Volatilidad?

Fintual usa CVaR (Expected Shortfall) como medida principal de riesgo porque:
1. **Coherente matemáticamente** - Cumple propiedades deseables (subaditividad, etc)
2. **Captura tail risk** - Mide la magnitud de pérdidas extremas, no solo su probabilidad
3. **Mejor para optimización** - Problemas convexos, convergencia garantizada

### Implementación

```python
from app.core.metrics import CVaRCalculator, MonteCarloSimulator

# Calcular CVaR de un portfolio
calc = CVaRCalculator(confidence_level=0.95)
cvar = calc.calculate_cvar(returns)  # CVaR al 95%

# Simulación Monte Carlo
simulator = MonteCarloSimulator(n_scenarios=1000)
portfolio_returns = simulator.simulate_portfolio_returns(
    weights=np.array([0.6, 0.4]),
    expected_returns=np.array([0.08, 0.10]),
    cov_matrix=cov_matrix
)

# CVaR integrado con Monte Carlo (approach de Fintual)
from app.core.metrics import calculate_portfolio_cvar_monte_carlo

cvar, simulated_returns = calculate_portfolio_cvar_monte_carlo(
    weights, expected_returns, cov_matrix,
    confidence_level=0.95,
    n_scenarios=1000
)
```

## 🚀 Quick Start

### Instalación

```bash
# Clonar repositorio
git clone https://github.com/gfdiazc/fintual-portfolio-showcase.git
cd fintual-portfolio-showcase

# Instalar dependencias (usando Poetry)
poetry install

# O con pip
pip install -r requirements.txt

# Configurar variables de entorno
cp .env.example .env
```

### Ejecutar Tests

```bash
# Todos los tests
make test

# Tests unitarios con coverage
pytest tests/unit/ -v --cov=app --cov-report=html

# Solo tests de CVaR
pytest tests/unit/test_metrics.py -v

# Performance benchmarks
pytest tests/performance/ -v
```

### Uso Básico

```python
from decimal import Decimal
from app.core.models import Asset, Portfolio, Goal, AssetType, GoalType, RiskProfile

# Crear assets
aapl = Asset(
    ticker="AAPL",
    name="Apple Inc.",
    asset_type=AssetType.STOCK,
    current_price=Decimal("180.50")
)

meta = Asset(
    ticker="META",
    name="Meta Platforms",
    asset_type=AssetType.STOCK,
    current_price=Decimal("400.00")
)

# Crear portfolio
portfolio = Portfolio(id="port_001", cash=Decimal("500.00"))

portfolio.add_position(
    asset=aapl,
    shares=Decimal("10"),
    target_allocation=Decimal("0.6"),  # 60% target
    deposited=Decimal("1750.00")
)

portfolio.add_position(
    asset=meta,
    shares=Decimal("5"),
    target_allocation=Decimal("0.4"),  # 40% target
    deposited=Decimal("1950.00")
)

# Crear Goal (abstracción de Fintual)
goal = Goal(
    id="goal_001",
    name="Jubilación 2050",
    goal_type=GoalType.RETIREMENT,
    risk_profile=RiskProfile.MODERATE,
    portfolio=portfolio,
    target_amount=Decimal("100000.00")
)

# Métricas clave (alineadas con Fintual)
print(f"Balance: ${goal.balance}")              # $4,305.00
print(f"Depositado Neto: ${goal.depositado_neto}")  # $4,200.00
print(f"Ganado: ${goal.ganado}")                # $105.00 (2.5% return)
print(f"Progreso: {goal.progress_percentage}%")  # 4.31%
```

## 📈 Features Implementadas

### ✅ Phase 1: Core Models (Completado)
- `Asset`, `Position`, `Portfolio`, `Goal` con nomenclatura Fintual
- Validaciones Pydantic robustas
- Computed fields para métricas (Balance, Depositado, Ganado)
- **30 tests pasando** con edge cases

### ✅ Phase 2: CVaR Risk Metrics (Completado)
- `CVaRCalculator` - Cálculo de CVaR y VaR
- `MonteCarloSimulator` - Simulación con distribuciones normal y Student-t
- `PortfolioMetrics` - Sharpe, Sortino, Max Drawdown, Volatility
- **28 tests pasando** incluyendo validación estadística

### ✅ Phase 3: Rebalancing Strategies (Completado)
- **SimpleRebalanceStrategy** - Baseline con constraints configurables
  - Trading constraints (min_trade_value, rebalance_threshold, max_turnover)
  - Fractional shares support
  - Liquidity preservation
  - **29 tests pasando**

- **CVaRRebalanceStrategy** 🤖 *Implementado por Gemini*
  - Optimización CVaR + Monte Carlo (scipy.optimize SLSQP)
  - 1000 escenarios Monte Carlo por defecto
  - Expected returns sintéticos + covariance matrix
  - Risk aversion parameter para balancear CVaR vs tracking error
  - **4 tests pasando**

### ✅ Phase 4: FastAPI REST API (Completado)
- **10 endpoints funcionales**:
  - Goals CRUD (create, list, get, update, delete)
  - Positions management (add, update, delete)
  - Rebalancing con strategy selection
  - Health check

- **Features**:
  - Pydantic schemas con validación
  - Dependency injection (GoalService)
  - Error handling comprehensivo
  - OpenAPI/Swagger docs automático
  - Demo script funcional (`scripts/test_api.sh`)

### 📋 Roadmap (Phases 5-7)
- [ ] Fast Metrics con Numba (XIRR optimizado)
- [ ] Fintual API Adapter bidireccional
- [ ] React frontend (UX simple estilo Fintual)
- [ ] CI/CD + Performance benchmarks
- [ ] [NOTEBOOKLM] Documentación formato Shape Up

## 🧪 Testing Strategy

Alineado con el rigor de Fintual (deploy 2x/día con 90%+ coverage):

```bash
# Coverage actual
pytest tests/ --cov=app --cov-report=term-missing

# Tests por componente
pytest tests/unit/test_models.py -v      # 30 tests - Models
pytest tests/unit/test_metrics.py -v     # 28 tests - CVaR/Metrics
pytest tests/unit/test_rebalancer.py -v  # 33 tests - Rebalancing (Simple + CVaR)

# Tests específicos de estrategias
pytest tests/unit/test_rebalancer.py::TestSimpleRebalanceStrategy -v  # 29 tests
pytest tests/unit/test_rebalancer.py::TestCVaRRebalanceStrategy -v    # 4 tests

# Edge cases incluidos
pytest tests/unit/test_models.py::TestEdgeCases -v
pytest tests/unit/test_metrics.py::TestEdgeCases -v
```

### Edge Cases Testeados
- Portfolio vacío (solo cash)
- Portfolio con un solo stock
- Goal con pérdidas (ganado negativo)
- CVaR con todos retornos positivos/negativos
- Volatilidad extrema
- Division por cero en Sharpe ratio
- Validación de allocations (deben sumar ≤1.0)

## 🎨 Alineación con Fintual

### Filosofía de Producto
- ✅ **Máxima sofisticación técnica** (CVaR, Monte Carlo) → **Máxima simplicidad UX** (Balance, Depositado, Ganado)
- ✅ **Transparencia**: Documentación exhaustiva de decisiones técnicas
- ✅ **Testing riguroso**: 90%+ coverage como en producción de Fintual

### Nomenclatura
- ✅ `Goal` (user-facing) vs `Portfolio` (internal) - match con API de Fintual
- ✅ Métricas: Balance, Depositado Neto, Ganado (exactas)
- ✅ CVaR como medida de riesgo principal (no volatilidad)

### Arquitectura
- ✅ SOLID principles (Strategy pattern para rebalancing)
- ✅ Pydantic para validaciones (type-safe)
- ✅ Computed fields para métricas derivadas
- ✅ Modularización clara (core, api, services, adapters)

## 🔬 Decisiones Técnicas

### 1. CVaR vs Volatilidad
**Decisión**: Usar CVaR como medida principal de riesgo

**Razón**:
- Fintual usa CVaR en su optimización (confirmado via research)
- CVaR es matemáticamente coherente (subaditividad, monotonicidad)
- Volatilidad no diferencia entre upside/downside
- CVaR captura tail risk (crash scenarios)

**Trade-off**: CVaR requiere más cómputo (Monte Carlo), pero es más robusto

### 2. Monte Carlo vs Analítico
**Decisión**: Monte Carlo simulation para portfolio optimization

**Razón**:
- No asume normalidad de retornos (mercados tienen fat tails)
- Captura correlaciones no-lineales
- Mismo approach que Fintual
- Permite distribuciones Student-t (más realistas)

**Trade-off**: Más lento que fórmulas analíticas, pero mucho más robusto

### 3. Decimal vs Float
**Decisión**: `Decimal` para todos los valores monetarios

**Razón**:
- Precisión exacta (no errores de redondeo de floats)
- Critical para financial calculations
- Pydantic soporta validaciones

**Trade-off**: Ligeramente más lento que float, pero necesario para finanzas

### 4. Pydantic 2.x
**Decisión**: Pydantic 2.x con computed fields

**Razón**:
- Type safety + runtime validation
- Computed fields para métricas derivadas (DRY)
- JSON schema automático para API
- 5-50x más rápido que Pydantic 1.x

## 📚 Recursos y Research

### Documentación NotebookLM
- [`docs/notebook_lm_research/`](docs/notebook_lm_research/) - 6 documentos de research sobre Fintual
- Filosofía de producto, arquitectura técnica, estrategia de inversión
- Alineación competitiva y showcase strategy

### Conversaciones LLM
- [`docs/llm_conversations/`](docs/llm_conversations/) - Proceso de desarrollo documentado
- Claude Code: Arquitectura, testing, API
- Gemini: Performance optimization (próximamente)
- NotebookLM: Documentación Shape Up (próximamente)

### Plan Técnico
- [`docs/plan_*.md`](docs/) - Plan completo de arquitectura e implementación
- Decisiones de diseño, secuencia de implementación
- Checklist de completitud

## 🏆 Performance Targets

| Operación | Target | Status |
|-----------|--------|--------|
| CVaR calculation (1000 scenarios) | < 50ms | ⏳ TODO |
| XIRR optimized (100 txns) | < 10ms | ⏳ TODO |
| Rebalance (10 stocks) | < 100ms | ⏳ TODO |
| Rebalance (100 stocks) | < 1s | ⏳ TODO |
| Test coverage | 90%+ | ✅ On track |

## 🛠️ Desarrollo

### Comandos Útiles

```bash
# Instalar pre-commit hooks
pre-commit install

# Formatear código
make format

# Linting
make lint

# Type checking
mypy app/

# Benchmarks
make benchmark
```

### Estructura de Branches
- `main` - Código production-ready
- `feature/*` - Features nuevas
- `phase-*` - Branches por fase de implementación

## 📄 Licencia

MIT License - Ver [LICENSE](LICENSE) para detalles

## 👤 Autor

**Gonzalo Díaz** - Postulación Software Engineer @ Fintual

- GitHub: [@gfdiazc](https://github.com/gfdiazc)
- Email: godiazc@udd.cl

---

## 🤖 Proceso de Desarrollo con LLMs

Este proyecto fue desarrollado usando múltiples LLMs estratégicamente:

- **Claude Code**: Arquitectura, core models, SimpleRebalanceStrategy, FastAPI
- **Gemini**: CVaRRebalanceStrategy con scipy.optimize ✅ (91 tests pasando)
- **NotebookLM**: Research de Fintual, alineación estratégica ✅

### División de Trabajo

**Claude Code (Phases 1-4):**
- Core models (Goal, Portfolio, Asset) - 30 tests
- CVaR Risk Metrics (CVaRCalculator, MonteCarloSimulator) - 28 tests
- SimpleRebalanceStrategy + TradingConstraints - 29 tests
- FastAPI REST API - 10 endpoints funcionales
- Integration testing y demo scripts

**Gemini (Phase 3):**
- CVaRRebalanceStrategy con optimización scipy SLSQP
- Monte Carlo portfolio optimization (1000 scenarios)
- Refactorización: _estimate_final_allocations a base class
- Portfolio helper methods para NumPy arrays
- 4 tests comprehensivos
- **Debugging iterativo**: Resolvió 5 problemas durante implementación

**NotebookLM (Research):**
- Análisis de filosofía de producto de Fintual
- Arquitectura técnica y stack tecnológico
- Estrategia de inversión (CVaR + Monte Carlo)
- Alineación competitiva y cultura de ingeniería
- 6 documentos de research generados

Todas las conversaciones están documentadas en [`docs/llm_conversations/`](docs/llm_conversations/).

---

**Status**: Phases 1-4 completados ✅ | 91 tests pasando | Coverage: 92%+ | FastAPI funcional | CVaR Strategy implementada 🤖
