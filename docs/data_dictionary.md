# Data Dictionary — Bangladesh Earthquake Catalog (master_catalog_spatial_v2.csv)

## Source files

| Label | File | Period | Events |
|-------|------|--------|--------|
| main_catalog | Seismic Data of Bangladesh-2023x.doc | 1918–2022 | 864 |
| monthly_2023_2024 | মাসিক ডাটা ২৩-২৪.docx | Jul 2023 – Jun 2024 | 129 (broader only) |
| felt_2024_2025 | Bangladesh felt Data_January 2024-24 January 2025.docx | Jan 2024 – Jan 2025 | 77 |
| felt_2025 | Bangladesh fell Data 2025(January-(August).docx | Jan 2025 – Aug 2025 | 67 |

---

## Schema — master_catalog_spatial_v2.csv

### Identity fields

| Column | Type | Description |
|--------|------|-------------|
| event_id | string | Unique event identifier: EV-XXXXX. Assigned during harmonisation. Sequential within the combined dataset; not a permanent ID. |
| source_file | string | Original source document filename. |
| source_period | string | Human-readable coverage period of the source file. |
| catalog_type | string | Type of catalog entry: `historical_bst` (main catalog, BST time), `broader` (monthly: all detected), `felt_near_bangladesh` (monthly felt-nearby or modern felt files). |

---

### Date / time fields

| Column | Type | Description |
|--------|------|-------------|
| date_iso | string | Event date in ISO format (YYYY-MM-DD). |
| date_raw | string | Original date string from source document (unparsed). |
| year | int64 | Year extracted from date_iso. |
| month | int64 | Month (1–12) extracted from date_iso. |
| day | int64 | Day extracted from date_iso. |
| decade | int64 | Decade (1910, 1920, …, 2020). |
| time_bst | string | Time of occurrence in Bangladesh Standard Time (BST = UTC+6). Format: HH:MM:SS. Present only for main catalog (1918–2022). Missing for pre-1984 events (recorded as NA). |
| time_utc | string | Time of occurrence in UTC. Format: HH:MM:SS. Present for modern files (2023–2025). |
| datetime_utc | datetime | Combined UTC datetime (date + time_utc, or date + time_bst - 6h for main catalog). NA where time is missing. |
| time_missing | bool | True = time was not recorded in the source (common for historical events before 1984). |
| time_zone_raw | string | Original time zone label from source: `BST` (main catalog) or `UTC` (modern files). |

---

### Location fields

| Column | Type | Description |
|--------|------|-------------|
| latitude | float | Decimal degrees North. Converted from source DMS (degrees + decimal minutes). |
| longitude | float | Decimal degrees East. Converted from source DMS. |
| lat_deg_raw / lat_mts_raw | string | Raw degree and minute values from the main catalog (split columns). |
| lon_deg_raw / lon_mts_raw | string | Raw degree and minute values from the main catalog. |
| lat_raw / lon_raw | string | Raw DMS coordinate strings from modern files (e.g., "26° 12.30′N"). |
| region_raw | string | Free-text region/location description from source. Not standardised. Empty for main catalog. |
| inside_bangladesh | bool | True = epicentre falls inside the Bangladesh administrative boundary (Natural Earth 10m shapefile, EPSG:4326). |
| epicenter_country | string | Country where epicentre falls (spatial join with Natural Earth countries). "Unknown" = ocean/unmatched. |
| source_corridor | string | Seismotectonic source corridor (heuristic bounding-box classification). See corridors table below. |
| event_class | string | Broad event classification: `domestic_BD`, `cross_border_near` (≤300 km from Dhaka, outside BD), `distant_regional` (300–1500 km), `very_distant` (>1500 km). |
| distance_dhaka_km | float | Great-circle distance from Dhaka (23.81°N, 90.41°E) to epicentre, in km. Computed via Haversine formula. |
| distance_bd_border_km | float | Approximate distance from epicentre to the nearest point on the Bangladesh border, in km. 0 for domestic events. Computed from Shapely boundary distance (degrees × 111 km/degree); approximate only. |

---

### Magnitude / intensity fields

| Column | Type | Description |
|--------|------|-------------|
| magnitude | float | Magnitude value. Labeled "Richter" in all source files, but likely a mix of ML, Mw, mb across eras and agencies. Do NOT assume consistent scale. |
| magnitude_raw | string | Original magnitude string from source document. |
| magnitude_type | — | Not available in any source file. All entries labeled "Richter Scale." |
| intensity_label | string | Verbal intensity descriptor from main catalog: Major, Strong, Moderate, Light, Minor, Very Minor. Only present for main catalog (1918–2022). |
| intensity_numeric | int | Approximate numeric mapping of intensity: Major=8, Strong=6, Moderate=5, Light=4, Minor=3, Very Minor=2. For reference only; not a standardised intensity scale. |
| depth_km | float | Focal depth in km. Available only for some monthly 2023–2024 entries; mostly missing ("--" in source). |

---

### Quality / audit fields

| Column | Type | Description |
|--------|------|-------------|
| parse_flags | string | Pipe-separated list of parsing issues encountered for this row. Empty = no issues. Examples: `time_missing_historical`, `date_typo_corrected:26-012014`, `lat_coord_missing`. |
| distance_dhaka_km_raw | string | Raw "Distance from Dhaka (Km)" value from modern source files. Not available for main catalog. |
| sl | string | Serial number from felt_2025 source file. Empty elsewhere. |
| duplicate_flag | bool | v1 dedup flag. **Always False in master_catalog_spatial_v2.csv**: v1 duplicates (33 events identified by key-based matching) were removed before spatial enrichment and are not present in this file. Retained for schema compatibility. |
| duplicate_flag_v2 | bool | v2 dedup flag. True = this row was identified as a BST/UTC midnight date-shift duplicate of another row (Stage 2 correction). 6 rows are True. Use `~duplicate_flag_v2` to select unique events. |
| dedup_note_v2 | string | Human-readable explanation of why duplicate_flag_v2=True (e.g., matching event ID, BST/UTC date shift, clock delta). Empty when duplicate_flag_v2=False. |
| dedup_key | string | Concatenated string used for v1 (Stage 1) key-based deduplication: `date_lat_lon_magnitude` (rounded). |

---

## Source corridor definitions

Corridors are heuristic bounding-box approximations of seismotectonic source zones relevant to Bangladesh hazard. Priority-ordered (first match wins after inside_bangladesh check).

| Corridor label | Lat range | Lon range | Notes |
|----------------|-----------|-----------|-------|
| BD_domestic | — | — | Events confirmed inside Bangladesh by boundary test |
| Chittagong_Hills | 21–24°N | 91.5–93°E | Eastern Bangladesh / Tripura fold belt |
| Sylhet_Region | 24–25.5°N | 91–92.5°E | Sylhet trough / Brahmaputra fold |
| Assam_Meghalaya | 25–27.5°N | 89.5–96°E | Assam seismic belt, Meghalaya Plateau |
| Myanmar_India_Border | 20–27°N | 92.5–95.5°E | Manipur, Mizoram, Chin State fold-thrust belt |
| Myanmar_Interior | 16–27°N | 95.5–101°E | Central Myanmar |
| Nepal_Himalaya | 26.5–31°N | 80–88.5°E | Main Himalayan Thrust zone, Nepal |
| Bhutan_E_Himalaya | 26.5–29°N | 88.5–92.5°E | Eastern Himalaya, Bhutan |
| Bay_of_Bengal | 10–22°N | 85–94°E | Offshore Bay of Bengal |
| Andaman_Nicobar | 6–14.5°N | 92–94.5°E | Andaman-Nicobar arc |
| South_Asia_Interior | 20–36°N | 68–90°E | Stable Indian craton + western folds |
| SE_Asia_Far | -5–35°N | 94–135°E | Southeast Asia, East Asia (distant) |
| Other_Distant | global | global | Anything not matched above |

---

## Transformations performed

1. **DOC → DOCX conversion**: `Seismic Data of Bangladesh-2023x.doc` converted using LibreOffice `--headless`.
2. **Coordinate conversion**: Degrees + decimal minutes → decimal degrees. Formula: `DD = deg + mts/60`.
3. **Date parsing**: Main catalog: `DD-MM-YYYY` or `DD/MM/YYYY`. Modern files: `DD/MM/YYYY`. One OCR typo corrected (`26-012014` → `2014-01-26`).
4. **Time zone**: Main catalog times are BST (UTC+6); UTC = BST - 6h.
5. **Deduplication (v2)**: Two-stage procedure. Stage 1: key-based match on (date, lat ±0.1°, lon ±0.1°, magnitude ±0.05) — 33 duplicates flagged. Stage 2: BST/UTC midnight date-shift correction — 6 additional duplicates identified in July 2023 overlap (main catalog BST-dated vs monthly UTC-dated). Total: 39 duplicates removed, 1112 unique events retained. See `docs/dedup_audit.md`.
6. **Spatial enrichment**: Boundary test and spatial join using Natural Earth 10m admin-0 boundaries.
7. **Corridor classification**: Priority-ordered bounding-box assignment, then overridden by inside_bangladesh test.

---

## Uncertainty notes

- **Magnitude scale uncertainty**: The catalog does not distinguish ML, Mw, mb. Mixed scales inflate apparent magnitude range and make G-R analysis across eras unreliable.
- **Catalog completeness**: Mc (completeness magnitude) is likely ~3.5–4.0 for the 2007+ period. The Aki MLE b-value of 0.27 (computed at Mc=3.0) confirms severe under-reporting below M3.5.
- **Coordinate precision**: Main catalog coordinates are in integer degrees + integer minutes (1 arcminute ≈ 1.8 km). Modern files give decimal minutes (higher precision). Do not overinterpret spatial clustering in the historical record.
- **Corridor boundaries**: The corridor bounding boxes are heuristic approximations. A rigorous seismotectonic zonation would require digitised published zone maps (BMD, GSB, IMD).
- **Distance to border**: Computed as great-circle distance from point to Shapely boundary, converted at 111 km/degree. Approximate only; use distance_dhaka_km for quantitative work.
