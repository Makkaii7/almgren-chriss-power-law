"""
combined/kappa_sweep.py
=========================

Urgency sensitivity analysis added per professor's feedback.

κ = √(γ σ² / η) is the urgency parameter that bundles risk aversion,
volatility, and impact cost into a single dimensionless number.  We sweep
κ across nine values (0.001 → 5.0) by varying γ while holding σ and η at
their baseline values, then measure the certainty-equivalent excess cost
of using the linear strategy when reality follows the power-law impact
rule.

Outputs:
    figures/cost_gap_vs_kappa.png
    combined/kappa_sweep_results.npz
"""
import os
import sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_ROOT)
FIGURES_DIR = os.path.join(REPO_ROOT, "figures")

from ali.linear_baseline import (
    set_params,
    optimal_trajectory_linear,
    compute_cost_linear,
)
from combined.verify_cvxpy import optimal_trajectory_power_law_cvxpy
from mohamed.power_law_extension import compute_cost_power_law


KAPPA_VALUES = [0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0]
BETA = 0.6


def gamma_from_kappa(kappa, sigma, eta):
    """κ = √(γσ²/η)  ⇒  γ = κ² η / σ²"""
    return (kappa ** 2) * eta / (sigma ** 2)


def main():
    base = set_params()
    sigma = base["sigma"]
    eta = base["eta"]

    print("=" * 96)
    print(f"KAPPA SWEEP — Cost gap of linear strategy under power-law impact (β = {BETA})")
    print("=" * 96)
    print(f"Holding σ = {sigma} and η = {eta} fixed; varying γ via κ = √(γσ²/η).")
    print()
    hdr = (f"{'kappa':>8s} | {'gamma':>12s} | "
           f"{'linear @ pl':>16s} | {'power-law opt':>16s} | "
           f"{'abs gap':>14s} | {'rel gap %':>10s}")
    print(hdr)
    print("-" * len(hdr))

    rows = []
    for kappa in KAPPA_VALUES:
        gamma = gamma_from_kappa(kappa, sigma, eta)
        params = set_params(gamma=gamma)

        linear_traj = optimal_trajectory_linear(params)
        pl_traj, _obj, _status = optimal_trajectory_power_law_cvxpy(
            params, beta=BETA)

        c_lin_pl = compute_cost_power_law(linear_traj, params, beta=BETA)
        c_pl_pl = compute_cost_power_law(pl_traj, params, beta=BETA)
        abs_gap = c_lin_pl - c_pl_pl
        rel_gap = (abs_gap / c_pl_pl) * 100.0 if c_pl_pl > 0 else float("nan")

        rows.append({
            "kappa": kappa,
            "gamma": gamma,
            "linear_at_pl": c_lin_pl,
            "pl_at_pl": c_pl_pl,
            "abs_gap": abs_gap,
            "rel_gap_pct": rel_gap,
        })
        print(f"{kappa:>8.3f} | {gamma:>12.3e} | "
              f"{c_lin_pl:>16,.2f} | {c_pl_pl:>16,.2f} | "
              f"{abs_gap:>14,.2f} | {rel_gap:>9.4f}%")

    # ------------------------------------------------------------------
    # Threshold crossings
    # ------------------------------------------------------------------
    thresholds = [1.0, 10.0, 50.0, 100.0]
    crossings = {}
    for thr in thresholds:
        first = next((r["kappa"] for r in rows if r["rel_gap_pct"] >= thr), None)
        crossings[thr] = first
    print()
    print("Relative gap threshold crossings:")
    for thr in thresholds:
        v = crossings[thr]
        print(f"  first κ ≥ {thr:>5.0f}% gap : "
              f"{v if v is not None else 'never reached in this sweep'}")

    # ------------------------------------------------------------------
    # Save data
    # ------------------------------------------------------------------
    npz_path = os.path.join(REPO_ROOT, "combined", "kappa_sweep_results.npz")
    np.savez(
        npz_path,
        kappas=np.array([r["kappa"] for r in rows]),
        gammas=np.array([r["gamma"] for r in rows]),
        linear_at_pl=np.array([r["linear_at_pl"] for r in rows]),
        pl_at_pl=np.array([r["pl_at_pl"] for r in rows]),
        abs_gaps=np.array([r["abs_gap"] for r in rows]),
        rel_gaps_pct=np.array([r["rel_gap_pct"] for r in rows]),
        beta=np.float64(BETA),
    )
    print(f"\nData saved: {npz_path}")

    # ------------------------------------------------------------------
    # Chart — pair-style with cost_gap_vs_beta.png
    # ------------------------------------------------------------------
    kappas = np.array([r["kappa"] for r in rows])
    abs_gaps = np.array([r["abs_gap"] for r in rows])
    rel_gaps = np.array([r["rel_gap_pct"] for r in rows])

    RED = "#d7301f"
    BLUE = "#2b8cbe"

    fig, ax1 = plt.subplots(figsize=(12, 6.5))

    # Regime shading + annotations (left/middle/right)
    ax1.axvspan(1e-4, 0.01, color="#e8f4ea", alpha=0.55, zorder=0)
    ax1.axvspan(0.01, 0.5, color="#fdf3d8", alpha=0.55, zorder=0)
    ax1.axvspan(0.5, 1e2, color="#f9dad5", alpha=0.55, zorder=0)

    # Absolute gap
    ax1.plot(kappas, abs_gaps, "o-", color=RED, linewidth=2.2,
             markersize=7, label="Absolute gap ($)")
    ax1.set_xscale("log")
    ax1.set_xlabel(r"Urgency parameter  $\kappa = \sqrt{\gamma\sigma^2 / \eta}$",
                   fontsize=12)
    ax1.set_ylabel("Absolute cost gap (dollars)", color=RED, fontsize=12)
    ax1.tick_params(axis="y", labelcolor=RED)
    ax1.grid(True, which="both", alpha=0.3, zorder=1)
    ax1.set_xlim(min(kappas) * 0.6, max(kappas) * 1.6)

    # Relative gap on twin axis
    ax2 = ax1.twinx()
    ax2.plot(kappas, rel_gaps, "s--", color=BLUE, linewidth=2.2,
             markersize=7, label="Relative gap (%)")
    ax2.set_ylabel("Relative cost gap (% of optimum)", color=BLUE, fontsize=12)
    ax2.tick_params(axis="y", labelcolor=BLUE)

    # Regime labels at top of plot
    y_top = ax1.get_ylim()[1]
    ax1.text(0.0032, y_top * 0.96, "Patient", ha="center",
             fontsize=11, color="#3a7d44", fontweight="bold")
    ax1.text(0.07, y_top * 0.96, "Moderate", ha="center",
             fontsize=11, color="#9a7b06", fontweight="bold")
    ax1.text(2.2, y_top * 0.96, "Panicked", ha="center",
             fontsize=11, color="#a23028", fontweight="bold")

    # Title
    plt.suptitle(r"Transaction Cost Gap vs $\kappa$  (Urgency)",
                 fontsize=15, fontweight="bold", y=0.995)
    ax1.set_title("Linear strategy's certainty-equivalent excess cost "
                  "under power-law impact",
                  fontsize=11, color="#444", pad=12)

    # Combined legend
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper left",
               framealpha=0.92)

    fig.tight_layout()
    out_path = os.path.join(FIGURES_DIR, "cost_gap_vs_kappa.png")
    os.makedirs(FIGURES_DIR, exist_ok=True)
    plt.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Figure saved: {out_path}")

    return rows, crossings


def generate_two_line_chart():
    """
    Reload saved κ-sweep data and emit a side-by-side comparison of the two
    strategies' total transaction costs (per professor's "different
    transaction cost outcomes" wording — both costs visible, not just the
    gap).
    """
    npz_path = os.path.join(REPO_ROOT, "combined", "kappa_sweep_results.npz")
    data = np.load(npz_path)
    kappas = data["kappas"]
    linear_at_pl = data["linear_at_pl"]
    pl_at_pl = data["pl_at_pl"]

    RED = "#d7301f"
    BLUE = "#2b8cbe"

    fig, ax = plt.subplots(figsize=(12, 6.5))

    # Regime shading — patient / moderate / panicked
    ax.axvspan(min(kappas) * 0.5, 0.01, color="#e6e6e6", alpha=0.55, zorder=0)
    ax.axvspan(0.01, 0.5,                 color="#fde7c1", alpha=0.55, zorder=0)
    ax.axvspan(0.5,  max(kappas) * 2.0,   color="#f6c8c1", alpha=0.55, zorder=0)

    # Two cost lines — same axes, log-scale Y
    ax.plot(kappas, linear_at_pl, "o-", color=RED, linewidth=2.4,
            markersize=8, label="Linear strategy cost (under power-law impact)")
    ax.plot(kappas, pl_at_pl, "s-", color=BLUE, linewidth=2.4,
            markersize=8, label="Power-law optimal cost")

    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xticks(kappas)
    ax.set_xticklabels([f"{k:g}" for k in kappas])
    ax.set_xlim(min(kappas) * 0.6, max(kappas) * 1.6)

    ax.set_xlabel(r"Urgency parameter  $\kappa = \sqrt{\gamma\sigma^2/\eta}$",
                  fontsize=12)
    ax.set_ylabel("Total transaction cost (dollars, log scale)", fontsize=12)
    ax.grid(True, which="both", alpha=0.3, zorder=1)

    # Regime labels at the top
    y_top = ax.get_ylim()[1]
    ax.text(0.0032, y_top * 0.6, "Patient", ha="center",
            fontsize=11, color="#404040", fontweight="bold")
    ax.text(0.07,   y_top * 0.6, "Moderate urgency", ha="center",
            fontsize=11, color="#9a7b06", fontweight="bold")
    ax.text(2.2,    y_top * 0.6, "Panicked", ha="center",
            fontsize=11, color="#a23028", fontweight="bold")

    # Title + subtitle
    plt.suptitle("Transaction Costs vs Kappa (Urgency Parameter)",
                 fontsize=15, fontweight="bold", y=0.995)
    ax.set_title("Linear and power-law strategies compared across the "
                 "urgency spectrum",
                 fontsize=11, color="#444", pad=12)

    ax.legend(loc="upper left", framealpha=0.92, fontsize=11)

    fig.tight_layout()
    out_path = os.path.join(FIGURES_DIR, "cost_vs_kappa_two_line.png")
    os.makedirs(FIGURES_DIR, exist_ok=True)
    plt.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Figure saved: {out_path}")
    return out_path


if __name__ == "__main__":
    main()
    generate_two_line_chart()
