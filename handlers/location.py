import datetime

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from config import (
    ALL_LEAD_MINUTES,
    MIN_REMIND_THRESHOLD,
    REMIND_SCHEDULE,
    SG_TZ,
    STOP_EMOJIS,
    STOP_NAMES,
    TRIP_DESTINATIONS,
    no_sunday_service,
    service_notice,
)
from helpers import (
    add_minutes,
    format_bus_msg,
    get_day_type,
    get_singapore_now,
    get_stop_schedule,
    get_trips_for_day_type,
    minutes_until,
)


def _get_lead_times(minutes_away):
    for threshold, leads in REMIND_SCHEDULE:
        if minutes_away >= threshold:
            return leads
    return []


def location_inline_keyboard(remind_info=None, selected_stop=None, active_reminder=False):
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
                f":{remind_info['time_compact']}:{remind_info['trip_type']}"
            )
            rows.append([InlineKeyboardButton("✅ Reminder set", callback_data=cancel_data)])
        else:
            cb = (
                f"remind:{remind_info['stop_key']}"
                f":{remind_info['time_compact']}:{remind_info['trip_type']}"
            )
            rows.append([InlineKeyboardButton("⏰ Remind me", callback_data=cb)])
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
            if mins >= MIN_REMIND_THRESHOLD:
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
        return False
    for m in ALL_LEAD_MINUTES:
        name = _make_job_name(user_id, remind_info["stop_key"], remind_info["time_compact"], m)
        if context.job_queue.get_jobs_by_name(name):
            return True
    return False


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


def _parse_reminder_callback(data):
    parts = data.split(":")
    if len(parts) != 4:
        return None
    _, stop_key, time_compact, trip_type = parts
    if stop_key not in STOP_NAMES or trip_type not in TRIP_DESTINATIONS:
        return None
    return stop_key, time_compact, trip_type


def _make_job_name(user_id, stop_key, time_compact, lead_minutes):
    return f"remind:{user_id}:{stop_key}:{time_compact}:{lead_minutes}"


async def handle_remind_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    parsed = _parse_reminder_callback(query.data)
    if not parsed:
        return
    stop_key, time_compact, trip_type = parsed

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

    mins_away = minutes_until(now.time(), bus_time)
    lead_times = _get_lead_times(mins_away)

    for lead in lead_times:
        job_name = _make_job_name(query.from_user.id, stop_key, time_compact, lead)
        if context.job_queue.get_jobs_by_name(job_name):
            continue

        if lead == 0:
            fire_dt = now
        else:
            fire_time_str = add_minutes(departure_time_str, -lead)
            fire_time = datetime.datetime.strptime(fire_time_str, "%H:%M").time()
            fire_dt = datetime.datetime.combine(now.date(), fire_time, tzinfo=SG_TZ)

        reminder_data = {
            "chat_id": query.message.chat_id,
            "stop_key": stop_key,
            "departure_time": departure_time_str,
            "trip_type": trip_type,
            "lead_minutes": lead,
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
    await query.edit_message_text(
        text,
        parse_mode=ParseMode.HTML,
        reply_markup=location_inline_keyboard(
            remind_info, selected_stop=stop_key, active_reminder=True
        ),
    )


async def send_reminder(context: ContextTypes.DEFAULT_TYPE) -> None:
    data = context.job.data
    stop_key = data["stop_key"]
    departure_time = data["departure_time"]
    trip_type = data["trip_type"]
    stop_name = STOP_NAMES[stop_key]
    stop_emoji = STOP_EMOJIS[stop_key]
    destination = TRIP_DESTINATIONS[trip_type] if stop_key == "asr" else STOP_NAMES["asr"]
    lead_minutes = data["lead_minutes"]

    if lead_minutes == 0:
        timing_line = f"🚌 Bus at {departure_time} is here!"
        cta = "Go queue for boarding! 🚶"
    elif lead_minutes <= 2:
        timing_line = f"🚌 Bus arriving in {lead_minutes} min at {departure_time}"
        cta = "Go go go! 🏃"
    else:
        timing_line = f"🚌 Bus coming in {lead_minutes} min at {departure_time}"
        cta = "Time to get ready! 👟"

    text = (
        f"🔔 <b>Bus reminder!</b>\n\n"
        f"{timing_line}\n"
        f"{stop_emoji} {stop_name}\n"
        f"➡️ Going to <b>{destination}</b>\n\n"
        f"{cta}"
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

    parsed = _parse_reminder_callback(query.data)
    if not parsed:
        return
    stop_key, time_compact, _ = parsed

    for m in ALL_LEAD_MINUTES:
        job_name = _make_job_name(query.from_user.id, stop_key, time_compact, m)
        for job in context.job_queue.get_jobs_by_name(job_name):
            job.schedule_removal()

    day_type = get_day_type()
    text, remind_info = build_next_bus_text(stop_key, day_type)
    await query.edit_message_text(
        text,
        parse_mode=ParseMode.HTML,
        reply_markup=location_inline_keyboard(remind_info, selected_stop=stop_key),
    )
