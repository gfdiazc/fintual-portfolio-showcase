// API service para comunicación con FastAPI backend

const API_BASE = '/api/v1';

// Helper para manejar responses
async function handleResponse(response) {
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }
  return response.json();
}

// Goals API
export const goalsAPI = {
  // GET /goals - Listar todos los goals
  async list() {
    const response = await fetch(`${API_BASE}/goals/`);
    return handleResponse(response);
  },

  // GET /goals/{id} - Obtener un goal específico
  async get(goalId) {
    const response = await fetch(`${API_BASE}/goals/${goalId}`);
    return handleResponse(response);
  },

  // POST /goals - Crear nuevo goal
  async create(goalData) {
    const response = await fetch(`${API_BASE}/goals/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(goalData),
    });
    return handleResponse(response);
  },

  // PUT /goals/{id} - Actualizar goal
  async update(goalId, goalData) {
    const response = await fetch(`${API_BASE}/goals/${goalId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(goalData),
    });
    return handleResponse(response);
  },

  // DELETE /goals/{id} - Eliminar goal
  async delete(goalId) {
    const response = await fetch(`${API_BASE}/goals/${goalId}`, {
      method: 'DELETE',
    });
    if (response.status === 204) {
      return { success: true };
    }
    return handleResponse(response);
  },

  // POST /goals/{id}/positions - Agregar position
  async addPosition(goalId, positionData) {
    const response = await fetch(`${API_BASE}/goals/${goalId}/positions`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(positionData),
    });
    return handleResponse(response);
  },

  // PUT /goals/{goal_id}/positions/{ticker} - Actualizar position
  async updatePosition(goalId, ticker, positionData) {
    const response = await fetch(`${API_BASE}/goals/${goalId}/positions/${ticker}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(positionData),
    });
    return handleResponse(response);
  },

  // DELETE /goals/{goal_id}/positions/{ticker} - Eliminar position
  async deletePosition(goalId, ticker) {
    const response = await fetch(`${API_BASE}/goals/${goalId}/positions/${ticker}`, {
      method: 'DELETE',
    });
    if (response.status === 204) {
      return { success: true };
    }
    return handleResponse(response);
  },
};

// Rebalance API
export const rebalanceAPI = {
  // POST /rebalance/{goal_id} - Ejecutar rebalanceo
  async execute(goalId, options = {}) {
    const {
      strategy = 'simple',
      dry_run = true,
      constraints = null,
    } = options;

    const requestBody = {
      strategy,
      dry_run,
    };

    if (constraints) {
      requestBody.constraints = constraints;
    }

    const response = await fetch(`${API_BASE}/rebalance/${goalId}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(requestBody),
    });
    return handleResponse(response);
  },
};

// Health check
export const healthAPI = {
  async check() {
    const response = await fetch('/health');
    return handleResponse(response);
  },
};

// Sample data para demo (cuando backend no está disponible)
export const sampleData = {
  goal: {
    id: 'goal_demo',
    name: 'Mi Jubilación',
    goal_type: 'retirement',
    risk_profile: 'moderate',
    balance: '15450000',
    depositado_neto: '15000000',
    ganado: '450000',
    progress_percentage: '30.9',
    target_amount: '50000000',
    portfolio: {
      id: 'port_demo',
      cash: '250000',
      total_value: '15450000',
      positions: [
        {
          ticker: 'AAPL',
          shares: '25',
          current_price: '178500',  // ~$178 USD aprox en CLP
          market_value: '4462500',
          target_allocation: '0.40',
          current_allocation: '0.293',
        },
        {
          ticker: 'META',
          shares: '15',
          current_price: '485000',  // ~$485 USD aprox en CLP
          market_value: '7275000',
          target_allocation: '0.35',
          current_allocation: '0.477',
        },
        {
          ticker: 'GOOGL',
          shares: '20',
          current_price: '145000',  // ~$145 USD aprox en CLP
          market_value: '2900000',
          target_allocation: '0.25',
          current_allocation: '0.190',
        },
      ],
    },
  },

  rebalanceResult: {
    trades: [
      {
        ticker: 'AAPL',
        action: 'BUY',
        shares: '9',
        current_price: '178500',
        value: '1606500',
        reason: 'Portfolio underweight in AAPL: actual 29.3% vs target 40% (-10.7% drift)',
      },
      {
        ticker: 'META',
        action: 'SELL',
        shares: '3',
        current_price: '485000',
        value: '1455000',
        reason: 'Portfolio overweight in META: actual 47.7% vs target 35% (+12.7% drift)',
      },
      {
        ticker: 'GOOGL',
        action: 'BUY',
        shares: '5',
        current_price: '145000',
        value: '725000',
        reason: 'Portfolio underweight in GOOGL: actual 19.0% vs target 25% (-6.0% drift)',
      },
    ],
    total_buy_value: '2331500',
    total_sell_value: '1455000',
    estimated_cost: '9466',  // 0.25% transaction cost
    final_allocations: {
      AAPL: '0.398',
      META: '0.352',
      GOOGL: '0.250',
    },
    metrics: {
      turnover_pct: '20.1',
      max_drift_before: '12.7',
      max_drift_after: '2.3',
      execution_time: '0.0002',
    },
  },
};
