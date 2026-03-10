# **2.2. Architecture of the HPF-P Platform: From Theoretical Framework to Production System**

The preceding section established the conceptual foundations of the Decision Readiness Index (DRI) and Decision Readiness Levels (DRL) as diagnostic instruments for governing portfolio decisions under structural uncertainty. The present section describes the architecture of **HPF-P** (*Holistic Portfolio Framework — Platform*), the production system that operationalises these theoretical constructs into an executable decision-support pipeline for pharmaceutical SKU portfolio management.

HPF-P transforms the abstract DRI/DRL framework into a concrete computational system that ingests real-world pharmaceutical data, computes decision readiness diagnostics, applies conditionally permitted optimisation strategies, and produces auditable portfolio recommendations. The platform targets commercial pharmaceutical portfolios — the inventory allocation and revenue optimisation decisions faced by Ukrainian manufacturers such as Farmak, Darnitsa, Arterium, Yuria-Pharm, and Zdorovye — rather than clinical trial pipeline management.

This section presents the platform's eight-module pipeline architecture, data contracts, algorithmic specifications, and technology stack, referencing the production implementation throughout.

## **2.2.1 System Architecture Overview**

### **Eight-Module Pipeline**

HPF-P implements the diagnostic-gated analytical pipeline introduced in Section 2.2 of the HPF framework as a sequential eight-module computation:

```
Input(CSV + JSON) → M1 Ingest → M2 DRI/DRL → M3 ML Forecast → M4 Multi-Strategy Optimise → M5 Monte Carlo → M5b Time-Series Simulation → M6 Output Assembly
```

Each module receives the outputs of its predecessors and produces structured diagnostics alongside its primary results. The pipeline is designed such that each transition is *conditional*: modules M3 through M6 operate only on SKUs that have passed the diagnostic validation of M1 and M2. This architectural constraint directly implements the HPF principle that optimisation is a *permitted action* contingent upon diagnostic adequacy, not an automatic procedure.

The modules are:

- **M1 — Data Ingestion and Validation:** Parses input data, validates schema compliance, cross-references SKU identifiers between data sources, imputes missing values, and computes per-SKU quality flags.
- **M2 — DRI Computation and DRL Assignment:** Evaluates five diagnostic dimensions for each SKU and assigns Decision Readiness Levels that govern downstream analytical permissibility.
- **M3 — ML Estimation Module:** Fits demand forecasting models with Fourier seasonal features, estimates price elasticity via log-log regression, and computes per-SKU risk scores.
- **M4 — Multi-Strategy Portfolio Optimisation:** Generates portfolio weights under eight distinct strategies and selects the best-performing strategy via rapid Monte Carlo evaluation.
- **M5 — Monte Carlo Simulation Engine:** Executes 1,000-iteration stochastic simulation to produce portfolio-level risk metrics including VaR-95 and CVaR-95.
- **M5b — Time-Series Simulation:** Projects 12-month revenue trajectories across 500 simulation paths for three scenarios (historical, baseline, HPF-optimised) with percentile bands and economic comparison metrics.
- **M6 — Output Assembly:** Aggregates all module outputs into a structured response with per-SKU justifications, portfolio metrics, strategy comparisons, and a narrative summary.

### **Deployment Topology**

HPF-P operates as a three-tier web application deployed on a single Linux server:

1. **Backend API:** A FastAPI application (Python 3.12) running as a systemd service (hpf-app) on port 8901. The API exposes three endpoints: /api/health (liveness check), /api/sample (demonstration data), and /api/analyze (the full pipeline).
2. **Frontend presentation layer:** An inline WordPress page served via the hpf-project.php mu-plugin, which provides styling, scenario management, interactive controls, and Chart.js-based visualisation. Predefined scenario data for five Ukrainian pharmaceutical companies is delivered via /wp-content/uploads/hpf-samples.js.
3. **Reverse proxy:** Apache HTTP Server proxies requests from the /hpf/ URL path to localhost:8901, providing TLS termination, access logging, and integration with the broader research portal.

This topology enables HPF-P to function simultaneously as a research instrument and a demonstration platform accessible to non-technical stakeholders through a standard web browser.


## **2.2.2 Data Layer: Contracts, Validation, and Imputation**

The data layer implements strict input contracts that enforce structural consistency before any analytical computation proceeds. HPF-P accepts two complementary inputs: a time-series CSV file containing transactional observations and a JSON metadata document describing SKU-level characteristics and portfolio constraints.

### **CSV Data Contract**

The CSV input follows a columnar schema with four required fields and two optional fields:

| Column | Type | Required | Description |
|:---|:---|:---:|:---|
| date | ISO 8601 | Yes | Month of observation |
| sku_id | string | Yes | Unique SKU identifier matching metadata keys |
| quantity | float | Yes | Units sold (>= 0) |
| revenue | float | Yes | Revenue in UAH |
| price | float | No | Unit price (derived as revenue/quantity if absent) |
| marketing_spend | float | No | Promotional expenditure |

### **Metadata JSON Contract**

The metadata document provides institutional and economic context that cannot be inferred from transaction data alone:

```json
{
  "company": "string",
  "currency": "UAH",
  "market_context": { "reimbursement_model": "string" },
  "portfolio_rules": { "default_min_weight": 0.0, "default_max_weight": 0.35 },
  "skus": {
    "SKU_ID": {
      "status": "active|discontinuing",
      "demand": {
        "historical_coverage_ratio": "[0.0, 1.0]",
        "observability": "high|medium|low"
      },
      "economics": {
        "gross_margin": "[0.0, 1.0]",
        "price_elasticity": "float"
      },
      "allocation_bounds": { "min": "float", "max": "float" }
    }
  }
}
```

This dual-input architecture reflects a fundamental design principle: transactional data provides *what happened*, while metadata encodes *what is known about the decision environment*. The separation allows the DRI computation to diagnose discrepancies between claimed and observed data quality.

### **Validation Pipeline**

Module M1 performs the following validation and preparation steps:

1. **Schema validation:** Required columns are verified; their absence triggers an HTTP 400 error with field-level diagnostics.
2. **Cross-referencing:** SKU identifiers in the CSV are intersected with metadata keys. Only SKUs present in *both* sources proceed through the pipeline, ensuring that every analysed SKU has both observational and institutional characterisation.
3. **Type coercion:** Date fields are parsed via pd.to_datetime with error coercion; numeric fields are converted via pd.to_numeric. Invalid entries become NaN values subject to imputation.
4. **Imputation:** Missing values in quantity and revenue are filled using three-stage interpolation: linear interpolation across the time series, forward fill for leading gaps, and backward fill for trailing gaps. This conservative approach preserves observed trends while minimising the introduction of synthetic variance.
5. **Quality flagging:** For each SKU, the raw missingness ratio is computed as ρ_miss = n_missing / (2 · n_obs), where the denominator accounts for both quantity and revenue columns. SKUs with ρ_miss < 0.20 receive a quality flag of OK; those exceeding this threshold are flagged as DATA_QUALITY=POOR.

Critically, the raw missingness ratios are preserved *prior to imputation* and passed to Module M2 for use in DRI computation. This design ensures that the DRI reflects actual data availability rather than post-imputation completeness — a distinction that directly implements the HPF principle that data absence is an informational signal, not merely a technical defect to be corrected.


## **2.2.3 DRI Computation Engine**

Module M2 computes the Decision Readiness Index for each SKU as a weighted composite of five diagnostic dimensions, each measuring a distinct aspect of informational adequacy for portfolio decision-making.

### **DRI Formula**

The DRI for SKU *s* is defined as:

**DRI(s) = w₁·R₁(s) + w₂·R₂(s) + w₃·R₃(s) + w₄·R₄(s) + w₅·R₅(s)**

where the weights are:

| Dimension | Symbol | Weight | Interpretation |
|:---|:---:|:---:|:---|
| Data Completeness | R₁ | 0.25 | Observability of key economic variables |
| Demand Signal Strength | R₂ | 0.25 | Identifiability of market response |
| Tail Risk Observability | R₃ | 0.20 | Visibility of downside outcomes |
| Regulatory / Constraint Feasibility | R₄ | 0.15 | Institutional stability and compliance |
| Temporal Stability | R₅ | 0.15 | Preservation of economic relationships over time |

Each dimension R_i ∈ [0, 1], and consequently DRI ∈ [0, 1].

### **Dimension Specifications**

**R₁ — Data Completeness.** This dimension takes the more pessimistic of two completeness indicators:

R₁(s) = min(1 − ρ_miss(s), metadata_coverage(s))

where ρ_miss is the raw missingness ratio computed in M1 (before imputation) and metadata_coverage is the historical_coverage_ratio declared in the metadata. By taking the minimum, the system ensures that neither self-reported metadata nor observed completeness alone can inflate the completeness assessment.

**R₂ — Demand Signal Strength.** The coefficient of variation (CV) of observed demand serves as the base measure, with a penalty for heavy imputation:

CV_eff(s) = CV(s) + min(2ρ_miss, 1) · 0.5

R₂(s) = clip(1 − CV_eff(s), 0, 1)

The missingness penalty addresses a subtle but important bias: linear interpolation during imputation artificially reduces observed variance, which would overstate demand signal strength if the raw CV were used. The penalty term re-introduces uncertainty proportional to the degree of imputation.

**R₃ — Tail Risk Observability.** This dimension quantifies whether the lower tail of the demand distribution is observable:

R₃(s) = 0.5 + 0.5 · tanh(2 · (1 − τ_frac(s)))

where τ_frac is the fraction of observations below the 10th percentile of quantity. The hyperbolic tangent transformation maps this fraction into a smooth score that is insensitive to outliers while penalising heavy-tailed distributions where downside risk cannot be reliably assessed.

**R₄ — Regulatory and Constraint Feasibility.** This dimension integrates three institutional signals:

- *Observability mapping:* high → 1.0, medium → 0.65, low → 0.35
- *Status adjustment:* SKUs with status = "discontinuing" receive a 0.15 penalty
- *Reimbursement bonus:* Public reimbursement models add 0.10 (reflecting greater price transparency)

R₄(s) = clip(obs_map(s) + status_adj(s) + reimb_adj(s), 0, 1)

**R₅ — Temporal Stability via Chow Test.** Structural breaks in the demand series are detected using the Chow test applied at annual segment boundaries. For a time series of *n* observations with potential breakpoints at t = 12k (where k = 1, 2, …), the test computes:

F = ((RSS_full − RSS_restricted) / k) / (RSS_restricted / (n − 2k))

where RSS_full is the residual sum of squares from the pooled regression and RSS_restricted = RSS₁ + RSS₂ from segment-specific regressions. A breakpoint is declared significant at p < 0.05. The temporal stability score is then:

R₅(s) = 1 − n_breaks / n_breakpoints

For series too short to support breakpoint analysis (fewer than 6 observations), a default value of R₅ = 0.85 is assigned — a conservative assumption that acknowledges limited temporal evidence without excessively penalising new SKUs.

### **DRL Assignment**

The computed DRI score maps to one of five Decision Readiness Levels via threshold classification:

| DRL | DRI Range | Permitted Strategy | Economic Interpretation |
|:---:|:---|:---|:---|
| 1 | < 0.25 | ABSTAIN_HOLD | Insufficient information; preserve status quo |
| 2 | [0.25, 0.45) | REVENUE_PROPORTIONAL | Minimal optimisation; proportional allocation |
| 3 | [0.45, 0.65) | CONSTRAINED_LP | Linear programming with hard constraints |
| 4 | [0.65, 0.80) | CVaR_MV | Mean-variance with risk controls |
| 5 | >= 0.80 | MULTI_OBJECTIVE_ML | Full multi-objective optimisation |

This mapping directly operationalises the HPF principle of conditional analytical permissibility: the complexity of the optimisation method applied to each SKU is bounded by the quality of information available about that SKU.


## **2.2.4 ML Estimation Module**

Module M3 provides the statistical estimates required by the optimisation and simulation modules. For each SKU, it produces four outputs: demand forecasts, price elasticity estimates, risk scores, and per-SKU revenue projection series.

### **Demand Forecasting with Fourier Features**

Demand is modelled as a linear trend augmented with Fourier seasonal components at period 12 (monthly cycle):

q_t = β₀ + β₁t + Σ_{k=1}^{2} [α_k sin(2πkt/12) + γ_k cos(2πkt/12)] + ε_t

This specification captures both linear growth/decline trends and the first two harmonics of annual seasonality. The model is estimated via ordinary least squares (OLS) using the statsmodels library. Twelve-month-ahead forecasts are generated by evaluating the fitted model at t = n, n+1, …, n+11, with 95% confidence intervals obtained from the prediction distribution.

The choice of Fourier features over ARIMA or more complex time-series models reflects a deliberate trade-off aligned with HPF principles. Fourier-augmented linear models are:

- **Interpretable:** Each coefficient has a direct physical meaning (trend slope, seasonal amplitude, seasonal phase).
- **Robust to short series:** The model requires only 2K + 2 = 6 parameters for K = 2 harmonics, enabling reliable estimation even with 18–24 monthly observations.
- **Stable under imputation:** Unlike autoregressive models that propagate imputation artefacts through lagged terms, Fourier models treat each observation independently.

### **Price Elasticity Estimation**

Price elasticity is estimated via log-log OLS regression:

ln(q_t) = α + η·ln(p_t) + ε_t

where η is the price elasticity of demand. The estimation is attempted only when sufficient price variation exists (standard deviation > 10⁻⁴) and at least 6 observations are available. When these conditions are not met, the system falls back to the metadata-provided elasticity value — a practical application of the DRI principle that estimation should not be attempted when data conditions are insufficient.

### **Risk Scoring**

Each SKU receives a composite risk score combining two indicators:

risk(s) = 0.5 · volatility(s) + 0.5 · tail_ratio(s)

where:
- volatility is the mean of rolling 12-month revenue coefficient of variation
- tail_ratio is |CVaR₉₅| / |r̄| — the ratio of the 5th-percentile revenue to mean revenue

This dual construction captures both *dispersion risk* (how much revenue fluctuates) and *tail risk* (how severe the worst outcomes are relative to the average).


## **2.2.5 Multi-Strategy Portfolio Optimisation**

Module M4 implements a competitive multi-strategy approach to portfolio weight determination. Rather than committing to a single optimisation methodology, the platform generates portfolio weights under eight distinct strategies and selects the best performer via empirical evaluation. This design reflects the No Free Lunch theorem and the HPF recognition that no single optimisation approach dominates across all data conditions.

### **Strategy Catalogue**

The eight strategies span a spectrum from naive baselines to sophisticated multi-objective formulations:

**1. Equal-Weight.** The 1/N baseline:

w_s^EW = 1/N for all s

This strategy serves as the benchmark against which all others are evaluated. Its inclusion is not trivial: DeMiguel et al. (2009) demonstrated that 1/N portfolios frequently outperform optimised portfolios when estimation error dominates.

**2. DRL-Grouped.** The original HPF strategy from Section 2.1, where each DRL group receives a budget proportional to its aggregate profit potential, and within-group allocation follows the DRL-specific strategy (hold for DRL-1, revenue-proportional for DRL-2, constrained LP for DRL-3, CVaR/MV for DRL-4, multi-objective for DRL-5). This is the only strategy that directly implements diagnostic gating.

**3. Momentum.** Weights proportional to the cubed ratio of forecast to historical demand:

w_s^Mom ∝ (q̂_s / q̄_s)³

The cubic exponent concentrates allocation on SKUs exhibiting strong growth trends, reflecting the empirical observation that pharmaceutical demand momentum tends to persist due to physician prescribing inertia and formulary lock-in effects.

**4. DRI-Weighted.** Allocation proportional to the squared DRI score, scaled by a DRL-dependent multiplier:

w_s^DRI ∝ m(DRL_s) · DRI(s)²

where m(·) ∈ {0.02, 0.2, 1.0, 2.5, 5.0} for DRL levels 1 through 5. This strategy rewards informational adequacy: SKUs with higher decision readiness receive disproportionately larger allocations.

**5. Risk-Parity.** Inverse-volatility weighting:

w_s^RP ∝ 1 / max(σ_s, 0.02)

This strategy equalises risk contribution across SKUs, providing a hedge against concentration risk in volatile pharmaceutical markets.

**6. Profit-Maximiser.** Squared profit potential:

w_s^PM ∝ (margin_s · q̂_s)²

By squaring the profit potential, this strategy aggressively concentrates on top-performing SKUs — appropriate when the portfolio manager prioritises expected return over diversification.

**7. Mean-Variance.** Return-to-variance ratio:

w_s^MV ∝ max(0.01, (r_s + 0.1) / σ_s²)

where r_s is the forecast return relative to historical mean. The additive constant 0.1 prevents negative or zero weights for declining SKUs while maintaining the variance-penalised structure.

**8. HPF-Ensemble.** The arithmetic mean of all non-equal strategies:

w_s^Ens = (1/6) · Σ_{k ∈ {Mom, DRI, RP, PM, MV, DRL}} w_s^(k)

This ensemble approach provides natural diversification across optimisation philosophies, reducing the risk of any single strategy's failure mode dominating.

### **Strategy Selection via Monte Carlo Evaluation**

After generating all eight weight vectors, the platform evaluates each strategy through a rapid 200-iteration Monte Carlo simulation. For each iteration, demand and price are sampled from normal distributions centred on forecast values, and the total expected portfolio revenue is computed:

R_total^(k) = Σ_{i=1}^{200} Σ_s w_s^(k) · margin_s · q̃_{s,i} · p̃_{s,i}

The strategy with the highest total expected revenue is selected as the recommended allocation. This empirical competition replaces *a priori* strategy selection with data-driven performance evaluation, ensuring that the chosen approach is demonstrably superior under the current data conditions.

All strategy scores are preserved in the output diagnostics, enabling the portfolio manager to inspect the competitive landscape and understand how close alternative strategies performed.


## **2.2.6 Monte Carlo Simulation Engine**

Modules M5 and M5b provide stochastic evaluation of the selected portfolio through two complementary simulation frameworks.

### **Portfolio-Level Risk Simulation (M5)**

The primary Monte Carlo engine executes 1,000 iterations to produce portfolio-level risk metrics. Each iteration proceeds as follows:

1. **Demand sampling:** q̃_s ~ N(q̂_s, σ̂_{q,s}), clipped at zero
2. **Price sampling:** p̃_s ~ N(p̄_s, 0.05·p̄_s), clipped at 10⁻⁹
3. **Portfolio return:** R̃ = Σ_s w_s · margin_s · q̃_s · p̃_s

From the empirical distribution of {R̃_i}_{i=1}^{1000}, the platform computes:

- **VaR-95:** The 5th percentile of portfolio returns
- **CVaR-95:** E[R̃ | R̃ ≤ VaR₉₅] — the expected return conditional on being in the worst 5% of outcomes
- **Return distribution statistics:** Mean, standard deviation, P5, P95

### **Deterministic vs. Stochastic Modes**

HPF-P supports two reproducibility modes controlled by the deterministic flag in the API request:

- **Deterministic mode** (default): The pseudo-random number generator (PRNG) is seeded with a fixed base seed of 42. Each iteration *i* uses seed 42 + i, guaranteeing identical outputs for identical inputs across runs. This mode supports auditable, reproducible analysis.
- **Stochastic mode:** A random base seed is generated per run via numpy.random.default_rng().integers(0, 2³¹). Each iteration then uses base + i, ensuring within-run reproducibility (same relative perturbations) while producing different results across runs. This mode enables sensitivity analysis and robustness testing.

### **Time-Series Revenue Simulation (M5b)**

The time-series simulation engine projects 12-month revenue trajectories across three scenarios:

1. **Historical:** Actual observed monthly portfolio revenue (no simulation)
2. **Baseline (Equal-Weight):** Revenue under 1/N allocation, simulated across 500 paths
3. **HPF-Optimised:** Revenue under the selected strategy weights, simulated across 500 paths

For each simulated path, monthly SKU-level revenue is sampled from the Fourier forecast distributions and aggregated using the respective weight vectors. A calibration step scales both simulated scenarios to match the last observed historical revenue value, ensuring visual and numerical comparability.

The prediction line is the **median (P50)** across simulation paths — chosen over the mean for its robustness to outliers. Uncertainty bands are reported at four percentile levels: **P10, P25, P75, and P90**, providing a comprehensive view of the distribution tails.

### **Economic Comparison Metrics**

Module M5b computes a rich set of economic comparison metrics between the baseline and HPF scenarios:

- **Sharpe ratio:** Annualised excess return per unit of total volatility, computed from month-over-month returns with a 0.5% monthly risk-free rate proxy (reflecting NBU policy rates)
- **Sortino ratio:** Annualised excess return per unit of downside deviation, penalising only negative returns
- **Calmar ratio:** Annualised return divided by maximum drawdown, measuring return per unit of peak-to-trough loss
- **VaR-95 and CVaR-95:** Computed on total horizon revenue across all simulation paths
- **Maximum drawdown:** Median per-path maximum drawdown, avoiding the mean-path smoothing bias
- **Probability of outperformance:** Fraction of simulation paths where HPF total revenue exceeds baseline total revenue
- **Breakeven month:** First month where mean HPF revenue consistently exceeds mean baseline revenue
- **Revenue gain percentage:** (R_HPF − R_baseline) / R_baseline × 100


## **2.2.7 Client-Side Scenario Engine**

In addition to the server-side API, HPF-P includes a browser-based scenario engine that provides immediate, zero-latency portfolio analysis for predefined Ukrainian pharmaceutical company scenarios. This client-side component serves both a pedagogical function — enabling stakeholders to explore DRI/DRL concepts interactively — and a practical demonstration function, showcasing the platform's capabilities without requiring data upload.

### **Predefined Company Scenarios**

Five scenarios model stylised Ukrainian pharmaceutical manufacturers with distinct portfolio characteristics:

| Company | SKUs | Volatility Profile | Growth Trend | Design Rationale |
|:---|:---:|:---|:---|:---|
| Farmak | 18 | Low | Moderate | Market leader; stable, diversified portfolio |
| Darnitsa | 15 | Low | Moderate | Top-3 manufacturer; generic-heavy portfolio |
| Arterium | 16 | Medium | Moderate | Mid-market with therapeutic diversification |
| Yuria-Pharm | 14 | Medium | High | Growth-oriented infusion/injectable specialist |
| Zdorovye (Kharkiv) | 12 | Extreme | Negative | War-affected manufacturer; structural disruption |

The Zdorovye scenario is particularly significant: it models a manufacturer operating in a conflict zone (Kharkiv), where extreme volatility, negative growth, and structural breaks are the norm. This scenario stress-tests the DRI framework's ability to correctly identify situations where optimisation should be *withheld* rather than applied — the ABSTAIN_HOLD outcome that Section 2.1 identified as a fundamental contribution of HPF.

### **Synthetic Data Generation**

Each scenario generates synthetic time-series data using a tiered SKU model:

- **Stars (~30%):** High growth rate, low volatility — representing established blockbuster products
- **Stable (~40%):** Moderate growth, moderate volatility — the portfolio backbone
- **Declining (~30%):** Negative growth, high volatility — products approaching end-of-lifecycle or facing generic competition

For each SKU, monthly quantity data is generated as:

q_t = base · (1 + g)^{t/12} · (1 + A·sin(2πt/12 + φ)) + ε_t

where g is the annual growth rate, A is the seasonal amplitude, φ is the seasonal phase, and ε_t ~ N(0, σ²) represents noise. The noise level σ varies by company scenario, producing the distinct volatility profiles described above.

### **Client-Side DRI Computation**

The browser engine implements the same R₁–R₅ DRI formula as the server, using the Mulberry32 seeded PRNG for deterministic reproducibility:

```javascript
function mulberry32(seed) {
    return function() {
        seed |= 0; seed = seed + 0x6D2B79F5 | 0;
        let t = Math.imul(seed ^ seed >>> 15, 1 | seed);
        t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t;
        return ((t ^ t >>> 14) >>> 0) / 4294967296;
    }
}
```

In deterministic mode, the PRNG is seeded with 42 + idx × 1000 (where idx is the scenario index), ensuring identical results across browser sessions. In stochastic mode, the seeded PRNG generates data while Math.random() drives Monte Carlo sampling, providing controlled stochasticity.

The client-side engine implements six rebalancing strategies: DRL-Weighted, Momentum, Mean-Variance, Risk-Parity, Growth-DRI, and HPF-Ensemble — a subset of the server-side eight strategies adapted for browser execution performance.


## **2.2.8 Technology Stack**

HPF-P is built on an open-source scientific computing stack selected for mathematical rigour, audit transparency, and deployment simplicity.

### **Backend: Python Scientific Computing**

| Library | Version | Role in HPF-P |
|:---|:---|:---|
| **FastAPI** | 0.100+ | Asynchronous HTTP API framework with automatic OpenAPI documentation |
| **NumPy** | 1.26+ | Array operations, random number generation, statistical computations |
| **Pandas** | 2.1+ | Time-series data management, CSV parsing, group-by aggregations |
| **SciPy** | 1.11+ | Statistical distributions (scipy.stats), linear programming (scipy.optimize.linprog) |
| **statsmodels** | 0.14+ | OLS regression, Fourier-augmented demand models, Chow test implementation |
| **CVXPY** | 1.4+ | Convex optimisation for CVaR/MV (DRL-4) and multi-objective (DRL-5) problems |
| **Pydantic** | 2.0+ | Request/response validation and serialisation |

The choice of CVXPY with the SCS solver for portfolio optimisation reflects a design priority for *mathematical guarantees*: SCS provides convergence certificates for second-order cone programs, ensuring that the optimisation results are either optimal (within numerical tolerance) or explicitly flagged as infeasible. This is critical for the HPF framework's requirement that every analytical step be auditable.

### **Frontend: Browser-Based Visualisation**

| Technology | Role |
|:---|:---|
| **Chart.js** | Interactive portfolio visualisation: revenue trajectories, weight distributions, DRI bar charts, delta comparison bars, DRL donut charts, per-SKU forecast plots |
| **WordPress** | Content management, user authentication, page templating via hpf-project.php mu-plugin |
| **Vanilla JavaScript** | Scenario engine, DRI computation, seeded PRNG, UI state management |
| **CSS @media print** | PDF export via window.print() with print-optimised layouts |

### **Integration Architecture**

The platform integrates with the broader research infrastructure through:

- **Apache reverse proxy:** Maps /hpf/ to the FastAPI backend, enabling co-location with the research portal
- **WordPress mu-plugin system:** The hpf-project.php plugin injects styles, scripts, and the scenario engine without modifying the WordPress core
- **Static file serving:** FastAPI serves the interactive frontend from /opt/hpf-app/static/, with scenario data loaded from /wp-content/uploads/hpf-samples.js
- **CSV/JSON download:** Analysis results can be exported for offline processing or integration with external tools

### **Reproducibility and Auditability**

Every analysis run produces a unique run_id (UUID v4) and UTC timestamp, enabling complete audit trails. The deterministic mode ensures that identical inputs produce identical outputs across runs, supporting regulatory compliance and peer review. Module-level diagnostics expose intermediate computations, allowing reviewers to trace any portfolio recommendation back through the diagnostic pipeline to the raw input data.

---

**Summary.** The HPF-P platform architecture translates the theoretical DRI/DRL framework into a production-ready decision-support system. Its eight-module pipeline enforces diagnostic gating at every stage, its multi-strategy optimisation approach empirically selects the best-performing allocation method, and its dual-mode simulation engine provides both reproducible analysis and sensitivity testing. The platform demonstrates that the HPF principle — that optimisation is an economically justified action only under diagnostically confirmed informational conditions — can be operationalised in a practical, deployable system for Ukrainian pharmaceutical portfolio management.
