#!/usr/bin/env python3
"""Dashboard — lê o fato tidy (DuckDB) e gera uma peça editorial de dados, autocontida.

Não é um "explorador de indicadores": é um artigo que conta um fio condutor — Santa Maria
começa forte no Ensino Fundamental e perde o passo conforme o aluno avança. Segue princípios
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


HTML = r"""<div class="paper">

  <header class="masthead">
    <p class="kicker">Observatório da educação básica · rede pública · Santa Maria / RS</p>
    <h1 class="headline">Santa Maria começa forte<br>e vai perdendo o passo</h1>
    <p class="standfirst">Nos anos iniciais, a cidade acompanha o Brasil e o Rio Grande do Sul.
      Aí o caminho encompridado revela suas rachaduras: o atraso se acumula, a aprendizagem
      leva um baque que a aprovação disfarça, e o Ensino Médio vira um abismo. Vinte anos de
      dados oficiais do INEP, lidos de ponta a ponta.</p>
    <button id="theme" class="theme-btn" type="button" aria-label="Alternar tema">tema</button>
    <nav class="section-nav" aria-label="Seções do painel">
      <a href="#analise">Análise</a>
      <a href="#explorador">Explorador</a>
      <a href="#metodologia">Arquitetura e metodologia</a>
    </nav>
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
    <p class="hero-caption">A curva do Brasil também cai; o gargalo do Ensino Médio é nacional.
      Mas a de Santa Maria <b>despenca</b>: um 5,8 de primeiro da turma nos anos iniciais vira um
      <b>2,4</b> no Médio, quando a média nacional ainda segura 4,1.</p>
  </section>

  <div class="rule"></div>

  <!-- ATO 1 -->
  <article class="act">
    <div class="act-txt">
      <p class="act-num">Anos iniciais</p>
      <h2>A base é sólida e melhorou muito.</h2>
      <p>Entre 2005 e 2023, o IDEB dos anos iniciais de Santa Maria saltou de 4,3 para
        <b>5,8</b>. Hoje empata com o Rio Grande do Sul e passa o Brasil. É a parte da história
        em que a cidade tem do que se orgulhar.</p>
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
      <p class="act-num">O gargalo</p>
      <h2>No Ensino Médio, o fluxo colapsa.</h2>
      <p>A aprovação que era exemplar no Fundamental (~97%) despenca no Médio: <b>78%</b> em
        Santa Maria contra <b>95%</b> no Brasil. É o retrato do IDEB de EM da cidade caindo de
        3,1 (2019) para 2,4 (2023). O Médio é rede estadual, não municipal, o que aponta para
        <i>onde</i> está o problema.</p>
    </div>
    <figure class="fig" data-chart data-ind="taxa_aprovacao" data-eta="em"
      data-ann='[{"niv":"santa_maria","ano":2022,"text":"78%, abaixo de todas as referências","ty":72,"tano":2018},{"niv":"brasil","ano":2025,"text":"Brasil: 95%","ty":90,"tano":2021}]'></figure>
  </article>

  <!-- ATO 4 -->
  <article class="act">
    <div class="act-txt">
      <p class="act-num">O atraso que acumula</p>
      <h2>Quanto mais longe no caminho, mais alunos ficam para trás.</h2>
      <p>Distorção idade-série é a fatia de alunos mais velhos que o esperado para a série. Nos
        anos finais, Santa Maria tem <b>mais</b> atraso (19,8%) que o Brasil (14,4%) e o reduziu
        mais tarde. A base larga bem; o percurso é que emperra.</p>
    </div>
    <figure class="fig" data-chart data-ind="distorcao_idade_serie" data-eta="ef_anos_finais"
      data-ann='[{"niv":"santa_maria","ano":2024,"text":"19,8%, acima do Brasil","ty":24,"tano":2019}]'></figure>
  </article>

  <div class="rule"></div>

  <!-- EXPLORADOR -->
  <section class="explore" id="explorador">
    <p class="act-num">Explore você mesmo</p>
    <h2>Todos os indicadores, todas as etapas.</h2>
    <p class="explore-lede">Escolha o indicador e a etapa. Santa Maria em destaque; Brasil (cinza
      cheio) e RS (cinza tracejado) como referência. Passe o mouse para os valores.</p>
    <div class="controls">
      <div class="ctl"><span class="ctl-lbl">Indicador</span><div id="ind-pills" class="pills" role="tablist"></div></div>
      <div class="ctl"><span class="ctl-lbl">Etapa</span><div id="eta-pills" class="pills" role="tablist"></div></div>
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

  <div class="rule"></div>

  <section class="method" id="metodologia">
    <p class="act-num">Por trás do painel</p>
    <h2>Arquitetura e metodologia</h2>
    <p class="method-lede">Este painel é a última camada de um pipeline reproduzível. O dado
      público do INEP chega pela Base dos Dados no BigQuery, passa por tratamento e testes e só
      então vira análise visual.</p>

    <div class="pipeline" aria-label="Fluxo do pipeline de dados">
      <div><span>Fonte</span><b>INEP via Base dos Dados</b><small>consultas no BigQuery</small></div>
      <div><span>Bronze</span><b>Parquet local</b><small>extração preservada</small></div>
      <div><span>Silver e gold</span><b>dbt e DuckDB</b><small>limpeza, modelo e testes</small></div>
      <div><span>Visualização</span><b>HTML e gráficos</b><small>painel editorial</small></div>
    </div>

    <div class="method-block">
      <h3>Como os dados chegam</h3>
      <p>As tabelas harmonizadas da Base dos Dados dão acesso, pelo BigQuery, aos indicadores
        publicados pelo INEP. A ingestão em Python consulta os recortes de Santa Maria, Rio
        Grande do Sul e Brasil e grava arquivos Parquet na camada bronze. Essa cópia mantém a
        extração separada das decisões analíticas e permite repetir as etapas seguintes sem
        consultar a origem a cada execução.</p>
    </div>

    <div class="method-block">
      <h3>Como o pipeline é construído</h3>
      <p>O projeto segue a arquitetura medalhão. A bronze guarda o dado extraído. Na silver, os
        modelos de staging do dbt padronizam nomes, tipos e recortes e aplicam a curadoria. Na
        gold, <code>fct_indicadores</code> reúne uma linha por indicador, nível, etapa, ano e
        valor. O DuckDB executa os modelos localmente. Depois, o pipeline gera os gráficos e
        este HTML autocontido.</p>
      <p><code>run_pipeline.py</code> encadeia ingestão, <code>dbt build</code>, gráficos e painel.
        As etapas são idempotentes: uma nova execução recompõe os produtos a partir das mesmas
        regras. Código, modelos dbt, testes, documentação e saídas visuais são versionados no
        Git, o que deixa cada mudança rastreável.</p>
    </div>

    <div class="method-block">
      <h3>Regras de cálculo e curadoria</h3>
      <ul>
        <li><b>IDEB:</b> combina proficiência no SAEB e rendimento escolar. Por isso o painel
          mostra as notas de Matemática e Língua Portuguesa separadas da aprovação.</li>
        <li><b>Aprovação:</b> valores fora do intervalo de 40% a 100% são descartados. O filtro
          retira pontos incompatíveis com uma taxa válida.</li>
        <li><b>Distorção idade-série:</b> aparece apenas nos anos finais do Ensino Fundamental,
          único recorte que permaneceu consistente na auditoria célula a célula.</li>
        <li><b>Regra das séries:</b> uma etapa entra no gráfico quando pelo menos dois níveis têm
          cinco ou mais anos válidos. Apenas as séries que atendem ao critério são desenhadas.</li>
      </ul>
    </div>

    <p class="method-note">A auditoria encontrou valores corrompidos na camada harmonizada da
      Base dos Dados, não na publicação oficial do INEP. A integração direta dos arquivos
      públicos do instituto é uma evolução planejada. Até lá, o painel mantém a fonte
      harmonizada com filtros explícitos, exclusões documentadas e testes versionados.</p>
  </section>

  <footer class="foot">
    <div class="foot-notes">
      <p class="foot-h">Como estes números foram tratados</p>
      <p>Os dados vêm do INEP via Base dos Dados, e foram auditados célula a célula. A tabela de
        indicadores da Base dos Dados tem colunas corrompidas na harmonização. A aprovação de EM
        do RS, por exemplo, aparece entre 4% e 11% em <i>todas</i> as fatias de rede, o que é
        impossível. A publicação oficial do INEP é pública e consistente; a integração direta
        desses arquivos é uma evolução planejada. Por enquanto, usamos a Base dos Dados com
        curadoria explícita: a distorção idade-série só aparece nos anos finais, única série que
        sobreviveu à auditoria, e o RS fica fora dos recortes frágeis.</p>
    </div>
    <div class="foot-meta">
      <span>Fonte: INEP · <code>br_inep_ideb</code>, <code>br_inep_indicadores_educacionais</code></span>
      <span>Santa Maria/RS · IBGE <code>4316907</code></span>
      <span>Rede pública · 2005–2025 · projeto de portfólio de dados</span>
    </div>
  </footer>
</div>

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

const NS = "http://www.w3.org/2000/svg";
const fmt = n => n.toLocaleString("pt-BR",{minimumFractionDigits:1,maximumFractionDigits:1});
const fmt0 = n => fmt(n).replace(",0","");
const el = (t,a) => { const e=document.createElementNS(NS,t); for(const k in a) e.setAttribute(k,a[k]); return e; };

function seriesFor(ind, eta){
  const d = (DATA[ind]||{})[eta] || {};
  return NIV_ORDER.filter(n => d[n] && d[n].length).map(n => ({niv:n, pts:d[n]}));
}
function etapasFor(ind){ return ETA_ORDER.filter(e => DATA[ind] && DATA[ind][e]); }
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
    b.dataset.ind=ind; b.setAttribute("role","tab");
    b.onclick=()=>{ state.ind=ind; if(!etapasFor(ind).includes(state.eta)) state.eta=etapasFor(ind)[0]; renderEx(); };
    ip.appendChild(b); });
}
function buildEtapa(){
  const ep=document.getElementById("eta-pills"); ep.innerHTML=""; const avail=etapasFor(state.ind);
  ETA_ORDER.forEach(eta=>{ const b=document.createElement("button"); b.className="pill"; b.type="button"; b.textContent=ETA[eta];
    b.dataset.eta=eta; b.setAttribute("role","tab"); b.disabled=!avail.includes(eta);
    if(avail.includes(eta)) b.onclick=()=>{state.eta=eta; renderEx();};
    ep.appendChild(b); });
}
function syncPills(){
  document.querySelectorAll("#ind-pills .pill").forEach(b=>b.setAttribute("aria-selected",b.dataset.ind===state.ind));
  document.querySelectorAll("#eta-pills .pill").forEach(b=>b.setAttribute("aria-selected",b.dataset.eta===state.eta));
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
  let h=`<table><thead><tr><th>Ano</th>${series.map(s=>`<th>${NIV[s.niv].label}</th>`).join("")}</tr></thead><tbody>`;
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
  document.getElementById("theme").onclick=()=>root.setAttribute("data-theme",cur()==="dark"?"light":"dark");
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
.section-nav{display:flex;flex-wrap:wrap;gap:8px 20px;margin-top:24px;font-family:var(--font-sans);font-size:12.5px;}
.section-nav a{color:var(--ink-2);text-decoration:none;border-bottom:1px solid var(--rule);}
.section-nav a:hover{color:var(--sm);border-color:var(--sm);}

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
.pill[aria-selected="true"]{color:var(--ink);border-bottom-color:var(--sm);font-weight:600;}
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
th,td{padding:6px 12px;text-align:right;border-bottom:1px solid var(--rule-2);font-variant-numeric:tabular-nums;}
th:first-child,td:first-child{text-align:left;color:var(--muted);}
thead th{color:var(--ink-2);border-bottom:1px solid var(--rule);}

/* architecture and methodology */
.method{scroll-margin-top:24px;}
.method h2{font-size:clamp(25px,3.8vw,34px);line-height:1.12;margin:0 0 12px;}
.method-lede{font-size:18px;color:var(--ink-2);line-height:1.55;margin:0 0 28px;}
.pipeline{display:grid;grid-template-columns:repeat(4,1fr);border-top:1px solid var(--rule);border-bottom:1px solid var(--rule);margin:0 0 34px;}
.pipeline div{padding:15px 12px 16px 0;position:relative;}
.pipeline div:not(:last-child)::after{content:"→";position:absolute;right:5px;top:37px;color:var(--muted);font-family:var(--font-sans);}
.pipeline span,.pipeline small{display:block;font-family:var(--font-sans);font-size:10.5px;color:var(--muted);line-height:1.35;}
.pipeline span{text-transform:uppercase;letter-spacing:.05em;margin-bottom:5px;}
.pipeline b{display:block;font-size:13px;line-height:1.3;margin-bottom:4px;padding-right:12px;}
.method-block{margin:28px 0;}
.method-block h3{font-size:20px;margin:0 0 8px;}
.method-block p,.method-block li{font-size:16px;color:var(--ink-2);line-height:1.55;}
.method-block p{margin:0 0 10px;}
.method-block ul{margin:8px 0 0;padding-left:20px;}
.method-block li{margin:8px 0;padding-left:3px;}
.method-block li b{color:var(--ink);}
.method-note{border-left:2px solid var(--sm);padding-left:14px;font-size:15px;color:var(--ink-2);line-height:1.5;margin:30px 0 0;}

/* footer */
.foot{margin-top:56px;padding-top:26px;border-top:2px solid var(--ink);}
.foot-h{font-family:var(--font-sans);font-size:12.5px;font-weight:700;letter-spacing:.02em;color:var(--ink);margin:0 0 8px;}
.foot-notes p{font-size:15px;color:var(--ink-2);line-height:1.5;margin:0;max-width:66ch;}
.foot-meta{display:flex;flex-direction:column;gap:3px;margin-top:22px;font-family:var(--font-sans);font-size:11.5px;color:var(--muted);}

@media (max-width:560px){ .paper{padding:44px 18px 56px;} body{font-size:17px;} .pipeline{grid-template-columns:1fr 1fr;} .pipeline div:nth-child(2)::after{display:none;} }
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


def main():
    nested = load_nested()
    data_json = json.dumps(nested, ensure_ascii=False, separators=(",", ":"))
    body = HTML.replace("__DATA__", data_json)
    style = f"<style>\n{CSS}\n</style>"
    title = "Observatório da Educação — Santa Maria/RS"
    desc = ("Vinte anos de dado do INEP: Santa Maria começa forte na educação básica e vai "
            "perdendo o passo. IDEB, SAEB, aprovação e distorção idade-série.")

    # 1) versão Artifact (só conteúdo; o harness embrulha em <html>/<head>/<body>)
    OUT.write_text(f"<title>{title}</title>\n{style}\n{body}", encoding="utf-8")
    # 2) versão standalone p/ web/Railway (documento completo, com <head> e meta tags)
    PUB.parent.mkdir(parents=True, exist_ok=True)
    PUB.write_text(_standalone(title, desc, style, body), encoding="utf-8")

    print(f"✔ {OUT.relative_to(ROOT)} ({OUT.stat().st_size/1024:.1f} KB)")
    print(f"✔ {PUB.relative_to(ROOT)} ({PUB.stat().st_size/1024:.1f} KB)")


if __name__ == "__main__":
    main()
