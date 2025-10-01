import datetime
import os

import pytz
import telegram
from dotenv import load_dotenv
from telegram import ParseMode, Update
from telegram.ext import (CallbackContext, CommandHandler, Filters,
                          MessageHandler, Updater)

load_dotenv(override=True)  # take environment variables

TOKEN = os.getenv("TOKEN")

# Bus schedules for ASR and Outram MRT
asr_schedule = [
    "08:00",
    "08:30",
    "09:00",
    "09:30",
    "10:00",
    "10:35",
    "11:05",
    "11:35",
    "12:05",
    "12:35",
    "13:05",
    "14:20",
    "14:50",
    "15:20",
    "15:50",
    "16:20",
    "16:50",
    "17:40",
    "18:10",
    "18:40",
    "19:10",
    "19:40",
]

outram_schedule = [
    "08:04",
    "08:34",
    "09:04",
    "09:34",
    "10:04",
    "10:39",
    "11:09",
    "11:39",
    "12:09",
    "12:39",
    "13:09",
    "14:24",
    "14:54",
    "15:24",
    "15:54",
    "16:24",
    "16:54",
    "17:44",
    "18:14",
    "18:44",
    "19:14",
    "19:44",
]

intro_text = """
Hi neighbour, I'm a bot programmed to tell you the estimated time our ASR buses will arrive.
    
Commands you may try:
/location
/schedule
"""

# Service notice message to be added to all timing responses
service_notice = """
⚠️ <b>IMPORTANT</b>: Our beloved shuttle bus service ends <b>30 Sep 2025</b>! 

💙 This service connects our community daily and <b>keeps our property attractive</b>. To keep it running, please:
✓ Attend the upcoming EOGM/AGM
✓ Vote to continue this essential service

<b>Your voice matters for our community!</b> 🗳️
"""

# Warning message for when service is paused
service_paused_warning = """
🚌❌ <b>SHUTTLE BUS SERVICE CURRENTLY PAUSED</b> ❌🚌

Our beloved shuttle bus service has ended as of <b>30 September 2025</b>.

🗳️ <b>BUT THERE'S HOPE!</b> 🗳️

📢 <b>UPCOMING EGM (EXTRAORDINARY GENERAL MEETING)</b>
Your participation can bring back our shuttle bus service! 

✅ <b>PLEASE VOTE IN THE UPCOMING EGM!</b>
💙 <b>Your vote matters!</b> Together we can restore this essential community service that:
   • Connects our residents daily
   • Keeps our property attractive and valuable
   • Serves our community's transport needs

<b>🏘️ Our community needs YOUR voice to bring back our shuttle bus! 🗳️</b>

Meanwhile, for alternative transport options:
🚇 Public transport (MRT/Bus)
🚗 Private transport
🚕 Ride-hailing services

<b>Don't forget: VOTE in the EGM to restore our shuttle bus service!</b> 💪
"""


def is_service_paused():
    """Check if the shuttle bus service should be paused"""
    singapore_timezone = pytz.timezone("Asia/Singapore")
    current_date = datetime.datetime.now(singapore_timezone).date()
    service_end_date = datetime.date(2025, 9, 30)
    return current_date > service_end_date


# Function to display disclaimer when a new user joins
def start(update: Update, context: CallbackContext) -> None:
    # Check if service is paused
    if is_service_paused():
        update.message.reply_text(service_paused_warning, parse_mode=ParseMode.HTML)
        return
        
    introduction = intro_text
    disclaimer = """
        Please note:
        * Bus timings are estimated and subjected to traffic conditions.
        * Residents are advised to be at least 5 to 8 minutes early at the designated alight/pickup points but do expect some delays especially during peak hours.
        * For the safety of passengers, standing, heavy, lengthy & bulky items in the bus are not allowed.
        * The bus will only stop at the designated stops.
        * No waiting, parking/holding of buses are allowed, as such facilities are meant for boarding and alighting activities only.
    """
    update.message.reply_text(introduction, parse_mode=ParseMode.HTML)
    update.message.reply_text(disclaimer, parse_mode=ParseMode.HTML)


# Function to prompt user for location schedule they want
def prompt_schedule(update: Update, context: CallbackContext) -> None:
    # Check if service is paused
    if is_service_paused():
        update.message.reply_text(service_paused_warning, parse_mode=ParseMode.HTML)
        return
        
    options = ["ASR Schedule", "Outram MRT Schedule"]
    keyboard = [[telegram.KeyboardButton(option)] for option in options]
    reply_markup = telegram.ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)

    update.message.reply_text("Which one you need?", reply_markup=reply_markup)


# Function to return schedule
def get_schedule(update: Update, context: CallbackContext) -> None:
    # Check if service is paused
    if is_service_paused():
        update.message.reply_text(service_paused_warning, parse_mode=ParseMode.HTML)
        return

    # Determine the location based on the user's response
    location_schedule = update.message.text.lower()
    schedule = asr_schedule if location_schedule == "asr schedule" else outram_schedule
    # Convert schedule to rich output format
    message_text = "\n".join(schedule)
    update.message.reply_text(message_text, parse_mode=ParseMode.HTML)
    update.message.reply_text(service_notice, parse_mode=ParseMode.HTML)


# Function to prompt user for location
def prompt_location(update: Update, context: CallbackContext) -> None:
    # Check if service is paused
    if is_service_paused():
        update.message.reply_text(service_paused_warning, parse_mode=ParseMode.HTML)
        return
        
    options = ["ASR", "Outram MRT"]
    keyboard = [[telegram.KeyboardButton(option)] for option in options]
    reply_markup = telegram.ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)

    update.message.reply_text("Where are you now ah?", reply_markup=reply_markup)


# Function to calculate and return the time until the next bus
def next_bus_time(update: Update, context: CallbackContext) -> None:
    # Check if service is paused
    if is_service_paused():
        update.message.reply_text(service_paused_warning, parse_mode=ParseMode.HTML)
        return
    
    # Get the current time in the Singapore time zone
    singapore_timezone = pytz.timezone("Asia/Singapore")
    current_time = datetime.datetime.now(singapore_timezone).time()

    # Determine the location based on the user's response
    user_location = update.message.text.lower()
    if user_location == "asr":
        schedule = asr_schedule
    elif user_location == "outram mrt":
        schedule = outram_schedule
    else:
        update.message.reply_text(
            "Sorry, I didn't understand your location. Please choose either ASR or Outram MRT."
        )
        return

    # Find the next bus time
    for bus_time_str in schedule:
        bus_time_obj = datetime.datetime.strptime(bus_time_str, "%H:%M").time()
        if current_time < bus_time_obj:
            time_until_next_bus = (
                datetime.datetime.combine(datetime.date.today(), bus_time_obj)
                - datetime.datetime.combine(datetime.date.today(), current_time)
            ).seconds // 60
            update.message.reply_text(
                f"The next {user_location} bus will arrive in <b>{time_until_next_bus} minutes</b>.",
                parse_mode=ParseMode.HTML,
            )

            # Find the time for the bus following the next bus
            index_of_next_bus = schedule.index(bus_time_str)
            if index_of_next_bus < len(schedule) - 1:
                following_bus_time = datetime.datetime.strptime(
                    schedule[index_of_next_bus + 1], "%H:%M"
                ).time()
                time_until_following_bus = (
                    datetime.datetime.combine(datetime.date.today(), following_bus_time)
                    - datetime.datetime.combine(datetime.date.today(), current_time)
                ).seconds // 60
                update.message.reply_text(
                    f"The following {user_location} bus will arrive in <b>{time_until_following_bus} minutes</b>.",
                    parse_mode=ParseMode.HTML,
                )
                update.message.reply_text(service_notice, parse_mode=ParseMode.HTML)
            else:
                update.message.reply_text(
                    f"There is no following {user_location} bus for today."
                )
                update.message.reply_text(service_notice, parse_mode=ParseMode.HTML)
            return

    # If all buses have passed for the day
    update.message.reply_text(
        f"All {user_location} buses for today have already passed."
    )
    update.message.reply_text(service_notice, parse_mode=ParseMode.HTML)


# Set up the Telegram bot
def main() -> None:
    updater = Updater(TOKEN)
    dp = updater.dispatcher

    # Add command and message handlers
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("schedule", prompt_schedule))
    dp.add_handler(CommandHandler("location", prompt_location))
    dp.add_handler(
        MessageHandler(
            Filters.text(["ASR Schedule", "Outram MRT Schedule"]), get_schedule
        )
    )
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, next_bus_time))

    # Start the Bot
    updater.start_polling()

    # Run the bot until you send a signal to stop it
    updater.idle()


if __name__ == "__main__":
    main()
