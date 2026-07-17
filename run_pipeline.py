#!/usr/bin/env python3
"""Runner do pipeline Observatório da Educação RS.

Encadeia: ingestão (BigQuery/Base dos Dados -> Parquet bronze) -> dbt (silver/gold no DuckDB)
-> gráficos (PNG em assets/). Cada etapa é idempotente. dbt é sempre invocado da raiz do repo.
"""
import os
import subprocess
import sys
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env")


def run(cmd):
    print(f"\n$ {' '.join(cmd)}", flush=True)
    subprocess.run(cmd, check=True, cwd=ROOT)


def step_ingest():
    run([sys.executable, "ingestion/extract_bd.py"])


def step_dbt():
    # usa o dbt do mesmo ambiente que roda este script (ao lado do python),
    # pra não depender do venv estar ativado no PATH.
    dbt = Path(sys.executable).with_name("dbt")
    run([str(dbt), "build", "--project-dir", "dbt", "--profiles-dir", "dbt"])


def step_charts():
    run([sys.executable, "viz/make_charts.py"])


def step_dashboard():
    run([sys.executable, "viz/build_dashboard.py"])


def main():
    if not os.environ.get("BILLING_PROJECT_ID"):
        sys.exit("BILLING_PROJECT_ID não definido — configure o .env (veja docs/COMO_RODAR.md).")
    step_ingest()
    step_dbt()
    step_charts()
    step_dashboard()
    print("\nPipeline completo. Gráficos em assets/, painel em viz/dashboard.html, "
          "dados em data/educacao.duckdb.")


if __name__ == "__main__":
    main()
