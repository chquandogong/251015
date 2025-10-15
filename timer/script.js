const translations = {
  ko: {
    title: "세계 시각 타이머",
    instructions: "주요 도시를 클릭하여 타임존을 변경하세요.",
    timezoneLabel: (zone, offset) => `타임존 • ${zone} (GMT${offset})`,
    ampm: { am: "AM", pm: "PM" },
    formatDate: (date) => {
      const dayNames = ["일", "월", "화", "수", "목", "금", "토"];
      const year = date.getFullYear();
      const month = String(date.getMonth() + 1).padStart(2, "0");
      const day = String(date.getDate()).padStart(2, "0");
      const weekday = dayNames[date.getDay()];
      return `${year}년 ${month}월 ${day}일 (${weekday})`;
    },
  },
  en: {
    title: "World Pulse Timer",
    instructions: "Tap a major city to shift the timezone.",
    timezoneLabel: (zone, offset) => `TIMEZONE • ${zone} (GMT${offset})`,
    ampm: { am: "AM", pm: "PM" },
    formatDate: (date) =>
      new Intl.DateTimeFormat("en-US", {
        weekday: "short",
        month: "short",
        day: "2-digit",
        year: "numeric",
      }).format(date),
  },
};

const cities = [
  {
    id: "seoul",
    timeZone: "Asia/Seoul",
    labels: { ko: "서울", en: "Seoul" },
    position: { left: "74%", top: "46%" },
  },
  {
    id: "tokyo",
    timeZone: "Asia/Tokyo",
    labels: { ko: "도쿄", en: "Tokyo" },
    position: { left: "78%", top: "49%" },
  },
  {
    id: "dubai",
    timeZone: "Asia/Dubai",
    labels: { ko: "두바이", en: "Dubai" },
    position: { left: "62%", top: "55%" },
  },
  {
    id: "london",
    timeZone: "Europe/London",
    labels: { ko: "런던", en: "London" },
    position: { left: "48%", top: "40%" },
  },
  {
    id: "newyork",
    timeZone: "America/New_York",
    labels: { ko: "뉴욕", en: "New York" },
    position: { left: "31%", top: "43%" },
  },
  {
    id: "losangeles",
    timeZone: "America/Los_Angeles",
    labels: { ko: "LA", en: "Los Angeles" },
    position: { left: "23%", top: "45%" },
  },
  {
    id: "sydney",
    timeZone: "Australia/Sydney",
    labels: { ko: "시드니", en: "Sydney" },
    position: { left: "86%", top: "76%" },
  },
];

const state = {
  language: "ko",
  timeZone: "Asia/Seoul",
};

const elements = {};
const cityElements = new Map();

let rafId = null;
let lastSecond = null;

function init() {
  cacheElements();
  createCityMarkers();
  bindEvents();
  updateLanguage();
  startClock();
}

function cacheElements() {
  elements.title = document.getElementById("title");
  elements.languageToggle = document.getElementById("languageToggle");
  elements.timeDisplay = document.getElementById("timeDisplay");
  elements.timeValue = document.getElementById("timeValue");
  elements.ampm = document.getElementById("ampm");
  elements.millis = document.getElementById("millis");
  elements.dateLine = document.getElementById("dateLine");
  elements.timezoneLabel = document.getElementById("timezoneLabel");
  elements.map = document.getElementById("map");
  elements.mapInstructions = document.getElementById("mapInstructions");
}

function createCityMarkers() {
  if (!elements.map) {
    return;
  }

  cities.forEach((city) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "city-marker";
    button.style.left = city.position.left;
    button.style.top = city.position.top;
    button.dataset.timeZone = city.timeZone;
    button.dataset.cityId = city.id;
    button.innerHTML = `
      <span class="marker-glow"></span>
      <span class="city-label">${city.labels[state.language]}</span>
    `;
    button.addEventListener("click", () => setTimeZone(city.timeZone));
    elements.map.appendChild(button);
    cityElements.set(city.id, button);
  });
}

function bindEvents() {
  elements.languageToggle?.addEventListener("click", toggleLanguage);
}

function startClock() {
  if (rafId) {
    cancelAnimationFrame(rafId);
  }

  const loop = () => {
    updateClock();
    rafId = requestAnimationFrame(loop);
  };

  loop();
}

function toggleLanguage() {
  state.language = state.language === "ko" ? "en" : "ko";
  updateLanguage();
}

function updateLanguage() {
  const lang = state.language;
  const t = translations[lang];

  document.documentElement.lang = lang;
  elements.title.textContent = t.title;
  elements.mapInstructions.textContent = t.instructions;
  elements.languageToggle.textContent = lang === "ko" ? "English" : "한국어";
  updateCityMarkers(new Date());
}

function setTimeZone(timeZone) {
  if (state.timeZone === timeZone) {
    return;
  }
  state.timeZone = timeZone;
  updateCityMarkers(new Date());
}

function updateClock() {
  const now = new Date();
  const { zonedDate, offsetMinutes } = convertToTimeZone(now, state.timeZone);

  const hours24 = zonedDate.getHours();
  const minutes = zonedDate.getMinutes();
  const seconds = zonedDate.getSeconds();
  const millis = zonedDate.getMilliseconds();

  const hours12 = hours24 % 12 || 12;
  const ampmKey = hours24 >= 12 ? "pm" : "am";

  elements.timeValue.textContent = `${pad(hours12)}:${pad(minutes)}:${pad(
    seconds
  )}`;
  elements.ampm.textContent = translations[state.language].ampm[ampmKey];
  elements.millis.textContent = `.${String(millis).padStart(3, "0")}`;
  elements.dateLine.textContent = translations[state.language].formatDate(
    zonedDate
  );
  elements.timezoneLabel.textContent = translations[
    state.language
  ].timezoneLabel(state.timeZone, formatOffset(offsetMinutes));

  if (seconds !== lastSecond) {
    triggerTickAnimation();
    updateCityMarkers(now);
    lastSecond = seconds;
  }
}

function triggerTickAnimation() {
  elements.timeDisplay.classList.remove("tick");
  // Force reflow to restart animation.
  void elements.timeDisplay.offsetWidth;
  elements.timeDisplay.classList.add("tick");
}

function updateCityMarkers(referenceDate) {
  cityElements.forEach((button, cityId) => {
    const city = cities.find((item) => item.id === cityId);
    if (!city) {
      return;
    }
    const { zonedDate } = convertToTimeZone(referenceDate, city.timeZone);
    const hour = zonedDate.getHours();
    const isDay = hour >= 6 && hour < 18;
    button.classList.toggle("day", isDay);
    button.classList.toggle("night", !isDay);
    button.classList.toggle("active", city.timeZone === state.timeZone);

    const label = button.querySelector(".city-label");
    if (label) {
      const icon = isDay ? "☀" : "🌙";
      label.textContent = `${city.labels[state.language]} ${icon}`;
    }
  });
}

function convertToTimeZone(date, timeZone) {
  const offsetMinutes = getOffsetMinutes(timeZone, date);
  const utcTime = date.getTime() + date.getTimezoneOffset() * 60000;
  const zonedTime = new Date(utcTime + offsetMinutes * 60000);
  return { zonedDate: zonedTime, offsetMinutes };
}

function getOffsetMinutes(timeZone, date) {
  try {
    const formatter = new Intl.DateTimeFormat("en-US", {
      hour: "2-digit",
      timeZone,
      timeZoneName: "shortOffset",
    });
    const parts = formatter.formatToParts(date);
    const zonePart = parts.find((part) => part.type === "timeZoneName");

    if (zonePart) {
      const match = zonePart.value.match(/GMT([+-]\d{1,2})(?::?(\d{2}))?/);
      if (match) {
        const sign = match[1].startsWith("-") ? -1 : 1;
        const hours = parseInt(match[1].replace(/[+-]/, ""), 10);
        const minutes = match[2] ? parseInt(match[2], 10) : 0;
        return sign * (hours * 60 + minutes);
      }
    }
  } catch (error) {
    console.error("Failed to resolve timezone offset", { timeZone, error });
  }
  return 0;
}

function formatOffset(minutes) {
  const sign = minutes >= 0 ? "+" : "-";
  const absolute = Math.abs(minutes);
  const hours = String(Math.floor(absolute / 60)).padStart(2, "0");
  const mins = String(absolute % 60).padStart(2, "0");
  return `${sign}${hours}:${mins}`;
}

function pad(value) {
  return String(value).padStart(2, "0");
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", init);
} else {
  init();
}
