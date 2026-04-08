"""
Temporal analysis of the Bangladesh earthquake catalog.

Produces:
  outputs/figures/temporal_annual_counts.png
  outputs/figures/temporal_decadal_summary.png
  outputs/figures/temporal_magnitude_stacked.png
  outputs/figures/temporal_rolling_avg.png
  outputs/figures/temporal_seasonality.png
  outputs/tables/temporal_annual_counts.csv
  outputs/tables/temporal_decadal_summary.csv

CAUTION: Catalog completeness varies strongly across the study period.
  - Pre-2000: Only significant events (M≥4.5 approximately) recorded.
  - 2000-2006: Sparse — apparent gap, possibly reporting gap.
  - 2007+: More systematic, lower-magnitude threshold.
  - 2023+: Multiple overlapping sources; modern felt-near-BD catalog.
  Count increases in recent decades likely reflect improved monitoring,
  NOT increased seismicity. All count-trend conclusions must be made
  with completeness caveats.
"""

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROC_DIR     = PROJECT_ROOT / "data_processed"
FIG_DIR      = PROJECT_ROOT / "outputs" / "figures"
TBL_DIR      = PROJECT_ROOT / "outputs" / "tables"
FIG_DIR.mkdir(parents=True, exist_ok=True)
TBL_DIR.mkdir(parents=True, exist_ok=True)

STYLE = {
    "font.family":   "DejaVu Sans",
    "font.size":     11,
    "axes.spines.top":    False,
    "axes.spines.right":  False,
    "axes.grid":          True,
    "grid.alpha":         0.35,
    "figure.dpi":         150,
    "savefig.dpi":        150,
    "savefig.bbox":       "tight",
}
plt.rcParams.update(STYLE)

COMPLETENESS_NOTE = (
    "⚠ Catalog completeness varies by era. "
    "Count trends reflect detection improvements, not real seismicity changes."
)

# Magnitude bands for colour coding
MAG_BANDS = {
    "M<3.0":   (0.0,  3.0, "#b3cde3"),
    "M3.0–3.9":(3.0,  4.0, "#8db6cd"),
    "M4.0–4.9":(4.0,  5.0, "#4e8fbd"),
    "M5.0–5.9":(5.0,  6.0, "#f4a460"),
    "M6.0–6.9":(6.0,  7.0, "#e07020"),
    "M≥7.0":   (7.0, 99.0, "#cc2020"),
}


def load_catalog() -> pd.DataFrame:
    df = pd.read_csv(PROC_DIR / "master_catalog_spatial.csv", low_memory=False)
    df = df[df["duplicate_flag"] == False].copy()
    df["year"]  = pd.to_numeric(df["year"],  errors="coerce").astype("Int64")
    df["month"] = pd.to_numeric(df["month"], errors="coerce").astype("Int64")
    df["decade"] = pd.to_numeric(df["decade"], errors="coerce").astype("Int64")
    df["magnitude"] = pd.to_numeric(df["magnitude"], errors="coerce")
    return df


def assign_mag_band(mag: float) -> str:
    for label, (lo, hi, _) in MAG_BANDS.items():
        if lo <= mag < hi:
            return label
    return "M≥7.0"


# ── Figure 1: Annual event counts ─────────────────────────────────────────────

def fig_annual_counts(df: pd.DataFrame):
    annual = (
        df.dropna(subset=["year"])
          .groupby("year")
          .size()
          .reset_index(name="count")
          .astype({"year": int})
    )

    # Rolling 5-year average
    annual = annual.set_index("year")
    annual["rolling5"] = annual["count"].rolling(5, center=True, min_periods=3).mean()

    fig, ax = plt.subplots(figsize=(14, 5))
    ax.bar(annual.index, annual["count"], color="#4e8fbd", alpha=0.7, label="Annual count", width=0.9)
    ax.plot(annual.index, annual["rolling5"], color="#cc2020", lw=2.5, label="5-yr rolling mean")

    # Mark key eras
    ax.axvspan(1918, 1999, alpha=0.05, color="gray", label="Pre-2000 (sparse)")
    ax.axvspan(2000, 2006, alpha=0.10, color="orange", label="2000–2006 (apparent gap)")

    ax.set_xlabel("Year")
    ax.set_ylabel("Number of events")
    ax.set_title("Annual Earthquake Event Counts — Bangladesh & Surroundings (1918–2025)")
    ax.legend(fontsize=9)
    ax.text(0.5, -0.18, COMPLETENESS_NOTE, ha="center", va="top",
            transform=ax.transAxes, fontsize=8, color="gray", style="italic")

    plt.tight_layout()
    fig.savefig(FIG_DIR / "temporal_annual_counts.png")
    plt.close(fig)
    print("  Saved: temporal_annual_counts.png")

    # Save table
    annual.reset_index().to_csv(TBL_DIR / "temporal_annual_counts.csv", index=False)
    return annual


# ── Figure 2: Decadal summary bar chart ───────────────────────────────────────

def fig_decadal_summary(df: pd.DataFrame):
    decadal = (
        df.dropna(subset=["decade", "magnitude"])
          .assign(mag_band=lambda x: x["magnitude"].apply(assign_mag_band))
          .groupby(["decade", "mag_band"])
          .size()
          .unstack(fill_value=0)
    )

    # Ensure all columns in correct order
    ordered_cols = [c for c in MAG_BANDS.keys() if c in decadal.columns]
    colours      = [MAG_BANDS[c][2] for c in ordered_cols]
    decadal_ord  = decadal[ordered_cols]

    fig, ax = plt.subplots(figsize=(12, 5))
    decadal_ord.plot(kind="bar", stacked=True, ax=ax, color=colours,
                     width=0.7, edgecolor="white", linewidth=0.5)

    ax.set_xlabel("Decade")
    ax.set_ylabel("Number of events")
    ax.set_title("Events by Decade and Magnitude Band — Bangladesh Earthquake Catalog")
    ax.set_xticklabels([f"{int(d)}s" for d in decadal_ord.index], rotation=45, ha="right")
    ax.legend(title="Magnitude band", bbox_to_anchor=(1.01, 1), loc="upper left", fontsize=9)
    ax.text(0.5, -0.22, COMPLETENESS_NOTE, ha="center", va="top",
            transform=ax.transAxes, fontsize=8, color="gray", style="italic")

    plt.tight_layout()
    fig.savefig(FIG_DIR / "temporal_decadal_summary.png")
    plt.close(fig)
    print("  Saved: temporal_decadal_summary.png")

    # Save table
    decadal.reset_index().to_csv(TBL_DIR / "temporal_decadal_summary.csv", index=False)
    return decadal


# ── Figure 3: Magnitude-stratified annual counts ──────────────────────────────

def fig_magnitude_stratified(df: pd.DataFrame):
    """Annual counts for three magnitude thresholds (M≥3, M≥4, M≥5)."""
    thresholds = [3.0, 4.0, 5.0]
    colours    = ["#4e8fbd", "#e07020", "#cc2020"]
    labels     = ["M≥3.0", "M≥4.0", "M≥5.0"]

    fig, axes = plt.subplots(3, 1, figsize=(14, 10), sharex=True)

    for ax, thr, col, lbl in zip(axes, thresholds, colours, labels):
        sub = df[df["magnitude"] >= thr].dropna(subset=["year"])
        counts = sub.groupby("year").size().astype(int)
        ax.bar(counts.index, counts.values, color=col, alpha=0.75, width=0.9)
        roll = counts.rolling(5, center=True, min_periods=3).mean()
        ax.plot(counts.index, roll.values, color="black", lw=1.8)
        ax.set_ylabel("Count")
        ax.set_title(f"{lbl} events per year (n={len(sub)})")
        ax.yaxis.set_major_locator(ticker.MaxNLocator(integer=True))

    axes[-1].set_xlabel("Year")
    axes[0].text(0.5, 1.05, COMPLETENESS_NOTE, ha="center", va="bottom",
                 transform=axes[0].transAxes, fontsize=8, color="gray", style="italic")

    fig.suptitle("Magnitude-Stratified Annual Event Counts", y=1.01, fontsize=13, fontweight="bold")
    plt.tight_layout()
    fig.savefig(FIG_DIR / "temporal_magnitude_stacked.png")
    plt.close(fig)
    print("  Saved: temporal_magnitude_stacked.png")


# ── Figure 4: Seasonality (month-of-year) ─────────────────────────────────────

def fig_seasonality(df: pd.DataFrame):
    """
    Month-of-year event frequency. Only include the post-2000 period to
    avoid completeness bias from the sparse historical record.
    """
    modern = df[(df["year"] >= 2007) & df["month"].notna()].copy()
    monthly_counts = modern.groupby("month").size()

    month_labels = ["Jan","Feb","Mar","Apr","May","Jun",
                    "Jul","Aug","Sep","Oct","Nov","Dec"]

    fig, ax = plt.subplots(figsize=(9, 4))
    bars = ax.bar(range(1, 13), monthly_counts.reindex(range(1, 13), fill_value=0),
                  color="#4e8fbd", alpha=0.8, edgecolor="white")
    ax.set_xticks(range(1, 13))
    ax.set_xticklabels(month_labels)
    ax.set_xlabel("Month")
    ax.set_ylabel("Number of events")
    ax.set_title("Seasonality: Events by Month of Year\n(2007–2025, post-completeness-threshold period)")
    ax.axhline(monthly_counts.mean(), color="#e07020", lw=2, ls="--",
               label=f"Mean = {monthly_counts.mean():.0f}")
    ax.legend()

    plt.tight_layout()
    fig.savefig(FIG_DIR / "temporal_seasonality.png")
    plt.close(fig)
    print("  Saved: temporal_seasonality.png")


# ── Figure 5: Decade-wise magnitude composition (box plots) ───────────────────

def fig_decade_magnitude_box(df: pd.DataFrame):
    df_plot = df.dropna(subset=["decade", "magnitude"]).copy()
    df_plot = df_plot[df_plot["decade"] >= 2000]  # modern period only
    decades = sorted(df_plot["decade"].unique())

    data_by_decade = [df_plot[df_plot["decade"] == d]["magnitude"].dropna().values
                      for d in decades]
    labels = [f"{int(d)}s" for d in decades]

    fig, ax = plt.subplots(figsize=(10, 5))
    bp = ax.boxplot(data_by_decade, labels=labels, patch_artist=True,
                    medianprops=dict(color="black", lw=2))

    colors = ["#b3cde3", "#8db6cd", "#4e8fbd"][:len(decades)]
    for patch, color in zip(bp["boxes"], colors):
        patch.set_facecolor(color)

    ax.set_xlabel("Decade")
    ax.set_ylabel("Magnitude")
    ax.set_title("Magnitude Distribution by Decade (2000–2025)")

    plt.tight_layout()
    fig.savefig(FIG_DIR / "temporal_decade_magnitude_box.png")
    plt.close(fig)
    print("  Saved: temporal_decade_magnitude_box.png")


def main():
    print("Loading catalog...")
    df = load_catalog()
    print(f"  Events: {len(df)}  |  Year range: {df['year'].min()}–{df['year'].max()}")

    print("\nGenerating temporal analysis figures...")
    fig_annual_counts(df)
    fig_decadal_summary(df)
    fig_magnitude_stratified(df)
    fig_seasonality(df)
    fig_decade_magnitude_box(df)

    print("\nDone.")


if __name__ == "__main__":
    main()
