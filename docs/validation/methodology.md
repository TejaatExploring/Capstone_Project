# Validation Methodology - IEMS

## Overview

This document defines the validation strategy for the Intelligent Energy Management Simulator (IEMS). Each AI component (Brain 1a, 1b, 2) must demonstrate statistically significant improvement over established baseline methods.

---

## General Principles

### 1. Baseline Comparison Requirement

**Rule**: Every AI method MUST be compared against at least one baseline strategy.

**Purpose**: Establish that AI methods provide measurable value over conventional approaches.

### 2. Statistical Significance

**Threshold**: p-value < 0.05 (95% confidence)

**Tests**:
- Paired t-test for comparing two methods
- ANOVA for comparing multiple methods
- Wilcoxon signed-rank test for non-parametric data

### 3. Minimum Improvement Threshold

**Rule**: AI method must demonstrate at least **5% improvement** in key metrics.

**Rationale**: Small improvements may not justify computational complexity.

---

## Phase 2 Validation: Brain 1a (Load Generator)

### Objective
Validate that Markov + KMeans generates more realistic load profiles than simple baselines.

### Baseline Strategy
**Flat Profile Generator**: Constant load = average of historical data

### Metrics

| Metric | Description | Target |
|--------|-------------|--------|
| Mean Absolute Error (MAE) | Average deviation from actual patterns | < 1.0 kW |
| Root Mean Square Error (RMSE) | Penalizes large deviations | < 1.5 kW |
| Peak Error | Deviation in peak load | < 15% |
| Correlation Coefficient | Shape similarity | > 0.85 |
| Silhouette Score | Clustering quality | > 0.5 |

### Validation Steps

1. **Split Data**: 80% training, 20% testing
2. **Train Models**: Markov+KMeans vs. Flat baseline
3. **Generate Profiles**: 720-hour profiles (30 days)
4. **Compare Metrics**: Statistical tests
5. **Report**: 
   - Improvement percentages
   - Confidence intervals
   - Visualizations (actual vs. generated)

### Success Criteria

✅ Markov+KMeans MAE < Flat baseline MAE  
✅ Correlation > 0.85  
✅ p-value < 0.05 in paired t-test  

---

## Phase 3 Validation: Brain 1b (Genetic Algorithm)

### Objective
Validate that GA finds better system configurations than exhaustive search (within constraints).

### Baseline Strategy
**Brute-Force Grid Search**: Exhaustive evaluation of discrete parameter combinations

Parameters:
- PV: [0, 5, 10, 15, 20, 25, 30] kW
- Battery: [0, 10, 20, 30, 40, 50] kWh

### Metrics

| Metric | Description | Target |
|--------|-------------|--------|
| Total Cost | Component + operational cost | Minimize |
| Self-Sufficiency Ratio | Load met by PV+Battery | Maximize |
| Grid Independence | Reduction in grid import | Maximize |
| Convergence Speed | Generations to optimum | < 50 |
| Constraint Satisfaction | Budget, roof area | 100% |

### Validation Steps

1. **Define Problem**: Load profile, weather data, constraints
2. **Run Brute-Force**: Evaluate all combinations
3. **Run GA**: 50 generations, population=100
4. **Compare Solutions**:
   - Cost comparison
   - Time comparison
   - Solution quality
5. **Statistical Analysis**: Multiple runs (10+) for robustness

### Success Criteria

✅ GA finds solution within 5% of brute-force optimum  
✅ GA completes in < 50% of brute-force time  
✅ 100% constraint satisfaction  

---

## Phase 4 Validation: Brain 2 (DQN Controller)

### Objective
Validate that DQN controller achieves better economic performance than rule-based strategies.

### Baseline Strategy
**Rule-Based Controller**:
- **Rule 1**: If excess PV, charge battery
- **Rule 2**: If shortage, discharge battery
- **Rule 3**: If battery empty, import from grid
- **Rule 4**: If high electricity price, use battery

### Metrics

| Metric | Description | Target |
|--------|-------------|--------|
| Total Cost | Electricity + degradation cost | Minimize |
| Battery Cycles | Total charge/discharge cycles | Minimize |
| Grid Import | Total kWh from grid | Minimize |
| Peak Demand | Maximum grid import | Minimize |
| Reward | Cumulative DQN reward | Maximize |

### Validation Steps

1. **Training**: 1000 episodes, multiple scenarios
2. **Testing**: 30-day simulation (unseen data)
3. **Baseline Run**: Same scenarios, rule-based controller
4. **Compare Performance**:
   - Cost savings
   - Battery degradation
   - Grid usage patterns
5. **Sensitivity Analysis**: Vary electricity prices, PV capacity

### Success Criteria

✅ DQN cost < Rule-based cost (5%+ improvement)  
✅ DQN battery cycles < Rule-based cycles  
✅ p-value < 0.05 across 10+ test scenarios  

---

## Integrated System Validation (Phase 5-7)

### End-to-End Pipeline Test

**Scenario**: Simulate complete workflow

1. **Brain 1a**: Generate load profile
2. **Brain 1b**: Optimize system sizing
3. **Brain 2**: Control dispatch for 30 days
4. **Baseline**: Run equivalent baseline pipeline

**Comparison**:
- Total system cost (capital + operational)
- Energy metrics (self-sufficiency, grid import)
- Economic metrics (payback period, NPV)

### Success Criteria

✅ AI pipeline outperforms baseline pipeline by 10%+ in total cost  
✅ All individual components validated independently  
✅ System stability (no crashes, constraint violations)  

---

## Statistical Tests Reference

### Paired t-test
**Use**: Compare two methods on same data  
**Null Hypothesis**: No difference in means  
**Python**: `scipy.stats.ttest_rel()`

### ANOVA
**Use**: Compare multiple methods  
**Null Hypothesis**: All means are equal  
**Python**: `scipy.stats.f_oneway()`

### Wilcoxon Signed-Rank Test
**Use**: Non-parametric alternative to t-test  
**Null Hypothesis**: No difference in distributions  
**Python**: `scipy.stats.wilcoxon()`

### Confidence Intervals
**95% CI**: Mean ± 1.96 * (Std / √n)

---

## Reporting Template

### For Each Phase

```markdown
## Validation Results: [Phase Name]

### Experimental Setup
- Dataset: [description]
- Train/Test Split: 80/20
- Random Seed: 42
- Hardware: [specs]

### Baseline Strategy
[Description of baseline]

### Results

| Metric | Baseline | AI Method | Improvement | p-value |
|--------|----------|-----------|-------------|---------|
| ...    | ...      | ...       | ...         | ...     |

### Visualization
[Charts: comparison plots, convergence, etc.]

### Statistical Analysis
- Test Used: [t-test, ANOVA, etc.]
- Confidence Level: 95%
- Conclusion: [Accept/Reject AI superiority]

### Discussion
[Interpretation, limitations, future work]
```

---

## Documentation Requirements

For each validation experiment:

1. **Code**: Jupyter notebook or Python script
2. **Data**: Raw results (CSV)
3. **Report**: Markdown document (README)
4. **Figures**: High-resolution plots (PNG/PDF)
5. **Reproducibility**: Random seeds, environment specs

---

## Next Steps

- **Phase 1**: No validation (deterministic physics)
- **Phase 2**: Implement Brain 1a baseline + validation
- **Phase 3**: Implement Brain 1b baseline + validation
- **Phase 4**: Implement Brain 2 baseline + validation
- **Phase 7**: Generate comprehensive validation report

---

**Status**: Methodology Defined ✅ | Ready for Implementation 🚀
