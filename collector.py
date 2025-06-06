
import os
import requests
import csv
from datetime import datetime
from dotenv import load_dotenv
import time
import subprocess

# 🔐 Load token from .env
load_dotenv()
MARKER = os.getenv("MARKER")
GH_TOKEN = os.getenv("GH_TOKEN")         # ✅ Load GitHub Token
GH_REPO = os.getenv("GH_REPO")           # ✅ Load GitHub Repo path


# 🌍 50 global hot cities (balanced by region)
HOT_CITIES = [
    'NYC', 'LAX', 'SFO', 'MIA', 'LAS', 'SEA', 'BOS', 'ORD', 'ATL', 'DFW', 'YVR', 'YYZ',
    'LHR', 'CDG', 'AMS', 'FRA', 'BCN', 'MAD', 'ROM', 'ATH', 'DUB', 'CPH', 'ZRH', 'PRG',
    'DXB', 'DEL', 'BOM', 'SIN', 'ICN', 'TYO', 'HKG', 'BKK', 'MNL', 'KUL', 'DOH', 'TPE',
    'MEX', 'CUN', 'GRU', 'EZE', 'SCL', 'BOG', 'CAI', 'JNB', 'CMN', 'SYD', 'AKL', 'TLV', 'IST', 'SAW'
]

# 🗓️ Date-based filename
CURRENCY = 'usd'
today = datetime.today().strftime('%Y-%m-%d')
CSV_FILE = f'flight_prices_{today}.csv'
PERIOD = datetime.today().strftime('%Y-%m')  # e.g., "2025-06"

def collect_flight_data():
    with open(CSV_FILE, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(['From', 'To', 'Depart_Date', 'Price'])

        for origin in HOT_CITIES:
            for destination in HOT_CITIES:
                if origin == destination:
                    continue
                print(f'📡 Querying {origin} → {destination}')
                url = (
                    f'https://api.travelpayouts.com/aviasales/v3/get_latest_prices'
                    f'?currency={CURRENCY}&origin={origin}&destination={destination}'
                    f'&beginning_of_period={PERIOD}&period_type=month&one_way=true'
                    f'&market=us&token={MARKER}'
                )

                try:
                    response = requests.get(url, timeout=10)
                    result = response.json()

                    if result.get('success') and result.get('data'):
                        for item in result['data']:
                            writer.writerow([
                                item.get('origin', origin),
                                item.get('destination', destination),
                                item.get('depart_date'),
                                item.get('value')
                            ])
                            print(f'✅ {origin} → {destination} on {item["depart_date"]} = ${item["value"]}')
                    else:
                        print(f'⚠️ No price for {origin} → {destination}')

                    time.sleep(0.7)

                except Exception as e:
                    print(f'❌ Error for {origin} → {destination}:', e)

def push_to_github():
    try:
        subprocess.run(['git', 'add', CSV_FILE], check=True)
        subprocess.run(['git', 'commit', '-m', f'🛫 Daily snapshot for {today}'], check=True)
        subprocess.run(['git', 'push'], check=True)
        print('✅ Pushed to GitHub.')
    except Exception as e:
        print('❌ Git push failed:', e)

if __name__ == "__main__":
    collect_flight_data()
    push_to_github()
