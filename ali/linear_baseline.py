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
    params = {
        'X': X,
        'N': N,
        'sigma': sigma,
        'gamma': gamma,
        'eta': eta,
        'tau': 1.0 / N,   # length of each trading interval (T=1 day)
    }
    return params


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
    X = params['X']
    N = params['N']
    sigma = params['sigma']
    gamma = params['gamma']
    eta = params['eta']
    
    # Compute kappa — the urgency parameter.
    # Note: This is the small-lambda/eta approximation. The exact discrete-time
    # kappa is arccosh(1 + gamma*sigma^2/(2*eta)). For the baseline parameters
    # the difference is negligible (< 1e-10).
    kappa = np.sqrt(gamma * sigma**2 / eta)
    
    # Apply closed-form solution: x_k = X * sinh(kappa * (N - k)) / sinh(kappa * N)
    k_values = np.arange(N + 1)   # k goes from 0 to N inclusive
    trajectory = X * np.sinh(kappa * (N - k_values)) / np.sinh(kappa * N)
    
    return trajectory


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
    trade_list = trajectory[:-1] - trajectory[1:]
    return trade_list


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
    N = params['N']
    sigma = params['sigma']
    gamma = params['gamma']
    eta = params['eta']
    
    trade_list = compute_trade_list(trajectory)
    
    # Temporary impact cost: eta * sum(v_k^2)
    impact_cost = eta * np.sum(trade_list**2)
    
    # Risk penalty: gamma * sigma^2 * sum(x_k^2) for k=1..N
    risk_cost = gamma * sigma**2 * np.sum(trajectory[1:]**2)
    
    total_cost = impact_cost + risk_cost
    return total_cost


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
    N = params['N']
    k_values = np.arange(N + 1)
    
    plt.figure(figsize=(10, 6))
    plt.plot(k_values, trajectory, 'b-o', markersize=4, linewidth=1.5)
    plt.xlabel("Trading Period k")
    plt.ylabel("Remaining Inventory x_k (shares)")
    plt.title(title)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=150)
        plt.close()
    else:
        plt.show()


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
    N = params['N']
    k_values = np.arange(1, N + 1)   # periods 1 through N
    
    plt.figure(figsize=(10, 6))
    plt.bar(k_values, trade_list, color='steelblue', edgecolor='black', alpha=0.8)
    plt.xlabel("Trading Period k")
    plt.ylabel("Shares Traded v_k")
    plt.title(title)
    plt.grid(True, alpha=0.3, axis='y')
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=150)
        plt.close()
    else:
        plt.show()


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
    if gamma_values is None:
        gamma_values = [1e-7, 1e-5, 1e-3, 1e-2, 1e-1]
    
    plt.figure(figsize=(10, 6))
    
    for gamma in gamma_values:
        params = set_params(gamma=gamma)
        trajectory = optimal_trajectory_linear(params)
        k_values = np.arange(params['N'] + 1)
        plt.plot(k_values, trajectory, '-o', markersize=3, 
                 label=f'γ = {gamma:.0e}')
    
    plt.xlabel("Trading Period k")
    plt.ylabel("Remaining Inventory x_k (shares)")
    plt.title("Linear Model — Trajectory Sensitivity to Risk Aversion (γ)")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=150)
        plt.close()
    else:
        plt.show()

def plot_trade_rate_sensitivity(gamma_values=None, save_path=None):
    """
    Compare trading rates (bar charts) across different risk aversion levels.
    Shows how trading patterns shift from uniform (TWAP) to front-loaded
    as risk aversion increases.
    """
    if gamma_values is None:
        gamma_values = [1e-7, 1e-3, 1e-1]
    
    fig, axes = plt.subplots(1, len(gamma_values), figsize=(18, 5), sharey=False)
    
    for ax, gamma in zip(axes, gamma_values):
        params = set_params(gamma=gamma)
        trajectory = optimal_trajectory_linear(params)
        trade_list = compute_trade_list(trajectory)
        k_values = np.arange(1, params['N'] + 1)
        
        ax.bar(k_values, trade_list, color='steelblue', edgecolor='black', alpha=0.8)
        ax.set_xlabel("Trading Period k")
        ax.set_title(f"γ = {gamma:.0e}")
        ax.grid(True, alpha=0.3, axis='y')
    
    axes[0].set_ylabel("Shares Traded v_k")
    fig.suptitle("Trading Rate Shifts with Risk Aversion", fontsize=14)
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=150)
        plt.close()
    else:
        plt.show()

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
    impact_only = params['eta'] * np.sum(trade_list**2)
    risk_only = params['gamma'] * params['sigma']**2 * np.sum(trajectory[1:]**2)
    print(f"Impact cost (real money lost):  ${impact_only:,.2f}")
    print(f"Risk penalty (not real money):  ${risk_only:,.2f}")  
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
        gamma_values=[1e-7, 1e-5, 1e-3, 1e-2, 1e-1],
        save_path=os.path.join(FIGURES_DIR, "linear_gamma_sensitivity.png")
    )
    plot_trade_rate_sensitivity(
        gamma_values=[1e-7, 1e-3, 1e-1],
        save_path=os.path.join(FIGURES_DIR, "linear_trade_rate_sensitivity.png")
    )
    print(f"\nFigures saved to {FIGURES_DIR}/")