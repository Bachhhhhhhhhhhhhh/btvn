# -*- coding: utf-8 -*-
"""Build index.html that embeds data and loads clean app.js."""
from pathlib import Path
import json
import shutil

root = Path(__file__).resolve().parent
data = json.loads((root / "data.json").read_text(encoding="utf-8"))
data_js = json.dumps(data, ensure_ascii=False)
app_js = (root / "app.js").read_text(encoding="utf-8")

# Validate app.js syntax via node if available
import subprocess
tmp = root / "_check.js"
tmp.write_text(app_js, encoding="utf-8")
try:
    r = subprocess.run(
        ["node", "--check", str(tmp)], capture_output=True, text=True
    )
    if r.returncode != 0:
        print("SYNTAX ERROR in app.js:\n", r.stderr)
        raise SystemExit(1)
    print("app.js syntax OK")
except FileNotFoundError:
    print("node not found — skip syntax check")
finally:
    if tmp.exists():
        tmp.unlink()

html = r'''<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>Doraemon LOG · Cute Control Room</title>
<link href="https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700;800;900&family=JetBrains+Mono:wght@500&display=swap" rel="stylesheet" />
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.6/dist/chart.umd.min.js"></script>
<link rel="stylesheet" href="styles.css" />
</head>
<body>
<span class="floaty" style="top:10%;right:3%">☁️</span>
<span class="floaty" style="bottom:20%;right:10%;font-size:28px;animation-delay:1s">☁️</span>
<span class="floaty" style="top:40%;right:6%;font-size:22px;animation-delay:2s">⭐</span>

<aside class="sidebar">
  <div class="hero">
    <svg viewBox="0 0 200 200" width="108" height="108" class="dora-svg">
      <circle cx="100" cy="100" r="92" fill="#00A0E9"/>
      <ellipse cx="100" cy="118" rx="72" ry="62" fill="#fff"/>
      <ellipse cx="78" cy="78" rx="28" ry="32" fill="#fff"/>
      <ellipse cx="122" cy="78" rx="28" ry="32" fill="#fff"/>
      <circle cx="86" cy="82" r="8" fill="#1A2B3C"/><circle cx="114" cy="82" r="8" fill="#1A2B3C"/>
      <circle cx="88" cy="80" r="2.5" fill="#fff"/><circle cx="116" cy="80" r="2.5" fill="#fff"/>
      <ellipse cx="100" cy="92" rx="10" ry="8" fill="#E60012"/>
      <path d="M100 100 V130" stroke="#1A2B3C" stroke-width="2.5"/>
      <path d="M100 108 H60 M100 108 H140 M100 118 H55 M100 118 H145 M100 128 H62 M100 128 H138" stroke="#1A2B3C" stroke-width="2" stroke-linecap="round"/>
      <path d="M72 145 Q100 170 128 145" fill="none" stroke="#1A2B3C" stroke-width="3" stroke-linecap="round"/>
      <rect x="55" y="155" width="90" height="14" rx="4" fill="#E60012"/>
      <circle cx="100" cy="172" r="12" fill="#FFD54F" stroke="#1A2B3C" stroke-width="2"/>
      <circle cx="100" cy="176" r="3" fill="#1A2B3C"/>
      <line x1="88" y1="172" x2="112" y2="172" stroke="#1A2B3C" stroke-width="2"/>
    </svg>
    <div class="k">4D Pocket · Finance</div>
    <div class="t">Doraemon LOG</div>
    <div class="s">Live Control Room v4</div>
  </div>
  <a class="nav-item active" href="#overview" data-nav><span class="ico">🏠</span>Overview</a>
  <a class="nav-item" href="#midterm" data-nav><span class="ico">🚀</span>Mid-term</a>
  <a class="nav-item" href="#compare" data-nav><span class="ico">⚖️</span>Compare</a>
  <a class="nav-item" href="#monthly" data-nav><span class="ico">📅</span>Monthly</a>
  <a class="nav-item" href="#heatmap" data-nav><span class="ico">🗺️</span>Heatmap</a>
  <a class="nav-item" href="#movers" data-nav><span class="ico">📈</span>Movers</a>
  <a class="nav-item" href="#assets" data-nav><span class="ico">📦</span>Assets</a>
  <a class="nav-item" href="#tables" data-nav><span class="ico">📋</span>Tables</a>
  <a class="nav-item" href="#favs" data-nav><span class="ico">⭐</span>Favorites</a>
  <div class="side-foot">
    <button type="button" id="btnNight">🌙 Night mode</button>
    <button type="button" id="btnExportCsv">📤 Export CSV</button>
    <button type="button" id="btnShare">📝 Copy summary</button>
    <button type="button" id="btnPrint">🖨️ Print</button>
    <button type="button" id="btnConfetti">🎉 Party</button>
  </div>
</aside>

<main class="main">
  <div class="topbar">
    <div>
      <h1 id="pageTitle">Overview</h1>
      <div class="sub">Source: <span id="srcName">—</span> · <span id="genAt">—</span> · VND</div>
    </div>
    <div class="toolbar top-live">
      <div id="liveBadge" class="live-badge off"><span class="live-dot"></span><span class="live-text">…</span></div>
      <input id="globalSearch" type="search" placeholder="🔍 Tìm asset / CC / G/L…" style="min-width:180px" />
      <label class="lbl">Focus <select id="periodFocus"></select></label>
      <button type="button" class="btn" id="btnReload">🔄 Reload Excel</button>
    </div>
  </div>

  <div class="drop-zone" id="dropZone">
    📁 Kéo thả Excel (.xlsx) vào đây để cập nhật realtime
    <small>Click để chọn file · chạy <b>py -3 server.py</b> để bật LIVE watch</small>
    <input id="fileInput" type="file" accept=".xlsx,.xlsm" hidden />
  </div>

  <div class="pocket">
    <div class="bell" id="bellBtn" title="Ring!"></div>
    <div>
      <p id="pocketText">Xin chào! Mình là Doraemon — dashboard LIVE: sửa Excel là web tự nhảy số!</p>
      <span id="liveFoot">Tip: so sánh 2 kỳ · favorites · upload Excel · server watch</span>
    </div>
  </div>

  <div class="chips" id="insightChips"></div>
  <section id="overview"><div class="kpi-grid" id="kpiGrid"></div></section>

  <section id="midterm" class="section"><div class="badge">🚀</div><div><h2>Mid-term trajectory</h2><p>103KI → 108KI</p></div></section>
  <div class="grid-2">
    <div class="card"><h3>Total KH by period</h3><div class="desc">Click cột để đổi Focus</div><div class="chart-box lg"><canvas id="chartPeriod"></canvas></div></div>
    <div class="card"><h3>Waterfall bridge</h3><div class="desc">Cầu nối giữa các kỳ</div><div class="chart-box lg"><canvas id="chartWaterfall"></canvas></div></div>
  </div>
  <div class="grid-3">
    <div class="card"><h3>By Cost Center</h3><div class="desc" id="descCC">Share Focus</div><div class="chart-box sm"><canvas id="chartCC"></canvas></div></div>
    <div class="card"><h3>By G/L class</h3><div class="desc" id="descGL">Class mix</div><div class="chart-box sm"><canvas id="chartGL"></canvas></div></div>
    <div class="card"><h3>CC over time</h3><div class="desc">Stacked</div><div class="chart-box sm"><canvas id="chartCCstack"></canvas></div></div>
  </div>
  <div class="card mb"><h3>GAP vs prior</h3><div class="desc">Tăng / giảm</div><div class="chart-box sm"><canvas id="chartGap"></canvas></div></div>

  <section id="compare" class="section"><div class="badge">⚖️</div><div><h2>Compare two periods</h2><p>Period A vs B</p></div></section>
  <div class="card mb">
    <div class="compare-box">
      <label class="lbl">Period A<select id="cmpA"></select></label>
      <div class="vs">VS</div>
      <label class="lbl">Period B<select id="cmpB"></select></label>
    </div>
    <div class="chips" id="cmpKpis"></div>
    <div class="chart-box"><canvas id="chartCompare"></canvas></div>
  </div>

  <section id="monthly" class="section"><div class="badge">📅</div><div><h2>103KI monthly</h2><p>Đường cong tháng</p></div></section>
  <div class="grid-2">
    <div class="card"><h3>Monthly total</h3><div class="desc">All CC</div><div class="chart-box"><canvas id="chartMonthly"></canvas></div></div>
    <div class="card"><h3>By Cost Center</h3><div class="desc">SGA vs FAC3</div><div class="chart-box"><canvas id="chartMonthlyCC"></canvas></div></div>
  </div>
  <div class="card mb"><h3>Monthly by G/L</h3><div class="desc">Stacked</div><div class="chart-box"><canvas id="chartMonthlyGL"></canvas></div></div>

  <section id="heatmap" class="section"><div class="badge">🗺️</div><div><h2>Heatmap</h2><p>CC × G/L intensity</p></div></section>
  <div class="card mb"><div class="heat" id="heatMap"></div></div>

  <section id="movers" class="section"><div class="badge">📈</div><div><h2>Top movers 104 vs 103</h2><p>Ai tăng / giảm mạnh</p></div></section>
  <div class="grid-2 mb">
    <div class="card"><h3>⬆️ Tăng mạnh</h3><div class="desc">GAP dương</div><div id="moversUp"></div></div>
    <div class="card"><h3>⬇️ Giảm mạnh</h3><div class="desc">GAP âm</div><div id="moversDown"></div></div>
  </div>

  <section id="assets" class="section"><div class="badge">📦</div><div><h2>Assets</h2><p>Click dòng · gắn sao · lọc trạng thái</p></div></section>
  <div class="filters">
    <select id="statusFilter">
      <option value="">All status</option>
      <option value="active">🟢 Active</option>
      <option value="ending_soon">🟡 Ending ≤24m</option>
      <option value="ended">🔴 Ended</option>
      <option value="fav">⭐ Favorites only</option>
    </select>
  </div>
  <div class="grid-21">
    <div class="card"><h3>Top 12 acquisition</h3><div class="desc">Nguyên giá</div><div class="chart-box lg"><canvas id="chartTopAssets"></canvas></div></div>
    <div class="card"><h3>Status + class mix</h3><div class="desc">Lifecycle</div><div class="chart-box lg"><canvas id="chartAssetGL"></canvas></div><div class="chips" id="statusChips" style="margin-top:10px"></div></div>
  </div>

  <section id="tables" class="section"><div class="badge">📋</div><div><h2>Tables</h2><p>Sort header · filter · export</p></div></section>
  <div class="card mb">
    <h3>Budget lines</h3><div class="desc">CC × G/L</div>
    <div class="filters">
      <select id="filterCC"><option value="">All CC</option></select>
      <select id="filterGL"><option value="">All G/L</option></select>
    </div>
    <div class="table-wrap"><table><thead id="budgetHead"></thead><tbody id="budgetBody"></tbody></table></div>
  </div>
  <div class="card mb">
    <h3>Asset list</h3><div class="desc">Search + favorites</div>
    <div class="filters"><input id="assetSearch" type="search" placeholder="Tìm asset…" style="min-width:240px"/></div>
    <div class="table-wrap">
      <table>
        <thead><tr>
          <th></th><th data-sort="code">Code</th><th data-sort="name">Asset</th><th>CC</th><th>Class</th><th>Status</th>
          <th class="num" data-sort="cost">Acquisition</th><th class="num" data-sort="life">Life</th>
          <th class="num" data-sort="totalAll">Σ MT</th>
        </tr></thead>
        <tbody id="assetBody"></tbody>
      </table>
    </div>
  </div>

  <section id="favs" class="section"><div class="badge">⭐</div><div><h2>Favorites</h2><p>Lưu trên máy (localStorage)</p></div></section>
  <div class="card"><div id="favList" class="desc">Chưa có favorite — bấm ⭐ trên bảng asset!</div></div>

  <footer>
    <div>🐱 Doraemon LOG Control Room v4 · LIVE + cute</div>
    <div class="mono" id="footMeta">—</div>
  </footer>
</main>

<div class="helper" id="helper">
  <div class="face">
    <svg viewBox="0 0 200 200" width="42" height="42">
      <circle cx="100" cy="100" r="92" fill="#00A0E9"/><ellipse cx="100" cy="118" rx="70" ry="60" fill="#fff"/>
      <circle cx="86" cy="82" r="8" fill="#1A2B3C"/><circle cx="114" cy="82" r="8" fill="#1A2B3C"/>
      <ellipse cx="100" cy="92" rx="10" ry="8" fill="#E60012"/>
    </svg>
    <div class="bubble" id="helperText">Mẹo từ túi thần kỳ~</div>
  </div>
  <div class="actions">
    <button class="btn yellow" type="button" id="helperNext">Mẹo khác ✨</button>
    <button class="btn" type="button" id="helperHide">Ẩn</button>
  </div>
</div>

<div class="modal-bg" id="modalBg">
  <div class="modal">
    <button class="btn" id="modalClose" type="button" style="float:right">Đóng</button>
    <h3 id="modalTitle">Asset</h3>
    <div id="modalSub" class="desc"></div>
    <div id="modalBody"></div>
    <div class="chart-box sm" style="margin-top:12px"><canvas id="chartAssetDetail"></canvas></div>
  </div>
</div>
<div class="toast" id="toast"></div>
<div class="confetti" id="confetti"></div>

<script>const DATA = __DATA_JSON__;</script>
<script src="app.js"></script>
</body>
</html>
'''

html = html.replace("__DATA_JSON__", data_js)
(root / "index.html").write_text(html, encoding="utf-8")

# Also embed app.js inline as fallback for file:// quirks? Separate app.js works with file:// for same folder.
# Copy styles if missing - write styles.css from previous CSS in build

styles = (root / "styles.css")
if not styles.exists() or True:
    # extract styles from a compact source - write essential CSS file
    pass

print("Built index.html", (root / "index.html").stat().st_size)
print("app.js", (root / "app.js").stat().st_size)
