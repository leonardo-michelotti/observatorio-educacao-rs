# Observatório da Educação: RS e Santa Maria

> Um produto de dados de ponta a ponta sobre a educação básica em **Santa Maria/RS**.
> Parte de dados públicos do INEP, organiza uma arquitetura medalhão local, aplica
> transformação e testes com dbt e entrega uma narrativa visual publicada na web.

![stack](https://img.shields.io/badge/stack-INEP%20%C2%B7%20BigQuery%20%C2%B7%20DuckDB%20%C2%B7%20dbt-blue)
[![CI](https://github.com/leonardo-michelotti/observatorio-educacao-rs/actions/workflows/ci.yml/badge.svg)](https://github.com/leonardo-michelotti/observatorio-educacao-rs/actions/workflows/ci.yml)

**[Abrir a análise](https://observatorio-educacao-rs-production.up.railway.app/)** ·
**[Ver arquitetura e metodologia](https://observatorio-educacao-rs-production.up.railway.app/arquitetura.html)**

O projeto responde como Santa Maria se compara ao Rio Grande do Sul e ao Brasil e como esse
quadro evolui no tempo. O escopo é pequeno de propósito: uma fonte principal, três níveis
geográficos e um contrato de dados simples. O resultado é um pipeline completo, auditável e
fácil de ampliar com novos indicadores e recortes.

### O que este projeto demonstra

- **Engenharia de dados:** ingestão direta das planilhas oficiais do INEP para rendimento e
  distorção, BigQuery apenas para IDEB/SAEB, bronze em Parquet, dbt e DuckDB.
- **Qualidade:** testes de schema, regras explícitas de validade, referências oficiais e
  proveniência verificável por hash.
- **Produto:** gráficos versionados, painel editorial responsivo e explorador com tabela
  alternativa.
- **Operação:** execução centralizada em um runner e deploy estático endurecido no Railway,
  sem credenciais ou dados brutos na imagem. A CI reconstrói e testa o pipeline com fixtures
  sintéticas; uma Action manual valida a ingestão real e preserva sua proveniência.
- **Evolução:** o fato tidy permite acrescentar indicadores semelhantes sem redesenhar todo o
  fluxo. Novas granularidades, como escola e rede administrativa, têm um caminho claro para
  dimensões próprias.

**Três achados que os dados contam:**
1. **A aprendizagem caiu no período da pandemia, mas o IDEB amorteceu o movimento.** Separando
   o índice em proficiência (SAEB) e rendimento (aprovação), vê-se que a proficiência caiu de
   2019 para 2021 enquanto a aprovação subiu.
2. **Santa Maria vai bem no Fundamental, mas patina no resto.** A distorção idade-série da
   cidade (18,2%) é maior que a do Brasil (14,4%) nos anos finais, comparando 2025.
3. **O Ensino Médio é o gargalo.** A aprovação de EM de Santa Maria (88,1%) fica abaixo
   do RS (91,9%) e do Brasil (94,8%) em 2025; o IDEB de EM caiu de 3,1 (2019) para 2,4 (2023).

---

## A vitrine

### IDEB — rede pública, Ensino Fundamental

![IDEB — Santa Maria vs RS vs Brasil](assets/ideb.png)

**IDEB 2023 (rede pública):**

| Etapa | Santa Maria | RS | Brasil |
|---|:-:|:-:|:-:|
| EF · Anos iniciais | **5,8** | 5,8 | 5,7 |
| EF · Anos finais | **4,6** | 4,7 | 4,7 |

Santa Maria acompanha de perto o estado e o país nos anos iniciais (empata com o RS,
acima do Brasil) e fica um décimo abaixo nos anos finais. A diferença entre as etapas também
aparece no RS e no Brasil, sem que o indicador isolado explique suas causas.

### SAEB — proficiência (o que compõe o IDEB)

O IDEB combina **proficiência padronizada a partir do SAEB** e **rendimento** (aprovação).
Separar os dois revela o que o índice suaviza: **a perda de aprendizagem da pandemia**.

![SAEB Matemática — Santa Maria vs RS vs Brasil](assets/saeb_matematica.png)
![SAEB Língua Portuguesa — Santa Maria vs RS vs Brasil](assets/saeb_lingua_portuguesa.png)

**Proficiência SAEB · Santa Maria, EF anos iniciais (o vale da pandemia):**

| Ano | Matemática | Português |
|---|:-:|:-:|
| 2019 | 224,8 | 216,4 |
| 2021 | 210,2 | 206,1 |
| 2023 | 221,5 | 214,8 |

A proficiência caiu cerca de 15 pontos de 2019 para 2021 e recuperou quase tudo em 2023. O mesmo
padrão aparece no RS e no Brasil. No **mesmo período a taxa de aprovação subiu**: mais alunos
foram aprovados apesar da queda na aprendizagem medida, e o IDEB, que combina os dois
componentes, amorteceu o movimento. Nos **anos finais de 2019**, Santa Maria ficou acima de RS
e Brasil: Matemática **266,8** e Português **269,5**.

### Taxa de aprovação — Ensino Fundamental e Médio

![Taxa de aprovação — Santa Maria vs RS vs Brasil](assets/taxa_aprovacao.png)

**Taxa de aprovação, comparação no mesmo ano:**

| Etapa | Santa Maria | RS | Brasil |
|---|:-:|:-:|:-:|
| EF · Anos iniciais (2025) | **96,5%** | 96,9% | 98,3% |
| EF · Anos finais (2025) | **91,3%** | 93,9% | 96,2% |
| Ensino médio (2025) | **88,1%** | 91,9% | 94,8% |

Em 2025, Santa Maria fica abaixo de RS e Brasil nas três etapas. A diferença é maior no
Ensino Médio: 88,1% na cidade, ante 91,9% no estado e 94,8% no país. O resultado é coerente
com o IDEB de EM da cidade (2,4 em 2023) e aponta a etapa onde ainda há mais a ganhar.

### Distorção idade-série — EF anos finais

![Distorção idade-série — Santa Maria vs RS vs Brasil](assets/distorcao_idade_serie.png)

Com a fonte oficial direta, as três etapas e os três níveis voltam à vitrine. Em 2025, nos
anos finais, Santa Maria registra **18,2%**, acima do RS (**17,2%**) e do Brasil (**14,4%**).
O Ensino Médio também permanece acima das referências: **20,9%** na cidade, 18,0% no estado e
16,0% no país. A base larga melhor; o atraso se acumula conforme o percurso avança.

---

## Arquitetura

```mermaid
flowchart LR
  INEP[INEP<br/>ZIP · XLS/XLSX] --> ING1[Parser oficial<br/>rendimento + TDI]
  BQ[Base dos Dados<br/>BigQuery] --> ING2[IDEB + SAEB]
  ING1 --> BRONZE[(Bronze<br/>Parquet + proveniência)]
  ING2 --> BRONZE
  BRONZE --> DBT[dbt-duckdb<br/>staging · marts + testes]
  DBT --> DUCK[(DuckDB<br/>educacao.duckdb)]
  DUCK --> CHARTS[matplotlib<br/>PNG em assets/]
  DUCK --> PAGES[HTML autocontido<br/>análise + arquitetura]
  CHARTS --> README[Vitrine no README]
  PAGES --> WEB[Railway<br/>Caddy estático]
```

| Camada | Ferramenta |
|---|---|
| Ingestão | Python: downloads oficiais do INEP para rendimento/TDI; [Base dos Dados](https://basedosdados.org/) no BigQuery para IDEB/SAEB |
| Lakehouse | [DuckDB](https://duckdb.org/) + Parquet (arquitetura medalhão: bronze → silver → gold) |
| Transformação | [dbt](https://www.getdbt.com/) (`dbt-duckdb`) com testes de schema |
| Visualização | [matplotlib](https://matplotlib.org/) → PNG versionados no repo |

O runner [`run_pipeline.py`](run_pipeline.py) encadeia ingestão, `dbt build`, geração dos
gráficos e construção das páginas.

> **Painel interativo.** Além dos PNGs da vitrine, o pipeline gera uma peça editorial de dados
> autocontida, com a narrativa "começa forte e perde o passo", gráficos anotados, hover, visão de
> tabela e tema claro/escuro. O mesmo gerador cria uma segunda página dedicada à arquitetura,
> metodologia e decisões de curadoria. Saídas de [`viz/build_dashboard.py`](viz/build_dashboard.py):
> [`viz/dashboard.html`](viz/dashboard.html) (abra localmente, pois o GitHub sanitiza JS) e
> [`viz/arquitetura.html`](viz/arquitetura.html), além de [`public/index.html`](public/index.html)
> e [`public/arquitetura.html`](public/arquitetura.html), prontos para a web.
>
> **No ar.** `Dockerfile` + `Caddyfile` (estático, endurecido) + `railway.toml` automatizam o
> deploy no [Railway](https://railway.app/) com HTTPS, sem incluir credenciais ou dados brutos
> na imagem. Passo a passo em [`docs/DEPLOY.md`](docs/DEPLOY.md).

### Escopo atual e caminho de evolução

Esta é uma arquitetura deliberadamente simples, adequada ao volume e à frequência atuais. Ela
está fechada como produto de portfólio: dados, transformação, testes, documentação, visualização
e deploy fazem parte do mesmo fluxo.

Para crescer dentro do recorte atual, um novo indicador passa por ingestão, staging, mart,
testes e registro na visualização. Se o projeto avançar para escolas, múltiplas redes, mais
fontes ou atualizações frequentes, a evolução natural inclui dimensões explícitas, ingestão
atômica, testes de contrato mais amplos e proveniência de cada extração.

## Recorte e metodologia

- **Níveis geográficos:** Santa Maria (`4316907`) · Rio Grande do Sul · Brasil.
- **Fonte:** planilhas oficiais do INEP para
  [taxa de aprovação](https://www.gov.br/inep/pt-br/acesso-a-informacao/dados-abertos/indicadores-educacionais/taxas-de-rendimento-escolar/)
  e [TDI](https://www.gov.br/inep/pt-br/acesso-a-informacao/dados-abertos/indicadores-educacionais/taxas-de-distorcao-idade-serie);
  IDEB/SAEB via
  `br_inep_ideb` da Base dos Dados no BigQuery.
- **Indicadores:** IDEB, **notas SAEB** (Matemática/Português), **taxa de aprovação** e
  **distorção idade-série** nas três etapas: anos iniciais, anos finais e Ensino Médio.
- **IDEB / SAEB:** rede **pública**, a única comparável nos três níveis no Ensino Fundamental.
- **Modelo tidy** (`fct_indicadores`): uma linha por `(indicador, nível, etapa, ano, valor)`,
  com **10 testes dbt**: oito testes de schema (`not_null`, `accepted_values`) e dois testes
  singulares para unicidade do grão e faixas físicas dos indicadores.
- **Regra dos gráficos:** cada etapa é renderizada se tiver **pelo menos 2 séries sólidas**
  (≥5 anos), plotando só as que passam. Por isso o IDEB de EM fica de fora (série curta) mas a
  distorção aparece como Santa Maria vs Brasil.

## Notas de qualidade de dados

O erro identificado estava na camada harmonizada, não nas publicações do INEP. Ele está
registrado na [issue #1430](https://github.com/basedosdados/pipelines/issues/1430), e o
[PR #1653](https://github.com/basedosdados/pipelines/pull/1653) propõe um teste contra novas
regressões. Para não depender da correção externa, este projeto agora baixa as planilhas
oficiais, seleciona semanticamente as colunas e grava URL, hash SHA-256 e tamanho de cada
arquivo em `data/bronze/inep_provenance.json`.

O parser cobre XLS e XLSX e valida valores de referência publicados para 2025. No dbt ficam
somente contratos físicos (`0 <= valor <= 100`): não há mais filtros criados para mascarar a
corrupção anterior. IDEB e SAEB continuam temporariamente via BigQuery; removê-lo por completo
é a próxima etapa isolada da migração.

## Como rodar

Pré-requisitos: Python 3.12+ e um projeto Google Cloud com a BigQuery API ativa e faturamento
configurado. O BigQuery oferece franquia mensal de 1 TiB para consultas sob o modelo on-demand;
uso excedente pode gerar cobrança. Consulte os [preços atuais](https://cloud.google.com/bigquery/pricing)
e configure limites de custo. Passo a passo detalhado em
[`docs/COMO_RODAR.md`](docs/COMO_RODAR.md).

Em Bash (Linux, macOS ou WSL):

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

gcloud auth application-default login          # autentica o ADC (abre o navegador)
cp .env.example .env                           # e preencha BILLING_PROJECT_ID

python run_pipeline.py                         # ingest → dbt build → gráficos → páginas
```

Em PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

gcloud auth application-default login
Copy-Item .env.example .env                    # preencha BILLING_PROJECT_ID

python run_pipeline.py
```

Ao final: dados em `data/educacao.duckdb`, gráficos em `assets/` e páginas em `public/`.

Para baixar somente os indicadores oficiais, sem Google Cloud:

```bash
python ingestion/extract_inep.py --years 2025       # teste rápido
python ingestion/extract_inep.py                    # histórico completo
```

### Integração contínua sem credenciais

O workflow [`ci.yml`](.github/workflows/ci.yml) roda em cada push e pull request. Ele cria um
bronze sintético determinístico, executa `dbt build`, gera os gráficos e as páginas, roda testes
de integração com pytest e preserva os artefatos por sete dias. A consulta real ao BigQuery não
faz parte da CI e continua protegida por credenciais locais.

O workflow manual [`refresh-inep.yml`](.github/workflows/refresh-inep.yml) exercita os downloads
reais, valida as referências oficiais, reconstrói o produto e publica Parquet, proveniência,
logs e páginas como artefatos por 14 dias. Quando as páginas mudam, o bot envia uma branch e
abre um PR; o merge desse PR aciona o deploy normal do Railway.

## Estrutura

```
ingestion/extract_bd.py   Base dos Dados (BigQuery) → Parquet bronze (IDEB + SAEB)
ingestion/extract_inep.py planilhas oficiais INEP → Parquet (aprovação + TDI + proveniência)
ingestion/load_ideb_snapshot.py  painel versionado → snapshot bronze de IDEB/SAEB
dbt/models/staging/       stg_ideb, stg_indicadores (limpeza + unpivot + curadoria)
dbt/models/marts/         fct_indicadores (fato tidy + testes)
viz/make_charts.py        DuckDB → PNGs em assets/ (vitrine do README)
viz/build_dashboard.py    DuckDB → páginas autocontidas de análise e arquitetura
run_pipeline.py           orquestra as quatro etapas
tests/                    fixtures e testes de integração offline
.github/workflows/ci.yml  lint, dbt build, geração e testes em push/PR
.github/workflows/refresh-inep.yml  validação manual com dados oficiais
docs/PESQUISA_FONTES.md   fontes públicas, proveniência e limites de uso
```

---

*Projeto pessoal de portfólio de dados. Fonte: INEP e Base dos Dados. Dados públicos de origem oficial.*
