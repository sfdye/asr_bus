// icon-color: deep-green; icon-glyph: bus;

// Configure stop via widget parameter: asr, outram6, outram7, harbourfront
// Default: asr

const lang = Device.language().startsWith("zh") ? "zh" : "en";

const STRINGS = {
  en: {
    noSunService: "🚌 No Sun service",
    noMoreBus: "🚌 No more bus today",
    noSunServiceDetail: "No service on Sundays",
    noMoreBusDetail: "No more buses today",
    min: "min",
    inHrs: "in ~%s hrs",
    next: "Next:",
    updated: "Last update at %s",
    widgetParam: "Widget param: asr, outram6, outram7, harbourfront",
    setInConfig: "Set in widget config",
  },
  zh: {
    noSunService: "🚌 周日无班车",
    noMoreBus: "🚌 今日已无班车",
    noSunServiceDetail: "周日无班车服务",
    noMoreBusDetail: "今日已无班车",
    min: "分钟",
    inHrs: "约%s小时后",
    next: "下一班:",
    updated: "最后更新 %s",
    widgetParam: "参数: asr, outram6, outram7, harbourfront",
    setInConfig: "在小组件配置中设置",
  },
};
const T = STRINGS[lang];

const STOPS = {
  asr: { name: "ASR", emoji: "🏠", offset: 0, lat: 1.276626, lon: 103.830288 },
  outram6: { name: lang === "zh" ? "欧南园6号口" : "Outram Exit 6", emoji: "🚇", offset: 6, lat: 1.2789872116033196, lon: 103.83856904062411 },
  outram7: { name: lang === "zh" ? "欧南园7号口" : "Outram Exit 7", emoji: "🚇", offset: 8, lat: 1.280980927082586, lon: 103.83878336326352 },
  harbourfront: { name: lang === "zh" ? "港湾" : "Harbourfront", emoji: "🛍️", offset: 10, lat: 1.265883572108345, lon: 103.82149497860111 },
};

const TRIP_STOPS = {
  A: ["asr", "outram6", "outram7"],
  B: ["asr", "harbourfront"],
};

const DESTINATIONS = {
  A: lang === "zh" ? "🚇 欧南园" : "🚇 Outram Park",
  B: lang === "zh" ? "🛍️ 港湾" : "🛍️ Harbourfront",
};

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

const HOLIDAYS_URL = "https://raw.githubusercontent.com/sfdye/asr_bus/master/ios_widget/holidays.json";
const HOLIDAYS_CACHE_KEY = "asr_bus_holidays";

const FALLBACK_HOLIDAYS = [
  "2026-01-01", "2026-02-17", "2026-02-18", "2026-03-21",
  "2026-04-03", "2026-05-01", "2026-05-27", "2026-05-31",
  "2026-06-01", "2026-08-09", "2026-08-10", "2026-11-08",
  "2026-11-09", "2026-12-25",
];

async function loadHolidays() {
  const fm = FileManager.local();
  const cachePath = fm.joinPath(fm.documentsDirectory(), HOLIDAYS_CACHE_KEY + ".json");

  try {
    const req = new Request(HOLIDAYS_URL);
    req.timeoutInterval = 5;
    const json = await req.loadJSON();
    fm.writeString(cachePath, JSON.stringify(json));
    return json;
  } catch {
    try {
      if (fm.fileExists(cachePath)) {
        return JSON.parse(fm.readString(cachePath));
      }
    } catch {}
  }
  return null;
}

function isHoliday(date, holidays) {
  const dateStr = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}-${String(date.getDate()).padStart(2, "0")}`;
  const year = String(date.getFullYear());
  if (holidays && holidays[year]) {
    return holidays[year].includes(dateStr);
  }
  return FALLBACK_HOLIDAYS.includes(dateStr);
}

function getSGTime() {
  const now = new Date();
  const sgOffset = 8 * 60;
  const utcMs = now.getTime() + now.getTimezoneOffset() * 60000;
  return new Date(utcMs + sgOffset * 60000);
}

function getDayType(date, holidays) {
  const day = date.getDay();
  if (day === 0) return "sunday";
  if (day === 6 || isHoliday(date, holidays)) return "saturday";
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

function getNextBuses(stopKey, now, holidays) {
  const dayType = getDayType(now, holidays);
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
const holidays = await loadHolidays();
const stop = STOPS[resolvedKey];
const now = getSGTime();
const result = getNextBuses(resolvedKey, now, holidays);

if (config.runsInWidget) {
  const widget = new ListWidget();
  widget.setPadding(0, 0, 0, 0);

  if (result.noService) {
    const row = widget.addStack();
    row.addText(T.noSunService);
  } else if (result.noMoreBus) {
    const row = widget.addStack();
    row.addText(T.noMoreBus);
  } else {
    const bus = result.buses[0];
    const header = widget.addStack();
    header.layoutHorizontally();
    const icon = header.addText(`🚌 ${stop.name}`);
    icon.font = Font.boldSystemFont(12);
    header.addSpacer();
    const timeStr = `${String(now.getHours()).padStart(2, "0")}:${String(now.getMinutes()).padStart(2, "0")}`;
    const updatedText = header.addText(T.updated.replace("%s", timeStr));
    updatedText.font = Font.systemFont(9);
    updatedText.textOpacity = 0.4;

    widget.addSpacer(2);

    const main = widget.addStack();
    main.layoutHorizontally();
    if (bus.mins <= 60) {
      const minsText = main.addText(`${bus.mins} ${T.min}`);
      minsText.font = Font.boldSystemFont(26);
      main.addSpacer(4);
      const timeText = main.addText(bus.time);
      timeText.font = Font.systemFont(14);
      timeText.textOpacity = 0.7;
    } else {
      const timeText = main.addText(bus.time);
      timeText.font = Font.boldSystemFont(26);
      main.addSpacer(4);
      const hrs = (bus.mins / 60).toFixed(1).replace(/\.0$/, "");
      const hrsText = main.addText(T.inHrs.replace("%s", hrs));
      hrsText.font = Font.systemFont(12);
      hrsText.textOpacity = 0.5;
    }

    widget.addSpacer(2);

    const dest = widget.addStack();
    const destLabel = resolvedKey === "asr" ? `→ ${bus.dest}` : "→ 🏠 ASR";
    const destText = dest.addText(destLabel);
    destText.font = Font.systemFont(11);
    destText.textOpacity = 0.7;

    if (result.buses.length > 1) {
      const next = result.buses[1];
      const nextRow = widget.addStack();
      const nextLabel = resolvedKey === "asr" ? `${T.next} ${next.time} → ${next.dest}` : `${T.next} ${next.time}`;
      const nextText = nextRow.addText(nextLabel);
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
    row.addText(T.noSunServiceDetail);
    table.addRow(row);
  } else if (result.noMoreBus) {
    const row = new UITableRow();
    row.addText(T.noMoreBusDetail);
    table.addRow(row);
  } else {
    for (const bus of result.buses) {
      const row = new UITableRow();
      const label = resolvedKey === "asr" ? `→ ${bus.dest}` : "";
      const duration = bus.mins <= 60
        ? `${bus.mins} ${T.min}`
        : T.inHrs.replace("%s", (bus.mins / 60).toFixed(1).replace(/\.0$/, ""));
      row.addText(`${bus.time} (${duration}) ${label}`);
      table.addRow(row);
    }
  }

  const infoRow = new UITableRow();
  infoRow.addText(T.widgetParam, T.setInConfig);
  table.addRow(infoRow);

  await table.present();
}
