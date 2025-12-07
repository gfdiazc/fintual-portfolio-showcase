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
        <h3>{goal.name}</h3>
        <span
          className="risk-badge"
          style={{ backgroundColor: getRiskProfileColor(goal.risk_profile) }}
        >
          {getRiskProfileLabel(goal.risk_profile)}
        </span>
      </div>

      <div className="goal-type">
        <span className="badge badge-info">{getGoalTypeLabel(goal.goal_type)}</span>
      </div>

      <div className="goal-metrics">
        <div className="metric">
          <label>Balance</label>
          <span className="value">{formatCurrency(goal.balance)}</span>
        </div>

        <div className="metric">
          <label>Depositado</label>
          <span className="value-secondary">{formatCurrency(goal.depositado_neto)}</span>
        </div>

        <div className="metric">
          <label>Ganado</label>
          <span className={goal.ganado >= 0 ? 'value-success' : 'value-error'}>
            {goal.ganado >= 0 ? '+' : ''}{formatCurrency(goal.ganado)}
          </span>
        </div>
      </div>

      {goal.target_amount && (
        <div className="goal-progress">
          <div className="progress-header">
            <label>Progreso</label>
            <span>{formatPercentage(goal.progress_percentage)}</span>
          </div>
          <div className="progress-bar">
            <div
              className="progress-fill"
              style={{ width: `${Math.min(goal.progress_percentage, 100)}%` }}
            ></div>
          </div>
          <div className="progress-label">
            <span>Meta: {formatCurrency(goal.target_amount)}</span>
          </div>
        </div>
      )}

      <div className="goal-footer">
        <span className="positions-count">
          {goal.portfolio?.positions?.length || 0} posiciones
        </span>
        <span className="view-link">Ver detalles →</span>
      </div>
    </div>
  );
}

export default GoalCard
