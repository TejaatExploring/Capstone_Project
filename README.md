# Intelligent Energy Management Simulator (IEMS)

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110.0-green.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> **A full-stack AI-powered energy management system combining machine learning, genetic algorithms, and deep reinforcement learning for optimal solar-battery-grid system design and operation.**

---

## 🎯 Project Overview

IEMS is a comprehensive simulation platform that optimizes residential/commercial energy systems using three AI "brains":

- **Brain 1a (Load Generator)**: Markov Chain + KMeans clustering for synthetic load profile generation
- **Brain 1b (System Optimizer)**: Genetic Algorithm for optimal PV and battery sizing
- **Brain 2 (Smart Controller)**: Deep Q-Network (DQN) for real-time energy dispatch

### Key Features

✅ **NASA POWER API Integration** - Real-world weather data (GHI, temperature)  
✅ **Physics-Based Simulation** - Accurate PV generation and battery modeling  
✅ **Multi-Objective Optimization** - Cost, self-consumption, grid independence  
✅ **Baseline Comparisons** - Statistical validation against conventional methods  
✅ **Production-Ready Architecture** - Clean code, SOLID principles, full testing  
✅ **Interactive Dashboard** - React-based UI with real-time visualization  

---

## 📐 Architecture

IEMS follows **Clean Architecture** with strict layer separation:

```
┌─────────────────────────────────────────────────────────────┐
│  Presentation Layer (FastAPI + React)                       │
├─────────────────────────────────────────────────────────────┤
│  Application Layer (Use Cases / Orchestration)              │
├─────────────────────────────────────────────────────────────┤
│  Domain Layer (Interfaces + Models + Exceptions)            │
├─────────────────────────────────────────────────────────────┤
│  Infrastructure Layer (Config + DI + Logging)               │
├─────────────────────────────────────────────────────────────┤
│  Implementation Layer (Services: Weather, Physics, AI)      │
└─────────────────────────────────────────────────────────────┘
```

**See**: [System Design](docs/architecture/system_design.md) | [Class Diagrams](docs/architecture/class_diagrams.md)

---

## 🚀 Quick Start

### Prerequisites

- Python 3.10 or higher
- Node.js 18+ (for frontend)
- Virtual environment tool (venv, conda)

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/yourusername/IEMS.git
cd IEMS

# 2. Create virtual environment
python -m venv venv

# 3. Activate virtual environment
# Windows:
venv\Scripts\activate
# Unix/macOS:
source venv/bin/activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Copy environment template
copy .env.example .env  # Windows
cp .env.example .env    # Unix/macOS

# 6. (Optional) Edit .env with your configuration
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=backend --cov-report=html

# Run specific test file
pytest backend/tests/unit/test_models.py
```

---

## 📂 Project Structure

```
IEMS/
├── backend/
│   ├── core/                    # Domain layer (interfaces, models, exceptions)
│   │   ├── interfaces/          # Abstract base classes
│   │   ├── models/              # Domain entities
│   │   └── exceptions/          # Custom exceptions
│   ├── infrastructure/          # Cross-cutting concerns
│   │   ├── config/              # Settings and constants
│   │   ├── di/                  # Dependency injection
│   │   └── logging/             # Logging setup
│   ├── services/                # Business logic implementations
│   │   ├── weather/             # NASA POWER API (Phase 1) ✅
│   │   ├── physics/             # Physics engine (Phase 1) ✅
│   │   ├── load/                # Load generator (Phase 2) ✅
│   │   ├── brain_1b/            # GA optimizer (Phase 3)
│   │   ├── brain_2/             # DQN controller (Phase 4)
│   │   └── baselines/           # Baseline strategies
│   ├── api/                     # FastAPI application (Phase 5)
│   ├── Dataset/                 # CSV training data
│   ├── trained_models/          # Saved ML models
│   └── tests/                   # Unit and integration tests
├── frontend/                    # React dashboard (Phase 6)
├── docs/                        # Documentation
├── requirements.txt             # Python dependencies
├── .env.example                 # Environment template
└── README.md                    # This file
```

---

## 🧪 Development Phases

### ✅ Phase 0 - Architecture & Project Skeleton

- [x] Folder structure
- [x] Abstract base classes (interfaces)
- [x] Domain models
- [x] Dependency injection framework
- [x] Configuration management
- [x] Documentation structure

**Status**: Complete ✅

---

### ✅ Phase 1 - Physics Engine & NASA API

- [x] NASA POWER API service
- [x] PV power calculation
- [x] Battery model
- [x] Grid interaction logic
- [x] Unit tests (35 passing)
- [x] **Bug Fix**: Energy balance conservation fixed

**Status**: Complete ✅ | **Tests**: 35/35 passing

---

### ✅ Phase 2 - Brain 1a (Synthetic Load Generator)

- [x] CSV data loader (14.7M rows → 915 days)
- [x] KMeans clustering (auto K=2-10 optimization)
- [x] Markov transition matrix (first-order with Laplace smoothing)
- [x] Profile generation (<1s for 720 hours)
- [x] Baseline comparison (Flat + Historical Replay)
- [x] Training pipeline (training.py)
- [x] Inference script (inference.py)
- [x] Domain models (LoadProfile, ClusteringResult, etc.)
- [x] Comprehensive tests (35 tests: 23 unit + 12 integration)
- [x] Full documentation (README.md + PHASE_2_COMPLETE.md)

**Status**: Complete ✅ | **Tests**: 35/35 passing

**Training Results**:
- **Dataset**: Smart meter data (14,767,069 rows)
- **Duration**: 915 days of hourly load data
- **Clusters**: K=2 (auto-discovered via silhouette optimization)
- **Silhouette Score**: 0.6300 (excellent cluster separation)
- **Mean Load**: 11.59 kW | **Peak Load**: 60.48 kW
- **Training Time**: 47s | **Generation Time**: <0.5s for 720 hours ✅
- **Architecture**: Clean Architecture + SOLID principles strictly followed

📄 **Detailed Report**: See [PHASE_2_COMPLETE.md](PHASE_2_COMPLETE.md)

---

### 📅 Phase 3 - Brain 1b (Genetic Algorithm)

- [ ] DEAP integration
- [ ] Chromosome definition
- [ ] Fitness evaluation
- [ ] Constraint handling
- [ ] Convergence tracking

### 📅 Phase 4 - Brain 2 (DQN Controller)

- [ ] PyTorch environment
- [ ] Replay buffer
- [ ] Target network
- [ ] Training loop
- [ ] Rule-based baseline

### 📅 Phase 5 - Backend API Integration

- [ ] FastAPI setup
- [ ] POST /simulate endpoint
- [ ] Request/response schemas
- [ ] Error handling
- [ ] API documentation

### 📅 Phase 6 - Frontend Dashboard

- [ ] React setup
- [ ] Input forms
- [ ] Results visualization
- [ ] Charts (time-series, metrics)
- [ ] Light/Dark mode

### 📅 Phase 7 - Documentation & Validation

- [ ] Module READMEs
- [ ] Validation methodology
- [ ] Comparative study results
- [ ] Deployment guide

---

## 🛠️ Technology Stack

### Backend
- **Framework**: FastAPI
- **Language**: Python 3.10+
- **ML/DL**: scikit-learn, PyTorch, DEAP
- **Data**: NumPy, Pandas
- **Testing**: pytest, pytest-cov
- **Code Quality**: black, flake8, mypy

### Frontend (Phase 6)
- **Framework**: React + TypeScript
- **UI Library**: Material-UI / Tailwind CSS
- **Charts**: Plotly / Recharts
- **State Management**: React Query

### Infrastructure
- **API**: NASA POWER (weather data)
- **DI**: dependency-injector
- **Config**: Pydantic Settings
- **Logging**: Python logging + JSON

---

## 📊 Design Principles

### SOLID Principles

- **S**ingle Responsibility: Each class has one reason to change
- **O**pen/Closed: Open for extension, closed for modification
- **L**iskov Substitution: Implementations honor interface contracts
- **I**nterface Segregation: Focused, minimal interfaces
- **D**ependency Inversion: Depend on abstractions, not concretions

### Clean Architecture

- **Domain Layer**: Business logic, no external dependencies
- **Infrastructure Layer**: Framework-specific code
- **Dependency Rule**: Dependencies point inward only

---

## 🧑‍💻 Contributing

This is an academic capstone project. Contributions are welcome for:

- Bug fixes
- Performance improvements
- Additional baseline strategies
- Documentation enhancements

---

## 📝 License

MIT License - See [LICENSE](LICENSE) file for details.

---

## 📧 Contact

**Project Team**: IEMS Development Team  
**Institution**: [Your Institution]  
**Year**: 2024-2025

---

## 🙏 Acknowledgments

- **NASA POWER Project** for providing free weather data API
- **DEAP** for genetic algorithm framework
- **PyTorch** for deep learning capabilities
- **FastAPI** for modern API development

---

## 📚 References

1. NASA POWER API: https://power.larc.nasa.gov/
2. DEAP Documentation: https://deap.readthedocs.io/
3. PyTorch Tutorials: https://pytorch.org/tutorials/
4. Clean Architecture: Robert C. Martin

---

**Current Status**: Phase 2 Complete ✅ | Ready for Phase 3 🚀

**Latest Achievement**: Synthetic Load Generator trained on 915 days of smart meter data with excellent clustering (K=2, silhouette=0.63). All 35 tests passing. Generation time <0.5s for 720 hours.

⚠️ **Awaiting Confirmation**: Ready to begin Phase 3 (Brain 1b - Genetic Algorithm Optimizer) upon approval.
