#!/usr/bin/env python3
"""Reconstrói os bronzes analíticos a partir do snapshot versionado no painel.

O painel publicado embute o fato analítico em JSON. Enquanto IDEB/SAEB ainda dependem do
BigQuery, este carregador preserva o snapshot real já auditado e permite atualizar rendimento
e TDI diretamente do Inep sem introduzir a fixture sintética no produto publicado. O histórico
de fluxo também é restaurado para que a atualização oficial precise baixar apenas o ano novo.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PANEL = ROOT / "public" / "index.html"
OUTPUT = ROOT / "data" / "bronze" / "ideb.parquet"
FLOW_OUTPUT = ROOT / "data" / "bronze" / "indicadores.parquet"
INDICATORS = {
    "ideb": "ideb",
    "saeb_matematica": "nota_saeb_matematica",
    "saeb_lingua_portuguesa": "nota_saeb_lingua_portuguesa",
}
STAGES = {
    "ef_anos_iniciais": ("fundamental", "iniciais (1-5)"),
    "ef_anos_finais": ("fundamental", "finais (6-9)"),
    "em": ("medio", "todos"),
}
FLOW_INDICATORS = {
    "taxa_aprovacao": "taxa_aprovacao",
    "distorcao_idade_serie": "tdi",
}


def embedded_data(path: Path = PANEL) -> dict:
    html = path.read_text(encoding="utf-8")
    marker = "const DATA = "
    start = html.find(marker)
    if start < 0:
        raise ValueError(f"Snapshot DATA ausente em {path}")
    start += len(marker)
    end = html.find(";", start)
    if end < 0:
        raise ValueError(f"Fim do snapshot DATA ausente em {path}")
    return json.loads(html[start:end])


def snapshot_frame(path: Path = PANEL) -> pd.DataFrame:
    nested = embedded_data(path)
    records: dict[tuple[str, str, int], dict] = {}
    for indicator, column in INDICATORS.items():
        if indicator not in nested:
            raise ValueError(f"Indicador ausente no snapshot: {indicator}")
        for stage, levels in nested[indicator].items():
            if stage not in STAGES:
                continue
            ensino, anos_escolares = STAGES[stage]
            for level, series in levels.items():
                for year, value in series:
                    key = (level, stage, int(year))
                    row = records.setdefault(
                        key,
                        {
                            "nivel": level,
                            "ano": int(year),
                            "ensino": ensino,
                            "anos_escolares": anos_escolares,
                        },
                    )
                    row[column] = float(value)

    frame = pd.DataFrame(records.values())
    frame = frame[frame["ideb"].notna()].sort_values(
        ["ano", "nivel", "ensino", "anos_escolares"]
    )
    expected = {"brasil", "rs", "santa_maria"}
    if set(frame["nivel"]) != expected:
        raise ValueError(f"Níveis inesperados no snapshot: {sorted(frame['nivel'].unique())}")
    return frame.reset_index(drop=True)


def flow_snapshot_frame(path: Path = PANEL) -> pd.DataFrame:
    nested = embedded_data(path)
    records: dict[tuple[str, int], dict] = {}
    for indicator, prefix in FLOW_INDICATORS.items():
        if indicator not in nested:
            raise ValueError(f"Indicador ausente no snapshot: {indicator}")
        for stage, levels in nested[indicator].items():
            if stage not in STAGES:
                continue
            column = f"{prefix}_{stage}"
            for level, series in levels.items():
                for year, value in series:
                    key = (level, int(year))
                    row = records.setdefault(key, {"nivel": level, "ano": int(year)})
                    row[column] = float(value)

    frame = pd.DataFrame(records.values()).sort_values(["ano", "nivel"])
    expected = {"brasil", "rs", "santa_maria"}
    if set(frame["nivel"]) != expected:
        raise ValueError(f"Níveis inesperados no snapshot: {sorted(frame['nivel'].unique())}")
    return frame.reset_index(drop=True)


def main() -> None:
    ideb = snapshot_frame()
    flow = flow_snapshot_frame()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    ideb.to_parquet(OUTPUT, index=False)
    flow.to_parquet(FLOW_OUTPUT, index=False)
    print(f"Snapshot IDEB/SAEB: {len(ideb)} linhas em {OUTPUT}")
    print(f"Snapshot aprovação/TDI: {len(flow)} linhas em {FLOW_OUTPUT}")


if __name__ == "__main__":
    main()
