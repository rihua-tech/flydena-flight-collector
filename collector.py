#!/usr/bin/env python3
import os
import csv
import shutil
import requests
from datetime import date, datetime, timedelta
from dotenv import load_dotenv

# ── LOAD ENV ─────────────────────────────────────────────────────────────────────
# Local testing: load from .env if present
load_dotenv()

# Expect the Travelpayouts API key in this var
API_TOKEN = os.getenv("TRAVELPAYOUTS_API_KEY")
# GH_TOKEN and GH_REPO are no longer needed inside script if workflow commits in-place,
# but you can still read them if you had logic requiring them.
# GH_TOKEN = os.getenv("GH_TOKEN")
# GH_REPO  = os.getenv("GH_REPO")

CLONE_DIR  = "temp_flight_data"  # directory under repo to store CSVs
CURRENCY   = "usd"
MARKET     = "us"
DAYS_AHEAD = 100

# Safety check: Ensure critical env variable is loaded
if not API_TOKEN:
    raise ValueError("❌ Missing required environment variable: TRAVELPAYOUTS_API_KEY")

# ── HOT CITIES ───────────────────────────────────────────────────────────────────
HOT_CITIES = [
    "NYC", "LHR", "DXB", "TYO", "SIN",
    "CDG", "LAX", "HND", "SYD", "MIA",
]

# ── STEP 1: COLLECT ──────────────────────────────────────────────────────────────
def collect_flight_data(days_ahead=DAYS_AHEAD):
    today       = date.today()
    search_date = today.isoformat()
    cutoff      = today + timedelta(days=days_ahead)
    csvname     = f"flight_prices_{search_date}.csv"

    with open(csvname, "w", newline="", encoding="utf-8") as fp:
        writer = csv.writer(fp)
        writer.writerow(["origin", "destination", "search_date", "depart_date", "price"])

        for origin in HOT_CITIES:
            for dest in HOT_CITIES:
                if origin == dest:
                    continue

                print(f"📡 {origin} → {dest}")
                url = (
                    "https://api.travelpayouts.com/aviasales/v3/get_latest_prices"
                    f"?origin={origin}&destination={dest}"
                    f"&currency={CURRENCY}&market={MARKET}"
                    f"&token={API_TOKEN}"
                    "&period_type=year"
                )

                try:
                    resp = requests.get(url, timeout=10)
                    resp.raise_for_status()
                    data = resp.json()
                    if data.get("success") and data.get("data"):
                        for item in data["data"]:
                            # Parse depart_date: ensure ISO format without timezone issues
                            depart_str = item.get("depart_date")
                            try:
                                # If endswith 'Z', fromisoformat needs adjustment
                                if depart_str.endswith("Z"):
                                    # convert 'YYYY-MM-DDTHH:MM:SSZ' → 'YYYY-MM-DDTHH:MM:SS+00:00'
                                    depart_str_adj = depart_str[:-1] + "+00:00"
                                    dep_dt = datetime.fromisoformat(depart_str_adj)
                                else:
                                    dep_dt = datetime.fromisoformat(depart_str)
                                dep = dep_dt.date()
                            except Exception as e:
                                print(f"⚠️ Skipping unparsable date '{depart_str}': {e}")
                                continue

                            if dep <= cutoff:
                                writer.writerow([
                                    origin,
                                    dest,
                                    search_date,
                                    dep.isoformat(),
                                    item.get("value", "")
                                ])
                    else:
                        print("⚠️ No data returned or success=False.")
                except Exception as e:
                    print(f"❌ Error fetching {origin}→{dest}: {e}")

    return csvname

# ── MAIN ─────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    # Ensure output directory exists
    os.makedirs(CLONE_DIR, exist_ok=True)

    # Collect data and get the CSV filename (in current dir)
    csvfile = collect_flight_data()

    # Move CSV into temp_flight_data/
    src = csvfile
    dst = os.path.join(CLONE_DIR, csvfile)
    try:
        # If a file with same name already exists, overwrite it:
        if os.path.exists(dst):
            os.remove(dst)
        shutil.move(src, dst)
        print(f"✅ Saved CSV to {dst}")
    except Exception as e:
        print(f"❌ Failed to move {src} to {dst}: {e}")
        # Optionally: leave the CSV in root if move fails
