-- Indicadores (formato largo na origem) -> unpivot para formato longo (tidy).
-- Cura DUAS famílias de indicador: taxa de aprovação e distorção idade-série (TDI).
with src as (
    select * from read_parquet('data/bronze/indicadores.parquet')
),

-- 1) TAXA DE APROVAÇÃO -------------------------------------------------------
-- Filtro de validade: aprovação plausível fica em [40, 100]. Remove pontos corrompidos
-- isolados da fonte (ex.: RS 2023 = 6,0, onde as colunas vieram trocadas na origem).
aprovacao as (
    select nivel, ano, 'taxa_aprovacao' as indicador, 'ef_anos_iniciais' as etapa, taxa_aprovacao_ef_anos_iniciais as valor from src
    union all
    select nivel, ano, 'taxa_aprovacao', 'ef_anos_finais', taxa_aprovacao_ef_anos_finais from src
    union all
    select nivel, ano, 'taxa_aprovacao', 'em',             taxa_aprovacao_em             from src
),
aprovacao_valida as (
    select * from aprovacao where valor between 40 and 100
),

-- 2) DISTORÇÃO IDADE-SÉRIE (curadoria célula a célula) -----------------------
-- Antes excluída por inteiro. A auditoria (docs/MELHORIAS.md, AF-3) mostrou que a
-- corrupção na fonte é IRREGULAR entre séries — e que só UMA sobrevive:
--   * EF anos INICIAIS: Santa Maria corrompida pós-2020 (6,5% em 2022 -> 23,5% em 2023). ❌
--   * Ensino MÉDIO: corrompido para todos (até o Brasil salta 44->55->63). ❌
--   * EF anos FINAIS: Santa Maria e Brasil plausíveis e suaves; RS só confiável >=2023. ✅
-- Mantemos apenas a série que passa na auditoria (EF anos finais), curando ainda a
-- janela corrompida do RS. É curadoria transparente, não exclusão em bloco.
tdi as (
    select nivel, ano, 'distorcao_idade_serie' as indicador, 'ef_anos_finais' as etapa, tdi_ef_anos_finais as valor from src
),
tdi_curada as (
    select * from tdi
    where valor between 0 and 100
      and not (nivel = 'rs' and ano < 2023)   -- descarta a janela corrompida do RS
)

select nivel, ano, indicador, etapa, valor from aprovacao_valida
union all
select nivel, ano, indicador, etapa, valor from tdi_curada
