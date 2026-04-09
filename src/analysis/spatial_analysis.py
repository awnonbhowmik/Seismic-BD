"""
Spatial analysis and mapping of the Bangladesh earthquake catalog.

Produces:
  outputs/maps/map_all_epicenters.png
  outputs/maps/map_epicenters_by_magnitude.png
  outputs/maps/map_modern_epicenters.png
  outputs/maps/map_source_corridors.png
  outputs/maps/map_domestic_vs_crossborder.png
  outputs/tables/spatial_corridor_summary.csv
  outputs/tables/spatial_country_summary.csv
"""

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
DATA_RAW     = PROJECT_ROOT / "data_raw"
MAP_DIR      = PROJECT_ROOT / "outputs" / "maps"
TBL_DIR      = PROJECT_ROOT / "outputs" / "tables"
MAP_DIR.mkdir(parents=True, exist_ok=True)
TBL_DIR.mkdir(parents=True, exist_ok=True)

# Bangladesh + surrounding region bounding box for maps
BBOX = dict(lon_min=76, lon_max=105, lat_min=10, lat_max=33)
# Tight Bangladesh-centric view
BBOX_TIGHT = dict(lon_min=84, lon_max=98, lat_min=18, lat_max=30)

STYLE = {
    "font.family": "DejaVu Sans",
    "font.size":   10,
    "figure.dpi":  150,
    "savefig.dpi": 150,
    "savefig.bbox": "tight",
}
plt.rcParams.update(STYLE)

DHAKA_LAT = 23.8103
DHAKA_LON  = 90.4125


def load_data():
    df = pd.read_csv(DATA_DIR / "master_catalog_spatial_v2.csv", low_memory=False)
    _dup_col = "duplicate_flag_v2" if "duplicate_flag_v2" in df.columns else "duplicate_flag"
    df = df[~df[_dup_col].astype(bool)].copy()
    df["magnitude"]      = pd.to_numeric(df["magnitude"], errors="coerce")
    df["year"]           = pd.to_numeric(df["year"], errors="coerce").astype("Int64")
    df["latitude"]       = pd.to_numeric(df["latitude"], errors="coerce")
    df["longitude"]      = pd.to_numeric(df["longitude"], errors="coerce")
    df["inside_bangladesh"] = df["inside_bangladesh"].astype(bool)

    world = gpd.read_file(DATA_RAW / "world_countries.gpkg").to_crs("EPSG:4326")
    bd    = gpd.read_file(DATA_RAW / "bangladesh_boundary.gpkg").to_crs("EPSG:4326")
    return df, world, bd


def clip_to_bbox(world: gpd.GeoDataFrame, bbox: dict) -> gpd.GeoDataFrame:
    """Clip world GDF to a bounding box for plotting."""
    from shapely.geometry import box
    b = box(bbox["lon_min"], bbox["lat_min"], bbox["lon_max"], bbox["lat_max"])
    return world.clip(b)


def add_basemap(ax, world_clipped: gpd.GeoDataFrame, bd: gpd.GeoDataFrame, bbox: dict):
    """Add world boundaries and Bangladesh highlight."""
    world_clipped.plot(ax=ax, color="#e8e8e8", edgecolor="#aaaaaa", linewidth=0.4, zorder=0)
    bd.plot(ax=ax, color="#c8ddb8", edgecolor="#4a8040", linewidth=1.0, zorder=1)
    ax.set_xlim(bbox["lon_min"], bbox["lon_max"])
    ax.set_ylim(bbox["lat_min"], bbox["lat_max"])
    ax.set_xlabel("Longitude (°E)")
    ax.set_ylabel("Latitude (°N)")
    ax.grid(True, alpha=0.25, linestyle=":")


def magnitude_to_size(mag_series: pd.Series) -> pd.Series:
    """Map magnitude to marker size (area-scaled)."""
    base = mag_series.fillna(3.0).clip(lower=2.0)
    return (2 ** (base - 2.0)) * 8


# ── Map 1: All epicenters ──────────────────────────────────────────────────────

def map_all_epicenters(df: pd.DataFrame, world: gpd.GeoDataFrame, bd: gpd.GeoDataFrame):
    df_plot = df.dropna(subset=["latitude", "longitude"])
    world_c = clip_to_bbox(world, BBOX)

    fig, ax = plt.subplots(figsize=(11, 8))
    add_basemap(ax, world_c, bd, BBOX)

    # Colour by era
    eras = {
        "1918–1999":    (df_plot["year"] < 2000,  "#8b0000", "^"),
        "2000–2006":    ((df_plot["year"] >= 2000) & (df_plot["year"] <= 2006), "#ff8c00", "s"),
        "2007–2022":    ((df_plot["year"] >= 2007) & (df_plot["year"] <= 2022), "#1f77b4", "o"),
        "2023–2025":    (df_plot["year"] >= 2023,  "#2ca02c", "o"),
    }

    for label, (mask, color, marker) in eras.items():
        sub = df_plot[mask]
        if len(sub) > 0:
            sizes = magnitude_to_size(sub["magnitude"])
            ax.scatter(sub["longitude"], sub["latitude"],
                       s=sizes, c=color, marker=marker, alpha=0.65,
                       linewidths=0.3, edgecolors="white", label=f"{label} (n={len(sub)})",
                       zorder=5)

    # Dhaka marker
    ax.scatter([DHAKA_LON], [DHAKA_LAT], marker="*", c="red", s=150, zorder=10,
               edgecolors="white", linewidths=0.5)
    ax.annotate("Dhaka", (DHAKA_LON + 0.3, DHAKA_LAT + 0.2), fontsize=8, color="red")

    # Magnitude legend (size)
    for mag, label_text in [(3, "M3"), (5, "M5"), (7, "M7")]:
        ax.scatter([], [], s=magnitude_to_size(pd.Series([mag])).iloc[0],
                   c="gray", alpha=0.6, label=label_text)

    ax.set_title("Earthquake Epicentres — Bangladesh & Surrounding Region (1918–2025)\n"
                 "★ = Dhaka", pad=10)
    ax.legend(title="Era / Magnitude", bbox_to_anchor=(1.01, 1), loc="upper left",
              fontsize=8, title_fontsize=9)

    fig.savefig(MAP_DIR / "map_all_epicenters.png")
    plt.close(fig)
    print("  Saved: map_all_epicenters.png")


# ── Map 2: Magnitude-coloured epicenters (modern, tight view) ─────────────────

def map_epicenters_magnitude(df: pd.DataFrame, world: gpd.GeoDataFrame, bd: gpd.GeoDataFrame):
    modern = df[(df["year"] >= 2007)].dropna(subset=["latitude", "longitude", "magnitude"])
    world_c = clip_to_bbox(world, BBOX_TIGHT)

    fig, ax = plt.subplots(figsize=(10, 8))
    add_basemap(ax, world_c, bd, BBOX_TIGHT)

    cmap   = plt.cm.plasma_r
    norm   = mcolors.Normalize(vmin=2.5, vmax=7.5)
    sizes  = magnitude_to_size(modern["magnitude"])
    colors = cmap(norm(modern["magnitude"]))

    sc = ax.scatter(modern["longitude"], modern["latitude"],
                    s=sizes, c=modern["magnitude"],
                    cmap=cmap, norm=norm, alpha=0.75,
                    linewidths=0.3, edgecolors="white", zorder=5)

    cbar = plt.colorbar(sc, ax=ax, pad=0.02, shrink=0.8)
    cbar.set_label("Magnitude")

    ax.scatter([DHAKA_LON], [DHAKA_LAT], marker="*", c="red", s=150, zorder=10,
               edgecolors="white", linewidths=0.5)
    ax.annotate("Dhaka", (DHAKA_LON + 0.15, DHAKA_LAT + 0.15), fontsize=8, color="red")

    ax.set_title("Earthquake Epicentres Coloured by Magnitude (2007–2025)", pad=10)

    fig.savefig(MAP_DIR / "map_epicenters_by_magnitude.png")
    plt.close(fig)
    print("  Saved: map_epicenters_by_magnitude.png")


# ── Map 3: Source corridors ────────────────────────────────────────────────────

CORRIDOR_COLORS = {
    "BD_domestic":           "#2ca02c",
    "Chittagong_Hills":      "#98df8a",
    "Sylhet_Region":         "#17becf",
    "Assam_Meghalaya":       "#1f77b4",
    "Myanmar_India_Border":  "#d62728",
    "Myanmar_Interior":      "#ff7f0e",
    "Nepal_Himalaya":        "#9467bd",
    "Bhutan_E_Himalaya":     "#e377c2",
    "Bay_of_Bengal":         "#17becf",
    "Andaman_Nicobar":       "#bcbd22",
    "South_Asia_Interior":   "#7f7f7f",
    "SE_Asia_Far":           "#c49c94",
    "Other_Distant":         "#c7c7c7",
    "Unknown":               "#dddddd",
}


def map_source_corridors(df: pd.DataFrame, world: gpd.GeoDataFrame, bd: gpd.GeoDataFrame):
    df_plot = df.dropna(subset=["latitude", "longitude", "source_corridor"])
    world_c = clip_to_bbox(world, BBOX)

    fig, ax = plt.subplots(figsize=(12, 9))
    add_basemap(ax, world_c, bd, BBOX)

    for corridor, color in CORRIDOR_COLORS.items():
        sub = df_plot[df_plot["source_corridor"] == corridor]
        if len(sub) == 0:
            continue
        sizes = magnitude_to_size(sub["magnitude"])
        ax.scatter(sub["longitude"], sub["latitude"],
                   s=sizes, c=color, alpha=0.7,
                   linewidths=0.3, edgecolors="white",
                   label=f"{corridor} (n={len(sub)})", zorder=5)

    ax.scatter([DHAKA_LON], [DHAKA_LAT], marker="*", c="red", s=200, zorder=10,
               edgecolors="white", linewidths=0.5)
    ax.annotate("Dhaka", (DHAKA_LON + 0.3, DHAKA_LAT + 0.2), fontsize=8, color="red")

    ax.set_title("Earthquake Epicentres by Source Corridor\n(1918–2025)", pad=10)
    ax.legend(title="Source corridor", bbox_to_anchor=(1.01, 1), loc="upper left",
              fontsize=7.5, title_fontsize=9)

    fig.savefig(MAP_DIR / "map_source_corridors.png")
    plt.close(fig)
    print("  Saved: map_source_corridors.png")


# ── Map 4: Domestic vs cross-border (modern) ──────────────────────────────────

def map_domestic_vs_crossborder(df: pd.DataFrame, world: gpd.GeoDataFrame, bd: gpd.GeoDataFrame):
    modern  = df[(df["year"] >= 2007)].dropna(subset=["latitude", "longitude"])
    world_c = clip_to_bbox(world, BBOX_TIGHT)

    fig, ax = plt.subplots(figsize=(10, 8))
    add_basemap(ax, world_c, bd, BBOX_TIGHT)

    domestic  = modern[modern["inside_bangladesh"] == True]
    crossbord = modern[modern["inside_bangladesh"] == False]

    ax.scatter(crossbord["longitude"], crossbord["latitude"],
               s=magnitude_to_size(crossbord["magnitude"]),
               c="#d62728", alpha=0.6, linewidths=0.3, edgecolors="white",
               label=f"External (n={len(crossbord)})", zorder=5)

    ax.scatter(domestic["longitude"], domestic["latitude"],
               s=magnitude_to_size(domestic["magnitude"]),
               c="#2ca02c", alpha=0.9, linewidths=0.5, edgecolors="white",
               marker="^", label=f"Domestic BD (n={len(domestic)})", zorder=6)

    ax.scatter([DHAKA_LON], [DHAKA_LAT], marker="*", c="gold", s=200, zorder=10,
               edgecolors="black", linewidths=0.5)
    ax.annotate("Dhaka", (DHAKA_LON + 0.15, DHAKA_LAT + 0.15), fontsize=8, color="black")

    ax.set_title("Domestic vs External Epicentres (2007–2025)\n"
                 "▲ = Inside Bangladesh  ●= Outside Bangladesh", pad=10)
    ax.legend(bbox_to_anchor=(1.01, 1), loc="upper left", fontsize=9)

    fig.savefig(MAP_DIR / "map_domestic_vs_crossborder.png")
    plt.close(fig)
    print("  Saved: map_domestic_vs_crossborder.png")


# ── Map 5: Faceted by decade (modern) ─────────────────────────────────────────

def map_faceted_by_decade(df: pd.DataFrame, world: gpd.GeoDataFrame, bd: gpd.GeoDataFrame):
    modern  = df[(df["year"] >= 2007)].dropna(subset=["latitude", "longitude", "decade"])
    world_c = clip_to_bbox(world, BBOX_TIGHT)
    decades = sorted(modern["decade"].unique())

    n_dec = len(decades)
    ncols = min(3, n_dec)
    nrows = int(np.ceil(n_dec / ncols))

    fig, axes = plt.subplots(nrows, ncols, figsize=(5.5 * ncols, 5 * nrows))
    axes = np.array(axes).flatten()

    for ax, decade in zip(axes, decades):
        add_basemap(ax, world_c, bd, BBOX_TIGHT)
        sub = modern[modern["decade"] == decade]
        if len(sub) > 0:
            ax.scatter(sub["longitude"], sub["latitude"],
                       s=magnitude_to_size(sub["magnitude"]),
                       c="#d62728" if (sub["inside_bangladesh"] == False).all() else "#4e8fbd",
                       alpha=0.7, linewidths=0.3, edgecolors="white", zorder=5)
        ax.scatter([DHAKA_LON], [DHAKA_LAT], marker="*", c="gold", s=80, zorder=10)
        ax.set_title(f"{int(decade)}s (n={len(sub)})", fontsize=10)
        ax.set_xlabel("")
        ax.set_ylabel("")

    # Hide unused axes
    for ax in axes[n_dec:]:
        ax.set_visible(False)

    fig.suptitle("Epicentres by Decade (2000–2025)", fontsize=13, fontweight="bold", y=1.02)
    plt.tight_layout()
    fig.savefig(MAP_DIR / "map_faceted_by_decade.png")
    plt.close(fig)
    print("  Saved: map_faceted_by_decade.png")


# ── Summary tables ─────────────────────────────────────────────────────────────

def save_spatial_tables(df: pd.DataFrame):
    # Corridor summary
    corridor_tbl = (
        df.groupby("source_corridor")
          .agg(
            n_events    = ("event_id", "count"),
            mag_mean    = ("magnitude", "mean"),
            mag_max     = ("magnitude", "max"),
            n_M4plus    = ("magnitude", lambda x: (x >= 4.0).sum()),
            n_M5plus    = ("magnitude", lambda x: (x >= 5.0).sum()),
          )
          .round(2)
          .sort_values("n_events", ascending=False)
          .reset_index()
    )
    corridor_tbl.to_csv(TBL_DIR / "spatial_corridor_summary.csv", index=False)
    print("\n  Source corridor summary:")
    print(corridor_tbl.to_string(index=False))

    # Country summary
    country_tbl = (
        df.groupby("epicenter_country")
          .agg(
            n_events  = ("event_id", "count"),
            mag_mean  = ("magnitude", "mean"),
            mag_max   = ("magnitude", "max"),
            n_M5plus  = ("magnitude", lambda x: (x >= 5.0).sum()),
          )
          .round(2)
          .sort_values("n_events", ascending=False)
          .reset_index()
    )
    country_tbl.to_csv(TBL_DIR / "spatial_country_summary.csv", index=False)
    print("\n  Country summary:")
    print(country_tbl.to_string(index=False))


def main():
    print("Loading data...")
    df, world, bd = load_data()
    print(f"  Events: {len(df)}")

    print("\nGenerating spatial tables...")
    save_spatial_tables(df)

    print("\nGenerating maps...")
    map_all_epicenters(df, world, bd)
    map_epicenters_magnitude(df, world, bd)
    map_source_corridors(df, world, bd)
    map_domestic_vs_crossborder(df, world, bd)
    map_faceted_by_decade(df, world, bd)

    print("\nDone.")


if __name__ == "__main__":
    main()
