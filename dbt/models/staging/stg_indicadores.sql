-- Indicadores (formato largo na origem) -> unpivot para formato longo.
--
-- Só a TAXA DE APROVAÇÃO é curada aqui. A DISTORÇÃO IDADE-SÉRIE (colunas tdi_*) foi
-- DELIBERADAMENTE EXCLUÍDA: na origem (Base dos Dados / br_inep_indicadores_educacionais)
-- a série do RS é irreal (~1,5% a década toda vs ~15% do Brasil) e os anos 2023-2024
-- estão corrompidos para RS e Santa Maria — inviável como comparação. Ver README.
--
-- Filtro de validade: aprovação plausível fica em [40, 100]. Isso remove pontos
-- corrompidos isolados (ex.: RS 2023 = 6,0, onde as colunas vieram trocadas na fonte).
with src as (
    select * from read_parquet('data/bronze/indicadores.parquet')
),
unpivotado as (
    select nivel, ano, 'ef_anos_iniciais' as etapa, taxa_aprovacao_ef_anos_iniciais as valor from src
    union all
    select nivel, ano, 'ef_anos_finais',   taxa_aprovacao_ef_anos_finais   from src
    union all
    select nivel, ano, 'em',               taxa_aprovacao_em               from src
)
select
    nivel,
    cast(ano as integer) as ano,
    'taxa_aprovacao'     as indicador,
    etapa,
    valor
from unpivotado
where valor between 40 and 100
