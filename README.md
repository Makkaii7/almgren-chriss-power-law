# Optimal Execution with Non-Linear (Power-Law) Market Impact

**Authors:** Ali Almehairbi, Mohamed Alhmoudi
**Course:** CODS 612 — Computational Methods and Optimization in Finance, Spring 2026

---

## Project Summary

This project implements and compares two optimal-execution models for liquidating a large equity position over a finite trading horizon. The classical Almgren-Chriss framework assumes linear temporary market impact, yielding a closed-form Quadratic Program. Empirical microstructure research — the so-called "Square Root Law" — shows that real impact follows a power law with a fractional exponent (typically β ≈ 0.5–0.6). We drop the linear assumption, solve the resulting non-linear convex problem numerically, and quantify how much execution cost the naive linear strategy leaves on the table when reality follows power-law dynamics.

For the canonical parameter set (1M shares, N=50 half-hour bins, β=0.6) the linear strategy costs **$1,336 more than the power-law optimum (a 1.47% gap)**. The gap grows sharply when impact becomes more concave: at **β=0.3 the gap reaches 157%**, and along the risk-aversion axis it reaches **~40× (3,901%) at κ=1**, where κ = √(γσ²/η) is the dimensionless concentration parameter from Almgren-Chriss. Methodologically, the solver was switched from `scipy.optimize` SLSQP to CVXPY after a side-by-side verification showed SLSQP was returning sub-optimal trajectories at low β; CVXPY recovers the verified-best objective and is now the primary solver in all comparison and sweep code.

---

## Repository Structure

```
almgren-chriss-power-law/
├── ali/
│   └── linear_baseline.py          Linear Almgren-Chriss QP (closed-form + CVXPY)
├── mohamed/
│   └── power_law_extension.py      Power-law extension (SLSQP non-linear solver)
├── combined/
│   ├── verify_cvxpy.py             SLSQP vs CVXPY side-by-side verification
│   ├── comparison.py               Trajectory/cost comparison + β-sweep
│   ├── kappa_sweep.py              Cost-gap vs κ = √(γσ²/η) sweep
│   ├── cvxpy_trajectories.npz      Cached CVXPY-optimal trajectories
│   └── kappa_sweep_results.npz     Cached κ-sweep data
├── presentation/
│   ├── rebuild_report.py           Generates report.docx and report.pdf
│   ├── report.docx                 Final written report (Word)
│   └── report.pdf                  Final written report (PDF)
├── figures/                        All generated charts (PNG)
├── Project 1.pdf                   Original assignment specification
├── README.md
├── requirements.txt
└── .gitignore
```

---

## Required Python Packages

- `numpy` — numerics
- `scipy` — SLSQP non-linear solver
- `cvxpy` — primary convex solver (via Clarabel/SCS)
- `matplotlib` — figures
- `python-docx` — DOCX report generation
- `reportlab` — PDF report generation

Pinned versions are in `requirements.txt`.

---

## Installation

```bash
pip install -r requirements.txt
```

Python 3.10+ recommended.

---

## How to Reproduce All Results

Run the scripts in this order from the repository root:

1. **Linear baseline** — solves the linear QP and writes baseline figures.
   ```bash
   python ali/linear_baseline.py
   ```

2. **Power-law extension** — solves the β=0.6 problem with SLSQP and writes power-law figures.
   ```bash
   python mohamed/power_law_extension.py
   ```

3. **Solver verification** — runs SLSQP vs CVXPY across β ∈ [0.3, 1.0] and caches the verified-best CVXPY trajectories to `combined/cvxpy_trajectories.npz`.
   ```bash
   python combined/verify_cvxpy.py
   ```

4. **Comparison and β-sweep** — produces the trajectory comparison, cost-mismatch table, and the cost-gap-vs-β sensitivity plot.
   ```bash
   python combined/comparison.py
   ```

5. **κ-sweep** — sweeps the dimensionless risk-aversion parameter κ = √(γσ²/η) and produces the cost-gap-vs-κ plots.
   ```bash
   python combined/kappa_sweep.py
   ```

6. **Build the report** — assembles all numbers and figures into `presentation/report.docx` and `presentation/report.pdf`.
   ```bash
   python presentation/rebuild_report.py
   ```

All figures are written to `figures/`. Steps 3 and 5 cache `.npz` files used by later steps.

---

## Headline Results

| Sweep / scenario | Cost gap of linear strategy under power-law impact |
|---|---|
| Baseline (β = 0.6) | **$1,336 (1.47%)** |
| Most concave impact tested (β = 0.3) | **157%** |
| Most risk-averse tested (κ = 1) | **~40× (3,901%)** |

These confirm that the linear Almgren-Chriss prescription is acceptable in the calm-market / mildly-concave regime but degrades catastrophically once impact becomes strongly concave or the trader is highly risk-averse — exactly the regimes where execution quality matters most.

---

## Methodology Note: SLSQP → CVXPY

The first implementation used `scipy.optimize.minimize` with SLSQP for the non-linear power-law problem. The verification script (`combined/verify_cvxpy.py`) showed SLSQP terminating at sub-optimal points for small β: at β=0.4 the SLSQP objective was 23.6% worse than the CVXPY optimum, and at β=0.3 SLSQP failed to converge entirely. CVXPY (which canonicalises the fractional power into a sequence of second-order cone constraints) returns a tighter optimum at every β tested, and at β=1.0 it matches the linear closed-form solution to ~3×10⁻⁶ relative error. All comparison and sensitivity analyses therefore use the CVXPY-verified trajectories. SLSQP is retained in `mohamed/power_law_extension.py` to document the original approach and the verification gap that motivated the pivot.
