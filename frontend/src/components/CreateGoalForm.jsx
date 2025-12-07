import { useState } from 'react'
import './CreateGoalForm.css'

function CreateGoalForm({ onSubmit, onCancel }) {
  const [formData, setFormData] = useState({
    name: '',
    goal_type: 'retirement',
    risk_profile: 'moderate',
    initial_cash: '',
    target_amount: '',
  });

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value,
    }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();

    // Validate
    if (!formData.name || !formData.initial_cash) {
      alert('Por favor completa los campos obligatorios');
      return;
    }

    // Format data
    const goalData = {
      ...formData,
      initial_cash: parseFloat(formData.initial_cash),
      target_amount: formData.target_amount ? parseFloat(formData.target_amount) : null,
    };

    onSubmit(goalData);
  };

  return (
    <div className="create-goal-form card">
      <h3>Crear Nuevo Objetivo</h3>
      <form onSubmit={handleSubmit}>
        <div className="form-grid">
          <div className="form-group">
            <label htmlFor="name">Nombre del Objetivo *</label>
            <input
              type="text"
              id="name"
              name="name"
              value={formData.name}
              onChange={handleChange}
              placeholder="ej. Jubilación 2050"
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="goal_type">Tipo de Objetivo</label>
            <select
              id="goal_type"
              name="goal_type"
              value={formData.goal_type}
              onChange={handleChange}
            >
              <option value="retirement">Jubilación</option>
              <option value="education">Educación</option>
              <option value="house">Casa</option>
              <option value="vacation">Vacaciones</option>
              <option value="general">General</option>
            </select>
          </div>

          <div className="form-group">
            <label htmlFor="risk_profile">Perfil de Riesgo</label>
            <select
              id="risk_profile"
              name="risk_profile"
              value={formData.risk_profile}
              onChange={handleChange}
            >
              <option value="conservative">Conservador</option>
              <option value="moderate">Moderado</option>
              <option value="risky">Arriesgado</option>
            </select>
          </div>

          <div className="form-group">
            <label htmlFor="initial_cash">Cash Inicial (CLP) *</label>
            <input
              type="number"
              id="initial_cash"
              name="initial_cash"
              value={formData.initial_cash}
              onChange={handleChange}
              placeholder="1000000"
              min="0"
              step="1000"
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="target_amount">Meta (CLP)</label>
            <input
              type="number"
              id="target_amount"
              name="target_amount"
              value={formData.target_amount}
              onChange={handleChange}
              placeholder="100000000"
              min="0"
              step="1000"
            />
          </div>
        </div>

        <div className="form-actions">
          <button type="button" className="secondary" onClick={onCancel}>
            Cancelar
          </button>
          <button type="submit" className="primary">
            Crear Objetivo
          </button>
        </div>
      </form>
    </div>
  );
}

export default CreateGoalForm
