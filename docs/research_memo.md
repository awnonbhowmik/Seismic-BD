# Research Memo: Bangladesh Earthquake Catalog Analysis

**Date**: April 2026
**Data**: BMD earthquake catalog, four source documents, 1918–2025
**Author**: Analysis performed programmatically; to be reviewed by researcher

---

## 1. What the data credibly supports

### 1.1 Catalog structure and era effects

The BMD catalog is real and usable but has pronounced era effects that make direct cross-period comparisons invalid without explicit correction:

| Period | Events | Status |
|--------|--------|--------|
| 1918–1999 | 27 | Sparse historical record; only significant events (M≥5 effectively) |
| 2000–2006 | 0 | Clear reporting/digitisation gap — NOT seismically quiet |
| 2007–2022 | 776 | Modern instrument era; more systematic; felt-in-BD threshold |
| 2023–2025 | 308 | Multiple overlapping sources; densest coverage |
| Year unknown | 1 | EV-01151: parsing artefact (all fields NaN); excluded from analyses |
| **Total** | **1112** | |

**Implication**: Any count-trend analysis spanning the 2000–2006 gap is invalid. Count increases from 1990s to 2010s are entirely explained by detection improvements, not increased seismicity.

### 1.2 Cross-border seismic dependence (primary finding)

This is the **single strongest finding** from this dataset:

| Magnitude threshold | N events | Inside BD | Outside BD |
|---------------------|----------|-----------|------------|
| All | 1112 | 107 (9.6%) | 1005 (90.4%) |
| M ≥ 3.0 | 1096 | 95 (8.7%) | 1001 (91.3%) |
| M ≥ 4.0 | 943 | 53 (5.6%) | 890 (94.4%) |
| M ≥ 5.0 | 314 | 6 (1.9%) | 308 (98.1%) |
| M ≥ 6.0 | 58 | 3 (5.2%) | 55 (94.8%) |
| M ≥ 7.0 | 21 | 3 (14.3%) | 18 (85.7%) |

**Key fact**: At the hazard-relevant threshold of M ≥ 4.0, **94.4% of earthquakes are external to Bangladesh**. This is not an artefact of geographic scope — it reflects the actual seismotectonic situation: Bangladesh sits on a tectonically active margin surrounded by much more seismically productive zones.

### 1.3 Source region composition

Top epicentre countries in catalog:
1. Myanmar: 380 events (34.2%)
2. India: 314 events (28.2%)
3. Bangladesh (domestic): 107 events (9.6%)
4. Unmatched (oceanic / remote): 98 events (8.8%)
5. China (distant): 89 events (8.0%)
6. Nepal: 70 events (6.3%)

Top source corridors:
1. Myanmar-India Border: 311 events (28.0%)
2. Assam-Meghalaya: 160 events (14.4%)
3. Myanmar Interior: 115 events (10.3%)
4. BD Domestic: 107 events (9.6%)
5. Nepal-Himalaya: 105 events (9.4%)

The Myanmar-India Border corridor alone accounts for nearly three times the domestic Bangladesh seismicity.

### 1.4 Magnitude distribution

- Overall range: M 2.5 – M 8.8
- Mean magnitude: 4.63
- Largest historical event: M 7.6 (1918, inside Bangladesh — Srimangal earthquake)
- Largest raw magnitude in catalog: M 8.8 (2025-07-29, Kamchatka, Russia — EV-01144, ~6575 km from Dhaka; BMD-reported value **requires USGS cross-check** — not a Myanmar event)
- Largest Myanmar/regional event in catalog: M 7.3 (2025-03-28, Mandalay, Myanmar — EV-01120; BMD value; USGS reports M 7.7 for this event)

> **AUDIT NOTE (2026-04)**: The manuscript/memo previously described the largest catalog event as "M 8.8 (2025 Myanmar — the Mandalay earthquake sequence)." This is factually incorrect. The M 8.8 event (EV-01144) is located at 52.53°N 160.16°E (Kamchatka, Russia), 6575 km from Dhaka, recorded in the BMD felt-events document. The March 28, 2025 Mandalay earthquake is a separate event (EV-01120, M 7.3 BMD / M 7.7 USGS). The BMD magnitude of 8.8 for the Kamchatka event is itself suspicious and should be cross-validated against USGS; if wrong, the catalog maximum shifts to M 8.7 (2012-04-11 Indian Ocean doublet, EV-00198).

G-R analysis (2007+, conservative Mc = 3.0):
- b-value (linear regression): 0.591
- b-value (Aki MLE): 0.267 ± 0.004
- R²: 0.981

The Aki MLE b-value of 0.27 is strongly anomalous (typical: 0.8–1.2). This is **diagnostic of catalog incompleteness below Mc ≈ 3.5–4.0**, not a geophysical anomaly. The linear regression b-value (0.59) is more reasonable but still below typical values, consistent with a mixed-magnitude-scale catalog. Do not publish these b-values as seismically meaningful without formal Mc estimation (e.g., ZMAP).

---

## 2. Main limitations

1. **No depth data**: The main 1918–2022 catalog has no focal depth. The monthly 2023–2024 file has a depth column but it is almost entirely missing ("--"). Without depth, fault-plane solutions, hazard attenuation modelling, and discrimination between crustal/intermediate events are impossible.

2. **No magnitude type discrimination**: All magnitudes are labeled "Richter Scale" but this is likely a heterogeneous mix of ML (local magnitude), mb (body-wave magnitude), Mw (moment magnitude), and possibly Ms, depending on the reporting agency and era. Mixing these without conversion is a significant source of uncertainty.

3. **Catalog completeness (Mc ≈ 3.5–4.0)**: The Aki MLE b-value strongly indicates the catalog is not complete below M 3.5–4.0. Analyses of event frequency below this threshold are unreliable. Any Gutenberg-Richter extrapolation must use Mc ≥ 3.5 minimum.

4. **2000–2006 data gap**: The complete absence of events in this period is almost certainly a reporting failure, not a seismically quiet period. Any analysis spanning this gap must exclude it or explicitly flag it.

5. **No district-level enrichment**: The source documents contain region labels (e.g., "Jagannathpur, Sylhet") but not structured district codes. District-level assignment would require geocoding the free-text region labels, which is feasible but error-prone.

6. **Coordinate precision disparity**: Main catalog coordinates are in integer degrees + integer minutes (precision ~1.8 km). Modern files give decimal minutes (precision ~0.02–0.1 km). Spatial clustering analyses in the historical record should use generous tolerance.

7. **No independent cross-validation**: The BMD catalog has not been cross-checked against USGS, ISC, or IMD catalogs. Some events may be mislabeled; some external events that affected Bangladesh may be missing.

8. **Notable historical absences confirmed**: The 1950 Assam earthquake (M 8.6–8.7, 1950-08-15) and 1934 Bihar–Nepal earthquake (M 8.0–8.1, 1934-01-15) are **absent** from the catalog despite being among the largest 20th-century earthquakes felt in Bangladesh. This confirms the pre-2000 record captures only a fraction of significant events. Do not use the pre-2000 catalog to infer historical seismic hazard without independent sources.

9. **Kamchatka M 8.8 event (EV-01144, 2025-07-29)**: The BMD source document records an M 8.8 event at 52.53°N 160.16°E (Kamchatka, Russia), ~6575 km from Dhaka. The BMD-reported magnitude of 8.8 has not been cross-validated against USGS; this should be verified. This event is **not** the 2025 Myanmar earthquake — that event (Mandalay, 2025-03-28) is separately recorded as EV-01120 at M 7.3 (BMD) / M 7.7 (USGS).

---

## 3. Catalog completeness guidance

| Analysis | Recommended period | Justification |
|----------|-------------------|---------------|
| Long-run spatial history (M≥5) | 1918–2025 (with gap flagged) | Large events reliably recorded across all eras |
| Descriptive spatial clustering | 2007–2025 | Consistent detection threshold |
| Cross-border fraction analysis | 2007–2025 | More complete; felt events well-documented |
| G-R analysis | 2007–2025 | Only reliable era |
| Magnitude trend analysis | 2007–2025 | Only comparable era |
| Annual count trends | 2007–2025 | Do NOT include 2000–2006 gap |

---

## 4. Ranked paper directions

### Rank 1 (Strongest): Candidate B — Cross-Border Seismic Dependence

**Recommended titles:**
- *"Cross-border seismic dominance: Quantifying external earthquake exposure in Bangladesh from a national catalog (1918–2025)"*
- *"The external seismic exposure of Bangladesh: source region analysis from a century-long BMD earthquake catalog"*

**Why this is the strongest direction:**
- The 90.4% external fraction is a striking, defensible, policy-relevant finding with clear implications.
- It does not require completeness assumptions — the percentage is robust even if the absolute counts change with better data.
- It directly answers a question that is NOT answered by existing literature for Bangladesh.
- The figures are strong: pie charts, corridor maps, country-magnitude breakdown.
- Methodology is transparent and reproducible.
- Policy implications are clear: Bangladesh's seismic building codes and early warning systems must account for external sources.

**Proposed paper structure (5 sections):**
1. Introduction: Bangladesh seismotectonic setting; gap in cross-border dependence quantification.
2. Data and methods: BMD catalog description, harmonisation, quality assessment, spatial classification.
3. Catalog completeness and quality: Era effects, Mc estimation, limitations.
4. Results: Cross-border fraction by magnitude threshold; source-region composition; corridor analysis; temporal trends in source composition.
5. Discussion and conclusions: Implications for seismic hazard assessment; limitations; comparison with regional catalogs.

**Target journals:** Natural Hazards and Earth System Sciences (NHESS), Natural Hazards (Springer), Seismological Research Letters (SRL), BSSA.

---

### Rank 2: Candidate D — Hybrid Catalog + Modern Analysis

**Title ideas:**
- *"A century-scale BMD earthquake catalog for Bangladesh (1918–2025): spatiotemporal patterns and cross-border seismic exposure"*

Adds long-run spatial history as backbone context before the cross-border analysis. Better fit for a broader journal (Natural Hazards) vs pure seismology journals. Requires more work to maintain analytical coherence across sections.

---

### Rank 3: Candidate A — Data/Catalog Paper

Best framed as a **data paper** (Scientific Data, ESSD). Describes the harmonisation methodology, quality flags, and schema. Lower citation ceiling but a genuine methodological contribution. Can be submitted quickly.

---

### Rank 4 (Weakest standalone): Candidate C — Population Exposure

Without annual district-level population density data, this is not viable as a standalone paper. Best as Section 4 of Candidate D. Would require BBS district census data and careful documentation of interpolation assumptions.

---

## 5. Recommended next steps

1. **Immediately**: Run the full notebook analysis. Review all figures. Identify the 3–5 most compelling figures for a paper.

2. **Short-term (1–2 weeks)**:
   - Perform formal ZMAP Mc estimation on the 2007+ data.
   - Compute corridor-specific b-values (domestic vs external).
   - Cross-validate 10–20 key historical events against USGS/ISC.
   - Geocode the region_raw strings to district names where possible.

3. **Medium-term (1–2 months)**:
   - Draft the Candidate B paper structure.
   - Refine corridor boundaries using digitised seismotectonic zone maps from GSB/BMD.
   - If district enrichment is done, add a district-level exposure section.

4. **Supplemental**:
   - Consider merging with USGS/ISC for pre-2007 completeness improvement.
   - Consider a formal probabilistic magnitude conversion to Mw for the historical record.

---

*End of research memo.*
