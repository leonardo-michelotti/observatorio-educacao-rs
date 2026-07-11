#!/usr/bin/env python3
"""Ingestão — Base dos Dados (BigQuery) -> Parquet bronze.

Extrai 3 indicadores (IDEB, taxa de aprovação, distorção idade-série) em 3 níveis
geográficos (Brasil, RS, Santa Maria) e grava em data/bronze/*.parquet.

- Fonte IDEB:        basedosdados.br_inep_ideb.{brasil,uf,municipio}         (formato longo)
- Fonte indicadores: basedosdados.br_inep_indicadores_educacionais.{...}    (formato largo)

O recorte de rede é feito aqui (rede='publica' no IDEB; rede/localizacao='total' nos
indicadores), com normalização lower() porque a base mistura maiúsculas/minúsculas ao
longo dos anos. A tidificação (unpivot dos indicadores, união dos níveis) fica no dbt.
"""
import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from google.cloud import bigquery

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

BRONZE = ROOT / "data" / "bronze"
MUNICIPIO_SANTA_MARIA = "4316907"
UF = "RS"

# nível -> (tabela, filtro SQL adicional)
NIVEIS = {
    "brasil": ("brasil", ""),
    "rs": ("uf", f"AND sigla_uf = '{UF}'"),
    "santa_maria": ("municipio", f"AND id_municipio = '{MUNICIPIO_SANTA_MARIA}'"),
}

IDEB_COLS = (
    "ano, ensino, anos_escolares, ideb, taxa_aprovacao, indicador_rendimento, "
    # componentes de proficiência do IDEB — permitem decompor o índice (proficiência x
    # rendimento) e ver a perda de aprendizagem da pandemia. Ver docs/MELHORIAS.md (A2/AF-1).
    "nota_saeb_matematica, nota_saeb_lingua_portuguesa"
)
IND_COLS = (
    "ano, "
    "taxa_aprovacao_ef_anos_iniciais, taxa_aprovacao_ef_anos_finais, taxa_aprovacao_em, "
    "tdi_ef_anos_iniciais, tdi_ef_anos_finais, tdi_em"
)


def _client() -> bigquery.Client:
    proj = os.environ.get("BILLING_PROJECT_ID")
    if not proj:
        raise SystemExit("BILLING_PROJECT_ID não definido — configure o .env.")
    return bigquery.Client(project=proj)


def _extract(client: bigquery.Client, dataset: str, cols: str, where: str) -> pd.DataFrame:
    frames = []
    for nivel, (tabela, geo_filter) in NIVEIS.items():
        sql = f"""
            SELECT {cols}
            FROM `basedosdados.{dataset}.{tabela}`
            WHERE {where} {geo_filter}
        """
        df = client.query(sql).to_dataframe()
        df.insert(0, "nivel", nivel)
        frames.append(df)
        print(f"  {dataset}.{tabela:9s} nivel={nivel:11s} -> {len(df):4d} linhas")
    return pd.concat(frames, ignore_index=True)


def main() -> None:
    BRONZE.mkdir(parents=True, exist_ok=True)
    client = _client()

    print("IDEB:")
    ideb = _extract(client, "br_inep_ideb", IDEB_COLS, "lower(rede) = 'publica'")
    ideb.to_parquet(BRONZE / "ideb.parquet", index=False)

    print("Indicadores educacionais (aprovação; tdi bruto p/ referência):")
    ind = _extract(
        client,
        "br_inep_indicadores_educacionais",
        IND_COLS,
        "lower(rede) = 'total' AND lower(localizacao) = 'total'",
    )
    ind.to_parquet(BRONZE / "indicadores.parquet", index=False)

    print(f"\n✅ Bronze gravado em {BRONZE} "
          f"(ideb={len(ideb)} linhas, indicadores={len(ind)} linhas).")


if __name__ == "__main__":
    main()
