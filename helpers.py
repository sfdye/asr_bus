import datetime

from config import (
    SG_HOLIDAYS,
    SG_TZ,
    STOP_OFFSETS,
    TRIP_DESTINATIONS,
    TRIP_TYPE_STOPS,
    saturday_trips,
    weekday_trips,
)


def get_singapore_now():
    return datetime.datetime.now(SG_TZ)


def get_day_type():
    now = get_singapore_now()
    weekday = now.weekday()
    if weekday == 6:
        return "sunday"
    if weekday == 5 or now.date() in SG_HOLIDAYS:
        return "saturday"
    return "weekday"


def get_trips_for_day_type(day_type):
    if day_type == "weekday":
        return weekday_trips
    if day_type == "saturday":
        return saturday_trips
    return None


def add_minutes(time_str, minutes):
    t = datetime.datetime.strptime(time_str, "%H:%M")
    t += datetime.timedelta(minutes=minutes)
    return t.strftime("%H:%M")


def get_stop_schedule(trips, stop_key):
    results = []
    for asr_time, trip_type in trips:
        if stop_key in TRIP_TYPE_STOPS[trip_type]:
            arrival = add_minutes(asr_time, STOP_OFFSETS[stop_key])
            results.append((arrival, trip_type))
    return results


def minutes_until(current_time, target_time):
    return (
        datetime.datetime.combine(datetime.date.today(), target_time)
        - datetime.datetime.combine(datetime.date.today(), current_time)
    ).seconds // 60


def format_bus_msg(label, minutes, time_str, stop_key, trip_type):
    if stop_key == "asr":
        return (
            f"🚌 {label} in <b>{minutes} min</b> ({time_str})\n"
            f"➡️ Going to <b>{TRIP_DESTINATIONS[trip_type]}</b>"
        )
    return f"🚌 {label} in <b>{minutes} min</b> ({time_str})"


def format_asr_schedule(trips, breaks, last_dropoff):
    lines = []
    for asr_time, trip_type in trips:
        lines.append(f"{asr_time}  → {TRIP_DESTINATIONS[trip_type]}")
        if asr_time in breaks:
            lines.append(f"<i>—— {breaks[asr_time]} ——</i>")
    lines.append(f"\n<i>Last drop-off: {last_dropoff}</i>")
    return "\n".join(lines)


def format_stop_schedule(trips, stop_key, breaks):
    lines = []
    has_times = False
    for asr_time, trip_type in trips:
        if stop_key in TRIP_TYPE_STOPS[trip_type]:
            lines.append(add_minutes(asr_time, STOP_OFFSETS[stop_key]))
            has_times = True
        if asr_time in breaks and has_times:
            lines.append(f"<i>—— {breaks[asr_time]} ——</i>")
    while lines and lines[-1].startswith("<i>"):
        lines.pop()
    return "\n".join(lines)
