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
  data/master_catalog_spatial_v2.csv
  data/master_catalog_spatial_v2.parquet
  data_intermediate/dedup_report.txt
"""

from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
INT_DIR  = PROJECT_ROOT / "data_intermediate"
DATA_DIR = PROJECT_ROOT / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

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

# Thresholds for the v2 two-stage dedup (see docs/dedup_audit.md for full rationale)
_DEDUP_DIST_KM   = 25    # maximum epicentre separation to consider a duplicate
_DEDUP_DMAG_B    = 0.20  # maximum |ΔM| for Stage B (BST/UTC date-shift correction)
_DEDUP_CLOCK_M   = 15    # maximum clock-time mismatch for Stage B (minutes)


def dedup_key(df: pd.DataFrame, lat_tol: float = 0.1, lon_tol: float = 0.1) -> pd.Series:
    """
    v1 dedup key: (date_iso, rounded lat, rounded lon, rounded magnitude).
    Kept for reference and as the fallback key column in the output catalog.

    KNOWN LIMITATION: does not handle BST/UTC midnight date shift.
    Use apply_v2_dedup() after this for the corrected duplicate flags.
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


def _haversine_km(lat1, lon1, lat2, lon2):
    """Vectorised Haversine distance (arrays → km)."""
    R = 6371.0
    phi1, phi2 = np.radians(lat1), np.radians(lat2)
    dphi = np.radians(lat2 - lat1)
    dlam = np.radians(lon2 - lon1)
    a = np.sin(dphi / 2) ** 2 + np.cos(phi1) * np.cos(phi2) * np.sin(dlam / 2) ** 2
    return 2 * R * np.arcsin(np.sqrt(a))


def _bst_time_to_minutes(time_str) -> float:
    """Parse HH:MM:SS BST string → minutes since midnight. Returns NaN if unparseable."""
    try:
        t = pd.to_datetime(f"2000-01-01 {str(time_str).strip()}", errors="coerce")
        if pd.isna(t):
            return np.nan
        return t.hour * 60 + t.minute + t.second / 60
    except Exception:
        return np.nan


def apply_v2_dedup(df: pd.DataFrame) -> pd.DataFrame:
    """
    Stage 2 BST/UTC date-shift correction.  Applied after the v1 key-based pass (Stage 1).

    Catches events where the BST-dated main catalog and a UTC-dated modern file
    record the same physical earthquake on different calendar dates:
        BST_date = UTC_date + 1 day  (event at 00:00–05:59 BST → previous UTC day)
        BST_time − 6h ≈ UTC_time  (within _DEDUP_CLOCK_M minutes)
        dist ≤ _DEDUP_DIST_KM km  AND  |ΔM| ≤ _DEDUP_DMAG_B

    Events that fail the clock-time consistency check (|Δ_clock| > _DEDUP_CLOCK_M min)
    are NOT merged — they are treated as genuinely distinct events (aftershocks,
    swarms) despite geographic proximity.

    Background: the July 2023 overlap between the BST-dated main catalog and the
    UTC-dated monthly file produces 6 double-counted events.  The v1 key misses
    these because they have different date_iso values (BST vs UTC calendar day).
    See docs/dedup_audit.md for full audit results and rationale.
    """
    SOURCE_RANK = {
        "Seismic Data of Bangladesh-2023x.doc":                       1,
        "মাসিক ডাটা ২৩-২৪.docx":                                     2,
        "Bangladesh felt Data_January 2024-24 January 2025.docx":     3,
        "Bangladesh fell Data 2025(January-(August).docx":            4,
    }

    df = df.copy()
    df["datetime_utc"] = pd.to_datetime(df["datetime_utc"], errors="coerce")
    df["date_dt"]      = pd.to_datetime(df["date_iso"],      errors="coerce")

    already_dup = set(df.index[df["duplicate_flag"]])  # flagged by v1

    # Work only on non-duplicate rows from v1
    active = df[~df["duplicate_flag"]].copy().reset_index()
    active.rename(columns={"index": "orig_idx"}, inplace=True)

    new_dup_orig_indices = set()

    # ── Stage B: BST/UTC date-shift ────────────────────────────────────────────
    bst_mask = active["catalog_type"] == "historical_bst"
    bst_rows = active[bst_mask].copy()
    utc_rows = active[~bst_mask].copy()

    bst_rows["bst_min"] = bst_rows["time_bst"].apply(_bst_time_to_minutes)
    bst_rows["date_int"] = bst_rows["date_dt"].dt.to_period("D").astype("int64")
    utc_rows["date_int"] = utc_rows["date_dt"].dt.to_period("D").astype("int64")

    has_utc_time = utc_rows["datetime_utc"].notna()
    utc_rows["utc_min"] = np.nan
    if has_utc_time.any():
        utc_rows.loc[has_utc_time, "utc_min"] = (
            utc_rows.loc[has_utc_time, "datetime_utc"].dt.hour * 60
            + utc_rows.loc[has_utc_time, "datetime_utc"].dt.minute
            + utc_rows.loc[has_utc_time, "datetime_utc"].dt.second / 60
        )

    # Cross-join on BST_date = UTC_date + 1 day
    for day_shift in [1, 0]:
        bst_j = bst_rows.copy(); bst_j["join_date"] = bst_j["date_int"] - day_shift
        utc_j = utc_rows.copy(); utc_j["join_date"] = utc_j["date_int"]

        pairs = pd.merge(bst_j, utc_j, on="join_date", suffixes=("_b", "_u"))
        if len(pairs) == 0:
            continue

        # Distance filter
        pairs["dist_km"] = _haversine_km(
            pairs["latitude_b"].values, pairs["longitude_b"].values,
            pairs["latitude_u"].values, pairs["longitude_u"].values,
        )
        pairs = pairs[pairs["dist_km"] <= _DEDUP_DIST_KM]
        if len(pairs) == 0:
            continue

        # Magnitude filter
        pairs["dmag"] = (pairs["magnitude_b"] - pairs["magnitude_u"]).abs()
        pairs = pairs[pairs["dmag"] <= _DEDUP_DMAG_B]
        if len(pairs) == 0:
            continue

        # Skip same source file
        pairs = pairs[pairs["source_file_b"] != pairs["source_file_u"]]
        if len(pairs) == 0:
            continue

        # Clock-time consistency check (only when both times are available)
        has_both = pairs["bst_min_b"].notna() & pairs["utc_min_u"].notna()
        pairs["clock_delta_min"] = np.nan
        if has_both.any():
            bst_as_utc = (pairs.loc[has_both, "bst_min_b"] - 360.0) % 1440
            diff = (bst_as_utc - pairs.loc[has_both, "utc_min_u"]).abs()
            diff = diff.where(diff <= 720, 1440 - diff)
            pairs.loc[has_both, "clock_delta_min"] = diff

        # Confirm: BST hour < 6 (midnight crossing), day_shift==1, clock within tolerance
        confirmed = pairs[
            (pairs["bst_min_b"] / 60 < 6.0)
            & (pairs["clock_delta_min"].isna() | (pairs["clock_delta_min"] <= _DEDUP_CLOCK_M))
        ]

        for _, p in confirmed.iterrows():
            oi = int(p["orig_idx_b"])  # BST main-catalog row → mark as duplicate
            if oi not in new_dup_orig_indices:
                new_dup_orig_indices.add(oi)

    # Apply Stage B flags
    if new_dup_orig_indices:
        df.loc[list(new_dup_orig_indices), "duplicate_flag"] = True

    return df


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

    # ── Stage 1: v1 key-based dedup ───────────────────────────────────────────
    df_all["dedup_key"] = dedup_key(df_all)

    # Sort so that higher _source_rank (more modern / curated) comes first within each key
    df_all = df_all.sort_values(["dedup_key", "_source_rank"], ascending=[True, False])

    # Mark duplicates: first occurrence (highest rank) is kept; others are flagged
    df_all["duplicate_flag"] = df_all.duplicated(subset=["dedup_key"], keep="first")

    n_dups_v1 = df_all["duplicate_flag"].sum()
    print(f"\n  Total rows before dedup: {len(df_all)}")
    print(f"  Stage 1 (v1 key) duplicates:  {n_dups_v1}")

    # ── Stage 2: v2 BST/UTC date-shift correction ──────────────────────────────
    # Catches events where BST date ≠ UTC date (00:00–05:59 BST → previous UTC day).
    # The July 2023 overlap between the main catalog (BST) and monthly file (UTC)
    # produces 6 such pairs.  See docs/dedup_audit.md for full audit.
    df_all = apply_v2_dedup(df_all)

    n_dups = df_all["duplicate_flag"].sum()
    n_stage2 = n_dups - n_dups_v1
    print(f"  Stage 2 (BST/UTC shift) additional:  {n_stage2}")
    print(f"  Total duplicate rows flagged:  {n_dups}")
    print(f"  Unique events:                 {len(df_all) - n_dups}")

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
    out_csv     = DATA_DIR / "master_catalog_spatial_v2.csv"
    out_parquet = DATA_DIR / "master_catalog_spatial_v2.parquet"

    # Save only unique physical events as the canonical analysis dataset
    df_unique = df[~df["duplicate_flag"]].copy()

    # Cast all object (mixed-type) columns to string for parquet compatibility
    df_parquet = df_unique.copy()
    for col in df_parquet.select_dtypes(include=["object", "str"]).columns:
        df_parquet[col] = df_parquet[col].astype(str).replace("nan", "")

    df_unique.to_csv(out_csv, index=False, encoding="utf-8")
    df_parquet.to_parquet(out_parquet, index=False)

    print(f"\n  Saved CSV     → {out_csv.relative_to(PROJECT_ROOT)}")
    print(f"  Saved Parquet → {out_parquet.relative_to(PROJECT_ROOT)}")

    return df


if __name__ == "__main__":
    main()
