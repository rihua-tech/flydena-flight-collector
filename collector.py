
import os
import csv
import time
import stat
import shutil
import requests
import subprocess
from datetime import datetime
from dotenv import load_dotenv

# 🔐 Load token from .env
load_dotenv()
MARKER = os.getenv("MARKER")
GH_TOKEN = os.getenv("GH_TOKEN")         # ✅ GitHub Token
GH_REPO = os.getenv("GH_REPO")           # ✅ GitHub Repo path (e.g. user/repo-name)


# 🌍 Top 10 flight cities
HOT_CITIES = [
    'NYC',  # New York
    'LHR',  # London Heathrow
    'DXB',  # Dubai
    'TYO',  # Tokyo
    'SIN',  # Singapore
    'CDG',  # Paris
    'LAX',  # Los Angeles
    'HND',  # Tokyo Haneda
    'SYD',  # Sydney
    'MIA'   # Miami
]

# 🗓️ Create filename
CURRENCY = 'usd'
today = datetime.today().strftime('%Y-%m-%d')
CSV_FILE = f'flight_prices_{today}.csv'
PERIOD = datetime.today().strftime('%Y-%m')

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



import shutil
import stat

def remove_readonly(func, path, _):
    os.chmod(path, stat.S_IWRITE)
    func(path)

def push_to_github():
    try:
        gh_token = os.getenv("GH_TOKEN")
        gh_repo = os.getenv("GH_REPO")
        repo_url = f"https://x-access-token:{gh_token}@github.com/{gh_repo}.git"

        folder = "temp_flight_data"

        # 🧹 Clean up old folder completely and safely
        if os.path.exists(folder):
            shutil.rmtree(folder, onerror=remove_readonly)

        # ✅ Clone the repo
        subprocess.run(["git", "clone", repo_url, folder], check=True)

        # 📄 Copy the new file into the repo
        dst = os.path.join(folder, CSV_FILE)
        shutil.copyfile(CSV_FILE, dst)

        # ✅ Add, commit, and push
        subprocess.run(["git", "add", CSV_FILE], cwd=folder, check=True)
        subprocess.run(["git", "commit", "-m", f"✅ Add snapshot {today}"], cwd=folder, check=True)
        subprocess.run(["git", "push"], cwd=folder, check=True)

        print("✅ CSV pushed and previous files kept.")

    except Exception as e:
        print("❌ GitHub push failed:", e)


# ▶️ Run both steps
if __name__ == "__main__":
    collect_flight_data()
    push_to_github()
