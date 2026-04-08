"""
Step 7: Spatial enrichment of the master catalog.

For each earthquake event:
  1. Determine if epicenter falls inside Bangladesh.
  2. Assign country of epicenter.
  3. Classify source corridor (seismotectonic region).
  4. Classify event_class (domestic / cross-border / distant-regional / offshore).
  5. Compute distance to nearest Bangladesh border (for non-domestic events).

Source corridors defined by approximate bounding boxes (lat/lon):
  Corridor definitions are rectangular approximations of known seismotectonic zones
  relevant to Bangladesh hazard. These are heuristic classifications based on published
  literature (Steckler et al., Ansary et al., BMD zone maps). Not a formal zonation.

Output:
  data_processed/master_catalog_spatial.csv
  data_processed/master_catalog_spatial.parquet
"""

from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
from shapely.geometry import Point

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROC_DIR     = PROJECT_ROOT / "data_processed"
DATA_RAW     = PROJECT_ROOT / "data_raw"

DHAKA_LAT = 23.8103
DHAKA_LON = 90.4125

# ── Source corridor definitions ────────────────────────────────────────────────
# Each entry: (label, lat_min, lat_max, lon_min, lon_max)
# Priority is top-to-bottom: first matching box is assigned.
SOURCE_CORRIDORS = [
    # Bangladesh domestic (coarse bounding box; refine by actual BD boundary later)
    ("BD_domestic",            20.0, 26.9, 88.0, 92.7),
    # Chittagong Hill Tracts / eastern Bangladesh
    ("Chittagong_Hills",       21.0, 24.0, 91.5, 93.0),
    # Sylhet / Brahmaputra fold
    ("Sylhet_Region",          24.0, 25.5, 91.0, 92.5),
    # Assam / Meghalaya seismic belt
    ("Assam_Meghalaya",        25.0, 27.5, 89.5, 96.0),
    # Myanmar-India border (Manipur, Mizoram, Chin)
    ("Myanmar_India_Border",   20.0, 27.0, 92.5, 95.5),
    # Myanmar interior
    ("Myanmar_Interior",       16.0, 27.0, 95.5, 101.0),
    # Nepal / Himalayan arc
    ("Nepal_Himalaya",         26.5, 31.0, 80.0, 88.5),
    # Bhutan / Eastern Himalaya
    ("Bhutan_E_Himalaya",      26.5, 29.0, 88.5, 92.5),
    # Bay of Bengal
    ("Bay_of_Bengal",          10.0, 22.0, 85.0, 94.0),
    # Andaman-Nicobar Islands
    ("Andaman_Nicobar",         6.0, 14.5, 92.0, 94.5),
    # South Asian interior (India, far)
    ("South_Asia_Interior",    20.0, 36.0, 68.0, 90.0),
    # East Asia / Southeast Asia (far)
    ("SE_Asia_Far",            -5.0, 35.0, 94.0, 135.0),
    # Other / global
    ("Other_Distant",         -90.0, 90.0, -180.0, 180.0),
]


def assign_source_corridor(lat: float, lon: float) -> str:
    """Assign a seismotectonic source corridor by coordinate bounding box."""
    if pd.isna(lat) or pd.isna(lon):
        return "Unknown"
    for label, lat_min, lat_max, lon_min, lon_max in SOURCE_CORRIDORS:
        if lat_min <= lat <= lat_max and lon_min <= lon <= lon_max:
            return label
    return "Other_Distant"


def load_boundaries():
    """Load Bangladesh boundary and world country boundaries."""
    bd_path    = DATA_RAW / "bangladesh_boundary.gpkg"
    world_path = DATA_RAW / "world_countries.gpkg"

    bd_gdf    = gpd.read_file(bd_path).to_crs("EPSG:4326")
    world_gdf = gpd.read_file(world_path).to_crs("EPSG:4326")

    # Build a single union polygon for Bangladesh
    bd_poly = bd_gdf.geometry.union_all()
    return bd_poly, world_gdf


def points_in_bangladesh(df: pd.DataFrame, bd_poly) -> pd.Series:
    """Return boolean Series: True if point is inside Bangladesh boundary."""
    has_coord = df["latitude"].notna() & df["longitude"].notna()
    result    = pd.Series(False, index=df.index)

    if has_coord.any():
        pts = gpd.GeoSeries(
            [Point(lon, lat) if pd.notna(lon) and pd.notna(lat) else None
             for lat, lon in zip(df["latitude"], df["longitude"])],
            crs="EPSG:4326",
        )
        result[has_coord] = pts[has_coord].apply(
            lambda p: bd_poly.contains(p) if p is not None else False
        )

    return result


def assign_country(df: pd.DataFrame, world_gdf: gpd.GeoDataFrame) -> pd.Series:
    """
    Spatial join to find which country each point falls in.
    Returns a Series of country names.
    """
    has_coord = df["latitude"].notna() & df["longitude"].notna()

    # Build GeoDataFrame of event points
    geom = [
        Point(lon, lat) if (pd.notna(lat) and pd.notna(lon)) else None
        for lat, lon in zip(df["latitude"], df["longitude"])
    ]
    gdf_pts = gpd.GeoDataFrame(df[["event_id"]].copy(), geometry=geom, crs="EPSG:4326")

    # Spatial join
    joined = gpd.sjoin(
        gdf_pts[gdf_pts.geometry.notna()],
        world_gdf[["ADMIN", "geometry"]],
        how="left",
        predicate="within",
    )

    country_series = pd.Series("Unknown", index=df.index)
    # Map back by event_id (use first match if multiple)
    matched = joined.groupby("event_id")["ADMIN"].first()
    country_series.loc[df["event_id"].isin(matched.index)] = (
        df["event_id"].map(matched).fillna("Unknown")
    )

    return country_series


def classify_event(row) -> str:
    """
    Classify event into broad class:
      - domestic_BD          : inside Bangladesh
      - cross_border_near    : within ~300 km of Dhaka, outside BD
      - distant_regional     : 300–1500 km
      - very_distant         : > 1500 km
    """
    if row["inside_bangladesh"]:
        return "domestic_BD"
    dist = row.get("distance_dhaka_km", None)
    if pd.isna(dist):
        return "unknown"
    if dist <= 300:
        return "cross_border_near"
    elif dist <= 1500:
        return "distant_regional"
    else:
        return "very_distant"


def distance_to_bd_border(lat: float, lon: float, bd_poly) -> float:
    """
    Return approximate distance in km from a point to the Bangladesh border.
    For domestic events, this is 0 (inside).
    For external events, this uses the Shapely exterior distance (in degrees)
    and converts approximately using 111 km/degree.
    NOTE: This is a rough approximation only.
    """
    if pd.isna(lat) or pd.isna(lon):
        return np.nan
    pt = Point(lon, lat)
    if bd_poly.contains(pt):
        return 0.0
    # Works for both Polygon and MultiPolygon
    dist_deg = bd_poly.boundary.distance(pt)
    return round(dist_deg * 111.0, 1)  # approx km


def main():
    print("Loading master catalog...")
    df = pd.read_csv(PROC_DIR / "master_catalog_unique.csv", low_memory=False)
    print(f"  Events: {len(df)}")

    print("\nLoading boundary data...")
    bd_poly, world_gdf = load_boundaries()

    # ── 1. Inside Bangladesh flag ──────────────────────────────────────────────
    print("  Assigning inside_bangladesh flag...")
    df["inside_bangladesh"] = points_in_bangladesh(df, bd_poly)
    print(f"    Domestic (inside BD): {df['inside_bangladesh'].sum()}")
    print(f"    External:             {(~df['inside_bangladesh']).sum()}")

    # ── 2. Country assignment ──────────────────────────────────────────────────
    print("  Assigning country of epicenter...")
    df["epicenter_country"] = assign_country(df, world_gdf)
    print("  Top countries:")
    for ctry, cnt in df["epicenter_country"].value_counts().head(10).items():
        print(f"    {ctry:<35} {cnt}")

    # ── 3. Source corridor ─────────────────────────────────────────────────────
    print("  Assigning source corridors...")
    df["source_corridor"] = [
        assign_source_corridor(lat, lon)
        for lat, lon in zip(df["latitude"], df["longitude"])
    ]

    # Refine corridors using the precise boundary flag:
    # 1. Events confirmed inside BD → BD_domestic
    df.loc[df["inside_bangladesh"], "source_corridor"] = "BD_domestic"
    # 2. Events where bounding box said BD_domestic but actual boundary says external
    #    → reclassify based on region label or distance (assign to nearest neighbour box)
    wrong_domestic = (~df["inside_bangladesh"]) & (df["source_corridor"] == "BD_domestic")
    if wrong_domestic.any():
        # Re-run corridor assignment skipping the BD_domestic box
        CORRIDORS_EXCL_BD = [c for c in SOURCE_CORRIDORS if c[0] != "BD_domestic"]
        def reassign(row):
            lat, lon = row["latitude"], row["longitude"]
            if pd.isna(lat) or pd.isna(lon):
                return "Unknown"
            for label, lat_min, lat_max, lon_min, lon_max in CORRIDORS_EXCL_BD:
                if lat_min <= lat <= lat_max and lon_min <= lon <= lon_max:
                    return label
            return "Other_Distant"
        df.loc[wrong_domestic, "source_corridor"] = df[wrong_domestic].apply(reassign, axis=1)
        print(f"  Reclassified {wrong_domestic.sum()} events from BD_domestic to correct corridor")

    print("  Source corridor distribution:")
    for corridor, cnt in df["source_corridor"].value_counts().items():
        print(f"    {corridor:<35} {cnt}")

    # ── 4. Event class ─────────────────────────────────────────────────────────
    print("  Classifying event class...")
    df["event_class"] = df.apply(classify_event, axis=1)
    print("  Event class distribution:")
    for cls, cnt in df["event_class"].value_counts().items():
        print(f"    {cls:<35} {cnt}")

    # ── 5. Distance to BD border ───────────────────────────────────────────────
    print("  Computing distance to Bangladesh border (approx)...")
    df["distance_bd_border_km"] = [
        distance_to_bd_border(lat, lon, bd_poly)
        for lat, lon in zip(df["latitude"], df["longitude"])
    ]

    # ── 6. Cross-border dependency summary ────────────────────────────────────
    print("\n  === CROSS-BORDER DEPENDENCY SUMMARY ===")
    total = len(df)
    n_domestic = df["inside_bangladesh"].sum()
    n_external = total - n_domestic
    print(f"  Events inside Bangladesh:    {n_domestic} ({n_domestic/total*100:.1f}%)")
    print(f"  Events outside Bangladesh:   {n_external} ({n_external/total*100:.1f}%)")

    # For M≥4 events
    m4 = df[df["magnitude"] >= 4.0]
    m4_dom = m4["inside_bangladesh"].sum()
    m4_ext = len(m4) - m4_dom
    print(f"\n  M≥4.0 events inside BD:     {m4_dom} ({m4_dom/len(m4)*100:.1f}%)")
    print(f"  M≥4.0 events outside BD:    {m4_ext} ({m4_ext/len(m4)*100:.1f}%)")

    # ── Save ───────────────────────────────────────────────────────────────────
    out_csv     = PROC_DIR / "master_catalog_spatial.csv"
    df.to_csv(out_csv, index=False, encoding="utf-8")

    df_parquet = df.copy()
    for col in df_parquet.select_dtypes(include=["object", "str"]).columns:
        df_parquet[col] = df_parquet[col].astype(str).replace("nan", "")
    df_parquet.to_parquet(PROC_DIR / "master_catalog_spatial.parquet", index=False)

    print(f"\n  Saved → {out_csv.relative_to(PROJECT_ROOT)}")
    return df


if __name__ == "__main__":
    main()
