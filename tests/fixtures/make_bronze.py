"""Gera uma entrada bronze pequena e determinística para a CI offline.

Os valores são sintéticos. A fixture exercita os contratos e os geradores sem
consultar o BigQuery ou usar credenciais.
"""

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
BRONZE = ROOT / "data" / "bronze"

NIVEIS = ("brasil", "rs", "santa_maria")
ANOS_IDEB = (2005, 2011, 2017, 2019, 2021, 2023)
ANOS_INDICADORES = tuple(range(2018, 2025))


def _ideb_rows() -> list[dict]:
    rows = []
    offsets = {"brasil": 0.0, "rs": 0.2, "santa_maria": 0.3}
    for nivel in NIVEIS:
        for indice, ano in enumerate(ANOS_IDEB):
            ganho = indice * 0.18
            for etapa, anos_escolares, base in (
                ("fundamental", "iniciais (1-5)", 4.1),
                ("fundamental", "finais (6-9)", 3.7),
            ):
                valor = base + offsets[nivel] + ganho
                rows.append(
                    {
                        "nivel": nivel,
                        "ano": ano,
                        "ensino": etapa,
                        "anos_escolares": anos_escolares,
                        "ideb": round(valor, 1),
                        "nota_saeb_matematica": round(190 + valor * 12, 1),
                        "nota_saeb_lingua_portuguesa": round(185 + valor * 12, 1),
                    }
                )

    for nivel, anos in (("brasil", ANOS_IDEB), ("santa_maria", (2019, 2023))):
        for indice, ano in enumerate(anos):
            valor = 3.2 + indice * 0.15 + (0.1 if nivel == "santa_maria" else 0)
            rows.append(
                {
                    "nivel": nivel,
                    "ano": ano,
                    "ensino": "medio",
                    "anos_escolares": "todos",
                    "ideb": round(valor, 1),
                    "nota_saeb_matematica": round(225 + valor * 12, 1),
                    "nota_saeb_lingua_portuguesa": round(220 + valor * 12, 1),
                }
            )
    return rows


def _indicador_rows() -> list[dict]:
    rows = []
    offsets = {"brasil": 1.0, "rs": 0.0, "santa_maria": -1.0}
    for nivel in NIVEIS:
        for indice, ano in enumerate(ANOS_INDICADORES):
            aprovacao_em = 82 + offsets[nivel] + indice
            rows.append(
                {
                    "nivel": nivel,
                    "ano": ano,
                    "taxa_aprovacao_ef_anos_iniciais": 92 + offsets[nivel] + indice * 0.5,
                    "taxa_aprovacao_ef_anos_finais": 86 + offsets[nivel] + indice * 0.7,
                    "taxa_aprovacao_em": aprovacao_em,
                    "tdi_ef_anos_iniciais": 10 - indice * 0.5,
                    "tdi_ef_anos_finais": 25 - offsets[nivel] - indice,
                    "tdi_em": 30 - indice,
                }
            )
    return rows


def main() -> None:
    BRONZE.mkdir(parents=True, exist_ok=True)
    ideb = pd.DataFrame(_ideb_rows())
    indicadores = pd.DataFrame(_indicador_rows())
    ideb.to_parquet(BRONZE / "ideb.parquet", index=False)
    indicadores.to_parquet(BRONZE / "indicadores.parquet", index=False)
    print(f"Bronze sintético: ideb={len(ideb)} linhas, indicadores={len(indicadores)} linhas")


if __name__ == "__main__":
    main()
