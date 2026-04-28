import datetime
import os
from zoneinfo import ZoneInfo

import holidays
from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.constants import ParseMode
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes, Defaults

load_dotenv(override=True)

TOKEN = os.getenv("TOKEN")
SG_TZ = ZoneInfo("Asia/Singapore")
SG_HOLIDAYS = holidays.Singapore()

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

TRIP_DESTINATIONS = {"A": "Outram Park MRT Exit 6/7", "B": "Harbourfront MRT Exit D"}

REMIND_OPTIONS = [3, 5, 10]

weekday_trips = [
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

saturday_trips = [
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

<b>🗺️ Route:</b> ASR → Outram Park MRT Exit 6/7 / Harbourfront MRT Exit D
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


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        intro_text, parse_mode=ParseMode.HTML, reply_markup=ReplyKeyboardRemove()
    )
    disclaimer = (
        "⚠️ Take note ah:\n"
        "• Bus timing is estimate only, traffic can affect one.\n"
        "• Come 5 to 8 min early to be safe lah.\n"
        "• Cannot bring heavy/bulky items on the bus hor.\n"
        "• Bus only stop at designated stops.\n"
        "• No waiting or holding the bus at stops!"
    )
    await update.message.reply_text(
        disclaimer, parse_mode=ParseMode.HTML, reply_markup=ReplyKeyboardRemove()
    )


def schedule_inline_keyboard():
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    f"{STOP_EMOJIS[k]} {STOP_NAMES[k]}", callback_data=f"schedule:{k}"
                )
            ]
            for k in STOP_NAMES
        ]
    )


async def prompt_schedule(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    day_type = get_day_type()
    label = "Saturday" if day_type == "saturday" else "Weekday"

    if day_type == "sunday":
        msg = "😴 Sunday no bus lah.\n📋 Showing <b>Weekday</b> schedule.\nWhich stop you want?"
    else:
        msg = f"📋 <b>{label} Schedule</b>\nWhich stop you want to see?"
    await update.message.reply_text(
        msg, reply_markup=schedule_inline_keyboard(), parse_mode=ParseMode.HTML
    )


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


async def handle_schedule_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    stop_key = query.data.split(":")[1]
    if stop_key not in STOP_NAMES:
        return

    day_type = get_day_type()
    if day_type == "sunday":
        day_type = "weekday"

    text = build_schedule_text(stop_key, day_type)
    await query.edit_message_text(
        text, parse_mode=ParseMode.HTML, reply_markup=schedule_inline_keyboard()
    )


def location_inline_keyboard(remind_info=None, selected_stop=None, active_reminder=None):
    rows = []
    for k in STOP_NAMES:
        stop_btn = InlineKeyboardButton(
            f"{STOP_EMOJIS[k]} {STOP_NAMES[k]}", callback_data=f"location:{k}"
        )
        rows.append([stop_btn])

        if k != selected_stop or not remind_info:
            continue

        if active_reminder:
            cancel_data = (
                f"cancel:{remind_info['stop_key']}"
                f":{remind_info['time_compact']}:{remind_info['trip_type']}:{active_reminder}"
            )
            label = f"✅ Reminder set: {active_reminder} min before"
            rows.append([InlineKeyboardButton(label, callback_data=cancel_data)])
        else:
            time_btns = []
            for m in REMIND_OPTIONS:
                if remind_info["minutes_away"] >= m:
                    cb = (
                        f"remind:{remind_info['stop_key']}"
                        f":{remind_info['time_compact']}:{remind_info['trip_type']}:{m}"
                    )
                    time_btns.append(InlineKeyboardButton(f"{m} min", callback_data=cb))
            if time_btns:
                rows.append([InlineKeyboardButton("⏰ Remind me:", callback_data="noop")])
                rows.append(time_btns)
    return InlineKeyboardMarkup(rows)


async def prompt_location(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if get_day_type() == "sunday":
        await update.message.reply_text(
            no_sunday_service, parse_mode=ParseMode.HTML, reply_markup=ReplyKeyboardRemove()
        )
        return

    await update.message.reply_text(
        "📍 Where you at now ah?",
        reply_markup=location_inline_keyboard(),
        parse_mode=ParseMode.HTML,
    )


def build_next_bus_text(stop_key, day_type):
    current_time = get_singapore_now().time()
    trips = get_trips_for_day_type(day_type)
    schedule = get_stop_schedule(trips, stop_key)

    for i, (time_str, trip_type) in enumerate(schedule):
        bus_time = datetime.datetime.strptime(time_str, "%H:%M").time()
        if current_time <= bus_time:
            mins = minutes_until(current_time, bus_time)
            lines = [
                format_bus_msg(
                    "Next bus departs" if stop_key == "asr" else "Next bus arrives",
                    mins,
                    time_str,
                    stop_key,
                    trip_type,
                )
            ]

            if i < len(schedule) - 1:
                next_time, next_type = schedule[i + 1]
                next_bus = datetime.datetime.strptime(next_time, "%H:%M").time()
                next_mins = minutes_until(current_time, next_bus)
                lines.append(
                    format_bus_msg("Following bus", next_mins, next_time, stop_key, next_type)
                )
            else:
                lines.append("☝️ Last bus already, no more after this one!")

            lines.append(service_notice)

            remind_info = None
            if mins >= min(REMIND_OPTIONS):
                time_compact = time_str.replace(":", "")
                remind_info = {
                    "stop_key": stop_key,
                    "time_compact": time_compact,
                    "trip_type": trip_type,
                    "minutes_away": mins,
                }

            return "\n".join(lines), remind_info

    return "😢 Aiyoh, no more bus today already!" + "\n" + service_notice, None


def find_active_reminder(context, user_id, remind_info):
    if not remind_info:
        return None
    prefix = f"remind:{user_id}:{remind_info['stop_key']}:{remind_info['time_compact']}"
    for m in REMIND_OPTIONS:
        jobs = context.job_queue.get_jobs_by_name(f"{prefix}:{m}")
        if jobs:
            return m
    return None


async def handle_location_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    stop_key = query.data.split(":")[1]
    if stop_key not in STOP_NAMES:
        return

    day_type = get_day_type()
    if day_type == "sunday":
        await query.edit_message_text(no_sunday_service, parse_mode=ParseMode.HTML)
        return

    text, remind_info = build_next_bus_text(stop_key, day_type)
    active_reminder = find_active_reminder(context, query.from_user.id, remind_info)
    await query.edit_message_text(
        text,
        parse_mode=ParseMode.HTML,
        reply_markup=location_inline_keyboard(
            remind_info, selected_stop=stop_key, active_reminder=active_reminder
        ),
    )


async def handle_remind_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    parts = query.data.split(":")
    if len(parts) != 5:
        return
    _, stop_key, time_compact, trip_type, lead_str = parts
    if stop_key not in STOP_NAMES or trip_type not in TRIP_DESTINATIONS:
        return
    lead_minutes = int(lead_str)

    departure_time_str = f"{time_compact[:2]}:{time_compact[2:]}"
    bus_time = datetime.datetime.strptime(departure_time_str, "%H:%M").time()
    now = get_singapore_now()

    if now.time() > bus_time:
        await query.edit_message_text(
            "😅 This bus already gone lah! Use /location to check again.",
            parse_mode=ParseMode.HTML,
            reply_markup=location_inline_keyboard(),
        )
        return

    fire_time_str = add_minutes(departure_time_str, -lead_minutes)
    fire_time = datetime.datetime.strptime(fire_time_str, "%H:%M").time()
    fire_dt = datetime.datetime.combine(now.date(), fire_time, tzinfo=SG_TZ)

    job_name = f"remind:{query.from_user.id}:{stop_key}:{time_compact}:{lead_minutes}"
    existing = context.job_queue.get_jobs_by_name(job_name)
    if not existing:
        reminder_data = {
            "chat_id": query.message.chat_id,
            "stop_key": stop_key,
            "departure_time": departure_time_str,
            "trip_type": trip_type,
            "lead_minutes": lead_minutes,
        }
        context.job_queue.run_once(
            send_reminder,
            when=fire_dt,
            data=reminder_data,
            name=job_name,
            chat_id=query.message.chat_id,
            user_id=query.from_user.id,
        )

    day_type = get_day_type()
    text, remind_info = build_next_bus_text(stop_key, day_type)
    text += f"\n✅ Reminder set for {fire_time_str}!"
    await query.edit_message_text(
        text,
        parse_mode=ParseMode.HTML,
        reply_markup=location_inline_keyboard(
            remind_info, selected_stop=stop_key, active_reminder=lead_minutes
        ),
    )


async def send_reminder(context: ContextTypes.DEFAULT_TYPE) -> None:
    data = context.job.data
    stop_key = data["stop_key"]
    departure_time = data["departure_time"]
    trip_type = data["trip_type"]
    stop_name = STOP_NAMES[stop_key]
    stop_emoji = STOP_EMOJIS[stop_key]
    destination = TRIP_DESTINATIONS[trip_type]

    lead_minutes = data["lead_minutes"]

    text = (
        f"🔔 <b>Bus reminder!</b>\n\n"
        f"🚌 Bus coming in {lead_minutes} min at {departure_time}\n"
        f"🚏 {stop_emoji} {stop_name}\n"
        f"➡️ Going to <b>{destination}</b>\n\n"
        f"Faster go downstairs ah! 😄"
    )

    await context.bot.send_message(
        chat_id=data["chat_id"],
        text=text,
        parse_mode=ParseMode.HTML,
    )


async def handle_noop_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.callback_query.answer()


async def handle_cancel_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    parts = query.data.split(":")
    if len(parts) != 5:
        return
    _, stop_key, time_compact, _trip_type, lead_str = parts
    if stop_key not in STOP_NAMES:
        return

    job_name = f"remind:{query.from_user.id}:{stop_key}:{time_compact}:{lead_str}"
    for job in context.job_queue.get_jobs_by_name(job_name):
        job.schedule_removal()

    day_type = get_day_type()
    text, remind_info = build_next_bus_text(stop_key, day_type)
    await query.edit_message_text(
        text,
        parse_mode=ParseMode.HTML,
        reply_markup=location_inline_keyboard(remind_info, selected_stop=stop_key),
    )


def main() -> None:
    application = Application.builder().token(TOKEN).defaults(Defaults(tzinfo=SG_TZ)).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("schedule", prompt_schedule))
    application.add_handler(CallbackQueryHandler(handle_schedule_callback, pattern=r"^schedule:"))
    application.add_handler(CommandHandler("location", prompt_location))
    application.add_handler(CallbackQueryHandler(handle_location_callback, pattern=r"^location:"))
    application.add_handler(CallbackQueryHandler(handle_remind_callback, pattern=r"^remind:"))
    application.add_handler(CallbackQueryHandler(handle_cancel_callback, pattern=r"^cancel:"))
    application.add_handler(CallbackQueryHandler(handle_noop_callback, pattern=r"^noop$"))

    application.run_polling()


if __name__ == "__main__":
    main()
