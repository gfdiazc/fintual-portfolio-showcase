#!/bin/bash

# Script de prueba para la API de Fintual Portfolio Showcase
# Demuestra el flujo completo:
# 1. Crear goal
# 2. Agregar posiciones
# 3. Ejecutar rebalanceo
# 4. Ver métricas

set -e

API_BASE="http://localhost:8000/api/v1"

echo "=========================================="
echo "  FINTUAL PORTFOLIO SHOWCASE - API DEMO"
echo "=========================================="
echo ""

# 1. Crear un Goal
echo "1️⃣  Creando Goal 'Jubilación 2050'..."
GOAL_RESPONSE=$(curl -s -X POST "$API_BASE/goals/" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Jubilación 2050",
    "goal_type": "retirement",
    "risk_profile": "moderate",
    "initial_cash": 5000.00,
    "target_amount": 100000.00
  }')

GOAL_ID=$(echo $GOAL_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])")
echo "✅ Goal creado: $GOAL_ID"
echo ""

# 2. Agregar posición AAPL (underweight)
echo "2️⃣  Agregando posición AAPL (target 60%, actual ~31%)..."
curl -s -X POST "$API_BASE/goals/$GOAL_ID/positions" \
  -H "Content-Type: application/json" \
  -d '{
    "ticker": "AAPL",
    "shares": 10,
    "target_allocation": 0.60,
    "deposited": 1800.00,
    "asset": {
      "ticker": "AAPL",
      "name": "Apple Inc.",
      "asset_type": "stock",
      "current_price": 180.50,
      "currency": "USD"
    }
  }' > /dev/null
echo "✅ Posición AAPL agregada"
echo ""

# 3. Agregar posición META (overweight)
echo "3️⃣  Agregando posición META (target 40%, actual ~69%)..."
curl -s -X POST "$API_BASE/goals/$GOAL_ID/positions" \
  -H "Content-Type: application/json" \
  -d '{
    "ticker": "META",
    "shares": 10,
    "target_allocation": 0.40,
    "deposited": 4000.00,
    "asset": {
      "ticker": "META",
      "name": "Meta Platforms Inc.",
      "asset_type": "stock",
      "current_price": 400.00,
      "currency": "USD"
    }
  }' > /dev/null
echo "✅ Posición META agregada"
echo ""

# 4. Ver estado del Goal
echo "4️⃣  Estado actual del Goal..."
GOAL_STATUS=$(curl -s "$API_BASE/goals/$GOAL_ID")
echo "Balance: \$$(echo $GOAL_STATUS | python3 -c "import sys, json; print(json.load(sys.stdin)['balance'])")"
echo "Depositado: \$$(echo $GOAL_STATUS | python3 -c "import sys, json; print(json.load(sys.stdin)['depositado_neto'])")"
echo "Ganado: \$$(echo $GOAL_STATUS | python3 -c "import sys, json; print(json.load(sys.stdin)['ganado'])")"
echo ""

# 5. Ejecutar rebalanceo (dry run)
echo "5️⃣  Ejecutando rebalanceo (dry run)..."
REBALANCE_RESPONSE=$(curl -s -X POST "$API_BASE/rebalance/$GOAL_ID" \
  -H "Content-Type: application/json" \
  -d '{
    "strategy": "simple",
    "dry_run": true
  }')

echo "📊 Resultado del rebalanceo:"
echo "$REBALANCE_RESPONSE" | python3 -c "
import sys, json
data = json.load(sys.stdin)
print('  • Total trades:', data['total_trades'])
print('  • Compras: \$' + str(data['total_buy_value']))
print('  • Ventas: \$' + str(data['total_sell_value']))
print('  • Costo estimado: \$' + str(data['estimated_cost']))
print('  • Turnover: {:.2f}%'.format(data['turnover_pct']))
print('  • Max drift before: {:.2f}%'.format(data['max_drift_before']*100))
if data['trades']:
    print('\n  Trades a ejecutar:')
    for trade in data['trades']:
        print('    {} {} {} @ \${} = \${:.2f}'.format(
            trade['action'], str(trade['shares']), trade['ticker'],
            trade['current_price'], float(trade['value'])
        ))
        print('         Razón:', trade['reason'])
"
echo ""

# 6. Listar todos los goals
echo "6️⃣  Listando todos los goals..."
GOALS_LIST=$(curl -s "$API_BASE/goals/")
echo "Total goals: $(echo $GOALS_LIST | python3 -c "import sys, json; print(json.load(sys.stdin)['total'])")"
echo ""

echo "=========================================="
echo "✅ Demo completado!"
echo "=========================================="
echo ""
echo "📖 Ver Swagger docs: http://localhost:8000/docs"
echo "📖 Ver ReDoc: http://localhost:8000/redoc"
echo ""
