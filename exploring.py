import os
import requests
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()
key = os.environ["AT_API_KEY"]
now = datetime.now()

stop_id = "7394-7baa4c89"
url = f"https://api.at.govt.nz/gtfs/v3/stops/{stop_id}/stoptrips"

params = {
    "filter[date]": now.strftime("%Y-%m-%d"),
    "filter[start_hour]": now.hour
}

headers = {"Ocp-Apim-Subscription-Key": key}

r = requests.get(url, params=params, headers=headers)
for item in r.json()["data"]:
    a = item["attributes"]
    dep = datetime.strptime(a["departure_time"], "%H:%M:%S").time()
    if dep >= now.time():
        print(a["departure_time"], a["stop_headsign"], a["route_id"])