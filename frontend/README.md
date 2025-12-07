# Fintual Portfolio Showcase - Frontend

React frontend for portfolio rebalancing visualization with Fintual-inspired UX.

## Features

- 🎨 **Fintual-inspired Design** - Simple, clean, modern UI
- 📊 **Portfolio Visualization** - Pie charts showing asset allocation
- ⚖️ **Rebalance Comparison** - Simple vs CVaR strategy comparison
- 📱 **Responsive** - Works on desktop and mobile
- 🚀 **Fast** - Built with Vite for instant HMR

## Tech Stack

- **React 18** - UI framework
- **Vite** - Build tool (instant HMR)
- **Recharts** - Chart library
- **Pure CSS** - No CSS frameworks, custom Fintual theme

## Getting Started

### Prerequisites

- Node.js 18+ and npm
- Backend API running on `localhost:8000`

### Installation

```bash
npm install
```

### Development

```bash
npm run dev
```

Opens at `http://localhost:3000`

### Build for Production

```bash
npm run build
```

Outputs to `dist/` directory.

### Preview Production Build

```bash
npm run preview
```

## Project Structure

```
frontend/
├── src/
│   ├── components/         # React components
│   │   ├── GoalCard.jsx           # Goal display card
│   │   ├── RebalanceView.jsx      # Rebalance execution view
│   │   └── CreateGoalForm.jsx     # Create goal form
│   ├── services/
│   │   └── api.js                 # API service layer
│   ├── styles/
│   │   ├── index.css              # Global styles + Fintual theme
│   │   └── App.css                # App-level styles
│   ├── App.jsx                    # Main app component
│   └── main.jsx                   # Entry point
├── index.html
├── vite.config.js
└── package.json
```

## API Integration

The frontend communicates with the FastAPI backend via:

- **Goals API**: `/api/v1/goals/` - CRUD operations
- **Rebalance API**: `/api/v1/rebalance/{goal_id}` - Execute rebalancing
- **Health Check**: `/health` - API status

Vite proxy configuration (`vite.config.js`) forwards `/api` requests to `localhost:8000`.

## Color Palette (Fintual-inspired)

```css
--fintual-blue: #00D1B2     /* Primary action color */
--fintual-dark: #1A1A1A     /* Text primary */
--fintual-gray: #6B7280     /* Text secondary */
--success-green: #10B981    /* Positive values */
--warning-yellow: #F59E0B   /* Warnings */
--error-red: #EF4444        /* Errors */
```

## Components

### GoalCard

Displays portfolio goal with:
- Balance, Depositado Neto, Ganado
- Progress bar toward target
- Risk profile badge
- Click to view details

### RebalanceView

Full rebalancing interface with:
- Portfolio summary metrics
- Allocation pie chart
- Positions table with drift indicators
- Strategy selector (Simple vs CVaR)
- Trade execution preview
- Results visualization

### CreateGoalForm

Form to create new goals:
- Name, type, risk profile
- Initial cash, target amount
- Validation and error handling

## Features Showcase

### Real-time Updates
- Health check on mount
- Auto-refresh after actions
- Loading states

### Error Handling
- API errors displayed clearly
- Demo mode fallback
- User-friendly error messages

### Responsive Design
- Mobile-first approach
- Grid layouts adapt to screen size
- Touch-friendly buttons

## Demo Mode

If backend API is not available, the app shows:
- Demo mode badge
- Sample data for visualization
- Disabled actions with helpful messages

## Future Enhancements

- [ ] Add position management UI
- [ ] Historical performance charts
- [ ] Export reports (PDF/CSV)
- [ ] Dark mode toggle
- [ ] Real-time WebSocket updates
- [ ] Animations and transitions
- [ ] Accessibility improvements (ARIA labels)

## License

MIT
