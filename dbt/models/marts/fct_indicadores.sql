-- Fato tidy: uma linha por (indicador, nível geográfico, etapa, ano, valor).
-- Une IDEB + taxa de aprovação + distorção idade-série nos 3 níveis (Brasil, RS, Santa Maria).
with ideb as (
    select nivel, ano, 'ideb' as indicador, etapa, ideb as valor
    from {{ ref('stg_ideb') }}
    where etapa is not null
),
indicadores as (
    select nivel, ano, indicador, etapa, valor
    from {{ ref('stg_indicadores') }}
)
select nivel, ano, indicador, etapa, valor from ideb
union all
select nivel, ano, indicador, etapa, valor from indicadores
