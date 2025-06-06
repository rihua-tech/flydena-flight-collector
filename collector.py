
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


# 🌍 10 global hot cities (balanced by region)


HOT_CITIES = [
    'NYC',   # New York City
    'LHR',   # London Heathrow
    'DXB',   # Dubai
    'TYO',   # Tokyo (Narita or Haneda)
    'SIN',   # Singapore
    'CDG',   # Paris Charles de Gaulle
    'LAX',   # Los Angeles
    'HND',   # Tokyo Haneda
    'SYD',   # Sydney
    'MIA'    # Miami
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
        import shutil  # ✅ move this to top if you prefer
        gh_token = os.getenv("GH_TOKEN")
        gh_repo = os.getenv("GH_REPO")
        repo_url = f"https://x-access-token:{gh_token}@github.com/{gh_repo}.git"

        # Create temp folder
        folder = "temp_flight_data"
        os.makedirs(folder, exist_ok=True)
        dst = os.path.join(folder, CSV_FILE)

        # Copy today's CSV file into the folder
        shutil.copyfile(CSV_FILE, dst)

        # 🧹 Clean up old git data if present
        git_folder = os.path.join(folder, ".git")
        if os.path.exists(git_folder):
            shutil.rmtree(git_folder)

        # ✅ Init git and push
        subprocess.run(["git", "init"], cwd=folder, check=True)
        subprocess.run(["git", "remote", "add", "origin", repo_url], cwd=folder, check=True)
        subprocess.run(["git", "config", "user.email", "action@github.com"], cwd=folder, check=True)
        subprocess.run(["git", "config", "user.name", "Flight Bot"], cwd=folder, check=True)
        subprocess.run(["git", "add", CSV_FILE], cwd=folder, check=True)
        subprocess.run(["git", "commit", "-m", f"✅ Flight price snapshot {today}"], cwd=folder, check=True)
        subprocess.run(["git", "branch", "-M", "main"], cwd=folder, check=True)
        subprocess.run(["git", "push", "-u", "origin", "main", "--force"], cwd=folder, check=True)

        print("✅ CSV pushed to flight-price-data repo.")
    except Exception as e:
        print("❌ GitHub push failed:", e)
        
if __name__ == "__main__":
    collect_flight_data()
    push_to_github()
