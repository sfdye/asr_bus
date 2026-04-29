from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from config import (
    SATURDAY_LAST_DROPOFF,
    STOP_EMOJIS,
    STOP_NAMES,
    WEEKDAY_LAST_DROPOFF,
    intro_text,
    saturday_breaks,
    service_notice,
    weekday_breaks,
)
from helpers import format_asr_schedule, format_stop_schedule, get_day_type, get_trips_for_day_type


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
