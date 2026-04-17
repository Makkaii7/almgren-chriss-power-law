# Project Plan — Detailed Task Breakdown

## Shared Interface

Both halves communicate through a **shared parameter dictionary** and a **common trajectory format**.

**Parameter dictionary** (defined by Ali in `set_params()`):
```python
{
    "X": 1_000_000,      # initial inventory (shares)
    "N": 50,             # number of trading periods
    "sigma": 0.02,       # daily volatility
    "gamma": 2.5e-6,     # risk aversion parameter
    "eta": 2.0e-4,       # temporary impact coefficient
}
```

**Trajectory format:** `np.ndarray` of shape `(N+1,)` = `[x_0, x_1, ..., x_N]` where `x_0 = X` and `x_N = 0`.

**Trade list format:** `np.ndarray` of shape `(N,)` = `[v_1, v_2, ..., v_N]` where `v_k = x_{k-1} - x_k`.

---

## Ali's Half — Linear Almgren-Chriss Baseline

### File: `ali/linear_baseline.py`

### Mathematical Formulation

Objective (Equation from project spec — Linear Model):
```
min_x  sum_{k=1}^{N} [ eta * v_k^2  +  gamma * sigma^2 * x_k^2 ]
```

Subject to:
- x_0 = X = 1,000,000
- x_N = 0
- v_k = x_{k-1} - x_k  for k = 1, ..., N

With beta = 1.0, the impact term is eta * v_k^2 (quadratic), making this a standard QP.

### Task Breakdown

#### Task A1: `set_params()` — Shared Parameter Setup
- Define all model parameters in one place
- This function is imported by Mohamed's code
- Returns a dictionary with keys: X, N, sigma, gamma, eta
- **This is the single source of truth for all parameters**

#### Task A2: `optimal_trajectory_linear()` — Solve the QP
- **Approach option 1 (Closed-form):** The Euler-Lagrange conditions for this quadratic objective yield a recursive formula. The optimal trajectory can be expressed in terms of hyperbolic functions:
  ```
  kappa = sqrt(gamma * sigma^2 / eta)
  x_k = X * sinh(kappa * (N - k)) / sinh(kappa * N)
  ```
- **Approach option 2 (Numerical QP):** Formulate using `cvxpy`:
  - Decision variables: x_1, ..., x_{N-1}
  - Objective: sum of eta * v_k^2 + gamma * sigma^2 * x_k^2
  - This is a convex QP and solves instantly
- Either approach is acceptable. The closed-form is elegant; the QP demonstrates the framework.
- **Output:** np.ndarray of shape (N+1,) = [x_0, x_1, ..., x_N]

#### Task A3: `compute_trade_list()` — Extract Trading Rates
- Given a trajectory [x_0, ..., x_N], compute v_k = x_{k-1} - x_k
- Simple: `v = -np.diff(trajectory)` or `trajectory[:-1] - trajectory[1:]`
- **Output:** np.ndarray of shape (N,)

#### Task A4: `compute_cost_linear()` — Evaluate Cost Under Linear Impact
- Given any trajectory and params, compute the total cost:
  ```
  cost = sum_{k=1}^{N} [ eta * v_k^2 + gamma * sigma^2 * x_k^2 ]
  ```
- This function must accept ANY trajectory (not just the optimal one) — Mohamed's combined analysis needs to evaluate the linear trajectory under different cost models
- **Output:** float

#### Task A5: `plot_trajectory()` — Inventory Over Time
- x-axis: trading period k (0 to N)
- y-axis: remaining inventory x_k
- Should show a smooth, roughly linear decline for the linear model
- Save to `figures/linear_trajectory.png`

#### Task A6: `plot_trade_rate()` — Trading Rate Over Time
- x-axis: trading period k (1 to N)
- y-axis: shares traded v_k
- For the linear model, the trade rate starts lower and increases over time (front-loads less)
- Save to `figures/linear_trade_rate.png`

#### Task A7: Sensitivity to Gamma
- Run the optimizer for gamma values: [1e-7, 1e-6, 2.5e-6, 1e-5, 1e-4]
- Plot all trajectories on the same chart
- Higher gamma = more risk averse = faster liquidation (more front-loaded)
- Lower gamma = more patient = closer to uniform (TWAP)
- Save to `figures/linear_gamma_sensitivity.png`

### Testing
- Verify x_0 = X and x_N = 0
- Verify all v_k > 0 (monotonically decreasing inventory)
- Verify sum(v_k) = X (full liquidation)
- Verify cost is positive and finite

---

## Mohamed's Half — Power-Law Extension

### File: `mohamed/power_law_extension.py`

### Mathematical Formulation

Objective (Equation from project spec — Power-Law Model):
```
min_x  sum_{k=1}^{N} [ eta * |v_k|^(1+beta)  +  gamma * sigma^2 * x_k^2 ]
```

Subject to:
- x_0 = X = 1,000,000
- x_N = 0
- v_k = x_{k-1} - x_k  for k = 1, ..., N
- x_k >= 0  for all k (no short selling)

With beta = 0.6, the impact term is eta * |v_k|^1.6 — a non-linear, non-quadratic convex function. No closed-form solution exists.

### Task Breakdown

#### Task M1: Import Shared Parameters
- `from ali.linear_baseline import set_params`
- Use the exact same parameter dictionary as Ali
- This ensures both models are compared on equal footing

#### Task M2: `objective_power_law()` — The Cost Function
- Computes the total objective value for a given set of intermediate inventory levels
- **Input:** x_intermediate = [x_1, x_2, ..., x_{N-1}] (N-1 decision variables)
- Internally constructs full trajectory: [X, x_1, ..., x_{N-1}, 0]
- Computes v_k = x_{k-1} - x_k for each period
- Returns: sum of eta * |v_k|^(1+beta) + gamma * sigma^2 * x_k^2
- **IMPORTANT:** Use `np.abs(v_k)` for the absolute value to handle potential negative trade sizes. Even though we expect all v_k > 0 (selling), the optimizer may explore negative values during iteration. The absolute value ensures the objective remains well-defined and convex.

#### Task M3: `optimal_trajectory_power_law()` — Numerical Solver
- **Decision variables:** x_1, x_2, ..., x_{N-1} (the N-1 intermediate inventory levels)
- x_0 = X and x_N = 0 are fixed boundary conditions, not decision variables
- **Initial guess:** Linear interpolation (TWAP) — `x_k = X * (1 - k/N)`
- **Solver:** `scipy.optimize.minimize` with method='SLSQP'
  - Bounds: (0, X) for each x_k (no short selling, can't hold more than initial)
  - The equality constraint sum(v_k) = X is automatically satisfied by fixing x_0 and x_N
  - Optionally add monotonicity constraints: x_k >= x_{k+1} (ensures we only sell, never buy back)
- **Output:** np.ndarray of shape (N+1,) = [x_0, x_1, ..., x_N] — same format as Ali's

#### Task M4: `compute_cost_power_law()` — Evaluate Power-Law Cost
- Given any trajectory and params, compute:
  ```
  cost = sum_{k=1}^{N} [ eta * |v_k|^(1+beta) + gamma * sigma^2 * x_k^2 ]
  ```
- Must accept ANY trajectory — this is critical for the cost mismatch analysis where we evaluate Ali's linear trajectory under power-law costs
- **Output:** float

#### Task M5: `plot_trajectory_power_law()` — Inventory Over Time
- Same axes and format as Ali's plot
- The power-law trajectory should appear more "convex" — more aggressive selling early, slower later
- Save to `figures/power_law_trajectory.png`

#### Task M6: Beta Sensitivity Analysis
- Run the optimizer for beta values: [0.3, 0.5, 0.6, 0.7, 1.0]
- Plot all trajectories on the same chart
- **Key sanity check:** beta = 1.0 should produce a trajectory matching Ali's linear result (since |v_k|^(1+1) = v_k^2)
- Lower beta = more concave impact = more aggressive early trading
- Save to `figures/power_law_beta_sensitivity.png`

### Testing
- Verify x_0 = X and x_N = 0
- Verify all v_k > 0
- Verify sum(v_k) = X
- **Sanity check:** Run with beta = 1.0 and compare to Ali's linear result — should match within solver tolerance
- Verify optimizer converges (check `result.success` and `result.message`)

---

## Combined Work — comparison.py

### File: `combined/comparison.py`

Done together by Ali and Mohamed after both halves are complete.

### Task C1: Trajectory Comparison Plot (REQUIRED DELIVERABLE)
- Import `optimal_trajectory_linear` from Ali's module
- Import `optimal_trajectory_power_law` from Mohamed's module
- Plot both trajectories on the same chart:
  - x-axis: trading period k (0 to 50)
  - y-axis: remaining inventory (shares)
  - Blue line: Linear model (beta = 1.0)
  - Red line: Power-law model (beta = 0.6)
  - Legend, axis labels, title
- **Key visual difference:** The power-law trajectory is more convex — it front-loads trading more aggressively. The linear trajectory is closer to a straight line (TWAP). This is because the power-law model penalizes large trades less severely (concave impact), so it's optimal to trade more aggressively when inventory (and hence risk) is high.
- Save to `figures/trajectory_comparison.png`

### Task C2: Trading Rate Comparison
- Plot v_k for both models on the same chart
- The linear model has a more uniform trading rate
- The power-law model starts with larger trades and tapers off
- Save to `figures/trade_rate_comparison.png`

### Task C3: Cost Mismatch Analysis (REQUIRED DELIVERABLE)
- Compute four key numbers:
  1. **Linear cost of linear trajectory:** `compute_cost_linear(linear_traj, params)`
  2. **Power-law cost of power-law trajectory:** `compute_cost_power_law(pl_traj, params, beta=0.6)`
  3. **Power-law cost of linear trajectory:** `compute_cost_power_law(linear_traj, params, beta=0.6)` — this is the "true" cost of the naive strategy
  4. **Cost gap:** (3) - (2) = money left on the table by the linear model
- Print results as a formatted table
- Create a bar chart comparing costs (2) and (3)
- Save to `figures/cost_mismatch.png`

### Task C4: Sensitivity — Cost Gap vs. Beta
- For beta in [0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]:
  - Solve the power-law model
  - Compute the cost gap
- Plot cost gap vs. beta
- At beta = 1.0, the cost gap should be ~0
- The gap should increase as beta decreases (more non-linear impact)
- Save to `figures/cost_gap_vs_beta.png`

### Task C5: Sensitivity — Trajectories vs. Gamma
- For different gamma values, plot both linear and power-law trajectories
- Show how risk aversion affects the shape difference between the two models
- Save to `figures/gamma_sensitivity_comparison.png`

---

## Integration Checklist

- [ ] Ali's `set_params()` is the single source of truth — Mohamed imports it
- [ ] Both trajectory functions return arrays of shape (N+1,)
- [ ] Both cost functions accept any trajectory array
- [ ] Beta = 1.0 sanity check passes (power-law matches linear)
- [ ] All figures saved to `figures/` with descriptive filenames
- [ ] Code runs end-to-end: `python combined/comparison.py`
- [ ] No hardcoded paths — all imports work from the repo root
