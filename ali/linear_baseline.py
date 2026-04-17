"""
Linear Almgren-Chriss Optimal Execution Baseline
=================================================

Ali's Half — Implements the classical Almgren-Chriss model with linear temporary
market impact. This corresponds to beta = 1.0 in the general power-law framework.

Objective (from project spec — Linear Model):

    min_x  sum_{k=1}^{N} [ eta * v_k^2  +  gamma * sigma^2 * x_k^2 ]

    where:
        x_k = inventory remaining at time step k
        v_k = x_{k-1} - x_k = shares traded in period k
        x_0 = X (initial inventory)
        x_N = 0 (must fully liquidate)

There is NO permanent impact term. Only temporary impact + risk penalty.

With beta = 1.0, the impact cost eta * v_k^2 is quadratic, making this a standard
Quadratic Program (QP). It admits a closed-form solution via the Euler-Lagrange
equations, expressible in terms of hyperbolic sine functions.
"""

import numpy as np
import matplotlib.pyplot as plt
import os

# ---------------------------------------------------------------------------
# Path setup — figures are saved to the repo's figures/ directory
# ---------------------------------------------------------------------------
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIGURES_DIR = os.path.join(REPO_ROOT, "figures")


# ===================================================================
# SHARED PARAMETER INTERFACE — imported by Mohamed's module
# ===================================================================

def set_params(X=1_000_000, N=50, sigma=0.02, gamma=2.5e-6, eta=2.0e-4):
    """
    Create the shared parameter dictionary for both execution models.

    This function is the SINGLE SOURCE OF TRUTH for all model parameters.
    Mohamed's power_law_extension.py imports this function.

    Parameters
    ----------
    X : float
        Initial inventory — total shares to liquidate.
        Default: 1,000,000 shares.
    N : int
        Number of trading periods (e.g., 50 half-hour bins in a trading day).
        Default: 50.
    sigma : float
        Daily volatility of the asset price.
        Default: 0.02 ($2 on a $100 stock).
    gamma : float
        Risk aversion parameter — higher gamma penalizes holding inventory.
        Default: 2.5e-6.
    eta : float
        Temporary impact coefficient — scales the cost of trading.
        Default: 2.0e-4.

    Returns
    -------
    params : dict
        Dictionary with keys: 'X', 'N', 'sigma', 'gamma', 'eta'.
    """
    # TODO: Implement — return a dictionary with all parameters
    pass


# ===================================================================
# CORE FUNCTIONS
# ===================================================================

def optimal_trajectory_linear(params):
    """
    Solve the linear Almgren-Chriss optimal execution problem.

    Finds the inventory trajectory x_k that minimizes:
        sum_{k=1}^{N} [ eta * v_k^2  +  gamma * sigma^2 * x_k^2 ]

    This is a standard QP with a known closed-form solution via the
    Euler-Lagrange equations:

        x_k = X * sinh(kappa * (N - k)) / sinh(kappa * N)

    where kappa = sqrt(gamma * sigma^2 / eta).

    Alternatively, can be solved numerically using cvxpy or scipy as a QP.

    Parameters
    ----------
    params : dict
        Parameter dictionary from set_params().

    Returns
    -------
    trajectory : np.ndarray, shape (N+1,)
        Inventory levels [x_0, x_1, ..., x_N] where x_0 = X and x_N = 0.
    """
    # TODO: Implement the closed-form solution or solve as a QP
    # Steps:
    #   1. Extract X, N, sigma, gamma, eta from params
    #   2. Compute kappa = sqrt(gamma * sigma^2 / eta)
    #   3. For each k in 0..N: x_k = X * sinh(kappa * (N - k)) / sinh(kappa * N)
    #   4. Return the trajectory array of shape (N+1,)
    pass


def compute_trade_list(trajectory):
    """
    Extract the trade list (shares traded per period) from an inventory trajectory.

    v_k = x_{k-1} - x_k  for k = 1, ..., N

    Parameters
    ----------
    trajectory : np.ndarray, shape (N+1,)
        Inventory levels [x_0, x_1, ..., x_N].

    Returns
    -------
    trade_list : np.ndarray, shape (N,)
        Shares traded in each period [v_1, v_2, ..., v_N].
        All values should be positive (selling).
    """
    # TODO: Implement — compute v_k = x_{k-1} - x_k
    # Hint: trade_list = trajectory[:-1] - trajectory[1:]
    pass


def compute_cost_linear(trajectory, params):
    """
    Compute the total execution cost under the LINEAR impact model.

    Cost = sum_{k=1}^{N} [ eta * v_k^2  +  gamma * sigma^2 * x_k^2 ]

    This function must accept ANY trajectory (not just the optimal one),
    because the combined analysis evaluates different trajectories under
    different cost models.

    Parameters
    ----------
    trajectory : np.ndarray, shape (N+1,)
        Inventory levels [x_0, x_1, ..., x_N].
    params : dict
        Parameter dictionary from set_params().

    Returns
    -------
    cost : float
        Total execution cost (temporary impact + risk penalty).
    """
    # TODO: Implement
    # Steps:
    #   1. Compute trade list v_k from trajectory
    #   2. Impact cost = eta * sum(v_k^2)
    #   3. Risk cost = gamma * sigma^2 * sum(x_k^2) for k=1..N (exclude x_0)
    #   4. Return total = impact_cost + risk_cost
    pass


# ===================================================================
# PLOTTING FUNCTIONS
# ===================================================================

def plot_trajectory(trajectory, params, title="Linear Model — Optimal Inventory Trajectory",
                    save_path=None):
    """
    Plot the inventory trajectory x_k over trading periods.

    Parameters
    ----------
    trajectory : np.ndarray, shape (N+1,)
        Inventory levels [x_0, x_1, ..., x_N].
    params : dict
        Parameter dictionary from set_params().
    title : str
        Plot title.
    save_path : str or None
        If provided, save the figure to this path. Otherwise show it.
    """
    # TODO: Implement
    # x-axis: trading period k (0 to N)
    # y-axis: remaining inventory x_k
    # Add axis labels, title, grid
    pass


def plot_trade_rate(trade_list, params, title="Linear Model — Trading Rate per Period",
                    save_path=None):
    """
    Plot the trading rate v_k over trading periods.

    Parameters
    ----------
    trade_list : np.ndarray, shape (N,)
        Shares traded per period [v_1, v_2, ..., v_N].
    params : dict
        Parameter dictionary from set_params().
    title : str
        Plot title.
    save_path : str or None
        If provided, save the figure to this path. Otherwise show it.
    """
    # TODO: Implement
    # x-axis: trading period k (1 to N)
    # y-axis: shares traded v_k
    # Add axis labels, title, grid
    pass


def plot_gamma_sensitivity(gamma_values=None, save_path=None):
    """
    Plot how the optimal trajectory changes with different risk aversion (gamma).

    Higher gamma = more risk averse = faster liquidation (front-loaded).
    Lower gamma = more patient = closer to uniform (TWAP).

    Parameters
    ----------
    gamma_values : list of float or None
        Risk aversion values to test. Default: [1e-7, 1e-6, 2.5e-6, 1e-5, 1e-4].
    save_path : str or None
        If provided, save the figure to this path.
    """
    # TODO: Implement
    # For each gamma value:
    #   1. Create params with that gamma (call set_params with gamma=g)
    #   2. Solve for the optimal trajectory
    #   3. Plot on the same chart with a label
    # Add legend, axis labels, title
    pass


# ===================================================================
# MAIN — Run independently to test Ali's half
# ===================================================================

if __name__ == "__main__":
    # ---------------------------------------------------------------
    # Setup with exact project parameters
    # ---------------------------------------------------------------
    params = set_params(
        X=1_000_000,       # shares to liquidate
        N=50,              # trading periods (half-hour bins)
        sigma=0.02,        # daily volatility ($2 on $100 stock)
        gamma=2.5e-6,      # risk aversion
        eta=2.0e-4         # temporary impact coefficient
    )
    print("=" * 60)
    print("LINEAR ALMGREN-CHRISS OPTIMAL EXECUTION")
    print("=" * 60)
    print(f"Parameters: {params}")

    # ---------------------------------------------------------------
    # Solve for optimal trajectory
    # ---------------------------------------------------------------
    trajectory = optimal_trajectory_linear(params)
    trade_list = compute_trade_list(trajectory)
    cost = compute_cost_linear(trajectory, params)

    print(f"\nOptimal trajectory (first 10 values): {trajectory[:10]}")
    print(f"Trade list (first 10 values): {trade_list[:10]}")
    print(f"Total execution cost: {cost:,.2f}")

    # ---------------------------------------------------------------
    # Validation checks
    # ---------------------------------------------------------------
    print(f"\n--- Validation ---")
    print(f"x_0 = {trajectory[0]:,.0f} (should be {params['X']:,.0f})")
    print(f"x_N = {trajectory[-1]:,.0f} (should be 0)")
    print(f"sum(v_k) = {np.sum(trade_list):,.0f} (should be {params['X']:,.0f})")
    print(f"All v_k > 0: {np.all(trade_list > 0)}")

    # ---------------------------------------------------------------
    # Generate plots
    # ---------------------------------------------------------------
    os.makedirs(FIGURES_DIR, exist_ok=True)

    plot_trajectory(trajectory, params,
                    save_path=os.path.join(FIGURES_DIR, "linear_trajectory.png"))
    plot_trade_rate(trade_list, params,
                    save_path=os.path.join(FIGURES_DIR, "linear_trade_rate.png"))
    plot_gamma_sensitivity(
        gamma_values=[1e-7, 1e-6, 2.5e-6, 1e-5, 1e-4],
        save_path=os.path.join(FIGURES_DIR, "linear_gamma_sensitivity.png")
    )
    print(f"\nFigures saved to {FIGURES_DIR}/")
