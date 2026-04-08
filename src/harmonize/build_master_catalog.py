"""
Step 4: Build the harmonised master earthquake catalog.

Sources (all pre-parsed):
  1. data_intermediate/parsed_main_catalog.csv       1918–2023, BST, no region label
  2. data_intermediate/parsed_monthly_2023_2024.csv  Jul 2023–Jun 2024, UTC, broader + felt subsets
  3. data_intermediate/parsed_felt_2024_2025.csv     Jan 2024–Jan 2025, UTC, felt-near-BD
  4. data_intermediate/parsed_felt_2025.csv          Jan 2025–Aug 2025, UTC, felt-near-BD

Key design decisions:
  a. For the monthly 2023-2024 file, ONLY USE the "broader" tables (catalog_type='broader').
     The "felt_nearby" sub-tables are strict subsets of the broader tables for the same month.
     Using both would double-count events. We do preserve the felt_nearby flag where it matches.
     Exception: July 2023 only has a broader table anyway.
  b. The main catalog (1918-2023) and modern files (2023+) overlap at 2023.
     Deduplication is performed on (date, rounded_lat, rounded_lon, magnitude).
  c. felt_2024_2025 and felt_2025 overlap at Jan 2025.
     Same deduplication applies.
  d. BST times in the main catalog are converted to UTC where time is available
     (BST = UTC+6, so UTC = BST - 6h).

Output:
  data_processed/master_catalog.csv
  data_processed/master_catalog.parquet
  data_intermediate/dedup_report.txt
"""

from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
INT_DIR  = PROJECT_ROOT / "data_intermediate"
PROC_DIR = PROJECT_ROOT / "data_processed"
PROC_DIR.mkdir(parents=True, exist_ok=True)

DHAKA_LAT = 23.8103
DHAKA_LON = 90.4125


# ── Utility ────────────────────────────────────────────────────────────────────

def haversine_km(lat1, lon1, lat2, lon2) -> float:
    """Vectorised Haversine distance in km."""
    R = 6371.0
    phi1 = np.radians(lat1)
    phi2 = np.radians(lat2)
    dphi = np.radians(lat2 - lat1)
    dlam = np.radians(lon2 - lon1)
    a = np.sin(dphi / 2) ** 2 + np.cos(phi1) * np.cos(phi2) * np.sin(dlam / 2) ** 2
    return 2 * R * np.arcsin(np.sqrt(a))


def bst_to_utc(date_iso: pd.Series, time_bst: pd.Series) -> pd.Series:
    """
    Subtract 6 hours from BST time to get UTC.
    Returns a UTC datetime Series (timezone-naive, explicit UTC label kept in column name).
    Returns NaT if time is missing.
    """
    # Combine date + time
    combined = date_iso.str.cat(time_bst, sep=" ")
    dt_bst = pd.to_datetime(combined, errors="coerce")
    dt_utc = dt_bst - pd.Timedelta(hours=6)
    return dt_utc


# ── Load sources ───────────────────────────────────────────────────────────────

def load_main_catalog() -> pd.DataFrame:
    df = pd.read_csv(INT_DIR / "parsed_main_catalog.csv", low_memory=False)

    # Build UTC datetime where possible
    has_time = ~df["time_missing"].fillna(True).astype(bool)
    utc_times = pd.NaT * len(df)  # initialise to NaT

    mask = has_time & df["date_iso"].notna() & df["time_bst"].notna()
    df["datetime_utc"] = pd.NaT
    if mask.any():
        df.loc[mask, "datetime_utc"] = bst_to_utc(
            df.loc[mask, "date_iso"],
            df.loc[mask, "time_bst"],
        )

    # No region label in this source; assign placeholder
    df["region_raw"]            = ""
    df["distance_dhaka_km_raw"] = pd.NA
    df["depth_km"]              = pd.NA
    df["catalog_type"]          = "historical_bst"
    df["catalog_month"]         = pd.NA
    df["sl"]                    = pd.NA

    return df


def load_monthly() -> pd.DataFrame:
    df = pd.read_csv(INT_DIR / "parsed_monthly_2023_2024.csv", low_memory=False)

    # Build UTC datetime
    mask = df["date_iso"].notna() & df["time_utc"].notna()
    df["datetime_utc"] = pd.NaT
    df.loc[mask, "datetime_utc"] = pd.to_datetime(
        df.loc[mask, "date_iso"].str.cat(df.loc[mask, "time_utc"], sep=" "),
        errors="coerce",
    )

    df["time_bst"]              = pd.NA
    df["time_missing"]          = False
    df["intensity_raw"]         = pd.NA
    df["intensity_label"]       = pd.NA
    df["intensity_numeric"]     = pd.NA
    df["distance_dhaka_km_raw"] = df.get("distance_dhaka_km", pd.NA)
    df["sl"]                    = pd.NA

    return df


def load_felt_2024_2025() -> pd.DataFrame:
    df = pd.read_csv(INT_DIR / "parsed_felt_2024_2025.csv", low_memory=False)

    mask = df["date_iso"].notna() & df["time_utc"].notna()
    df["datetime_utc"] = pd.NaT
    df.loc[mask, "datetime_utc"] = pd.to_datetime(
        df.loc[mask, "date_iso"].str.cat(df.loc[mask, "time_utc"], sep=" "),
        errors="coerce",
    )

    df["time_bst"]          = pd.NA
    df["time_missing"]      = False
    df["intensity_raw"]     = pd.NA
    df["intensity_label"]   = pd.NA
    df["intensity_numeric"] = pd.NA
    df["depth_km"]          = pd.NA
    df["catalog_month"]     = pd.NA
    df["catalog_type"]      = "felt_near_bangladesh"
    df["distance_dhaka_km_raw"] = df.get("distance_dhaka_km", pd.NA)

    return df


def load_felt_2025() -> pd.DataFrame:
    df = pd.read_csv(INT_DIR / "parsed_felt_2025.csv", low_memory=False)

    mask = df["date_iso"].notna() & df["time_utc"].notna()
    df["datetime_utc"] = pd.NaT
    df.loc[mask, "datetime_utc"] = pd.to_datetime(
        df.loc[mask, "date_iso"].str.cat(df.loc[mask, "time_utc"], sep=" "),
        errors="coerce",
    )

    df["time_bst"]          = pd.NA
    df["time_missing"]      = False
    df["intensity_raw"]     = pd.NA
    df["intensity_label"]   = pd.NA
    df["intensity_numeric"] = pd.NA
    df["depth_km"]          = pd.NA
    df["catalog_month"]     = pd.NA
    df["catalog_type"]      = "felt_near_bangladesh"
    df["distance_dhaka_km_raw"] = df.get("distance_dhaka_km", pd.NA)

    return df


# ── Deduplication ──────────────────────────────────────────────────────────────

def dedup_key(df: pd.DataFrame, lat_tol: float = 0.1, lon_tol: float = 0.1) -> pd.Series:
    """
    Create a deduplication key from rounded date, lat, lon, magnitude.
    Two events are considered duplicates if they share the same date,
    rounded lat/lon (within tolerance), and magnitude (rounded to 1dp).
    """
    lat_r = (df["latitude"]  / lat_tol).round(0) * lat_tol
    lon_r = (df["longitude"] / lon_tol).round(0) * lon_tol
    mag_r = df["magnitude"].round(1)
    return (
        df["date_iso"].fillna("").astype(str)
        + "_"
        + lat_r.fillna(-999).round(1).astype(str)
        + "_"
        + lon_r.fillna(-999).round(1).astype(str)
        + "_"
        + mag_r.fillna(-9).astype(str)
    )


# ── Master assembly ────────────────────────────────────────────────────────────

FINAL_COLS = [
    "event_id",
    "source_file",
    "source_period",
    "catalog_type",
    "date_iso",
    "time_bst",
    "time_utc",
    "datetime_utc",
    "year",
    "month",
    "day",
    "decade",
    "latitude",
    "longitude",
    "magnitude",
    "magnitude_raw",
    "intensity_label",
    "intensity_numeric",
    "depth_km",
    "distance_dhaka_km",
    "distance_dhaka_km_raw",
    "region_raw",
    "parse_flags",
    "dedup_key",
    "duplicate_flag",
]


def build_master() -> pd.DataFrame:
    print("Loading source files...")

    df_main     = load_main_catalog()
    df_monthly  = load_monthly()
    df_felt_24  = load_felt_2024_2025()
    df_felt_25  = load_felt_2025()

    print(f"  Main catalog:       {len(df_main):>5} rows  ({df_main['year'].min():.0f}–{df_main['year'].max():.0f})")
    print(f"  Monthly 2023-2024:  {len(df_monthly):>5} rows  (Jul 2023–Jun 2024)")
    print(f"  Felt 2024-2025:     {len(df_felt_24):>5} rows  (Jan 2024–Jan 2025)")
    print(f"  Felt 2025:          {len(df_felt_25):>5} rows  (Jan–Aug 2025)")

    # For monthly, use ONLY the broader tables to avoid double-counting.
    # The felt_nearby subset of monthly overlaps with felt_2024_2025 for Jan 2024.
    df_monthly_broader = df_monthly[df_monthly["catalog_type"] == "broader"].copy()
    df_monthly_felt    = df_monthly[df_monthly["catalog_type"] == "felt_nearby"].copy()

    print(f"\n  Monthly broader (used):      {len(df_monthly_broader)} rows")
    print(f"  Monthly felt_nearby (kept separate as reference): {len(df_monthly_felt)} rows")

    # Rename time column for consistency
    for df in [df_monthly_broader, df_felt_24, df_felt_25]:
        if "time_utc" not in df.columns and "time_bst" not in df.columns:
            df["time_utc"] = pd.NA

    df_main["time_utc"] = pd.NA  # main catalog uses BST, not UTC

    # Concatenate: main catalog + monthly broader + modern felt
    # Ordering ensures that if duplicates are found, we keep the more modern/precise record
    # (felt files are more carefully curated) by marking older duplicates
    sources = [
        ("main_catalog",    df_main),
        ("monthly_broader", df_monthly_broader),
        ("felt_2024_2025",  df_felt_24),
        ("felt_2025",       df_felt_25),
    ]

    combined_parts = []
    for label, df in sources:
        df = df.copy()
        df["_source_rank"] = {
            "main_catalog":    1,
            "monthly_broader": 2,
            "felt_2024_2025":  3,
            "felt_2025":       4,
        }[label]
        combined_parts.append(df)

    df_all = pd.concat(combined_parts, ignore_index=True)

    # Derive key computed columns
    df_all["date_iso"] = pd.to_datetime(df_all["date_iso"], errors="coerce").dt.strftime("%Y-%m-%d")
    dt = pd.to_datetime(df_all["date_iso"], errors="coerce")
    df_all["year"]   = dt.dt.year.astype("Int64")
    df_all["month"]  = dt.dt.month.astype("Int64")
    df_all["day"]    = dt.dt.day.astype("Int64")
    df_all["decade"] = (dt.dt.year // 10 * 10).astype("Int64")

    # Compute distance from Dhaka (km) using coordinates
    has_coord = df_all["latitude"].notna() & df_all["longitude"].notna()
    df_all["distance_dhaka_km"] = np.nan
    df_all.loc[has_coord, "distance_dhaka_km"] = haversine_km(
        df_all.loc[has_coord, "latitude"],
        df_all.loc[has_coord, "longitude"],
        DHAKA_LAT,
        DHAKA_LON,
    ).round(1)

    # Deduplication
    df_all["dedup_key"] = dedup_key(df_all)

    # Sort so that higher _source_rank (more modern / curated) comes first within each key
    df_all = df_all.sort_values(["dedup_key", "_source_rank"], ascending=[True, False])

    # Mark duplicates: first occurrence (highest rank) is kept; others are flagged
    df_all["duplicate_flag"] = df_all.duplicated(subset=["dedup_key"], keep="first")

    n_dups = df_all["duplicate_flag"].sum()
    print(f"\n  Total rows before dedup: {len(df_all)}")
    print(f"  Duplicate rows flagged:  {n_dups}")
    print(f"  Unique events:           {len(df_all) - n_dups}")

    # Build event_id (for non-duplicates, assign sequential ID)
    df_all = df_all.reset_index(drop=True)
    df_all["event_id"] = ["EV-{:05d}".format(i + 1) for i in range(len(df_all))]

    # Harmonise column names
    if "distance_dhaka_km_raw" not in df_all.columns:
        df_all["distance_dhaka_km_raw"] = pd.NA

    # Final column selection (keep all, but reorder)
    available = [c for c in FINAL_COLS if c in df_all.columns]
    extra     = [c for c in df_all.columns if c not in FINAL_COLS and not c.startswith("_")]
    df_final  = df_all[available + extra]

    # Summary statistics
    df_unique = df_final[~df_final["duplicate_flag"]]
    print(f"\n  === MASTER CATALOG SUMMARY ===")
    print(f"  Total events (unique):   {len(df_unique)}")
    print(f"  Year range:              {df_unique['year'].min()} – {df_unique['year'].max()}")
    print(f"  Magnitude range:         {df_unique['magnitude'].min():.1f} – {df_unique['magnitude'].max():.1f}")
    print(f"  Missing coordinates:     {(df_unique['latitude'].isna() | df_unique['longitude'].isna()).sum()}")
    print(f"  Missing magnitude:       {df_unique['magnitude'].isna().sum()}")
    print(f"\n  Events by source:")
    for src, cnt in df_unique["source_file"].value_counts().items():
        print(f"    {src:<55} {cnt}")
    print(f"\n  Events by catalog_type:")
    for ctype, cnt in df_unique["catalog_type"].value_counts().items():
        print(f"    {ctype:<35} {cnt}")
    print(f"\n  Events by decade:")
    for dec, cnt in df_unique.groupby("decade")["event_id"].count().items():
        print(f"    {dec}s: {cnt}")

    return df_final


def save_dedup_report(df: pd.DataFrame):
    """Write a human-readable deduplication report."""
    dups = df[df["duplicate_flag"]]
    lines = [
        "DEDUPLICATION REPORT",
        "=" * 60,
        f"Total rows in combined dataset: {len(df)}",
        f"Duplicate rows flagged:         {len(dups)}",
        f"Unique events retained:         {len(df) - len(dups)}",
        "",
        "Sample duplicate pairs (dedup_key → both records):",
        "-" * 60,
    ]

    # Show a few duplicate examples
    dup_keys = dups["dedup_key"].unique()[:10]
    for key in dup_keys:
        group = df[df["dedup_key"] == key][["event_id", "date_iso", "latitude", "longitude", "magnitude", "source_file", "duplicate_flag"]]
        lines.append(f"\nKey: {key}")
        lines.append(group.to_string(index=False))

    report_path = INT_DIR / "dedup_report.txt"
    report_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"\n  Dedup report → {report_path.relative_to(PROJECT_ROOT)}")


def main():
    df = build_master()
    save_dedup_report(df)

    # Save outputs
    out_csv     = PROC_DIR / "master_catalog.csv"
    out_parquet = PROC_DIR / "master_catalog.parquet"

    # Cast all object (mixed-type) columns to string for parquet compatibility
    df_parquet = df.copy()
    for col in df_parquet.select_dtypes(include=["object", "str"]).columns:
        df_parquet[col] = df_parquet[col].astype(str).replace("nan", "")

    df.to_csv(out_csv, index=False, encoding="utf-8")
    df_parquet.to_parquet(out_parquet, index=False)

    print(f"\n  Saved CSV     → {out_csv.relative_to(PROJECT_ROOT)}")
    print(f"  Saved Parquet → {out_parquet.relative_to(PROJECT_ROOT)}")

    # Also save the unique-only version (primary research dataset)
    df_unique = df[~df["duplicate_flag"]].copy()
    out_unique_csv = PROC_DIR / "master_catalog_unique.csv"
    df_unique.to_csv(out_unique_csv, index=False, encoding="utf-8")
    print(f"  Saved unique  → {out_unique_csv.relative_to(PROJECT_ROOT)}")

    return df


if __name__ == "__main__":
    main()
