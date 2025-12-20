import csv
from datetime import date, timedelta
import random
import requests

# -----------------------------
# REAL SITES (Tunisia) – good enough accuracy for weather APIs
# -----------------------------
SITES = [
    {"name": "Oued Meliane (Tunis)", "lat": 36.739, "lon": 10.273, "runoff_factor": 0.8, "land_risk": 0.7, "plastic_score": 0.85, "ndvi": 0.22},
    {"name": "Oued Medjerda (Jendouba/Beja)", "lat": 36.497, "lon": 9.879, "runoff_factor": 0.7, "land_risk": 0.4, "plastic_score": 0.60, "ndvi": 0.28},
    {"name": "Nabeul Coast", "lat": 36.456, "lon": 10.737, "runoff_factor": 0.6, "land_risk": 0.5, "plastic_score": 0.55, "ndvi": 0.25},
    {"name": "Sfax Coast", "lat": 34.740, "lon": 10.760, "runoff_factor": 0.5, "land_risk": 0.8, "plastic_score": 0.70, "ndvi": 0.18},
    {"name": "Gabes Coast", "lat": 33.881, "lon": 10.098, "runoff_factor": 0.4, "land_risk": 0.7, "plastic_score": 0.50, "ndvi": 0.20},
]

# -----------------------------
# REAL EVENT LABELS (Tunisia flood activation)
# Copernicus EMS Rapid Mapping: EMSR319 (Flood in northern Tunisia)
# We'll label a short window around the activation day as event=1.
# -----------------------------
EVENT_WINDOWS = [
    # 2018-09-29 activation day (and surrounding 1–2 days)
    (date(2018, 9, 28), date(2018, 10, 1)),
]

# How many negative (non-event) days per site to sample
NEGATIVE_DAYS_PER_SITE = 40

OUT_PATH = "data/train_water_risk.csv"

def is_event_day(d: date) -> bool:
    for start, end in EVENT_WINDOWS:
        if start <= d <= end:
            return True
    return False

def open_meteo_daily(lat: float, lon: float, start: date, end: date):
    """
    Uses Open-Meteo Historical Weather API (/v1/archive) to get daily precipitation sum and max temp.
    """
    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": start.isoformat(),
        "end_date": end.isoformat(),
        "daily": "precipitation_sum,temperature_2m_max",
        "timezone": "Africa/Tunis",
    }
    r = requests.get(url, params=params, timeout=30)
    r.raise_for_status()
    return r.json()

def build_rows_for_site(site):
    rows = []

    # 1) Positive samples: all event-window days
    for start, end in EVENT_WINDOWS:
        js = open_meteo_daily(site["lat"], site["lon"], start, end)
        dates = js["daily"]["time"]
        rain = js["daily"]["precipitation_sum"]
        tmax = js["daily"]["temperature_2m_max"]

        for i, ds in enumerate(dates):
            d = date.fromisoformat(ds)
            event = 1 if is_event_day(d) else 0
            rows.append([
                site["plastic_score"],
                float(rain[i]),
                float(tmax[i]),
                site["ndvi"],
                site["runoff_factor"],
                site["land_risk"],
                event
            ])

    # 2) Negative samples: random days in similar months (Sep–Nov) excluding event windows
    # We sample across a couple of years around 2018 to keep it "real" and seasonal.
    candidate_days = []
    for year in [2017, 2018, 2019]:
        for month in [9, 10, 11]:
            # take first 28 days safe
            for day in range(1, 29):
                d = date(year, month, day)
                if not is_event_day(d):
                    candidate_days.append(d)

    random.shuffle(candidate_days)
    picked = candidate_days[:NEGATIVE_DAYS_PER_SITE]

    # Fetch negatives in batches by month to reduce API calls
    # We'll group by (year, month)
    buckets = {}
    for d in picked:
        buckets.setdefault((d.year, d.month), []).append(d)

    for (y, m), days in buckets.items():
        start = min(days)
        end = max(days)
        js = open_meteo_daily(site["lat"], site["lon"], start, end)
        dates = js["daily"]["time"]
        rain = js["daily"]["precipitation_sum"]
        tmax = js["daily"]["temperature_2m_max"]
        lookup = {date.fromisoformat(dates[i]): (rain[i], tmax[i]) for i in range(len(dates))}

        for d in days:
            rr, tt = lookup[d]
            rows.append([
                site["plastic_score"],
                float(rr),
                float(tt),
                site["ndvi"],
                site["runoff_factor"],
                site["land_risk"],
                0
            ])

    return rows

def main():
    random.seed(42)

    header = ["plastic_score","rain_mm_24","temp_max_24","ndvi","runoff_factor","land_risk","event"]

    all_rows = []
    for site in SITES:
        all_rows.extend(build_rows_for_site(site))

    # Shuffle rows so training is not site-ordered
    random.shuffle(all_rows)

    with open(OUT_PATH, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(all_rows)

    print(f"✅ Saved real-data training file: {OUT_PATH}")
    print(f"Rows: {len(all_rows)}  |  Sites: {len(SITES)}")
    print("Tip: open the CSV to see real precipitation/temp values.")

if __name__ == "__main__":
    main()
