

# Synthetic Load Generator (Brain 1a)

**Phase 2 - Intelligent Energy Management Simulator (IEMS)**

## 🎯 Overview

The Synthetic Load Generator creates realistic hourly electricity consumption profiles using **Markov Chains** and **KMeans Clustering** trained on real smart meter data.

### Why This Approach?

| Method | Pros | Cons |
|--------|------|------|
| **Flat Baseline** | Simple, fast | Unrealistic (no variation) |
| **Historical Replay** | Uses real data | Limited diversity, no forecasting |
| **Markov + KMeans** ✅ | Captures patterns, generates novel sequences, statistically similar | Requires training data |

### Key Innovation

1. **KMeans** discovers typical daily load patterns (e.g., weekday, weekend, high-usage)
2. **Markov Chain** models day-to-day transitions between patterns
3. **Gaussian Noise** adds micro-variations for realism

---

## 📁 Architecture

```
backend/services/load/
├── load_generator.py       # Main LoadGenerator (implements ILoadGenerator)
├── data_loader.py          # SmartMeterDataLoader
├── clustering.py           # LoadClusterer (KMeans + silhouette optimization)
├── markov_model.py         # MarkovLoadModel (transition matrix)
├── baselines.py            # FlatBaseline, HistoricalReplayBaseline
├── training.py             # Training pipeline script
├── inference.py            # Generation script
└── README.md               # This file
```

**Clean Architecture Compliance:**
- ✅ Implements `ILoadGenerator` interface (core/interfaces/)
- ✅ Uses domain models (core/models/)
- ✅ No business logic in API layer
- ✅ Dependency inversion (interface-based design)

---

## 🚀 Quick Start

### 1. Training

```bash
# Train on smart meter dataset
python -m backend.services.load.training
```

**Output:**
- `backend/trained_models/load_generator/kmeans_model.pkl`
- `backend/trained_models/load_generator/markov_matrix.pkl`
- `backend/trained_models/load_generator/training_stats.pkl`
- `backend/trained_models/load_generator/evaluation_report.txt`

**Expected Performance:**
- Training time: **< 10 seconds** ✅
- Silhouette score: **> 0.3** (higher is better)

### 2. Inference

```bash
# Generate 720 hours (30 days) of synthetic load
python -m backend.services.load.inference --hours 720 --seed 42 --output synthetic_load.csv
```

**Expected Performance:**
- Generation time: **< 1 second** ✅

### 3. Programmatic Usage

```python
from backend.services.load import LoadGenerator

# Train
generator = LoadGenerator()
generator.train("backend/Dataset/smart_meter_data.csv")
generator.save_model("backend/trained_models/load_generator")

# Generate
profile = generator.generate_profile(duration_hours=720, seed=42)
# profile is np.ndarray of shape (720,) with hourly kW values
```

---

## 🧠 Technical Details

### Data Pipeline

```
Smart Meter CSV (3-min intervals)
    ↓
[SmartMeterDataLoader]
    - Parse timestamps
    - Handle missing values
    - Resample to hourly
    - Validate continuity
    ↓
Hourly Load DataFrame (kW)
    ↓
[LoadClusterer]
    - Extract daily 24-hour profiles
    - Standardize features
    - KMeans (K=2 to 10)
    - Silhouette score optimization
    ↓
Cluster Labels + Centroids
    ↓
[MarkovLoadModel]
    - Count transitions (day i → day i+1)
    - Laplace smoothing (avoid zero probabilities)
    - Normalize to probabilities
    ↓
Transition Matrix P[i, j]
```

### Generation Algorithm

1. **Sample initial cluster** (uniform or stationary distribution)
2. **For each day:**
   - Use Markov chain to select next cluster
   - Sample from cluster centroid + Gaussian noise
3. **Concatenate hourly values**
4. **Apply smoothing** at day boundaries
5. **Clip negative values** (ensure physical validity)

### Mathematical Foundation

**Markov Property:**
```
P(State_tomorrow | State_today, State_yesterday, ...) = P(State_tomorrow | State_today)
```

**Transition Probability (with Laplace smoothing):**
```
P(i → j) = (count(i → j) + α) / (Σ_k count(i → k) + α * K)
```

Where:
- `α = 0.01` (smoothing parameter)
- `K` = number of clusters

**Sampling:**
```
Daily Load = Cluster_Centroid + Gaussian_Noise
Noise ~ N(0, σ)
σ = mean(Centroid) * 0.1
```

---

## 📊 Evaluation Metrics

### Statistical Comparison

| Metric | Description | Target |
|--------|-------------|--------|
| **Mean Error** | `|μ_synthetic - μ_real|` | < 20% |
| **Std Error** | `|σ_synthetic - σ_real|` | < 30% |
| **KS Test** | Kolmogorov-Smirnov p-value | > 0.05 (distributions similar) |
| **RMSE** | Root mean squared error | Lower is better |

### Baseline Comparison

Run evaluation to compare:
- **Markov + KMeans** (this model)
- **Flat Baseline** (constant average load)
- **Historical Replay** (random sampling of real days)

See `evaluation_report.txt` for detailed comparison.

---

## 🧪 Testing

### Run Tests

```bash
# Unit tests (20+ tests)
pytest tests/unit/test_load_generator.py -v

# Integration tests (10+ tests)
pytest tests/integration/test_load_pipeline.py -v

# All tests
pytest tests/ -k load -v
```

### Test Coverage

- ✅ Domain models (LoadProfile, DailyLoadProfile, ClusteringResult, MarkovTransitionMatrix)
- ✅ Data loading and preprocessing
- ✅ Clustering (KMeans, silhouette optimization)
- ✅ Markov model (transition matrix, sequence generation)
- ✅ Main generator (training, generation, persistence)
- ✅ Baselines (Flat, Historical Replay)
- ✅ Statistical comparisons
- ✅ End-to-end pipeline
- ✅ Performance requirements
- ✅ Reproducibility

---

## 📈 Results Summary

After running `training.py`, you should see:

```
Training Metrics:
  Duration: ~365 days
  Mean Load: ~X.XX kW
  Peak Load: ~X.XX kW
  Clusters (K): 3-5 (auto-optimized)
  Silhouette Score: ~0.4-0.6

Baseline Comparison:
  1. Historical Replay: ~5% mean error
  2. Markov+KMeans: ~10% mean error
  3. Flat Baseline: ~15% mean error

Performance:
  Training: < 10 seconds ✅
  Generation (720h): < 1 second ✅
```

---

## 🔬 Limitations & Future Work

### Current Limitations

1. **First-order Markov:** Only considers previous day (could extend to higher-order)
2. **No external features:** Doesn't use weather, holidays, etc.
3. **Stationary transitions:** Assumes transition probabilities don't change over time
4. **Gaussian noise:** Simplistic variability model

### Potential Improvements (Brain 2)

- Add **LSTM/RNN** for sequence modeling
- Incorporate **external features** (temperature, day-of-week, holidays)
- Use **Gaussian Mixture Models** instead of KMeans
- Implement **variational autoencoders** for richer generative model
- Add **seasonality modeling** (summer vs winter patterns)

---

## 📝 References

- **KMeans Clustering:** Sklearn documentation
- **Silhouette Score:** Rousseeuw, P. J. (1987). Silhouettes: A graphical aid to the interpretation of clustering
- **Markov Chains:** Ross, S. M. (2014). Introduction to Probability Models
- **Laplace Smoothing:** Manning & Schütze (1999). Foundations of Statistical NLP

---

## ✅ Phase 2 Completion Checklist

- [x] Data loader with validation
- [x] KMeans clustering with automatic K optimization
- [x] Markov transition matrix with smoothing
- [x] Synthetic load generator (720 hours)
- [x] Model persistence (.pkl files)
- [x] Baseline implementations (Flat, Historical Replay)
- [x] Statistical comparison utilities
- [x] Comprehensive tests (30+ tests)
- [x] Training < 10 seconds
- [x] Generation < 1 second
- [x] Documentation (this README)
- [x] Clean Architecture compliance
- [x] No hardcoded parameters
- [x] Full typing hints
- [x] Docstrings for all classes

**Status: Phase 2 Complete** ✅

---

**Next Phase:** Brain 2 (Deep RL Optimizer) - See Phase 3 documentation.
