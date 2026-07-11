# -*- coding: utf-8 -*-
"""Build cuter Doraemon dashboard v3 with more features."""
from pathlib import Path
import json

root = Path(__file__).resolve().parent
data_js = json.dumps(json.loads((root / "data.json").read_text(encoding="utf-8")), ensure_ascii=False)

# Write HTML in parts to avoid huge single edit issues
parts = []

parts.append(r'''<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>Doraemon LOG · Cute Control Room</title>
<link href="https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700;800;900&family=JetBrains+Mono:wght@500&display=swap" rel="stylesheet" />
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.6/dist/chart.umd.min.js"></script>
<style>
:root{
  --blue:#00A0E9;--blue2:#0077C8;--blue3:#005A9E;--sky:#EAF7FF;--sky2:#B3E5FC;
  --red:#E60012;--yellow:#FFD54F;--gold:#F9A825;--pink:#FFC1D4;--ink:#1A2B3C;
  --muted:#5A7A94;--white:#fff;--soft:#F0FAFF;--shadow:0 14px 36px rgba(0,90,158,.16);
  --sidebar:270px;--radius:24px;
}
*{box-sizing:border-box;margin:0;padding:0}
body{
  font-family:Nunito,system-ui,sans-serif;color:var(--ink);min-height:100vh;display:flex;
  background:
    radial-gradient(circle at 8% 12%,#fff 0 22px,transparent 23px),
    radial-gradient(circle at 92% 20%,#fff 0 16px,transparent 17px),
    radial-gradient(circle at 78% 78%,#fff 0 28px,transparent 29px),
    linear-gradient(165deg,#EAF8FF 0%,#B9E6FF 45%,#7EC8F0 100%);
  background-attachment:fixed;
}
body.night{
  background:linear-gradient(165deg,#0B1A2A 0%,#123048 50%,#0B1A2A 100%);
  color:#E8F4FF;
}
body.night .card,body.night .topbar,body.night .pocket,body.night .helper,body.night .modal,body.night footer{
  background:rgba(15,35,55,.92)!important;color:#E8F4FF;border-color:rgba(255,255,255,.12)!important;
}
body.night .kpi{background:rgba(15,35,55,.92)!important;border-color:rgba(255,255,255,.12)!important}
body.night th{background:linear-gradient(180deg,#0077C8,#005A9E)!important}
body.night td{border-color:rgba(255,255,255,.08);color:#E8F4FF}
body.night .kpi-value,body.night .card h3,body.night .section h2,body.night .topbar h1{color:#B3E5FC!important}
body.night .muted,body.night .desc,body.night .kpi-hint,body.night .sub{color:#8FB3CC!important}
.mono{font-family:"JetBrains Mono",monospace}

/* Sidebar */
.sidebar{
  width:var(--sidebar);position:fixed;inset:0 auto 0 0;z-index:40;
  background:linear-gradient(180deg,#00A0E9 0%,#0077C8 55%,#005A9E 100%);
  color:#fff;padding:16px 12px;display:flex;flex-direction:column;gap:4px;
  box-shadow:10px 0 40px rgba(0,90,158,.28);overflow:auto;
}
.hero{text-align:center;padding:6px 6px 14px;border-bottom:2px dashed rgba(255,255,255,.28);margin-bottom:8px}
.hero svg{filter:drop-shadow(0 8px 10px rgba(0,0,0,.18));animation:bob 3.2s ease-in-out infinite}
@keyframes bob{0%,100%{transform:translateY(0)}50%{transform:translateY(-6px)}}
.hero .k{font-size:10px;font-weight:900;letter-spacing:.16em;color:var(--yellow);text-transform:uppercase}
.hero .t{font-size:20px;font-weight:900;margin-top:4px}
.hero .s{font-size:12px;opacity:.9;font-weight:700;margin-top:2px}
.nav-item{
  display:flex;align-items:center;gap:10px;padding:10px 12px;border-radius:999px;
  color:rgba(255,255,255,.92);text-decoration:none;font-size:13px;font-weight:800;
  border:2px solid transparent;transition:.18s;
}
.nav-item:hover{background:rgba(255,255,255,.14);transform:translateX(3px)}
.nav-item.active{background:#fff;color:var(--blue2);border-color:var(--yellow);box-shadow:0 6px 14px rgba(0,0,0,.12)}
.nav-item .ico{width:30px;height:30px;border-radius:50%;display:grid;place-items:center;background:rgba(255,255,255,.18);font-size:15px}
.nav-item.active .ico{background:var(--sky)}
.side-foot{margin-top:auto;display:grid;gap:8px;padding-top:10px}
.side-foot button,.btn,.toolbar button{
  cursor:pointer;font-family:inherit;font-weight:800;font-size:12.5px;border-radius:999px;
  padding:10px 12px;border:2px solid rgba(255,255,255,.28);background:rgba(255,255,255,.14);color:#fff;transition:.15s
}
.side-foot button:hover{background:#fff;color:var(--blue2)}
.btn{border:2px solid #fff;background:#fff;color:var(--blue2);box-shadow:0 3px 0 rgba(0,119,200,.15)}
.btn:hover{transform:translateY(-1px)}
.btn.primary{background:linear-gradient(135deg,var(--red),#ff4d5a);color:#fff;border:none;box-shadow:0 6px 14px rgba(230,0,18,.25)}
.btn.yellow{background:linear-gradient(135deg,var(--yellow),#ffe082);color:#5D4037;border:none}

.main{margin-left:var(--sidebar);flex:1;min-width:0;padding:18px 22px 56px;position:relative;z-index:1}
.topbar{
  display:flex;flex-wrap:wrap;align-items:center;justify-content:space-between;gap:12px;
  background:rgba(255,255,255,.88);backdrop-filter:blur(12px);border:3px solid #fff;
  border-radius:28px;padding:14px 18px;margin-bottom:14px;box-shadow:var(--shadow)
}
.topbar h1{font-size:23px;font-weight:900;color:var(--blue3)}
.sub{font-size:12.5px;color:var(--muted);font-weight:700;margin-top:2px}
.toolbar{display:flex;flex-wrap:wrap;gap:8px;align-items:center}
.toolbar select,.toolbar input, .filters select,.filters input{
  font-family:inherit;font-weight:800;font-size:13px;background:var(--sky);color:var(--ink);
  border:2px solid #fff;border-radius:999px;padding:9px 14px;outline:none;box-shadow:0 2px 0 var(--dora-line,rgba(0,119,200,.12))
}
.toolbar select:focus,.toolbar input:focus{border-color:var(--blue)}

.pocket{
  display:flex;align-items:center;gap:12px;background:linear-gradient(90deg,#fff,var(--sky));
  border:3px solid var(--blue);border-radius:999px;padding:10px 16px 10px 10px;margin-bottom:14px;box-shadow:var(--shadow)
}
.bell{width:46px;height:46px;border-radius:50%;flex-shrink:0;position:relative;
  background:radial-gradient(circle at 35% 30%,#ffe082,var(--gold));border:3px solid var(--ink);
  animation:jiggle 4s ease-in-out infinite}
@keyframes jiggle{0%,90%,100%{transform:rotate(0)}93%{transform:rotate(8deg)}96%{transform:rotate(-8deg)}}
.bell:before{content:"";position:absolute;left:8px;right:8px;top:48%;height:3px;background:var(--ink);border-radius:2px}
.bell:after{content:"";position:absolute;left:50%;bottom:6px;transform:translateX(-50%);width:10px;height:10px;border-radius:50%;background:var(--ink)}
.pocket p{font-size:13px;font-weight:800;color:var(--blue3);line-height:1.35}
.pocket span{display:block;font-size:12px;color:var(--muted);font-weight:700;margin-top:2px}

.kpi-grid{display:grid;grid-template-columns:repeat(6,1fr);gap:11px;margin-bottom:14px}
@media(max-width:1200px){.kpi-grid{grid-template-columns:repeat(3,1fr)}}
@media(max-width:720px){.sidebar{display:none}.main{margin-left:0}.kpi-grid{grid-template-columns:1fr 1fr}}
.kpi{background:#fff;border:3px solid #fff;border-radius:22px;padding:13px;box-shadow:var(--shadow);position:relative;overflow:hidden;transition:.2s}
.kpi:hover{transform:translateY(-3px)}
.kpi:before{content:"";position:absolute;right:-14px;top:-14px;width:58px;height:58px;border-radius:50%;background:var(--sky2);opacity:.5}
.kpi:nth-child(1){border-bottom:5px solid var(--blue)}
.kpi:nth-child(2){border-bottom:5px solid var(--red)}
.kpi:nth-child(3){border-bottom:5px solid var(--gold)}
.kpi:nth-child(4){border-bottom:5px solid #7C4DFF}
.kpi:nth-child(5){border-bottom:5px solid var(--pink)}
.kpi:nth-child(6){border-bottom:5px solid #26A69A}
.kpi-label{font-size:10px;font-weight:900;letter-spacing:.06em;text-transform:uppercase;color:var(--muted);position:relative}
.kpi-value{font-size:18px;font-weight:900;margin-top:5px;color:var(--blue3);position:relative;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.kpi-hint{font-size:11px;color:var(--muted);margin-top:3px;font-weight:700;position:relative}
.kpi-value.pos{color:#00897B}.kpi-value.neg{color:var(--red)}

.grid-2{display:grid;grid-template-columns:1.35fr 1fr;gap:12px;margin-bottom:12px}
.grid-3{display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;margin-bottom:12px}
.grid-21{display:grid;grid-template-columns:1fr 1.15fr;gap:12px;margin-bottom:12px}
@media(max-width:1100px){.grid-2,.grid-3,.grid-21{grid-template-columns:1fr}}
.card{background:rgba(255,255,255,.95);border:3px solid #fff;border-radius:var(--radius);padding:15px;box-shadow:var(--shadow);position:relative}
.card:after{content:"";position:absolute;left:16px;right:16px;top:0;height:5px;border-radius:0 0 10px 10px;background:linear-gradient(90deg,var(--blue),var(--sky2),var(--yellow),var(--red))}
.card h3{font-size:14.5px;font-weight:900;color:var(--blue3)}
.card .desc{font-size:12px;color:var(--muted);margin:2px 0 11px;font-weight:700}
.chart-box{position:relative;height:270px}
.chart-box.sm{height:230px}.chart-box.lg{height:300px}

.section{margin:18px 0 8px;display:flex;align-items:center;gap:10px;flex-wrap:wrap}
.section .badge{width:38px;height:38px;border-radius:50%;background:var(--blue);color:#fff;display:grid;place-items:center;font-weight:900;border:3px solid #fff;box-shadow:0 4px 0 var(--blue2);font-size:16px}
.section h2{font-size:18px;font-weight:900;color:var(--blue3)}
.section p{width:100%;margin-left:48px;margin-top:-4px;color:var(--muted);font-size:12.5px;font-weight:700}

.chips{display:flex;flex-wrap:wrap;gap:8px;margin-bottom:12px}
.chip{background:#fff;border:2px solid #fff;border-radius:999px;padding:8px 12px;font-size:12px;font-weight:800;box-shadow:var(--shadow);display:flex;align-items:center;gap:6px}
.chip b{color:var(--blue3)}.chip.up b{color:#00897B}.chip.down b{color:var(--red)}
.chip .emoji{font-size:15px}

.mover{display:flex;justify-content:space-between;align-items:center;gap:8px;padding:9px 10px;border-radius:14px;background:var(--soft);margin-bottom:6px;border:2px solid #fff;font-size:12.5px;font-weight:800}
.mover .amt{font-family:monospace;font-size:12px}
.mover.up .amt{color:#00897B}.mover.down .amt{color:var(--red)}

.heat{display:grid;gap:4px;overflow:auto;grid-template-columns:170px repeat(6,minmax(68px,1fr));font-size:11px}
.heat .h{color:var(--muted);font-weight:900;text-align:center;padding:6px}
.heat .r{color:var(--blue3);font-weight:800;padding:6px 8px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.heat .c{text-align:center;padding:8px 4px;border-radius:12px;font-family:monospace;font-size:10.5px;font-weight:800;border:2px solid #fff}

.table-wrap{overflow:auto;max-height:420px;border-radius:16px;border:2px solid var(--sky2);background:#fff}
table{width:100%;border-collapse:collapse;font-size:12.5px}
th{position:sticky;top:0;z-index:1;background:linear-gradient(180deg,var(--blue),var(--blue2));color:#fff;text-align:left;padding:11px 12px;font-size:11px;font-weight:900;text-transform:uppercase;letter-spacing:.03em;white-space:nowrap;cursor:pointer;user-select:none}
th:hover{filter:brightness(1.08)}
td{padding:9px 12px;border-bottom:1px solid var(--sky);font-weight:700}
tr:nth-child(even) td{background:rgba(0,160,233,.04)}
tr:hover td{background:rgba(255,213,79,.22)}
td.num,th.num{text-align:right;font-family:monospace;font-size:11.5px}
td.name{max-width:210px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.tag{display:inline-block;padding:3px 10px;border-radius:999px;font-size:11px;font-weight:900;background:var(--sky);color:var(--blue2);border:2px solid #fff}
.tag.blue{background:#E3F2FD;color:#1565C0}.tag.violet{background:#F3E5F5;color:#7B1FA2}
.tag.gold{background:#FFF8E1;color:#F9A825}.tag.red{background:#FFEBEE;color:var(--red)}
.tag.green{background:#E8F5E9;color:#2E7D32}
.pos{color:#00897B;font-weight:900}.neg{color:var(--red);font-weight:900}
.star{cursor:pointer;font-size:16px;filter:grayscale(1);transition:.15s}.star.on{filter:none;transform:scale(1.15)}
.filters{display:flex;flex-wrap:wrap;gap:8px;margin-bottom:10px}

/* Helper bubble */
.helper{
  position:fixed;right:18px;bottom:18px;z-index:45;width:min(320px,calc(100vw - 36px));
  background:#fff;border:4px solid var(--blue);border-radius:24px;padding:14px 14px 12px;
  box-shadow:var(--shadow);animation:pop .35s ease;
}
@keyframes pop{from{transform:scale(.9);opacity:0}to{transform:scale(1);opacity:1}}
.helper .face{display:flex;gap:10px;align-items:flex-start}
.helper .bubble{flex:1;font-size:12.5px;font-weight:800;color:var(--blue3);line-height:1.4}
.helper .actions{display:flex;gap:6px;margin-top:10px;flex-wrap:wrap}
.helper .mini{width:42px;height:42px;flex-shrink:0}
.helper.hidden{display:none}

.modal-bg{display:none;position:fixed;inset:0;z-index:60;background:rgba(0,70,120,.48);align-items:center;justify-content:center;padding:18px}
.modal-bg.show{display:flex}
.modal{background:#fff;width:min(580px,100%);max-height:86vh;overflow:auto;border-radius:28px;padding:20px;border:4px solid var(--blue);box-shadow:0 22px 50px rgba(0,90,158,.3)}
.modal h3{font-size:18px;font-weight:900;color:var(--blue3);margin:4px 0}
.modal .row{display:flex;justify-content:space-between;gap:10px;padding:9px 0;border-bottom:1px dashed var(--sky2);font-size:13px;font-weight:800}
.modal .row span:first-child{color:var(--muted)}

footer{margin-top:24px;padding:12px 16px;background:rgba(255,255,255,.8);border-radius:999px;border:2px solid #fff;color:var(--muted);font-size:12px;font-weight:800;display:flex;justify-content:space-between;flex-wrap:wrap;gap:8px;box-shadow:var(--shadow)}
.toast{position:fixed;bottom:22px;left:50%;transform:translate(-50%,12px);z-index:80;background:var(--blue2);color:#fff;padding:12px 18px;border-radius:999px;font-weight:900;font-size:13px;border:3px solid #fff;box-shadow:var(--shadow);opacity:0;transition:.25s;pointer-events:none}
.toast.show{opacity:1;transform:translate(-50%,0)}
.confetti{position:fixed;inset:0;pointer-events:none;z-index:70;overflow:hidden}
.confetti i{position:absolute;top:-12px;width:10px;height:10px;border-radius:3px;animation:fall linear forwards}
@keyframes fall{to{transform:translateY(110vh) rotate(720deg);opacity:.2}}
.floaty{position:fixed;z-index:0;pointer-events:none;opacity:.5;font-size:40px;animation:float 6s ease-in-out infinite}
@keyframes float{0%,100%{transform:translateY(0)}50%{transform:translateY(-14px)}}
.compare-box{display:grid;grid-template-columns:1fr auto 1fr;gap:10px;align-items:end;margin-bottom:10px}
.compare-box .vs{font-weight:900;color:var(--red);padding-bottom:10px;text-align:center}
</style>
</head>
<body>
<span class="floaty" style="top:10%;right:3%;animation-delay:0s">☁️</span>
<span class="floaty" style="bottom:20%;right:10%;font-size:28px;animation-delay:1s">☁️</span>
<span class="floaty" style="top:40%;right:6%;font-size:22px;animation-delay:2s">⭐</span>

<aside class="sidebar">
  <div class="hero">
    <svg class="mini" viewBox="0 0 200 200" width="108" height="108">
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
    <div class="s">Cute Control Room v3</div>
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
    <div class="toolbar">
      <input id="globalSearch" type="search" placeholder="🔍 Tìm asset / CC / G/L…" style="min-width:200px" />
      <label style="font-size:12px;font-weight:900;color:var(--muted)">Focus
        <select id="periodFocus"></select>
      </label>
    </div>
  </div>

  <div class="pocket">
    <div class="bell" id="bellBtn" title="Ring!"></div>
    <div>
      <p id="pocketText">Xin chào! Mình là Doraemon — cùng xem khấu hao LOG thật dễ thương nhé!</p>
      <span>Tip: so sánh 2 kỳ · gắn sao favorites · xem tài sản sắp hết khấu hao</span>
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
    <div class="card"><h3>By Cost Center</h3><div class="desc" id="descCC">Focus period</div><div class="chart-box sm"><canvas id="chartCC"></canvas></div></div>
    <div class="card"><h3>By G/L</h3><div class="desc" id="descGL">Class mix</div><div class="chart-box sm"><canvas id="chartGL"></canvas></div></div>
    <div class="card"><h3>CC over time</h3><div class="desc">Stacked</div><div class="chart-box sm"><canvas id="chartCCstack"></canvas></div></div>
  </div>
  <div class="card" style="margin-bottom:12px"><h3>GAP vs prior</h3><div class="desc">Tăng / giảm</div><div class="chart-box sm"><canvas id="chartGap"></canvas></div></div>

  <section id="compare" class="section"><div class="badge">⚖️</div><div><h2>Compare two periods</h2><p>Chọn Period A vs B</p></div></section>
  <div class="card" style="margin-bottom:12px">
    <div class="compare-box">
      <label style="font-weight:900;font-size:12px;color:var(--muted)">Period A<select id="cmpA" style="width:100%;margin-top:4px"></select></label>
      <div class="vs">VS</div>
      <label style="font-weight:900;font-size:12px;color:var(--muted)">Period B<select id="cmpB" style="width:100%;margin-top:4px"></select></label>
    </div>
    <div class="chips" id="cmpKpis"></div>
    <div class="chart-box"><canvas id="chartCompare"></canvas></div>
  </div>

  <section id="monthly" class="section"><div class="badge">📅</div><div><h2>103KI monthly</h2><p>Đường cong tháng</p></div></section>
  <div class="grid-2">
    <div class="card"><h3>Monthly total</h3><div class="desc">All CC</div><div class="chart-box"><canvas id="chartMonthly"></canvas></div></div>
    <div class="card"><h3>By Cost Center</h3><div class="desc">SGA vs FAC3</div><div class="chart-box"><canvas id="chartMonthlyCC"></canvas></div></div>
  </div>
  <div class="card" style="margin-bottom:12px"><h3>Monthly by G/L</h3><div class="desc">Stacked classes</div><div class="chart-box"><canvas id="chartMonthlyGL"></canvas></div></div>

  <section id="heatmap" class="section"><div class="badge">🗺️</div><div><h2>Heatmap</h2><p>CC × G/L intensity</p></div></section>
  <div class="card" style="margin-bottom:12px"><div class="heat" id="heatMap"></div></div>

  <section id="movers" class="section"><div class="badge">📈</div><div><h2>Top movers 104 vs 103</h2><p>Ai tăng / giảm mạnh nhất</p></div></section>
  <div class="grid-2" style="margin-bottom:12px">
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
    <div class="card"><h3>Status + class mix</h3><div class="desc">Lifecycle snapshot</div><div class="chart-box lg"><canvas id="chartAssetGL"></canvas></div>
      <div class="chips" id="statusChips" style="margin-top:10px"></div>
    </div>
  </div>

  <section id="tables" class="section"><div class="badge">📋</div><div><h2>Tables</h2><p>Sort header · filter · export</p></div></section>
  <div class="card" style="margin-bottom:12px">
    <h3>Budget lines</h3><div class="desc">Click header để sort</div>
    <div class="filters">
      <select id="filterCC"><option value="">All CC</option></select>
      <select id="filterGL"><option value="">All G/L</option></select>
    </div>
    <div class="table-wrap"><table><thead id="budgetHead"></thead><tbody id="budgetBody"></tbody></table></div>
  </div>
  <div class="card" style="margin-bottom:12px">
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

  <section id="favs" class="section"><div class="badge">⭐</div><div><h2>Favorites</h2><p>Lưu trên máy bạn (localStorage)</p></div></section>
  <div class="card"><div id="favList" class="desc">Chưa có favorite — bấm ⭐ trên bảng asset nhé!</div></div>

  <footer>
    <div>🐱 Doraemon LOG Control Room v3 · đáng yêu &amp; nhiều tính năng</div>
    <div class="mono" id="footMeta">—</div>
  </footer>
</main>

<div class="helper" id="helper">
  <div class="face">
    <svg class="mini" viewBox="0 0 200 200" width="42" height="42">
      <circle cx="100" cy="100" r="92" fill="#00A0E9"/><ellipse cx="100" cy="118" rx="70" ry="60" fill="#fff"/>
      <circle cx="86" cy="82" r="8" fill="#1A2B3C"/><circle cx="114" cy="82" r="8" fill="#1A2B3C"/>
      <ellipse cx="100" cy="92" rx="10" ry="8" fill="#E60012"/>
    </svg>
    <div class="bubble" id="helperText">Mẹo từ túi thần kỳ sẽ hiện ở đây~</div>
  </div>
  <div class="actions">
    <button class="btn yellow" type="button" id="helperNext" style="padding:7px 12px">Mẹo khác ✨</button>
    <button class="btn" type="button" id="helperHide" style="padding:7px 12px">Ẩn</button>
  </div>
</div>

<div class="modal-bg" id="modalBg">
  <div class="modal">
    <button class="btn close" id="modalClose" type="button" style="float:right">Đóng</button>
    <h3 id="modalTitle">Asset</h3>
    <div id="modalSub" class="desc"></div>
    <div id="modalBody"></div>
    <div class="chart-box sm" style="margin-top:12px"><canvas id="chartAssetDetail"></canvas></div>
  </div>
</div>
<div class="toast" id="toast"></div>
<div class="confetti" id="confetti"></div>
''')

# JS part
parts.append(r'''
<script>
const DATA = __DATA_JSON__;
const periods = DATA.meta.periods;
const colors = ["#00A0E9","#E60012","#FFD54F","#7C4DFF","#26A69A","#FF8A65","#42A5F5","#EC407A","#66BB6A"];
let charts = {}, focusPeriod = periods[0], assetDetailChart = null;
let assetSort = {key:"cost", dir:-1};
let favs = new Set(JSON.parse(localStorage.getItem("dora_favs") || "[]"));
let helperIdx = 0;

const tips = [
  "Bấm chuông 🔔 để Doraemon reo lên và nhận insight ngẫu nhiên!",
  "Dùng Compare để soi 2 kỳ bất kỳ — rất tiện khi thuyết trình.",
  "Gắn ⭐ asset quan trọng — xem lại ở mục Favorites.",
  "Cột Ending ≤24m giúp phát hiện TS sắp hết khấu hao.",
  "Export CSV mang bảng budget sang Excel trong 1 nốt nhạc.",
  "Night mode xem về đêm cũng dịu mắt nè 🌙",
  ...(DATA.insights || []),
];

function bn(v){if(v==null||isNaN(v))return"—";const n=+v,a=Math.abs(n);if(a>=1e12)return(n/1e12).toFixed(2)+"T";if(a>=1e9)return(n/1e9).toFixed(2)+"B";if(a>=1e6)return(n/1e6).toFixed(2)+"M";if(a>=1e3)return(n/1e3).toFixed(1)+"K";return n.toLocaleString("en-US",{maximumFractionDigits:0})}
function full(v){if(v==null||isNaN(v))return"—";return(+v).toLocaleString("en-US",{maximumFractionDigits:0})}
function toast(m){const el=document.getElementById("toast");el.textContent=m;el.classList.add("show");setTimeout(()=>el.classList.remove("show"),2400)}
function destroy(k){if(charts[k]){charts[k].destroy();delete charts[k]}}
function gVal(p){return DATA.kpi.grand?.[p]??DATA.kpi.byPeriod[p]??0}
function saveFavs(){localStorage.setItem("dora_favs",JSON.stringify([...favs]))}
function ringBell(){
  try{
    const ctx=new (window.AudioContext||window.webkitAudioContext)();
    const o=ctx.createOscillator(), g=ctx.createGain();
    o.type="sine"; o.frequency.value=880; g.gain.value=0.04;
    o.connect(g); g.connect(ctx.destination); o.start();
    o.frequency.exponentialRampToValueAtTime(1320, ctx.currentTime+0.08);
    g.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime+0.35);
    o.stop(ctx.currentTime+0.36);
  }catch(e){}
}

Chart.defaults.color="#5A7A94";
Chart.defaults.borderColor="rgba(0,160,233,.12)";
Chart.defaults.font.family="'Nunito',system-ui,sans-serif";

// Period selects
["periodFocus","cmpA","cmpB"].forEach(id=>{
  const sel=document.getElementById(id);
  periods.forEach(p=>{const o=document.createElement("option");o.value=p;o.textContent=p;sel.appendChild(o)});
});
document.getElementById("periodFocus").value=focusPeriod;
document.getElementById("cmpA").value=periods[0];
document.getElementById("cmpB").value=periods[1]||periods[0];
document.getElementById("periodFocus").onchange=()=>{focusPeriod=document.getElementById("periodFocus").value;renderAll(false);toast("Focus: "+focusPeriod+" 🔔")};
document.getElementById("cmpA").onchange=document.getElementById("cmpB").onchange=()=>renderCompare();

function renderKPI(){
  const gF=gVal(focusPeriod), g103=gVal("103Ki");
  const idx=periods.indexOf(focusPeriod);
  const prev=idx>0?gVal(periods[idx-1]):null;
  const gap=prev==null?0:gF-prev;
  const sc=DATA.kpi.statusCounts||{};
  const items=[
    {l:"Focus KH",v:bn(gF),h:focusPeriod+" · "+full(gF),c:""},
    {l:"103KI baseline",v:bn(g103),h:full(g103)+" VND",c:""},
    {l:"MT total",v:bn(DATA.kpi.totalMT),h:"103–108 sum",c:""},
    {l:"GAP vs prior",v:(gap>=0?"+":"")+bn(gap),h:prev==null?"First period":full(gap),c:gap>0?"pos":(gap<0?"neg":"")},
    {l:"Assets",v:String(DATA.kpi.assetCount),h:"🟡 "+(sc.ending_soon||0)+" ending soon",c:""},
    {l:"Acquisition",v:bn(DATA.kpi.totalAcquisition),h:"Nguyên giá portfolio",c:""},
  ];
  document.getElementById("kpiGrid").innerHTML=items.map(i=>`<div class="kpi"><div class="kpi-label">${i.l}</div><div class="kpi-value mono ${i.c}">${i.v}</div><div class="kpi-hint">${i.h}</div></div>`).join("");
}

function renderInsights(){
  document.getElementById("insightChips").innerHTML=(DATA.insights||[]).map((t,i)=>`<div class="chip"><span class="emoji">${["💡","📌","✨","🔔","🎯"][i%5]}</span><span>${t}</span></div>`).join("");
}

function renderPeriod(){
  destroy("period");
  const vals=periods.map(gVal);
  charts.period=new Chart(document.getElementById("chartPeriod"),{type:"bar",data:{labels:periods,datasets:[{data:vals,backgroundColor:periods.map(p=>p===focusPeriod?"#00A0E9":"rgba(0,160,233,.32)"),borderRadius:14,borderSkipped:false}]},options:{responsive:true,maintainAspectRatio:false,onClick:(_,els)=>{if(!els.length)return;focusPeriod=periods[els[0].index];document.getElementById("periodFocus").value=focusPeriod;renderAll(false);toast("Focus: "+focusPeriod)},plugins:{legend:{display:false},tooltip:{callbacks:{label:c=>" "+full(c.raw)+" VND"}}},scales:{x:{grid:{display:false},ticks:{font:{weight:"800"}}},y:{ticks:{callback:v=>bn(v)},grid:{color:"rgba(0,160,233,.08)"}}}}});
}

function renderWaterfall(){
  destroy("wf");
  const wf=DATA.waterfall||[]; const labels=wf.map(x=>x.label); const base=[],mid=[],cols=[]; let run=0;
  wf.forEach(s=>{
    if(s.type==="total"){base.push(0);mid.push(s.value);cols.push("#00A0E9");run=s.value}
    else if(s.value>=0){base.push(run);mid.push(s.value);cols.push("#26A69A");run+=s.value}
    else{base.push(run+s.value);mid.push(-s.value);cols.push("#E60012");run+=s.value}
  });
  charts.wf=new Chart(document.getElementById("chartWaterfall"),{type:"bar",data:{labels,datasets:[{data:base,backgroundColor:"transparent",stack:"w",barPercentage:.72},{data:mid,backgroundColor:cols,stack:"w",borderRadius:8,barPercentage:.72}]},options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false},tooltip:{filter:i=>i.datasetIndex===1,callbacks:{label:c=>{const s=wf[c.dataIndex];return" "+(s.type==="delta"?(s.value>=0?"+":"")+full(s.value):full(s.value))}}}},scales:{x:{stacked:true,grid:{display:false},ticks:{font:{size:10,weight:"800"}}},y:{stacked:true,ticks:{callback:v=>bn(v)},grid:{color:"rgba(0,160,233,.08)"}}}}});
}

function sumBy(field,period){const m={};DATA.budgetRows.forEach(r=>{m[r[field]]=(m[r[field]]||0)+(r.values[period]||0)});return m}
function renderPies(){
  destroy("cc");destroy("gl");
  document.getElementById("descCC").textContent="Share · "+focusPeriod;
  document.getElementById("descGL").textContent="Class · "+focusPeriod;
  const mk=(id,map,key)=>{const labels=Object.keys(map),vals=labels.map(k=>map[k]);
    charts[key]=new Chart(document.getElementById(id),{type:"doughnut",data:{labels,datasets:[{data:vals,backgroundColor:colors,borderWidth:4,borderColor:"#fff",hoverOffset:7}]},options:{responsive:true,maintainAspectRatio:false,cutout:"58%",plugins:{legend:{position:"bottom",labels:{boxWidth:12,font:{weight:"800",size:11}}},tooltip:{callbacks:{label:c=>{const t=vals.reduce((a,b)=>a+b,0)||1;return` ${c.label}: ${bn(c.raw)} (${(c.raw/t*100).toFixed(1)}%)`}}}}})};
  mk("chartCC",sumBy("ccName",focusPeriod),"cc");
  mk("chartGL",sumBy("glName",focusPeriod),"gl");
}
function renderStack(){
  destroy("stack");const ccs=Object.keys(DATA.byCC);
  charts.stack=new Chart(document.getElementById("chartCCstack"),{type:"bar",data:{labels:periods,datasets:ccs.map((cc,i)=>({label:cc,data:periods.map(p=>DATA.byCC[cc][p]||0),backgroundColor:colors[i%colors.length],stack:"s",borderRadius:4}))},options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{position:"bottom",labels:{boxWidth:10,font:{weight:"800",size:10}}},tooltip:{callbacks:{label:c=>` ${c.dataset.label}: ${bn(c.raw)}`}}},scales:{x:{stacked:true,grid:{display:false}},y:{stacked:true,ticks:{callback:v=>bn(v)},grid:{color:"rgba(0,160,233,.08)"}}}}});
}
function renderGap(){
  destroy("gap");const gaps=[];for(let i=1;i<periods.length;i++)gaps.push(gVal(periods[i])-gVal(periods[i-1]));
  charts.gap=new Chart(document.getElementById("chartGap"),{type:"bar",data:{labels:periods.slice(1).map((p,i)=>p+" vs "+periods[i]),datasets:[{data:gaps,backgroundColor:gaps.map(v=>v>=0?"#26A69A":"#E60012"),borderRadius:12}]},options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false},tooltip:{callbacks:{label:c=>" "+full(c.raw)}}},scales:{x:{grid:{display:false},ticks:{font:{weight:"800"}}},y:{ticks:{callback:v=>bn(v)},grid:{color:"rgba(0,160,233,.08)"}}}}});
}
function renderMonthly(){
  destroy("mTot");destroy("mCC");destroy("mGL");
  charts.mTot=new Chart(document.getElementById("chartMonthly"),{type:"line",data:{labels:DATA.monthly.labels,datasets:[{data:DATA.monthly.total,borderColor:"#00A0E9",backgroundColor:"rgba(0,160,233,.16)",fill:true,tension:.4,pointRadius:4,pointBackgroundColor:"#FFD54F",pointBorderColor:"#00A0E9",pointBorderWidth:2,borderWidth:3}]},options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false},tooltip:{callbacks:{label:c=>" "+full(c.raw)}}},scales:{x:{grid:{display:false}},y:{ticks:{callback:v=>bn(v)},grid:{color:"rgba(0,160,233,.08)"}}}}});
  const byCC={};DATA.monthly.rows.forEach(r=>{if(!byCC[r.ccName])byCC[r.ccName]=DATA.monthly.labels.map(()=>0);r.months.forEach((v,i)=>byCC[r.ccName][i]+=v)});
  charts.mCC=new Chart(document.getElementById("chartMonthlyCC"),{type:"line",data:{labels:DATA.monthly.labels,datasets:Object.keys(byCC).map((k,i)=>({label:k,data:byCC[k],borderColor:colors[i%colors.length],tension:.4,pointRadius:3,borderWidth:3,backgroundColor:"transparent"}))},options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{position:"bottom",labels:{boxWidth:12,font:{weight:"800"}}},tooltip:{callbacks:{label:c=>` ${c.dataset.label}: ${bn(c.raw)}`}}},scales:{x:{grid:{display:false}},y:{ticks:{callback:v=>bn(v)},grid:{color:"rgba(0,160,233,.08)"}}}}});
  const byGL={};DATA.monthly.rows.forEach(r=>{if(!byGL[r.glName])byGL[r.glName]=DATA.monthly.labels.map(()=>0);r.months.forEach((v,i)=>byGL[r.glName][i]+=v)});
  charts.mGL=new Chart(document.getElementById("chartMonthlyGL"),{type:"bar",data:{labels:DATA.monthly.labels,datasets:Object.keys(byGL).map((k,i)=>({label:k,data:byGL[k],backgroundColor:colors[i%colors.length],stack:"m",borderRadius:4}))},options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{position:"bottom",labels:{boxWidth:10,font:{weight:"800",size:10}}},tooltip:{callbacks:{label:c=>` ${c.dataset.label}: ${bn(c.raw)}`}}},scales:{x:{stacked:true,grid:{display:false}},y:{stacked:true,ticks:{callback:v=>bn(v)},grid:{color:"rgba(0,160,233,.08)"}}}}});
}
function renderHeatmap(){
  const rows=DATA.heatmap||[];let max=1;rows.forEach(r=>r.values.forEach(v=>{if(v>max)max=v}));
  document.getElementById("heatMap").innerHTML=`<div class="h"></div>${periods.map(p=>`<div class="h">${p}</div>`).join("")}`+rows.map(r=>`<div class="r" title="${r.key}">${r.key}</div>`+r.values.map(v=>{const t=max?v/max:0;const bg=`rgba(0,160,233,${(0.12+t*0.88).toFixed(3)})`;const col=t>0.45?"#fff":"#005A9E";return`<div class="c" style="background:${bg};color:${col}" title="${full(v)}">${bn(v)}</div>`}).join("")).join("");
}
function renderMovers(){
  document.getElementById("moversUp").innerHTML=(DATA.moversUp||[]).map(m=>`<div class="mover up"><span>${m.key}</span><span class="amt">+${full(m.gap)}</span></div>`).join("")||"<div class='desc'>Không có tăng</div>";
  document.getElementById("moversDown").innerHTML=(DATA.moversDown||[]).map(m=>`<div class="mover down"><span>${m.key}</span><span class="amt">${full(m.gap)}</span></div>`).join("")||"<div class='desc'>Không có giảm</div>";
}
function renderCompare(){
  destroy("cmp");
  const a=document.getElementById("cmpA").value, b=document.getElementById("cmpB").value;
  const va=gVal(a), vb=gVal(b), d=vb-va, pct=va? (d/va*100):0;
  document.getElementById("cmpKpis").innerHTML=`
    <div class="chip"><span class="emoji">🅰️</span>${a}: <b class="mono">${bn(va)}</b></div>
    <div class="chip"><span class="emoji">🅱️</span>${b}: <b class="mono">${bn(vb)}</b></div>
    <div class="chip ${d>=0?"up":"down"}"><span class="emoji">Δ</span>Diff: <b class="mono">${(d>=0?"+":"")+bn(d)}</b> (${pct>=0?"+":""}${pct.toFixed(1)}%)</div>`;
  // compare by CC
  const ccs=[...new Set(DATA.budgetRows.map(r=>r.ccName))];
  const da=ccs.map(cc=>DATA.budgetRows.filter(r=>r.ccName===cc).reduce((s,r)=>s+(r.values[a]||0),0));
  const db=ccs.map(cc=>DATA.budgetRows.filter(r=>r.ccName===cc).reduce((s,r)=>s+(r.values[b]||0),0));
  charts.cmp=new Chart(document.getElementById("chartCompare"),{type:"bar",data:{labels:ccs,datasets:[{label:a,data:da,backgroundColor:"#00A0E9",borderRadius:10},{label:b,data:db,backgroundColor:"#FFD54F",borderRadius:10}]},options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{position:"bottom",labels:{boxWidth:12,font:{weight:"800"}}},tooltip:{callbacks:{label:c=>` ${c.dataset.label}: ${bn(c.raw)}`}}},scales:{x:{grid:{display:false},ticks:{font:{weight:"800"}}},y:{ticks:{callback:v=>bn(v)},grid:{color:"rgba(0,160,233,.08)"}}}}});
}
function renderAssetsCharts(){
  destroy("topA");destroy("aGL");
  const top=DATA.assets.slice(0,12);
  charts.topA=new Chart(document.getElementById("chartTopAssets"),{type:"bar",data:{labels:top.map(a=>(a.name||a.code).slice(0,26)),datasets:[{data:top.map(a=>a.cost),backgroundColor:"#00A0E9",borderRadius:10}]},options:{indexAxis:"y",responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false},tooltip:{callbacks:{label:c=>" "+full(c.raw)}}},scales:{x:{ticks:{callback:v=>bn(v)},grid:{color:"rgba(0,160,233,.08)"}},y:{grid:{display:false},ticks:{font:{size:10,weight:"800"}}}}}});
  const map={};DATA.assetsAll.forEach(a=>{map[a.glName||"Other"]=(map[a.glName||"Other"]||0)+(a.cost||0)});
  const labels=Object.keys(map);
  charts.aGL=new Chart(document.getElementById("chartAssetGL"),{type:"doughnut",data:{labels,datasets:[{data:labels.map(k=>map[k]),backgroundColor:colors,borderWidth:4,borderColor:"#fff"}]},options:{responsive:true,maintainAspectRatio:false,cutout:"55%",plugins:{legend:{position:"bottom",labels:{boxWidth:12,font:{weight:"800"}}},tooltip:{callbacks:{label:c=>` ${c.label}: ${bn(c.raw)}`}}}}});
  const sc=DATA.kpi.statusCounts||{};
  document.getElementById("statusChips").innerHTML=`
    <div class="chip"><span class="emoji">🟢</span>Active <b>${sc.active||0}</b></div>
    <div class="chip"><span class="emoji">🟡</span>Ending soon <b>${sc.ending_soon||0}</b></div>
    <div class="chip"><span class="emoji">🔴</span>Ended <b>${sc.ended||0}</b></div>
    <div class="chip"><span class="emoji">⭐</span>Favorites <b>${favs.size}</b></div>`;
}

function statusTag(s){
  if(s==="ending_soon") return '<span class="tag gold">Ending soon</span>';
  if(s==="ended") return '<span class="tag red">Ended</span>';
  return '<span class="tag green">Active</span>';
}

function renderTables(){
  const head=document.getElementById("budgetHead"), body=document.getElementById("budgetBody");
  const filterCC=document.getElementById("filterCC"), filterGL=document.getElementById("filterGL");
  if(!filterCC.dataset.ready){
    [...new Set(DATA.budgetRows.map(r=>r.ccName))].forEach(c=>{const o=document.createElement("option");o.value=c;o.textContent=c;filterCC.appendChild(o)});
    [...new Set(DATA.budgetRows.map(r=>r.glName))].forEach(c=>{const o=document.createElement("option");o.value=c;o.textContent=c;filterGL.appendChild(o)});
    filterCC.dataset.ready="1"; filterCC.onchange=filterGL.onchange=renderTables;
  }
  head.innerHTML=`<tr><th>CC</th><th>G/L</th>${periods.map(p=>`<th class="num">${p}</th>`).join("")}<th class="num">GAP 104/103</th></tr>`;
  const cc=filterCC.value, gl=filterGL.value;
  let rows=DATA.budgetRows.filter(r=>(!cc||r.ccName===cc)&&(!gl||r.glName===gl));
  const gq=(document.getElementById("globalSearch").value||"").toLowerCase().trim();
  if(gq) rows=rows.filter(r=>(r.ccName+r.glName).toLowerCase().includes(gq));
  body.innerHTML=rows.map(r=>{
    const gap=r.gaps["104Ki"]??((r.values["104Ki"]||0)-(r.values["103Ki"]||0));
    const gapCls=gap>0?"pos":(gap<0?"neg":"");
    return `<tr><td><span class="tag">${r.ccName}</span></td><td><span class="tag blue">${r.glName}</span></td>${periods.map(p=>`<td class="num">${full(r.values[p]||0)}</td>`).join("")}<td class="num ${gapCls}">${full(gap)}</td></tr>`;
  }).join("");

  // assets
  const q=(document.getElementById("assetSearch").value||document.getElementById("globalSearch").value||"").toLowerCase().trim();
  const st=document.getElementById("statusFilter").value;
  let list=DATA.assetsAll.slice();
  if(st==="fav") list=list.filter(a=>favs.has(a.code||a.name));
  else if(st) list=list.filter(a=>a.status===st);
  if(q) list=list.filter(a=>((a.name||"")+(a.code||"")+(a.ccName||"")+(a.glName||"")).toLowerCase().includes(q));
  list.sort((a,b)=>{
    const k=assetSort.key; let av=a[k], bv=b[k];
    if(typeof av==="string") return av.localeCompare(bv)*assetSort.dir;
    return ((av||0)-(bv||0))*assetSort.dir;
  });
  document.getElementById("assetBody").innerHTML=list.slice(0,120).map(a=>{
    const id=a.code||a.name; const on=favs.has(id)?"on":"";
    const idx=DATA.assetsAll.indexOf(a);
    return `<tr data-idx="${idx}">
      <td><span class="star ${on}" data-fav="${id}">⭐</span></td>
      <td class="mono">${a.code||"—"}</td>
      <td class="name" title="${(a.name||"").replace(/"/g,"&quot;")}">${a.name||"—"}</td>
      <td><span class="tag">${a.ccName||"—"}</span></td>
      <td><span class="tag violet">${a.glName||"—"}</span></td>
      <td>${statusTag(a.status)}</td>
      <td class="num">${full(a.cost)}</td>
      <td class="num">${a.life??"—"}</td>
      <td class="num">${full(a.totalAll)}</td>
    </tr>`;
  }).join("");
  document.querySelectorAll("#assetBody tr").forEach(tr=>{
    tr.style.cursor="pointer";
    tr.onclick=e=>{
      if(e.target.classList.contains("star")){
        e.stopPropagation();
        const id=e.target.dataset.fav;
        if(favs.has(id)) favs.delete(id); else favs.add(id);
        saveFavs(); renderTables(); renderFavs(); renderAssetsCharts(); toast(favs.has(id)?"Đã gắn sao ⭐":"Bỏ sao");
        return;
      }
      openAsset(Number(tr.dataset.idx));
    };
  });
}

function renderFavs(){
  const list=DATA.assetsAll.filter(a=>favs.has(a.code||a.name));
  const el=document.getElementById("favList");
  if(!list.length){el.innerHTML="<div class='desc'>Chưa có favorite — bấm ⭐ trên bảng asset nhé!</div>";return}
  el.innerHTML=list.map(a=>`<div class="mover"><span>⭐ ${(a.name||a.code).slice(0,40)}</span><span class="amt mono">${bn(a.cost)}</span></div>`).join("");
}

function openAsset(idx){
  const a=DATA.assetsAll[idx]; if(!a) return;
  document.getElementById("modalTitle").textContent="📦 "+(a.name||a.code||"Asset");
  document.getElementById("modalSub").textContent=`${a.code||""} · ${a.ccName||""} · ${a.glName||""} · ${a.status}`;
  document.getElementById("modalBody").innerHTML=[
    ["Acquisition",full(a.cost)+" VND"],["Life",a.life!=null?a.life+" months":"—"],
    ["Monthly rate",full(a.monthlyRate||0)+" VND"],["Start → End",(a.start||"—")+" → "+(a.end||"—")],
    ["Months left",a.monthsLeft!=null?a.monthsLeft:"—"],["Σ MT KH",full(a.totalAll)+" VND"],
  ].map(([k,v])=>`<div class="row"><span>${k}</span><span class="mono">${v}</span></div>`).join("");
  if(assetDetailChart) assetDetailChart.destroy();
  assetDetailChart=new Chart(document.getElementById("chartAssetDetail"),{type:"bar",data:{labels:periods,datasets:[{data:a.periodTotals||[],backgroundColor:"#7C4DFF",borderRadius:10}]},options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false},tooltip:{callbacks:{label:c=>" "+full(c.raw)}}},scales:{x:{grid:{display:false}},y:{ticks:{callback:v=>bn(v)},grid:{color:"rgba(0,160,233,.08)"}}}}});
  document.getElementById("modalBg").classList.add("show");
}

function renderAll(meta=true){
  if(meta){
    document.getElementById("srcName").textContent=DATA.meta.source;
    document.getElementById("genAt").textContent=DATA.meta.generated;
    document.getElementById("footMeta").textContent=`v${DATA.meta.version} · ${DATA.meta.generated}`;
  }
  renderKPI(); renderInsights(); renderPeriod(); renderWaterfall(); renderPies(); renderStack();
  renderGap(); renderCompare(); renderMonthly(); renderHeatmap(); renderMovers();
  renderAssetsCharts(); renderTables(); renderFavs();
  document.getElementById("helperText").textContent=tips[helperIdx%tips.length];
}

// confetti
function party(){
  const box=document.getElementById("confetti"); box.innerHTML="";
  const cols=["#00A0E9","#E60012","#FFD54F","#fff","#7C4DFF","#26A69A"];
  for(let i=0;i<48;i++){
    const el=document.createElement("i");
    el.style.left=Math.random()*100+"%";
    el.style.background=cols[i%cols.length];
    el.style.animationDuration=(2+Math.random()*2.5)+"s";
    el.style.width=(6+Math.random()*8)+"px";
    el.style.height=el.style.width;
    box.appendChild(el);
  }
  setTimeout(()=>box.innerHTML="",4500);
  ringBell(); toast("Yayyy! 🎉 Doraemon party!");
}

// events
document.getElementById("assetSearch").oninput=renderTables;
document.getElementById("statusFilter").onchange=renderTables;
document.getElementById("globalSearch").oninput=()=>{renderTables();};
document.getElementById("modalClose").onclick=()=>document.getElementById("modalBg").classList.remove("show");
document.getElementById("modalBg").onclick=e=>{if(e.target.id==="modalBg")e.currentTarget.classList.remove("show")};
document.getElementById("btnPrint").onclick=()=>window.print();
document.getElementById("btnNight").onclick=()=>{document.body.classList.toggle("night");toast(document.body.classList.contains("night")?"Night mode 🌙":"Day mode ☀️")};
document.getElementById("btnConfetti").onclick=party;
document.getElementById("bellBtn").onclick=()=>{ringBell();helperIdx++;document.getElementById("helperText").textContent=tips[helperIdx%tips.length];document.getElementById("helper").classList.remove("hidden");toast("Ting-a-ling 🔔")};
document.getElementById("helperNext").onclick=()=>{helperIdx++;document.getElementById("helperText").textContent=tips[helperIdx%tips.length];ringBell()};
document.getElementById("helperHide").onclick=()=>document.getElementById("helper").classList.add("hidden");
document.getElementById("btnShare").onclick=async()=>{
  const g=gVal(focusPeriod);
  const text=`LOG Depreciation (${DATA.meta.source})\nFocus ${focusPeriod}: ${full(g)} VND\nMT total: ${full(DATA.kpi.totalMT)} VND\nAssets: ${DATA.kpi.assetCount}\nGenerated: ${DATA.meta.generated}`;
  try{await navigator.clipboard.writeText(text);toast("Đã copy summary 📝")}catch(e){toast("Clipboard blocked")}
};
document.getElementById("btnExportCsv").onclick=()=>{
  const lines=[["CC","G/L",...periods,"GAP_104_103"]];
  DATA.budgetRows.forEach(r=>{const gap=r.gaps["104Ki"]??((r.values["104Ki"]||0)-(r.values["103Ki"]||0));lines.push([r.ccName,r.glName,...periods.map(p=>r.values[p]||0),gap])});
  const csv=lines.map(row=>row.map(x=>`"${String(x).replace(/"/g,'""')}"`).join(",")).join("\n");
  const blob=new Blob([csv],{type:"text/csv;charset=utf-8"});
  const a=document.createElement("a");a.href=URL.createObjectURL(blob);a.download="log_depreciation_budget.csv";a.click();URL.revokeObjectURL(a.href);toast("CSV exported 📤");
};

// sortable asset headers
document.querySelectorAll("th[data-sort]").forEach(th=>{
  th.onclick=()=>{
    const k=th.dataset.sort;
    if(assetSort.key===k) assetSort.dir*=-1; else {assetSort.key=k;assetSort.dir=-1}
    renderTables();
  };
});

const titles={overview:"Overview",midterm:"Mid-term",compare:"Compare",monthly:"Monthly",heatmap:"Heatmap",movers:"Movers",assets:"Assets",tables:"Tables",favs:"Favorites"};
document.querySelectorAll("[data-nav]").forEach(a=>{
  a.addEventListener("click",()=>{
    document.querySelectorAll("[data-nav]").forEach(x=>x.classList.remove("active"));
    a.classList.add("active");
    document.getElementById("pageTitle").textContent=titles[a.getAttribute("href").slice(1)]||"Dashboard";
  });
});

renderAll(true);
setTimeout(party, 400);
</script>
</body>
</html>
''')

html = "".join(parts).replace("__DATA_JSON__", data_js)
(root / "index.html").write_text(html, encoding="utf-8")
print("Built v3 cute:", (root / "index.html").stat().st_size)
