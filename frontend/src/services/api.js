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
    name: 'Jubilación 2050',
    goal_type: 'retirement',
    risk_profile: 'moderate',
    balance: '4305.00',
    depositado_neto: '4200.00',
    ganado: '105.00',
    progress_percentage: '4.31',
    target_amount: '100000.00',
    portfolio: {
      id: 'port_demo',
      cash: '500.00',
      total_value: '4305.00',
      positions: [
        {
          ticker: 'AAPL',
          shares: '10.00',
          current_price: '180.50',
          market_value: '1805.00',
          target_allocation: '0.60',
          current_allocation: '0.42',
        },
        {
          ticker: 'META',
          shares: '5.00',
          current_price: '400.00',
          market_value: '2000.00',
          target_allocation: '0.40',
          current_allocation: '0.46',
        },
      ],
    },
  },

  rebalanceResult: {
    trades: [
      {
        ticker: 'AAPL',
        action: 'BUY',
        shares: '3.00',
        current_price: '180.50',
        value: '541.50',
        reason: 'Rebalance to target allocation',
      },
      {
        ticker: 'META',
        action: 'SELL',
        shares: '0.50',
        current_price: '400.00',
        value: '200.00',
        reason: 'Rebalance to target allocation',
      },
    ],
    total_buy_value: '541.50',
    total_sell_value: '200.00',
    estimated_cost: '7.42',
    final_allocations: {
      AAPL: '0.59',
      META: '0.41',
    },
    metrics: {
      cvar: '0.1234',
      execution_time: '0.0923',
    },
  },
};
