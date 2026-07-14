-- IDEB (formato longo na origem): normaliza a etapa e mantém IDEB + notas SAEB (Mat/Port).
-- As notas SAEB são os componentes de PROFICIÊNCIA do IDEB (o outro componente é o
-- rendimento/aprovação). Carregá-las permite decompor o índice e enxergar o baque da
-- pandemia que a taxa de aprovação mascara. A decisão está documentada no README.
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
    ideb,
    nota_saeb_matematica        as saeb_matematica,
    nota_saeb_lingua_portuguesa as saeb_lingua_portuguesa
from src
where ideb is not null
