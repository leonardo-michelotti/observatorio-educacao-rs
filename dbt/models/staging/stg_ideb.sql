-- IDEB (formato longo na origem): normaliza a etapa e mantém só o valor do IDEB.
with src as (
    select * from read_parquet('data/bronze/ideb.parquet')
)
select
    nivel,
    cast(ano as integer) as ano,
    case
        when ensino = 'fundamental' and anos_escolares like 'iniciais%' then 'ef_anos_iniciais'
        when ensino = 'fundamental' and anos_escolares like 'finais%'   then 'ef_anos_finais'
        when ensino = 'medio'                                           then 'em'
    end as etapa,
    ideb
from src
where ideb is not null
