# Como rodar

## Fontes e pré-requisitos

Taxas de aprovação e distorção idade-série são baixadas diretamente das planilhas públicas
do INEP e não exigem conta. O BigQuery é necessário apenas para IDEB e SAEB nesta fase.

### Acesso aos dados da Base dos Dados no BigQuery

Os dados vêm da [Base dos Dados](https://basedosdados.org/) (cópia tratada do INEP hospedada no
BigQuery). Consultar exige um projeto Google Cloud com faturamento configurado. O BigQuery
oferece uma franquia mensal de 1 TiB para consultas on-demand; uso excedente pode gerar cobrança.

1. Tenha um projeto no [Google Cloud Console](https://console.cloud.google.com/) e anote o
   **Project ID**. Consulte os [preços atuais](https://cloud.google.com/bigquery/pricing) e
   configure limites de custo.
2. Autentique as credenciais de aplicação (abre o navegador para login com seu Google):
   ```bash
   gcloud auth application-default login
   ```
3. Copie o `.env.example` para `.env` e preencha:
   ```bash
   cp .env.example .env
   # edite: BILLING_PROJECT_ID=seu-project-id
   ```

## Instalar

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Rodar o pipeline

```bash
source .venv/bin/activate
python run_pipeline.py
```

Isso executa: ingestão (BigQuery → `data/bronze/*.parquet`) → dbt (`dbt build`, silver/gold no
`data/educacao.duckdb`) → gráficos (`assets/*.png`). Tudo idempotente.

A ingestão primeiro obtém IDEB/SAEB pelo BigQuery e depois obtém os demais indicadores nas
planilhas oficiais do INEP.

### Rodar etapas isoladas

```bash
python ingestion/extract_bd.py                        # bronze
python ingestion/extract_inep.py --years 2025        # aprovação/TDI oficiais, um ano
python ingestion/extract_inep.py                      # aprovação/TDI, histórico completo
dbt build --project-dir dbt --profiles-dir dbt        # silver/gold + testes
python viz/make_charts.py                              # gráficos
```

## Rodar a validação offline

A mesma sequência da CI pode ser executada sem credenciais e sem consultar o BigQuery. Ela usa
dados sintéticos e sobrescreve temporariamente os arquivos em `data/`, `assets/`, `public/` e
`viz/`; por isso, prefira executá-la em um clone ou worktree separado.

```bash
pip install -r requirements-dev.txt
python -m ruff check ingestion viz tests run_pipeline.py
python tests/fixtures/make_bronze.py
dbt build --project-dir dbt --profiles-dir dbt
python viz/make_charts.py
python viz/build_dashboard.py
python -m pytest
```

Os ZIPs ficam em cache sob `data/raw/inep/`. Cada execução gera
`data/bronze/inep_provenance.json` com URL, SHA-256 e tamanho dos arquivos. Como o servidor do
INEP pode oscilar, o extrator repete downloads interrompidos e reaproveita ZIPs já validados.
