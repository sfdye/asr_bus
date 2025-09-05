# ASR Bus Telegram Bot 🚌

A Telegram bot that provides real-time shuttle bus schedules and arrival times for residents of Avenue South Residence (ASR) traveling to/from Outram Park MRT station in Singapore.

## ✨ Features

- **Real-time bus arrivals** - Get next bus timing based on current time
- **Complete schedules** - View full timetables for both directions
- **User-friendly interface** - Custom keyboards for easy interaction
- **Accurate data** - Synchronized with official shuttle bus schedules

## 🚍 Schedule Overview

- **Service Hours**: 8:00 AM - 7:40 PM daily (Monday to Sunday)
- **Frequency**: 22 trips per day in each direction
- **Travel Time**: ~4 minutes from ASR to Outram Park MRT
- **Break Periods**:
  - 10:15-10:35 (Break)
  - 13:20-14:20 (Lunch Break)  
  - 17:05-17:40 (Pump petrol & break)

## 🛠 Prerequisites

- Python 3.7 or higher
- Telegram account

## 📦 Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd asr_bus
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment

Create a `.env` file in the project root:

```bash
TOKEN=your_bot_token_here
```

### 4. Run the Bot

```bash
python bus_bot.py
```

You should see output indicating the bot is running and polling for updates.

## 🎮 Bot Commands

| Command | Description |
|---------|-------------|
| `/start` | Welcome message with bot introduction and disclaimer |
| `/location` | Get next bus arrival time from your current location |
| `/schedule` | View complete bus schedules for both directions |

## 🧪 Testing

### Automated Testing

Run the comprehensive test suite:

```bash
python -m unittest test_bus_bot.py -v
```

### Manual Testing Checklist

#### 1. Start Command

```
Send: /start
Expected: Welcome message + disclaimer + commands list
```

#### 2. Schedule Display

```
Send: /schedule
Click: "ASR Schedule" → See 22 departure times (08:00 to 19:40)
Click: "Outram MRT Schedule" → See 22 arrival times (08:04 to 19:44)
```

#### 3. Location-Based Timing

```
Send: /location
Click: "ASR" → Next bus timing + service notice
Click: "Outram MRT" → Next bus timing + service notice
```


## 🚀 Deployment

### Local Development

```bash
source .venv/bin/activate
export TOKEN=<dev-token>
(venv) python bus_bot.py
```

### Production Deployment

Deployed on Raspberry Pi 4.

```bash
ssh raspberrypi.local


cat /etc/supervisor/conf.d/asr_bus.conf

[program:asr_bus]
user=pi
directory=/home/pi/Code/asr_bus
command=/home/pi/Code/asr_bus/.virtualenv/bin/python bus_bot.py

autostart=true
autorestart=true
stdout_logfile=/home/pi/Code/asr_bus/stdout.log
stderr_logfile=/home/pi/Code/asr_bus/stderr.log
```

---

**Built with ❤️ for the ASR community** 🏠🚌
