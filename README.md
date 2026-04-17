# Optimal Execution with Non-Linear (Power-Law) Market Impact

This project implements and compares two optimal execution models for liquidating a large equity position. The classical Almgren-Chriss framework assumes linear temporary market impact, yielding a tractable Quadratic Program. However, empirical microstructure research—the "Square Root Law"—shows that impact follows a power law with a fractional exponent (typically beta ~ 0.5-0.6). We drop the linear assumption, solve the resulting non-linear convex optimization problem numerically, and quantify how much cost the naive linear model leaves on the table when reality follows power-law dynamics.

## Team

| Member  | Responsibility                          |
|---------|-----------------------------------------|
| **Ali** | Linear Almgren-Chriss Baseline (QP)     |
| **Mohamed** | Power-Law Extension (Non-linear solver) |

---

## Problem Formulation

### Notation

| Symbol | Definition |
|--------|-----------|
| N = 50 | Number of trading periods (half-hour bins) |
| x_k | Portfolio inventory remaining at time step k |
| v_k = x_{k-1} - x_k | Shares traded in period k |
| X = 1,000,000 | Initial inventory (x_0 = X) |
| x_N = 0 | Terminal constraint (full liquidation) |
| sigma = 0.02 | Daily volatility ($2 on a $100 stock) |
| gamma = 2.5e-6 | Risk aversion parameter |
| eta = 2.0e-4 | Temporary impact coefficient |

### Linear Model (Ali's Half)

The classical Almgren-Chriss objective with **linear temporary impact** (beta = 1.0):

```
min_x  sum_{k=1}^{N} [ eta * v_k^2  +  gamma * sigma^2 * x_k^2 ]
```

This is a standard **Quadratic Program (QP)**. The objective is quadratic in v_k and x_k, and the constraints (x_0 = X, x_N = 0, v_k = x_{k-1} - x_k) are linear. It admits a closed-form solution via the Euler-Lagrange equations or can be solved directly as a QP.

**There is NO permanent impact term.** Only temporary impact + risk penalty.

### Power-Law Model (Mohamed's Half)

The empirical power-law objective with **fractional exponent** (beta = 0.6):

```
min_x  sum_{k=1}^{N} [ eta * |v_k|^(1+beta)  +  gamma * sigma^2 * x_k^2 ]
```

Because of the absolute value and the fractional exponent (1 + beta = 1.6), this objective has **no closed-form solution** and must be solved using numerical convex optimization (e.g., `scipy.optimize.minimize` with SLSQP, or `cvxpy` with power cone constraints).

---

## Exact Parameters

```python
X     = 1_000_000    # shares to liquidate
N     = 50           # trading periods (half-hour bins)
sigma = 0.02         # daily volatility
gamma = 2.5e-6       # risk aversion
eta   = 2.0e-4       # temporary impact coefficient
beta_linear    = 1.0 # linear model exponent
beta_power_law = 0.6 # empirical power-law exponent
```

---

## Ali's Half — Linear Almgren-Chriss Baseline

**Directory:** `ali/linear_baseline.py`

**Responsibilities:**
1. Implement `set_params()` — the shared parameter interface used by both halves
2. Solve the linear QP to obtain the optimal inventory trajectory x_k
3. Compute the total execution cost under the linear model
4. Generate plots: inventory trajectory, trading rate, sensitivity to gamma

**Key functions:**
- `set_params(X, N, sigma, gamma, eta)` -> dict
- `optimal_trajectory_linear(params)` -> np.ndarray of x_k
- `compute_trade_list(trajectory)` -> np.ndarray of v_k
- `compute_cost_linear(trajectory, params)` -> float
- `plot_trajectory(trajectory, params, title)` -> figure
- `plot_trade_rate(trade_list, params, title)` -> figure

**Output format:** Array of inventory levels `[x_0, x_1, ..., x_N]` of length N+1, where `x_0 = X` and `x_N = 0`.

---

## Mohamed's Half — Power-Law Extension

**Directory:** `mohamed/power_law_extension.py`

**Responsibilities:**
1. Import `set_params()` from Ali's module to share the same parameters
2. Solve the non-linear convex optimization problem for beta = 0.6
3. Compute the total execution cost under the power-law model
4. Generate plots: power-law trajectory, sensitivity to beta values

**Key functions:**
- `objective_power_law(x_intermediate, params, beta)` -> float
- `optimal_trajectory_power_law(params, beta)` -> np.ndarray of x_k
- `compute_cost_power_law(trajectory, params, beta)` -> float
- `plot_trajectory_power_law(trajectory, params, beta, title)` -> figure

**Output format:** Same as Ali's — array `[x_0, x_1, ..., x_N]` of length N+1.

---

## How to Merge

Both halves produce trajectories in the **same format**: a NumPy array of length N+1 representing inventory levels from x_0 to x_N.

1. Ali writes `set_params()` which returns a parameter dictionary. Mohamed imports it.
2. Both `optimal_trajectory_linear()` and `optimal_trajectory_power_law()` return arrays of the same shape.
3. In `combined/comparison.py`, we import both trajectory functions and both cost functions, then:
   - Plot both trajectories on the same chart (Trajectory Comparison Plot)
   - Evaluate the linear trajectory under the power-law cost function (Cost Mismatch Analysis)
   - Run sensitivity analyses across beta and gamma

**Merge checklist:**
- [ ] Ali's `set_params()` is finalized and importable
- [ ] Both trajectory arrays have shape (N+1,) with x_0 = X and x_N = 0
- [ ] Both cost functions accept any trajectory (not just their own optimal)
- [ ] Combined plots saved to `figures/`

---

## Timeline

| Milestone | Deadline | Owner |
|-----------|----------|-------|
| Repo setup and stubs | Day 1 | Ali |
| Linear model implemented and tested | Day 3 | Ali |
| Power-law solver implemented and tested | Day 4 | Mohamed |
| Sanity check: beta=1.0 power-law matches linear | Day 4 | Mohamed |
| Combined comparison plots and cost analysis | Day 5 | Both |
| Sensitivity analyses (beta, gamma sweeps) | Day 6 | Both |
| Written report draft (5-6 pages) | Day 8 | Both |
| Presentation slides (10 min) | Day 9 | Both |
| Final review and submission | Day 10 | Both |

---

## Deliverables Checklist

- [ ] **Written Report** (5-6 page PDF)
  - [ ] Trajectory Comparison Plot (linear vs. power-law on same chart)
  - [ ] Cost Penalty Analysis (money left on the table by linear model)
  - [ ] Mathematical explanation of why the trajectories differ
- [ ] **Python Code** (fully reproducible)
  - [ ] `ali/linear_baseline.py` — Linear QP solver
  - [ ] `mohamed/power_law_extension.py` — Power-law numerical solver
  - [ ] `combined/comparison.py` — Comparison and cost mismatch analysis
- [ ] **Presentation** (10-minute in-class)
  - [ ] Slides in `presentation/`
  - [ ] Key figures from `figures/`

---

## How to Run

```bash
# Install dependencies
pip install -r requirements.txt

# Run Ali's linear baseline
python ali/linear_baseline.py

# Run Mohamed's power-law extension
python mohamed/power_law_extension.py

# Run the combined comparison
python combined/comparison.py
```

All generated figures are saved to the `figures/` directory.
