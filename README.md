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

- Python 3.11 or higher
- [uv](https://docs.astral.sh/uv/) package manager
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

## 🧪 Testing

### Automated Testing

Run the test suite (55 tests):

```bash
uv run python -m unittest test_bus_bot.py -v
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
command=/home/pi/Code/asr_bus/.venv/bin/python bus_bot.py

autostart=true
autorestart=true
stdout_logfile=/home/pi/Code/asr_bus/stdout.log
stderr_logfile=/home/pi/Code/asr_bus/stderr.log
```

---

**Built with ❤️ for the ASR community** 🏠🚌
