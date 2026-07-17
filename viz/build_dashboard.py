#!/usr/bin/env python3
"""Dashboard — lê o fato tidy (DuckDB) e gera uma peça editorial de dados, autocontida.

Não é um "explorador de indicadores": é um artigo que conta um fio condutor — a distância
entre Santa Maria e as referências aumenta conforme as etapas avançam. Segue princípios
de data-journalism (cor como atenção seletiva: Santa Maria em destaque, RS/Brasil em cinza;
anotação direta na linha; a escolha do gráfico é a narrativa). Dados embutidos inline (o
Artifact/CSP bloqueia rede). O explorador interativo fica no fim, como ferramenta secundária.
"""
import json
import urllib.parse
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "data" / "educacao.duckdb"
OUT = ROOT / "viz" / "dashboard.html"          # versão p/ o Artifact (só conteúdo)
PUB = ROOT / "public" / "index.html"           # versão standalone p/ web/Railway
ARCH_OUT = ROOT / "viz" / "arquitetura.html"
ARCH_PUB = ROOT / "public" / "arquitetura.html"


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


def _latest_common(nested, indicator, stage, levels=("brasil", "rs", "santa_maria")):
    series = nested[indicator][stage]
    by_level = {level: dict(series[level]) for level in levels}
    common_years = set.intersection(*(set(values) for values in by_level.values()))
    if not common_years:
        raise ValueError(f"Sem ano comum para {indicator}/{stage}")
    year = max(common_years)
    return year, {level: by_level[level][year] for level in levels}


def _percent(value):
    return f"{value:.1f}".replace(".", ",")


SITE_NAV = r"""<nav class="site-nav" aria-label="Navegação principal">
  <div class="site-nav-inner">
    <a class="site-brand" href="index.html">Observatório da Educação</a>
    <div class="site-links">
      <a href="index.html" data-page="analise">Análise</a>
      <a href="arquitetura.html" data-page="arquitetura">Arquitetura e metodologia</a>
    </div>
  </div>
</nav>"""


HTML = r"""<main class="paper">

  <header class="masthead">
    <p class="kicker">Observatório da educação básica · indicadores oficiais · Santa Maria / RS</p>
    <h1 class="headline">A distância aumenta<br>ao longo do percurso</h1>
    <p class="standfirst">Nos anos iniciais, Santa Maria permanece próxima do Brasil e do Rio
      Grande do Sul. Nas etapas seguintes, as diferenças de aprovação e atraso escolar se
      ampliam. Vinte anos de dados oficiais do INEP mostram tanto a melhora recente quanto o
      desafio que permanece no Ensino Médio.</p>
    <button id="theme" class="theme-btn" type="button" aria-label="Alternar tema">tema</button>
  </header>

  <!-- HERO: a queda entre etapas -->
  <section class="hero" id="analise">
    <div class="hero-lead">
      <p class="lede">O IDEB vai de 0 a 10. Siga a linha de Santa Maria por dentro de uma
        mesma foto de 2023, à medida que o aluno sobe as etapas:</p>
    </div>
    <figure class="fig fig-hero">
      <svg id="traj" viewBox="0 0 860 360" role="img" aria-label="Trajetória do IDEB de Santa Maria por etapa em 2023"></svg>
    </figure>
    <p class="hero-caption">A comparação entre etapas não acompanha a mesma turma, mas revela um
      contraste importante: Santa Maria marca <b>5,8</b> nos anos iniciais e <b>2,4</b> no Médio,
      enquanto o Brasil registra 5,7 e 4,1, respectivamente.</p>
  </section>

  <div class="rule"></div>

  <!-- ATO 1 -->
  <article class="act">
    <div class="act-txt">
      <p class="act-num">Anos iniciais</p>
      <h2>Na base, a cidade permanece próxima das referências.</h2>
      <p>Entre 2005 e 2023, o IDEB dos anos iniciais de Santa Maria saltou de 4,3 para
        <b>5,8</b>. No último ano, empatou com o Rio Grande do Sul e ficou um décimo acima do
        Brasil. O indicador mostra uma base comparável às referências, sem explicar sozinho
        o que acontece nas etapas seguintes.</p>
    </div>
    <figure class="fig" data-chart data-ind="ideb" data-eta="ef_anos_iniciais"
      data-ann='[{"niv":"santa_maria","ano":2005,"text":"4,3 em 2005","ty":4.65,"tano":2005},{"niv":"santa_maria","ano":2023,"text":"5,8: empata com o RS e supera o Brasil","ty":5.35,"tano":2018}]'></figure>
  </article>

  <!-- ATO 2 -->
  <article class="act">
    <div class="act-txt">
      <p class="act-num">A cicatriz invisível</p>
      <h2>A pandemia derrubou o aprendizado. A aprovação escondeu a queda.</h2>
      <p>O IDEB mistura duas coisas: <i>quanto o aluno aprende</i> (a nota SAEB) e <i>quantos
        passam de ano</i> (a aprovação). Separadas, aparece o que o índice suaviza. Em 2021 a
        proficiência em Matemática despencou durante a pandemia, enquanto a
        <b>taxa de aprovação subia</b>. Aprovou-se mais gente que aprendeu menos.</p>
    </div>
    <figure class="fig" data-chart data-ind="saeb_matematica" data-eta="ef_anos_iniciais"
      data-ann='[{"niv":"santa_maria","ano":2021,"text":"queda da pandemia: −15 pontos","ty":214,"tano":2015}]'></figure>
  </article>

  <!-- ATO 3 -->
  <article class="act">
    <div class="act-txt">
      <p class="act-num">A diferença entre etapas</p>
      <h2>A distância de aprovação cresce no Ensino Médio.</h2>
      <p>Em __APROV_YEAR__, Santa Maria ficou __APROV_GAP_AI__ pontos percentuais abaixo do Brasil
        nos anos iniciais, __APROV_GAP_AF__ nos finais e __APROV_GAP_EM__ no Médio. Nessa última
        etapa, a cidade registrou <b>__APROV_SM__%</b>, ante __APROV_RS__% no RS e
        __APROV_BR__% no país. É uma diferença relevante, embora o resultado local tenha
        melhorado desde 2019.</p>
    </div>
    <figure class="fig" data-chart data-ind="taxa_aprovacao" data-eta="em"
      data-ann='[]'></figure>
  </article>

  <!-- ATO 4 -->
  <article class="act">
    <div class="act-txt">
      <p class="act-num">O atraso escolar</p>
      <h2>A diferença é pequena na base e maior nas etapas seguintes.</h2>
      <p>Em __TDI_YEAR__, a TDI de Santa Maria estava praticamente alinhada ao Brasil nos anos
        iniciais (__TDI_AI_SM__% contra __TDI_AI_BR__%). Nos anos finais, passou a
        <b>__TDI_AF_SM__%</b> contra __TDI_AF_BR__%; no Médio, chegou a __TDI_EM_SM__% contra
        __TDI_EM_BR__%. A TDI local caiu desde 2019, mas menos que nas duas referências.</p>
    </div>
    <figure class="fig" data-chart data-ind="distorcao_idade_serie" data-eta="ef_anos_finais"
      data-ann='[]'></figure>
  </article>

  <div class="rule"></div>

  <!-- EXPLORADOR -->
  <section class="explore" id="explorador">
    <p class="act-num">Explore você mesmo</p>
    <h2>Todos os indicadores, todas as etapas.</h2>
    <p class="explore-lede">Escolha o indicador e a etapa. Santa Maria em destaque; Brasil (cinza
      cheio) e RS (cinza tracejado) como referência. Passe o mouse para os valores.</p>
    <div class="controls">
      <div class="ctl"><span class="ctl-lbl">Indicador</span><div id="ind-pills" class="pills"></div></div>
      <div class="ctl"><span class="ctl-lbl">Etapa</span><div id="eta-pills" class="pills"></div></div>
    </div>
    <div class="chart-head">
      <h3 id="ex-title">—</h3>
      <button id="view-toggle" class="link-btn" type="button">ver tabela</button>
    </div>
    <p id="ex-unit" class="ex-unit">—</p>
    <figure class="fig" id="ex-fig">
      <svg id="ex-chart" viewBox="0 0 860 400" role="img" aria-labelledby="ex-title"></svg>
      <div id="ex-tip" class="tooltip" hidden></div>
    </figure>
    <div id="ex-legend" class="legend"></div>
    <div id="ex-table" class="table-wrap" hidden></div>
  </section>

  <footer class="foot">
    <div class="foot-notes">
      <p class="foot-h">Como estes números foram tratados</p>
      <p>Rendimento e distorção idade-série vêm diretamente das planilhas oficiais do INEP.
        O pipeline aceita os formatos históricos XLS e XLSX, valida valores de referência e
        registra URL, tamanho e SHA-256 de cada arquivo. IDEB e SAEB permanecem no snapshot
        auditado obtido pela Base dos Dados enquanto a segunda fase da migração é preparada.</p>
    </div>
    <div class="foot-meta">
      <span>Fonte: planilhas oficiais do INEP · IDEB/SAEB via <code>br_inep_ideb</code></span>
      <span>Santa Maria/RS · IBGE <code>4316907</code></span>
      <span>IDEB e SAEB: rede pública · demais indicadores: rede total · 2005–2025</span>
      <span class="foot-author">Projeto desenvolvido por <a href="https://github.com/leonardo-michelotti" target="_blank" rel="noopener noreferrer">Leonardo Michelotti</a>. Código e metodologia disponíveis no <a href="https://github.com/leonardo-michelotti/observatorio-educacao-rs" target="_blank" rel="noopener noreferrer">GitHub</a>.</span>
    </div>
  </footer>
</main>

<script>
const DATA = __DATA__;

const IND = {
  ideb:                    {label:"IDEB",                     unit:"IDEB — escala de 0 a 10"},
  saeb_matematica:         {label:"SAEB · Matemática",        unit:"Proficiência — escala SAEB"},
  saeb_lingua_portuguesa:  {label:"SAEB · Língua Portuguesa", unit:"Proficiência — escala SAEB"},
  taxa_aprovacao:          {label:"Taxa de aprovação",        unit:"% de alunos aprovados"},
  distorcao_idade_serie:   {label:"Distorção idade-série",    unit:"% de alunos em atraso idade-série"},
};
const IND_ORDER = ["ideb","saeb_matematica","saeb_lingua_portuguesa","taxa_aprovacao","distorcao_idade_serie"];
const ETA = {ef_anos_iniciais:"Anos iniciais", ef_anos_finais:"Anos finais", em:"Ensino médio"};
const ETA_ORDER = ["ef_anos_iniciais","ef_anos_finais","em"];
const NIV = {
  santa_maria:{label:"Santa Maria",       cls:"sm"},
  brasil:     {label:"Brasil",            cls:"br"},
  rs:         {label:"Rio Grande do Sul", cls:"rs"},
};
const NIV_ORDER = ["santa_maria","brasil","rs"];  // protagonista primeiro; contexto depois
const MIN_POINTS = 5;

const NS = "http://www.w3.org/2000/svg";
const fmt = n => n.toLocaleString("pt-BR",{minimumFractionDigits:1,maximumFractionDigits:1});
const fmt0 = n => fmt(n).replace(",0","");
const el = (t,a) => { const e=document.createElementNS(NS,t); for(const k in a) e.setAttribute(k,a[k]); return e; };

function seriesFor(ind, eta){
  const d = (DATA[ind]||{})[eta] || {};
  return NIV_ORDER.filter(n => d[n] && d[n].length >= MIN_POINTS).map(n => ({niv:n, pts:d[n]}));
}
function etapasFor(ind){
  return ETA_ORDER.filter(e => DATA[ind] && DATA[ind][e] &&
    NIV_ORDER.filter(n => (DATA[ind][e][n]||[]).length >= MIN_POINTS).length >= 2);
}
function valAt(pts, ano){ const h = pts.find(p=>p[0]===ano); return h?h[1]:null; }

// ---- scales ----------------------------------------------------------------
function niceStep(range, target){
  const raw = range/target, mag = Math.pow(10, Math.floor(Math.log10(raw))), n = raw/mag;
  return (n<1.5?1:n<3?2:n<7?5:10)*mag;
}
function scales(series, W, H, M){
  let ylo=Infinity, yhi=-Infinity, xlo=Infinity, xhi=-Infinity;
  series.forEach(s=>s.pts.forEach(([a,v])=>{ylo=Math.min(ylo,v);yhi=Math.max(yhi,v);xlo=Math.min(xlo,a);xhi=Math.max(xhi,a);}));
  if(ylo===yhi){ylo-=1;yhi+=1;}
  const pad=(yhi-ylo)*0.14; ylo-=pad; yhi+=pad;
  const step=niceStep(yhi-ylo,4); ylo=Math.floor(ylo/step)*step; yhi=Math.ceil(yhi/step)*step;
  const iw=W-M.l-M.r, ih=H-M.t-M.b;
  const sx=a=>M.l+(xhi===xlo?iw/2:(a-xlo)/(xhi-xlo)*iw);
  const sy=v=>M.t+(1-(v-ylo)/(yhi-ylo))*ih;
  return {sx,sy,ylo,yhi,step,xlo,xhi,iw,ih};
}

// ---- time-series chart (highlight scheme) ----------------------------------
const M = {t:22, r:118, b:34, l:44};
const CW = 860, CHH = 400;

function drawSeries(svg, fig, ind, eta, opts){
  opts = opts || {};
  svg.innerHTML = "";
  fig.querySelectorAll(".annot").forEach(n=>n.remove());
  const series = seriesFor(ind, eta);
  if(!series.length) return null;
  const H = opts.H || CHH;
  const sc = scales(series, CW, H, M);
  const {sx, sy} = sc;

  for(let v=sc.ylo; v<=sc.yhi+1e-9; v+=sc.step){
    svg.appendChild(el("line",{x1:M.l,x2:CW-M.r,y1:sy(v),y2:sy(v),class:"grid"}));
    const t=el("text",{x:M.l-8,y:sy(v)+3.5,class:"axis-lbl","text-anchor":"end"}); t.textContent=fmt0(v); svg.appendChild(t);
  }
  const span=sc.xhi-sc.xlo, xs=Math.max(1,Math.round(span/6));
  for(let a=sc.xlo;a<=sc.xhi;a+=xs){ const t=el("text",{x:sx(a),y:H-M.b+18,class:"axis-lbl","text-anchor":"middle"}); t.textContent=a; svg.appendChild(t); }

  // connectors for annotations (drawn under lines)
  (opts.ann||[]).forEach(an=>{
    const s=series.find(x=>x.niv===an.niv); if(!s) return;
    const v=valAt(s.pts,an.ano); if(v==null) return;
    const x2=sx(an.tano!=null?an.tano:an.ano), y2=sy(an.ty!=null?an.ty:v);
    svg.appendChild(el("line",{x1:sx(an.ano),y1:sy(v),x2:x2,y2:y2,class:"annot-line "+(NIV[an.niv]?"c-"+NIV[an.niv].cls:"")}));
    svg.appendChild(el("circle",{cx:sx(an.ano),cy:sy(v),r:3.5,class:"annot-anchor d-"+NIV[an.niv].cls}));
  });

  // series (context first so protagonist paints on top)
  [...series].reverse().forEach(s=>{
    const cls=NIV[s.niv].cls, top=s.niv==="santa_maria";
    const d=s.pts.map(([a,v],i)=>`${i?"L":"M"}${sx(a).toFixed(1)},${sy(v).toFixed(1)}`).join(" ");
    svg.appendChild(el("path",{d,class:`line l-${cls}`,fill:"none"}));
    if(top) s.pts.forEach(([a,v])=>svg.appendChild(el("circle",{cx:sx(a),cy:sy(v),r:3,class:`dot d-${cls}`})));
    const [la,lv]=s.pts[s.pts.length-1];
    svg.appendChild(el("circle",{cx:sx(la),cy:sy(lv),r:3.4,class:`dot-end d-${cls}`}));
    const t=el("text",{x:sx(la)+9,y:sy(lv)+3.6,class:`end-lbl e-${cls}`});
    t.innerHTML=`<tspan class="e-val">${fmt0(lv)}</tspan>  <tspan class="e-name">${NIV[s.niv].short||NIV[s.niv].label}</tspan>`;
    svg.appendChild(t);
  });

  // annotation text as HTML overlays (positioned by %)
  (opts.ann||[]).forEach(an=>{
    const s=series.find(x=>x.niv===an.niv); if(!s||valAt(s.pts,an.ano)==null) return;
    const x=sx(an.tano!=null?an.tano:an.ano), y=sy(an.ty!=null?an.ty:valAt(s.pts,an.ano));
    const div=document.createElement("div");
    div.className="annot a-"+NIV[an.niv].cls;
    div.textContent=an.text;
    div.style.left=(x/CW*100)+"%"; div.style.top=(y/H*100)+"%";
    fig.appendChild(div);
  });

  if(opts.hover) attachHover(svg, fig, series, sx, sy, CW, H);
  return {series, sx, sy};
}

// ---- hover -----------------------------------------------------------------
function attachHover(svg, fig, series, sx, sy, W, H){
  let tip=fig.querySelector(".tooltip");
  const focus=el("g",{class:"focus",visibility:"hidden"});
  const vline=el("line",{y1:M.t,y2:H-M.b,class:"crosshair"}); focus.appendChild(vline);
  const dots=series.map(s=>{const c=el("circle",{r:4.5,class:"focus-dot d-"+NIV[s.niv].cls}); focus.appendChild(c); return c;});
  svg.appendChild(focus);
  const hit=el("rect",{x:M.l,y:M.t,width:W-M.l-M.r,height:H-M.t-M.b,fill:"transparent",style:"cursor:crosshair"});
  svg.appendChild(hit);
  const years=[...new Set(series.flatMap(s=>s.pts.map(p=>p[0])))].sort((a,b)=>a-b);
  hit.addEventListener("pointermove",ev=>{
    const pt=svg.createSVGPoint(); pt.x=ev.clientX; pt.y=ev.clientY;
    const loc=pt.matrixTransform(svg.getScreenCTM().inverse());
    let best=years[0],bd=1e9; years.forEach(y=>{const d=Math.abs(sx(y)-loc.x); if(d<bd){bd=d;best=y;}});
    const x=sx(best); focus.setAttribute("visibility","visible"); vline.setAttribute("x1",x); vline.setAttribute("x2",x);
    let rows="";
    series.forEach((s,i)=>{ const v=valAt(s.pts,best);
      if(v!=null){dots[i].setAttribute("visibility","visible");dots[i].setAttribute("cx",x);dots[i].setAttribute("cy",sy(v));
        rows+=`<div class="tip-row"><span class="tip-dot dot-${NIV[s.niv].cls}"></span>${NIV[s.niv].label}<b>${fmt(v)}</b></div>`;
      } else dots[i].setAttribute("visibility","hidden"); });
    if(!tip){tip=fig.querySelector(".tooltip");}
    tip.innerHTML=`<div class="tip-year">${best}</div>${rows}`; tip.hidden=false;
    const r=fig.getBoundingClientRect(), px=x/W*r.width;
    tip.style.left=Math.min(r.width-tip.offsetWidth-8,Math.max(8,px+12))+"px";
  });
  hit.addEventListener("pointerleave",()=>{focus.setAttribute("visibility","hidden"); if(tip) tip.hidden=true;});
}

// ---- HERO: trajectory across stages ----------------------------------------
function drawTrajectory(){
  const svg=document.getElementById("traj"); svg.innerHTML="";
  const W=860,H=360,ML=40,MR=134,MT=54,MB=64;
  const stages=["ef_anos_iniciais","ef_anos_finais","em"];
  const YEAR=2023;
  const get=(niv)=>stages.map(e=>valAt(((DATA.ideb||{})[e]||{})[niv]||[],YEAR));
  const sm=get("santa_maria"), br=get("brasil");
  const ylo=2, yhi=6.2;
  const x=i=>ML+i*((W-ML-MR)/(stages.length-1));
  const y=v=>MT+(1-(v-ylo)/(yhi-ylo))*(H-MT-MB);
  // faint horizontal guides
  [3,4,5,6].forEach(v=>{ svg.appendChild(el("line",{x1:ML,x2:W-MR,y1:y(v),y2:y(v),class:"grid"}));
    const t=el("text",{x:ML-6,y:y(v)+3.5,class:"axis-lbl","text-anchor":"end"}); t.textContent=v; svg.appendChild(t); });
  // stage labels
  stages.forEach((e,i)=>{ const t=el("text",{x:x(i),y:H-MB+26,class:"stage-lbl","text-anchor":"middle"}); t.textContent=ETA[e]; svg.appendChild(t); });
  function path(vals){ return vals.map((v,i)=>v==null?null:`${i&&vals[i-1]!=null?"L":"M"}${x(i)},${y(v)}`).filter(Boolean).join(" "); }
  // Brasil (contexto) — sem números inline; rótulo só no fim, onde as linhas se separam
  svg.appendChild(el("path",{d:path(br),class:"traj-line l-br",fill:"none"}));
  br.forEach((v,i)=>{ if(v==null) return; svg.appendChild(el("circle",{cx:x(i),cy:y(v),r:4,class:"dot d-br"})); });
  // Santa Maria (protagonista) — números nos dois primeiros pontos; o do fim vai no rótulo
  svg.appendChild(el("path",{d:path(sm),class:"traj-line l-sm",fill:"none"}));
  sm.forEach((v,i)=>{ if(v==null) return; svg.appendChild(el("circle",{cx:x(i),cy:y(v),r:5,class:"dot-end d-sm"}));
    if(i<sm.length-1){ const t=el("text",{x:x(i),y:y(v)-14,class:"traj-num n-sm","text-anchor":"middle"}); t.textContent=fmt(v); svg.appendChild(t); } });
  // rótulos-fim: valor + nome, bem separados (SM embaixo em 2,4; Brasil acima em 4,1)
  const li=sm.length-1;
  const tSM=el("text",{x:x(li)+16,y:y(sm[li])+5,class:"traj-endtag"});
  tSM.innerHTML=`<tspan class="n-sm traj-endnum">${fmt(sm[li])}</tspan><tspan class="t-sm" dx="7">Santa Maria</tspan>`;
  svg.appendChild(tSM);
  const tBR=el("text",{x:x(li)+16,y:y(br[li])+5,class:"traj-endtag"});
  tBR.innerHTML=`<tspan class="n-br traj-endnum">${fmt(br[li])}</tspan><tspan class="t-br" dx="7">Brasil</tspan>`;
  svg.appendChild(tBR);
}

// ---- narrative charts ------------------------------------------------------
function drawNarrative(){
  document.querySelectorAll("[data-chart]").forEach(fig=>{
    const svg=fig.querySelector("svg") || (()=>{const s=el("svg",{viewBox:`0 0 ${CW} ${CHH}`}); s.setAttribute("role","img"); fig.appendChild(s); return s;})();
    svg.setAttribute("aria-label",`${IND[fig.dataset.ind].label}, ${ETA[fig.dataset.eta]}. Série temporal comparando os níveis disponíveis.`);
    const ann=fig.dataset.ann?JSON.parse(fig.dataset.ann):[];
    drawSeries(svg, fig, fig.dataset.ind, fig.dataset.eta, {ann, hover:true});
  });
}

// ---- explorer --------------------------------------------------------------
const state={ind:"ideb",eta:"ef_anos_finais"};
let tableOpen=false;
function buildPills(){
  const ip=document.getElementById("ind-pills"); ip.innerHTML="";
  IND_ORDER.forEach(ind=>{ const b=document.createElement("button"); b.className="pill"; b.type="button"; b.textContent=IND[ind].label;
    b.dataset.ind=ind;
    b.onclick=()=>{ state.ind=ind; if(!etapasFor(ind).includes(state.eta)) state.eta=etapasFor(ind)[0]; renderEx(); };
    ip.appendChild(b); });
}
function buildEtapa(){
  const ep=document.getElementById("eta-pills"); ep.innerHTML=""; const avail=etapasFor(state.ind);
  ETA_ORDER.forEach(eta=>{ const b=document.createElement("button"); b.className="pill"; b.type="button"; b.textContent=ETA[eta];
    b.dataset.eta=eta; b.disabled=!avail.includes(eta);
    if(avail.includes(eta)) b.onclick=()=>{state.eta=eta; renderEx();};
    ep.appendChild(b); });
}
function syncPills(){
  document.querySelectorAll("#ind-pills .pill").forEach(b=>b.setAttribute("aria-pressed",b.dataset.ind===state.ind));
  document.querySelectorAll("#eta-pills .pill").forEach(b=>b.setAttribute("aria-pressed",b.dataset.eta===state.eta));
}
function drawLegend(){
  const lg=document.getElementById("ex-legend"); lg.innerHTML="";
  seriesFor(state.ind,state.eta).forEach(s=>{ const i=document.createElement("span"); i.className="leg-item";
    i.innerHTML=`<span class="leg-swatch sw-${NIV[s.niv].cls}"></span>${NIV[s.niv].label}`; lg.appendChild(i); });
}
function drawTable(){
  const wrap=document.getElementById("ex-table"); const series=seriesFor(state.ind,state.eta);
  const years=[...new Set(series.flatMap(s=>s.pts.map(p=>p[0])))].sort((a,b)=>a-b);
  const map={}; series.forEach(s=>map[s.niv]=Object.fromEntries(s.pts));
  let h=`<table><caption>${IND[state.ind].label}, ${ETA[state.eta]}</caption><thead><tr><th scope="col">Ano</th>${series.map(s=>`<th scope="col">${NIV[s.niv].label}</th>`).join("")}</tr></thead><tbody>`;
  years.forEach(y=>{ h+=`<tr><td>${y}</td>${series.map(s=>`<td>${map[s.niv][y]!=null?fmt(map[s.niv][y]):"—"}</td>`).join("")}</tr>`; });
  wrap.innerHTML=h+"</tbody></table>";
}
function renderEx(){
  buildEtapa(); syncPills();
  document.getElementById("ex-title").textContent=`${IND[state.ind].label} · ${ETA[state.eta]}`;
  document.getElementById("ex-unit").textContent=IND[state.ind].unit;
  drawSeries(document.getElementById("ex-chart"), document.getElementById("ex-fig"), state.ind, state.eta, {hover:true});
  drawLegend(); drawTable();
  document.getElementById("ex-table").hidden=!tableOpen;
  document.getElementById("ex-fig").hidden=tableOpen;
  document.getElementById("ex-legend").hidden=tableOpen;
  document.getElementById("view-toggle").textContent=tableOpen?"ver gráfico":"ver tabela";
}

// ---- theme -----------------------------------------------------------------
function initTheme(){
  const root=document.documentElement;
  const cur=()=>root.getAttribute("data-theme")||(matchMedia("(prefers-color-scheme: dark)").matches?"dark":"light");
  const button=document.getElementById("theme");
  button.onclick=()=>{const next=cur()==="dark"?"light":"dark";root.setAttribute("data-theme",next);button.setAttribute("aria-pressed",next==="dark");};
}

// ---- boot ------------------------------------------------------------------
NIV.rs.short="RS"; NIV.brasil.short="Brasil"; NIV.santa_maria.short="Santa Maria";
initTheme();
drawTrajectory();
drawNarrative();
buildPills(); renderEx();
document.getElementById("view-toggle").onclick=()=>{tableOpen=!tableOpen; renderEx();};
addEventListener("resize",()=>{ drawTrajectory(); drawNarrative(); if(!tableOpen) renderEx(); });
</script>
"""

ARCH_HTML = r"""<main class="paper architecture">
  <header class="arch-head">
    <p class="kicker">Engenharia de dados · decisões reproduzíveis</p>
    <h1 class="headline">Arquitetura<br>e metodologia</h1>
    <p class="standfirst">Do dado público do INEP à narrativa visual. Esta página abre as
      camadas do projeto, mostra onde cada decisão acontece e registra o que entra, o que fica
      de fora e por quê.</p>
    <button id="theme" class="theme-btn" type="button" aria-label="Alternar tema" aria-pressed="false">tema</button>
  </header>

  <section class="arch-section">
    <p class="act-num">Visão do sistema</p>
    <h2>Um caminho único, com responsabilidades separadas.</h2>
    <p class="section-lede">A arquitetura medalhão é lógica: bronze, staging e mart vivem no
      mesmo projeto local, mas cada camada tem um contrato diferente.</p>
    <div class="system-map" role="img" aria-label="Fluxo dos dados do INEP até o painel">
      <article><span>01 · Origem</span><h3>INEP</h3><p>Indicadores públicos oficiais</p></article>
      <article><span>02 · Acesso</span><h3>Base dos Dados</h3><p>Tabelas no BigQuery</p></article>
      <article><span>03 · Bronze</span><h3>Parquet</h3><p>Extração local preservada</p></article>
      <article><span>04 · Silver e gold</span><h3>dbt + DuckDB</h3><p>Curadoria, modelo e testes</p></article>
      <article><span>05 · Produto</span><h3>PNG + HTML</h3><p>Narrativa e explorador</p></article>
    </div>
  </section>

  <section class="arch-section">
    <p class="act-num">Responsabilidade por camada</p>
    <h2>O dado muda de papel, não apenas de formato.</h2>
    <div class="layer-list">
      <article class="layer-row"><div class="layer-id"><span>Fonte</span><b>INEP</b></div><div><h3>O que representa</h3><p>Publicações oficiais de IDEB, SAEB, rendimento e indicadores educacionais.</p></div><div><h3>Como acessamos</h3><p>Rendimento e TDI vêm das planilhas oficiais; IDEB/SAEB usam snapshot auditado da Base dos Dados.</p></div></article>
      <article class="layer-row"><div class="layer-id"><span>Bronze</span><b>Parquet</b></div><div><h3>O que preserva</h3><p>Recortes de Brasil, RS e Santa Maria, separados da lógica analítica.</p></div><div><h3>Contrato</h3><p>A extração é a entrada reproduzível; não recebe regras editoriais.</p></div></article>
      <article class="layer-row"><div class="layer-id"><span>Silver</span><b>staging</b></div><div><h3>O que transforma</h3><p>Normaliza etapas, tipos e nomes; converte indicadores largos para formato tidy.</p></div><div><h3>Onde há curadoria</h3><p>Filtros e exclusões auditadas ficam explícitos em SQL versionado.</p></div></article>
      <article class="layer-row"><div class="layer-id"><span>Gold</span><b>mart</b></div><div><h3>O que entrega</h3><p><code>fct_indicadores</code>, uma linha por indicador, nível, etapa, ano e valor.</p></div><div><h3>Quem consome</h3><p>Os geradores de gráficos e do painel leem apenas esse contrato final.</p></div></article>
    </div>
  </section>

  <section class="arch-section">
    <p class="act-num">Orquestração</p>
    <h2><code>run_pipeline.py</code> encadeia quatro etapas.</h2>
    <ol class="runbook">
      <li><span>01</span><div><b>Ingestão</b><code>ingestion/extract_inep.py</code><p>Baixa as planilhas oficiais e grava a bronze com proveniência.</p></div></li>
      <li><span>02</span><div><b>Transformação e testes</b><code>dbt build</code><p>Materializa staging e mart no DuckDB.</p></div></li>
      <li><span>03</span><div><b>Gráficos</b><code>viz/make_charts.py</code><p>Gera os PNGs usados no README.</p></div></li>
      <li><span>04</span><div><b>Painel</b><code>viz/build_dashboard.py</code><p>Gera as páginas autocontidas para web.</p></div></li>
    </ol>
    <p class="method-note">Cada execução recompõe os produtos pelas mesmas regras. Código,
      SQL, testes, documentação e saídas publicadas são rastreados no Git. O dbt registra a
      dependência entre modelos por meio de <code>ref()</code>.</p>
  </section>

  <section class="arch-section">
    <p class="act-num">Contrato analítico</p>
    <h2>Quatro regras sustentam o que aparece no painel.</h2>
    <div class="rule-grid">
      <article><span>Índice</span><h3>IDEB</h3><p>Combina rendimento com proficiência padronizada a partir do SAEB. Notas por disciplina e aprovação aparecem separadas para revelar os componentes.</p></article>
      <article><span>Validade</span><h3>Aprovação</h3><p>O pipeline valida o intervalo físico de 0% a 100% e referências oficiais de 2025.</p></article>
      <article><span>Recorte</span><h3>Distorção idade-série</h3><p>As três etapas oficiais ficam disponíveis para Brasil, RS e Santa Maria.</p></article>
      <article><span>Solidez</span><h3>Séries comparáveis</h3><p>Uma etapa entra quando dois níveis têm cinco ou mais anos válidos. Só os níveis que cumprem o mínimo são desenhados.</p></article>
    </div>
  </section>

  <section class="arch-section quality">
    <p class="act-num">Qualidade e proveniência</p>
    <h2>A origem e cada transformação são verificáveis.</h2>
    <div class="quality-grid">
      <div><h3>O que foi encontrado</h3><p>Há valores incompatíveis na harmonização da Base dos Dados. A publicação oficial do INEP é pública e constitui a referência de origem.</p></div>
      <div><h3>Como o projeto responde</h3><p>Consome as planilhas oficiais sem interpolar nem corrigir números manualmente e registra hashes dos arquivos.</p></div>
      <div><h3>Próxima evolução</h3><p>Migrar também IDEB e SAEB para uma fonte oficial direta e eliminar a dependência restante do BigQuery.</p></div>
    </div>
  </section>

  <footer class="foot"><div class="foot-meta"><span>Python · BigQuery · Parquet · dbt · DuckDB · Caddy</span><span>Modelos e decisões versionados no repositório</span><span class="foot-author">Projeto desenvolvido por <a href="https://github.com/leonardo-michelotti" target="_blank" rel="noopener noreferrer">Leonardo Michelotti</a>. Código e metodologia disponíveis no <a href="https://github.com/leonardo-michelotti/observatorio-educacao-rs" target="_blank" rel="noopener noreferrer">GitHub</a>.</span><a href="index.html">Voltar à análise dos indicadores</a></div></footer>
</main>
<script>
const root=document.documentElement,button=document.getElementById("theme");
const currentTheme=()=>root.getAttribute("data-theme")||(matchMedia("(prefers-color-scheme: dark)").matches?"dark":"light");
button.onclick=()=>{const next=currentTheme()==="dark"?"light":"dark";root.setAttribute("data-theme",next);button.setAttribute("aria-pressed",next==="dark");};
</script>"""

CSS = r"""
:root{
  --paper:#f5f4ef; --ink:#1c1b16; --ink-2:#565349; --muted:#928e82; --rule:#d8d5cb; --rule-2:#e6e3da;
  --sm:#c1402a; --br:#3f3c34; --rs:#a29d90;
  --font-serif:"Iowan Old Style","Charter","Sorts Mill Goudy","Georgia","Times New Roman",serif;
  --font-sans:ui-sans-serif,"Avenir Next","Segoe UI",system-ui,sans-serif;
}
@media (prefers-color-scheme: dark){
  :root{ --paper:#16150f; --ink:#efe9d9; --ink-2:#b2ac9a; --muted:#787366; --rule:#2e2b22; --rule-2:#221f18;
    --sm:#e0603f; --br:#c9c3b2; --rs:#7c7768; }
}
:root[data-theme="light"]{ --paper:#f5f4ef; --ink:#1c1b16; --ink-2:#565349; --muted:#928e82; --rule:#d8d5cb; --rule-2:#e6e3da;
  --sm:#c1402a; --br:#3f3c34; --rs:#a29d90; }
:root[data-theme="dark"]{ --paper:#16150f; --ink:#efe9d9; --ink-2:#b2ac9a; --muted:#787366; --rule:#2e2b22; --rule-2:#221f18;
  --sm:#e0603f; --br:#c9c3b2; --rs:#7c7768; }

*{box-sizing:border-box}
body{margin:0;background:var(--paper);color:var(--ink);font-family:var(--font-serif);
  line-height:1.62;-webkit-font-smoothing:antialiased;font-size:18px;}
.paper{max-width:720px;margin:0 auto;padding:64px 28px 72px;}
b{font-weight:700;} i{font-style:italic;}
code{font-family:var(--font-sans);font-size:.78em;color:var(--ink-2);letter-spacing:.01em;}

/* persistent site navigation */
.site-nav{position:sticky;top:0;z-index:20;background:color-mix(in srgb,var(--paper) 94%,transparent);
  border-bottom:1px solid var(--rule);backdrop-filter:blur(10px);font-family:var(--font-sans);}
.site-nav-inner{max-width:1040px;margin:0 auto;padding:10px 28px;display:flex;align-items:center;justify-content:space-between;gap:22px;}
.site-brand{color:var(--ink);font-size:12.5px;font-weight:700;text-decoration:none;white-space:nowrap;}
.site-links{display:flex;align-items:center;gap:22px;font-size:12.5px;}
.site-links a{color:var(--muted);text-decoration:none;padding:4px 0;border-bottom:1px solid transparent;}
.site-links a:hover,.site-links a[aria-current="page"]{color:var(--sm);border-bottom-color:var(--sm);}

/* masthead */
.masthead{position:relative;border-bottom:2px solid var(--ink);padding-bottom:26px;}
.kicker{font-family:var(--font-sans);font-size:12.5px;letter-spacing:.02em;color:var(--sm);
  text-transform:none;margin:0 0 18px;font-weight:600;}
.headline{font-size:clamp(34px,6.4vw,54px);line-height:1.02;font-weight:700;letter-spacing:-.015em;
  margin:0;text-wrap:balance;}
.standfirst{font-size:19px;color:var(--ink-2);margin:20px 0 0;max-width:60ch;line-height:1.55;}
.theme-btn{position:absolute;top:0;right:0;font-family:var(--font-sans);font-size:12px;color:var(--muted);
  background:none;border:1px solid var(--rule);border-radius:2px;padding:4px 9px;cursor:pointer;letter-spacing:.04em;}
.theme-btn:hover{color:var(--ink);border-color:var(--ink-2);}

/* hero */
.hero{margin:38px 0 8px;}
.lede,.hero-caption{font-size:17px;color:var(--ink-2);line-height:1.5;}
.lede{margin:0 0 6px;}
.hero-caption{margin:10px 0 0;border-left:2px solid var(--sm);padding-left:14px;}
.hero-caption b{color:var(--ink);}
.fig-hero{margin:14px 0 0;}

/* rules & sections */
.rule{height:0;border-top:1px solid var(--rule);margin:52px 0;}
.act{margin:46px 0;}
.act-num{font-family:var(--font-sans);font-size:12.5px;font-weight:700;letter-spacing:.02em;color:var(--sm);
  margin:0 0 6px;}
.act h2{font-size:clamp(23px,3.4vw,30px);line-height:1.14;font-weight:700;letter-spacing:-.01em;margin:0 0 12px;
  text-wrap:balance;}
.act p{margin:0;color:var(--ink-2);font-size:17.5px;line-height:1.56;max-width:62ch;}
.act p b{color:var(--ink);}

/* figures (no cards, no shadow) */
.fig{position:relative;margin:22px 0 0;}
.fig svg{width:100%;height:auto;display:block;overflow:visible;}
.grid{stroke:var(--rule-2);stroke-width:1;}
.axis-lbl{fill:var(--muted);font-family:var(--font-sans);font-size:11px;font-variant-numeric:tabular-nums;}
.line{stroke-width:2;stroke-linecap:round;stroke-linejoin:round;}
.l-sm{stroke:var(--sm);stroke-width:2.6;} .l-br{stroke:var(--br);} .l-rs{stroke:var(--rs);stroke-dasharray:5 4;}
.dot{stroke:var(--paper);stroke-width:1.4;}
.d-sm{fill:var(--sm);} .d-br{fill:var(--br);} .d-rs{fill:var(--rs);}
.dot-end{stroke:var(--paper);stroke-width:1.6;}
.end-lbl{font-family:var(--font-sans);font-size:12px;font-variant-numeric:tabular-nums;}
.end-lbl .e-val{font-weight:700;} .end-lbl .e-name{font-size:10.5px;}
.e-sm{fill:var(--sm);} .e-br{fill:var(--ink-2);} .e-rs{fill:var(--muted);}
.e-sm .e-name{fill:var(--sm);}

/* annotations */
.annot-line{stroke-width:1;fill:none;opacity:.55;}
.annot-line.c-sm{stroke:var(--sm);} .annot-line.c-br{stroke:var(--br);}
.annot-anchor{stroke:var(--paper);stroke-width:1.5;}
.annot{position:absolute;transform:translate(-50%,-50%);font-family:var(--font-sans);font-size:12px;
  line-height:1.25;max-width:150px;text-align:center;pointer-events:none;font-weight:600;
  background:var(--paper);padding:1px 5px;border-radius:2px;}
.annot.a-sm{color:var(--sm);} .annot.a-br{color:var(--ink-2);}

/* hero trajectory */
.traj-line{stroke-width:2.4;stroke-linecap:round;stroke-linejoin:round;fill:none;}
.traj-num{font-family:var(--font-serif);font-weight:700;font-size:20px;font-variant-numeric:tabular-nums;}
.n-sm{fill:var(--sm);} .n-br{fill:var(--ink-2);}
.stage-lbl{fill:var(--ink);font-family:var(--font-sans);font-size:13px;font-weight:600;}
.traj-endtag{font-family:var(--font-sans);font-size:12px;font-weight:600;}
.traj-endnum{font-family:var(--font-serif);font-weight:700;font-variant-numeric:tabular-nums;}
.n-sm.traj-endnum{font-size:22px;} .n-br.traj-endnum{font-size:16px;}
.t-sm{fill:var(--sm);} .t-br{fill:var(--muted);}

/* crosshair + tooltip */
.crosshair{stroke:var(--ink-2);stroke-width:1;stroke-dasharray:3 3;opacity:.45;}
.focus-dot{stroke:var(--paper);stroke-width:1.8;}
.tooltip{position:absolute;top:8px;background:var(--paper);border:1px solid var(--rule);border-radius:3px;
  padding:8px 10px;font-family:var(--font-sans);font-size:12.5px;pointer-events:none;min-width:150px;z-index:5;
  box-shadow:0 6px 18px rgba(0,0,0,.10);}
.tip-year{font-weight:700;margin-bottom:5px;font-variant-numeric:tabular-nums;}
.tip-row{display:flex;align-items:center;gap:7px;padding:2px 0;color:var(--ink-2);}
.tip-row b{margin-left:auto;color:var(--ink);font-variant-numeric:tabular-nums;}
.tip-dot,.leg-swatch{width:10px;flex:none;}
.tip-dot{height:10px;border-radius:50%;}
.dot-sm{background:var(--sm);} .dot-br{background:var(--br);} .dot-rs{background:var(--rs);}

/* explorer */
.explore{margin-top:8px;}
.explore h2{font-size:clamp(23px,3.4vw,30px);font-weight:700;margin:0 0 10px;letter-spacing:-.01em;}
.explore-lede{color:var(--ink-2);font-size:16.5px;margin:0 0 22px;}
.controls{display:flex;flex-wrap:wrap;gap:18px 28px;padding:16px 0;border-top:1px solid var(--rule);
  border-bottom:1px solid var(--rule);}
.ctl{display:flex;flex-direction:column;gap:9px;}
.ctl-lbl{font-family:var(--font-sans);font-size:11px;letter-spacing:.04em;color:var(--muted);text-transform:uppercase;}
.pills{display:flex;flex-wrap:wrap;gap:0;}
.pill{font-family:var(--font-sans);font-size:13.5px;padding:5px 13px;cursor:pointer;border:none;background:none;
  color:var(--muted);border-bottom:2px solid transparent;transition:color .12s,border-color .12s;}
.pill:hover:not(:disabled){color:var(--ink);}
.pill[aria-pressed="true"]{color:var(--ink);border-bottom-color:var(--sm);font-weight:600;}
.pill:disabled{opacity:.32;cursor:not-allowed;}
.pill:focus-visible,.link-btn:focus-visible,.theme-btn:focus-visible{outline:2px solid var(--sm);outline-offset:2px;}
.chart-head{display:flex;justify-content:space-between;align-items:baseline;margin:22px 0 2px;gap:12px;}
.chart-head h3{font-size:21px;font-weight:700;margin:0;}
.ex-unit{font-family:var(--font-sans);font-size:12.5px;color:var(--muted);margin:0 0 4px;}
.link-btn{font-family:var(--font-sans);font-size:13px;color:var(--sm);background:none;border:none;cursor:pointer;
  padding:0;border-bottom:1px solid currentColor;}
.legend{display:flex;flex-wrap:wrap;gap:18px;margin:12px 0 0;font-family:var(--font-sans);font-size:13px;color:var(--ink-2);}
.leg-item{display:flex;align-items:center;gap:7px;}
.leg-swatch{height:3px;border-radius:2px;}
.sw-sm{background:var(--sm);height:4px;} .sw-br{background:var(--br);}
.sw-rs{background:linear-gradient(90deg,var(--rs) 60%,transparent 60%);background-size:9px 100%;height:3px;}
.table-wrap{overflow-x:auto;margin-top:12px;}
table{border-collapse:collapse;width:100%;font-family:var(--font-sans);font-size:13.5px;}
caption{text-align:left;color:var(--muted);font-size:12px;padding:0 0 8px;}
th,td{padding:6px 12px;text-align:right;border-bottom:1px solid var(--rule-2);font-variant-numeric:tabular-nums;}
th:first-child,td:first-child{text-align:left;color:var(--muted);}
thead th{color:var(--ink-2);border-bottom:1px solid var(--rule);}

/* architecture page */
.architecture{max-width:1040px;}
.arch-head{position:relative;border-bottom:2px solid var(--ink);padding:0 0 34px;}
.arch-section{padding:58px 0;border-bottom:1px solid var(--rule);}
.arch-section h2{font-size:clamp(25px,3.5vw,38px);line-height:1.12;margin:0 0 12px;max-width:22ch;}
.section-lede{color:var(--ink-2);font-size:17px;max-width:64ch;margin:0 0 28px;}
.system-map{display:grid;grid-template-columns:repeat(5,1fr);margin-top:32px;border-top:1px solid var(--rule);border-bottom:1px solid var(--rule);}
.system-map article{position:relative;padding:18px 20px 20px 0;min-height:150px;}
.system-map article:not(:last-child)::after{content:"→";position:absolute;right:7px;top:65px;color:var(--sm);font-family:var(--font-sans);}
.system-map span,.rule-grid span,.layer-id span{font-family:var(--font-sans);font-size:10.5px;text-transform:uppercase;letter-spacing:.05em;color:var(--sm);}
.system-map h3{font-size:18px;line-height:1.15;margin:13px 20px 6px 0;}
.system-map p{font-family:var(--font-sans);font-size:12px;line-height:1.4;color:var(--muted);margin:0 20px 0 0;}
.layer-list{border-top:1px solid var(--rule);margin-top:30px;}
.layer-row{display:grid;grid-template-columns:150px 1fr 1fr;gap:30px;padding:24px 0;border-bottom:1px solid var(--rule);}
.layer-row h3{font-family:var(--font-sans);font-size:11px;text-transform:uppercase;letter-spacing:.04em;color:var(--muted);margin:0 0 6px;}
.layer-row p{font-size:15px;color:var(--ink-2);line-height:1.48;margin:0;}
.layer-id b{display:block;font-size:22px;margin-top:3px;}
.runbook{list-style:none;margin:30px 0 0;padding:0;border-top:1px solid var(--rule);}
.runbook li{display:grid;grid-template-columns:52px 1fr;padding:18px 0;border-bottom:1px solid var(--rule);}
.runbook>li>span{font-family:var(--font-sans);font-size:11px;color:var(--sm);padding-top:4px;}
.runbook b{display:inline-block;min-width:210px;font-size:17px;}
.runbook code{font-size:12px;}.runbook p{display:inline;color:var(--muted);font-size:14px;margin-left:18px;}
.rule-grid{display:grid;grid-template-columns:1fr 1fr;gap:1px;background:var(--rule);margin-top:30px;border:1px solid var(--rule);}
.rule-grid article{background:var(--paper);padding:24px;}
.rule-grid h3{font-size:22px;margin:5px 0 8px;}.rule-grid p{font-size:15px;line-height:1.5;color:var(--ink-2);margin:0;}
.quality-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:28px;margin-top:30px;}
.quality-grid h3{font-size:18px;margin:0 0 8px;}.quality-grid p{font-size:15px;color:var(--ink-2);line-height:1.5;margin:0;}
.method-note{border-left:2px solid var(--sm);padding-left:14px;font-size:15px;color:var(--ink-2);line-height:1.5;margin:30px 0 0;}

/* footer */
.foot{margin-top:56px;padding-top:26px;border-top:2px solid var(--ink);}
.foot-h{font-family:var(--font-sans);font-size:12.5px;font-weight:700;letter-spacing:.02em;color:var(--ink);margin:0 0 8px;}
.foot-notes p{font-size:15px;color:var(--ink-2);line-height:1.5;margin:0;max-width:66ch;}
.foot-meta{display:flex;flex-direction:column;gap:3px;margin-top:22px;font-family:var(--font-sans);font-size:11.5px;color:var(--muted);}
.foot-meta a{color:inherit;text-decoration-color:color-mix(in srgb,currentColor 45%,transparent);text-underline-offset:2px;}
.foot-meta a:hover{color:var(--ink);}
.foot-author{margin-top:8px;}

@media (max-width:760px){
  .site-nav-inner{padding:9px 18px;align-items:flex-start;}.site-brand{display:none}.site-links{width:100%;justify-content:space-between;gap:14px;}
  .paper{padding:44px 18px 56px;} body{font-size:17px;}
  .theme-btn{position:static;margin-top:18px;}
  .system-map{grid-template-columns:1fr 1fr;}.system-map article{min-height:125px}.system-map article:nth-child(2)::after,.system-map article:nth-child(4)::after{display:none;}
  .layer-row{grid-template-columns:1fr;gap:12px}.layer-row>div:not(.layer-id){padding-left:18px;border-left:1px solid var(--rule);}
  .runbook b{display:block;min-width:0}.runbook code{display:block;margin:2px 0 5px}.runbook p{display:block;margin:0;}
  .rule-grid,.quality-grid{grid-template-columns:1fr}.quality-grid{gap:24px}
}
@media (prefers-reduced-motion: reduce){ *{transition:none !important;} }
"""


def _standalone(title, desc, style, body):
    """Documento HTML completo p/ servir na web (o Artifact embrulha sozinho; a web não)."""
    svg = ("<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'>"
           "<circle cx='50' cy='50' r='44' fill='%23c1402a'/>"
           "<path d='M24 58h52M31 44h38M39 30h22' stroke='white' stroke-width='8'/></svg>")
    favicon = "data:image/svg+xml," + urllib.parse.quote(svg)
    return (
        "<!doctype html>\n<html lang=\"pt-BR\">\n<head>\n"
        "<meta charset=\"utf-8\">\n"
        "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">\n"
        f"<title>{title}</title>\n"
        f"<meta name=\"description\" content=\"{desc}\">\n"
        f"<meta property=\"og:title\" content=\"{title}\">\n"
        f"<meta property=\"og:description\" content=\"{desc}\">\n"
        "<meta property=\"og:type\" content=\"website\">\n"
        "<meta name=\"color-scheme\" content=\"light dark\">\n"
        f"<link rel=\"icon\" href=\"{favicon}\">\n"
        f"{style}\n</head>\n<body>\n{body}\n</body>\n</html>\n"
    )


def _nav(current: str, analysis_href: str = "index.html") -> str:
    marker = f'data-page="{current}"'
    nav = SITE_NAV.replace(marker, f'{marker} aria-current="page"')
    return nav.replace('href="index.html"', f'href="{analysis_href}"')


def main():
    nested = load_nested()
    data_json = json.dumps(nested, ensure_ascii=False, separators=(",", ":"))
    content = HTML.replace("__DATA__", data_json)
    aprov_by_stage = {
        stage: _latest_common(nested, "taxa_aprovacao", stage)
        for stage in ("ef_anos_iniciais", "ef_anos_finais", "em")
    }
    tdi_by_stage = {
        stage: _latest_common(nested, "distorcao_idade_serie", stage)
        for stage in ("ef_anos_iniciais", "ef_anos_finais", "em")
    }
    aprov_year, aprov = aprov_by_stage["em"]
    tdi_year, _ = tdi_by_stage["em"]

    def gap(values):
        return _percent(values["brasil"] - values["santa_maria"])

    aprov_ai = aprov_by_stage["ef_anos_iniciais"][1]
    aprov_af = aprov_by_stage["ef_anos_finais"][1]
    tdi_ai = tdi_by_stage["ef_anos_iniciais"][1]
    tdi_af = tdi_by_stage["ef_anos_finais"][1]
    tdi_em = tdi_by_stage["em"][1]
    replacements = {
        "__APROV_YEAR__": str(aprov_year),
        "__APROV_SM__": _percent(aprov["santa_maria"]),
        "__APROV_RS__": _percent(aprov["rs"]),
        "__APROV_BR__": _percent(aprov["brasil"]),
        "__APROV_GAP_AI__": gap(aprov_ai),
        "__APROV_GAP_AF__": gap(aprov_af),
        "__APROV_GAP_EM__": gap(aprov),
        "__TDI_YEAR__": str(tdi_year),
        "__TDI_AI_SM__": _percent(tdi_ai["santa_maria"]),
        "__TDI_AI_BR__": _percent(tdi_ai["brasil"]),
        "__TDI_AF_SM__": _percent(tdi_af["santa_maria"]),
        "__TDI_AF_BR__": _percent(tdi_af["brasil"]),
        "__TDI_EM_SM__": _percent(tdi_em["santa_maria"]),
        "__TDI_EM_BR__": _percent(tdi_em["brasil"]),
    }
    for marker, value in replacements.items():
        content = content.replace(marker, value)
    body = _nav("analise") + content
    artifact_body = _nav("analise", "dashboard.html") + content
    arch_body = _nav("arquitetura") + ARCH_HTML
    arch_artifact_body = _nav("arquitetura", "dashboard.html") + ARCH_HTML.replace(
        'href="index.html"', 'href="dashboard.html"'
    )
    style = f"<style>\n{CSS}\n</style>"
    title = "Observatório da Educação — Santa Maria/RS"
    desc = ("Vinte anos de dados do INEP mostram como a distância entre Santa Maria e as "
            "referências aumenta ao longo das etapas. IDEB, SAEB, aprovação e TDI.")
    arch_title = "Arquitetura e metodologia — Observatório da Educação"
    arch_desc = ("Arquitetura do pipeline: INEP, Base dos Dados, BigQuery, Parquet, dbt, "
                 "DuckDB, testes, proveniência e visualização.")

    # 1) versão Artifact (só conteúdo; o harness embrulha em <html>/<head>/<body>)
    OUT.write_text(f"<title>{title}</title>\n{style}\n{artifact_body}", encoding="utf-8")
    ARCH_OUT.write_text(f"<title>{arch_title}</title>\n{style}\n{arch_artifact_body}", encoding="utf-8")
    # 2) versão standalone p/ web/Railway (documento completo, com <head> e meta tags)
    PUB.parent.mkdir(parents=True, exist_ok=True)
    PUB.write_text(_standalone(title, desc, style, body), encoding="utf-8")
    ARCH_PUB.write_text(_standalone(arch_title, arch_desc, style, arch_body), encoding="utf-8")

    print(f"OK {OUT.relative_to(ROOT)} ({OUT.stat().st_size/1024:.1f} KB)")
    print(f"OK {PUB.relative_to(ROOT)} ({PUB.stat().st_size/1024:.1f} KB)")
    print(f"OK {ARCH_OUT.relative_to(ROOT)} ({ARCH_OUT.stat().st_size/1024:.1f} KB)")
    print(f"OK {ARCH_PUB.relative_to(ROOT)} ({ARCH_PUB.stat().st_size/1024:.1f} KB)")


if __name__ == "__main__":
    main()
