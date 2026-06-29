# ASR Bus 🚌

Shuttle bus schedule tools for Avenue South Residence (ASR) in Singapore.

**👉 [Install Widget](https://sfdye.github.io/asr_bus/install.html)** — works on both iPhone and Android.

## 🚍 Schedule Overview

- **Service Days**: Monday to Saturday (no Sunday service)
- **Route A**: ASR → Outram Park MRT Exit 6 → Outram Park MRT Exit 7
- **Route B**: ASR → Harbourfront MRT Exit D
- **Travel Time**: +6 min (Exit 6), +8 min (Exit 7), +10 min (Harbourfront)

### Weekday (Mon-Fri)
- **Service Hours**: 7:20 AM - 8:00 PM (24 trips)

### Saturday & Public Holidays
- **Service Hours**: 9:00 AM - 8:30 PM (20 trips)

---

## 📱 iOS Widget (Scriptable)

A lock screen widget showing next bus timing. Auto-detects your nearest stop via GPS.

- Runs on [Scriptable](https://apps.apple.com/app/scriptable/id1405459188) (free)
- Works offline — schedule is embedded
- English & Chinese auto-detected

**[Install →](https://sfdye.github.io/asr_bus/install.html)**

See [`ios_widget/`](ios_widget/) for the source.

---

## 🤖 Android Widget

A native home screen widget showing next bus timing with 5-minute auto-refresh.

- Download the APK from [Releases](https://github.com/sfdye/asr_bus/releases)
- Works offline — schedule is embedded
- Configurable stop selection & text size
- English & Chinese auto-detected

**[Install →](https://sfdye.github.io/asr_bus/install.html)**

See [`android_widget/`](android_widget/) for source and build instructions.

---

## 💬 Telegram Bot

A Telegram bot with real-time schedule lookup. Good for occasional checks or sharing with others who don't want a widget.

### Commands

| Command | Description |
|---------|-------------|
| `/start` | Welcome message |
| `/location` | Next bus from your current stop |
| `/schedule` | Full timetable for a specific stop |

### Running the Bot

```bash
uv sync
export TOKEN=your_bot_token_here
uv run python bus_bot.py
```

Deployed on Raspberry Pi 4 via supervisord. See `bus_bot.py` for source.

---

## 🛠 Development

### Prerequisites

- Python 3.13+ and [uv](https://docs.astral.sh/uv/) (for the bot)
- Android Studio (for the Android widget)

### Linting & Testing

```bash
uv run ruff check --fix .
uv run ruff format .
uv run pytest -v
```

---

**Built with ❤️ for the ASR community** 🏠🚌
