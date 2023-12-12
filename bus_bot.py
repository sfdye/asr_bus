import telegram
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
import datetime
import pytz
import os 

TOKEN = os.getenv('TOKEN') || ""

# Bus schedules for ASR and Outram MRT
asr_schedule = [
    "08:00", "08:15", "08:30", "08:45", "09:00", "09:15", "09:30", "09:45",
    "10:00", "10:15", "10:35", "10:50", "11:05", "11:20", "11:35", "11:50",
    "12:05", "12:20", "12:35", "12:50", "13:05", "13:20", "14:20", "14:35",
    "14:50", "15:05", "15:20", "15:35", "15:50", "16:05", "16:20", "16:35",
    "16:50", "17:05", "17:40", "17:55", "18:10", "18:25", "18:40", "18:55",
    "19:10", "19:25", "19:40", "19:55"
]

outram_schedule = [
    "08:04", "08:34", "09:04", "09:34", "10:04", "10:39", "11:09", "11:39",
    "12:09", "12:39", "13:09", "14:24", "14:54", "15:24", "15:54", "16:24",
    "16:54", "17:24", "17:54", "18:24", "18:54", "19:24", "19:54"
]

# Function to display disclaimer when a new user joins
def start(update: Update, context: CallbackContext) -> None:
    introduction = (
        "Hi neighbour, I’m a bot programmed to tell you the estimated time our ASR buses will arrive.\n"
        "Commands you may try:\n"
        "/location \n"
        "/schedule"
    )
    disclaimer = (
        "Please note:\n"
        "* Bus timings are estimated and subjected to traffic conditions.\n"
        "* Residents are advised to be at least 5 to 8 minutes early at the designated alight/pickup points but do expect some delays especially during peak hours.\n"
        "* For the safety of passengers, standing, heavy, lengthy & bulky items in the bus are not allowed.\n"
        "* The bus will only stop at the designated stops.\n"
        "* No waiting, parking/holding of buses are allowed, as such facilities are meant for boarding and alighting activities only."
    )
    update.message.reply_text(introduction)
    update.message.reply_text(disclaimer)

# Function to prompt user for location schedule they want
def prompt_schedule(update: Update, context: CallbackContext) -> None:
    options = ["ASR Schedule", "Outram MRT Schedule"]
    keyboard = [[telegram.KeyboardButton(option)] for option in options]
    reply_markup = telegram.ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)

    update.message.reply_text("Which one you need?", reply_markup=reply_markup)

# Function to return schedule
def get_schedule(update: Update, context: CallbackContext) -> None:

    # Determine the location based on the user's response
    location_schedule = update.message.text.lower()
    if location_schedule == "asr schedule":
        schedule = asr_schedule
    elif location_schedule == "outram mrt schedule":
        schedule = outram_schedule
    
    update.message.reply_text(f"{location_schedule}: {schedule}")

# Function to prompt user for location
def prompt_location(update: Update, context: CallbackContext) -> None:
    options = ["ASR", "Outram MRT"]
    keyboard = [[telegram.KeyboardButton(option)] for option in options]
    reply_markup = telegram.ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)

    update.message.reply_text("Where are you now ah?", reply_markup=reply_markup)

# Function to calculate and return the time until the next bus
def next_bus_time(update: Update, context: CallbackContext) -> None:
    # Get the current time in the Singapore time zone
    singapore_timezone = pytz.timezone('Asia/Singapore')
    current_time = datetime.datetime.now(singapore_timezone).time()

    # Determine the location based on the user's response
    user_location = update.message.text.lower()
    if user_location == "asr":
        schedule = asr_schedule
    elif user_location == "outram mrt":
        schedule = outram_schedule
    else:
        update.message.reply_text("Sorry, I didn't understand your location. Please choose either ASR or Outram MRT.")
        return

    # Find the next bus time
    for bus_time_str in schedule:
        bus_time_obj = datetime.datetime.strptime(bus_time_str, "%H:%M").time()
        if current_time < bus_time_obj:
            time_until_next_bus = (datetime.datetime.combine(datetime.date.today(), bus_time_obj) -
                                   datetime.datetime.combine(datetime.date.today(), current_time)).seconds // 60
            update.message.reply_text(f"The next {user_location} bus will arrive in {time_until_next_bus} minutes.")

            # Find the time for the bus following the next bus
            index_of_next_bus = schedule.index(bus_time_str)
            if index_of_next_bus < len(schedule) - 1:
                following_bus_time = datetime.datetime.strptime(schedule[index_of_next_bus + 1], "%H:%M").time()
                time_until_following_bus = (datetime.datetime.combine(datetime.date.today(), following_bus_time) -
                                            datetime.datetime.combine(datetime.date.today(), current_time)).seconds // 60
                update.message.reply_text(
                    f"The following {user_location} bus will arrive in {time_until_following_bus} minutes."
                )
            else:
                update.message.reply_text(f"There is no following {user_location} bus for today.")
            return


    # If all buses have passed for the day
    update.message.reply_text(f"All {user_location} buses for today have already passed.")

# Set up the Telegram bot
def main() -> None:
    updater = Updater(TOKEN)
    dp = updater.dispatcher

    # Add command and message handlers
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("schedule", prompt_schedule))
    dp.add_handler(CommandHandler("location", prompt_location))
    dp.add_handler(MessageHandler(Filters.text(["ASR Schedule", "Outram MRT Schedule"]), get_schedule))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, next_bus_time))

    # Start the Bot
    updater.start_polling()

    # Run the bot until you send a signal to stop it
    updater.idle()

if __name__ == '__main__':
    main()
