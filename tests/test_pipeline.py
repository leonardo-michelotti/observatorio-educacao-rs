"""Testes de integração do pipeline construído com a fixture offline."""

import json
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "educacao.duckdb"


def _query(sql: str):
    with duckdb.connect(str(DB), read_only=True) as con:
        return con.execute(sql).fetchall()


def test_mart_expoe_o_contrato_esperado():
    indicadores = {row[0] for row in _query("select distinct indicador from fct_indicadores")}
    niveis = {row[0] for row in _query("select distinct nivel from fct_indicadores")}

    assert indicadores == {
        "ideb",
        "saeb_matematica",
        "saeb_lingua_portuguesa",
        "taxa_aprovacao",
        "distorcao_idade_serie",
    }
    assert niveis == {"brasil", "rs", "santa_maria"}


def test_indicadores_oficiais_mantem_todas_as_etapas_e_historico_rs():
    etapas = {
        row[0]
        for row in _query(
            """select distinct etapa from fct_indicadores
            where indicador = 'distorcao_idade_serie'"""
        )
    }
    tdi_rs_antiga = _query(
        """select count(*) from fct_indicadores
        where indicador = 'distorcao_idade_serie' and nivel = 'rs' and ano < 2023"""
    )[0][0]

    assert etapas == {"ef_anos_iniciais", "ef_anos_finais", "em"}
    assert tdi_rs_antiga > 0


def test_resultado_dbt_registra_modelos_e_testes_aprovados():
    resultado = json.loads((ROOT / "dbt" / "target" / "run_results.json").read_text())
    status = {item["status"] for item in resultado["results"]}
    testes = [item for item in resultado["results"] if item["unique_id"].startswith("test.")]

    assert status <= {"success", "pass"}
    assert len(testes) >= 10


def test_artefatos_publicaveis_foram_gerados():
    arquivos = [
        ROOT / "public" / "index.html",
        ROOT / "public" / "arquitetura.html",
        ROOT / "assets" / "ideb.png",
        ROOT / "assets" / "taxa_aprovacao.png",
        ROOT / "assets" / "distorcao_idade_serie.png",
    ]

    assert all(arquivo.exists() and arquivo.stat().st_size > 500 for arquivo in arquivos)
    painel = arquivos[0].read_text(encoding="utf-8")
    assert "const DATA =" in painel
    assert "__APROV_" not in painel and "__TDI_" not in painel
    assert "planilhas oficiais do INEP" in painel
    assert "A distância aumenta" in painel
    assert "fluxo colapsa" not in painel
    arquitetura = arquivos[1].read_text(encoding="utf-8")
    assert "Duas rotas de entrada" in arquitetura
    assert "não acompanha alunos" in arquitetura
    assert "Limite de leitura" in arquitetura
    assert arquivos[2].read_bytes().startswith(b"\x89PNG\r\n\x1a\n")
