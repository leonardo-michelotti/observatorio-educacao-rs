# Como rodar

## Pré-requisito (1x): acesso aos dados da Base dos Dados no BigQuery

Os dados vêm da [Base dos Dados](https://basedosdados.org/) (cópia tratada do INEP hospedada no
BigQuery). Consultar exige um projeto Google Cloud **grátis** como "billing" (você tem 1 TB/mês de
consulta sem custo — este projeto usa uma fração disso).

1. Tenha um projeto no [Google Cloud Console](https://console.cloud.google.com/) (crie um, é grátis) e
   anote o **Project ID**.
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

### Rodar etapas isoladas

```bash
python ingestion/extract_bd.py                        # bronze
dbt build --project-dir dbt --profiles-dir dbt        # silver/gold + testes
python viz/make_charts.py                              # gráficos
```
