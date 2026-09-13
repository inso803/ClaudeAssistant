function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str ?? "";
  return div.innerHTML;
}

function getRequestedDate() {
  return new URLSearchParams(window.location.search).get("date");
}

function setRequestedDate(dateStr) {
  const url = new URL(window.location.href);
  if (dateStr) {
    url.searchParams.set("date", dateStr);
  } else {
    url.searchParams.delete("date");
  }
  window.location.href = url.toString();
}

async function loadManifest() {
  try {
    const res = await fetch("data/manifest.json", { cache: "no-store" });
    if (!res.ok) throw new Error("no manifest");
    const data = await res.json();
    return data.dates || [];
  } catch (err) {
    return [];
  }
}

function renderNav(dates, currentDate) {
  const select = document.getElementById("nav-history");
  const prevBtn = document.getElementById("nav-prev");
  const nextBtn = document.getElementById("nav-next");
  const latestBtn = document.getElementById("nav-latest");

  select.innerHTML = dates
    .map((d) => `<option value="${d}" ${d === currentDate ? "selected" : ""}>${d}</option>`)
    .join("");
  select.onchange = () => setRequestedDate(select.value);

  // dates 是新到舊排序；「前一天」= 陣列中下一筆（更舊），「後一天」= 上一筆（更新）
  const idx = dates.indexOf(currentDate);
  const older = idx >= 0 ? dates[idx + 1] : undefined;
  const newer = idx > 0 ? dates[idx - 1] : undefined;

  prevBtn.disabled = !older;
  prevBtn.onclick = () => older && setRequestedDate(older);

  nextBtn.disabled = !newer;
  nextBtn.onclick = () => setRequestedDate(newer || null);

  latestBtn.onclick = () => setRequestedDate(null);
}

const WEEKDAYS = ["日", "一", "二", "三", "四", "五", "六"];

function formatDateline(dateStr) {
  const d = new Date(`${dateStr}T00:00:00`);
  if (Number.isNaN(d.getTime())) return dateStr;
  return `${d.getFullYear()} 年 ${d.getMonth() + 1} 月 ${d.getDate()} 日 星期${WEEKDAYS[d.getDay()]}`;
}

function show(el) {
  el.hidden = false;
}
function hide(el) {
  el.hidden = true;
}

function renderWeather(data) {
  const el = document.getElementById("dateline-weather");
  const textEl = document.getElementById("dateline-weather-text");
  const w = data.weather;
  if (!w || !w.city) {
    hide(el);
    return;
  }
  textEl.textContent = `${w.city}　${w.summary}　${w.low}–${w.high}°　降雨 ${w.rain_pct}%`;
  show(el);
}

function renderSchedule(data) {
  const section = document.getElementById("section-schedule");
  const list = document.getElementById("schedule-list");
  const fallback = document.getElementById("schedule-note");

  const schedule = Array.isArray(data.schedule) ? data.schedule : [];
  if (schedule.length) {
    list.innerHTML = schedule
      .map(
        (ev) => `
      <div class="schedule-row">
        <span class="schedule-time${ev.highlight ? " is-highlight" : ""}">${escapeHtml(ev.time || "")}</span>
        <div>
          <div class="schedule-title">${escapeHtml(ev.title || "")}</div>
          <div class="schedule-meta">${escapeHtml(ev.meta || "")}</div>
        </div>
      </div>`
      )
      .join("");
    hide(fallback);
    show(section);
    return;
  }

  if (data.schedule_summary) {
    list.innerHTML = `<p class="schedule-fallback">${escapeHtml(data.schedule_summary)}</p>`;
    hide(fallback);
    show(section);
    return;
  }

  hide(section);
}

function renderTodoSection(sectionId, listId, todos) {
  const section = document.getElementById(sectionId);
  const list = document.getElementById(listId);
  if (!Array.isArray(todos) || !todos.length) {
    hide(section);
    return;
  }
  list.innerHTML = todos
    .map(
      (label) => `
    <div class="todo-row">
      <span class="todo-mark">□</span>
      <span class="todo-label">${escapeHtml(label)}</span>
    </div>`
    )
    .join("");
  show(section);
}

function renderInbox(data) {
  const section = document.getElementById("section-inbox");
  const list = document.getElementById("inbox-list");
  const inbox = Array.isArray(data.inbox) ? data.inbox : [];
  if (!inbox.length) {
    hide(section);
    return;
  }
  list.innerHTML = inbox
    .map(
      (m) => `
    <div class="inbox-item">
      <div class="inbox-head">
        <span class="inbox-from">${escapeHtml(m.from || "")}</span>
        <span class="inbox-when">${escapeHtml(m.when || "")}</span>
      </div>
      <div class="inbox-text">${escapeHtml(m.text || "")}</div>
    </div>`
    )
    .join("");
  show(section);
}

function renderReading(data) {
  const section = document.getElementById("section-reading");
  const list = document.getElementById("reading-list");
  const items = Array.isArray(data.recommendations) ? data.recommendations : [];

  if (!items.length) {
    hide(section);
    return;
  }

  const isRich = typeof items[0] === "object" && items[0] !== null;

  if (!isRich) {
    list.innerHTML = items.map((text) => `<p class="reading-simple">${escapeHtml(text)}</p>`).join("");
    show(section);
    return;
  }

  list.innerHTML = items
    .map((item) => {
      const url = item.url || "#";
      const thumb = item.thumbnail
        ? `<img src="${escapeHtml(item.thumbnail)}" alt="" loading="lazy" />`
        : `<span class="reading-thumb-placeholder">縮圖</span>`;
      return `
      <div class="reading-item">
        <div class="reading-main">
          <div class="reading-head">
            <span class="tag tag-accent reading-tag">${escapeHtml(item.source || "")}</span>
            <span class="reading-meta">${escapeHtml(item.meta || "")}</span>
          </div>
          <a class="reading-title" href="${escapeHtml(url)}" target="_blank" rel="noopener">${escapeHtml(item.title || "")}</a>
          <p class="reading-lede">${escapeHtml(item.lede || "")}</p>
          ${item.body ? `<p class="reading-body">${escapeHtml(item.body)}</p>` : ""}
          <a class="reading-source-link" href="${escapeHtml(url)}" target="_blank" rel="noopener">閱讀原文 ↗</a>
        </div>
        <a class="reading-thumb halftone" href="${escapeHtml(url)}" target="_blank" rel="noopener">${thumb}</a>
      </div>`;
    })
    .join("");

  show(section);
}

function renderStats(data) {
  const section = document.getElementById("section-stats");
  const row = document.getElementById("stats-row");
  const note = document.getElementById("stats-note");

  const stats = Array.isArray(data.stats) ? data.stats : [];
  const highlights = Array.isArray(data.habit_highlights) ? data.habit_highlights : [];

  if (!stats.length && !highlights.length) {
    hide(section);
    return;
  }

  row.innerHTML = stats
    .map(
      (s) => `
    <div>
      <div class="stat-value tone-${escapeHtml(s.tone || "plain")}">${escapeHtml(s.value)}</div>
      <div class="stat-label">${escapeHtml(s.label)}</div>
    </div>`
    )
    .join("");

  note.innerHTML = highlights.map((h) => `<p>${escapeHtml(h)}</p>`).join("");

  show(section);
}

async function loadReport() {
  const dateEl = document.getElementById("dateline-date");
  const issueEl = document.getElementById("dateline-issue");
  const greetingEl = document.getElementById("greeting");
  const greetingSubEl = document.getElementById("greeting-sub");
  const closingSection = document.getElementById("section-closing");
  const closingTextEl = document.getElementById("closing-text");

  const requestedDate = getRequestedDate();
  const dataFile = requestedDate ? `data/${requestedDate}.json` : "data/latest.json";

  const manifestDates = await loadManifest();
  let data = null;
  try {
    const res = await fetch(dataFile, { cache: "no-store" });
    if (!res.ok) throw new Error("no data");
    data = await res.json();
  } catch (err) {
    data = null;
  }

  if (manifestDates.length) {
    renderNav(manifestDates, requestedDate || (data && data.date) || manifestDates[0]);
  }

  if (!data) {
    greetingEl.textContent = "尚未有這天的晨報資料。";
    return;
  }

  dateEl.textContent = formatDateline(data.date);
  if (data.issue_no) {
    issueEl.textContent = `第 ${data.issue_no} 期`;
    show(issueEl);
  } else {
    hide(issueEl);
  }

  greetingEl.textContent = data.greeting || "";
  if (data.greeting_sub) {
    greetingSubEl.textContent = data.greeting_sub;
    show(greetingSubEl);
  } else {
    hide(greetingSubEl);
  }

  renderWeather(data);
  renderSchedule(data);
  renderTodoSection("section-todo-today", "todo-today-list", data.todos);
  renderTodoSection("section-todo-longterm", "todo-longterm-list", data.todos_longterm);
  renderInbox(data);
  renderReading(data);
  renderStats(data);

  if (data.closing_note) {
    closingTextEl.textContent = data.closing_note;
    show(closingSection);
  } else {
    hide(closingSection);
  }
}

loadReport();
