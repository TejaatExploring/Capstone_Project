# Frontend - React Dashboard

> **Implementation**: Phase 6

This directory will contain the React-based frontend dashboard for IEMS.

## Planned Structure

```
frontend/
├── public/
│   ├── index.html
│   └── favicon.ico
├── src/
│   ├── components/
│   │   ├── InputForm/
│   │   ├── Dashboard/
│   │   ├── Charts/
│   │   └── Layout/
│   ├── services/
│   │   └── api.ts
│   ├── hooks/
│   │   └── useSimulation.ts
│   ├── types/
│   │   └── simulation.ts
│   ├── utils/
│   │   └── formatters.ts
│   ├── App.tsx
│   └── main.tsx
├── package.json
├── tsconfig.json
├── vite.config.ts
└── README.md
```

## Technology Stack

- **Framework**: React 18+ with TypeScript
- **Build Tool**: Vite
- **UI Library**: Material-UI or Tailwind CSS
- **Charts**: Recharts or Plotly.js
- **State Management**: React Query
- **HTTP Client**: Axios

## Features (To Be Implemented)

- [ ] Simulation configuration form
- [ ] Real-time simulation status
- [ ] Interactive result dashboard
- [ ] Time-series charts (PV, load, battery SoC, grid)
- [ ] Performance metrics display
- [ ] Comparison view (AI vs. Baseline)
- [ ] Export results (PDF/CSV)
- [ ] Light/Dark mode toggle

## Setup (Phase 6)

```bash
cd frontend
npm install
npm run dev
```

## API Integration

Frontend will communicate with FastAPI backend:

- **Base URL**: `http://localhost:8000/api`
- **Endpoints**: `/simulate`, `/results`, `/models`

---

**Status**: Placeholder ⏳ | To Be Implemented in Phase 6
