"""
Combined Comparison — Trajectory and Cost Mismatch Analysis
============================================================

Done together by Ali and Mohamed after both halves are complete.

This script:
1. Imports both optimal trajectory solvers and cost functions
2. Generates the REQUIRED trajectory comparison plot
3. Performs the REQUIRED cost mismatch analysis
4. Runs sensitivity analyses (beta sweep, gamma sweep)

All figures are saved to the figures/ directory.
"""

import numpy as np
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
# Import from both halves
# ---------------------------------------------------------------------------
from ali.linear_baseline import (
    set_params,
    optimal_trajectory_linear,
    compute_trade_list,
    compute_cost_linear,
)
from mohamed.power_law_extension import (
    optimal_trajectory_power_law,
    compute_cost_power_law,
)


# ===================================================================
# TASK C1: Trajectory Comparison Plot (REQUIRED DELIVERABLE)
# ===================================================================

def plot_trajectory_comparison(linear_traj, power_law_traj, params, beta=0.6,
                                save_path=None):
    """
    Plot both optimal trajectories (linear and power-law) on the same chart.

    This is the key visual deliverable. The power-law trajectory should appear
    more "convex" — more aggressive selling early, slower selling later —
    compared to the linear trajectory.

    Why the difference?
    The power-law model has a concave impact function (|v|^1.6 grows slower than
    v^2 for large v). This means large trades are penalized LESS than in the
    linear model. Therefore, it's optimal to front-load trading to reduce risk
    exposure faster.

    Parameters
    ----------
    linear_traj : np.ndarray, shape (N+1,)
        Linear model optimal trajectory.
    power_law_traj : np.ndarray, shape (N+1,)
        Power-law model optimal trajectory.
    params : dict
        Parameter dictionary from set_params().
    beta : float
        Power-law exponent used (for labeling).
    save_path : str or None
        If provided, save the figure to this path.
    """
    # TODO: Implement
    # - x-axis: trading period k (0 to N)
    # - y-axis: remaining inventory (shares)
    # - Blue solid line: Linear model (beta = 1.0), labeled "Linear (beta=1.0)"
    # - Red dashed line: Power-law model, labeled "Power-Law (beta=0.6)"
    # - Add a gray dashed line for TWAP (uniform liquidation) as reference
    # - Legend, axis labels, title, grid
    pass


# ===================================================================
# TASK C2: Trading Rate Comparison
# ===================================================================

def plot_trade_rate_comparison(linear_traj, power_law_traj, params, beta=0.6,
                               save_path=None):
    """
    Plot the trading rate v_k for both models on the same chart.

    The linear model has a more uniform trading rate.
    The power-law model starts with larger trades and tapers off.

    Parameters
    ----------
    linear_traj : np.ndarray, shape (N+1,)
        Linear model optimal trajectory.
    power_law_traj : np.ndarray, shape (N+1,)
        Power-law model optimal trajectory.
    params : dict
        Parameter dictionary.
    beta : float
        Power-law exponent.
    save_path : str or None
        If provided, save the figure.
    """
    # TODO: Implement
    # Compute trade lists for both trajectories
    # Plot v_k for both on same chart
    pass


# ===================================================================
# TASK C3: Cost Mismatch Analysis (REQUIRED DELIVERABLE)
# ===================================================================

def cost_mismatch_analysis(linear_traj, power_law_traj, params, beta=0.6):
    """
    Compute and display the cost mismatch between the linear and power-law models.

    Four key numbers:
    1. Linear cost of linear trajectory (what the linear model thinks it costs)
    2. Power-law cost of power-law trajectory (optimal cost under true dynamics)
    3. Power-law cost of linear trajectory (TRUE cost of the naive strategy)
    4. Cost gap = (3) - (2) = money "left on the table" by the linear model

    The cost gap quantifies how much the linear Almgren-Chriss model
    underperforms because it misunderstands the shape of order book resilience.

    Parameters
    ----------
    linear_traj : np.ndarray, shape (N+1,)
        Linear model optimal trajectory.
    power_law_traj : np.ndarray, shape (N+1,)
        Power-law model optimal trajectory.
    params : dict
        Parameter dictionary.
    beta : float
        Power-law exponent.

    Returns
    -------
    results : dict
        Dictionary with keys:
        - 'linear_cost_linear': cost of linear traj under linear model
        - 'pl_cost_pl': cost of power-law traj under power-law model
        - 'pl_cost_linear': cost of linear traj under power-law model
        - 'cost_gap': pl_cost_linear - pl_cost_pl
        - 'cost_gap_pct': percentage cost increase
    """
    # TODO: Implement
    # Steps:
    #   1. linear_cost_linear = compute_cost_linear(linear_traj, params)
    #   2. pl_cost_pl = compute_cost_power_law(power_law_traj, params, beta)
    #   3. pl_cost_linear = compute_cost_power_law(linear_traj, params, beta)
    #   4. cost_gap = pl_cost_linear - pl_cost_pl
    #   5. cost_gap_pct = (cost_gap / pl_cost_pl) * 100
    #   6. Print formatted table
    #   7. Return results dict
    pass


def plot_cost_mismatch(results, save_path=None):
    """
    Create a bar chart comparing the power-law costs of both trajectories.

    Two bars:
    - "Power-Law Optimal": cost of the power-law trajectory under power-law model
    - "Linear (Naive)": cost of the linear trajectory under power-law model

    The difference between the bars = money left on the table.

    Parameters
    ----------
    results : dict
        Output from cost_mismatch_analysis().
    save_path : str or None
        If provided, save the figure.
    """
    # TODO: Implement
    pass


# ===================================================================
# TASK C4: Sensitivity — Cost Gap vs. Beta
# ===================================================================

def cost_gap_vs_beta(beta_values=None, save_path=None):
    """
    Analyze how the cost gap between linear and power-law models changes with beta.

    At beta = 1.0, the cost gap should be approximately zero (both models agree).
    As beta decreases (more non-linear impact), the cost gap should increase.

    Parameters
    ----------
    beta_values : list of float or None
        Default: [0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0].
    save_path : str or None
        If provided, save the figure.
    """
    # TODO: Implement
    # For each beta:
    #   1. Solve the power-law model
    #   2. Compute cost gap
    # Plot cost gap vs. beta
    pass


# ===================================================================
# TASK C5: Sensitivity — Trajectories vs. Gamma
# ===================================================================

def gamma_sensitivity_comparison(gamma_values=None, beta=0.6, save_path=None):
    """
    Compare how risk aversion (gamma) affects trajectories in both models.

    For each gamma, plot the linear and power-law trajectories side by side
    to show how the shape difference between models varies with risk aversion.

    Parameters
    ----------
    gamma_values : list of float or None
        Default: [1e-7, 1e-6, 2.5e-6, 1e-5, 1e-4].
    beta : float
        Power-law exponent.
    save_path : str or None
        If provided, save the figure.
    """
    # TODO: Implement
    pass


# ===================================================================
# MAIN — Run the full combined analysis
# ===================================================================

if __name__ == "__main__":
    # ---------------------------------------------------------------
    # Setup
    # ---------------------------------------------------------------
    params = set_params()
    beta = 0.6
    os.makedirs(FIGURES_DIR, exist_ok=True)

    print("=" * 60)
    print("COMBINED ANALYSIS — Linear vs. Power-Law Execution")
    print("=" * 60)
    print(f"Parameters: {params}")
    print(f"Power-law beta: {beta}")

    # ---------------------------------------------------------------
    # Solve both models
    # ---------------------------------------------------------------
    print("\nSolving linear model...")
    linear_traj = optimal_trajectory_linear(params)
    print("Solving power-law model...")
    power_law_traj = optimal_trajectory_power_law(params, beta=beta)

    # ---------------------------------------------------------------
    # DELIVERABLE 1: Trajectory Comparison Plot
    # ---------------------------------------------------------------
    print("\n--- Trajectory Comparison ---")
    plot_trajectory_comparison(
        linear_traj, power_law_traj, params, beta=beta,
        save_path=os.path.join(FIGURES_DIR, "trajectory_comparison.png")
    )

    # ---------------------------------------------------------------
    # Trading Rate Comparison
    # ---------------------------------------------------------------
    plot_trade_rate_comparison(
        linear_traj, power_law_traj, params, beta=beta,
        save_path=os.path.join(FIGURES_DIR, "trade_rate_comparison.png")
    )

    # ---------------------------------------------------------------
    # DELIVERABLE 2: Cost Mismatch Analysis
    # ---------------------------------------------------------------
    print("\n--- Cost Mismatch Analysis ---")
    results = cost_mismatch_analysis(linear_traj, power_law_traj, params, beta=beta)
    plot_cost_mismatch(
        results,
        save_path=os.path.join(FIGURES_DIR, "cost_mismatch.png")
    )

    # ---------------------------------------------------------------
    # Sensitivity: Cost Gap vs. Beta
    # ---------------------------------------------------------------
    print("\n--- Sensitivity: Cost Gap vs. Beta ---")
    cost_gap_vs_beta(
        beta_values=[0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0],
        save_path=os.path.join(FIGURES_DIR, "cost_gap_vs_beta.png")
    )

    # ---------------------------------------------------------------
    # Sensitivity: Gamma Comparison
    # ---------------------------------------------------------------
    print("\n--- Sensitivity: Trajectories vs. Gamma ---")
    gamma_sensitivity_comparison(
        gamma_values=[1e-7, 1e-6, 2.5e-6, 1e-5, 1e-4],
        beta=beta,
        save_path=os.path.join(FIGURES_DIR, "gamma_sensitivity_comparison.png")
    )

    print(f"\nAll figures saved to {FIGURES_DIR}/")
    print("Done!")
