import './GoalCard.css'

function GoalCard({ goal, onClick }) {
  const formatCurrency = (value) => {
    return new Intl.NumberFormat('es-CL', {
      style: 'currency',
      currency: 'CLP',
      minimumFractionDigits: 0,
    }).format(value);
  };

  const formatPercentage = (value) => {
    return `${parseFloat(value).toFixed(2)}%`;
  };

  const getRiskProfileColor = (profile) => {
    const colors = {
      conservative: 'var(--success-green)',
      moderate: 'var(--fintual-blue)',
      risky: 'var(--warning-yellow)',
    };
    return colors[profile] || 'var(--fintual-gray)';
  };

  const getRiskProfileLabel = (profile) => {
    const labels = {
      conservative: 'Conservador',
      moderate: 'Moderado',
      risky: 'Arriesgado',
    };
    return labels[profile] || profile;
  };

  const getGoalTypeLabel = (type) => {
    const labels = {
      retirement: 'Jubilación',
      education: 'Educación',
      house: 'Casa',
      vacation: 'Vacaciones',
      general: 'General',
    };
    return labels[type] || type;
  };

  return (
    <div className="goal-card card" onClick={onClick}>
      <div className="goal-header">
        <div>
          <h3>{goal.name}</h3>
          <span className="goal-type-badge">{getGoalTypeLabel(goal.goal_type)}</span>
        </div>
        <div className="risk-indicator">
          <span
            className="risk-dot"
            style={{ backgroundColor: getRiskProfileColor(goal.risk_profile) }}
          ></span>
          {getRiskProfileLabel(goal.risk_profile)}
        </div>
      </div>

      <div className="goal-main-metric">
        <span className="metric-label">Monto actual</span>
        <div className="metric-value-large">{formatCurrency(goal.balance)}</div>
      </div>

      {goal.target_amount && (
        <div className="goal-progress">
          <div className="progress-info">
            <span>{formatPercentage(goal.progress_percentage)} de la meta</span>
            <span>{formatCurrency(goal.target_amount)}</span>
          </div>
          <div className="progress-track">
            <div
              className="progress-fill"
              style={{ width: `${Math.min(goal.progress_percentage, 100)}%` }}
            ></div>
          </div>
        </div>
      )}

      <div className="goal-secondary-metrics">
        <div className="metric-small">
          <span className="metric-label">Inversión</span>
          <span className="metric-value-small">{formatCurrency(goal.depositado_neto)}</span>
        </div>

        <div className="metric-small">
          <span className="metric-label">Rentabilidad</span>
          <span className={`metric-value-small ${goal.ganado >= 0 ? 'value-success' : 'value-error'}`}>
            {goal.ganado >= 0 ? '+' : ''}{formatCurrency(goal.ganado)}
          </span>
        </div>
      </div>

      {goal.portfolio?.positions && goal.portfolio.positions.length > 0 && (
        <div className="positions-preview">
          <h4>Posiciones</h4>
          {goal.portfolio.positions.slice(0, 3).map(pos => (
            <div key={pos.ticker} className="position-row">
              <div className="position-info">
                <strong>{pos.ticker}</strong>
                <span className="price-tag">
                  {formatCurrency(pos.current_price)}
                  <small>× {pos.shares} shares</small>
                </span>
              </div>
              <div className="position-value">
                {formatCurrency(pos.market_value)}
              </div>
            </div>
          ))}
          {goal.portfolio.positions.length > 3 && (
            <small className="more-positions">+{goal.portfolio.positions.length - 3} más...</small>
          )}
        </div>
      )}
    </div>
  );
}

export default GoalCard
