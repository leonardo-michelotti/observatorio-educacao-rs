#!/usr/bin/env python3
"""Gráficos — lê o fato tidy (DuckDB) e gera PNGs de série temporal em assets/.

Uma figura por indicador (IDEB, taxa de aprovação, distorção idade-série), com
3 subplots (etapas: EF anos iniciais/finais, EM) comparando Santa Maria, RS e Brasil.
Segue os princípios de dataviz: linhas finas, cor categórica por entidade em ordem
fixa, legenda + rótulos diretos, grid recessivo, superfície clara.
"""
from pathlib import Path

import duckdb
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FormatStrFormatter, MaxNLocator

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "data" / "educacao.duckdb"
ASSETS = ROOT / "assets"

# --- paleta / tokens (validados via dataviz/validate_palette.js) ---
SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK_2 = "#52514e"
MUTED = "#898781"
GRID = "#e1e0d9"
BASELINE = "#c3c2b7"

# nível -> (rótulo, cor categórica em ordem fixa: slot 1/2/3). Santa Maria é a protagonista.
NIVEIS = {
    "santa_maria": ("Santa Maria", "#2a78d6"),
    "rs": ("Rio Grande do Sul", "#1baf7a"),
    "brasil": ("Brasil", "#eda100"),
}
ETAPAS = {
    "ef_anos_iniciais": "EF · Anos iniciais",
    "ef_anos_finais": "EF · Anos finais",
    "em": "Ensino médio",
}
INDICADORES = {
    "ideb": ("IDEB", "IDEB (0–10)", "ideb"),
    "taxa_aprovacao": ("Taxa de aprovação", "% de aprovação", "taxa_aprovacao"),
}


def _style_ax(ax):
    ax.set_facecolor(SURFACE)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(BASELINE)
    ax.tick_params(colors=MUTED, labelsize=8, length=0)
    ax.grid(axis="y", color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    ax.xaxis.set_major_locator(MaxNLocator(integer=True, nbins=6))
    ax.xaxis.set_major_formatter(FormatStrFormatter("%d"))


def _load(con, indicador):
    rows = con.execute(
        """
        SELECT nivel, etapa, ano, valor
        FROM main.fct_indicadores
        WHERE indicador = ?
        ORDER BY nivel, etapa, ano
        """,
        [indicador],
    ).fetchall()
    data = {}
    for nivel, etapa, ano, valor in rows:
        data.setdefault(etapa, {}).setdefault(nivel, []).append((ano, valor))
    return data


def make_figure(con, indicador):
    titulo, unidade, _ = INDICADORES[indicador]
    data = _load(con, indicador)
    # só renderiza a etapa se os 3 níveis tiverem série mínima (>=5 anos). Evita
    # subplot capenga: no ensino médio a base é esburacada/corrompida para RS e
    # Santa Maria (EM é competência estadual, e a tabela de indicadores tem a série
    # EM do RS irreal), então EM cai fora e sobra o Ensino Fundamental, sólido.
    min_pontos = 5
    etapas = [e for e in ETAPAS
              if e in data and all(len(data[e].get(n, [])) >= min_pontos for n in NIVEIS)]

    fig, axes = plt.subplots(
        1, len(etapas), figsize=(4.6 * len(etapas), 3.9), sharey=True
    )
    if len(etapas) == 1:
        axes = [axes]
    fig.patch.set_facecolor(SURFACE)

    for ax, etapa in zip(axes, etapas):
        _style_ax(ax)
        ax.set_title(ETAPAS[etapa], color=INK, fontsize=10, fontweight="bold", pad=8)
        for nivel, (rotulo, cor) in NIVEIS.items():
            serie = sorted(data[etapa].get(nivel, []))
            if not serie:
                continue
            xs = [a for a, _ in serie]
            ys = [v for _, v in serie]
            ax.plot(xs, ys, color=cor, linewidth=2, marker="o", markersize=4,
                    markerfacecolor=cor, markeredgecolor=SURFACE, markeredgewidth=0.8,
                    label=rotulo, clip_on=False, zorder=3)
            # rótulo direto no fim da linha (regra de relevo p/ contraste)
            ax.annotate(f" {ys[-1]:.1f}", (xs[-1], ys[-1]), color=cor, fontsize=7.5,
                        va="center", fontweight="bold")
        ax.margins(x=0.08)

    axes[0].set_ylabel(unidade, color=INK_2, fontsize=9)
    fig.suptitle(f"{titulo} · Santa Maria vs RS vs Brasil", color=INK,
                 fontsize=13, fontweight="bold", x=0.01, ha="left", y=0.99)
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=3, frameon=False,
               fontsize=9, labelcolor=INK_2, bbox_to_anchor=(0.5, -0.02))
    fig.text(0.01, -0.02, "Fonte: INEP via Base dos Dados (BigQuery). Rede pública (IDEB) / total (demais).",
             color=MUTED, fontsize=7.5, ha="left")

    fig.tight_layout(rect=(0, 0.04, 1, 0.94))
    out = ASSETS / f"{indicador}.png"
    fig.savefig(out, dpi=150, bbox_inches="tight", facecolor=SURFACE)
    plt.close(fig)
    print(f"  ✔ {out.relative_to(ROOT)}")
    return out


def main():
    ASSETS.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(DB), read_only=True)
    try:
        print("Gerando gráficos:")
        for indicador in INDICADORES:
            make_figure(con, indicador)
    finally:
        con.close()
    print(f"\n✅ Gráficos em {ASSETS}.")


if __name__ == "__main__":
    main()
