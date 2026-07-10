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
    run(["dbt", "build", "--project-dir", "dbt", "--profiles-dir", "dbt"])


def step_charts():
    run([sys.executable, "viz/make_charts.py"])


def main():
    if not os.environ.get("BILLING_PROJECT_ID"):
        sys.exit("BILLING_PROJECT_ID não definido — configure o .env (veja docs/COMO_RODAR.md).")
    step_ingest()
    step_dbt()
    step_charts()
    print("\n✅ Pipeline completo. Gráficos em assets/, dados em data/educacao.duckdb.")


if __name__ == "__main__":
    main()
