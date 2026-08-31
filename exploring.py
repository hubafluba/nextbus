import os
import requests
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()
key = os.environ["AT_API_KEY"]

def get_departures(stop_id, limit=3):
    now = datetime.now()

    url = f"https://api.at.govt.nz/gtfs/v3/stops/{stop_id}/stoptrips"
    params = {
        "filter[date]": now.strftime("%Y-%m-%d"),
        "filter[start_hour]": now.hour
    }
    headers = {"Ocp-Apim-Subscription-Key": key}
    r = requests.get(url, params=params, headers=headers)

    upcoming = []
    for item in r.json()["data"]:
        attributes = item["attributes"]
        dep = datetime.strptime(attributes["departure_time"], "%H:%M:%S").time()
        if dep >= now.time():
            upcoming.append(attributes)

    route_ids = {a["route_id"] for a in upcoming[:limit]}
    names = {}
    for rid in route_ids:
        r2 = requests.get(f"https://api.at.govt.nz/gtfs/v3/routes/{rid}", headers=headers)
        names[rid] = r2.json()["data"]["attributes"]["route_short_name"]

    results = []
    for attributes in upcoming[:limit]:
        dep = datetime.strptime(attributes["departure_time"], "%H:%M:%S").time()
        dep_dt = datetime.combine(now.date(), dep)
        mins = int((dep_dt - now).total_seconds() // 60)
        results.append({
            "route": names[attributes["route_id"]],
            "minutes": mins,
            "destination": attributes["stop_headsign"],
        })
    return results

if __name__ == "__main__":
    for d in get_departures("7394-7baa4c89", 3):
        print(f"{d['route']}  {d['minutes']} minutes away")