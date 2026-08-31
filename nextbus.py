"""Show upcoming bus departures for an Auckland stop using the AT API."""
import os
import requests
from dotenv import load_dotenv
from datetime import datetime
import argparse

load_dotenv()
key = os.environ["AT_API_KEY"]

def get_departures(stop_id, limit=3):
    """Return upcoming departures for a stop

    Args: 
    stop_id: AT stop ID, e.g "7394-7baa4c89"
    limit: Max numbers of departures to return

    Returns:
    A list of dicts, each with keys: route, minutes, destination.
    Empty if no departures found.
    """

    now = datetime.now()

    url = f"https://api.at.govt.nz/gtfs/v3/stops/{stop_id}/stoptrips"
    params = {
        "filter[date]": now.strftime("%Y-%m-%d"),
        "filter[start_hour]": now.hour,
        "filter[hour_range]": 4
    }
    headers = {"Ocp-Apim-Subscription-Key": key}
    r = requests.get(url, params=params, headers=headers)

    # Finds the attributes of the upcoming departures and stores them, filtering out any that have already departed
    upcoming = []
    for item in r.json()["data"]:
        attributes = item["attributes"]
        dep = datetime.strptime(attributes["departure_time"], "%H:%M:%S").time()
        if dep >= now.time():
            upcoming.append(attributes)


    # creates a set of route_ids from the upcoming departures, and then gets the route name for each route_id
    route_ids = {a["route_id"] for a in upcoming[:limit]}
    names = {}
    for rid in route_ids:
        # separate call to API as the stoptrips call does not return the route name
        r2 = requests.get(f"https://api.at.govt.nz/gtfs/v3/routes/{rid}", headers=headers)
        names[rid] = r2.json()["data"]["attributes"]["route_short_name"]

    results = []

    for departure in upcoming[:limit]:
        dep = datetime.strptime(departure["departure_time"], "%H:%M:%S").time()
        dep_dt = datetime.combine(now.date(), dep)
        mins = int((dep_dt - now).total_seconds() // 60)
        results.append({
            "route": names[departure["route_id"]],
            "minutes": mins,
            "destination": departure["stop_headsign"],
        })
    return results

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Show next bus departures for an Auckland stop")
    parser.add_argument("stop_id", help="Stop ID")
    parser.add_argument("-n", type=int, default=3, help="Number of departures")
    args = parser.parse_args()
    departures = get_departures(args.stop_id, args.n)
    if not departures:
        print("No upcoming departures found.")
    for d in departures:
        print(f"{d['route']}  {d['minutes']} minutes away")