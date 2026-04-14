# Seismic-BD Audit Fixes

**Audit date**: 2026-04-14  
**Auditor**: Code-first audit pass (Claude Code)  
**Scope**: 8 issues per specification + follow-up magnitude-field architecture

---

## Issue 1: M 8.8 "Myanmar 2025" — misidentified event (identity error only)

### Root cause
The manuscript, README, research_memo, and build_notebook.py all described the largest catalog
event as "M 8.8 (2025 Myanmar — the Mandalay earthquake sequence)." This is a **location
misidentification**: the event is in Kamchatka, Russia, not Myanmar.

1. **Wrong location**: EV-01144 (M 8.8, 2025-07-29) is at **52.53°N 160.16°E — Kamchatka,
   Russia**, approximately 6,575 km from Dhaka. The `region_raw` field reads "kamchatka,Russia"
   and the event is classified `Other_Distant` / `very_distant`.

2. **Wrong earthquake**: The 2025 Myanmar (Mandalay) earthquake is a **separate event** —
   EV-01120 (2025-03-28, M 7.3 per BMD / M 7.7 per USGS, at 21.73°N 95.77°E, Mandalay,
   Myanmar).

3. **Magnitude (M 8.8) is accepted as reported by BMD.** No claim is made that this value
   is wrong; it is retained in both `magnitude` and `magnitude_analysis` columns. The event
   is in the BMD felt-events document and was recorded as felt in Bangladesh.

### Fix applied
- `src/utils/build_notebook.py`: All references to "M 8.8 Myanmar" corrected to distinguish
  the Kamchatka event (EV-01144, M 8.8) from the Mandalay event (EV-01120, M 7.3/7.7).
- `docs/research_memo.md`: Same corrections, plus audit note added.
- `README.md`: "Largest event" table row corrected.
- No wording implying the M 8.8 magnitude is suspicious or unverified.

### CSV change
**None to `magnitude`.** The catalog CSV retains M 8.8 for EV-01144 in both `magnitude`
(raw BMD) and `magnitude_analysis` (analysis field, introduced in follow-up — see below).

### Evidence
- EV-01144: lat=52.53, lon=160.16, region_raw="kamchatka,Russia", distance_dhaka_km=6575.1
- EV-01120: 2025-03-28, M=7.3, lat=21.73, lon=95.77, region_raw="Mandalay, Myanmar"

### Downstream outputs affected
- `analysis.ipynb` Sections 10, 11, 15, 16 text
- `README.md` Key findings table
- `docs/research_memo.md`

---

## Issue 2: Table 1 count mismatch (1111 vs 1112)

### Root cause
The Section 4 completeness table listed four time bins summing to 1111:
Pre-2000 (27) + 2000–2006 (0) + 2007–2022 (776) + 2023–2025 (308) = **1111**

The missing event is **EV-01151**, a parsing artifact with all-NaN fields. It is correctly
excluded from all year-binned analyses but was not accounted for in the table.

### Fix applied
- `src/utils/build_notebook.py` Section 4: added "Year unknown | 1" and "Total | 1112" rows.
- `docs/research_memo.md` Section 1.1: same rows added.

### Evidence
```python
df[df.year.isna()]  # → 1 row: EV-01151, all NaN
```

---

## Issue 3: Forecast text ranges corrected

### Root cause
Section 11 narrative stated approximate ranges ("55–70 per year" etc.) not matching the
actual 90% Poisson prediction intervals.

### Verified values (stationary Poisson, 90% PI):

| Category | Mean/yr | Old text | Actual 90% PI |
|---|---|---|---|
| All events | 56.3 | 55–70 | [44, 69] |
| M ≥ 4.0 | 48.1 | 48–62 | [37, 60] |
| M ≥ 5.0 | 14.9 | 16–20 | [9, 22] |
| Inside BD | 5.3 | 5–8 | [2, 9] |
| Cross-border | 51.0 | 50–65 | [40, 63] |

Domestic + cross-border means (5.33 + 51.00 = 56.33) exactly equal "All events" mean —
internally consistent. Five identical stationary rows in the forecast table are
mathematically correct for a stationary model.

### Fix applied
`src/utils/build_notebook.py` Section 11: replaced approximate text with computed
mean + 90% PI values.

---

## Issue 4: Magnitude scale disclosure

### Fix applied
Section 6 (G-R analysis) now opens with an explicit disclosure that the catalog mixes
ML/mb/Mw all labeled "Richter Scale"; no magnitude_type column exists; formal Mw
homogenisation recommended before publication.

---

## Issue 5: Historical catalog gaps

### Confirmed absences

| Event | Date | M | In catalog? |
|---|---|---|---|
| Assam earthquake | 1950-08-15 | 8.6–8.7 | **No** |
| Bihar–Nepal earthquake | 1934-01-15 | 8.0–8.1 | **No** |

These are **catalog limitations** (absent from source documents), not errors. Documented
in Section 4 notebook and research_memo.md limitations.

---

## Issue 6: Figure improvements

Already resolved (commit d81cc1d / d5b1664): FS=16, 300 dpi PNG, high-contrast palette,
thicker lines. No further changes needed.

---

## Issue 7: References to "M 8.8 Myanmar"

All 6 instances corrected (see Issue 1 above).

---

## Issue 8: Reproducibility

Notebook rebuilt and executed (64 cells, zero errors, all 20 figures regenerated).

---

## Follow-up: `magnitude_analysis` field introduced

### Motivation
To clearly separate the immutable BMD source-document magnitude from the field used
in analysis code, a `magnitude_analysis` column was added to the catalog. This enables:
- future per-event adjustments without touching the source-preserved `magnitude` field
- analysis code that explicitly documents which field it reads
- a clean separation between "what BMD recorded" and "what the study uses"

### Current values
`magnitude_analysis = magnitude` for all events (including EV-01144, M 8.8 Kamchatka).
No values differ from `magnitude` at present.

### Column position
Inserted immediately after `magnitude_raw` in `data/master_catalog_spatial_v2.csv`.

### Code changes
`src/utils/build_notebook.py`: all analysis code that previously read `df_bmd["magnitude"]`,
`df_mod.magnitude`, `modern.magnitude`, `row.magnitude`, etc. now reads the corresponding
`magnitude_analysis` attribute. The earthquakelist supplementary dataframe (`el_*`) retains
its own `magnitude` column unchanged.

Affected analysis sections: magnitude histogram (Fig 3a), ECDF (Fig 3b), G-R fit (Fig 3c),
cross-border magnitude subsets (Figs 8, 9), corridor statistics (Table 7), annual counts
(Fig 1), Mc estimation (Fig 14), magnitude-time plot (Fig 16), return periods (Fig 12),
exceedance probability (Fig 18), summary statistics (Section 19).

---

## Summary: what remains uncertain

1. **EV-01144 M 8.8 (Kamchatka, 2025-07-29)**: Identity confirmed as Kamchatka by
   coordinates and region_raw. BMD-reported magnitude 8.8 is accepted as-is; it is
   retained in `magnitude` and `magnitude_analysis` unchanged.

2. **EV-01120 Mandalay (2025-03-28)**: BMD M 7.3 vs USGS M 7.7 — normal inter-agency
   difference. BMD value used throughout; difference should be noted in paper methods.

3. **2012 Indian Ocean doublet (EV-00197/EV-00198)**: BMD records M 8.1/8.7; USGS M 8.6/8.2.
   Flagged but not corrected — insufficient local evidence to override source document.

4. **1950 Assam / 1934 Bihar-Nepal**: Absent from catalog; cannot be added without an
   independent catalog. Future enhancement only.

5. **EV-01151 (NaN artifact)**: Excluded from all analyses. Could be dropped from the CSV
   for cleanliness without affecting any result.

---

## Files modified

| File | Change |
|------|--------|
| `data/master_catalog_spatial_v2.csv` | `magnitude_analysis` column added |
| `src/utils/build_notebook.py` | Identity corrections; `magnitude_analysis` used in all analysis code; forecast text corrected; scale disclosure added; historical gaps documented |
| `docs/research_memo.md` | Count table fixed; identity corrections; limitations updated |
| `README.md` | Key findings table corrected; EPS→PNG reference |
| `AUDIT_FIXES.md` | This file |
| `analysis.ipynb` | Rebuilt and re-executed |
