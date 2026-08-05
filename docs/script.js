async function loadReport() {
  const dateEl = document.getElementById("board-date");
  const tableBody = document.querySelector("#board-table tbody");
  const tickerTrack = document.getElementById("ticker-track");
  const lastUpdated = document.getElementById("last-updated");

  try {
    const res = await fetch("data/latest.json", { cache: "no-store" });
    if (!res.ok) throw new Error("no data");
    const data = await res.json();

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
        <td>${r.item}</td>
        <td>${r.content}</td>
        <td class="cell-status ${r.statusClass}">${r.status}</td>
      </tr>`
      )
      .join("");

    tickerTrack.textContent = data.line_message || "今天沒有推播內容。";

    lastUpdated.textContent = `最後更新 LAST UPDATED: ${data.date || "--"}`;
  } catch (err) {
    tableBody.innerHTML = `
      <tr class="board-row">
        <td colspan="4">尚未有晨報資料 NO DATA YET</td>
      </tr>`;
    tickerTrack.textContent = "晨報系統尚未產生過內容。";
  }
}

loadReport();
