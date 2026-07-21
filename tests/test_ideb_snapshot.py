import json

from ingestion.load_ideb_snapshot import embedded_data, flow_snapshot_frame, snapshot_frame


def test_snapshot_reconstroi_formato_bronze(tmp_path):
    nested = {
        "ideb": {"ef_anos_iniciais": {"brasil": [[2023, 5.7]], "rs": [[2023, 5.8]], "santa_maria": [[2023, 5.8]]}},
        "saeb_matematica": {"ef_anos_iniciais": {"brasil": [[2023, 218.3]], "rs": [[2023, 222.1]], "santa_maria": [[2023, 221.5]]}},
        "saeb_lingua_portuguesa": {"ef_anos_iniciais": {"brasil": [[2023, 207.6]], "rs": [[2023, 212.9]], "santa_maria": [[2023, 214.8]]}},
    }
    panel = tmp_path / "index.html"
    panel.write_text(f"<script>const DATA = {json.dumps(nested)};</script>", encoding="utf-8")

    assert embedded_data(panel) == nested
    frame = snapshot_frame(panel)

    assert len(frame) == 3
    santa_maria = frame[frame["nivel"] == "santa_maria"].iloc[0]
    assert santa_maria["ensino"] == "fundamental"
    assert santa_maria["anos_escolares"] == "iniciais (1-5)"
    assert santa_maria["ideb"] == 5.8
    assert santa_maria["nota_saeb_matematica"] == 221.5


def test_snapshot_reconstroi_historico_de_aprovacao_e_tdi(tmp_path):
    nested = {
        "taxa_aprovacao": {
            "em": {level: [[2024, value]] for level, value in {
                "brasil": 94.0, "rs": 91.0, "santa_maria": 88.0
            }.items()}
        },
        "distorcao_idade_serie": {
            "em": {level: [[2024, value]] for level, value in {
                "brasil": 17.0, "rs": 19.0, "santa_maria": 21.0
            }.items()}
        },
    }
    panel = tmp_path / "index.html"
    panel.write_text(f"<script>const DATA = {json.dumps(nested)};</script>", encoding="utf-8")

    frame = flow_snapshot_frame(panel)

    santa_maria = frame[frame["nivel"] == "santa_maria"].iloc[0]
    assert santa_maria["taxa_aprovacao_em"] == 88.0
    assert santa_maria["tdi_em"] == 21.0
