"""
Cross-border seismic dependence analysis.

Key question: To what degree is Bangladesh exposed to seismicity originating
OUTSIDE its borders? What is the source-region composition, and has it changed
over time?

Produces:
  outputs/figures/crossborder_pie_charts.png
  outputs/figures/crossborder_by_decade.png
  outputs/figures/crossborder_magnitude_comparison.png
  outputs/figures/crossborder_distance_profile.png
  outputs/tables/crossborder_summary.csv
  outputs/tables/crossborder_by_decade.csv
  outputs/tables/source_country_by_magband.csv
"""

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import numpy as np
import pandas as pd

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
    df = pd.read_csv(PROC_DIR / "master_catalog_spatial.csv", low_memory=False)
    df = df[df["duplicate_flag"] == False].copy()
    df["magnitude"]         = pd.to_numeric(df["magnitude"],         errors="coerce")
    df["year"]              = pd.to_numeric(df["year"],               errors="coerce").astype("Int64")
    df["decade"]            = pd.to_numeric(df["decade"],             errors="coerce").astype("Int64")
    df["distance_dhaka_km"] = pd.to_numeric(df["distance_dhaka_km"], errors="coerce")
    df["inside_bangladesh"] = df["inside_bangladesh"].astype(bool)
    return df


# ── Figure 1: Pie charts — all / M≥4 / M≥5 ───────────────────────────────────

def fig_pie_charts(df: pd.DataFrame):
    thresholds = [
        ("All events",  df,                         ),
        ("M ≥ 4.0",    df[df["magnitude"] >= 4.0]  ),
        ("M ≥ 5.0",    df[df["magnitude"] >= 5.0]  ),
        ("M ≥ 6.0",    df[df["magnitude"] >= 6.0]  ),
    ]

    fig, axes = plt.subplots(1, 4, figsize=(18, 5))

    for ax, (label, sub) in zip(axes, thresholds):
        n_dom = sub["inside_bangladesh"].sum()
        n_ext = len(sub) - n_dom
        if len(sub) == 0:
            ax.text(0.5, 0.5, "No data", ha="center", va="center")
            ax.set_title(label)
            continue

        values = [n_dom, n_ext]
        slabels = [
            f"Inside BD\n{n_dom} ({n_dom/len(sub)*100:.0f}%)",
            f"Outside BD\n{n_ext} ({n_ext/len(sub)*100:.0f}%)",
        ]
        colors = ["#2ca02c", "#d62728"]
        wedge_props = dict(edgecolor="white", linewidth=2)
        ax.pie(values, labels=slabels, colors=colors,
               wedgeprops=wedge_props, startangle=90,
               textprops=dict(fontsize=9))
        ax.set_title(f"{label}\n(n={len(sub)})", fontsize=11)

    fig.suptitle("Cross-Border Seismic Dependence: Fraction of Events\nOriginating Inside vs Outside Bangladesh",
                 fontsize=13, fontweight="bold", y=1.02)
    plt.tight_layout()
    fig.savefig(FIG_DIR / "crossborder_pie_charts.png")
    plt.close(fig)
    print("  Saved: crossborder_pie_charts.png")


# ── Figure 2: Cross-border fraction by decade (modern) ───────────────────────

def fig_crossborder_by_decade(df: pd.DataFrame):
    modern = df[(df["year"] >= 2007)].dropna(subset=["decade"])

    decades = sorted(modern["decade"].unique())
    dom_pct = []
    ext_pct = []
    n_total = []

    for d in decades:
        sub = modern[modern["decade"] == d]
        n   = len(sub)
        nd  = sub["inside_bangladesh"].sum()
        dom_pct.append(nd / n * 100 if n else 0)
        ext_pct.append((n - nd) / n * 100 if n else 0)
        n_total.append(n)

    x      = np.arange(len(decades))
    labels = [f"{int(d)}s\n(n={n})" for d, n in zip(decades, n_total)]

    fig, ax = plt.subplots(figsize=(9, 5))
    ax.bar(x, ext_pct, color="#d62728", alpha=0.8, label="Outside BD (%)")
    ax.bar(x, dom_pct, color="#2ca02c", alpha=0.8, label="Inside BD (%)",
           bottom=ext_pct)
    ax.axhline(50, color="black", ls=":", lw=1)
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_ylabel("Percentage of events (%)")
    ax.set_ylim(0, 105)
    ax.set_title("Cross-Border Seismic Dependence by Decade (2007–2025)")
    ax.legend()

    plt.tight_layout()
    fig.savefig(FIG_DIR / "crossborder_by_decade.png")
    plt.close(fig)
    print("  Saved: crossborder_by_decade.png")


# ── Figure 3: Source-country magnitude comparison ─────────────────────────────

def fig_source_country_magnitude(df: pd.DataFrame):
    """Horizontal bar chart: events per country by magnitude band."""
    mag_bands = {
        "M<4.0":   (0,   4.0),
        "M4.0–4.9":(4.0, 5.0),
        "M5.0–5.9":(5.0, 6.0),
        "M≥6.0":   (6.0, 99),
    }
    colors = ["#b3cde3", "#4e8fbd", "#e07020", "#cc2020"]

    top_countries = (
        df["epicenter_country"]
          .value_counts()
          .head(8)
          .index.tolist()
    )

    sub = df[df["epicenter_country"].isin(top_countries)].copy()
    sub["mag_band"] = "M<4.0"
    for label, (lo, hi) in list(mag_bands.items())[1:]:
        sub.loc[(sub["magnitude"] >= lo) & (sub["magnitude"] < hi), "mag_band"] = label

    pivot = (
        sub.groupby(["epicenter_country", "mag_band"])
           .size()
           .unstack(fill_value=0)
           .reindex(columns=list(mag_bands.keys()), fill_value=0)
    )
    pivot = pivot.loc[top_countries]

    fig, ax = plt.subplots(figsize=(10, 6))
    pivot.plot(kind="barh", stacked=True, ax=ax, color=colors,
               width=0.7, edgecolor="white", linewidth=0.5)
    ax.set_xlabel("Number of events")
    ax.set_title("Events per Source Country by Magnitude Band\n(Top 8 countries)")
    ax.legend(title="Magnitude band", bbox_to_anchor=(1.01, 1), loc="upper left")
    ax.invert_yaxis()

    plt.tight_layout()
    fig.savefig(FIG_DIR / "crossborder_magnitude_comparison.png")
    plt.close(fig)
    print("  Saved: crossborder_magnitude_comparison.png")


# ── Figure 4: Distance profile ─────────────────────────────────────────────────

def fig_distance_profile(df: pd.DataFrame):
    """Distribution of event distances from Dhaka."""
    df_plot = df.dropna(subset=["distance_dhaka_km"])

    fig, axes = plt.subplots(1, 2, figsize=(13, 5))

    # Left: histogram
    ax = axes[0]
    bins = np.arange(0, 2500, 50)
    ax.hist(df_plot["distance_dhaka_km"], bins=bins, color="#4e8fbd", alpha=0.8, edgecolor="white")
    ax.axvline(300, color="#e07020", ls="--", lw=1.5, label="300 km")
    ax.axvline(500, color="#cc2020", ls="--", lw=1.5, label="500 km")
    ax.set_xlabel("Distance from Dhaka (km)")
    ax.set_ylabel("Count")
    ax.set_title("Distance from Dhaka — All Events")
    ax.legend(fontsize=9)

    # Right: by magnitude band
    ax = axes[1]
    for lo, hi, label, color in [
        (0,   4.0, "M<4.0",    "#b3cde3"),
        (4.0, 5.0, "M4.0–4.9", "#4e8fbd"),
        (5.0, 6.0, "M5.0–5.9", "#e07020"),
        (6.0, 99,  "M≥6.0",    "#cc2020"),
    ]:
        band = df_plot[(df_plot["magnitude"] >= lo) & (df_plot["magnitude"] < hi)]
        if len(band) == 0:
            continue
        ax.hist(band["distance_dhaka_km"], bins=bins, alpha=0.6,
                color=color, label=f"{label} (n={len(band)})", edgecolor="white")

    ax.axvline(300, color="gray", ls="--", lw=1)
    ax.set_xlabel("Distance from Dhaka (km)")
    ax.set_ylabel("Count")
    ax.set_title("Distance from Dhaka — by Magnitude Band")
    ax.legend(fontsize=8)

    fig.suptitle("Epicentre Distance from Dhaka", fontweight="bold")
    plt.tight_layout()
    fig.savefig(FIG_DIR / "crossborder_distance_profile.png")
    plt.close(fig)
    print("  Saved: crossborder_distance_profile.png")


# ── Summary tables ─────────────────────────────────────────────────────────────

def save_summary_tables(df: pd.DataFrame):
    # Overall cross-border summary
    thresholds = [
        ("All",   df,                        ),
        ("M≥3.0", df[df["magnitude"] >= 3.0] ),
        ("M≥4.0", df[df["magnitude"] >= 4.0] ),
        ("M≥5.0", df[df["magnitude"] >= 5.0] ),
        ("M≥6.0", df[df["magnitude"] >= 6.0] ),
        ("M≥7.0", df[df["magnitude"] >= 7.0] ),
    ]

    rows = []
    for label, sub in thresholds:
        n = len(sub)
        nd = sub["inside_bangladesh"].sum()
        rows.append({
            "threshold":   label,
            "n_total":     n,
            "n_inside_bd": int(nd),
            "n_outside_bd":int(n - nd),
            "pct_inside":  round(nd / n * 100, 1) if n else np.nan,
            "pct_outside": round((n - nd) / n * 100, 1) if n else np.nan,
        })

    tbl = pd.DataFrame(rows)
    tbl.to_csv(TBL_DIR / "crossborder_summary.csv", index=False)
    print("\n  Cross-border summary table:")
    print(tbl.to_string(index=False))

    # By decade (modern period)
    modern = df[df["year"] >= 2007].dropna(subset=["decade"])
    dec_rows = []
    for decade in sorted(modern["decade"].unique()):
        sub = modern[modern["decade"] == decade]
        nd  = sub["inside_bangladesh"].sum()
        n   = len(sub)
        dec_rows.append({
            "decade":      int(decade),
            "n_total":     n,
            "n_inside_bd": int(nd),
            "pct_inside":  round(nd / n * 100, 1) if n else np.nan,
            "top_country": sub["epicenter_country"].value_counts().index[0] if n > 0 else "",
        })
    dec_tbl = pd.DataFrame(dec_rows)
    dec_tbl.to_csv(TBL_DIR / "crossborder_by_decade.csv", index=False)
    print("\n  Cross-border by decade (2007+):")
    print(dec_tbl.to_string(index=False))

    # Source country by magnitude band
    mag_bands_labels = {
        "M<4.0":    (0,   4.0),
        "M4.0–4.9": (4.0, 5.0),
        "M5.0–5.9": (5.0, 6.0),
        "M≥6.0":    (6.0, 99),
    }
    country_rows = []
    top_ctry = df["epicenter_country"].value_counts().head(8).index.tolist()
    for ctry in top_ctry:
        row = {"country": ctry}
        csub = df[df["epicenter_country"] == ctry]
        for band_label, (lo, hi) in mag_bands_labels.items():
            row[band_label] = int(((csub["magnitude"] >= lo) & (csub["magnitude"] < hi)).sum())
        row["total"] = len(csub)
        country_rows.append(row)
    ctry_tbl = pd.DataFrame(country_rows)
    ctry_tbl.to_csv(TBL_DIR / "source_country_by_magband.csv", index=False)
    print("\n  Country by magnitude band:")
    print(ctry_tbl.to_string(index=False))


def main():
    print("Loading catalog...")
    df = load_catalog()
    print(f"  Events: {len(df)}")

    print("\nSaving summary tables...")
    save_summary_tables(df)

    print("\nGenerating cross-border figures...")
    fig_pie_charts(df)
    fig_crossborder_by_decade(df)
    fig_source_country_magnitude(df)
    fig_distance_profile(df)

    print("\nDone.")


if __name__ == "__main__":
    main()
