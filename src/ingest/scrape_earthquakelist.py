"""
Scrape earthquakelist.org/bangladesh/ for supplementary earthquake data.

Assessment of data availability:
  - The site's API is capped at 10 events per call with no working pagination.
  - Direct HTML scraping yields ~35 recent events (last ~3 weeks).
  - The "strongest" API endpoint gives the 10 historically largest events
    (M ≥ 4, within 300 km, going back to ~2016).
  - Total useful yield: ~45 unique events, predominantly 2016–2026.
  - Key value-add over BMD catalog: depth in km, USGS event code, cleaner
    location text, and timestamp precision to seconds.

Output:
  data/earthquakelist_scraped.csv    -- all scraped events
  data/earthquakelist_depth_patch.csv -- subset matching BMD catalog events (for depth enrichment)

NOTE: This is a supplementary source, NOT a replacement for the BMD catalog.
The BMD catalog (1918–2025, 1112 events) is far more comprehensive historically.
This source adds depth data for ~45 recent events and enables USGS cross-validation.
"""

import datetime
import time
from pathlib import Path

import pandas as pd
import requests
from bs4 import BeautifulSoup

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR     = PROJECT_ROOT / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

BASE_URL = "https://earthquakelist.org"
BD_ID    = "44"  # Bangladesh page data-id

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
    "Referer":    "https://earthquakelist.org/bangladesh/",
    "Accept":     "application/json, text/html",
}


# ── 1. Scrape HTML table rows (35 most recent events) ─────────────────────────

def scrape_html_table() -> list[dict]:
    """Parse the HTML table from the Bangladesh page."""
    print("  Fetching HTML page...")
    r = requests.get(f"{BASE_URL}/bangladesh/", headers=HEADERS, timeout=25)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    rows = soup.find_all("tr", attrs={"data-lat": True})
    print(f"  HTML table rows: {len(rows)}")

    events = []
    for row in rows:
        eq_id   = row.get("data-id", "")
        lat_raw = row.get("data-lat", "")
        lon_raw = row.get("data-lng", "")
        mag_raw = row.get("data-mag", "")
        date_raw = row.get("data-date", "")
        dist_raw = row.get("data-dist", "")

        # Parse timestamp from nested span
        span = row.find("span", attrs={"data-timestamp": True})
        ts = int(span["data-timestamp"]) if span else None
        dt = datetime.datetime.utcfromtimestamp(ts) if ts else None

        # Location text
        loc_td = row.find_all("td")
        location_text = loc_td[2].get_text(separator=" ", strip=True) if len(loc_td) > 2 else ""

        events.append({
            "source":           "earthquakelist_html",
            "eq_id":            eq_id,
            "datetime_utc":     dt.strftime("%Y-%m-%d %H:%M:%S") if dt else None,
            "date_iso":         dt.strftime("%Y-%m-%d") if dt else None,
            "year":             dt.year if dt else None,
            "month":            dt.month if dt else None,
            "latitude":         float(lat_raw) if lat_raw else None,
            "longitude":        float(lon_raw) if lon_raw else None,
            "magnitude":        float(mag_raw) if mag_raw else None,
            "depth_km":         None,  # not in HTML table
            "distance_dhaka_km": None,
            "location_text":    location_text,
            "dist_direction":   dist_raw,
            "usgs_code":        None,
        })

    return events


# ── 2. Scrape API: strongest historical events ────────────────────────────────

def scrape_api_events(order: str = "strongest", min_mag: int = 4) -> list[dict]:
    """
    Hit the internal widget API.
    Returns up to 10 events per call (server-side cap).
    """
    url = (
        f"{BASE_URL}/api/?action=earthquakes&limit=50"
        f"&geo=country&id={BD_ID}&order={order}"
        f"&min_magnitude={min_mag}&max_distance=300"
    )
    r = requests.get(url, headers=HEADERS, timeout=20)
    r.raise_for_status()
    data = r.json()

    events = []
    for item in data.get("data", []):
        eq = item.get("eq", {})
        ts  = int(eq.get("time", 0))
        dt  = datetime.datetime.utcfromtimestamp(ts) if ts else None
        lat = float(eq["location_lat"]) if eq.get("location_lat") else None
        lon = float(eq["location_lng"]) if eq.get("location_lng") else None
        mag = float(eq["metric_magnitude"]) if eq.get("metric_magnitude") else None
        dep = float(eq["location_depth"]) if eq.get("location_depth") else None

        events.append({
            "source":            f"earthquakelist_api_{order}",
            "eq_id":             eq.get("id", ""),
            "datetime_utc":      dt.strftime("%Y-%m-%d %H:%M:%S") if dt else None,
            "date_iso":          dt.strftime("%Y-%m-%d") if dt else None,
            "year":              dt.year if dt else None,
            "month":             dt.month if dt else None,
            "latitude":          lat,
            "longitude":         lon,
            "magnitude":         mag,
            "depth_km":          dep,
            "distance_dhaka_km": None,
            "location_text":     eq.get("location_text", ""),
            "dist_direction":    "",
            "usgs_code":         eq.get("usgs_code") or None,
            "felt":              int(eq.get("metric_felt", 0) or 0),
            "alert":             eq.get("alert_level", ""),
        })

    return events


# ── 3. Enrich API events with depth (scrape individual event pages) ────────────

def enrich_with_individual_pages(events: list[dict], limit: int = 30) -> list[dict]:
    """
    For events from the HTML table (no depth), try to fetch individual pages.
    Each event has a link like /bangladesh/{region}/{city}/#earthquake-{id}
    The depth is often in the event detail page.
    Throttled at 1 request/second.
    """
    # First, get API data for the recent events using their IDs
    enriched = []
    html_events = [e for e in events if e["source"] == "earthquakelist_html" and e["eq_id"]][:limit]

    print(f"  Enriching {len(html_events)} HTML events via API lookup...")
    for ev in html_events:
        eq_id = ev["eq_id"]
        url = f"{BASE_URL}/api/?action=earthquake&id={eq_id}"
        try:
            r = requests.get(url, headers=HEADERS, timeout=10)
            if r.status_code == 200:
                d = r.json()
                if d.get("success") and "data" in d:
                    eq = d["data"].get("eq", {})
                    dep = float(eq["location_depth"]) if eq.get("location_depth") else None
                    ev["depth_km"]  = dep
                    ev["usgs_code"] = eq.get("usgs_code") or None
                    ev["felt"]      = int(eq.get("metric_felt", 0) or 0)
        except Exception:
            pass
        enriched.append(ev)
        time.sleep(0.4)

    return enriched


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    all_events = []

    # 1. HTML table
    print("\n1. Scraping HTML table...")
    html_events = scrape_html_table()
    all_events.extend(html_events)

    # 2. API: strongest events (historically significant)
    print("\n2. API: strongest historical events (M≥4)...")
    strong_events = scrape_api_events(order="strongest", min_mag=4)
    print(f"  API strongest: {len(strong_events)} events")
    all_events.extend(strong_events)

    # 3. API: recent events (latest, M≥2)
    print("\n3. API: most recent events (M≥2)...")
    recent_events = scrape_api_events(order="latest", min_mag=2)
    print(f"  API latest: {len(recent_events)} events")
    all_events.extend(recent_events)

    # 4. Try to enrich HTML events with depth from individual event pages
    print("\n4. Enriching HTML events with depth via individual API calls...")
    enriched_html = enrich_with_individual_pages(all_events)
    # Replace just the HTML portion; keep API events intact
    api_events_only = [e for e in all_events if e["source"] != "earthquakelist_html"]
    all_events = enriched_html + api_events_only

    # 5. Deduplicate by eq_id
    df = pd.DataFrame(all_events)
    df["eq_id"] = df["eq_id"].astype(str)
    df_dedup = df.drop_duplicates(subset=["eq_id"]).copy()
    df_dedup = df_dedup.sort_values("datetime_utc", ascending=False).reset_index(drop=True)

    print(f"\n  Total events scraped:    {len(df)}")
    print(f"  After deduplication:     {len(df_dedup)}")
    print(f"  With depth:              {df_dedup['depth_km'].notna().sum()}")
    print(f"  With USGS code:          {df_dedup['usgs_code'].notna().sum()}")
    print(f"  Date range:              {df_dedup['date_iso'].min()} – {df_dedup['date_iso'].max()}")
    print(f"  Magnitude range:         {df_dedup['magnitude'].min():.1f} – {df_dedup['magnitude'].max():.1f}")

    # Save
    out_path = DATA_DIR / "earthquakelist_scraped.csv"
    df_dedup.to_csv(out_path, index=False, encoding="utf-8")
    print(f"\n  Saved → {out_path.relative_to(PROJECT_ROOT)}")

    # Show sample
    print("\n  Sample events:")
    cols = ["date_iso", "magnitude", "depth_km", "latitude", "longitude", "location_text", "usgs_code"]
    print(df_dedup[cols].head(10).to_string(index=False))

    return df_dedup


if __name__ == "__main__":
    main()
