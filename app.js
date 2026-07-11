/* global Chart */
(function () {
  "use strict";

  // ── Bootstrap ──────────────────────────────────────────────
  var DATA = window.DATA;
  if (!DATA || !DATA.meta) {
    document.addEventListener("DOMContentLoaded", function () {
      document.body.innerHTML =
        '<div style="max-width:520px;margin:48px auto;padding:28px;font-family:Nunito,system-ui,sans-serif;' +
        'background:#fff;border-radius:20px;border:3px solid #1e9fe0;box-shadow:0 12px 32px rgba(6,90,148,.15)">' +
        "<h1 style='color:#065a94;margin:0 0 12px;font-size:22px'>🐱 Chưa mở đúng cách</h1>" +
        "<p style='line-height:1.55;color:#5d7590;font-weight:700;margin:0 0 12px'>" +
        "Chạy server rồi mở đúng địa chỉ:</p>" +
        "<pre style='background:#eef8ff;padding:14px;border-radius:12px;overflow:auto;font-weight:700;" +
        "font-size:13px;line-height:1.5;margin:0'>cd Downloads\\log-depreciation-dashboard\n" +
        "start.bat\n\n" +
        "→ http://127.0.0.1:8765</pre>" +
        "<p style='margin:14px 0 0;font-weight:700;color:#5d7590;font-size:13px'>" +
        "Hoặc: <code>py -3 server.py</code></p></div>";
    });
    throw new Error("window.DATA missing");
  }

  var periods = DATA.meta.periods.slice();
  var COLORS = [
    "#1e9fe0", "#e53935", "#ffd54f", "#7c4dff",
    "#26a69a", "#ff8a65", "#42a5f5", "#ec407a", "#66bb6a",
  ];

  var charts = {};
  var focusPeriod = periods[0];
  var assetDetailChart = null;
  var assetSort = { key: "cost", dir: -1 };
  var favs = new Set(JSON.parse(localStorage.getItem("dora_favs") || "[]"));
  var helperIdx = 0;
  var liveVersion = DATA.meta.fileMtime || 0;
  var liveTimer = null;
  var nightPref = localStorage.getItem("dora_night") === "1";

  function buildTips() {
    return [
      "Chạy start.bat (hoặc py -3 server.py) để bật LIVE — Save Excel là web tự cập nhật.",
      "Kéo thả file .xlsx vào vùng Upload để nạp data mới ngay.",
      "Bấm chuông 🔔 để xem insight / mẹo ngẫu nhiên.",
      "Dùng Compare để so 2 kỳ khi thuyết trình.",
      "Gắn ⭐ asset quan trọng — xem lại ở Favorites.",
      "Lọc Ending ≤24m để thấy TS sắp hết khấu hao.",
      "Night mode lưu trên máy — bật lại lần sau vẫn giữ.",
    ].concat(DATA.insights || []);
  }
  var tips = buildTips();

  // ── Utils ──────────────────────────────────────────────────
  function esc(s) {
    return String(s == null ? "" : s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  function bn(v) {
    if (v == null || isNaN(v)) return "—";
    var n = Number(v);
    var a = Math.abs(n);
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
    var el = document.getElementById("toast");
    if (!el) return;
    el.textContent = msg;
    el.classList.add("show");
    clearTimeout(toast._t);
    toast._t = setTimeout(function () {
      el.classList.remove("show");
    }, 2400);
  }

  function destroy(key) {
    if (charts[key]) {
      charts[key].destroy();
      delete charts[key];
    }
  }

  function gVal(p) {
    if (DATA.kpi.grand && DATA.kpi.grand[p] != null) return DATA.kpi.grand[p];
    return (DATA.kpi.byPeriod && DATA.kpi.byPeriod[p]) || 0;
  }

  function saveFavs() {
    localStorage.setItem("dora_favs", JSON.stringify(Array.from(favs)));
  }

  function ringBell() {
    try {
      var Ctx = window.AudioContext || window.webkitAudioContext;
      var ctx = new Ctx();
      var o = ctx.createOscillator();
      var g = ctx.createGain();
      o.type = "sine";
      o.frequency.value = 880;
      g.gain.value = 0.03;
      o.connect(g);
      g.connect(ctx.destination);
      o.start();
      o.frequency.exponentialRampToValueAtTime(1320, ctx.currentTime + 0.08);
      g.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.3);
      o.stop(ctx.currentTime + 0.32);
    } catch (e) { /* ignore */ }
  }

  function setLiveBadge(state, text) {
    var el = document.getElementById("liveBadge");
    if (!el) return;
    el.className = "live-badge " + state;
    el.innerHTML =
      '<span class="live-dot"></span><span class="live-text">' +
      esc(text) +
      "</span>";
    el.title = text;
  }

  function statusTag(s) {
    if (s === "ending_soon") return '<span class="tag gold">Ending soon</span>';
    if (s === "ended") return '<span class="tag red">Ended</span>';
    return '<span class="tag green">Active</span>';
  }

  function shortName(name, n) {
    name = String(name || "");
    return name.length > n ? name.slice(0, n - 1) + "…" : name;
  }

  Chart.defaults.color = "#5d7590";
  Chart.defaults.borderColor = "rgba(30,159,224,.12)";
  Chart.defaults.font.family = "'Nunito', system-ui, sans-serif";
  Chart.defaults.plugins.legend.labels.usePointStyle = true;

  // ── Selects ────────────────────────────────────────────────
  function fillPeriodSelect(sel, value) {
    if (!sel) return;
    sel.innerHTML = "";
    periods.forEach(function (p) {
      var o = document.createElement("option");
      o.value = p;
      o.textContent = p;
      sel.appendChild(o);
    });
    if (value && periods.indexOf(value) >= 0) sel.value = value;
  }

  function initSelects() {
    fillPeriodSelect(document.getElementById("periodFocus"), focusPeriod);
    fillPeriodSelect(document.getElementById("cmpA"), periods[0]);
    fillPeriodSelect(document.getElementById("cmpB"), periods[1] || periods[0]);

    document.getElementById("periodFocus").onchange = function () {
      focusPeriod = this.value;
      renderAll(false);
      toast("Focus: " + focusPeriod);
    };
    document.getElementById("cmpA").onchange = renderCompare;
    document.getElementById("cmpB").onchange = renderCompare;
  }

  // ── Live ───────────────────────────────────────────────────
  function applyLiveData(newData, silent) {
    var prev = focusPeriod;
    DATA = newData;
    window.DATA = newData;
    periods = DATA.meta.periods.slice();
    tips = buildTips();
    liveVersion = DATA.meta.fileMtime || liveVersion;
    if (periods.indexOf(prev) >= 0) focusPeriod = prev;
    else focusPeriod = periods[0];

    fillPeriodSelect(document.getElementById("periodFocus"), focusPeriod);
    var a = document.getElementById("cmpA").value;
    var b = document.getElementById("cmpB").value;
    fillPeriodSelect(
      document.getElementById("cmpA"),
      periods.indexOf(a) >= 0 ? a : periods[0]
    );
    fillPeriodSelect(
      document.getElementById("cmpB"),
      periods.indexOf(b) >= 0 ? b : periods[1] || periods[0]
    );

    var fcc = document.getElementById("filterCC");
    var fgl = document.getElementById("filterGL");
    if (fcc) {
      fcc.dataset.ready = "";
      fcc.innerHTML = '<option value="">All CC</option>';
    }
    if (fgl) {
      fgl.dataset.ready = "";
      fgl.innerHTML = '<option value="">All G/L</option>';
    }

    renderAll(true);
    document.body.classList.add("data-flash");
    setTimeout(function () {
      document.body.classList.remove("data-flash");
    }, 550);
    if (!silent) {
      ringBell();
      toast("Đã cập nhật · " + (DATA.meta.fileMtimeIso || DATA.meta.generated));
    }
    setLiveBadge("on", "LIVE · updated");
  }

  async function pollLive() {
    try {
      var st = await fetch("/api/status", { cache: "no-store" });
      if (!st.ok) throw new Error("offline");
      var meta = await st.json();
      var ver = meta.fileMtime || meta.version || 0;
      var src = meta.source || "Excel";
      var label = "LIVE";
      if (meta.fileMtimeIso) label += " · " + meta.fileMtimeIso;
      else label += " · " + src;

      if (ver && ver !== liveVersion) {
        setLiveBadge("sync", "Syncing…");
        var res = await fetch("/api/data", { cache: "no-store" });
        var payload = await res.json();
        if (payload.ok && payload.data) {
          applyLiveData(payload.data, false);
          return;
        }
      }
      setLiveBadge("on", label);
      var foot = document.getElementById("liveFoot");
      if (foot && meta.lastExtract) {
        var ago = Math.max(0, Math.round(Date.now() / 1000 - meta.lastExtract));
        foot.textContent =
          "Watching every " +
          (meta.pollSec || 2) +
          "s · last extract " +
          ago +
          "s ago · " +
          src;
      }
    } catch (e) {
      setLiveBadge("off", "STATIC · chạy start.bat");
    }
  }

  function startLivePolling() {
    if (location.protocol === "file:") {
      setLiveBadge("off", "STATIC · chạy start.bat");
      return;
    }
    pollLive();
    liveTimer = setInterval(pollLive, 2500);
  }

  async function uploadExcel(file) {
    if (!file) return;
    if (location.protocol === "file:") {
      toast("Cần start.bat / server.py để upload");
      return;
    }
    var name = (file.name || "").toLowerCase();
    if (!name.endsWith(".xlsx") && !name.endsWith(".xlsm")) {
      toast("Chỉ nhận file .xlsx / .xlsm");
      return;
    }
    setLiveBadge("sync", "Uploading…");
    try {
      var fd = new FormData();
      fd.append("file", file, file.name);
      var res = await fetch("/api/upload", { method: "POST", body: fd });
      var payload = await res.json();
      if (!payload.ok) throw new Error(payload.error || "upload failed");
      var dataRes = await fetch("/api/data", { cache: "no-store" });
      var wrap = await dataRes.json();
      if (wrap.ok && wrap.data) applyLiveData(wrap.data, false);
      else throw new Error("no data after upload");
    } catch (err) {
      toast("Upload lỗi: " + err.message);
      setLiveBadge("err", "Upload failed");
    }
  }

  // ── Render ─────────────────────────────────────────────────
  function renderKPI() {
    var gF = gVal(focusPeriod);
    var g103 = gVal("103Ki");
    var idx = periods.indexOf(focusPeriod);
    var prev = idx > 0 ? gVal(periods[idx - 1]) : null;
    var gap = prev == null ? 0 : gF - prev;
    var sc = DATA.kpi.statusCounts || {};
    var items = [
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
        h: "Ending soon: " + (sc.ending_soon || 0),
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
      .map(function (i) {
        return (
          '<div class="kpi"><div class="kpi-label">' +
          esc(i.l) +
          '</div><div class="kpi-value mono ' +
          i.c +
          '">' +
          esc(i.v) +
          '</div><div class="kpi-hint">' +
          esc(i.h) +
          "</div></div>"
        );
      })
      .join("");
  }

  function renderInsights() {
    var el = document.getElementById("insightChips");
    if (!el) return;
    var em = ["💡", "📌", "✨", "🔔", "🎯"];
    el.innerHTML = (DATA.insights || [])
      .map(function (t, i) {
        return (
          '<div class="chip"><span class="emoji">' +
          em[i % 5] +
          "</span><span>" +
          esc(t) +
          "</span></div>"
        );
      })
      .join("");
  }

  function renderPeriod() {
    destroy("period");
    var vals = periods.map(gVal);
    charts.period = new Chart(document.getElementById("chartPeriod"), {
      type: "bar",
      data: {
        labels: periods,
        datasets: [
          {
            data: vals,
            backgroundColor: periods.map(function (p) {
              return p === focusPeriod ? "#1e9fe0" : "rgba(30,159,224,.28)";
            }),
            borderRadius: 10,
            borderSkipped: false,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        onClick: function (_, els) {
          if (!els.length) return;
          focusPeriod = periods[els[0].index];
          document.getElementById("periodFocus").value = focusPeriod;
          renderAll(false);
          toast("Focus: " + focusPeriod);
        },
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              label: function (c) {
                return " " + full(c.raw) + " VND";
              },
            },
          },
        },
        scales: {
          x: { grid: { display: false }, ticks: { font: { weight: "800" } } },
          y: {
            ticks: {
              callback: function (v) {
                return bn(v);
              },
            },
            grid: { color: "rgba(30,159,224,.08)" },
          },
        },
      },
    });
  }

  function renderWaterfall() {
    destroy("wf");
    var wf = DATA.waterfall || [];
    var labels = wf.map(function (x) {
      return x.label;
    });
    var base = [];
    var mid = [];
    var cols = [];
    var run = 0;
    wf.forEach(function (s) {
      if (s.type === "total") {
        base.push(0);
        mid.push(s.value);
        cols.push("#1e9fe0");
        run = s.value;
      } else if (s.value >= 0) {
        base.push(run);
        mid.push(s.value);
        cols.push("#26a69a");
        run += s.value;
      } else {
        base.push(run + s.value);
        mid.push(-s.value);
        cols.push("#e53935");
        run += s.value;
      }
    });
    charts.wf = new Chart(document.getElementById("chartWaterfall"), {
      type: "bar",
      data: {
        labels: labels,
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
            filter: function (item) {
              return item.datasetIndex === 1;
            },
            callbacks: {
              label: function (c) {
                var s = wf[c.dataIndex];
                if (s.type === "delta")
                  return " " + (s.value >= 0 ? "+" : "") + full(s.value);
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
            ticks: {
              callback: function (v) {
                return bn(v);
              },
            },
            grid: { color: "rgba(30,159,224,.08)" },
          },
        },
      },
    });
  }

  function sumBy(field, period) {
    var m = {};
    (DATA.budgetRows || []).forEach(function (r) {
      m[r[field]] = (m[r[field]] || 0) + (r.values[period] || 0);
    });
    return m;
  }

  function makeDoughnut(canvasId, map, key) {
    var labels = Object.keys(map);
    var vals = labels.map(function (k) {
      return map[k];
    });
    var total =
      vals.reduce(function (a, b) {
        return a + b;
      }, 0) || 1;
    charts[key] = new Chart(document.getElementById(canvasId), {
      type: "doughnut",
      data: {
        labels: labels,
        datasets: [
          {
            data: vals,
            backgroundColor: COLORS,
            borderWidth: 3,
            borderColor: "#fff",
            hoverOffset: 5,
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
            labels: { boxWidth: 10, font: { weight: "800", size: 10.5 } },
          },
          tooltip: {
            callbacks: {
              label: function (c) {
                var pct = ((c.raw / total) * 100).toFixed(1);
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
    var ccs = Object.keys(DATA.byCC || {});
    charts.stack = new Chart(document.getElementById("chartCCstack"), {
      type: "bar",
      data: {
        labels: periods,
        datasets: ccs.map(function (cc, i) {
          return {
            label: cc,
            data: periods.map(function (p) {
              return (DATA.byCC[cc] && DATA.byCC[cc][p]) || 0;
            }),
            backgroundColor: COLORS[i % COLORS.length],
            stack: "s",
            borderRadius: 3,
          };
        }),
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
              label: function (c) {
                return " " + c.dataset.label + ": " + bn(c.raw);
              },
            },
          },
        },
        scales: {
          x: { stacked: true, grid: { display: false } },
          y: {
            stacked: true,
            ticks: {
              callback: function (v) {
                return bn(v);
              },
            },
            grid: { color: "rgba(30,159,224,.08)" },
          },
        },
      },
    });
  }

  function renderGap() {
    destroy("gap");
    var gaps = [];
    for (var i = 1; i < periods.length; i++) {
      gaps.push(gVal(periods[i]) - gVal(periods[i - 1]));
    }
    charts.gap = new Chart(document.getElementById("chartGap"), {
      type: "bar",
      data: {
        labels: periods.slice(1).map(function (p, i) {
          return p + " vs " + periods[i];
        }),
        datasets: [
          {
            data: gaps,
            backgroundColor: gaps.map(function (v) {
              return v >= 0 ? "#26a69a" : "#e53935";
            }),
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
            callbacks: {
              label: function (c) {
                return " " + full(c.raw);
              },
            },
          },
        },
        scales: {
          x: { grid: { display: false }, ticks: { font: { weight: "800" } } },
          y: {
            ticks: {
              callback: function (v) {
                return bn(v);
              },
            },
            grid: { color: "rgba(30,159,224,.08)" },
          },
        },
      },
    });
  }

  function renderMonthly() {
    destroy("mTot");
    destroy("mCC");
    destroy("mGL");
    var monthly = DATA.monthly || { labels: [], total: [], rows: [] };

    charts.mTot = new Chart(document.getElementById("chartMonthly"), {
      type: "line",
      data: {
        labels: monthly.labels,
        datasets: [
          {
            data: monthly.total,
            borderColor: "#1e9fe0",
            backgroundColor: "rgba(30,159,224,.12)",
            fill: true,
            tension: 0.35,
            pointRadius: 3.5,
            pointBackgroundColor: "#ffd54f",
            pointBorderColor: "#1e9fe0",
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
            callbacks: {
              label: function (c) {
                return " " + full(c.raw);
              },
            },
          },
        },
        scales: {
          x: { grid: { display: false } },
          y: {
            ticks: {
              callback: function (v) {
                return bn(v);
              },
            },
            grid: { color: "rgba(30,159,224,.08)" },
          },
        },
      },
    });

    var byCC = {};
    (monthly.rows || []).forEach(function (r) {
      if (!byCC[r.ccName])
        byCC[r.ccName] = monthly.labels.map(function () {
          return 0;
        });
      r.months.forEach(function (v, i) {
        byCC[r.ccName][i] += v;
      });
    });
    charts.mCC = new Chart(document.getElementById("chartMonthlyCC"), {
      type: "line",
      data: {
        labels: monthly.labels,
        datasets: Object.keys(byCC).map(function (k, i) {
          return {
            label: k,
            data: byCC[k],
            borderColor: COLORS[i % COLORS.length],
            tension: 0.35,
            pointRadius: 2.5,
            borderWidth: 2.5,
            backgroundColor: "transparent",
          };
        }),
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: "bottom",
            labels: { boxWidth: 10, font: { weight: "800", size: 10.5 } },
          },
          tooltip: {
            callbacks: {
              label: function (c) {
                return " " + c.dataset.label + ": " + bn(c.raw);
              },
            },
          },
        },
        scales: {
          x: { grid: { display: false } },
          y: {
            ticks: {
              callback: function (v) {
                return bn(v);
              },
            },
            grid: { color: "rgba(30,159,224,.08)" },
          },
        },
      },
    });

    var byGL = {};
    (monthly.rows || []).forEach(function (r) {
      if (!byGL[r.glName])
        byGL[r.glName] = monthly.labels.map(function () {
          return 0;
        });
      r.months.forEach(function (v, i) {
        byGL[r.glName][i] += v;
      });
    });
    charts.mGL = new Chart(document.getElementById("chartMonthlyGL"), {
      type: "bar",
      data: {
        labels: monthly.labels,
        datasets: Object.keys(byGL).map(function (k, i) {
          return {
            label: k,
            data: byGL[k],
            backgroundColor: COLORS[i % COLORS.length],
            stack: "m",
            borderRadius: 3,
          };
        }),
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
              label: function (c) {
                return " " + c.dataset.label + ": " + bn(c.raw);
              },
            },
          },
        },
        scales: {
          x: { stacked: true, grid: { display: false } },
          y: {
            stacked: true,
            ticks: {
              callback: function (v) {
                return bn(v);
              },
            },
            grid: { color: "rgba(30,159,224,.08)" },
          },
        },
      },
    });
  }

  function renderHeatmap() {
    var rows = DATA.heatmap || [];
    var max = 1;
    rows.forEach(function (r) {
      r.values.forEach(function (v) {
        if (v > max) max = v;
      });
    });
    var header =
      '<div class="h"></div>' +
      periods
        .map(function (p) {
          return '<div class="h">' + esc(p) + "</div>";
        })
        .join("");
    var body = rows
      .map(function (r) {
        var cells = r.values
          .map(function (v) {
            var t = max ? v / max : 0;
            var bg =
              "rgba(30,159,224," + (0.1 + t * 0.9).toFixed(3) + ")";
            var col = t > 0.45 ? "#fff" : "#065a94";
            return (
              '<div class="c" style="background:' +
              bg +
              ";color:" +
              col +
              '" title="' +
              esc(full(v)) +
              '">' +
              esc(bn(v)) +
              "</div>"
            );
          })
          .join("");
        return (
          '<div class="r" title="' +
          esc(r.key) +
          '">' +
          esc(r.key) +
          "</div>" +
          cells
        );
      })
      .join("");
    document.getElementById("heatMap").innerHTML = header + body;
  }

  function renderMovers() {
    var up = DATA.moversUp || [];
    var down = DATA.moversDown || [];
    document.getElementById("moversUp").innerHTML = up.length
      ? up
          .map(function (m) {
            return (
              '<div class="mover up"><span title="' +
              esc(m.key) +
              '">' +
              esc(m.key) +
              '</span><span class="amt">+' +
              esc(full(m.gap)) +
              "</span></div>"
            );
          })
          .join("")
      : "<div class='desc'>Không có tăng</div>";
    document.getElementById("moversDown").innerHTML = down.length
      ? down
          .map(function (m) {
            return (
              '<div class="mover down"><span title="' +
              esc(m.key) +
              '">' +
              esc(m.key) +
              '</span><span class="amt">' +
              esc(full(m.gap)) +
              "</span></div>"
            );
          })
          .join("")
      : "<div class='desc'>Không có giảm</div>";
  }

  function renderCompare() {
    destroy("cmp");
    var a = document.getElementById("cmpA").value;
    var b = document.getElementById("cmpB").value;
    var va = gVal(a);
    var vb = gVal(b);
    var d = vb - va;
    var pct = va ? (d / va) * 100 : 0;
    document.getElementById("cmpKpis").innerHTML =
      '<div class="chip"><span class="emoji">A</span>' +
      esc(a) +
      ': <b class="mono">' +
      esc(bn(va)) +
      "</b></div>" +
      '<div class="chip"><span class="emoji">B</span>' +
      esc(b) +
      ': <b class="mono">' +
      esc(bn(vb)) +
      "</b></div>" +
      '<div class="chip ' +
      (d >= 0 ? "up" : "down") +
      '"><span class="emoji">Δ</span>Diff: <b class="mono">' +
      esc((d >= 0 ? "+" : "") + bn(d)) +
      "</b> (" +
      esc((pct >= 0 ? "+" : "") + pct.toFixed(1) + "%") +
      ")</div>";

    var ccs = [];
    (DATA.budgetRows || []).forEach(function (r) {
      if (ccs.indexOf(r.ccName) < 0) ccs.push(r.ccName);
    });
    var da = ccs.map(function (cc) {
      return DATA.budgetRows
        .filter(function (r) {
          return r.ccName === cc;
        })
        .reduce(function (s, r) {
          return s + (r.values[a] || 0);
        }, 0);
    });
    var db = ccs.map(function (cc) {
      return DATA.budgetRows
        .filter(function (r) {
          return r.ccName === cc;
        })
        .reduce(function (s, r) {
          return s + (r.values[b] || 0);
        }, 0);
    });
    charts.cmp = new Chart(document.getElementById("chartCompare"), {
      type: "bar",
      data: {
        labels: ccs,
        datasets: [
          { label: a, data: da, backgroundColor: "#1e9fe0", borderRadius: 9 },
          { label: b, data: db, backgroundColor: "#ffd54f", borderRadius: 9 },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: "bottom",
            labels: { boxWidth: 10, font: { weight: "800" } },
          },
          tooltip: {
            callbacks: {
              label: function (c) {
                return " " + c.dataset.label + ": " + bn(c.raw);
              },
            },
          },
        },
        scales: {
          x: { grid: { display: false }, ticks: { font: { weight: "800" } } },
          y: {
            ticks: {
              callback: function (v) {
                return bn(v);
              },
            },
            grid: { color: "rgba(30,159,224,.08)" },
          },
        },
      },
    });
  }

  function renderAssetsCharts() {
    destroy("topA");
    destroy("aGL");
    var top = (DATA.assets || []).slice(0, 12);
    charts.topA = new Chart(document.getElementById("chartTopAssets"), {
      type: "bar",
      data: {
        labels: top.map(function (a) {
          return shortName(a.name || a.code, 24);
        }),
        datasets: [
          {
            data: top.map(function (a) {
              return a.cost;
            }),
            backgroundColor: "#1e9fe0",
            borderRadius: 9,
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
            callbacks: {
              title: function (items) {
                var i = items[0] && items[0].dataIndex;
                var a = top[i];
                return a ? a.name || a.code : "";
              },
              label: function (c) {
                return " " + full(c.raw);
              },
            },
          },
        },
        scales: {
          x: {
            ticks: {
              callback: function (v) {
                return bn(v);
              },
            },
            grid: { color: "rgba(30,159,224,.08)" },
          },
          y: {
            grid: { display: false },
            ticks: { font: { size: 10, weight: "800" } },
          },
        },
      },
    });

    var map = {};
    (DATA.assetsAll || []).forEach(function (a) {
      var k = a.glName || "Other";
      map[k] = (map[k] || 0) + (a.cost || 0);
    });
    var labels = Object.keys(map);
    charts.aGL = new Chart(document.getElementById("chartAssetGL"), {
      type: "doughnut",
      data: {
        labels: labels,
        datasets: [
          {
            data: labels.map(function (k) {
              return map[k];
            }),
            backgroundColor: COLORS,
            borderWidth: 3,
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
            labels: { boxWidth: 10, font: { weight: "800", size: 10.5 } },
          },
          tooltip: {
            callbacks: {
              label: function (c) {
                return " " + c.label + ": " + bn(c.raw);
              },
            },
          },
        },
      },
    });

    var sc = DATA.kpi.statusCounts || {};
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

  function renderTables() {
    var head = document.getElementById("budgetHead");
    var body = document.getElementById("budgetBody");
    var filterCC = document.getElementById("filterCC");
    var filterGL = document.getElementById("filterGL");

    if (!filterCC.dataset.ready) {
      Array.from(
        new Set(
          (DATA.budgetRows || []).map(function (r) {
            return r.ccName;
          })
        )
      ).forEach(function (c) {
        var o = document.createElement("option");
        o.value = c;
        o.textContent = c;
        filterCC.appendChild(o);
      });
      Array.from(
        new Set(
          (DATA.budgetRows || []).map(function (r) {
            return r.glName;
          })
        )
      ).forEach(function (c) {
        var o = document.createElement("option");
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
      periods
        .map(function (p) {
          return '<th class="num">' + esc(p) + "</th>";
        })
        .join("") +
      '<th class="num">GAP 104/103</th></tr>';

    var cc = filterCC.value;
    var gl = filterGL.value;
    var gq = (
      document.getElementById("globalSearch").value || ""
    )
      .toLowerCase()
      .trim();
    var rows = (DATA.budgetRows || []).filter(function (r) {
      if (cc && r.ccName !== cc) return false;
      if (gl && r.glName !== gl) return false;
      if (gq && (r.ccName + " " + r.glName).toLowerCase().indexOf(gq) < 0)
        return false;
      return true;
    });

    body.innerHTML = rows
      .map(function (r) {
        var gap = r.gaps["104Ki"];
        if (gap == null)
          gap = (r.values["104Ki"] || 0) - (r.values["103Ki"] || 0);
        var gapCls = gap > 0 ? "pos" : gap < 0 ? "neg" : "";
        return (
          '<tr><td><span class="tag">' +
          esc(r.ccName) +
          '</span></td><td><span class="tag blue">' +
          esc(r.glName) +
          "</span></td>" +
          periods
            .map(function (p) {
              return (
                '<td class="num">' + esc(full(r.values[p] || 0)) + "</td>"
              );
            })
            .join("") +
          '<td class="num ' +
          gapCls +
          '">' +
          esc(full(gap)) +
          "</td></tr>"
        );
      })
      .join("");

    var q = (
      document.getElementById("assetSearch").value ||
      document.getElementById("globalSearch").value ||
      ""
    )
      .toLowerCase()
      .trim();
    var st = document.getElementById("statusFilter").value;
    var list = (DATA.assetsAll || []).slice();
    if (st === "fav")
      list = list.filter(function (a) {
        return favs.has(a.code || a.name);
      });
    else if (st)
      list = list.filter(function (a) {
        return a.status === st;
      });
    if (q) {
      list = list.filter(function (a) {
        return (
          (
            (a.name || "") +
            (a.code || "") +
            (a.ccName || "") +
            (a.glName || "")
          )
            .toLowerCase()
            .indexOf(q) >= 0
        );
      });
    }
    list.sort(function (a, b) {
      var k = assetSort.key;
      var av = a[k];
      var bv = b[k];
      if (typeof av === "string")
        return String(av).localeCompare(String(bv || "")) * assetSort.dir;
      return ((av || 0) - (bv || 0)) * assetSort.dir;
    });

    document.getElementById("assetBody").innerHTML = list
      .slice(0, 120)
      .map(function (a) {
        var id = a.code || a.name;
        var on = favs.has(id) ? "on" : "";
        var idx = DATA.assetsAll.indexOf(a);
        return (
          '<tr data-idx="' +
          idx +
          '">' +
          '<td><span class="star ' +
          on +
          '" data-fav="' +
          esc(id) +
          '">⭐</span></td>' +
          '<td class="mono">' +
          esc(a.code || "—") +
          "</td>" +
          '<td class="name" title="' +
          esc(a.name || "") +
          '">' +
          esc(a.name || "—") +
          "</td>" +
          '<td><span class="tag">' +
          esc(a.ccName || "—") +
          "</span></td>" +
          '<td><span class="tag violet">' +
          esc(a.glName || "—") +
          "</span></td>" +
          "<td>" +
          statusTag(a.status) +
          "</td>" +
          '<td class="num">' +
          esc(full(a.cost)) +
          "</td>" +
          '<td class="num">' +
          esc(a.life != null ? a.life : "—") +
          "</td>" +
          '<td class="num">' +
          esc(full(a.totalAll)) +
          "</td></tr>"
        );
      })
      .join("");

    Array.prototype.forEach.call(
      document.querySelectorAll("#assetBody tr"),
      function (tr) {
        tr.style.cursor = "pointer";
        tr.onclick = function (e) {
          if (e.target.classList.contains("star")) {
            e.stopPropagation();
            var id = e.target.getAttribute("data-fav");
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
      }
    );
  }

  function renderFavs() {
    var list = (DATA.assetsAll || []).filter(function (a) {
      return favs.has(a.code || a.name);
    });
    var el = document.getElementById("favList");
    if (!list.length) {
      el.innerHTML =
        "<div class='desc'>Chưa có favorite — bấm ⭐ trên bảng asset.</div>";
      return;
    }
    el.innerHTML = list
      .map(function (a) {
        return (
          '<div class="mover"><span>⭐ ' +
          esc(shortName(a.name || a.code, 42)) +
          '</span><span class="amt mono">' +
          esc(bn(a.cost)) +
          "</span></div>"
        );
      })
      .join("");
  }

  function openAsset(idx) {
    var a = DATA.assetsAll[idx];
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
      .map(function (pair) {
        return (
          '<div class="row"><span>' +
          esc(pair[0]) +
          '</span><span class="mono">' +
          esc(pair[1]) +
          "</span></div>"
        );
      })
      .join("");

    if (assetDetailChart) assetDetailChart.destroy();
    assetDetailChart = new Chart(
      document.getElementById("chartAssetDetail"),
      {
        type: "bar",
        data: {
          labels: periods,
          datasets: [
            {
              data: a.periodTotals || [],
              backgroundColor: "#7c4dff",
              borderRadius: 9,
            },
          ],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: { display: false },
            tooltip: {
              callbacks: {
                label: function (c) {
                  return " " + full(c.raw);
                },
              },
            },
          },
          scales: {
            x: { grid: { display: false } },
            y: {
              ticks: {
                callback: function (v) {
                  return bn(v);
                },
              },
              grid: { color: "rgba(30,159,224,.08)" },
            },
          },
        },
      }
    );
    document.getElementById("modalBg").classList.add("show");
  }

  function renderAll(meta) {
    if (meta !== false) {
      document.getElementById("srcName").textContent = DATA.meta.source || "—";
      document.getElementById("genAt").textContent =
        DATA.meta.fileMtimeIso || DATA.meta.generated || "—";
      document.getElementById("footMeta").textContent =
        "v" +
        (DATA.meta.version || "4") +
        " · " +
        (DATA.meta.generated || "") +
        " · " +
        (DATA.kpi.assetCount || 0) +
        " assets";
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
    var ht = document.getElementById("helperText");
    if (ht) ht.textContent = tips[helperIdx % tips.length];
  }

  function party() {
    var box = document.getElementById("confetti");
    if (!box) return;
    box.innerHTML = "";
    var cols = ["#1e9fe0", "#e53935", "#ffd54f", "#fff", "#7c4dff", "#26a69a"];
    for (var i = 0; i < 36; i++) {
      var el = document.createElement("i");
      el.style.left = Math.random() * 100 + "%";
      el.style.background = cols[i % cols.length];
      el.style.animationDuration = 2 + Math.random() * 2 + "s";
      el.style.width = 6 + Math.random() * 6 + "px";
      el.style.height = el.style.width;
      box.appendChild(el);
    }
    setTimeout(function () {
      box.innerHTML = "";
    }, 4000);
    ringBell();
  }

  function closeSidebar() {
    document.getElementById("sidebar").classList.remove("open");
    document.getElementById("sidebarOverlay").classList.remove("show");
  }

  function openSidebar() {
    document.getElementById("sidebar").classList.add("open");
    document.getElementById("sidebarOverlay").classList.add("show");
  }

  function wireEvents() {
    document.getElementById("assetSearch").oninput = renderTables;
    document.getElementById("statusFilter").onchange = renderTables;
    document.getElementById("globalSearch").oninput = renderTables;

    document.getElementById("modalClose").onclick = function () {
      document.getElementById("modalBg").classList.remove("show");
    };
    document.getElementById("modalBg").onclick = function (e) {
      if (e.target.id === "modalBg")
        e.currentTarget.classList.remove("show");
    };
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape") {
        document.getElementById("modalBg").classList.remove("show");
        closeSidebar();
      }
    });

    document.getElementById("btnPrint").onclick = function () {
      window.print();
    };
    document.getElementById("btnNight").onclick = function () {
      document.body.classList.toggle("night");
      var on = document.body.classList.contains("night");
      localStorage.setItem("dora_night", on ? "1" : "0");
      toast(on ? "Night mode 🌙" : "Day mode ☀️");
    };
    document.getElementById("btnConfetti").onclick = function () {
      party();
      toast("Yay! 🎉");
    };
    document.getElementById("bellBtn").onclick = function () {
      ringBell();
      helperIdx++;
      document.getElementById("helperText").textContent =
        tips[helperIdx % tips.length];
      document.getElementById("helper").classList.remove("hidden");
      toast("Ting-a-ling 🔔");
    };
    document.getElementById("helperNext").onclick = function () {
      helperIdx++;
      document.getElementById("helperText").textContent =
        tips[helperIdx % tips.length];
      ringBell();
    };
    document.getElementById("helperHide").onclick = function () {
      document.getElementById("helper").classList.add("hidden");
    };

    document.getElementById("btnShare").onclick = async function () {
      var g = gVal(focusPeriod);
      var text =
        "LOG Depreciation (" +
        DATA.meta.source +
        ")\n" +
        "Focus " +
        focusPeriod +
        ": " +
        full(g) +
        " VND\n" +
        "MT total: " +
        full(DATA.kpi.totalMT) +
        " VND\n" +
        "Assets: " +
        DATA.kpi.assetCount +
        "\n" +
        "Generated: " +
        DATA.meta.generated;
      try {
        await navigator.clipboard.writeText(text);
        toast("Đã copy summary 📝");
      } catch (e) {
        toast("Clipboard blocked");
      }
    };

    document.getElementById("btnExportCsv").onclick = function () {
      var lines = [["CC", "G/L"].concat(periods).concat(["GAP_104_103"])];
      (DATA.budgetRows || []).forEach(function (r) {
        var gap = r.gaps["104Ki"];
        if (gap == null)
          gap = (r.values["104Ki"] || 0) - (r.values["103Ki"] || 0);
        lines.push(
          [r.ccName, r.glName]
            .concat(
              periods.map(function (p) {
                return r.values[p] || 0;
              })
            )
            .concat([gap])
        );
      });
      var csv = lines
        .map(function (row) {
          return row
            .map(function (x) {
              return '"' + String(x).replace(/"/g, '""') + '"';
            })
            .join(",");
        })
        .join("\n");
      var blob = new Blob(["\uFEFF" + csv], {
        type: "text/csv;charset=utf-8",
      });
      var a = document.createElement("a");
      a.href = URL.createObjectURL(blob);
      a.download = "log_depreciation_budget.csv";
      a.click();
      URL.revokeObjectURL(a.href);
      toast("CSV exported 📤");
    };

    Array.prototype.forEach.call(
      document.querySelectorAll("th[data-sort]"),
      function (th) {
        th.onclick = function () {
          var k = th.dataset.sort;
          if (assetSort.key === k) assetSort.dir *= -1;
          else {
            assetSort.key = k;
            assetSort.dir = -1;
          }
          renderTables();
        };
      }
    );

    var titles = {
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
    Array.prototype.forEach.call(
      document.querySelectorAll("[data-nav]"),
      function (a) {
        a.addEventListener("click", function () {
          Array.prototype.forEach.call(
            document.querySelectorAll("[data-nav]"),
            function (x) {
              x.classList.remove("active");
            }
          );
          a.classList.add("active");
          var id = a.getAttribute("href").slice(1);
          document.getElementById("pageTitle").textContent =
            titles[id] || "Dashboard";
          closeSidebar();
        });
      }
    );

    // mobile menu
    var btnMenu = document.getElementById("btnMenu");
    var overlay = document.getElementById("sidebarOverlay");
    if (btnMenu) btnMenu.onclick = openSidebar;
    if (overlay) overlay.onclick = closeSidebar;

    var fi = document.getElementById("fileInput");
    var dz = document.getElementById("dropZone");
    if (fi) {
      fi.onchange = function () {
        if (fi.files && fi.files[0]) uploadExcel(fi.files[0]);
        fi.value = "";
      };
    }
    if (dz) {
      ["dragenter", "dragover"].forEach(function (ev) {
        dz.addEventListener(ev, function (e) {
          e.preventDefault();
          dz.classList.add("drag");
        });
      });
      ["dragleave", "drop"].forEach(function (ev) {
        dz.addEventListener(ev, function (e) {
          e.preventDefault();
          dz.classList.remove("drag");
        });
      });
      dz.addEventListener("drop", function (e) {
        var f = e.dataTransfer.files && e.dataTransfer.files[0];
        if (f) uploadExcel(f);
      });
      dz.addEventListener("click", function () {
        if (fi) fi.click();
      });
      dz.addEventListener("keydown", function (e) {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          if (fi) fi.click();
        }
      });
    }

    var btnReload = document.getElementById("btnReload");
    if (btnReload) {
      btnReload.onclick = async function () {
        if (location.protocol === "file:") {
          toast("Cần chạy start.bat / server.py");
          return;
        }
        setLiveBadge("sync", "Reloading…");
        try {
          await fetch("/api/reload");
          // force re-fetch even if mtime same
          var res = await fetch("/api/data", { cache: "no-store" });
          var payload = await res.json();
          if (payload.ok && payload.data) applyLiveData(payload.data, false);
          else await pollLive();
        } catch (e) {
          toast("Cần chạy start.bat / server.py");
          setLiveBadge("err", "Reload failed");
        }
      };
    }

    // scroll-spy for nav
    var sectionIds = Object.keys(titles);
    var spyTimer = null;
    window.addEventListener(
      "scroll",
      function () {
        if (spyTimer) return;
        spyTimer = setTimeout(function () {
          spyTimer = null;
          var y = window.scrollY + 140;
          var current = "overview";
          sectionIds.forEach(function (id) {
            var el = document.getElementById(id);
            if (el && el.offsetTop <= y) current = id;
          });
          Array.prototype.forEach.call(
            document.querySelectorAll("[data-nav]"),
            function (a) {
              var id = a.getAttribute("href").slice(1);
              a.classList.toggle("active", id === current);
            }
          );
          document.getElementById("pageTitle").textContent =
            titles[current] || "Dashboard";
        }, 80);
      },
      { passive: true }
    );
  }

  document.addEventListener("DOMContentLoaded", function () {
    try {
      if (nightPref) document.body.classList.add("night");
      initSelects();
      wireEvents();
      renderAll(true);
      startLivePolling();
      if (!sessionStorage.getItem("dora_welcomed")) {
        sessionStorage.setItem("dora_welcomed", "1");
        setTimeout(function () {
          toast("Xin chào! Dashboard sẵn sàng 🐱");
        }, 400);
      }
    } catch (err) {
      console.error(err);
      toast("Lỗi: " + err.message);
      alert("Dashboard error: " + err.message);
    }
  });
})();
