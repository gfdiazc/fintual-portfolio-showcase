import { useState } from 'react'
import { rebalanceAPI } from '../services/api'
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from 'recharts'
import './RebalanceView.css'

const COLORS = ['#00D1B2', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#EC4899'];

function RebalanceView({ goal, onBack, apiHealthy }) {
  const [strategy, setStrategy] = useState('simple');
  const [rebalanceResult, setRebalanceResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('es-CL', {
      style: 'currency',
      currency: 'CLP',
      minimumFractionDigits: 0,
    }).format(value);
  };

  const formatPercentage = (value) => {
    return `${(parseFloat(value) * 100).toFixed(2)}%`;
  };

  const handleRebalance = async () => {
    if (!apiHealthy) {
      alert('API no disponible. Modo demo.');
      return;
    }

    try {
      setLoading(true);
      setError(null);

      const result = await rebalanceAPI.execute(goal.id, {
        strategy,
        dry_run: true,
      });

      setRebalanceResult(result);
    } catch (err) {
      setError('Error al ejecutar rebalanceo: ' + err.message);
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  // Preparar datos para pie chart
  const getPieChartData = () => {
    if (!goal.portfolio?.positions) return [];

    return goal.portfolio.positions.map((pos, idx) => ({
      name: pos.ticker,
      value: parseFloat(pos.market_value),
      allocation: parseFloat(pos.current_allocation) * 100,
      target: parseFloat(pos.target_allocation) * 100,
    }));
  };

  const renderCustomLabel = ({ cx, cy, midAngle, innerRadius, outerRadius, percent }) => {
    const radius = innerRadius + (outerRadius - innerRadius) * 0.5;
    const x = cx + radius * Math.cos(-midAngle * Math.PI / 180);
    const y = cy + radius * Math.sin(-midAngle * Math.PI / 180);

    return (
      <text
        x={x}
        y={y}
        fill="white"
        textAnchor={x > cx ? 'start' : 'end'}
        dominantBaseline="central"
        fontSize="14"
        fontWeight="bold"
      >
        {`${(percent * 100).toFixed(0)}%`}
      </text>
    );
  };

  return (
    <div className="rebalance-view">
      <div className="rebalance-header">
        <button className="secondary" onClick={onBack}>
          ← Volver
        </button>
        <h2>{goal.name}</h2>
      </div>

      <div className="grid grid-2">
        {/* Portfolio Overview */}
        <div className="card">
          <h3>Resumen del Portfolio</h3>
          <div className="portfolio-metrics">
            <div className="metric-row">
              <span>Balance Total</span>
              <strong>{formatCurrency(goal.balance)}</strong>
            </div>
            <div className="metric-row">
              <span>Cash Disponible</span>
              <strong>{formatCurrency(goal.portfolio?.cash || 0)}</strong>
            </div>
            <div className="metric-row">
              <span>Ganado</span>
              <strong className={goal.ganado >= 0 ? 'text-success' : 'text-error'}>
                {goal.ganado >= 0 ? '+' : ''}{formatCurrency(goal.ganado)}
              </strong>
            </div>
          </div>
        </div>

        {/* Allocation Chart */}
        <div className="card">
          <h3>Distribución Actual</h3>
          {getPieChartData().length > 0 ? (
            <ResponsiveContainer width="100%" height={250}>
              <PieChart>
                <Pie
                  data={getPieChartData()}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={renderCustomLabel}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {getPieChartData().map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip formatter={(value) => formatCurrency(value)} />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <p className="text-gray">No hay posiciones</p>
          )}
        </div>
      </div>

      {/* Positions Table */}
      <div className="card">
        <h3>Posiciones</h3>
        <div className="positions-table">
          <table>
            <thead>
              <tr>
                <th>Ticker</th>
                <th>Shares</th>
                <th>Precio</th>
                <th>Valor</th>
                <th>Actual</th>
                <th>Target</th>
                <th>Drift</th>
              </tr>
            </thead>
            <tbody>
              {goal.portfolio?.positions?.map((pos) => {
                const drift = parseFloat(pos.current_allocation) - parseFloat(pos.target_allocation);
                return (
                  <tr key={pos.ticker}>
                    <td><strong>{pos.ticker}</strong></td>
                    <td>{pos.shares}</td>
                    <td>{formatCurrency(pos.current_price)}</td>
                    <td>{formatCurrency(pos.market_value)}</td>
                    <td>{formatPercentage(pos.current_allocation)}</td>
                    <td>{formatPercentage(pos.target_allocation)}</td>
                    <td className={drift > 0.05 ? 'text-warning' : drift < -0.05 ? 'text-error' : 'text-success'}>
                      {drift > 0 ? '+' : ''}{formatPercentage(drift)}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Rebalance Controls */}
      <div className="card">
        <h3>Ejecutar Rebalanceo</h3>
        <div className="rebalance-controls">
          <div className="form-group">
            <label htmlFor="strategy">Estrategia</label>
            <select
              id="strategy"
              value={strategy}
              onChange={(e) => setStrategy(e.target.value)}
            >
              <option value="simple">Simple (Baseline)</option>
              <option value="cvar">CVaR Optimized</option>
            </select>
          </div>

          <button
            className="primary"
            onClick={handleRebalance}
            disabled={loading || !apiHealthy}
          >
            {loading ? 'Calculando...' : 'Calcular Rebalanceo'}
          </button>

          {!apiHealthy && (
            <p className="text-warning">⚠️ API no disponible - modo demo</p>
          )}
        </div>

        {error && (
          <div className="error-message">
            {error}
          </div>
        )}
      </div>

      {/* Rebalance Result */}
      {rebalanceResult && (
        <div className="card rebalance-result">
          <h3>Resultado del Rebalanceo</h3>

          <div className="result-summary">
            <div className="summary-item">
              <label>Trades</label>
              <strong>{rebalanceResult.trades.length}</strong>
            </div>
            <div className="summary-item">
              <label>Compras</label>
              <strong className="text-success">{formatCurrency(rebalanceResult.total_buy_value)}</strong>
            </div>
            <div className="summary-item">
              <label>Ventas</label>
              <strong className="text-warning">{formatCurrency(rebalanceResult.total_sell_value)}</strong>
            </div>
            <div className="summary-item">
              <label>Costos</label>
              <strong className="text-error">{formatCurrency(rebalanceResult.estimated_cost)}</strong>
            </div>
          </div>

          <div className="trades-list">
            <h4>Trades Sugeridos</h4>
            {rebalanceResult.trades.length === 0 ? (
              <p className="text-gray">No se requieren trades</p>
            ) : (
              <table>
                <thead>
                  <tr>
                    <th>Ticker</th>
                    <th>Acción</th>
                    <th>Shares</th>
                    <th>Precio</th>
                    <th>Valor</th>
                    <th>Razón</th>
                  </tr>
                </thead>
                <tbody>
                  {rebalanceResult.trades.map((trade, idx) => (
                    <tr key={idx}>
                      <td><strong>{trade.ticker}</strong></td>
                      <td>
                        <span className={trade.action === 'BUY' ? 'badge-success' : 'badge-warning'}>
                          {trade.action}
                        </span>
                      </td>
                      <td>{trade.shares}</td>
                      <td>{formatCurrency(trade.current_price)}</td>
                      <td>{formatCurrency(trade.value)}</td>
                      <td className="text-gray">{trade.reason}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>

          {rebalanceResult.metrics && (
            <div className="metrics-display">
              <h4>Métricas</h4>
              <div className="metrics-grid">
                {Object.entries(rebalanceResult.metrics).map(([key, value]) => (
                  <div key={key} className="metric-item">
                    <label>{key}</label>
                    <span>{typeof value === 'number' ? value.toFixed(4) : value}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default RebalanceView
