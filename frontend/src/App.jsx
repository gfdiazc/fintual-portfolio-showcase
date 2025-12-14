import { useState, useEffect } from 'react'
import GoalCard from './components/GoalCard'
import RebalanceView from './components/RebalanceView'
import CreateGoalForm from './components/CreateGoalForm'
import { goalsAPI, healthAPI, sampleData } from './services/api'
import './styles/App.css'

function App() {
  const [goals, setGoals] = useState([]);
  const [selectedGoal, setSelectedGoal] = useState(null);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [apiHealthy, setApiHealthy] = useState(false);

  // Check API health on mount
  useEffect(() => {
    checkHealth();
  }, []);

  // Load goals on mount
  useEffect(() => {
    if (apiHealthy) {
      loadGoals();
    }
  }, [apiHealthy]);

  const checkHealth = async () => {
    try {
      await healthAPI.check();
      setApiHealthy(true);
    } catch (err) {
      console.warn('API not available, using demo mode');
      setApiHealthy(false);
      // Load sample data in demo mode
      setGoals([sampleData.goal]);
      setLoading(false);
    }
  };

  const loadGoals = async () => {
    try {
      setLoading(true);
      const data = await goalsAPI.list();
      setGoals(data);
      setError(null);
    } catch (err) {
      setError('Error al cargar goals: ' + err.message);
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateGoal = async (goalData) => {
    try {
      const newGoal = await goalsAPI.create(goalData);
      setGoals([...goals, newGoal]);
      setShowCreateForm(false);
      setError(null);
    } catch (err) {
      setError('Error al crear goal: ' + err.message);
      console.error(err);
    }
  };

  const handleSelectGoal = (goal) => {
    setSelectedGoal(goal);
  };

  const handleBackToList = () => {
    setSelectedGoal(null);
    loadGoals(); // Refresh en caso de cambios
  };

  return (
    <div className="app">
      <header className="app-header">
        <div className="header-content">
          <div className="brand">
            <span className="logo-text">fintual</span>
          </div>
          {!apiHealthy && (
            <div className="badge badge-warning">
              Demo Mode
            </div>
          )}
        </div>
      </header>

      {error && (
        <div className="error-banner">
          <strong>Error:</strong> {error}
          <button onClick={() => setError(null)}>✕</button>
        </div>
      )}

      <main className="app-content">
        {selectedGoal ? (
          <RebalanceView
            goal={selectedGoal}
            onBack={handleBackToList}
            apiHealthy={apiHealthy}
          />
        ) : (
          <>
            <div className="flex-between mb-3">
              <h2>Mis Objetivos</h2>
              <button
                className="primary"
                onClick={() => setShowCreateForm(!showCreateForm)}
              >
                {showCreateForm ? 'Cancelar' : '+ Nuevo Objetivo'}
              </button>
            </div>

            {showCreateForm && (
              <CreateGoalForm
                onSubmit={handleCreateGoal}
                onCancel={() => setShowCreateForm(false)}
              />
            )}

            {loading ? (
              <div className="flex-center" style={{ minHeight: '200px' }}>
                <div className="spinner"></div>
              </div>
            ) : goals.length === 0 ? (
              <div className="empty-state card">
                <h3>No hay objetivos todavía</h3>
                <p className="text-gray">
                  Crea tu primer objetivo para empezar a invertir.
                </p>
                <button
                  className="primary mt-2"
                  onClick={() => setShowCreateForm(true)}
                >
                  Crear Objetivo
                </button>
              </div>
            ) : (
              <div className="goals-grid">
                {goals.map(goal => (
                  <GoalCard
                    key={goal.id}
                    goal={goal}
                    onClick={() => handleSelectGoal(goal)}
                  />
                ))}
              </div>
            )}
          </>
        )}
      </main>

      <footer className="app-footer">
        <p>
          🤖 Built with React + FastAPI |
          Powered by CVaR optimization |
          <a href="https://github.com/gfdiazc/fintual-portfolio-showcase" target="_blank" rel="noopener noreferrer">
            GitHub
          </a>
        </p>
      </footer>
    </div>
  )
}

export default App
