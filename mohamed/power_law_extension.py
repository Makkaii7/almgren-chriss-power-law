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
    # TODO: Implement
    # Steps:
    #   1. Extract X, N, sigma, gamma, eta from params
    #   2. Construct full trajectory: [X, x_1, ..., x_{N-1}, 0]
    #   3. Compute v_k = x_{k-1} - x_k for k = 1, ..., N
    #   4. Impact cost = eta * sum(|v_k|^(1+beta))  — use np.abs(v_k)
    #   5. Risk cost = gamma * sigma^2 * sum(x_k^2) for k=1..N (exclude x_0)
    #   6. Return total = impact_cost + risk_cost
    pass


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
    # TODO: Implement
    # Steps:
    #   1. Extract X, N from params
    #   2. Create initial guess: x_k = X * (1 - k/N) for k = 1, ..., N-1
    #   3. Set bounds: [(0, X)] * (N-1)
    #   4. Call scipy.optimize.minimize:
    #        result = minimize(
    #            objective_power_law,
    #            x0=x_init,
    #            args=(params, beta),
    #            method='SLSQP',
    #            bounds=bounds,
    #            options={'maxiter': 1000, 'ftol': 1e-12}
    #        )
    #   5. Check result.success — print warning if optimization failed
    #   6. Construct full trajectory: [X, result.x, 0]
    #   7. Return trajectory of shape (N+1,)
    pass


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
    # TODO: Implement
    # Steps:
    #   1. Extract x_intermediate = trajectory[1:-1]
    #   2. Call objective_power_law(x_intermediate, params, beta)
    #   3. Return the cost
    #
    # Or compute directly:
    #   1. Compute v_k = trajectory[:-1] - trajectory[1:]
    #   2. Impact = eta * sum(|v_k|^(1+beta))
    #   3. Risk = gamma * sigma^2 * sum(x_k^2) for k=1..N
    #   4. Return total
    pass


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
    # TODO: Implement
    # x-axis: trading period k (0 to N)
    # y-axis: remaining inventory x_k
    # Label with beta value
    # Add axis labels, title, grid
    pass


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
    # TODO: Implement
    # For each beta value:
    #   1. Create params with set_params()
    #   2. Solve for the optimal trajectory with that beta
    #   3. Plot on the same chart with a label
    # Add legend, axis labels, title
    # Note: This may take a few seconds per beta value (numerical optimization)
    pass


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
    # Sanity check: beta = 1.0 should match linear model
    # ---------------------------------------------------------------
    print(f"\n--- Sanity Check: beta = 1.0 ---")
    traj_beta1 = optimal_trajectory_power_law(params, beta=1.0)
    # Import Ali's linear result for comparison
    from ali.linear_baseline import optimal_trajectory_linear
    traj_linear = optimal_trajectory_linear(params)
    max_diff = np.max(np.abs(traj_beta1 - traj_linear))
    print(f"Max difference between power-law(beta=1.0) and linear: {max_diff:.4f}")
    print(f"Match: {'YES' if max_diff < 100 else 'NO — investigate!'}")

    # ---------------------------------------------------------------
    # Generate plots
    # ---------------------------------------------------------------
    os.makedirs(FIGURES_DIR, exist_ok=True)

    plot_trajectory_power_law(trajectory, params, beta=beta,
                               save_path=os.path.join(FIGURES_DIR, "power_law_trajectory.png"))
    plot_beta_sensitivity(
        beta_values=[0.3, 0.5, 0.6, 0.7, 1.0],
        save_path=os.path.join(FIGURES_DIR, "power_law_beta_sensitivity.png")
    )
    print(f"\nFigures saved to {FIGURES_DIR}/")
