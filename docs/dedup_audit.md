# Deduplication Audit Report — Bangladesh Earthquake Catalog

**Date**: April 2026  
**Input**: `data/master_catalog_spatial.csv` (v1 dedup, 1118 unique events)  
**Output**: `data/master_catalog_spatial_v2.csv` (v2 dedup, 1112 unique events)  
**Net change**: −6 events removed (0.54% of v1 catalog)

---

## 1. Current (v1) deduplication rule

```
key = date_iso + "_" + round(lat,0.1°) + "_" + round(lon,0.1°) + "_" + round(mag,1dp)
```

Spatial tolerance ≈ 11 km. No time field. Matches only on exact same calendar date.

### Known weaknesses

| Weakness | Risk | Confirmed |
|----------|------|-----------|
| No time in dedup key | HIGH | Yes — missed 6 duplicates |
| BST/UTC midnight date shift | HIGH | Yes — confirmed mechanism |
| Same-day aftershock not distinguished | MEDIUM | Low — mag rounding buffers this |
| 0.1° tolerance may be too wide | LOW | Not confirmed |

---

## 2. Confirmed failure: BST/UTC midnight date shift

The main catalog (BST) and monthly 2023–2024 file (UTC) use different time zones.
Events at 00:00–05:59 BST are stored on the BST calendar date by the main catalog
but on the **previous** UTC calendar date by the monthly file.
The v1 key uses `date_iso` → these appear as different keys → false double-count.

**6 confirmed instances** found in the July 2023 overlap zone.

| Main catalog date | Monthly date | BST time (main) | Δ clock (min) | Dist (km) | ΔM |
|---|---|---|---|---|---|
| 2023-07-21 | 2023-07-20 | 04:39:45 BST | 0 | 1.7 | 0.00 |
| 2023-07-22 | 2023-07-21 | 02:05:46 BST | 0 | 0.8 | 0.00 |
| 2023-07-25 | 2023-07-24 | 02:14:30 BST | 0 | 1.6 | 0.00 |
| 2023-07-28 | 2023-07-27 | 04:13:55 BST | 0 | 1.5 | 0.00 |
| 2023-07-30 | 2023-07-29 | 04:29:31 BST | 0 | 1.5 | 0.00 |
| 2023-07-31 | 2023-07-30 | 00:33:44 BST | 0 | 1.6 | 0.00 |

---

## 3. False-merge risk under v1

9 event pairs share the same date + 0.1° bucket but have
different rounded magnitudes (survived v1). These show the current rule's limits.

| Date | M1 | M2 | Dist (km) | Δt (min) | Risk |
|------|----|----|-----------|----------|------|
| 2008-09-20 | 4.3 | 4.8 | 4.1 | 65 | LOW |
| 2015-04-25 | 4.7 | 5.3 | 10.5 | 102 | LOW |
| 2015-04-25 | 5.0 | 5.4 | 9.9 | 50 | LOW |
| 2019-11-26 | 4.7 | 5.4 | 9.5 | 90 | LOW |
| 2020-07-17 | 4.3 | 5.3 | 3.7 | 367 | LOW |
| 2021-05-29 | 2.8 | 4.1 | 0.0 | 39 | LOW |
| 2021-05-29 | 3.0 | 4.0 | 3.8 | 202 | LOW |
| 2023-07-30 | 4.8 | 4.9 | 3.5 | 859 | MEDIUM |
| 2024-06-02 | 5.0 | 5.1 | 7.5 | 8 | HIGH |

**Conclusion**: Magnitude rounding acts as an accidental safeguard.
The v1 false-merge risk is **low** for the actual data.

---

## 4. Improved (v2) deduplication

### Stage A — Strong match (both UTC timestamps available)
- |Δt| ≤ 60 min, dist ≤ 25 km, |ΔM| ≤ 0.3
- Different source files only

### Stage B — BST/UTC date-shift correction
- One source is `historical_bst`; other is UTC-dated
- BST_date = UTC_date + 1 day (midnight crossing)
- BST_time − 6h ≈ UTC_time (within 15 min)
- dist ≤ 25 km, |ΔM| ≤ 0.2

### Stage C — Do not merge
- Clock-time check fails (|Δ_clock| > 15 min)
- Same-day events with clearly different times (aftershocks, swarms)

---

## 5. Before vs after

| version | n_unique_events | n_inside_bd | n_outside_bd | pct_outside_bd | n_m_ge_4 | n_m_ge_5 | n_m_ge_6 | pct_outside_m4 | top_corridor | top_country | n_2023 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| v1 (original) | 1118 | 107 | 1011 | 90.43 | 949 | 315 | 58 | 94.42 | Myanmar_India_Border | Myanmar | 130 |
| v2 (improved) | 1112 | 107 | 1005 | 90.38 | 943 | 314 | 58 | 94.38 | Myanmar_India_Border | Myanmar | 124 |

---

## 6. Impact on paper conclusions

| Metric | v1 | v2 | Change |
|--------|----|----|--------|
| Total unique events | 1118 | 1112 | −6 (0.54%) |
| % outside Bangladesh | 90.43% | 90.38% | 0.05 pp |
| % M≥4 outside Bangladesh | 94.42% | 94.38% | 0.04 pp |
| 2023 annual count | 130 | 124 | −6 |
| Top corridor | Myanmar_India_Border | Myanmar_India_Border | unchanged |
| Top country | Myanmar | Myanmar | unchanged |

All removed events are cross-border. No domestic event is affected.
No decade-level, corridor-level, or paper-level conclusion changes.

---

## 7. Methods section language

> *'Events were deduplicated using a two-stage procedure.*
> *Stage A matched records from different source files with both UTC timestamps*
> *available: |Δt| ≤ 60 min, dist ≤ 25 km, |ΔM| ≤ 0.3.*
> *Stage B corrected for BST/UTC date shift: {n_removed} events in the July 2023*
> *overlap between the BST-dated main catalog and the UTC-dated monthly file*
> *appeared on different calendar dates despite being the same physical earthquake.*
> *These were identified by confirming that BST_time − 6h matched the monthly*
> *file UTC_time within 15 minutes and epicentral separation < 25 km.*
> *Same-day aftershock/swarm events were protected from false merging by*
> *the clock-time consistency check (Stage C).'*