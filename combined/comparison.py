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
    optimal_trajectory_power_law as optimal_trajectory_power_law_slsqp,
    compute_cost_power_law,
)

# CVXPY-verified solver is the primary.  Independent disciplined convex
# optimization (power cone, SCS / CLARABEL) — agrees with SLSQP only for
# β ≥ 0.8, beats it by up to 26% at β = 0.3.  See combined/verify_cvxpy.py.
from combined.verify_cvxpy import optimal_trajectory_power_law_cvxpy


def optimal_trajectory_power_law(params, beta=0.6):
    """Verified power-law solver: CVXPY primary, SLSQP fallback."""
    try:
        traj, _obj, _status = optimal_trajectory_power_law_cvxpy(params, beta=beta)
        return traj
    except Exception:
        return optimal_trajectory_power_law_slsqp(params, beta=beta)


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
    N = params["N"]
    X = params["X"]
    k = np.arange(N + 1)
    twap = X * (1.0 - k / N)

    plt.figure(figsize=(10, 6))
    plt.plot(k, linear_traj, "b-", linewidth=2, label=r"Linear ($\beta=1.0$)")
    plt.plot(k, power_law_traj, "r--", linewidth=2,
             label=rf"Power-Law ($\beta={beta}$)")
    plt.plot(k, twap, color="gray", linestyle=":", linewidth=1.2,
             label="TWAP (uniform)")
    plt.xlabel("Trading period k")
    plt.ylabel("Remaining inventory $x_k$ (shares)")
    plt.title("Optimal Execution: Linear vs Power-Law Impact")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()

    if save_path is not None:
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close()


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
    N = params["N"]
    v_linear = compute_trade_list(linear_traj)
    v_pl = compute_trade_list(power_law_traj)
    k = np.arange(1, N + 1)
    width = 0.4

    plt.figure(figsize=(11, 6))
    plt.bar(k - width / 2, v_linear, width=width, color="steelblue",
            label=r"Linear ($\beta=1.0$)", alpha=0.85)
    plt.bar(k + width / 2, v_pl, width=width, color="crimson",
            label=rf"Power-Law ($\beta={beta}$)", alpha=0.85)
    plt.xlabel("Trading period k")
    plt.ylabel("Shares traded $v_k$")
    plt.title("Trading Rate Comparison: Linear vs Power-Law")
    plt.legend()
    plt.grid(True, axis="y", alpha=0.3)
    plt.tight_layout()

    if save_path is not None:
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close()


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
    linear_cost_linear = compute_cost_linear(linear_traj, params)
    pl_cost_pl = compute_cost_power_law(power_law_traj, params, beta=beta)
    pl_cost_linear = compute_cost_power_law(linear_traj, params, beta=beta)
    linear_cost_pl = compute_cost_linear(power_law_traj, params)

    cost_gap = pl_cost_linear - pl_cost_pl
    cost_gap_pct = (cost_gap / pl_cost_pl) * 100.0

    print(f"{'(a) Linear traj  @ linear cost       ':40s}: "
          f"{linear_cost_linear:>18,.2f}")
    print(f"{'(b) Linear traj  @ power-law cost    ':40s}: "
          f"{pl_cost_linear:>18,.2f}   <- true cost of naive strategy")
    print(f"{'(c) Power-law traj @ power-law cost  ':40s}: "
          f"{pl_cost_pl:>18,.2f}   <- correct / optimal cost")
    print(f"{'(d) Power-law traj @ linear cost     ':40s}: "
          f"{linear_cost_pl:>18,.2f}")
    print("-" * 66)
    print(f"{'Money left on the table = (b) - (c)  ':40s}: "
          f"{cost_gap:>18,.2f}")
    print(f"{'Relative cost gap (% of optimal)     ':40s}: "
          f"{cost_gap_pct:>17,.4f}%")

    return {
        "linear_cost_linear": linear_cost_linear,
        "pl_cost_pl": pl_cost_pl,
        "pl_cost_linear": pl_cost_linear,
        "linear_cost_pl": linear_cost_pl,
        "cost_gap": cost_gap,
        "cost_gap_pct": cost_gap_pct,
    }


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
    labels = ["Power-Law Optimal\n(correct model)",
              "Linear Naive\n(wrong model, true cost)"]
    values = [results["pl_cost_pl"], results["pl_cost_linear"]]
    colors = ["#2b8cbe", "#d7301f"]

    plt.figure(figsize=(8, 6))
    bars = plt.bar(labels, values, color=colors, alpha=0.9)
    for bar, val in zip(bars, values):
        plt.text(bar.get_x() + bar.get_width() / 2, val,
                 f"{val:,.0f}", ha="center", va="bottom", fontsize=10)

    gap = results["cost_gap"]
    pct = results["cost_gap_pct"]
    plt.title(f"Cost Mismatch: Money Left on the Table\n"
              f"Gap = {gap:,.0f}  ({pct:.3f}% over optimal)")
    plt.ylabel("Total execution cost (power-law model)")
    plt.grid(True, axis="y", alpha=0.3)
    plt.tight_layout()

    if save_path is not None:
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close()


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
    if beta_values is None:
        beta_values = [0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]

    params = set_params()
    linear_traj = optimal_trajectory_linear(params)

    gaps = []
    pct_gaps = []
    pl_costs = []
    lin_costs = []

    print(f"{'beta':>6s} {'pl_optimal_cost':>20s} {'linear_under_pl':>20s} "
          f"{'gap':>16s} {'gap_%':>10s}")
    print("-" * 76)
    for b in beta_values:
        pl_traj = optimal_trajectory_power_law(params, beta=b)
        pl_cost = compute_cost_power_law(pl_traj, params, beta=b)
        lin_cost = compute_cost_power_law(linear_traj, params, beta=b)
        gap = lin_cost - pl_cost
        pct = (gap / pl_cost) * 100.0 if pl_cost > 0 else 0.0
        gaps.append(gap)
        pct_gaps.append(pct)
        pl_costs.append(pl_cost)
        lin_costs.append(lin_cost)
        print(f"{b:>6.2f} {pl_cost:>20,.2f} {lin_cost:>20,.2f} "
              f"{gap:>16,.2f} {pct:>9.3f}%")

    fig, ax1 = plt.subplots(figsize=(10, 6))
    ax1.plot(beta_values, gaps, "o-", color="#d7301f", linewidth=2,
             label="Absolute gap ($)")
    ax1.set_xlabel(r"Power-law exponent $\beta$")
    ax1.set_ylabel("Cost gap (money left on the table)", color="#d7301f")
    ax1.tick_params(axis="y", labelcolor="#d7301f")
    ax1.grid(True, alpha=0.3)
    ax1.axhline(0, color="gray", linewidth=0.8)

    ax2 = ax1.twinx()
    ax2.plot(beta_values, pct_gaps, "s--", color="#2b8cbe", linewidth=2,
             label="Relative gap (%)")
    ax2.set_ylabel("Relative gap (%)", color="#2b8cbe")
    ax2.tick_params(axis="y", labelcolor="#2b8cbe")

    plt.title(r"Cost Gap vs. Power-Law Exponent $\beta$"
              "\n(linear trajectory's excess cost under true power-law impact)")
    fig.tight_layout()

    if save_path is not None:
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)

    return {
        "beta_values": list(beta_values),
        "gaps": gaps,
        "pct_gaps": pct_gaps,
        "pl_costs": pl_costs,
        "lin_costs": lin_costs,
    }


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
    if gamma_values is None:
        gamma_values = [1e-7, 1e-6, 2.5e-6, 1e-5, 1e-4]

    fig, axes = plt.subplots(1, len(gamma_values), figsize=(4 * len(gamma_values), 5),
                              sharey=True)
    if len(gamma_values) == 1:
        axes = [axes]

    for ax, g in zip(axes, gamma_values):
        p = set_params(gamma=g)
        N = p["N"]
        k = np.arange(N + 1)
        lin = optimal_trajectory_linear(p)
        pl = optimal_trajectory_power_law(p, beta=beta)
        ax.plot(k, lin, "b-", linewidth=2, label=r"Linear ($\beta=1.0$)")
        ax.plot(k, pl, "r--", linewidth=2, label=rf"Power-Law ($\beta={beta}$)")
        ax.set_title(rf"$\gamma={g:.1e}$")
        ax.set_xlabel("Period k")
        ax.grid(True, alpha=0.3)

    axes[0].set_ylabel("Remaining inventory")
    axes[0].legend(loc="upper right", fontsize=9)
    fig.suptitle("Trajectory Sensitivity to Risk Aversion (gamma)")
    fig.tight_layout()

    if save_path is not None:
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


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
    sweep = cost_gap_vs_beta(
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

    # ---------------------------------------------------------------
    # SUMMARY TABLE
    # ---------------------------------------------------------------
    print("\n" + "=" * 78)
    print("SUMMARY TABLE")
    print("=" * 78)
    header = f"{'Model':<22s} {'Optimal cost':>16s} {'Cost under wrong model':>24s} {'$ gap':>12s}"
    print(header)
    print("-" * 78)
    print(f"{'Linear (beta=1.0)':<22s} "
          f"{results['linear_cost_linear']:>16,.2f} "
          f"{results['pl_cost_linear']:>24,.2f} "
          f"{results['cost_gap']:>12,.2f}")
    print(f"{'Power-Law (beta=0.6)':<22s} "
          f"{results['pl_cost_pl']:>16,.2f} "
          f"{results['linear_cost_pl']:>24,.2f} "
          f"{results['linear_cost_pl'] - results['linear_cost_linear']:>12,.2f}")
    print("-" * 78)
    print(f"Relative cost gap of linear strategy under true power-law impact: "
          f"{results['cost_gap_pct']:.4f}%")

    print("\nCost gap vs. beta (sweep):")
    print(f"{'beta':>6s} {'gap ($)':>16s} {'gap (%)':>12s}")
    for b, g, p in zip(sweep["beta_values"], sweep["gaps"], sweep["pct_gaps"]):
        print(f"{b:>6.2f} {g:>16,.2f} {p:>11.4f}%")

    print("\n" + "=" * 78)
    print("FIGURES GENERATED")
    print("=" * 78)
    for fn in [
        "trajectory_comparison.png",
        "trade_rate_comparison.png",
        "cost_mismatch.png",
        "cost_gap_vs_beta.png",
        "gamma_sensitivity_comparison.png",
    ]:
        print(f"  - figures/{fn}")

    print(f"\nAll figures saved to {FIGURES_DIR}/")
    print("Done!")
