#!/usr/bin/env python3
"""Dashboard — lê o fato tidy (DuckDB) e gera uma página HTML interativa autocontida.

Embute os dados inline (sem requests externos: o Artifact/CSP bloqueia rede) e renderiza
séries temporais SM/RS/Brasil por indicador e etapa, com crosshair+tooltip, rótulos diretos,
tema claro/escuro e visão de tabela. Paleta categórica validada (dataviz/validate_palette).
"""
import json
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "data" / "educacao.duckdb"
OUT = ROOT / "viz" / "dashboard.html"


def load_nested():
    con = duckdb.connect(str(DB), read_only=True)
    try:
        rows = con.execute(
            """select indicador, nivel, etapa, ano, round(valor,1) valor
               from fct_indicadores order by indicador, etapa, nivel, ano"""
        ).fetchall()
    finally:
        con.close()
    nested = {}
    for ind, niv, eta, ano, val in rows:
        nested.setdefault(ind, {}).setdefault(eta, {}).setdefault(niv, []).append([ano, val])
    for ind in nested:
        for eta in nested[ind]:
            for niv in nested[ind][eta]:
                nested[ind][eta][niv].sort()
    return nested


HTML = r"""<div class="wrap">
  <header class="head">
    <div class="head-txt">
      <p class="eyebrow">Observatório da educação · rede pública</p>
      <h1>Santa Maria <span class="vs">frente ao</span> RS e ao Brasil</h1>
      <p class="lede">Um raio-x da educação básica pública ao longo do tempo — IDEB, a
        proficiência que o compõe (SAEB), o rendimento (aprovação) e a distorção idade-série.
        Fonte: INEP via Base dos Dados. Tudo reprodutível pelo pipeline.</p>
    </div>
    <button id="theme" class="theme-btn" type="button" aria-label="Alternar tema">
      <span class="theme-ico"></span>
    </button>
  </header>

  <section class="kpis" aria-label="Achados principais">
    <article class="kpi">
      <p class="kpi-tag">A pandemia, sem o disfarce</p>
      <p class="kpi-num">210<span class="kpi-unit"> em 2021</span></p>
      <p class="kpi-desc">A proficiência SAEB de Matemática (anos iniciais) despencou de
        <b>224,8</b> (2019) para <b>210,2</b>, enquanto a <i>aprovação subia</i>. O IDEB, que
        pondera os dois, amortece a queda.</p>
      <svg class="spark" data-spark="saeb_matematica|ef_anos_iniciais|santa_maria" viewBox="0 0 120 32" preserveAspectRatio="none" aria-hidden="true"></svg>
    </article>
    <article class="kpi">
      <p class="kpi-tag">O percurso acumula atraso</p>
      <p class="kpi-num">19,8<span class="kpi-unit">% · 2024</span></p>
      <p class="kpi-desc">A distorção idade-série de Santa Maria nos anos finais é <b>mais alta</b>
        que a do Brasil (<b>14,4%</b>) e caiu mais tarde — a base vai bem, o percurso patina.</p>
      <svg class="spark" data-spark="distorcao_idade_serie|ef_anos_finais|santa_maria" viewBox="0 0 120 32" preserveAspectRatio="none" aria-hidden="true"></svg>
    </article>
    <article class="kpi">
      <p class="kpi-tag">O gargalo é o Ensino Médio</p>
      <p class="kpi-num">78,2<span class="kpi-unit">% · 2022</span></p>
      <p class="kpi-desc">A aprovação de EM de Santa Maria despenca frente ao Brasil (<b>94,8%</b>),
        coerente com o IDEB de EM da cidade, que caiu de 3,1 para <b>2,4</b>.</p>
      <svg class="spark" data-spark="taxa_aprovacao|em|santa_maria" viewBox="0 0 120 32" preserveAspectRatio="none" aria-hidden="true"></svg>
    </article>
  </section>

  <section class="panel" aria-label="Explorador de indicadores">
    <div class="controls">
      <div class="ctl">
        <span class="ctl-lbl">Indicador</span>
        <div id="ind-pills" class="pills" role="tablist"></div>
      </div>
      <div class="ctl">
        <span class="ctl-lbl">Etapa</span>
        <div id="eta-pills" class="pills" role="tablist"></div>
      </div>
    </div>

    <div class="chart-head">
      <div>
        <h2 id="chart-title">—</h2>
        <p id="chart-unit" class="chart-unit">—</p>
      </div>
      <button id="view-toggle" class="ghost-btn" type="button">Ver tabela</button>
    </div>

    <figure class="chart-fig" id="chart-fig">
      <svg id="chart" viewBox="0 0 820 400" role="img" aria-labelledby="chart-title"></svg>
      <div id="tooltip" class="tooltip" hidden></div>
    </figure>

    <div id="legend" class="legend"></div>

    <div id="table-wrap" class="table-wrap" hidden></div>

    <p id="chart-note" class="chart-note"></p>
  </section>

  <section class="notes" aria-label="Notas de qualidade">
    <h2>Por que alguns dados somem</h2>
    <p>Os dados mandam sobre o plano — e foram auditados célula a célula. Três decisões honestas:</p>
    <ul>
      <li><b>O bug é da Base dos Dados, não do INEP.</b> A aprovação de EM do RS aparece como
        4–11% em <i>todas</i> as fatias de rede (impossível). A fonte oficial do INEP é limpa,
        mas seu servidor é inacessível deste ambiente — então tratamos com curadoria transparente.</li>
      <li><b>Distorção idade-série só nos anos finais.</b> É a única série que passa na auditoria
        (RS quebrado até 2022; Santa Maria, nos anos iniciais, pós-2020; EM, para todos).</li>
      <li><b>Ensino médio entra onde o dado aguenta.</b> O IDEB de EM some (série curta); a
        aprovação de EM entra como Santa Maria vs Brasil (o RS cai sozinho).</li>
    </ul>
  </section>

  <footer class="foot">
    <span>Fonte: INEP (<code>br_inep_ideb</code>, <code>br_inep_indicadores_educacionais</code>) via
      Base dos Dados · rede pública</span>
    <span>Santa Maria/RS · <code>4316907</code> · projeto de portfólio de dados</span>
  </footer>
</div>

<script>
const DATA = __DATA__;

const IND = {
  ideb:                    {label:"IDEB",                    unit:"IDEB — escala 0 a 10"},
  saeb_matematica:         {label:"SAEB · Matemática",       unit:"Proficiência — escala SAEB"},
  saeb_lingua_portuguesa:  {label:"SAEB · Língua Portuguesa",unit:"Proficiência — escala SAEB"},
  taxa_aprovacao:          {label:"Taxa de aprovação",       unit:"% de aprovação"},
  distorcao_idade_serie:   {label:"Distorção idade-série",   unit:"% de alunos em distorção idade-série"},
};
const IND_ORDER = ["ideb","saeb_matematica","saeb_lingua_portuguesa","taxa_aprovacao","distorcao_idade_serie"];
const ETA = {ef_anos_iniciais:"EF · Anos iniciais", ef_anos_finais:"EF · Anos finais", em:"Ensino médio"};
const ETA_ORDER = ["ef_anos_iniciais","ef_anos_finais","em"];
const NIV = {
  santa_maria:{label:"Santa Maria",       cls:"sm"},
  rs:         {label:"Rio Grande do Sul", cls:"rs"},
  brasil:     {label:"Brasil",            cls:"br"},
};
const NIV_ORDER = ["santa_maria","rs","brasil"];

const NS = "http://www.w3.org/2000/svg";
const fmt = n => n.toLocaleString("pt-BR", {minimumFractionDigits:1, maximumFractionDigits:1});
const state = {ind:"ideb", eta:"ef_anos_finais"};

function etapasFor(ind){ return ETA_ORDER.filter(e => DATA[ind] && DATA[ind][e]); }
function seriesFor(ind, eta){
  const d = (DATA[ind]||{})[eta] || {};
  return NIV_ORDER.filter(n => d[n] && d[n].length).map(n => ({niv:n, pts:d[n]}));
}

// ---- pills -----------------------------------------------------------------
function buildPills(){
  const ip = document.getElementById("ind-pills"); ip.innerHTML = "";
  IND_ORDER.forEach(ind => {
    const b = document.createElement("button");
    b.className = "pill"; b.textContent = IND[ind].label; b.type = "button";
    b.setAttribute("role","tab");
    b.onclick = () => { state.ind = ind; if(!etapasFor(ind).includes(state.eta)) state.eta = etapasFor(ind)[0]; render(); };
    b.dataset.ind = ind;
    ip.appendChild(b);
  });
}
function buildEtapaPills(){
  const ep = document.getElementById("eta-pills"); ep.innerHTML = "";
  const avail = etapasFor(state.ind);
  ETA_ORDER.forEach(eta => {
    const b = document.createElement("button");
    b.className = "pill"; b.textContent = ETA[eta]; b.type = "button";
    b.setAttribute("role","tab");
    const ok = avail.includes(eta);
    b.disabled = !ok;
    if(ok) b.onclick = () => { state.eta = eta; render(); };
    b.dataset.eta = eta;
    ep.appendChild(b);
  });
}
function syncPills(){
  document.querySelectorAll("#ind-pills .pill").forEach(b =>
    b.setAttribute("aria-selected", b.dataset.ind === state.ind));
  document.querySelectorAll("#eta-pills .pill").forEach(b =>
    b.setAttribute("aria-selected", b.dataset.eta === state.eta));
}

// ---- scales ----------------------------------------------------------------
function niceStep(range, target){
  const raw = range / target, mag = Math.pow(10, Math.floor(Math.log10(raw)));
  const norm = raw / mag;
  const step = norm < 1.5 ? 1 : norm < 3 ? 2 : norm < 7 ? 5 : 10;
  return step * mag;
}
function domainY(series){
  let lo = Infinity, hi = -Infinity;
  series.forEach(s => s.pts.forEach(([,v]) => { lo = Math.min(lo,v); hi = Math.max(hi,v); }));
  if(lo === hi){ lo -= 1; hi += 1; }
  const pad = (hi - lo) * 0.12;
  lo -= pad; hi += pad;
  const step = niceStep(hi - lo, 4);
  lo = Math.floor(lo/step)*step; hi = Math.ceil(hi/step)*step;
  return {lo, hi, step};
}
function domainX(series){
  let lo = Infinity, hi = -Infinity;
  series.forEach(s => s.pts.forEach(([a]) => { lo = Math.min(lo,a); hi = Math.max(hi,a); }));
  return {lo, hi};
}

// ---- chart -----------------------------------------------------------------
const M = {t:16, r:64, b:34, l:46};
const W = 820, H = 400;
let CH = null; // current chart context for hover

function el(tag, attrs){ const e = document.createElementNS(NS, tag); for(const k in attrs) e.setAttribute(k, attrs[k]); return e; }

function drawChart(){
  const svg = document.getElementById("chart");
  svg.innerHTML = "";
  const series = seriesFor(state.ind, state.eta);
  if(!series.length){ return; }
  const dy = domainY(series), dx = domainX(series);
  const iw = W - M.l - M.r, ih = H - M.t - M.b;
  const sx = a => M.l + (dx.hi === dx.lo ? iw/2 : (a - dx.lo)/(dx.hi - dx.lo) * iw);
  const sy = v => M.t + (1 - (v - dy.lo)/(dy.hi - dy.lo)) * ih;

  // y grid + labels
  for(let v = dy.lo; v <= dy.hi + 1e-9; v += dy.step){
    const y = sy(v);
    svg.appendChild(el("line", {x1:M.l, x2:W-M.r, y1:y, y2:y, class:"grid"}));
    const t = el("text", {x:M.l-8, y:y+3.5, class:"axis-lbl", "text-anchor":"end"});
    t.textContent = fmt(v).replace(",0","");
    svg.appendChild(t);
  }
  // x labels (integer years, ~6)
  const span = dx.hi - dx.lo, xstep = Math.max(1, Math.round(span/6));
  for(let a = dx.lo; a <= dx.hi; a += xstep){
    const x = sx(a);
    const t = el("text", {x, y:H-M.b+18, class:"axis-lbl", "text-anchor":"middle"});
    t.textContent = a; svg.appendChild(t);
  }
  // baseline
  svg.appendChild(el("line", {x1:M.l, x2:W-M.r, y1:H-M.b, y2:H-M.b, class:"baseline"}));

  // series lines + markers + end mark/label
  series.forEach(s => {
    const cls = NIV[s.niv].cls;
    const d = s.pts.map(([a,v],i) => `${i?"L":"M"}${sx(a).toFixed(1)},${sy(v).toFixed(1)}`).join(" ");
    svg.appendChild(el("path", {d, class:`line l-${cls}`, fill:"none"}));
    s.pts.forEach(([a,v]) => svg.appendChild(el("circle", {cx:sx(a), cy:sy(v), r:3, class:`dot d-${cls}`})));
    const [la,lv] = s.pts[s.pts.length-1];
    svg.appendChild(el("circle", {cx:sx(la), cy:sy(lv), r:3.6, class:`dot-end d-${cls}`}));
    const t = el("text", {x:sx(la)+9, y:sy(lv)+3.5, class:"end-lbl"});
    t.textContent = fmt(lv).replace(",0",""); svg.appendChild(t);
  });

  // hover layer
  const focus = el("g", {class:"focus", visibility:"hidden"});
  const vline = el("line", {y1:M.t, y2:H-M.b, class:"crosshair"});
  focus.appendChild(vline);
  const fdots = series.map(s => { const c = el("circle", {r:4.5, class:`focus-dot d-${NIV[s.niv].cls}`}); focus.appendChild(c); return c; });
  svg.appendChild(focus);
  const hit = el("rect", {x:M.l, y:M.t, width:iw, height:ih, fill:"transparent", style:"cursor:crosshair"});
  svg.appendChild(hit);

  CH = {svg, series, sx, sy, dx, focus, vline, fdots, hit};
  attachHover();
}

function attachHover(){
  const tip = document.getElementById("tooltip");
  const {svg, series, sx, sy, dx, focus, vline, fdots, hit} = CH;
  // union of years present
  const years = [...new Set(series.flatMap(s => s.pts.map(p => p[0])))].sort((a,b)=>a-b);
  function move(ev){
    const pt = svg.createSVGPoint();
    pt.x = ev.clientX; pt.y = ev.clientY;
    const loc = pt.matrixTransform(svg.getScreenCTM().inverse());
    // nearest year
    let best = years[0], bd = Infinity;
    years.forEach(y => { const d = Math.abs(sx(y) - loc.x); if(d < bd){ bd = d; best = y; } });
    const x = sx(best);
    focus.setAttribute("visibility","visible");
    vline.setAttribute("x1", x); vline.setAttribute("x2", x);
    let rows = "";
    series.forEach((s,i) => {
      const hit = s.pts.find(p => p[0] === best);
      if(hit){ fdots[i].setAttribute("visibility","visible"); fdots[i].setAttribute("cx", x); fdots[i].setAttribute("cy", sy(hit[1]));
        rows += `<div class="tip-row"><span class="tip-dot dot-${NIV[s.niv].cls}"></span>${NIV[s.niv].label}<b>${fmt(hit[1])}</b></div>`;
      } else { fdots[i].setAttribute("visibility","hidden"); }
    });
    tip.innerHTML = `<div class="tip-year">${best}</div>${rows}`;
    tip.hidden = false;
    const fig = document.getElementById("chart-fig").getBoundingClientRect();
    const px = (x / W) * fig.width;
    tip.style.left = Math.min(fig.width - tip.offsetWidth - 8, Math.max(8, px + 12)) + "px";
    tip.style.top = "12px";
  }
  function leave(){ focus.setAttribute("visibility","hidden"); tip.hidden = true; }
  hit.addEventListener("pointermove", move);
  hit.addEventListener("pointerleave", leave);
}

// ---- legend + table + sparks ----------------------------------------------
function drawLegend(){
  const lg = document.getElementById("legend"); lg.innerHTML = "";
  seriesFor(state.ind, state.eta).forEach(s => {
    const item = document.createElement("span"); item.className = "leg-item";
    item.innerHTML = `<span class="leg-dot dot-${NIV[s.niv].cls}"></span>${NIV[s.niv].label}`;
    lg.appendChild(item);
  });
}
function drawTable(){
  const wrap = document.getElementById("table-wrap");
  const series = seriesFor(state.ind, state.eta);
  const years = [...new Set(series.flatMap(s => s.pts.map(p => p[0])))].sort((a,b)=>a-b);
  const map = {}; series.forEach(s => { map[s.niv] = Object.fromEntries(s.pts); });
  let h = `<table><thead><tr><th>Ano</th>${series.map(s=>`<th>${NIV[s.niv].label}</th>`).join("")}</tr></thead><tbody>`;
  years.forEach(y => {
    h += `<tr><td>${y}</td>${series.map(s => `<td>${map[s.niv][y]!=null ? fmt(map[s.niv][y]) : "—"}</td>`).join("")}</tr>`;
  });
  h += "</tbody></table>";
  wrap.innerHTML = h;
}
function drawSparks(){
  document.querySelectorAll("[data-spark]").forEach(svg => {
    const [ind,eta,niv] = svg.dataset.spark.split("|");
    const pts = ((DATA[ind]||{})[eta]||{})[niv]; if(!pts||pts.length<2) return;
    const xs = pts.map(p=>p[0]), ys = pts.map(p=>p[1]);
    const xlo=Math.min(...xs), xhi=Math.max(...xs), ylo=Math.min(...ys), yhi=Math.max(...ys);
    const sx=a=>4+(a-xlo)/(xhi-xlo||1)*112, sy=v=>28-(v-ylo)/(yhi-ylo||1)*24;
    const d = pts.map(([a,v],i)=>`${i?"L":"M"}${sx(a).toFixed(1)},${sy(v).toFixed(1)}`).join(" ");
    svg.innerHTML = `<path d="${d}" fill="none" class="spark-line"/>`+
      `<circle cx="${sx(xs[xs.length-1]).toFixed(1)}" cy="${sy(ys[ys.length-1]).toFixed(1)}" r="2.4" class="spark-end"/>`;
  });
}

// ---- render ----------------------------------------------------------------
let tableOpen = false;
function render(){
  buildEtapaPills(); syncPills();
  document.getElementById("chart-title").textContent = `${IND[state.ind].label} · ${ETA[state.eta]}`;
  document.getElementById("chart-unit").textContent = IND[state.ind].unit;
  drawChart(); drawLegend(); drawTable();
  const only = seriesFor(state.ind, state.eta).map(s=>NIV[s.niv].label);
  const note = document.getElementById("chart-note");
  const shown = only.length === 3 ? "" :
    ` Séries exibidas: ${only.join(", ")} (as demais não passam na auditoria de qualidade).`;
  note.textContent = `Passe o mouse para ver os valores por ano.${shown}`;
  document.getElementById("table-wrap").hidden = !tableOpen;
  document.getElementById("chart-fig").hidden = tableOpen;
  document.getElementById("legend").hidden = tableOpen;
  document.getElementById("view-toggle").textContent = tableOpen ? "Ver gráfico" : "Ver tabela";
}

// ---- theme -----------------------------------------------------------------
function initTheme(){
  const btn = document.getElementById("theme");
  const root = document.documentElement;
  const apply = t => { root.setAttribute("data-theme", t); };
  const cur = () => root.getAttribute("data-theme") ||
    (matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");
  btn.onclick = () => { apply(cur() === "dark" ? "light" : "dark"); };
}

// ---- boot ------------------------------------------------------------------
buildPills();
initTheme();
render();
drawSparks();
document.getElementById("view-toggle").onclick = () => { tableOpen = !tableOpen; render(); };
addEventListener("resize", () => { if(!tableOpen) drawChart(); });
</script>
"""

CSS = r"""
:root{
  --surface:#fbfbfa; --panel:#ffffff; --panel-2:#f5f5f3;
  --ink:#16181d; --ink-2:#4c515a; --muted:#8a8f98; --line:#e7e7e4; --line-2:#efefec;
  --c-sm:#2a78d6; --c-rs:#1baf7a; --c-br:#eda100;
  --accent:#2a78d6; --shadow:0 1px 2px rgba(20,22,28,.05), 0 8px 24px rgba(20,22,28,.06);
  --font-display:"Iowan Old Style","Palatino Linotype","Palatino","Georgia",serif;
  --font-body:system-ui,-apple-system,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
  --font-mono:ui-monospace,"SF Mono","JetBrains Mono","Menlo","Consolas",monospace;
}
@media (prefers-color-scheme: dark){
  :root{
    --surface:#121316; --panel:#1a1c20; --panel-2:#212429;
    --ink:#eceef1; --ink-2:#aab0b8; --muted:#727881; --line:#2a2d33; --line-2:#23262b;
    --c-sm:#4a90e2; --c-rs:#1baf7a; --c-br:#d07b12; --accent:#4a90e2;
    --shadow:0 1px 2px rgba(0,0,0,.3), 0 10px 30px rgba(0,0,0,.35);
  }
}
:root[data-theme="light"]{
  --surface:#fbfbfa; --panel:#ffffff; --panel-2:#f5f5f3;
  --ink:#16181d; --ink-2:#4c515a; --muted:#8a8f98; --line:#e7e7e4; --line-2:#efefec;
  --c-sm:#2a78d6; --c-rs:#1baf7a; --c-br:#eda100; --accent:#2a78d6;
  --shadow:0 1px 2px rgba(20,22,28,.05), 0 8px 24px rgba(20,22,28,.06);
}
:root[data-theme="dark"]{
  --surface:#121316; --panel:#1a1c20; --panel-2:#212429;
  --ink:#eceef1; --ink-2:#aab0b8; --muted:#727881; --line:#2a2d33; --line-2:#23262b;
  --c-sm:#4a90e2; --c-rs:#1baf7a; --c-br:#d07b12; --accent:#4a90e2;
  --shadow:0 1px 2px rgba(0,0,0,.3), 0 10px 30px rgba(0,0,0,.35);
}
*{box-sizing:border-box}
body{margin:0;background:var(--surface);color:var(--ink);font-family:var(--font-body);
  line-height:1.5;-webkit-font-smoothing:antialiased;}
.wrap{max-width:1060px;margin:0 auto;padding:40px 24px 64px;}

/* header */
.head{display:flex;justify-content:space-between;align-items:flex-start;gap:24px;
  border-bottom:1px solid var(--line);padding-bottom:28px;}
.eyebrow{font-family:var(--font-mono);font-size:12px;letter-spacing:.14em;text-transform:uppercase;
  color:var(--accent);margin:0 0 10px;}
h1{font-family:var(--font-display);font-weight:600;font-size:clamp(30px,4.4vw,46px);line-height:1.06;
  margin:0;letter-spacing:-.01em;text-wrap:balance;}
h1 .vs{color:var(--muted);font-style:italic;font-weight:500;}
.lede{max-width:60ch;color:var(--ink-2);font-size:15.5px;margin:16px 0 0;}
.theme-btn{flex:none;width:40px;height:40px;border-radius:10px;border:1px solid var(--line);
  background:var(--panel);cursor:pointer;display:grid;place-items:center;box-shadow:var(--shadow);}
.theme-btn:hover{border-color:var(--accent);}
.theme-ico{width:16px;height:16px;border-radius:50%;
  background:radial-gradient(circle at 32% 32%, var(--ink) 0 48%, transparent 52%);
  box-shadow:inset 0 0 0 1.6px var(--ink);}
:root[data-theme="dark"] .theme-ico, :root:not([data-theme="light"]) .theme-ico{}

/* kpis */
.kpis{display:grid;grid-template-columns:repeat(3,1fr);gap:16px;margin:28px 0;}
.kpi{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:20px 20px 12px;
  box-shadow:var(--shadow);display:flex;flex-direction:column;min-height:184px;}
.kpi-tag{font-family:var(--font-mono);font-size:11.5px;letter-spacing:.06em;text-transform:uppercase;
  color:var(--muted);margin:0 0 10px;}
.kpi-num{font-family:var(--font-display);font-size:40px;font-weight:600;line-height:1;margin:0 0 8px;
  font-variant-numeric:tabular-nums;letter-spacing:-.01em;}
.kpi-num .kpi-unit{font-family:var(--font-body);font-size:14px;font-weight:500;color:var(--muted);
  letter-spacing:0;}
.kpi-desc{font-size:13.5px;color:var(--ink-2);margin:0 0 12px;}
.kpi-desc b{color:var(--ink);font-variant-numeric:tabular-nums;}
.spark{width:100%;height:30px;margin-top:auto;}
.spark-line{stroke:var(--c-sm);stroke-width:1.6;stroke-linecap:round;stroke-linejoin:round;}
.spark-end{fill:var(--c-sm);}

/* panel */
.panel{background:var(--panel);border:1px solid var(--line);border-radius:16px;
  padding:22px 24px 20px;box-shadow:var(--shadow);}
.controls{display:flex;flex-wrap:wrap;gap:20px 32px;padding-bottom:18px;border-bottom:1px solid var(--line-2);}
.ctl{display:flex;flex-direction:column;gap:8px;}
.ctl-lbl{font-family:var(--font-mono);font-size:11px;letter-spacing:.1em;text-transform:uppercase;color:var(--muted);}
.pills{display:flex;flex-wrap:wrap;gap:6px;}
.pill{font-family:var(--font-body);font-size:13px;padding:6px 13px;border-radius:999px;cursor:pointer;
  border:1px solid var(--line);background:var(--panel-2);color:var(--ink-2);transition:all .12s;}
.pill:hover:not(:disabled){border-color:var(--accent);color:var(--ink);}
.pill[aria-selected="true"]{background:var(--accent);border-color:var(--accent);color:#fff;font-weight:500;}
:root[data-theme="dark"] .pill[aria-selected="true"]{color:#0c0e12;}
.pill:disabled{opacity:.36;cursor:not-allowed;}
.pill:focus-visible, .ghost-btn:focus-visible, .theme-btn:focus-visible{outline:2px solid var(--accent);outline-offset:2px;}

.chart-head{display:flex;justify-content:space-between;align-items:flex-end;gap:16px;margin:20px 0 6px;}
h2{font-family:var(--font-display);font-size:22px;font-weight:600;margin:0;letter-spacing:-.01em;}
.chart-unit{font-size:13px;color:var(--muted);margin:3px 0 0;}
.ghost-btn{flex:none;font-family:var(--font-body);font-size:13px;padding:7px 14px;border-radius:9px;
  border:1px solid var(--line);background:var(--panel-2);color:var(--ink-2);cursor:pointer;}
.ghost-btn:hover{border-color:var(--accent);color:var(--ink);}

.chart-fig{position:relative;margin:8px 0 0;}
#chart{width:100%;height:auto;display:block;overflow:visible;}
.grid{stroke:var(--line-2);stroke-width:1;}
.baseline{stroke:var(--line);stroke-width:1;}
.axis-lbl{fill:var(--muted);font-family:var(--font-mono);font-size:11px;font-variant-numeric:tabular-nums;}
.line{stroke-width:2.2;stroke-linecap:round;stroke-linejoin:round;}
.l-sm{stroke:var(--c-sm);} .l-rs{stroke:var(--c-rs);} .l-br{stroke:var(--c-br);}
.dot{stroke:var(--panel);stroke-width:1.4;}
.d-sm{fill:var(--c-sm);} .d-rs{fill:var(--c-rs);} .d-br{fill:var(--c-br);}
.dot-end{stroke:var(--panel);stroke-width:1.6;}
.end-lbl{fill:var(--ink);font-family:var(--font-mono);font-size:12px;font-weight:600;
  font-variant-numeric:tabular-nums;}
.crosshair{stroke:var(--ink-2);stroke-width:1;stroke-dasharray:3 3;opacity:.5;}
.focus-dot{stroke:var(--panel);stroke-width:1.8;}

.tooltip{position:absolute;background:var(--panel);border:1px solid var(--line);border-radius:10px;
  padding:9px 11px;box-shadow:var(--shadow);font-size:13px;pointer-events:none;min-width:132px;z-index:5;}
.tip-year{font-family:var(--font-mono);font-size:11px;letter-spacing:.08em;color:var(--muted);
  margin-bottom:5px;}
.tip-row{display:flex;align-items:center;gap:7px;padding:2px 0;color:var(--ink-2);}
.tip-row b{margin-left:auto;color:var(--ink);font-variant-numeric:tabular-nums;}
.tip-dot,.leg-dot{width:9px;height:9px;border-radius:50%;flex:none;display:inline-block;}
.dot-sm{background:var(--c-sm);} .dot-rs{background:var(--c-rs);} .dot-br{background:var(--c-br);}

.legend{display:flex;flex-wrap:wrap;gap:18px;justify-content:center;margin:14px 0 2px;}
.leg-item{display:flex;align-items:center;gap:7px;font-size:13px;color:var(--ink-2);}

.table-wrap{overflow-x:auto;margin-top:8px;}
table{border-collapse:collapse;width:100%;font-size:13.5px;}
th,td{padding:7px 12px;text-align:right;border-bottom:1px solid var(--line-2);
  font-variant-numeric:tabular-nums;}
th:first-child,td:first-child{text-align:left;font-family:var(--font-mono);color:var(--muted);}
thead th{color:var(--ink-2);font-weight:600;border-bottom:1px solid var(--line);}

.chart-note{font-size:12.5px;color:var(--muted);margin:14px 0 0;text-align:center;}

/* notes */
.notes{margin-top:34px;padding:24px 26px;background:var(--panel-2);border:1px solid var(--line);
  border-radius:14px;}
.notes h2{font-size:18px;margin-bottom:6px;}
.notes p{color:var(--ink-2);font-size:14px;margin:0 0 12px;}
.notes ul{margin:0;padding-left:18px;color:var(--ink-2);font-size:14px;}
.notes li{margin:7px 0;}
.notes b{color:var(--ink);}

.foot{display:flex;justify-content:space-between;flex-wrap:wrap;gap:10px;margin-top:28px;
  padding-top:18px;border-top:1px solid var(--line);font-size:12px;color:var(--muted);}
code{font-family:var(--font-mono);font-size:.92em;background:var(--panel-2);padding:1px 5px;border-radius:4px;}
.foot code{background:transparent;padding:0;}

@media (max-width:720px){
  .wrap{padding:28px 16px 48px;}
  .kpis{grid-template-columns:1fr;}
  .head{flex-direction:row;}
}
@media (prefers-reduced-motion: reduce){ *{transition:none !important;} }
"""


def main():
    nested = load_nested()
    data_json = json.dumps(nested, ensure_ascii=False, separators=(",", ":"))
    html = HTML.replace("__DATA__", data_json)
    title = "<title>Observatório da Educação — Santa Maria/RS</title>"
    doc = f"{title}\n<style>\n{CSS}\n</style>\n{html}"
    OUT.write_text(doc, encoding="utf-8")
    print(f"✔ {OUT.relative_to(ROOT)} ({OUT.stat().st_size/1024:.1f} KB)")


if __name__ == "__main__":
    main()
