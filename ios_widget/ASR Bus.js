// icon-color: deep-green; icon-glyph: bus;

// Configure stop via widget parameter: asr, outram6, outram7, harbourfront
// Default: asr

const STOPS = {
  asr: { name: "ASR", emoji: "🏠", offset: 0, lat: 1.276626, lon: 103.830288 },
  outram6: { name: "Outram Exit 6", emoji: "🚇", offset: 6, lat: 1.2789872116033196, lon: 103.83856904062411 },
  outram7: { name: "Outram Exit 7", emoji: "🚇", offset: 8, lat: 1.280980927082586, lon: 103.83878336326352 },
  harbourfront: { name: "Harbourfront", emoji: "🛍️", offset: 10, lat: 1.265883572108345, lon: 103.82149497860111 },
};

const TRIP_STOPS = {
  A: ["asr", "outram6", "outram7"],
  B: ["asr", "harbourfront"],
};

const DESTINATIONS = { A: "🚇 Outram Park", B: "🛍️ Harbourfront" };

const WEEKDAY_TRIPS = [
  ["07:20", "A"], ["07:40", "A"], ["08:00", "A"], ["08:20", "A"],
  ["08:40", "A"], ["09:00", "A"], ["09:30", "A"], ["10:00", "B"],
  ["10:30", "A"], ["11:00", "B"], ["11:30", "A"], ["13:00", "B"],
  ["13:30", "A"], ["14:00", "B"], ["14:30", "A"], ["15:00", "B"],
  ["16:30", "A"], ["17:00", "B"], ["17:30", "A"], ["18:00", "B"],
  ["18:30", "A"], ["19:00", "B"], ["19:30", "A"], ["20:00", "B"],
];

const SATURDAY_TRIPS = [
  ["09:00", "A"], ["09:30", "B"], ["10:00", "A"], ["10:30", "B"],
  ["11:00", "A"], ["11:30", "B"], ["12:00", "A"], ["12:30", "B"],
  ["14:00", "A"], ["14:30", "B"], ["15:00", "A"], ["15:30", "B"],
  ["16:00", "A"], ["16:30", "B"], ["18:00", "A"], ["18:30", "B"],
  ["19:00", "A"], ["19:30", "B"], ["20:00", "A"], ["20:30", "B"],
];

// Singapore public holidays 2025
const SG_HOLIDAYS = [
  "2025-01-01", "2025-01-29", "2025-01-30", "2025-03-31",
  "2025-04-18", "2025-05-01", "2025-05-12", "2025-06-06",
  "2025-06-07", "2025-08-09", "2025-10-20", "2025-11-01",
  "2025-12-25",
];

function getSGTime() {
  const now = new Date();
  const sgOffset = 8 * 60;
  const utcMs = now.getTime() + now.getTimezoneOffset() * 60000;
  return new Date(utcMs + sgOffset * 60000);
}

function isHoliday(date) {
  const dateStr = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}-${String(date.getDate()).padStart(2, "0")}`;
  return SG_HOLIDAYS.includes(dateStr);
}

function getDayType(date) {
  const day = date.getDay();
  if (day === 0) return "sunday";
  if (day === 6 || isHoliday(date)) return "saturday";
  return "weekday";
}

function getTrips(dayType) {
  if (dayType === "weekday") return WEEKDAY_TRIPS;
  if (dayType === "saturday") return SATURDAY_TRIPS;
  return null;
}

function timeToMinutes(timeStr) {
  const [h, m] = timeStr.split(":").map(Number);
  return h * 60 + m;
}

function addMinutes(timeStr, mins) {
  const total = timeToMinutes(timeStr) + mins;
  const h = Math.floor(total / 60);
  const m = total % 60;
  return `${String(h).padStart(2, "0")}:${String(m).padStart(2, "0")}`;
}

function getNextBuses(stopKey, now) {
  const dayType = getDayType(now);
  const trips = getTrips(dayType);
  if (!trips) return { noService: true };

  const stop = STOPS[stopKey];
  const nowMins = now.getHours() * 60 + now.getMinutes();
  const results = [];

  for (const [asrTime, tripType] of trips) {
    if (!TRIP_STOPS[tripType].includes(stopKey)) continue;
    const arrivalTime = addMinutes(asrTime, stop.offset);
    const arrivalMins = timeToMinutes(arrivalTime);
    if (arrivalMins >= nowMins) {
      results.push({
        time: arrivalTime,
        mins: arrivalMins - nowMins,
        dest: DESTINATIONS[tripType],
        type: tripType,
      });
    }
    if (results.length >= 2) break;
  }

  if (results.length === 0) return { noMoreBus: true };
  return { buses: results };
}

function distance(lat1, lon1, lat2, lon2) {
  const R = 6371000;
  const dLat = (lat2 - lat1) * Math.PI / 180;
  const dLon = (lon2 - lon1) * Math.PI / 180;
  const a = Math.sin(dLat / 2) ** 2 +
    Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
    Math.sin(dLon / 2) ** 2;
  return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
}

function nearestStop(lat, lon) {
  let best = "asr";
  let bestDist = Infinity;
  for (const [key, stop] of Object.entries(STOPS)) {
    const d = distance(lat, lon, stop.lat, stop.lon);
    if (d < bestDist) {
      bestDist = d;
      best = key;
    }
  }
  return best;
}

async function resolveStop() {
  const param = (args.widgetParameter || "").toLowerCase().trim();
  if (param === "auto" || param === "") {
    try {
      Location.setAccuracyToHundredMeters();
      const loc = await Location.current();
      return nearestStop(loc.latitude, loc.longitude);
    } catch {
      return "asr";
    }
  }
  return STOPS[param] ? param : "asr";
}

// Widget rendering
const resolvedKey = await resolveStop();
const stop = STOPS[resolvedKey];
const now = getSGTime();
const result = getNextBuses(resolvedKey, now);

if (config.runsInWidget) {
  const widget = new ListWidget();
  widget.setPadding(0, 0, 0, 0);

  if (result.noService) {
    const row = widget.addStack();
    row.addText("🚌 No Sun service");
  } else if (result.noMoreBus) {
    const row = widget.addStack();
    row.addText("🚌 No more bus today");
  } else {
    const bus = result.buses[0];
    const header = widget.addStack();
    header.layoutHorizontally();
    const icon = header.addText(`🚌 ${stop.name}`);
    icon.font = Font.boldSystemFont(12);

    widget.addSpacer(2);

    const main = widget.addStack();
    main.layoutHorizontally();
    const minsText = main.addText(`${bus.mins} min`);
    minsText.font = Font.boldSystemFont(26);
    main.addSpacer(4);
    const timeText = main.addText(bus.time);
    timeText.font = Font.systemFont(14);
    timeText.textOpacity = 0.7;

    widget.addSpacer(2);

    if (resolvedKey === "asr") {
      const dest = widget.addStack();
      const destText = dest.addText(`→ ${bus.dest}`);
      destText.font = Font.systemFont(11);
      destText.textOpacity = 0.7;
    }

    if (result.buses.length > 1) {
      const next = result.buses[1];
      const nextRow = widget.addStack();
      const nextText = nextRow.addText(`Next: ${next.time} (${next.mins} min)`);
      nextText.font = Font.systemFont(11);
      nextText.textOpacity = 0.5;
    }
  }

  widget.refreshAfterDate = new Date(Date.now() + 5 * 60 * 1000);
  Script.setWidget(widget);
  Script.complete();
} else {
  // Running in app - show detailed info
  const table = new UITable();
  table.showSeparators = true;

  const headerRow = new UITableRow();
  headerRow.isHeader = true;
  headerRow.addText(`🚌 ASR Bus - ${stop.name}`);
  table.addRow(headerRow);

  if (result.noService) {
    const row = new UITableRow();
    row.addText("No service on Sundays");
    table.addRow(row);
  } else if (result.noMoreBus) {
    const row = new UITableRow();
    row.addText("No more buses today");
    table.addRow(row);
  } else {
    for (const bus of result.buses) {
      const row = new UITableRow();
      const label = resolvedKey === "asr" ? `→ ${bus.dest}` : "";
      row.addText(`${bus.time} (${bus.mins} min) ${label}`);
      table.addRow(row);
    }
  }

  const infoRow = new UITableRow();
  infoRow.addText("Widget param: asr, outram6, outram7, harbourfront", "Set in widget config");
  table.addRow(infoRow);

  await table.present();
}
