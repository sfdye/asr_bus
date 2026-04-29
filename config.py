import os
from zoneinfo import ZoneInfo

import holidays
from dotenv import load_dotenv

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

REMIND_SCHEDULE = [(10, [5, 2]), (5, [3]), (2, [0])]
ALL_LEAD_MINUTES = sorted({m for _, leads in REMIND_SCHEDULE for m in leads})
MIN_REMIND_THRESHOLD = 2

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
