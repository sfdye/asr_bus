import telegram
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
import datetime

# Replace 'YOUR_BOT_TOKEN' with the token you obtained from BotFather
TOKEN = 'YOUR_BOT_TOKEN'

# Bus schedules for ASR and Outram MRT
asr_schedule = [
    "8:00 AM", "8:15 AM", "8:30 AM", "8:45 AM", "9:00 AM", "9:15 AM", "9:30 AM", "9:45 AM",
    "10:00 AM", "10:15 AM", "10:35 AM", "10:50 AM", "11:05 AM", "11:20 AM", "11:35 AM", "11:50 AM",
    "12:05 PM", "12:20 PM", "12:35 PM", "12:50 PM", "1:05 PM", "1:20 PM", "2:20 PM", "2:35 PM",
    "2:50 PM", "3:05 PM", "3:20 PM", "3:35 PM", "3:50 PM", "4:05 PM", "4:20 PM", "4:35 PM",
    "4:50 PM", "5:05 PM", "5:40 PM", "5:55 PM", "6:10 PM", "6:25 PM", "6:40 PM", "6:55 PM",
    "7:10 PM", "7:25 PM", "7:40 PM", "7:55 PM"
]

outram_schedule = [
    "8:04 AM", "8:34 AM", "9:04 AM", "9:34 AM", "10:04 AM", "10:39 AM", "11:09 AM", "11:39 AM",
    "12:09 PM", "12:39 PM", "1:09 PM", "2:24 PM", "2:54 PM", "3:24 PM", "3:54 PM", "4:24 PM",
    "4:54 PM", "5:24 PM", "5:54 PM", "6:24 PM", "6:54 PM", "7:24 PM", "7:54 PM"
]

# Function to display disclaimer when a new user joins
def start(update: Update, context: CallbackContext) -> None:
    disclaimer = (
        "Hi neighbour, I’m a bot programmed to tell you the estimated time our ASR buses will arrive. Please note:\n"
        "* Bus timings are estimated and subjected to traffic conditions.\n"
        "* Residents are advised to be at least 5 to 8 minutes early at the designated alight/pickup points but do expect some delays especially during peak hours.\n"
        "* For the safety of passengers, standing, heavy, lengthy & bulky items in the bus are not allowed.\n"
        "* The bus will only stop at the designated stops.\n"
        "* No waiting, parking/holding of buses are allowed, as such facilities are meant for boarding and alighting activities only."
    )
    update.message.reply_text(disclaimer)

# Function to prompt user for location
def prompt_location(update: Update, context: CallbackContext) -> None:
    options = ["ASR", "Outram MRT"]
    keyboard = [[telegram.KeyboardButton(option)] for option in options]
    reply_markup = telegram.ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)

    update.message.reply_text("Where are you now ah?", reply_markup=reply_markup)

# Function to calculate and return the time until the next bus
def next_bus_time(update: Update, context: CallbackContext) -> None:
    current_time = datetime.datetime.now().time()

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
    for bus_time in schedule:
        bus_time_obj = datetime.datetime.strptime(bus_time, "%I:%M %p").time()
        if current_time < bus_time_obj:
            time_until_next_bus = (datetime.datetime.combine(datetime.date.today(), bus_time_obj) -
                                   datetime.datetime.combine(datetime.date.today(), current_time)).seconds // 60
            update.message.reply_text(f"The next {user_location} bus will arrive in {time_until_next_bus} minutes.")
            return

    # If all buses have passed for the day
    update.message.reply_text(f"All {user_location} buses for today have already passed.")

# Set up the Telegram bot
def main() -> None:
    updater = Updater(TOKEN)
    dp = updater.dispatcher

    # Add command and message handlers
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, next_bus_time))
    dp.add_handler(MessageHandler(Filters.command, prompt_location))

    # Start the Bot
    updater.start_polling()

    # Run the bot until you send a signal to stop it
    updater.idle()

if __name__ == '__main__':
    main()
