# HPF-P Chapter 4 — Promotion Package

## Status: DRAFT — DO NOT PUBLISH YET

## WordPress URL (private)
https://hub.stabilarity.com/?p=1255

---

## Article Summary (for community posts)

Chapter 4 of Oleh Ivchenko's PhD dissertation presents the HPF-P platform — a production decision-support system for pharmaceutical SKU portfolio management that operationalises the Decision Readiness Index (DRI) and Decision Readiness Levels (DRL) into an executable, auditable analytical pipeline. Unlike conventional portfolio optimisation tools that assume data sufficiency, HPF-P first *diagnoses* informational readiness and gates analytical complexity accordingly: only data-rich SKUs receive sophisticated multi-objective optimisation, while information-poor SKUs receive honest ABSTAIN_HOLD recommendations instead of spurious outputs. Experimental validation on real Darnitsa and Farmak datasets demonstrates that HPF-optimised portfolios outperform equal-weight baselines in 82–91% of simulation paths with 10–14% annual revenue gains.

---

## Key Findings

- **Darnitsa (15 SKUs, 31 months):** HPF-P generated +UAH 10.15M annual revenue gain (+10.18% over equal-weight baseline), with Sharpe ratio improving 74.1% (0.49 → 0.85), maximum drawdown cut by 50.1% (18.25% → 9.11%), and 82.4% probability of outperformance across 500 simulation paths — breakeven from month 1.
- **Farmak (18 SKUs, 31 months):** HPF-P generated +UAH 18.46M annual revenue gain (+13.72%), Sharpe ratio +57.2% (0.56 → 0.88), CVaR₉₅ tail-risk reduced 33.8%, and 91.5% probability of outperformance across 500 paths — demonstrating robust superiority even in a low-volatility portfolio.
- **DRI-gated strategy selection works:** 93.3% of Darnitsa SKUs qualified for DRL-5 full multi-objective optimisation; Farmak's 3 DRL-4 SKUs received 3.31% vs 16.67% equal-weight — the 13.4pp reallocation away from informationally constrained positions is the primary mechanism generating economic improvement.

---

## Target Communities

1. **Zenodo** — register DOI first, then post to open science community
2. **ResearchGate** — post preprint link after DOI registration
3. **Academia.edu** — share research profile page
4. **LinkedIn** — professional post (Oleh Ivchenko profile)
5. **Ukrainian academic networks** — ONPU channels, Ukrainian Economic Association
6. **r/MachineLearning** — methodology is solid (Fourier demand forecasting, CVXPY, Monte Carlo, diagnostic gating)
7. **Hacker News** — "Show HN: Decision Readiness Framework for Pharma Portfolio Optimisation"
8. **ResearchHub** — open science community, coin rewards for engagement

---

## Draft LinkedIn Post

🔬 **New research: What if your portfolio optimiser knew when NOT to optimise?**

I'm excited to share Chapter 4 of my PhD dissertation — the experimental validation of **HPF-P**, a decision-support platform for pharmaceutical portfolio management that I built and tested on real Ukrainian market data from Darnitsa and Farmak.

The core idea: instead of assuming your data is good enough for optimisation, the system *diagnoses* data quality first. Only SKUs with sufficient informational readiness receive sophisticated allocation recommendations. SKUs with poor data get an honest "ABSTAIN_HOLD" — a documented scientific result, not a failure. This is what I call **Decision Readiness Economics**: analytical complexity bounded by informational readiness.

The results from 500-path Monte Carlo simulation: Darnitsa portfolio achieved **+10.2% annual revenue** over equal-weight baseline with Sharpe ratio +74% and drawdown cut by 50%. Farmak achieved **+13.7% revenue gain** with 91.5% probability of outperformance. The platform earned its keep not by adding risk, but by reducing it — and by being honest about what it doesn't know. Full chapter at: [link] | DOI: pending | Feedback welcome.

---

## Draft Tweet/X Thread

**Tweet 1:**
🧵 I built a pharmaceutical portfolio optimiser that refuses to optimise when it shouldn't. Here's why that's actually the right call, and the numbers behind it: (1/5)

**Tweet 2:**
Traditional portfolio tools assume your data is ready. HPF-P measures readiness first. Each drug SKU gets a Decision Readiness Index (DRI ∈ [0,1]) — a weighted composite of data completeness, demand signal quality, tail risk observability, regulatory coverage, and temporal stability. Low DRI = ABSTAIN. (2/5)

**Tweet 3:**
Validated on Darnitsa (15 SKUs) & Farmak (18 SKUs) — major Ukrainian pharma companies. Using Fourier demand forecasting + CVXPY optimisation + 1000-iter Monte Carlo.
Results: 8 competing strategies evaluated, best selected empirically per dataset. (3/5)

**Tweet 4:**
Numbers:
📊 Darnitsa: +10.2% revenue, Sharpe +74%, drawdown -50%, 82.4% outperformance
📊 Farmak: +13.7% revenue, Sharpe +57%, CVaR₉₅ risk -33.8%, 91.5% outperformance
Both: breakeven month 1. 500 simulation paths each. (4/5)

**Tweet 5:**
The key insight: **informational adequacy is a precondition for optimisation validity, not an assumption**. A portfolio tool that produces outputs regardless of data quality is making things up. HPF-P doesn't.
PhD preprint coming soon — DOI pending Zenodo registration. #MachineLearning #Pharma #PortfolioOptimisation (5/5)

---

## Zenodo Metadata (ready to register)

- **Title:** HPF-P Chapter 4: Experimental Validation and Comparative Analysis of the Decision Readiness Framework for Pharmaceutical Portfolio Management
- **Authors:** Ivchenko, Oleh
- **Affiliation:** Odessa National Polytechnic University (ONPU), Department of Economic Cybernetics
- **Keywords:** pharmaceutical portfolio management, Decision Readiness Index, DRI, portfolio optimisation, machine learning in economics, Ukrainian pharmaceuticals, Farmak, Darnitsa, Monte Carlo simulation, Fourier demand forecasting, CVXPY, decision support systems
- **Description:** This chapter presents the production implementation of the HPF-P (Holistic Portfolio Framework — Platform) decision-support system and its experimental validation on real pharmaceutical company data. The chapter introduces the Decision Readiness Index (DRI) as a computed precondition for portfolio optimisation: each SKU receives a DRI score measuring informational readiness across five dimensions (completeness, demand signal, tail risk, regulatory coverage, temporal stability), which maps to a Decision Readiness Level (DRL 1–5) that gates access to progressively sophisticated optimisation methods. Experimental results on Darnitsa (15 SKUs, 31 months) and Farmak (18 SKUs, 31 months) datasets demonstrate 10.18% and 13.72% annual revenue improvements over equal-weight baselines, with 82.4% and 91.5% outperformance probabilities across 500 Monte Carlo simulation paths respectively, alongside substantial improvements in Sharpe ratio, Sortino ratio, and tail-risk metrics.
- **License:** CC-BY-4.0
- **Resource type:** Preprint / Dissertation Chapter
- **Related identifiers:** (to be added — ONPU dissertation registration number)
- **Communities:** Machine Learning, Economics, Operations Research, Open Science

---

*Created by Yo AI assistant — 2026-03-06*
*Post is private (WP ID 1255). No DOI yet. Ready to publish when Doctor Yo gives the word.*
