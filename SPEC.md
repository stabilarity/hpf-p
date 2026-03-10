# HPF Portfolio Optimization App — Formal Specification
**Version:** 2.0  
**Author:** Oleh Ivchenko  
**Date:** 2026-03-04  
**Status:** AUTHORITATIVE

---

## 1. Purpose and Scope

Authoritative specification for HPF-P (Holistic Portfolio Framework — Platform). Defines data contracts, module interfaces, algorithmic formulas, API schemas, and multi-strategy optimization pipeline.

Target: **commercial pharmaceutical SKU portfolio management** (FARMAK, DARNYTSYA style) — inventory allocation optimization, not clinical trial portfolios.

---

## 2. System Architecture

### 2.1 Deployment
- **Backend:** FastAPI (Python 3.12) on port 8901, systemd service `hpf-app`
- **Frontend:** Inline WP page + mu-plugin (`hpf-project.php`) for styles/scenarios/engine
- **Scenarios:** `/wp-content/uploads/hpf-samples.js` — 5 Ukrainian pharma companies
- **Data:** `/opt/hpf-app/data/` — sample CSV + metadata JSON
- **Apache proxy:** `/hpf/` → `localhost:8901`

### 2.2 Pipeline (8 Modules)
```
Input CSV+JSON → M1 Ingest → M2 DRI/DRL → M3 ML Forecast → M4 Multi-Strategy Optimize → M5 Monte Carlo → M5b Time-Series Simulation → M6 Output Assembly
```

---

## 3. Data Contracts

### 3.1 Input: CSV
| Column | Type | Required | Description |
|--------|------|----------|-------------|
| date | ISO 8601 | ✅ | Month of observation |
| sku_id | string | ✅ | Matches metadata JSON keys |
| quantity | float | ✅ | Units sold ≥ 0 |
| revenue | float | ✅ | Revenue in UAH |
| price | float | ❌ | Unit price (derived if absent) |
| marketing_spend | float | ❌ | Ad spend |

### 3.2 Input: Metadata JSON
```json
{
  "company": "string",
  "currency": "UAH",
  "market_context": { "reimbursement_model": "string" },
  "portfolio_rules": { "default_min_weight": 0.0, "default_max_weight": 0.35 },
  "skus": {
    "SKU_ID": {
      "status": "active|discontinuing",
      "demand": { "historical_coverage_ratio": 0.0-1.0, "observability": "high|medium|low" },
      "economics": { "gross_margin": 0.0-1.0, "price_elasticity": float },
      "allocation_bounds": { "min": float, "max": float }
    }
  }
}
```

### 3.3 API Request
```
POST /api/analyze
{
  "csv_data": "string (CSV content)",
  "metadata": { ... },
  "deterministic": true|false
}
```

---

## 4. Module Specifications

### M1: Data Ingestion & Validation
- Parse CSV, validate required columns
- Cross-reference SKU IDs with metadata
- Impute missing values (linear interpolation + forward/back fill)
- Compute per-SKU missingness ratio
- Quality flags: OK (<20% missing) or DATA_QUALITY=POOR

### M2: DRI Computation & DRL Assignment
**DRI = 0.25·R1 + 0.25·R2 + 0.20·R3 + 0.15·R4 + 0.15·R5**

| Dimension | Weight | Computation |
|-----------|--------|-------------|
| R1 Data Completeness | 25% | min(1-missingness_ratio, metadata_coverage) |
| R2 Demand Signal | 25% | 1 - effective_CV (CV + missingness_penalty×0.5) |
| R3 Tail Risk | 20% | 0.5 + 0.5·tanh(2·(1 - tail_fraction)) |
| R4 Regulatory | 15% | Observability map + status + reimbursement adjustments |
| R5 Temporal Stability | 15% | 1 - (structural_breaks / total_segments) via Chow test |

**DRL Thresholds:**
| DRL | DRI Range | Strategy |
|-----|-----------|----------|
| 1 | <0.25 | ABSTAIN_HOLD |
| 2 | 0.25-0.45 | REVENUE_PROPORTIONAL |
| 3 | 0.45-0.65 | CONSTRAINED_LP |
| 4 | 0.65-0.80 | CVAR_MV |
| 5 | ≥0.80 | MULTI_OBJECTIVE_ML |

### M3: ML Estimation
- **Demand Forecast:** Linear trend + Fourier seasonal features (period=12)
- **Price Elasticity:** Log-log OLS or metadata fallback
- **Risk Score:** 0.5·rolling_volatility + 0.5·tail_revenue_ratio
- **Per-SKU outputs:** forecast_mean, forecast_std, CI, elasticity, risk_score, historical/forecast revenue series

### M4: Multi-Strategy Portfolio Optimization
Runs **8 strategies** in parallel, evaluates each via quick 200-iteration MC, selects best performer:

| Strategy | Method |
|----------|--------|
| Equal-Weight | 1/N baseline |
| DRL-Grouped | Per-DRL-group optimization (LP, CVaR/MV, multi-objective) |
| Momentum | (recent/older)³ — cubed momentum ratio |
| DRI-Weighted | DRL multiplier × DRI² |
| Risk-Parity | Inverse volatility |
| Profit-Max | (margin × forecast)² — squared profit potential |
| Mean-Variance | (return+0.1) / volatility² |
| HPF-Ensemble | Average of all non-equal strategies |

**Selection:** Strategy with highest total expected revenue wins.

### M5: Monte Carlo Simulation (1000 iterations)
- **Deterministic:** Fixed seed (42) for global PRNG
- **Stochastic:** Random base seed per run, per-iteration `seed(base + i)`
- Samples demand and price from normal distributions
- Outputs: VaR-95, CVaR-95, portfolio return mean/std/percentiles, per-SKU confidence intervals

### M5b: Time-Series Simulation (500 paths, 12-month horizon)
- 3 scenarios: Historical (actual), Baseline (equal weights), HPF (optimized weights)
- Per-SKU monthly Fourier forecast extrapolation
- **Prediction line:** Median (P50) across simulation paths
- **Bands:** P10/P25/P75/P90 for distribution visualization
- Scale factor: calibrated to match last historical revenue value

**Economic comparison metrics:**
Sharpe, Sortino, Calmar, VaR-95, CVaR-95, Max Drawdown, Prob. Outperform, Breakeven Month, Revenue Gain %

### M6: Output Assembly
- Portfolio weights with justification per SKU
- Module diagnostics
- Strategy comparison scores
- Narrative summary
- Per-SKU forecasts (historical + predicted + bands)

---

## 5. Client-Side Engine (Scenario Mode)

### 5.1 Predefined Scenarios
| Company | SKUs | Volatility | Growth |
|---------|------|-----------|--------|
| Farmak | 18 | Low | Moderate |
| Darnitsa | 15 | Low | Moderate |
| Arterium | 16 | Medium | Moderate |
| Yuria-Pharm | 14 | Medium | High |
| Zdorovye (Kharkiv) | 12 | Extreme | Negative |

### 5.2 Synthetic Data Generation
- SKU tier system: ~30% stars (high growth, low vol), ~40% stable, ~30% declining
- Fourier + noise historical series generation
- Client-side DRI calculation with same R1-R5 formula

### 5.3 Seeded PRNG
- **Deterministic:** Mulberry32 PRNG, seed = 42 + idx×1000
- **Stochastic:** Seeded data generation + Math.random() for MC only
- 6 rebalancing strategies (DRL-Weighted, Momentum, Mean-Variance, Risk-Parity, Growth-DRI, HPF-Ensemble)

---

## 6. UI Features
- Scenario picker (5 Ukrainian pharma companies)
- Deterministic/Stochastic toggle
- Backspace key → Run Analysis
- Re-run without reselecting data
- Print/PDF via window.print() + @media print styles
- DRL filter tabs for SKU cards
- Chart.js charts: trajectory, weights, DRI bars, delta bars, DRL donut, per-SKU forecasts
- CSV/JSON download of results
