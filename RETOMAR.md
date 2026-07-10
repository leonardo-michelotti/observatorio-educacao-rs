# Retomar — estado da execução

**Status (10/07/2026): pipeline v1 concluído ✅** — a vitrine está no [`README.md`](README.md).

## O que está pronto (M0–M6)
- **M0 — auth GCP:** ✅ ADC via conta pessoal; projeto de billing `observatorio-educacao-502019`.
  `.env` aponta `GOOGLE_APPLICATION_CREDENTIALS` e `BILLING_PROJECT_ID`.
- **M1 — ambiente:** ✅ `.venv` completo; `dbt debug` verde.
- **M2 — ingestão:** ✅ `ingestion/extract_bd.py` (BigQuery → `data/bronze/*.parquet`).
- **M3 — transformação:** ✅ models dbt (`stg_ideb`, `stg_indicadores`, `fct_indicadores`) + 8 testes.
- **M4 — gráficos:** ✅ `viz/make_charts.py` → `assets/ideb.png`, `assets/taxa_aprovacao.png`.
- **M5/M6 — vitrine:** ✅ README com gráficos, tabelas-resumo e notas de qualidade.

Rodar tudo: `python run_pipeline.py` (ingest → dbt build → gráficos).

## Decisões travadas (não reabrir)
- Fonte: Base dos Dados no BigQuery (cliente `google-cloud-bigquery`).
- Recorte: Santa Maria `4316907` vs RS vs Brasil.
- **Indicadores v1:** IDEB (rede pública, EF) + taxa de aprovação (EF). **Distorção idade-série
  e Ensino Médio foram excluídos por qualidade de dados na origem** — detalhes no README.
- Escopo: até a vitrine no README; sem deploy/tornar público.

## Próximos passos possíveis (fora do escopo v1)
- Investigar fonte alternativa para distorção idade-série (a tabela de indicadores do RS é irreal).
- Painel interativo (Evidence/Streamlit) e agendamento (GitHub Actions) para README vivo.
