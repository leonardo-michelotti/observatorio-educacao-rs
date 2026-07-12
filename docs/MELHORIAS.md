# Investigação de melhorias — documento vivo

> Resumo inicial (v0) do que podemos melhorar no `observatorio-educacao-rs`. Cada frente
> tem: **o que investigar**, **como verificar** (a evidência que decide) e **prioridade**.
> Este arquivo cresce a cada rodada — marcar `[ ]`→`[x]` conforme investigamos/decidimos.

**Legenda de prioridade:** 🔥 alto impacto / baixo esforço · 🟡 alto impacto / esforço médio ·
🔵 estratégico / esforço maior · ⚪ nice-to-have

**Estado do projeto hoje (baseline):** pipeline v1 fechado — BigQuery → bronze (parquet) →
dbt-duckdb (`stg_*` + `fct_indicadores` + 8 testes) → matplotlib → vitrine no README.
Dados: IDEB EF (2005–2023) e taxa de aprovação (2007–2025) em 3 níveis (Santa Maria/RS/Brasil).

---

## Frente A — Cobertura de dados (o que dá pra medir)

- [ ] **A1 · Sua escola (nível escola).** 🔥 `br_inep_ideb.escola` traz IDEB, taxa de
  aprovação **e notas SAEB de Matemática/Português** por escola. Adiciona um 4º nível
  (escola vs município vs RS vs Brasil) e uma dimensão nova (SAEB por disciplina).
  - *Investigar:* qual escola (nome → código INEP via diretório); a série dela é longa o bastante?
  - *Verificar:* `SELECT ano, ideb, nota_saeb_matematica, nota_saeb_lingua_portuguesa FROM br_inep_ideb.escola WHERE id_escola = ?`
- [x] **A2 · Notas SAEB (Mat/Port) nos níveis atuais.** 🔥 ✅ **INVESTIGADO (viável).** Mat/Port
  por município/RS/Brasil, rede pública, EF iniciais+finais, série **2005–2023 completa** (9–10
  pontos/nível). EM continua esburacado (só 2 pontos em Santa Maria — mesma limitação do IDEB).
  - **Achado (ver "Achados" abaixo):** revela o baque da pandemia que a aprovação mascara.
  - *Fonte confirmada:* `nota_saeb_matematica` / `nota_saeb_lingua_portuguesa` em `br_inep_ideb.{brasil,uf,municipio}`.
- [~] **A3 · Municípios pares, não só RS/Brasil.** 🟡 ✅ **VIÁVEL** — `br_inep_censo_escolar`
  tem tabela `matricula` (além de `escola`, `docente`, `turma`) pra dimensionar porte e achar
  pares. Seleção dos pares fica para a implementação. Comparar Santa Maria com municípios de
  porte semelhante (ex.: Pelotas, Passo Fundo, Rio Grande) é mais honesto que só o agregado.
- [ ] **A4 · Matrículas / Censo Escolar.** 🟡 Volume (matrículas por etapa/rede/ano) dá
  contexto de tamanho e permite per-capita. Fonte: `br_inep_censo_escolar`.
- [ ] **A5 · Recorte por rede.** 🔵 Hoje IDEB usa `rede='publica'` agregada. Separar
  municipal × estadual × federal (e privada como contraste) explica muito do EM ruim.
- [ ] **A6 · Reprovação / abandono.** ⚪ Complemento natural da aprovação (o fluxo escolar completo).

## Frente B — Qualidade e confiabilidade

- [x] **B1 · Reabrir a distorção idade-série (TDI).** 🟡 ✅ **INVESTIGADO E IMPLEMENTADO
  (resgate estreito).** Auditoria célula a célula mostrou corrupção IRREGULAR na fonte:
  RS quebrado até 2022; **Santa Maria quebrada nos anos INICIAIS pós-2020** (6,5% em 2022 →
  23,5% em 2023, impossível); **Ensino Médio corrompido para todos** (até Brasil salta
  44→55→63). A **única série que passa na auditoria é EF anos finais** (SM e Brasil suaves;
  RS confiável só ≥2023). → indicador recolocado na vitrine **restrito a EF anos finais,
  Santa Maria vs Brasil**, com a curadoria documentada no `stg_indicadores.sql`. A avaliação
  inicial ("só o RS quebrado") estava otimista — a corrupção é mais espalhada.
- [ ] **B2 · Mais testes dbt.** 🔥 Hoje só `not_null`/`accepted_values`. Adicionar:
  faixas (`ideb` em [0,10], aprovação em [0,100]), `relationships`, e teste de que cada
  `(indicador,nivel,etapa)` tem série mínima esperada.
- [ ] **B3 · Evidência reproduzível de cada exclusão.** 🟡 Transformar as notas de qualidade
  em queries versionadas (`analyses/` do dbt ou um `docs/QUALIDADE.md`) que qualquer um roda
  e vê o dado corrompido — hoje é texto no README, sem prova ao lado.
- [ ] **B4 · Freshness / proveniência.** ⚪ Registrar data de extração e versão da tabela BD.

## Frente C — Engenharia do pipeline

- [ ] **C1 · CI no GitHub Actions.** 🔥 Rodar `dbt build` (com os testes) num workflow — hoje
  a qualidade só é garantida na máquina do dev. Sem tocar em auth (usar dado bronze fixture ou
  secret do GCP).
- [ ] **C2 · "README vivo" agendado.** 🟡 Actions cron → roda pipeline → regenera PNGs →
  commita. Já está desenhado no `PESQUISA_FONTES.md`, nunca implementado.
- [ ] **C3 · Ingestão do microdado cru do INEP.** 🔵 A tese do projeto ("provar engenharia")
  pede ingerir o zip do Censo Escolar, não só a Base dos Dados harmonizada. Alto esforço.
- [ ] **C4 · Orquestração (Dagster) / ingestão com dlt.** 🔵 Roadmap do research. Troca o
  `run_pipeline.py` (subprocess) por assets. Faz sentido só quando houver +fontes.
- [ ] **C5 · Modelagem dimensional explícita.** 🟡 Hoje é um fato único. Com escola/rede/
  disciplina entrando, vale `dim_local`, `dim_indicador` e staging por fonte.

## Frente D — Visualização e dashboard

- [x] **D1 · Dashboard interativo.** 🔥 ✅ **FEITO.** `viz/build_dashboard.py` (DuckDB → HTML
  autocontido) gera `viz/dashboard.html`: filtros por indicador/etapa, série temporal SM/RS/Brasil
  com crosshair+tooltip, rótulos diretos, visão de tabela, tema claro/escuro. Paleta categórica
  revalidada (light + dark próprios) e renderização conferida por screenshot nos dois temas.
  Plugado no `run_pipeline.py` como 4ª etapa. Publicado como Artifact.
  - **v2 (redesign editorial):** a v1 tinha "cara de IA" (cards+sombra, eyebrow mono, explorador
    neutro). Refeito como **peça de data-journalism**: narrativa "começa forte e perde o passo",
    cor como atenção seletiva (Santa Maria em destaque, RS/Brasil em cinza), anotações direto nas
    linhas, hero = a queda 5,8→4,6→2,4 vs Brasil segurando, tipografia serif, sem cards. O
    explorador virou seção secundária. Conferido nos dois temas por screenshot.
- [ ] **D2 · Perfil da escola.** 🔥 Depende de A1: painel do seu colégio (IDEB no tempo,
  SAEB Mat vs Port, ranking dentro de Santa Maria).
- [ ] **D3 · Gráficos novos.** 🟡 Ranking de escolas de Santa Maria; gap vs meta INEP;
  decomposição IDEB = proficiência × rendimento; small multiples por etapa.
- [ ] **D4 · Versão dark/light no README.** ⚪ `<picture>` + `prefers-color-scheme` (research §3).

## Frente E — Narrativa e documentação

- [x] **E1 · Revisar o README de apresentação.** 🔥 ✅ **FEITO.** README reescrito: abre com os
  3 achados (vale da pandemia, distorção pior que Brasil, EM como gargalo); integra os gráficos
  novos (SAEB Mat/Port, distorção); tabela de aprovação ganhou a linha de EM; notas de qualidade
  reescritas (bug da BD, curadoria da distorção, EM). Badge de testes 11/11.
- [ ] **E2 · Diagrama de arquitetura "de verdade".** 🟡 Hoje só o mermaid inline. Um diagrama
  visual (SVG/HTML, export PNG) como asset do repo.
- [ ] **E3 · Página de metodologia.** ⚪ Consolidar recorte + decisões de qualidade num doc só.

---

## Achados da investigação

> Evidências coletadas ao investigar as frentes acima. Cada achado vira insumo de narrativa (E1)
> e/ou de dashboard (D).

- **AF-1 · O baque da pandemia que a aprovação mascara (via A2).** A proficiência SAEB caiu
  forte de 2019→2021 e recuperou parcial em 2023, nos 3 níveis. Ex. Santa Maria, EF anos
  iniciais: Mat 224,8→210,2→221,5 · Port 216,4→206,1→214,8 (queda ~15 pts, recuperação quase
  total). No mesmo período a **taxa de aprovação subiu** — aprovou-se mais com menos
  aprendizagem. Como o IDEB pesa proficiência × rendimento, ele **suaviza** essa perda; separar
  os dois componentes conta a história real. → alimenta E1 e D3 (decomposição do IDEB).
- **AF-2 · Pico de Santa Maria nos anos finais em 2019 (via A2).** SAEB 2019 EF finais:
  Mat 266,8 / Port 269,5 — **acima de RS e Brasil**. Reforça a leitura de que o gargalo local
  é o Ensino Médio, não o Fundamental.
- **AF-3 · A distorção idade-série só é resgatável em EF anos finais (via B1) — CORRIGIDO.**
  A corrupção na fonte é irregular: RS quebrado até 2022, Santa Maria quebrada nos anos
  iniciais pós-2020, EM corrompido para todos. Sobra **uma** série auditável: EF anos finais,
  Santa Maria vs Brasil. Nela o achado é honesto e **não lisonjeiro**: a distorção de Santa
  Maria (19,8% em 2024) é **mais alta que a do Brasil (14,4%)** e caiu mais tarde. Vira um bom
  exemplo de curadoria célula a célula — e de humildade analítica (a leitura inicial de que
  "só o RS estava quebrado" estava errada; a auditoria completa corrigiu).
- **AF-4 · SAEB implementado no pipeline (Rodada 2).** IDEB decomposto em proficiência
  (`saeb_matematica`, `saeb_lingua_portuguesa`) + rendimento (`taxa_aprovacao`), tudo tidy no
  `fct_indicadores` e testado. Gera `assets/saeb_matematica.png` e `saeb_lingua_portuguesa.png`.
- **AF-5 · Efeito colateral virou achado: EM de aprovação (via mudança de filtro na viz).**
  Ao trocar a regra de renderização de "3 níveis sólidos" para "≥2 níveis sólidos" (necessária
  para o gráfico de distorção SM vs Brasil), a etapa **Ensino Médio passou a renderizar no
  `taxa_aprovacao`** como Santa Maria vs Brasil (o RS, corrompido, cai sozinho). O dado é
  limpo (Brasil 74→94,8%; SM 64→78,2%) e o achado é forte: a aprovação de EM de Santa Maria
  (~78%) fica **muito abaixo do Brasil (~95%)** — coerente com o IDEB de EM baixo (2,4).
  ✅ **Resolvido na E1:** README passou a mostrar a linha de EM na tabela de aprovação e a nota
  de qualidade foi reescrita ("EM entra só onde o dado aguenta").

- **AF-6 · A corrupção é da Base dos Dados, não do INEP (investigação de fonte).** Auditoria
  das fatias rede×localização na tabela crua `br_inep_indicadores_educacionais.uf` mostrou que
  a coluna quebrada está errada em **todas** as fatias (RS, aprovação de EM 2019: Estadual 4,6%
  · Pública 6,5% · Privada 11% · Total 7,2% — todas impossíveis). Não é célula isolada: é bug
  de harmonização da BD. **A fonte oficial do INEP (Taxas de Rendimento / Distorção Idade-Série,
  por município, 2006–2025) é limpa** — mas o servidor `download.inep.gov.br` (200.130.24.15) é
  **inacessível deste ambiente** (conexão falha; outros hosts respondem — provável geobloqueio a
  IP fora do Brasil). Caminhos avaliados: (a) calcular do microdado do Censo no BigQuery, (b)
  download manual do INEP, (c) manter curadoria. **Decisão: (c)** — manter a curadoria cirúrgica
  e tratar o bug da BD como limitação conhecida, documentada no README (E1). Reabrir se algum dia
  o dado do INEP for acessível.

## Sequência sugerida (a confirmar)

1. **Rodada 1 — enriquecer o dado:** A1 (escola) + A2 (SAEB) → é o que destrava dashboard e narrativa.
2. **Rodada 2 — dashboard:** D1 + D2 sobre o dado novo.
3. **Rodada 3 — robustez:** B2 (testes) + C1 (CI) + E1 (README).
4. **Rodada 4 — estratégico:** B1 (TDI), C2 (README vivo), o que sobrar.

## Perguntas em aberto

- Qual escola (A1/D2)? Nome + confirmação de que é em Santa Maria/RS.
- Dashboard: HTML autocontido, Evidence ou Streamlit? (D1)
- O projeto quer ir pro lado "engenharia pesada" (Dagster/dlt/microdado cru) ou "produto de
  dados" (dashboard rico + narrativa)? Isso define o peso entre as Frentes C e D.
