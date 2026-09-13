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

async function loadReport() {
  const dateEl = document.getElementById("board-date");
  const tableBody = document.querySelector("#board-table tbody");
  const tickerTrack = document.getElementById("ticker-track");
  const lastUpdated = document.getElementById("last-updated");

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
    tableBody.innerHTML = `
      <tr class="board-row">
        <td colspan="4">尚未有這天的晨報資料 NO DATA</td>
      </tr>`;
    tickerTrack.textContent = "找不到這天的晨報內容。";
    return;
  }

  dateEl.textContent = data.date || "----/--/--";

  const rows = [];
  let no = 1;

  rows.push({
    no: no++,
    item: "問候 GREETING",
    content: data.greeting || "",
    status: "準時 ON TIME",
    statusClass: "cell-status--ontime",
  });

  rows.push({
    no: no++,
    item: "今日行程 SCHEDULE",
    content: data.schedule_summary || "",
    status: "準時 ON TIME",
    statusClass: "cell-status--ontime",
  });

  (data.habit_highlights || []).forEach((h) => {
    rows.push({
      no: no++,
      item: "自我提升 TRACKING",
      content: h,
      status: "追蹤中 TRACKING",
      statusClass: "cell-status--tracking",
    });
  });

  if (data.links_highlight) {
    rows.push({
      no: no++,
      item: "收藏連結 LINKS",
      content: data.links_highlight,
      status: "待閱讀 UNREAD",
      statusClass: "cell-status--tracking",
    });
  }

  (data.recommendations || []).forEach((r) => {
    rows.push({
      no: no++,
      item: "推薦 RECOMMENDED",
      content: r,
      status: "新內容 NEW",
      statusClass: "cell-status--ontime",
    });
  });

  if (data.closing_note) {
    rows.push({
      no: no++,
      item: "收尾 CLOSING",
      content: data.closing_note,
      status: "完成 DONE",
      statusClass: "cell-status--done",
    });
  }

  tableBody.innerHTML = rows
    .map(
      (r) => `
    <tr class="board-row">
      <td class="cell-no">${String(r.no).padStart(2, "0")}</td>
      <td>${escapeHtml(r.item)}</td>
      <td>${escapeHtml(r.content)}</td>
      <td class="cell-status ${r.statusClass}">${escapeHtml(r.status)}</td>
    </tr>`
    )
    .join("");

  tickerTrack.textContent = data.ticker_message || "今天沒有推播內容。";

  lastUpdated.textContent = `最後更新 LAST UPDATED: ${data.date || "--"}`;
}

loadReport();
