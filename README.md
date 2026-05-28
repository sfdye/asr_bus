# ASR Bus Telegram Bot 🚌

A Telegram bot that provides real-time shuttle bus schedules and arrival times for residents of Avenue South Residence (ASR) in Singapore.

## ✨ Features

- **Real-time bus arrivals** - Get next bus timing based on current time
- **4 stops** - ASR, Outram Park MRT Exit 6 & 7, Harbourfront MRT Exit D
- **Weekday & Saturday schedules** - Auto-detected based on current day
- **Singlish personality** - Local flavour with fun emojis
- **User-friendly interface** - Custom keyboards for easy interaction

## 🚍 Schedule Overview

- **Service Days**: Monday to Saturday (no Sunday service)
- **Route A**: ASR → Outram Park MRT Exit 6 → Outram Park MRT Exit 7
- **Route B**: ASR → Harbourfront MRT Exit D
- **Travel Time**: +6 min (Exit 6), +8 min (Exit 7), +10 min (Harbourfront)

### Weekday (Mon-Fri)
- **Service Hours**: 7:20 AM - 8:00 PM (23 trips)
- **Break Periods**:
  - After 09:00 (Driver Break)
  - 12:00-13:00 (Lunch Break)
  - After 15:00 (Driver Break & Petrol)
- **Last drop-off**: 20:15

### Saturday
- **Service Hours**: 9:00 AM - 8:30 PM (20 trips)
- **Break Periods**:
  - 13:00-14:00 (Lunch Break)
  - After 16:30 (Driver Break & Petrol)
- **Last drop-off**: 20:45

## 🛠 Prerequisites

- Python 3.13 or higher
- [uv](https://docs.astral.sh/uv/)
- Telegram account

## 📦 Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd asr_bus
```

### 2. Install Dependencies

```bash
uv sync
```

### 3. Configure Environment

Create a `.env` file in the project root:

```bash
TOKEN=your_bot_token_here
```

### 4. Run the Bot

```bash
uv run python bus_bot.py
```

## 🎮 Bot Commands

| Command | Description |
|---------|-------------|
| `/start` | Welcome message with bot introduction and disclaimer |
| `/location` | Get next bus arrival time from your current stop |
| `/schedule` | View full timetable for a specific stop |

## 🧹 Linting & Formatting

This project uses [ruff](https://docs.astral.sh/ruff/) for linting and formatting, enforced via [pre-commit](https://pre-commit.com/).

Set up the pre-commit hooks after cloning:

```bash
uv run pre-commit install
```

Ruff will auto-fix lint issues and format code on every commit. To run manually:

```bash
uv run ruff check --fix .
uv run ruff format .
```

## 🧪 Testing

### Automated Testing

Run the test suite:

```bash
uv run pytest -v
```

### Manual Testing Checklist

#### 1. Start Command

```
Send: /start
Expected: Welcome message + disclaimer
```

#### 2. Schedule Display

```
Send: /schedule
Expected: Day-type detected, 4 stop buttons shown
Click: "ASR Schedule" → Timetable with destinations per trip
Click: "Harbourfront MRT Exit D Schedule" → Arrival times only
```

#### 3. Location-Based Timing

```
Send: /location
Expected: 4 stop buttons shown (Sunday: no-service message)
Click: "ASR" → Next bus + destination + following bus
Click: "Outram Park MRT Exit 6" → Next bus + following bus
```

## 🚀 Deployment

### Local Development

```bash
export TOKEN=<dev-token>
uv run python bus_bot.py
```

### Production Deployment

Deployed on Raspberry Pi 4.

```bash
ssh raspberrypi.local


cat /etc/supervisor/conf.d/asr_bus.conf

[program:asr_bus]
user=pi
directory=/home/pi/Code/asr_bus
command=/home/pi/.local/bin/uv run python bus_bot.py

autostart=true
autorestart=true
stdout_logfile=/home/pi/Code/asr_bus/stdout.log
stderr_logfile=/home/pi/Code/asr_bus/stderr.log
```

## 📱 iOS Lock Screen Widget (Scriptable)

A lock screen widget showing next bus timing, auto-detecting your nearest stop.

### Setup

1. Install [Scriptable](https://apps.apple.com/app/scriptable/id1405459188) from the App Store (free)
2. Open Scriptable → tap **+** → paste the contents of [`ios_widget/ASR Bus.js`](ios_widget/ASR%20Bus.js)
3. Name the script "ASR Bus"
4. Grant Scriptable "Always" location permission (Settings → Privacy → Location Services → Scriptable)

### Add Lock Screen Widget

1. Long-press your lock screen → **Customize** → **Lock Screen**
2. Tap the widget area → Add **Scriptable**
3. Long-press the widget → **Edit Widget**
4. Set **Script** to "ASR Bus"
5. Set **Parameter** (optional, see below)

### Widget Parameters

| Parameter | Stop |
|-----------|------|
| *(empty)* or `auto` | Auto-detect nearest stop via GPS |
| `asr` | Avenue South Residence |
| `outram6` | Outram Park MRT Exit 6 |
| `outram7` | Outram Park MRT Exit 7 |
| `harbourfront` | Harbourfront MRT Exit D |

### What it shows

- **Minutes until next bus** (bold, large)
- **Arrival/departure time**
- **Destination** (when departing from ASR)
- **Following bus** timing

### Notes

- Widget refreshes every ~5 minutes (iOS controls actual refresh rate)
- No internet needed — schedule is embedded in the script

---

**Built with ❤️ for the ASR community** 🏠🚌
