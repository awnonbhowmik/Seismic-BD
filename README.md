# Seismic-BD: Bangladesh Earthquake Catalog Analysis

Research-grade analysis of the Bangladesh Meteorological Department (BMD) earthquake catalog, 1918–2025.

## Project overview

This project harmonises four source documents purchased from BMD into a single master earthquake catalog, performs systematic data audit, spatial enrichment, and temporal/magnitude/cross-border analyses, and produces a ranked assessment of the strongest publishable research directions.

**Primary finding**: 90.4% of all catalogued events — and 94.4% of M≥4.0 events — originate **outside Bangladesh**. The Myanmar-India Border and Assam-Meghalaya corridors are the dominant seismic sources affecting the country.

## Setup

### Requirements
- Python 3.13+
- Virtual environment (recommended)

```bash
python3.13 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Data

| File | Description |
|------|-------------|
| `data/master_catalog_spatial_v2.csv` | **Primary analysis dataset** — 1112 unique events, 1918–2025, with spatial enrichment (v2 dedup: BST/UTC corrected) |
| `data/master_catalog_spatial.csv` | v1 catalog (1118 events) — retained for comparison; use v2 for analysis |
| `data/earthquakelist_scraped.csv` | Supplementary scrape from earthquakelist.org — 100 events (2016–2026), includes depth & USGS codes |
| `data/bangladesh_boundary.gpkg` | Bangladesh admin boundary (Natural Earth 10m) |
| `data/world_countries.gpkg` | World countries (Natural Earth 10m) |

## Running the analysis

### Run the notebook

```bash
source .venv/bin/activate
jupyter lab
# Open: analysis.ipynb
```

Or execute headlessly to regenerate all figures:

```bash
source .venv/bin/activate
jupyter nbconvert --to notebook --execute analysis.ipynb --output analysis.ipynb --ExecutePreprocessor.timeout=600
```

### Rebuild data pipeline from source (if raw BMD DOCX files are available)

```bash
source .venv/bin/activate

# 1. Convert .doc → .docx
soffice --headless --convert-to docx "Seismic Data of Bangladesh-2023x.doc" --outdir .

# 2. Parse each source file
python src/ingest/parse_main_catalog.py
python src/ingest/parse_modern_files.py

# 3. Build harmonised master catalog
python src/harmonize/build_master_catalog.py

# 4. Spatial enrichment
python src/spatial/enrich_spatial.py

# 5. Scrape supplementary data (optional — requires internet)
python src/ingest/scrape_earthquakelist.py

# 6. Regenerate notebook
python src/utils/build_notebook.py
```

## Project structure

```
Seismic-BD/
├── analysis.ipynb                    Main analysis notebook (10 sections, 10 figures)
├── data/
│   ├── master_catalog_spatial_v2.csv PRIMARY DATASET (1112 unique events, 1918–2025, v2 dedup)
│   ├── master_catalog_spatial.csv    v1 catalog (1118 events, retained for comparison)
│   ├── earthquakelist_scraped.csv    Supplementary (100 events, depth + USGS codes)
│   ├── bangladesh_boundary.gpkg      Bangladesh admin boundary
│   └── world_countries.gpkg          World countries boundary
├── outputs/
│   ├── figures/                      Publication figures (EPS 300 dpi + PNG preview)
│   └── maps/                         Map figures (EPS 300 dpi + PNG preview)
├── src/
│   ├── ingest/                       File parsing + scraping scripts
│   ├── harmonize/                    Master catalog builder
│   ├── spatial/                      Spatial enrichment
│   ├── analysis/                     Standalone analysis scripts
│   └── utils/                        Notebook builder
├── docs/
│   ├── data_dictionary.md            Full variable definitions
│   ├── research_memo.md              Research direction memo
│   └── research_log.md               Running analysis log
└── requirements.txt                  Python dependencies
```

## Key findings

| Finding | Value |
|---------|-------|
| Total unique events | 1112 (v2 dedup) |
| Year range | 1918–2025 |
| Events inside Bangladesh | 107 (9.6%) |
| Events outside Bangladesh | 1005 (90.4%) |
| M≥4.0 outside Bangladesh | 94.4% |
| Top source country | Myanmar (34.2%) |
| Top source corridor | Myanmar-India Border (28.0%) |
| Largest event | M 8.8 (2025 Myanmar) |

## Recommended research direction

**Candidate B: Cross-Border Seismic Dependence**

The dominant seismic exposure of Bangladesh is external — driven by Myanmar-India Border
tectonics, Assam-Meghalaya seismicity, and Nepal/Himalayan events. This is a defensible,
novel, and policy-relevant finding that can be directly supported by this dataset.

See `docs/research_memo.md` for detailed paper direction rankings and recommendations.

## Important caveats

- **Catalog completeness varies strongly by era.** Pre-2000: sparse. 2000–2006: data gap. 2007+: more systematic.
- **Do not interpret count increases as real seismicity increases.** They reflect improved detection.
- **b-value is anomalously low** (Aki MLE ≈ 0.27) indicating Mc > 3.0–3.5.
- **Magnitude scale not standardised** — "Richter" label in source likely mixes ML, Mw, mb.

## Dependencies

- Python 3.13, pandas 3.x, numpy 2.x, geopandas 1.x, matplotlib 3.x, scipy 1.x
- Full requirements: `requirements.txt`
