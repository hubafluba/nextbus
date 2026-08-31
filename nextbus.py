"""Show upcoming bus departures for an Auckland stop using the AT API."""
import os
import requests
from dotenv import load_dotenv
from datetime import datetime
import argparse

load_dotenv()
key = os.environ["AT_API_KEY"]
headers = {"Ocp-Apim-Subscription-Key": key}

def resolve_stop_id(stop_code):
    """Turn a stop code from the sign into the API's stop ID."""
    url = "https://api.at.govt.nz/gtfs/v3/stops"
    params = {"filter[stop_code]": stop_code}
    r = requests.get(url, params=params, headers=headers)

    stops = r.json()["data"]
    if not stops:
        raise ValueError(f"No stop found with code {stop_code}")

    return stops[0]["id"]

def get_departures(stop_code, limit=3):
    """Return upcoming departures for a stop

    Args: 
    stop_code: AT stop code, e.g "7394"
    limit: Max numbers of departures to return

    Returns:
    A list of dicts, each with keys: route, minutes, destination.
    Empty if no departures found.
    """

    now = datetime.now()

    stop_id = resolve_stop_id(stop_code)

    url = f"https://api.at.govt.nz/gtfs/v3/stops/{stop_id}/stoptrips"
    params = {
        "filter[date]": now.strftime("%Y-%m-%d"),
        "filter[start_hour]": now.hour,
        "filter[hour_range]": 3
    }
    r = requests.get(url, params=params, headers=headers)
    if r.status_code == 404:
        return []
    r.raise_for_status()
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
    parser.add_argument("stop_code", help="Stop number from the sign, e.g. 7394")
    parser.add_argument("limit", nargs = "?", type=int, default=3, help="Number of departures")
    args = parser.parse_args()

    departures = get_departures(args.stop_code, args.limit)
    if not departures:
        print("No upcoming departures found.")
    for d in departures:
        print(f"{d['route']}  {d['minutes']} minutes away")
