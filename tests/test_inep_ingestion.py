"""Contratos do parser das planilhas oficiais do Inep."""

import pandas as pd
import pytest

from ingestion.extract_inep import _parse_rows, _requested_years, validate_reference


def test_rendimento_escolhe_bloco_de_aprovacao_quando_etapas_se_repetem():
    rows = [
        ["metadado"] + [None] * 13,
        ["Ano", "UF", "Rede", "Localização", "Aprovação", None, None, "Reprovação"],
        [None, None, None, None, "Anos iniciais", "Anos finais", "Médio total", "Anos iniciais"],
        [2025, "Brasil", "Total", "Total", 98.3, 96.2, 94.8, 1.0],
        [2025, "RS", "Total", "Total", 96.9, 93.9, 91.9, 2.0],
    ]

    found = _parse_rows(rows, "rendimento", 2025, {"brasil", "rs"})

    assert found["brasil"]["taxa_aprovacao_em"] == 94.8
    assert found["rs"]["taxa_aprovacao_ef_anos_finais"] == 93.9


def test_tdi_identifica_santa_maria_pelo_codigo_ibge():
    rows = [
        ["Ano", "Município", "Nome", "Rede", "Localização", "Anos iniciais", "Anos finais", "Médio total"],
        [2025, 4316907, "Santa Maria", "Total", "Total", 6.7, 18.2, 20.9],
    ]

    found = _parse_rows(rows, "tdi", 2025, {"santa_maria"})

    assert found["santa_maria"] == {
        "tdi_ef_anos_iniciais": 6.7,
        "tdi_ef_anos_finais": 18.2,
        "tdi_em": 20.9,
    }


def test_referencia_2025_detecta_regressao_semantica():
    frame = pd.DataFrame(
        [
            {
                "ano": 2025,
                "nivel": nivel,
                **{
                    coluna: valor
                    for coluna, valor in {
                        "taxa_aprovacao_ef_anos_iniciais": aprovacao[0],
                        "taxa_aprovacao_ef_anos_finais": aprovacao[1],
                        "taxa_aprovacao_em": aprovacao[2],
                        "tdi_ef_anos_iniciais": tdi[0],
                        "tdi_ef_anos_finais": tdi[1],
                        "tdi_em": tdi[2],
                    }.items()
                },
            }
            for nivel, aprovacao, tdi in (
                ("brasil", (98.3, 96.2, 94.8), (6.6, 14.4, 16.0)),
                ("rs", (96.9, 93.9, 91.9), (7.0, 17.2, 18.0)),
                ("santa_maria", (96.5, 91.3, 88.1), (6.7, 18.2, 20.9)),
            )
        ]
    )
    validate_reference(frame)

    frame.loc[frame["nivel"] == "rs", "tdi_em"] = 99.0
    with pytest.raises(ValueError, match="Referência divergente"):
        validate_reference(frame)


def test_intervalo_de_anos_rejeita_limites_invalidos():
    assert list(_requested_years("2023:2025", 2007, 2025)) == [2023, 2024, 2025]
    with pytest.raises(ValueError, match="fora do intervalo"):
        _requested_years("2025:2023", 2007, 2025)
