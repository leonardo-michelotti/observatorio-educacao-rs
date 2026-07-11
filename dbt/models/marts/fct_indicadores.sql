-- Fato tidy: uma linha por (indicador, nível geográfico, etapa, ano, valor).
-- Une IDEB + notas SAEB (Mat/Port) + taxa de aprovação + distorção idade-série nos 3 níveis.
with ideb_wide as (
    select nivel, ano, etapa, ideb, saeb_matematica, saeb_lingua_portuguesa
    from {{ ref('stg_ideb') }}
    where etapa is not null
),
-- unpivot: IDEB e seus dois componentes de proficiência viram indicadores próprios
ideb_tidy as (
    select nivel, ano, 'ideb'                   as indicador, etapa, ideb                   as valor from ideb_wide where ideb is not null
    union all
    select nivel, ano, 'saeb_matematica',       etapa, saeb_matematica       from ideb_wide where saeb_matematica is not null
    union all
    select nivel, ano, 'saeb_lingua_portuguesa', etapa, saeb_lingua_portuguesa from ideb_wide where saeb_lingua_portuguesa is not null
),
indicadores as (
    select nivel, ano, indicador, etapa, valor
    from {{ ref('stg_indicadores') }}
)
select nivel, ano, indicador, etapa, valor from ideb_tidy
union all
select nivel, ano, indicador, etapa, valor from indicadores
