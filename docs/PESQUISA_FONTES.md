# Pesquisa — Stack e Fontes de Dados

Levantamento inicial (jul/2026) que fundamenta o projeto. Duas frentes: (1) que stack o
mercado usa em projetos de engenharia de dados de portfólio, (2) que dados públicos de
educação existem para RS e Santa Maria.

## 1. Stack de referência (modern data stack open-source, 2025/2026)

Convergência clara nos projetos de portfólio atuais:

```
dlt (ingestão) → DuckDB + Parquet (lakehouse) → dbt (transformação) → Dagster (orquestração) → gráficos/painel
```
Organizado em **arquitetura medalhão**: bronze (cru) → silver (limpo) → gold (pronto).

Tendências consolidadas:
- **DuckDB** ganhou para qualquer volume < 1 TB (dispensa Spark). É o "SQLite analítico".
- **`dlt`** ganhou da Airbyte quando só é preciso mover dado (biblioteca Python, não um servidor).
- **Orquestração**: Dagster (melhor DX para portfólio, modelo de *assets* casa com dbt),
  Airflow 3.0 (veterano, relançado abr/2025), Kestra (novato em alta).
- **Iceberg** desponta como formato de tabela do lake.

Projetos-referência que fazem exatamente este padrão (ingerir dado público de governo →
medalhão em DuckDB → dbt/Dagster):
- https://github.com/edwinweber/dbt_duckdb_demo_public (Danish Democracy Data)
- https://github.com/Retail-Shake/dagster-dbt-duckdb

## 2. Fontes de dados de educação

Espinha dorsal é **federal** (INEP); RS e Santa Maria entram como recorte e contexto.

### Nacional — o coração
- **INEP — microdados** · https://www.gov.br/inep/pt-br/acesso-a-informacao/dados-abertos/microdados
  - Censo Escolar (escolas, turmas, **matrículas**, docentes), IDEB, SAEB, ENEM, Censo Superior.
  - Download direto por ano, ex.: `https://download.inep.gov.br/dados_abertos/microdados_censo_escolar_2023.zip`
  - Recorte local: filtrar `CO_MUNICIPIO = 4316907` (Santa Maria) e `CO_UF = 43` (RS).
  - **É a fonte principal** — microdado real, série longa, milhões de linhas.
- **Base dos Dados** · https://basedosdados.org/dataset/dae21af4-4b6a-42f4-b94a-4c2061ea9de5
  - Mesmos dados do INEP/IBGE **já tratados e harmonizados** (colunas consistentes entre anos),
    consultáveis via SQL (BigQuery) ou Python/R/DuckDB. Resolve a dor do INEP cru (cada ano com
    colunas diferentes, 100 GB+). **Uso: atalho/validação** — a ingestão crua do INEP fica no
    projeto para demonstrar engenharia.
- **IBGE** (SIDRA / Cidades) — população para normalizar (matrícula per capita etc.).
- **Atlas do Desenvolvimento Humano** (PNUD/IPEA/FJP) · https://www.atlasbrasil.org.br/perfil/municipio/431690
  - IDHM Educação por município. **Base censo decenal (2000/2010) — desatualizado**; usar só
    como pano de fundo, não como série principal.

### Estadual — RS
- **dados.rs.gov.br** · https://dados.rs.gov.br/ — portal **CKAN com API**.
  - **✅ VALIDADO (jul/2026):** `GET /api/3/action/package_search?fq=groups:educacao` →
    `success: true`, **63 datasets** de educação, **todos em CSV**. Ex.: matrículas por
    sexo/cor/idade/zona de residência; turmas, docentes e estabelecimentos por rede
    (fundamental, médio, profissional, infantil, especial, EJA). Dado **agregado** do estado.
  - Contato: `dadosrs@procergs.rs.gov.br`.
- **DEE-SPGG** (VisualizaDEE) · https://visualiza.dee.rs.gov.br/ — inclui o **IMERS**
  (Índice Municipal da Educação do RS, atualizado anualmente por DEE + SEDUC). Diferencial
  local: indicador estadual próprio.
- **Atlas Socioeconômico RS** · https://atlassocioeconomico.rs.gov.br/ — séries do estado.

### Municipal — Santa Maria (leitura honesta)
- **Portal da Transparência de Santa Maria** · https://www.santamaria.rs.gov.br/transparencia
  — majoritariamente **fiscal** (receita/despesa/folha/compras); pouco indicador educacional.
- A rede municipal roda no sistema **EducarWeb** (fechado, sem dado aberto).
- **Conclusão:** o dado analítico rico de Santa Maria vem do **INEP filtrado por `4316907`** —
  é assim que o nacional "aterrissa" na cidade. O município publica pouco dado próprio.

## 3. Visualização — README como apresentação

O GitHub **sanitiza** o README (sem `<script>`, sem gráfico interativo em JS, imagens proxiadas).
O que funciona:
1. **Imagens PNG/SVG** geradas pelo pipeline, commitadas em `/assets`, referenciadas no README.
2. **Mermaid** (render nativo) — diagrama de arquitetura e gráficos simples (`xychart-beta`, `pie`).
3. **`<picture>` + `prefers-color-scheme`** — versão clara/escura do gráfico conforme o tema.
4. **Badges** (shields.io) para números-manchete.

**README vivo:** um **GitHub Actions agendado** roda o pipeline → regenera as imagens dos
gráficos → faz commit delas de volta. O README mostra sempre o dado mais recente, sozinho.

Duas camadas de viz:
- **README = vitrine** — 4-5 gráficos-chave + narrativa, auto-atualizados.
- **Painel interativo** (Evidence.dev / Streamlit, deploy) — camada profunda para explorar.

## 4. Próximos passos

- **Fase 0** (em curso): validar as âncoras baixando dado real — 1 zip do Censo Escolar
  (schema + tamanho), 1 tabela via Base dos Dados, confirmar recorte de Santa Maria/RS.
- **Fase 1**: escolher o recorte v1 (sugestão: IDEB + fluxo escolar, Santa Maria vs RS vs BR)
  e montar bronze → silver → gold.

## Códigos úteis

| Código | Valor |
|---|---|
| Município Santa Maria (IBGE) | `4316907` (Atlas usa `431690` sem dígito) |
| UF Rio Grande do Sul (INEP/IBGE) | `43` |
