"""
Magnitude distribution and Gutenberg-Richter analysis.

Produces:
  outputs/figures/magnitude_histogram.png
  outputs/figures/magnitude_ecdf.png
  outputs/figures/gutenberg_richter.png
  outputs/tables/magnitude_summary.csv
  outputs/tables/gr_fit.csv

Gutenberg-Richter (G-R) analysis:
  log10(N) = a - b*M
  Fit using maximum-likelihood Aki estimator for b-value (valid for complete catalog).
  CAUTION: Only applied to the post-2007 period where catalog appears more complete.
  The b-value is sensitive to catalog completeness; do NOT extrapolate to the full
  historical catalog without careful completeness analysis (Mc estimation).
"""

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROC_DIR     = PROJECT_ROOT / "data_processed"
FIG_DIR      = PROJECT_ROOT / "outputs" / "figures"
TBL_DIR      = PROJECT_ROOT / "outputs" / "tables"

STYLE = {
    "font.family": "DejaVu Sans",
    "font.size":   11,
    "axes.spines.top":   False,
    "axes.spines.right": False,
    "axes.grid":         True,
    "grid.alpha":        0.35,
    "figure.dpi":        150,
    "savefig.dpi":       150,
    "savefig.bbox":      "tight",
}
plt.rcParams.update(STYLE)


def load_catalog() -> pd.DataFrame:
    df = pd.read_csv(PROC_DIR / "master_catalog_spatial_v2.csv", low_memory=False)
    _dup_col = "duplicate_flag_v2" if "duplicate_flag_v2" in df.columns else "duplicate_flag"
    df = df[~df[_dup_col].astype(bool)].copy()
    df["magnitude"] = pd.to_numeric(df["magnitude"], errors="coerce")
    df["year"]      = pd.to_numeric(df["year"], errors="coerce").astype("Int64")
    return df


def aki_b_value(magnitudes: np.ndarray, mc: float) -> tuple[float, float]:
    """
    Aki (1965) maximum-likelihood b-value estimator.
    b = log10(e) / (mean(M) - Mc)
    Returns (b, std_b).
    """
    mags = magnitudes[magnitudes >= mc]
    n    = len(mags)
    if n < 10:
        return np.nan, np.nan
    mean_m = mags.mean()
    b = np.log10(np.e) / (mean_m - mc)
    # Standard error (Shi & Bolt 1982)
    std_b = 2.30 * b**2 * np.std(mags, ddof=1) / np.sqrt(n)
    return b, std_b


def gutenberg_richter_fit(magnitudes: np.ndarray, mc: float) -> dict:
    """
    Fit G-R relation log10(N≥M) = a - b*M.
    Returns dict of fit parameters.
    """
    mags = magnitudes[magnitudes >= mc]
    n    = len(mags)
    if n < 10:
        return {}

    # Cumulative counts
    mag_bins = np.arange(mc, mags.max() + 0.1, 0.1)
    cum_counts = np.array([np.sum(mags >= m) for m in mag_bins])
    nonzero    = cum_counts > 0

    # Linear fit in log10 space
    slope, intercept, r, p, se = stats.linregress(
        mag_bins[nonzero],
        np.log10(cum_counts[nonzero]),
    )

    b_aki, std_b = aki_b_value(mags, mc)

    return {
        "n_events":    n,
        "mc":          mc,
        "b_linreg":    -slope,   # sign convention: b is positive
        "a_linreg":    intercept,
        "r_squared":   r**2,
        "b_aki_mle":   b_aki,
        "std_b_aki":   std_b,
        "mean_mag":    mags.mean(),
        "mag_min":     mags.min(),
        "mag_max":     mags.max(),
        # For the fit line
        "_mag_bins":   mag_bins[nonzero],
        "_fit_logN":   intercept + slope * mag_bins[nonzero],
        "_obs_logN":   np.log10(cum_counts[nonzero]),
    }


# ── Figures ────────────────────────────────────────────────────────────────────

def fig_magnitude_histogram(df: pd.DataFrame):
    mags = df["magnitude"].dropna()

    fig, axes = plt.subplots(1, 2, figsize=(13, 5))

    # All events
    ax = axes[0]
    ax.hist(mags, bins=np.arange(2.0, 9.5, 0.2), color="#4e8fbd", alpha=0.8, edgecolor="white")
    ax.axvline(4.0, color="#cc2020", ls="--", lw=1.5, label="M=4.0")
    ax.axvline(5.0, color="#e07020", ls="--", lw=1.5, label="M=5.0")
    ax.set_xlabel("Magnitude")
    ax.set_ylabel("Count")
    ax.set_title(f"Magnitude Histogram — All Events (n={len(mags)})")
    ax.legend(fontsize=9)

    # Modern period (2007+) for comparison
    ax = axes[1]
    modern = df[(df["year"] >= 2007)]["magnitude"].dropna()
    ax.hist(modern, bins=np.arange(2.0, 9.5, 0.2), color="#e07020", alpha=0.8, edgecolor="white")
    ax.axvline(4.0, color="#cc2020", ls="--", lw=1.5, label="M=4.0")
    ax.set_xlabel("Magnitude")
    ax.set_ylabel("Count")
    ax.set_title(f"Magnitude Histogram — 2007–2025 (n={len(modern)})")
    ax.legend(fontsize=9)

    plt.suptitle("Magnitude Distribution — Bangladesh Earthquake Catalog", fontweight="bold")
    plt.tight_layout()
    fig.savefig(FIG_DIR / "magnitude_histogram.png")
    plt.close(fig)
    print("  Saved: magnitude_histogram.png")


def fig_ecdf(df: pd.DataFrame):
    """Empirical CDF of magnitudes."""
    mags = df["magnitude"].dropna().sort_values()

    fig, ax = plt.subplots(figsize=(8, 5))
    ecdf = np.arange(1, len(mags) + 1) / len(mags)
    ax.step(mags, ecdf, color="#4e8fbd", lw=2, label="All events")

    modern = df[(df["year"] >= 2007)]["magnitude"].dropna().sort_values()
    ecdf_m = np.arange(1, len(modern) + 1) / len(modern)
    ax.step(modern, ecdf_m, color="#e07020", lw=2, ls="--", label="2007+ only")

    for mv in [3.0, 4.0, 5.0]:
        ax.axvline(mv, color="gray", ls=":", lw=1)
        ax.text(mv + 0.03, 0.02, f"M{mv:.0f}", color="gray", fontsize=8)

    ax.set_xlabel("Magnitude")
    ax.set_ylabel("Cumulative proportion")
    ax.set_title("Empirical CDF of Magnitudes")
    ax.legend()

    plt.tight_layout()
    fig.savefig(FIG_DIR / "magnitude_ecdf.png")
    plt.close(fig)
    print("  Saved: magnitude_ecdf.png")


def fig_gutenberg_richter(df: pd.DataFrame):
    """
    G-R plot for the post-2007 felt/modern catalog.
    Apply Mc estimation heuristically at M=3.0 (conservative).
    """
    modern = df[(df["year"] >= 2007)]["magnitude"].dropna().values
    mc     = 3.0  # conservative completeness threshold

    gr = gutenberg_richter_fit(modern, mc)
    if not gr:
        print("  Skipping G-R plot: insufficient data")
        return gr

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.scatter(gr["_mag_bins"], gr["_obs_logN"],
               color="#4e8fbd", s=40, zorder=5, label="Observed cumulative N")
    ax.plot(gr["_mag_bins"], gr["_fit_logN"],
            color="#cc2020", lw=2.5, label=(
                f"G-R fit: b={gr['b_linreg']:.2f}, R²={gr['r_squared']:.3f}\n"
                f"Aki MLE b={gr['b_aki_mle']:.2f}±{gr['std_b_aki']:.2f}"
            ))
    ax.axvline(mc, color="gray", ls="--", lw=1.5, label=f"Mc={mc}")

    ax.set_xlabel("Magnitude (M)")
    ax.set_ylabel("log₁₀(N ≥ M)")
    ax.set_title(
        f"Gutenberg-Richter Relation — 2007–2025 (n={gr['n_events']} events, Mc≥{mc})\n"
        "⚠ Preliminary — Mc estimated conservatively; treat b-value as indicative only"
    )
    ax.legend(fontsize=9)

    plt.tight_layout()
    fig.savefig(FIG_DIR / "gutenberg_richter.png")
    plt.close(fig)
    print("  Saved: gutenberg_richter.png")

    return gr


def save_magnitude_summary(df: pd.DataFrame):
    """Save a table of magnitude summary statistics."""
    rows = []
    periods = {
        "All events":    df,
        "Pre-2000":      df[df["year"] < 2000],
        "2000–2006":     df[(df["year"] >= 2000) & (df["year"] <= 2006)],
        "2007–2022":     df[(df["year"] >= 2007) & (df["year"] <= 2022)],
        "2023–2025":     df[df["year"] >= 2023],
    }
    for label, sub in periods.items():
        mags = sub["magnitude"].dropna()
        rows.append({
            "Period":    label,
            "N_events":  len(sub),
            "N_with_mag":len(mags),
            "Mag_min":   round(mags.min(), 1) if len(mags) else np.nan,
            "Mag_max":   round(mags.max(), 1) if len(mags) else np.nan,
            "Mag_mean":  round(mags.mean(), 2) if len(mags) else np.nan,
            "Mag_median":round(mags.median(), 2) if len(mags) else np.nan,
            "N_M4plus":  (mags >= 4.0).sum(),
            "N_M5plus":  (mags >= 5.0).sum(),
            "N_M6plus":  (mags >= 6.0).sum(),
            "N_M7plus":  (mags >= 7.0).sum(),
        })

    tbl = pd.DataFrame(rows)
    tbl.to_csv(TBL_DIR / "magnitude_summary.csv", index=False)
    print("  Saved: magnitude_summary.csv")
    print(tbl.to_string(index=False))
    return tbl


def main():
    print("Loading catalog...")
    df = load_catalog()
    print(f"  Events: {len(df)}")

    print("\nMagnitude summary:")
    tbl = save_magnitude_summary(df)

    print("\nGenerating magnitude figures...")
    fig_magnitude_histogram(df)
    fig_ecdf(df)
    gr = fig_gutenberg_richter(df)

    # Save G-R fit results
    if gr:
        gr_out = {k: v for k, v in gr.items() if not k.startswith("_")}
        pd.DataFrame([gr_out]).to_csv(TBL_DIR / "gr_fit.csv", index=False)
        print(f"\n  G-R b-value (linear): {gr['b_linreg']:.3f}")
        print(f"  G-R b-value (Aki MLE): {gr['b_aki_mle']:.3f} ± {gr['std_b_aki']:.3f}")
        print(f"  R²: {gr['r_squared']:.3f}")

    print("\nDone.")


if __name__ == "__main__":
    main()
