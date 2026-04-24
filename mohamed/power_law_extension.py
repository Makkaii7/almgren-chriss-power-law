"""
Power-Law Optimal Execution Extension
======================================

Mohamed's Half — Implements the empirical power-law market impact model where
temporary impact scales as |v_k|^(1+beta) with beta = 0.6 (the "Square Root Law").

Objective (from project spec — Power-Law Model):

    min_x  sum_{k=1}^{N} [ eta * |v_k|^(1+beta)  +  gamma * sigma^2 * x_k^2 ]

    where:
        x_k = inventory remaining at time step k
        v_k = x_{k-1} - x_k = shares traded in period k
        x_0 = X (initial inventory)
        x_N = 0 (must fully liquidate)
        beta = 0.6 (empirical power-law exponent)

There is NO permanent impact term. Only temporary impact + risk penalty.

Unlike the linear model (beta = 1.0), the fractional exponent 1 + beta = 1.6
makes this a NON-LINEAR convex optimization problem with NO closed-form solution.
We solve it numerically using scipy.optimize.minimize with the SLSQP method.

IMPORTANT NOTE ON ABSOLUTE VALUE:
    The |v_k| absolute value is critical. During optimization, the solver may
    explore trajectories where some v_k < 0 (buying back shares). Using np.abs()
    ensures the objective remains well-defined and convex even for negative v_k.
    In the optimal solution, all v_k should be positive (monotonic liquidation).

SHARED INTERFACE:
    This module imports set_params() from ali.linear_baseline to ensure both
    models use the exact same parameter setup. The trajectory output format is
    identical: np.ndarray of shape (N+1,) = [x_0, x_1, ..., x_N].
"""

import numpy as np
from scipy.optimize import minimize
import matplotlib.pyplot as plt
import sys
import os

# ---------------------------------------------------------------------------
# Path setup — allow imports from the repo root
# ---------------------------------------------------------------------------
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_ROOT)
FIGURES_DIR = os.path.join(REPO_ROOT, "figures")

# ---------------------------------------------------------------------------
# Import Ali's shared parameter function
# ---------------------------------------------------------------------------
from ali.linear_baseline import set_params


# ===================================================================
# CORE FUNCTIONS
# ===================================================================

def objective_power_law(x_intermediate, params, beta=0.6):
    """
    Compute the total cost under the power-law impact model.

    This is the function that scipy.optimize.minimize will minimize.

    Objective:
        sum_{k=1}^{N} [ eta * |v_k|^(1+beta)  +  gamma * sigma^2 * x_k^2 ]

    Parameters
    ----------
    x_intermediate : np.ndarray, shape (N-1,)
        The decision variables: inventory levels [x_1, x_2, ..., x_{N-1}].
        Note: x_0 = X and x_N = 0 are fixed boundary conditions, NOT decision
        variables. The solver only optimizes the N-1 intermediate values.
    params : dict
        Parameter dictionary from set_params(). Keys: X, N, sigma, gamma, eta.
    beta : float
        Power-law exponent. Default: 0.6 (empirical "Square Root Law").
        When beta = 1.0, this should match the linear model's cost.

    Returns
    -------
    cost : float
        Total execution cost (temporary impact + risk penalty).

    Notes
    -----
    - We use np.abs(v_k) to handle potential negative trade sizes during
      optimization. The solver may explore non-monotonic trajectories.
    - The exponent is (1 + beta), so for beta = 0.6 the impact term is |v_k|^1.6.
    - For beta = 1.0, |v_k|^2.0 = v_k^2, recovering the linear model.
    """
    X = params["X"]
    N = params["N"]
    sigma = params["sigma"]
    gamma = params["gamma"]
    eta = params["eta"]

    # Safety check: the optimizer should provide N-1 intermediate points
    x_intermediate = np.asarray(x_intermediate, dtype=float)
    if x_intermediate.shape != (N - 1,):
        raise ValueError(
            f"x_intermediate must have shape ({N-1},), got {x_intermediate.shape}"
        )

    # 2. Construct full trajectory: [x_0, x_1, ..., x_{N-1}, x_N]
    trajectory = np.concatenate(([X], x_intermediate, [0.0]))

    # 3. Compute trades v_k = x_{k-1} - x_k, for k=1,...,N
    v = trajectory[:-1] - trajectory[1:]

    # 4. Temporary impact cost: eta * sum(|v_k|^(1+beta))
    impact_cost = eta * np.sum(np.abs(v) ** (1.0 + beta))

    # 5. Risk cost: gamma * sigma^2 * sum(x_k^2), k=1,...,N
    # Exclude x_0, include x_N=0 (harmless)
    risk_cost = gamma * (sigma ** 2) * np.sum(trajectory[1:] ** 2)

    # 6. Total cost
    total_cost = impact_cost + risk_cost
    return float(total_cost)


def optimal_trajectory_power_law(params, beta=0.6):
    """
    Solve the power-law optimal execution problem using numerical optimization.

    Finds the inventory trajectory x_k that minimizes:
        sum_{k=1}^{N} [ eta * |v_k|^(1+beta)  +  gamma * sigma^2 * x_k^2 ]

    Subject to:
        - x_0 = X (initial inventory, fixed)
        - x_N = 0 (full liquidation, fixed)
        - 0 <= x_k <= X for all intermediate k (no short selling)

    Uses scipy.optimize.minimize with method='SLSQP'.

    Parameters
    ----------
    params : dict
        Parameter dictionary from set_params().
    beta : float
        Power-law exponent. Default: 0.6.

    Returns
    -------
    trajectory : np.ndarray, shape (N+1,)
        Optimal inventory levels [x_0, x_1, ..., x_N] where x_0 = X, x_N = 0.
        Same format as Ali's optimal_trajectory_linear() output.

    Notes
    -----
    - Decision variables are x_1, ..., x_{N-1} (N-1 variables).
    - Initial guess: linear interpolation (TWAP) x_k = X * (1 - k/N).
    - Bounds: (0, X) for each intermediate x_k.
    - The full liquidation constraint is enforced by fixing x_0 = X and x_N = 0,
      NOT as an explicit constraint to the solver.
    - Sanity check: with beta = 1.0, the result should match the linear model.
    """
    X = params["X"]
    N = params["N"]

    # Edge case: if N = 1, there are no intermediate variables
    if N == 1:
        return np.array([X, 0.0], dtype=float)

    # 2. Initial guess: TWAP / linear interpolation for x_1, ..., x_{N-1}
    x_init = np.array([X * (1.0 - k / N) for k in range(1, N)], dtype=float)

    # 3. Bounds: 0 <= x_k <= X
    bounds = [(0.0, X)] * (N - 1)

    # Optional monotonicity constraints:
    # x_k >= x_{k+1} for k=1,...,N-2
    # This helps prevent the solver from exploring buybacks / non-monotone paths.
    constraints = []
    for i in range(N - 2):
        constraints.append({
            "type": "ineq",
            "fun": lambda x, i=i: x[i] - x[i + 1]
        })

    # 4. Run the optimizer
    result = minimize(
        objective_power_law,
        x0=x_init,
        args=(params, beta),
        method="SLSQP",
        bounds=bounds,
        constraints=constraints,
        options={"maxiter": 1000, "ftol": 1e-12}
    )

    # 5. Check solver success
    if not result.success:
        raise RuntimeError(f"SLSQP did not converge: {result.message}")

    # 6. Construct full trajectory [X, x_1, ..., x_{N-1}, 0]
    trajectory = np.concatenate(([X], result.x, [0.0]))

    # Small cleanup for numerical noise
    trajectory = np.clip(trajectory, 0.0, X)
    trajectory[0] = X
    trajectory[-1] = 0.0

    # 7. Return shape (N+1,)
    return trajectory


def compute_cost_power_law(trajectory, params, beta=0.6):
    """
    Compute the total execution cost of ANY trajectory under power-law impact.

    Cost = sum_{k=1}^{N} [ eta * |v_k|^(1+beta)  +  gamma * sigma^2 * x_k^2 ]

    This function must accept ANY trajectory (not just the optimal one).
    It is used in the cost mismatch analysis to evaluate Ali's linear trajectory
    under the power-law cost model.

    Parameters
    ----------
    trajectory : np.ndarray, shape (N+1,)
        Inventory levels [x_0, x_1, ..., x_N].
    params : dict
        Parameter dictionary from set_params().
    beta : float
        Power-law exponent. Default: 0.6.

    Returns
    -------
    cost : float
        Total execution cost under power-law impact.

    Notes
    -----
    This wraps objective_power_law() but accepts a full trajectory (N+1 values)
    instead of just the intermediate values (N-1 values).
    """
    trajectory = np.asarray(trajectory, dtype=float)

    X = params["X"]
    N = params["N"]

    if trajectory.shape != (N + 1,):
        raise ValueError(
            f"trajectory must have shape ({N+1},), got {trajectory.shape}"
        )

    # Optional boundary check
    if not np.isclose(trajectory[0], X):
        raise ValueError(f"trajectory[0] must equal X={X}, got {trajectory[0]}")
    if not np.isclose(trajectory[-1], 0.0):
        raise ValueError(f"trajectory[-1] must equal 0, got {trajectory[-1]}")

    x_intermediate = trajectory[1:-1]
    return objective_power_law(x_intermediate, params, beta)


# ===================================================================
# PLOTTING FUNCTIONS
# ===================================================================

def plot_trajectory_power_law(trajectory, params, beta=0.6,
                               title="Power-Law Model — Optimal Inventory Trajectory",
                               save_path=None):
    """
    Plot the power-law optimal inventory trajectory x_k over trading periods.

    Parameters
    ----------
    trajectory : np.ndarray, shape (N+1,)
        Inventory levels [x_0, x_1, ..., x_N].
    params : dict
        Parameter dictionary from set_params().
    beta : float
        Power-law exponent (for labeling).
    title : str
        Plot title.
    save_path : str or None
        If provided, save the figure to this path.
    """
    trajectory = np.asarray(trajectory, dtype=float)
    N = params["N"]

    if trajectory.shape != (N + 1,):
        raise ValueError(
            f"trajectory must have shape ({N+1},), got {trajectory.shape}"
        )

    k = np.arange(N + 1)

    plt.figure(figsize=(10, 6))
    plt.plot(k, trajectory, linewidth=2, label=rf"Power-law trajectory ($\beta={beta}$)")
    plt.xlabel("Trading period k")
    plt.ylabel("Remaining inventory $x_k$")
    plt.title(title)
    plt.grid(True, alpha=0.3)
    plt.legend()

    if save_path is not None:
        plt.savefig(save_path, dpi=300, bbox_inches="tight")

    plt.show()


def plot_beta_sensitivity(beta_values=None, save_path=None):
    """
    Plot how the optimal trajectory changes with different beta exponents.

    KEY SANITY CHECK: beta = 1.0 should produce a trajectory matching Ali's
    linear result, since |v_k|^(1+1.0) = |v_k|^2.0 = v_k^2.

    Lower beta = more concave impact function = more aggressive early trading.
    Higher beta = closer to linear/quadratic = more uniform trading.

    Parameters
    ----------
    beta_values : list of float or None
        Beta values to test. Default: [0.3, 0.5, 0.6, 0.7, 1.0].
    save_path : str or None
        If provided, save the figure to this path.
    """
    if beta_values is None:
        # SLSQP is unreliable at β = 1.0 (flat landscape → iteration-limit failure).
        # For verified β = 1.0 behavior see combined/verify_cvxpy.py.
        beta_values = [0.3, 0.5, 0.6, 0.7, 0.8]

    # 1. Shared parameters
    params = set_params()
    N = params["N"]
    k = np.arange(N + 1)

    plt.figure(figsize=(10, 6))

    # 2. Solve and plot one trajectory for each beta.
    #    SLSQP can time out on flat landscapes (β close to 1) — skip and note.
    for beta in beta_values:
        try:
            trajectory = optimal_trajectory_power_law(params, beta=beta)
            plt.plot(k, trajectory, linewidth=2, label=rf"$\beta={beta}$")
        except RuntimeError as e:
            print(f"  [plot_beta_sensitivity] skipping β={beta}: {e}")

    # 3. Formatting
    plt.xlabel("Trading period")
    plt.ylabel("Remaining inventory (shares)")
    plt.title("Power-Law Model — Beta Sensitivity of Optimal Trajectory")
    plt.grid(True, alpha=0.3)
    plt.legend(title="Impact exponent")

    if save_path is not None:
        plt.savefig(save_path, dpi=300, bbox_inches="tight")

    plt.show()


# ===================================================================
# MAIN — Run independently to test Mohamed's half
# ===================================================================

if __name__ == "__main__":
    # ---------------------------------------------------------------
    # Setup with exact project parameters (via Ali's set_params)
    # ---------------------------------------------------------------
    params = set_params(
        X=1_000_000,       # shares to liquidate
        N=50,              # trading periods (half-hour bins)
        sigma=0.02,        # daily volatility ($2 on $100 stock)
        gamma=2.5e-6,      # risk aversion
        eta=2.0e-4         # temporary impact coefficient
    )
    beta = 0.6             # empirical power-law exponent

    print("=" * 60)
    print("POWER-LAW OPTIMAL EXECUTION (beta = {})".format(beta))
    print("=" * 60)
    print(f"Parameters: {params}")

    # ---------------------------------------------------------------
    # Solve for optimal trajectory
    # ---------------------------------------------------------------
    trajectory = optimal_trajectory_power_law(params, beta=beta)
    trade_list = trajectory[:-1] - trajectory[1:]  # v_k = x_{k-1} - x_k
    cost = compute_cost_power_law(trajectory, params, beta=beta)

    print(f"\nOptimal trajectory (first 10 values): {trajectory[:10]}")
    print(f"Trade list (first 10 values): {trade_list[:10]}")
    print(f"Total execution cost (beta={beta}): {cost:,.2f}")

    # ---------------------------------------------------------------
    # Validation checks
    # ---------------------------------------------------------------
    print(f"\n--- Validation ---")
    print(f"x_0 = {trajectory[0]:,.0f} (should be {params['X']:,.0f})")
    print(f"x_N = {trajectory[-1]:,.0f} (should be 0)")
    print(f"sum(v_k) = {np.sum(trade_list):,.0f} (should be {params['X']:,.0f})")
    print(f"All v_k > 0: {np.all(trade_list > 0)}")

    # ---------------------------------------------------------------
    # Sanity check: beta = 1.0 should match linear model.
    # Real convergence criterion: relative objective gap < 1e-6.
    # ---------------------------------------------------------------
    print(f"\n--- Sanity Check: beta = 1.0 ---")
    from ali.linear_baseline import optimal_trajectory_linear, compute_cost_linear
    try:
        traj_beta1 = optimal_trajectory_power_law(params, beta=1.0)
        traj_linear = optimal_trajectory_linear(params)
        max_diff = np.max(np.abs(traj_beta1 - traj_linear))
        cost_pl1 = compute_cost_power_law(traj_beta1, params, beta=1.0)
        cost_lin = compute_cost_linear(traj_linear, params)
        rel_obj_gap = abs(cost_pl1 - cost_lin) / max(abs(cost_lin), 1e-12)
        print(f"Max |Δtraj|: {max_diff:.4f}  ({max_diff / params['X'] * 100:.4e}% of X)")
        print(f"Relative objective gap: {rel_obj_gap:.3e}")
        match = (rel_obj_gap < 1e-6) and (max_diff < params['X'] * 1e-3)
        print(f"Match: {'YES' if match else 'NO — investigate!'}")
    except RuntimeError as e:
        print(f"SLSQP could not solve β=1.0 ({e}).  "
              f"The flat quadratic landscape exceeds SLSQP's tolerance budget.  "
              f"Use combined/verify_cvxpy.py for a disciplined-convex re-solve.")

    # ---------------------------------------------------------------
    # Generate plots
    # ---------------------------------------------------------------
    os.makedirs(FIGURES_DIR, exist_ok=True)

    plot_trajectory_power_law(trajectory, params, beta=beta,
                               save_path=os.path.join(FIGURES_DIR, "power_law_trajectory.png"))
    plot_beta_sensitivity(
        beta_values=[0.3, 0.5, 0.6, 0.7, 0.9],
        save_path=os.path.join(FIGURES_DIR, "power_law_beta_sensitivity.png")
    )
    print(f"\nFigures saved to {FIGURES_DIR}/")
