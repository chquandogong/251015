const dayNames = ["일", "월", "화", "수", "목", "금", "토"];

/**
 * Updates the clock and date labels with the current local time.
 */
function renderClock() {
  const now = new Date();
  const hours = String(now.getHours()).padStart(2, "0");
  const minutes = String(now.getMinutes()).padStart(2, "0");
  const seconds = String(now.getSeconds()).padStart(2, "0");

  const month = String(now.getMonth() + 1).padStart(2, "0");
  const date = String(now.getDate()).padStart(2, "0");
  const day = dayNames[now.getDay()];

  const clockEl = document.getElementById("clock");
  const dateEl = document.getElementById("date");

  if (clockEl) {
    clockEl.textContent = `${hours}:${minutes}:${seconds}`;
  }

  if (dateEl) {
    dateEl.textContent = `${month}월 ${date}일 (${day})`;
  }
}

function startClock() {
  renderClock();
  setInterval(renderClock, 1000);
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", startClock);
} else {
  startClock();
}
