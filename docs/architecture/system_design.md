# System Design - IEMS

## Architecture Overview

The Intelligent Energy Management Simulator (IEMS) follows **Clean Architecture** principles with clear separation of concerns.

### Layer Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Presentation Layer                       │
│                    (FastAPI / React)                         │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                    Application Layer                         │
│              (Use Cases / Orchestration)                     │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                      Domain Layer                            │
│            (Interfaces / Models / Exceptions)                │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                   Infrastructure Layer                       │
│        (DI Container / Config / Logging)                     │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                    Implementation Layer                      │
│     (Services: Weather, Physics, Brain 1a/1b/2)             │
└─────────────────────────────────────────────────────────────┘
```

## Design Principles

### 1. Dependency Inversion Principle (DIP)

- High-level modules depend on **abstractions** (interfaces)
- Low-level modules implement these abstractions
- Example: `IPhysicsEngine` interface → `PhysicsEngine` implementation

### 2. Single Responsibility Principle (SRP)

- Each class has one reason to change
- `IWeatherService`: Only weather data retrieval
- `IPhysicsEngine`: Only physics simulation
- `ILoadGenerator`: Only load generation

### 3. Open/Closed Principle (OCP)

- Open for extension, closed for modification
- New baseline strategies can be added without changing existing code
- New optimization algorithms can implement `IOptimizer`

### 4. Interface Segregation Principle (ISP)

- Clients depend only on methods they use
- Separate interfaces for each concern

### 5. Liskov Substitution Principle (LSP)

- Any implementation can replace the interface
- All implementations must honor the contract

## Component Interactions

### Simulation Pipeline (Phase 1-4)

```
┌──────────────┐      ┌─────────────┐      ┌──────────────┐
│  Weather     │─────→│  Physics    │─────→│   System     │
│  Service     │      │  Engine     │      │   State      │
└──────────────┘      └─────────────┘      └──────────────┘
                             ↑                      ↓
                             │                      │
                      ┌──────┴──────┐      ┌───────┴──────┐
                      │ Controller  │←─────│ Load Profile │
                      │  (Brain 2)  │      │  (Brain 1a)  │
                      └─────────────┘      └──────────────┘
                             ↑
                             │
                      ┌──────┴──────┐
                      │ Optimizer   │
                      │ (Brain 1b)  │
                      └─────────────┘
```

### Data Flow

1. **Brain 1a**: Generate synthetic load profile
2. **Weather Service**: Fetch GHI & temperature data
3. **Brain 1b**: Optimize PV & battery sizing
4. **Physics Engine**: Simulate system behavior
5. **Brain 2**: Control battery dispatch
6. **Result**: Performance metrics & comparison

## Technology Stack

### Backend
- **Framework**: FastAPI
- **Language**: Python 3.10+
- **ML Libraries**: scikit-learn, PyTorch, DEAP
- **DI**: dependency-injector
- **Config**: Pydantic Settings

### Frontend (Phase 6)
- **Framework**: React + TypeScript
- **UI**: Material-UI / Tailwind
- **Charts**: Recharts / Plotly
- **State**: React Query

### Data
- **Weather**: NASA POWER API (REST)
- **Storage**: CSV files, pickle models
- **Format**: JSON for API communication

## Security Considerations

- No authentication in Phase 0-6 (demo system)
- Environment variables for sensitive config
- Input validation using Pydantic
- Rate limiting on API endpoints (Phase 5)

## Scalability

- Stateless API design
- Asynchronous weather data fetching
- Model caching
- Horizontal scaling ready (Docker + Kubernetes future)

## Next Phase

**Phase 1**: Implement Physics Engine and Weather Service
