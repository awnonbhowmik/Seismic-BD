# Research Log — Bangladesh Earthquake Catalog Analysis

---

## Session 1 — April 2026

### File inventory
Discovered four source documents:
1. `Seismic Data of Bangladesh-2023x.doc` — 1 MB, main historical catalog 1918–2022
2. `Bangladesh felt Data_January 2024-24 January 2025.docx` — 56 KB
3. `Bangladesh fell Data 2025(January-(August).docx` — 64 KB
4. `মাসিক ডাটা ২৩-২৪.docx` — 91 KB, Bengali-titled monthly reports Jul 2023–Jun 2024

### Schema findings
- **Main catalog**: 11 tables, 10 columns each. Lat/Lon in split degrees + minutes. Time in BST. No region label.
- **Felt 2024-2025**: 1 table, 7 columns. UTC time. DMS coordinates as strings. Region text included.
- **Felt 2025**: 1 table, 8 columns (adds serial number). Same structure as 2024-2025.
- **Monthly 2023-2024**: 22 tables in pairs per month. "Broader" tables (all detected events) paired with "felt near Bangladesh" subsets. Bengali paragraph titles decoded from Bijoy ANSI encoding.

### Key parsing decisions
- Main catalog Table 10 uses DD/MM/YYYY (not DD-MM-YYYY) — fixed in parser.
- One OCR typo: `26-012014` corrected to `2014-01-26` with flag.
- Monthly Bengali titles decoded: patterns `RyjvB` = July, `AvM÷` = August, etc.
- Monthly "felt_nearby" tables excluded from master catalog to prevent double-counting.
- 33 events flagged as duplicates by (date, rounded lat/lon, magnitude) key.

### Deduplication
- 1151 total rows across all sources.
- 33 duplicates flagged by v1 key-based rule (2.9%).
- v2 audit (see docs/dedup_audit.md) identified 6 additional missed duplicates:
  BST/UTC midnight date-shift in July 2023 main catalog / monthly overlap.
- **1112 unique events retained** (v2 dedup, corrected catalog).
- Overlap concentrated at: monthly 2023-2024 / felt 2024-2025 boundary (Jan 2024).

### Spatial enrichment decisions
- Bangladesh boundary: Natural Earth 10m admin-0. 107 events inside BD.
- Country assignment: spatial join with world countries.
- Source corridor: priority-ordered bounding box assignment. BD_domestic bounding box initially too large (277 events) — refined to match inside_bangladesh flag (107 events). 170 events reclassified to more specific corridors.

### Key analytic findings
1. **90.4%** of unique events are outside Bangladesh. For M≥4.0: 94.4%.
2. Myanmar dominates (380 events, 34.2%). India second (314, 28.2%).
3. Myanmar-India Border corridor alone: 311 events (28.0%).
4. Domestic Bangladesh: 107 events (9.6%) — the 4th-largest source behind Myanmar, India, and distant/unmatched.
5. G-R b-value (Aki MLE, Mc=3.0, 2007+): 0.267 — strongly indicates Mc > 3.0. Catalog incomplete below M~3.5.
6. Seasonality chi-squared test: should be run in notebook to assess.
7. 2000–2006: complete gap (0 events). Cannot be treated as seismically quiet.

### Data quality flags
- No depth data in main catalog.
- No magnitude type info — all "Richter" label is unreliable across eras.
- Coordinate precision lower in main catalog (integer deg+min) vs modern files (decimal min).
- Pre-2000 events: 27 only. Safe for spatial distribution, not temporal trends.

### Paper direction decision
**Recommend Candidate B: Cross-Border Seismic Dependence** as the primary direction.
Strongest data support, novel finding, policy-relevant, no completeness assumption needed for the main result.

---

*Log continues in next session.*
