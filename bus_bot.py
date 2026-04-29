from telegram.ext import Application, CallbackQueryHandler, CommandHandler, Defaults

from config import SG_TZ, TOKEN
from handlers.location import (
    handle_cancel_callback,
    handle_location_callback,
    handle_noop_callback,
    handle_remind_callback,
    prompt_location,
)
from handlers.schedule import handle_schedule_callback, prompt_schedule, start


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
