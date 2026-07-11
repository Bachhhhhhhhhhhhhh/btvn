/* Doraemon LOG Dashboard — clean JS (no minified one-liners) */
/* global Chart, DATA */

const periods = DATA.meta.periods;
const colors = [
  "#00A0E9", "#E60012", "#FFD54F", "#7C4DFF",
  "#26A69A", "#FF8A65", "#42A5F5", "#EC407A", "#66BB6A",
];

let charts = {};
let focusPeriod = periods[0];
let assetDetailChart = null;
let assetSort = { key: "cost", dir: -1 };
let favs = new Set(JSON.parse(localStorage.getItem("dora_favs") || "[]"));
let helperIdx = 0;

const tips = [
  "Bấm chuông 🔔 để nghe ting-a-ling và nhận mẹo ngẫu nhiên!",
  "Dùng Compare để soi 2 kỳ khi thuyết trình — rất gọn.",
  "Gắn ⭐ asset quan trọng, xem lại ở Favorites.",
  "Lọc Ending ≤24m để thấy TS sắp hết khấu hao.",
  "Export CSV mang bảng budget sang Excel trong 1 nốt nhạc.",
  "Night mode xem ban đêm cũng dễ chịu 🌙",
  ...(DATA.insights || []),
];

function bn(v) {
  if (v == null || isNaN(v)) return "—";
  const n = Number(v);
  const a = Math.abs(n);
  if (a >= 1e12) return (n / 1e12).toFixed(2) + "T";
  if (a >= 1e9) return (n / 1e9).toFixed(2) + "B";
  if (a >= 1e6) return (n / 1e6).toFixed(2) + "M";
  if (a >= 1e3) return (n / 1e3).toFixed(1) + "K";
  return n.toLocaleString("en-US", { maximumFractionDigits: 0 });
}

function full(v) {
  if (v == null || isNaN(v)) return "—";
  return Number(v).toLocaleString("en-US", { maximumFractionDigits: 0 });
}

function toast(msg) {
  const el = document.getElementById("toast");
  el.textContent = msg;
  el.classList.add("show");
  setTimeout(() => el.classList.remove("show"), 2400);
}

function destroy(key) {
  if (charts[key]) {
    charts[key].destroy();
    delete charts[key];
  }
}

function gVal(p) {
  return DATA.kpi.grand?.[p] ?? DATA.kpi.byPeriod[p] ?? 0;
}

function saveFavs() {
  localStorage.setItem("dora_favs", JSON.stringify([...favs]));
}

function ringBell() {
  try {
    const ctx = new (window.AudioContext || window.webkitAudioContext)();
    const o = ctx.createOscillator();
    const g = ctx.createGain();
    o.type = "sine";
    o.frequency.value = 880;
    g.gain.value = 0.04;
    o.connect(g);
    g.connect(ctx.destination);
    o.start();
    o.frequency.exponentialRampToValueAtTime(1320, ctx.currentTime + 0.08);
    g.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.35);
    o.stop(ctx.currentTime + 0.36);
  } catch (e) {
    /* ignore */
  }
}

Chart.defaults.color = "#5A7A94";
Chart.defaults.borderColor = "rgba(0,160,233,.12)";
Chart.defaults.font.family = "'Nunito', system-ui, sans-serif";

function initSelects() {
  ["periodFocus", "cmpA", "cmpB"].forEach((id) => {
    const sel = document.getElementById(id);
    if (!sel || sel.options.length) return;
    periods.forEach((p) => {
      const o = document.createElement("option");
      o.value = p;
      o.textContent = p;
      sel.appendChild(o);
    });
  });
  document.getElementById("periodFocus").value = focusPeriod;
  document.getElementById("cmpA").value = periods[0];
  document.getElementById("cmpB").value = periods[1] || periods[0];
  document.getElementById("periodFocus").onchange = () => {
    focusPeriod = document.getElementById("periodFocus").value;
    renderAll(false);
    toast("Focus: " + focusPeriod + " 🔔");
  };
  document.getElementById("cmpA").onchange = renderCompare;
  document.getElementById("cmpB").onchange = renderCompare;
}

function renderKPI() {
  const gF = gVal(focusPeriod);
  const g103 = gVal("103Ki");
  const idx = periods.indexOf(focusPeriod);
  const prev = idx > 0 ? gVal(periods[idx - 1]) : null;
  const gap = prev == null ? 0 : gF - prev;
  const sc = DATA.kpi.statusCounts || {};
  const items = [
    { l: "Focus KH", v: bn(gF), h: focusPeriod + " · " + full(gF), c: "" },
    { l: "103KI baseline", v: bn(g103), h: full(g103) + " VND", c: "" },
    { l: "MT total", v: bn(DATA.kpi.totalMT), h: "103–108 sum", c: "" },
    {
      l: "GAP vs prior",
      v: (gap >= 0 ? "+" : "") + bn(gap),
      h: prev == null ? "First period" : full(gap),
      c: gap > 0 ? "pos" : gap < 0 ? "neg" : "",
    },
    {
      l: "Assets",
      v: String(DATA.kpi.assetCount),
      h: "🟡 " + (sc.ending_soon || 0) + " ending soon",
      c: "",
    },
    {
      l: "Acquisition",
      v: bn(DATA.kpi.totalAcquisition),
      h: "Nguyên giá portfolio",
      c: "",
    },
  ];
  document.getElementById("kpiGrid").innerHTML = items
    .map(
      (i) =>
        `<div class="kpi"><div class="kpi-label">${i.l}</div>` +
        `<div class="kpi-value mono ${i.c}">${i.v}</div>` +
        `<div class="kpi-hint">${i.h}</div></div>`
    )
    .join("");
}

function renderInsights() {
  const el = document.getElementById("insightChips");
  if (!el) return;
  const emojis = ["💡", "📌", "✨", "🔔", "🎯"];
  el.innerHTML = (DATA.insights || [])
    .map(
      (t, i) =>
        `<div class="chip"><span class="emoji">${emojis[i % 5]}</span><span>${t}</span></div>`
    )
    .join("");
}

function renderPeriod() {
  destroy("period");
  const vals = periods.map(gVal);
  charts.period = new Chart(document.getElementById("chartPeriod"), {
    type: "bar",
    data: {
      labels: periods,
      datasets: [
        {
          data: vals,
          backgroundColor: periods.map((p) =>
            p === focusPeriod ? "#00A0E9" : "rgba(0,160,233,.32)"
          ),
          borderRadius: 14,
          borderSkipped: false,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      onClick: (_, els) => {
        if (!els.length) return;
        focusPeriod = periods[els[0].index];
        document.getElementById("periodFocus").value = focusPeriod;
        renderAll(false);
        toast("Focus: " + focusPeriod);
      },
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: { label: (c) => " " + full(c.raw) + " VND" },
        },
      },
      scales: {
        x: { grid: { display: false }, ticks: { font: { weight: "800" } } },
        y: {
          ticks: { callback: (v) => bn(v) },
          grid: { color: "rgba(0,160,233,.08)" },
        },
      },
    },
  });
}

function renderWaterfall() {
  destroy("wf");
  const wf = DATA.waterfall || [];
  const labels = wf.map((x) => x.label);
  const base = [];
  const mid = [];
  const cols = [];
  let run = 0;
  wf.forEach((s) => {
    if (s.type === "total") {
      base.push(0);
      mid.push(s.value);
      cols.push("#00A0E9");
      run = s.value;
    } else if (s.value >= 0) {
      base.push(run);
      mid.push(s.value);
      cols.push("#26A69A");
      run += s.value;
    } else {
      base.push(run + s.value);
      mid.push(-s.value);
      cols.push("#E60012");
      run += s.value;
    }
  });
  charts.wf = new Chart(document.getElementById("chartWaterfall"), {
    type: "bar",
    data: {
      labels,
      datasets: [
        {
          data: base,
          backgroundColor: "transparent",
          stack: "w",
          barPercentage: 0.72,
        },
        {
          data: mid,
          backgroundColor: cols,
          stack: "w",
          borderRadius: 8,
          barPercentage: 0.72,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          filter: (item) => item.datasetIndex === 1,
          callbacks: {
            label: (c) => {
              const s = wf[c.dataIndex];
              if (s.type === "delta") {
                return " " + (s.value >= 0 ? "+" : "") + full(s.value);
              }
              return " " + full(s.value);
            },
          },
        },
      },
      scales: {
        x: {
          stacked: true,
          grid: { display: false },
          ticks: { font: { size: 10, weight: "800" } },
        },
        y: {
          stacked: true,
          ticks: { callback: (v) => bn(v) },
          grid: { color: "rgba(0,160,233,.08)" },
        },
      },
    },
  });
}

function sumBy(field, period) {
  const m = {};
  DATA.budgetRows.forEach((r) => {
    m[r[field]] = (m[r[field]] || 0) + (r.values[period] || 0);
  });
  return m;
}

function makeDoughnut(canvasId, map, chartKey) {
  const labels = Object.keys(map);
  const vals = labels.map((k) => map[k]);
  const total = vals.reduce((a, b) => a + b, 0) || 1;
  charts[chartKey] = new Chart(document.getElementById(canvasId), {
    type: "doughnut",
    data: {
      labels,
      datasets: [
        {
          data: vals,
          backgroundColor: colors,
          borderWidth: 4,
          borderColor: "#fff",
          hoverOffset: 7,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      cutout: "58%",
      plugins: {
        legend: {
          position: "bottom",
          labels: { boxWidth: 12, font: { weight: "800", size: 11 } },
        },
        tooltip: {
          callbacks: {
            label: (c) => {
              const pct = ((c.raw / total) * 100).toFixed(1);
              return " " + c.label + ": " + bn(c.raw) + " (" + pct + "%)";
            },
          },
        },
      },
    },
  });
}

function renderPies() {
  destroy("cc");
  destroy("gl");
  document.getElementById("descCC").textContent = "Share · " + focusPeriod;
  document.getElementById("descGL").textContent = "Class · " + focusPeriod;
  makeDoughnut("chartCC", sumBy("ccName", focusPeriod), "cc");
  makeDoughnut("chartGL", sumBy("glName", focusPeriod), "gl");
}

function renderStack() {
  destroy("stack");
  const ccs = Object.keys(DATA.byCC);
  charts.stack = new Chart(document.getElementById("chartCCstack"), {
    type: "bar",
    data: {
      labels: periods,
      datasets: ccs.map((cc, i) => ({
        label: cc,
        data: periods.map((p) => DATA.byCC[cc][p] || 0),
        backgroundColor: colors[i % colors.length],
        stack: "s",
        borderRadius: 4,
      })),
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: "bottom",
          labels: { boxWidth: 10, font: { weight: "800", size: 10 } },
        },
        tooltip: {
          callbacks: {
            label: (c) => " " + c.dataset.label + ": " + bn(c.raw),
          },
        },
      },
      scales: {
        x: { stacked: true, grid: { display: false } },
        y: {
          stacked: true,
          ticks: { callback: (v) => bn(v) },
          grid: { color: "rgba(0,160,233,.08)" },
        },
      },
    },
  });
}

function renderGap() {
  destroy("gap");
  const gaps = [];
  for (let i = 1; i < periods.length; i++) {
    gaps.push(gVal(periods[i]) - gVal(periods[i - 1]));
  }
  charts.gap = new Chart(document.getElementById("chartGap"), {
    type: "bar",
    data: {
      labels: periods.slice(1).map((p, i) => p + " vs " + periods[i]),
      datasets: [
        {
          data: gaps,
          backgroundColor: gaps.map((v) =>
            v >= 0 ? "#26A69A" : "#E60012"
          ),
          borderRadius: 12,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: { label: (c) => " " + full(c.raw) },
        },
      },
      scales: {
        x: { grid: { display: false }, ticks: { font: { weight: "800" } } },
        y: {
          ticks: { callback: (v) => bn(v) },
          grid: { color: "rgba(0,160,233,.08)" },
        },
      },
    },
  });
}

function renderMonthly() {
  destroy("mTot");
  destroy("mCC");
  destroy("mGL");

  charts.mTot = new Chart(document.getElementById("chartMonthly"), {
    type: "line",
    data: {
      labels: DATA.monthly.labels,
      datasets: [
        {
          data: DATA.monthly.total,
          borderColor: "#00A0E9",
          backgroundColor: "rgba(0,160,233,.16)",
          fill: true,
          tension: 0.4,
          pointRadius: 4,
          pointBackgroundColor: "#FFD54F",
          pointBorderColor: "#00A0E9",
          pointBorderWidth: 2,
          borderWidth: 3,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: { label: (c) => " " + full(c.raw) },
        },
      },
      scales: {
        x: { grid: { display: false } },
        y: {
          ticks: { callback: (v) => bn(v) },
          grid: { color: "rgba(0,160,233,.08)" },
        },
      },
    },
  });

  const byCC = {};
  DATA.monthly.rows.forEach((r) => {
    if (!byCC[r.ccName]) byCC[r.ccName] = DATA.monthly.labels.map(() => 0);
    r.months.forEach((v, i) => {
      byCC[r.ccName][i] += v;
    });
  });
  charts.mCC = new Chart(document.getElementById("chartMonthlyCC"), {
    type: "line",
    data: {
      labels: DATA.monthly.labels,
      datasets: Object.keys(byCC).map((k, i) => ({
        label: k,
        data: byCC[k],
        borderColor: colors[i % colors.length],
        tension: 0.4,
        pointRadius: 3,
        borderWidth: 3,
        backgroundColor: "transparent",
      })),
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: "bottom",
          labels: { boxWidth: 12, font: { weight: "800" } },
        },
        tooltip: {
          callbacks: {
            label: (c) => " " + c.dataset.label + ": " + bn(c.raw),
          },
        },
      },
      scales: {
        x: { grid: { display: false } },
        y: {
          ticks: { callback: (v) => bn(v) },
          grid: { color: "rgba(0,160,233,.08)" },
        },
      },
    },
  });

  const byGL = {};
  DATA.monthly.rows.forEach((r) => {
    if (!byGL[r.glName]) byGL[r.glName] = DATA.monthly.labels.map(() => 0);
    r.months.forEach((v, i) => {
      byGL[r.glName][i] += v;
    });
  });
  charts.mGL = new Chart(document.getElementById("chartMonthlyGL"), {
    type: "bar",
    data: {
      labels: DATA.monthly.labels,
      datasets: Object.keys(byGL).map((k, i) => ({
        label: k,
        data: byGL[k],
        backgroundColor: colors[i % colors.length],
        stack: "m",
        borderRadius: 4,
      })),
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: "bottom",
          labels: { boxWidth: 10, font: { weight: "800", size: 10 } },
        },
        tooltip: {
          callbacks: {
            label: (c) => " " + c.dataset.label + ": " + bn(c.raw),
          },
        },
      },
      scales: {
        x: { stacked: true, grid: { display: false } },
        y: {
          stacked: true,
          ticks: { callback: (v) => bn(v) },
          grid: { color: "rgba(0,160,233,.08)" },
        },
      },
    },
  });
}

function renderHeatmap() {
  const rows = DATA.heatmap || [];
  let max = 1;
  rows.forEach((r) =>
    r.values.forEach((v) => {
      if (v > max) max = v;
    })
  );
  const header =
    '<div class="h"></div>' +
    periods.map((p) => '<div class="h">' + p + "</div>").join("");
  const body = rows
    .map((r) => {
      const cells = r.values
        .map((v) => {
          const t = max ? v / max : 0;
          const bg = "rgba(0,160,233," + (0.12 + t * 0.88).toFixed(3) + ")";
          const col = t > 0.45 ? "#fff" : "#005A9E";
          return (
            '<div class="c" style="background:' +
            bg +
            ";color:" +
            col +
            '" title="' +
            full(v) +
            '">' +
            bn(v) +
            "</div>"
          );
        })
        .join("");
      return (
        '<div class="r" title="' +
        r.key +
        '">' +
        r.key +
        "</div>" +
        cells
      );
    })
    .join("");
  document.getElementById("heatMap").innerHTML = header + body;
}

function renderMovers() {
  const up = DATA.moversUp || [];
  const down = DATA.moversDown || [];
  document.getElementById("moversUp").innerHTML =
    up
      .map(
        (m) =>
          '<div class="mover up"><span>' +
          m.key +
          '</span><span class="amt">+' +
          full(m.gap) +
          "</span></div>"
      )
      .join("") || "<div class='desc'>Không có tăng</div>";
  document.getElementById("moversDown").innerHTML =
    down
      .map(
        (m) =>
          '<div class="mover down"><span>' +
          m.key +
          '</span><span class="amt">' +
          full(m.gap) +
          "</span></div>"
      )
      .join("") || "<div class='desc'>Không có giảm</div>";
}

function renderCompare() {
  destroy("cmp");
  const a = document.getElementById("cmpA").value;
  const b = document.getElementById("cmpB").value;
  const va = gVal(a);
  const vb = gVal(b);
  const d = vb - va;
  const pct = va ? (d / va) * 100 : 0;
  document.getElementById("cmpKpis").innerHTML =
    '<div class="chip"><span class="emoji">🅰️</span>' +
    a +
    ': <b class="mono">' +
    bn(va) +
    "</b></div>" +
    '<div class="chip"><span class="emoji">🅱️</span>' +
    b +
    ': <b class="mono">' +
    bn(vb) +
    "</b></div>" +
    '<div class="chip ' +
    (d >= 0 ? "up" : "down") +
    '"><span class="emoji">Δ</span>Diff: <b class="mono">' +
    (d >= 0 ? "+" : "") +
    bn(d) +
    "</b> (" +
    (pct >= 0 ? "+" : "") +
    pct.toFixed(1) +
    "%)</div>";

  const ccs = [...new Set(DATA.budgetRows.map((r) => r.ccName))];
  const da = ccs.map((cc) =>
    DATA.budgetRows
      .filter((r) => r.ccName === cc)
      .reduce((s, r) => s + (r.values[a] || 0), 0)
  );
  const db = ccs.map((cc) =>
    DATA.budgetRows
      .filter((r) => r.ccName === cc)
      .reduce((s, r) => s + (r.values[b] || 0), 0)
  );
  charts.cmp = new Chart(document.getElementById("chartCompare"), {
    type: "bar",
    data: {
      labels: ccs,
      datasets: [
        {
          label: a,
          data: da,
          backgroundColor: "#00A0E9",
          borderRadius: 10,
        },
        {
          label: b,
          data: db,
          backgroundColor: "#FFD54F",
          borderRadius: 10,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: "bottom",
          labels: { boxWidth: 12, font: { weight: "800" } },
        },
        tooltip: {
          callbacks: {
            label: (c) => " " + c.dataset.label + ": " + bn(c.raw),
          },
        },
      },
      scales: {
        x: {
          grid: { display: false },
          ticks: { font: { weight: "800" } },
        },
        y: {
          ticks: { callback: (v) => bn(v) },
          grid: { color: "rgba(0,160,233,.08)" },
        },
      },
    },
  });
}

function renderAssetsCharts() {
  destroy("topA");
  destroy("aGL");
  const top = DATA.assets.slice(0, 12);
  charts.topA = new Chart(document.getElementById("chartTopAssets"), {
    type: "bar",
    data: {
      labels: top.map((a) => (a.name || a.code).slice(0, 26)),
      datasets: [
        {
          data: top.map((a) => a.cost),
          backgroundColor: "#00A0E9",
          borderRadius: 10,
        },
      ],
    },
    options: {
      indexAxis: "y",
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: { label: (c) => " " + full(c.raw) },
        },
      },
      scales: {
        x: {
          ticks: { callback: (v) => bn(v) },
          grid: { color: "rgba(0,160,233,.08)" },
        },
        y: {
          grid: { display: false },
          ticks: { font: { size: 10, weight: "800" } },
        },
      },
    },
  });

  const map = {};
  DATA.assetsAll.forEach((a) => {
    const k = a.glName || "Other";
    map[k] = (map[k] || 0) + (a.cost || 0);
  });
  const labels = Object.keys(map);
  charts.aGL = new Chart(document.getElementById("chartAssetGL"), {
    type: "doughnut",
    data: {
      labels,
      datasets: [
        {
          data: labels.map((k) => map[k]),
          backgroundColor: colors,
          borderWidth: 4,
          borderColor: "#fff",
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      cutout: "55%",
      plugins: {
        legend: {
          position: "bottom",
          labels: { boxWidth: 12, font: { weight: "800" } },
        },
        tooltip: {
          callbacks: {
            label: (c) => " " + c.label + ": " + bn(c.raw),
          },
        },
      },
    },
  });

  const sc = DATA.kpi.statusCounts || {};
  document.getElementById("statusChips").innerHTML =
    '<div class="chip"><span class="emoji">🟢</span>Active <b>' +
    (sc.active || 0) +
    "</b></div>" +
    '<div class="chip"><span class="emoji">🟡</span>Ending soon <b>' +
    (sc.ending_soon || 0) +
    "</b></div>" +
    '<div class="chip"><span class="emoji">🔴</span>Ended <b>' +
    (sc.ended || 0) +
    "</b></div>" +
    '<div class="chip"><span class="emoji">⭐</span>Favorites <b>' +
    favs.size +
    "</b></div>";
}

function statusTag(s) {
  if (s === "ending_soon") return '<span class="tag gold">Ending soon</span>';
  if (s === "ended") return '<span class="tag red">Ended</span>';
  return '<span class="tag green">Active</span>';
}

function renderTables() {
  const head = document.getElementById("budgetHead");
  const body = document.getElementById("budgetBody");
  const filterCC = document.getElementById("filterCC");
  const filterGL = document.getElementById("filterGL");

  if (!filterCC.dataset.ready) {
    [...new Set(DATA.budgetRows.map((r) => r.ccName))].forEach((c) => {
      const o = document.createElement("option");
      o.value = c;
      o.textContent = c;
      filterCC.appendChild(o);
    });
    [...new Set(DATA.budgetRows.map((r) => r.glName))].forEach((c) => {
      const o = document.createElement("option");
      o.value = c;
      o.textContent = c;
      filterGL.appendChild(o);
    });
    filterCC.dataset.ready = "1";
    filterCC.onchange = renderTables;
    filterGL.onchange = renderTables;
  }

  head.innerHTML =
    "<tr><th>CC</th><th>G/L</th>" +
    periods.map((p) => '<th class="num">' + p + "</th>").join("") +
    '<th class="num">GAP 104/103</th></tr>';

  const cc = filterCC.value;
  const gl = filterGL.value;
  let rows = DATA.budgetRows.filter(
    (r) => (!cc || r.ccName === cc) && (!gl || r.glName === gl)
  );
  const gq = (document.getElementById("globalSearch").value || "")
    .toLowerCase()
    .trim();
  if (gq) {
    rows = rows.filter((r) =>
      (r.ccName + " " + r.glName).toLowerCase().includes(gq)
    );
  }

  body.innerHTML = rows
    .map((r) => {
      const gap =
        r.gaps["104Ki"] ??
        (r.values["104Ki"] || 0) - (r.values["103Ki"] || 0);
      const gapCls = gap > 0 ? "pos" : gap < 0 ? "neg" : "";
      return (
        "<tr><td><span class=\"tag\">" +
        r.ccName +
        '</span></td><td><span class="tag blue">' +
        r.glName +
        "</span></td>" +
        periods
          .map(
            (p) =>
              '<td class="num">' + full(r.values[p] || 0) + "</td>"
          )
          .join("") +
        '<td class="num ' +
        gapCls +
        '">' +
        full(gap) +
        "</td></tr>"
      );
    })
    .join("");

  const q = (
    document.getElementById("assetSearch").value ||
    document.getElementById("globalSearch").value ||
    ""
  )
    .toLowerCase()
    .trim();
  const st = document.getElementById("statusFilter").value;
  let list = DATA.assetsAll.slice();
  if (st === "fav") list = list.filter((a) => favs.has(a.code || a.name));
  else if (st) list = list.filter((a) => a.status === st);
  if (q) {
    list = list.filter((a) =>
      (
        (a.name || "") +
        (a.code || "") +
        (a.ccName || "") +
        (a.glName || "")
      )
        .toLowerCase()
        .includes(q)
    );
  }
  list.sort((a, b) => {
    const k = assetSort.key;
    const av = a[k];
    const bv = b[k];
    if (typeof av === "string") return av.localeCompare(bv || "") * assetSort.dir;
    return ((av || 0) - (bv || 0)) * assetSort.dir;
  });

  document.getElementById("assetBody").innerHTML = list
    .slice(0, 120)
    .map((a) => {
      const id = a.code || a.name;
      const on = favs.has(id) ? "on" : "";
      const idx = DATA.assetsAll.indexOf(a);
      return (
        '<tr data-idx="' +
        idx +
        '">' +
        '<td><span class="star ' +
        on +
        '" data-fav="' +
        id.replace(/"/g, "") +
        '">⭐</span></td>' +
        '<td class="mono">' +
        (a.code || "—") +
        "</td>" +
        '<td class="name">' +
        (a.name || "—") +
        "</td>" +
        '<td><span class="tag">' +
        (a.ccName || "—") +
        "</span></td>" +
        '<td><span class="tag violet">' +
        (a.glName || "—") +
        "</span></td>" +
        "<td>" +
        statusTag(a.status) +
        "</td>" +
        '<td class="num">' +
        full(a.cost) +
        "</td>" +
        '<td class="num">' +
        (a.life != null ? a.life : "—") +
        "</td>" +
        '<td class="num">' +
        full(a.totalAll) +
        "</td></tr>"
      );
    })
    .join("");

  document.querySelectorAll("#assetBody tr").forEach((tr) => {
    tr.style.cursor = "pointer";
    tr.onclick = (e) => {
      if (e.target.classList.contains("star")) {
        e.stopPropagation();
        const id = e.target.dataset.fav;
        if (favs.has(id)) favs.delete(id);
        else favs.add(id);
        saveFavs();
        renderTables();
        renderFavs();
        renderAssetsCharts();
        toast(favs.has(id) ? "Đã gắn sao ⭐" : "Bỏ sao");
        return;
      }
      openAsset(Number(tr.dataset.idx));
    };
  });
}

function renderFavs() {
  const list = DATA.assetsAll.filter((a) => favs.has(a.code || a.name));
  const el = document.getElementById("favList");
  if (!list.length) {
    el.innerHTML =
      "<div class='desc'>Chưa có favorite — bấm ⭐ trên bảng asset nhé!</div>";
    return;
  }
  el.innerHTML = list
    .map(
      (a) =>
        '<div class="mover"><span>⭐ ' +
        (a.name || a.code).slice(0, 40) +
        '</span><span class="amt mono">' +
        bn(a.cost) +
        "</span></div>"
    )
    .join("");
}

function openAsset(idx) {
  const a = DATA.assetsAll[idx];
  if (!a) return;
  document.getElementById("modalTitle").textContent =
    "📦 " + (a.name || a.code || "Asset");
  document.getElementById("modalSub").textContent =
    (a.code || "") +
    " · " +
    (a.ccName || "") +
    " · " +
    (a.glName || "") +
    " · " +
    a.status;
  document.getElementById("modalBody").innerHTML = [
    ["Acquisition", full(a.cost) + " VND"],
    ["Life", a.life != null ? a.life + " months" : "—"],
    ["Monthly rate", full(a.monthlyRate || 0) + " VND"],
    ["Start → End", (a.start || "—") + " → " + (a.end || "—")],
    ["Months left", a.monthsLeft != null ? a.monthsLeft : "—"],
    ["Σ MT KH", full(a.totalAll) + " VND"],
  ]
    .map(
      ([k, v]) =>
        '<div class="row"><span>' +
        k +
        '</span><span class="mono">' +
        v +
        "</span></div>"
    )
    .join("");

  if (assetDetailChart) assetDetailChart.destroy();
  assetDetailChart = new Chart(document.getElementById("chartAssetDetail"), {
    type: "bar",
    data: {
      labels: periods,
      datasets: [
        {
          data: a.periodTotals || [],
          backgroundColor: "#7C4DFF",
          borderRadius: 10,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: { label: (c) => " " + full(c.raw) },
        },
      },
      scales: {
        x: { grid: { display: false } },
        y: {
          ticks: { callback: (v) => bn(v) },
          grid: { color: "rgba(0,160,233,.08)" },
        },
      },
    },
  });
  document.getElementById("modalBg").classList.add("show");
}

function renderAll(meta) {
  if (meta !== false) {
    document.getElementById("srcName").textContent = DATA.meta.source;
    document.getElementById("genAt").textContent = DATA.meta.generated;
    document.getElementById("footMeta").textContent =
      "v" + (DATA.meta.version || "3") + " · " + DATA.meta.generated;
  }
  renderKPI();
  renderInsights();
  renderPeriod();
  renderWaterfall();
  renderPies();
  renderStack();
  renderGap();
  renderCompare();
  renderMonthly();
  renderHeatmap();
  renderMovers();
  renderAssetsCharts();
  renderTables();
  renderFavs();
  document.getElementById("helperText").textContent =
    tips[helperIdx % tips.length];
}

function party() {
  const box = document.getElementById("confetti");
  box.innerHTML = "";
  const cols = ["#00A0E9", "#E60012", "#FFD54F", "#fff", "#7C4DFF", "#26A69A"];
  for (let i = 0; i < 48; i++) {
    const el = document.createElement("i");
    el.style.left = Math.random() * 100 + "%";
    el.style.background = cols[i % cols.length];
    el.style.animationDuration = 2 + Math.random() * 2.5 + "s";
    el.style.width = 6 + Math.random() * 8 + "px";
    el.style.height = el.style.width;
    box.appendChild(el);
  }
  setTimeout(() => {
    box.innerHTML = "";
  }, 4500);
  ringBell();
  toast("Yayyy! 🎉 Doraemon party!");
}

function wireEvents() {
  document.getElementById("assetSearch").oninput = renderTables;
  document.getElementById("statusFilter").onchange = renderTables;
  document.getElementById("globalSearch").oninput = renderTables;
  document.getElementById("modalClose").onclick = () =>
    document.getElementById("modalBg").classList.remove("show");
  document.getElementById("modalBg").onclick = (e) => {
    if (e.target.id === "modalBg") e.currentTarget.classList.remove("show");
  };
  document.getElementById("btnPrint").onclick = () => window.print();
  document.getElementById("btnNight").onclick = () => {
    document.body.classList.toggle("night");
    toast(
      document.body.classList.contains("night")
        ? "Night mode 🌙"
        : "Day mode ☀️"
    );
  };
  document.getElementById("btnConfetti").onclick = party;
  document.getElementById("bellBtn").onclick = () => {
    ringBell();
    helperIdx++;
    document.getElementById("helperText").textContent =
      tips[helperIdx % tips.length];
    document.getElementById("helper").classList.remove("hidden");
    toast("Ting-a-ling 🔔");
  };
  document.getElementById("helperNext").onclick = () => {
    helperIdx++;
    document.getElementById("helperText").textContent =
      tips[helperIdx % tips.length];
    ringBell();
  };
  document.getElementById("helperHide").onclick = () =>
    document.getElementById("helper").classList.add("hidden");

  document.getElementById("btnShare").onclick = async () => {
    const g = gVal(focusPeriod);
    const text =
      "LOG Depreciation (" +
      DATA.meta.source +
      ")\nFocus " +
      focusPeriod +
      ": " +
      full(g) +
      " VND\nMT total: " +
      full(DATA.kpi.totalMT) +
      " VND\nAssets: " +
      DATA.kpi.assetCount +
      "\nGenerated: " +
      DATA.meta.generated;
    try {
      await navigator.clipboard.writeText(text);
      toast("Đã copy summary 📝");
    } catch (e) {
      toast("Clipboard blocked");
    }
  };

  document.getElementById("btnExportCsv").onclick = () => {
    const lines = [["CC", "G/L", ...periods, "GAP_104_103"]];
    DATA.budgetRows.forEach((r) => {
      const gap =
        r.gaps["104Ki"] ??
        (r.values["104Ki"] || 0) - (r.values["103Ki"] || 0);
      lines.push([
        r.ccName,
        r.glName,
        ...periods.map((p) => r.values[p] || 0),
        gap,
      ]);
    });
    const csv = lines
      .map((row) =>
        row.map((x) => '"' + String(x).replace(/"/g, '""') + '"').join(",")
      )
      .join("\n");
    const blob = new Blob([csv], { type: "text/csv;charset=utf-8" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = "log_depreciation_budget.csv";
    a.click();
    URL.revokeObjectURL(a.href);
    toast("CSV exported 📤");
  };

  document.querySelectorAll("th[data-sort]").forEach((th) => {
    th.onclick = () => {
      const k = th.dataset.sort;
      if (assetSort.key === k) assetSort.dir *= -1;
      else {
        assetSort.key = k;
        assetSort.dir = -1;
      }
      renderTables();
    };
  });

  const titles = {
    overview: "Overview",
    midterm: "Mid-term",
    compare: "Compare",
    monthly: "Monthly",
    heatmap: "Heatmap",
    movers: "Movers",
    assets: "Assets",
    tables: "Tables",
    favs: "Favorites",
  };
  document.querySelectorAll("[data-nav]").forEach((a) => {
    a.addEventListener("click", () => {
      document
        .querySelectorAll("[data-nav]")
        .forEach((x) => x.classList.remove("active"));
      a.classList.add("active");
      const id = a.getAttribute("href").slice(1);
      document.getElementById("pageTitle").textContent =
        titles[id] || "Dashboard";
    });
  });
}

document.addEventListener("DOMContentLoaded", () => {
  try {
    initSelects();
    wireEvents();
    renderAll(true);
    setTimeout(party, 500);
  } catch (err) {
    console.error(err);
    toast("Lỗi JS: " + err.message);
    alert("Dashboard error: " + err.message);
  }
});
