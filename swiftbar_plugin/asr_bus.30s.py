#!/usr/bin/python3
# <swiftbar.hideAbout>true</swiftbar.hideAbout>
# <swiftbar.hideRunInTerminal>true</swiftbar.hideRunInTerminal>
# <swiftbar.hideDisablePlugin>true</swiftbar.hideDisablePlugin>

"""ASR Bus SwiftBar plugin - shows next bus in menu bar, full schedule in dropdown."""

import json
import math
import os
import subprocess
import time
import urllib.request
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

SG_TZ = ZoneInfo("Asia/Singapore")

# Menu bar item only visible during this window (SGT hours, 24h format)
VISIBLE_START = 16
VISIBLE_END = 19

STOPS = {
    "asr": {"name": "ASR", "emoji": "🏠", "offset": 0, "lat": 1.276626, "lon": 103.830288},
    "outram6": {
        "name": "Outram Exit 6",
        "emoji": "🚇",
        "offset": 6,
        "lat": 1.278987,
        "lon": 103.838569,
    },
    "outram7": {
        "name": "Outram Exit 7",
        "emoji": "🚇",
        "offset": 8,
        "lat": 1.280981,
        "lon": 103.838783,
    },
    "harbourfront": {
        "name": "Harbourfront",
        "emoji": "🛍️",
        "offset": 10,
        "lat": 1.265884,
        "lon": 103.821495,
    },
}

PLUGIN_DIR = Path(__file__).parent
PROJECT_DIR = PLUGIN_DIR.parent

TRIP_STOPS = {
    "A": ["asr", "outram6", "outram7"],
    "B": ["asr", "harbourfront"],
}

DESTINATIONS = {"A": "🚇 Outram Park", "B": "🛍️ Harbourfront"}

WEEKDAY_TRIPS = [
    ("07:20", "A"),
    ("07:40", "A"),
    ("08:00", "A"),
    ("08:20", "A"),
    ("08:40", "A"),
    ("09:00", "A"),
    ("09:30", "A"),
    ("10:00", "B"),
    ("10:30", "A"),
    ("11:00", "B"),
    ("11:30", "A"),
    ("13:00", "B"),
    ("13:30", "A"),
    ("14:00", "B"),
    ("14:30", "A"),
    ("15:00", "B"),
    ("16:30", "A"),
    ("17:00", "B"),
    ("17:30", "A"),
    ("18:00", "B"),
    ("18:30", "A"),
    ("19:00", "B"),
    ("19:30", "A"),
    ("20:00", "B"),
]

SATURDAY_TRIPS = [
    ("09:00", "A"),
    ("09:30", "B"),
    ("10:00", "A"),
    ("10:30", "B"),
    ("11:00", "A"),
    ("11:30", "B"),
    ("12:00", "A"),
    ("12:30", "B"),
    ("14:00", "A"),
    ("14:30", "B"),
    ("15:00", "A"),
    ("15:30", "B"),
    ("16:00", "A"),
    ("16:30", "B"),
    ("18:00", "A"),
    ("18:30", "B"),
    ("19:00", "A"),
    ("19:30", "B"),
    ("20:00", "A"),
    ("20:30", "B"),
]

HOLIDAYS_URL = "https://raw.githubusercontent.com/sfdye/asr_bus/master/ios_widget/holidays.json"
CACHE_PATH = Path.home() / ".cache" / "asr_bus_holidays.json"


HOLIDAYS_TTL = 86400  # re-fetch once per day


def load_holidays():
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    if CACHE_PATH.exists():
        age = time.time() - os.path.getmtime(str(CACHE_PATH))
        if age < HOLIDAYS_TTL:
            try:
                return json.loads(CACHE_PATH.read_text())
            except Exception:
                pass
    try:
        req = urllib.request.Request(HOLIDAYS_URL, headers={"User-Agent": "SwiftBar"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read())
        CACHE_PATH.write_text(json.dumps(data))
        return data
    except Exception:
        pass
    try:
        if CACHE_PATH.exists():
            return json.loads(CACHE_PATH.read_text())
    except Exception:
        pass
    return None


def is_holiday(date, holidays_data):
    if not holidays_data:
        return False
    year = str(date.year)
    date_str = date.strftime("%Y-%m-%d")
    return date_str in holidays_data.get(year, [])


def get_day_type(now, holidays_data):
    day = now.weekday()
    if day == 6:
        return "sunday"
    if day == 5 or is_holiday(now, holidays_data):
        return "saturday"
    return "weekday"


def get_trips(day_type):
    if day_type == "weekday":
        return WEEKDAY_TRIPS
    if day_type == "saturday":
        return SATURDAY_TRIPS
    return None


def time_to_minutes(time_str):
    h, m = map(int, time_str.split(":"))
    return h * 60 + m


def minutes_to_time(mins):
    return f"{mins // 60:02d}:{mins % 60:02d}"


def get_next_buses(stop_key, now, holidays_data):
    day_type = get_day_type(now, holidays_data)
    trips = get_trips(day_type)
    if not trips:
        return {"no_service": True}

    offset = STOPS[stop_key]["offset"]
    now_mins = now.hour * 60 + now.minute
    results = []

    for asr_time, trip_type in trips:
        if stop_key not in TRIP_STOPS[trip_type]:
            continue
        arrival_mins = time_to_minutes(asr_time) + offset
        if arrival_mins >= now_mins:
            results.append(
                {
                    "time": minutes_to_time(arrival_mins),
                    "mins": arrival_mins - now_mins,
                    "dest": DESTINATIONS[trip_type],
                    "type": trip_type,
                }
            )
        if len(results) >= 3:
            break

    if not results:
        return {"no_more_bus": True}
    return {"buses": results}


def haversine(lat1, lon1, lat2, lon2):
    R = 6371000
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    )
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def nearest_stop(lat, lon):
    return min(STOPS, key=lambda k: haversine(lat, lon, STOPS[k]["lat"], STOPS[k]["lon"]))


LOCATION_HELPER = (
    PROJECT_DIR
    / "location_helper"
    / "LocationHelper.app"
    / "Contents"
    / "MacOS"
    / "location_helper"
)
LOCATION_FILE = Path("/tmp/asr_bus_location.txt")
LOCATION_TTL = 300  # reuse cached location for 5 minutes


def get_current_location():
    if not LOCATION_HELPER.exists():
        return None
    if LOCATION_FILE.exists():
        age = time.time() - os.path.getmtime(str(LOCATION_FILE))
        if age < LOCATION_TTL:
            try:
                parts = LOCATION_FILE.read_text().strip().split(",")
                return float(parts[0]), float(parts[1])
            except Exception:
                pass
    try:
        subprocess.run([str(LOCATION_HELPER)], capture_output=True, timeout=12)
        if LOCATION_FILE.exists():
            parts = LOCATION_FILE.read_text().strip().split(",")
            return float(parts[0]), float(parts[1])
    except Exception:
        pass
    return None


def resolve_stop():
    loc = get_current_location()
    if loc:
        return nearest_stop(loc[0], loc[1])
    return "asr"


def main():
    now = datetime.now(SG_TZ)
    if not (VISIBLE_START <= now.hour < VISIBLE_END):
        return

    holidays_data = load_holidays()
    stop_key = resolve_stop()
    result = get_next_buses(stop_key, now, holidays_data)

    # Menu bar title
    if result.get("no_service"):
        print("🚌 No Sun service")
    elif result.get("no_more_bus"):
        print("🚌 Done")
    else:
        bus = result["buses"][0]
        if bus["mins"] <= 60:
            print(f"🚌 {bus['mins']}min")
        else:
            hrs = bus["mins"] / 60
            print(f"🚌 ~{hrs:.1f}h")

    # Dropdown
    print("---")
    stop = STOPS[stop_key]
    print(f"{stop['emoji']} {stop['name']} — {now.strftime('%H:%M')} SGT | size=14")
    print("---")

    if result.get("no_service"):
        print("No service on Sundays")
    elif result.get("no_more_bus"):
        print("No more buses today")
    else:
        from_label = f"{stop['emoji']} {stop['name']}"
        for i, bus in enumerate(result["buses"]):
            label = "Next" if i == 0 else "Then"
            dest = bus["dest"] if stop_key == "asr" else "🏠 ASR"
            if bus["mins"] <= 60:
                wait = f"{bus['mins']} min"
            else:
                wait = f"~{bus['mins'] / 60:.1f}h"
            print(f"{label}: {bus['time']} ({wait}) {from_label} → {dest} | size=13")

    print("---")

    # Full schedule section
    day_type = get_day_type(now, holidays_data)
    trips = get_trips(day_type)
    if trips:
        day_label = "Saturday" if day_type == "saturday" else "Weekday"
        print(f"📋 {day_label} Schedule | size=12")

        offset = STOPS[stop_key]["offset"]
        now_mins = now.hour * 60 + now.minute
        next_mins = result.get("buses", [{}])[0].get("mins", -1)
        from_label = f"{stop['emoji']} {stop['name']}"
        for asr_time, trip_type in trips:
            if stop_key not in TRIP_STOPS[trip_type]:
                continue
            arrival_mins = time_to_minutes(asr_time) + offset
            dest_label = DESTINATIONS[trip_type] if stop_key == "asr" else "🏠 ASR"
            is_next = arrival_mins >= now_mins and arrival_mins - now_mins == next_mins
            marker = " ◀" if is_next else ""
            t = minutes_to_time(arrival_mins)
            print(f"--{t}  {from_label} → {dest_label}{marker} | font=Menlo size=12")

    print("---")
    print("Refresh | refresh=true")


if __name__ == "__main__":
    main()
