import datetime
import os

import pytz
from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode, Update
from telegram.ext import (CallbackContext, CallbackQueryHandler,
                          CommandHandler, Updater)

load_dotenv(override=True)

TOKEN = os.getenv("TOKEN")
SG_TZ = pytz.timezone("Asia/Singapore")

STOP_NAMES = {
    "asr": "Avenue South Residence",
    "outram_exit_6": "Outram Park MRT Exit 6",
    "outram_exit_7": "Outram Park MRT Exit 7",
    "harbourfront": "Harbourfront MRT Exit D",
}

STOP_EMOJIS = {"asr": "🏠", "outram_exit_6": "🚇", "outram_exit_7": "🚇", "harbourfront": "🛍️"}

STOP_OFFSETS = {"asr": 0, "outram_exit_6": 6, "outram_exit_7": 8, "harbourfront": 10}

TRIP_TYPE_STOPS = {
    "A": ["asr", "outram_exit_6", "outram_exit_7"],
    "B": ["asr", "harbourfront"],
}

TRIP_DESTINATIONS = {"A": "Outram Park MRT", "B": "Harbourfront MRT Exit D"}

weekday_trips = [
    ("07:20", "A"), ("07:40", "A"), ("08:00", "A"), ("08:20", "A"), ("08:40", "A"), ("09:00", "A"),
    ("09:30", "A"), ("10:00", "B"), ("10:30", "A"), ("11:00", "B"), ("11:30", "A"),
    ("13:00", "B"), ("13:30", "A"), ("14:00", "B"), ("14:30", "A"), ("15:00", "B"),
    ("16:30", "A"), ("17:00", "B"), ("17:30", "A"), ("18:00", "B"), ("18:30", "A"),
    ("19:00", "B"), ("19:30", "A"), ("20:00", "B"),
]

saturday_trips = [
    ("09:00", "A"), ("09:30", "B"), ("10:00", "A"), ("10:30", "B"), ("11:00", "A"),
    ("11:30", "B"), ("12:00", "A"), ("12:30", "B"),
    ("14:00", "A"), ("14:30", "B"), ("15:00", "A"), ("15:30", "B"), ("16:00", "A"),
    ("16:30", "B"),
    ("18:00", "A"), ("18:30", "B"), ("19:00", "A"), ("19:30", "B"), ("20:00", "A"),
    ("20:30", "B"),
]

weekday_breaks = {
    "09:00": "Driver Break",
    "11:30": "Lunch Break (12:00 - 13:00)",
    "15:00": "Driver Break & Petrol",
}

saturday_breaks = {
    "12:30": "Lunch Break (13:00 - 14:00)",
    "16:30": "Driver Break & Petrol",
}

WEEKDAY_LAST_DROPOFF = "20:15"
SATURDAY_LAST_DROPOFF = "20:45"


intro_text = """
🚌 Eh hello neighbour! I help you check ASR bus timing one.

<b>🗺️ Route:</b> ASR → Outram Park MRT / Harbourfront MRT Exit D
<b>📅 Service days:</b> Mon to Sat (Sunday no bus lah)

Try these:
/location - Next bus when ah? 🕐
/schedule - See full timetable 📋
"""

service_notice = """
⏰ Timing is estimate only ah, come 5 min early just in case!
"""

no_sunday_service = "😴 Sunday no bus lah. Service Mon to Sat only!"


def get_singapore_now():
    return datetime.datetime.now(SG_TZ)


def get_day_type():
    weekday = get_singapore_now().weekday()
    if weekday < 5:
        return "weekday"
    if weekday == 5:
        return "saturday"
    return "sunday"


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
        return (f"🚌 {label} in <b>{minutes} min</b> ({time_str})\n"
                f"➡️ Going to <b>{TRIP_DESTINATIONS[trip_type]}</b>")
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


def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text(intro_text, parse_mode=ParseMode.HTML)
    disclaimer = (
        "⚠️ Take note ah:\n"
        "• Bus timing is estimate only, traffic can affect one.\n"
        "• Come 5 to 8 min early to be safe lah.\n"
        "• Cannot bring heavy/bulky items on the bus hor.\n"
        "• Bus only stop at designated stops.\n"
        "• No waiting or holding the bus at stops!"
    )
    update.message.reply_text(disclaimer, parse_mode=ParseMode.HTML)


def schedule_inline_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(f"{STOP_EMOJIS[k]} {STOP_NAMES[k]}", callback_data=f"schedule:{k}")]
        for k in STOP_NAMES
    ])


def prompt_schedule(update: Update, context: CallbackContext) -> None:
    day_type = get_day_type()
    label = "Saturday" if day_type == "saturday" else "Weekday"

    if day_type == "sunday":
        msg = "😴 Sunday no bus lah.\n📋 Showing <b>Weekday</b> schedule.\nWhich stop you want?"
    else:
        msg = f"📋 <b>{label} Schedule</b>\nWhich stop you want to see?"
    update.message.reply_text(msg, reply_markup=schedule_inline_keyboard(),
                              parse_mode=ParseMode.HTML)


def build_schedule_text(stop_key, day_type):
    trips = get_trips_for_day_type(day_type)
    breaks = weekday_breaks if day_type == "weekday" else saturday_breaks
    last_dropoff = WEEKDAY_LAST_DROPOFF if day_type == "weekday" else SATURDAY_LAST_DROPOFF
    label = "Weekday (Mon-Fri)" if day_type == "weekday" else "Saturday"
    header = f"<b>{label} — {STOP_NAMES[stop_key]}</b>\n\n"

    if stop_key == "asr":
        body = format_asr_schedule(trips, breaks, last_dropoff)
    else:
        body = format_stop_schedule(trips, stop_key, breaks)

    return header + body + "\n" + service_notice


def handle_schedule_callback(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()

    stop_key = query.data.split(":")[1]
    if stop_key not in STOP_NAMES:
        return

    day_type = get_day_type()
    if day_type == "sunday":
        day_type = "weekday"

    text = build_schedule_text(stop_key, day_type)
    query.edit_message_text(text, parse_mode=ParseMode.HTML,
                            reply_markup=schedule_inline_keyboard())


def location_inline_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(f"{STOP_EMOJIS[k]} {STOP_NAMES[k]}", callback_data=f"location:{k}")]
        for k in STOP_NAMES
    ])


def prompt_location(update: Update, context: CallbackContext) -> None:
    if get_day_type() == "sunday":
        update.message.reply_text(no_sunday_service, parse_mode=ParseMode.HTML)
        return

    update.message.reply_text("📍 Where you at now ah?",
                              reply_markup=location_inline_keyboard(),
                              parse_mode=ParseMode.HTML)


def build_next_bus_text(stop_key, day_type):
    current_time = get_singapore_now().time()
    trips = get_trips_for_day_type(day_type)
    schedule = get_stop_schedule(trips, stop_key)

    for i, (time_str, trip_type) in enumerate(schedule):
        bus_time = datetime.datetime.strptime(time_str, "%H:%M").time()
        if current_time <= bus_time:
            mins = minutes_until(current_time, bus_time)
            lines = [format_bus_msg(
                "Next bus departs" if stop_key == "asr" else "Next bus arrives",
                mins, time_str, stop_key, trip_type)]

            if i < len(schedule) - 1:
                next_time, next_type = schedule[i + 1]
                next_bus = datetime.datetime.strptime(next_time, "%H:%M").time()
                next_mins = minutes_until(current_time, next_bus)
                lines.append(format_bus_msg("Following bus", next_mins, next_time,
                                            stop_key, next_type))
            else:
                lines.append("☝️ Last bus already, no more after this one!")

            lines.append(service_notice)
            return "\n".join(lines)

    return "😢 Aiyoh, no more bus today already!" + "\n" + service_notice


def handle_location_callback(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()

    stop_key = query.data.split(":")[1]
    if stop_key not in STOP_NAMES:
        return

    day_type = get_day_type()
    if day_type == "sunday":
        query.edit_message_text(no_sunday_service, parse_mode=ParseMode.HTML)
        return

    text = build_next_bus_text(stop_key, day_type)
    query.edit_message_text(text, parse_mode=ParseMode.HTML,
                            reply_markup=location_inline_keyboard())


def main() -> None:
    updater = Updater(TOKEN)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("schedule", prompt_schedule))
    dp.add_handler(CallbackQueryHandler(handle_schedule_callback, pattern=r"^schedule:"))
    dp.add_handler(CommandHandler("location", prompt_location))
    dp.add_handler(CallbackQueryHandler(handle_location_callback, pattern=r"^location:"))

    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()
