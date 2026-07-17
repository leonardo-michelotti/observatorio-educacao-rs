-- O contrato do mart exige uma única observação por indicador, nível, etapa e ano.
select indicador, nivel, etapa, ano, count(*) as quantidade
from {{ ref('fct_indicadores') }}
group by indicador, nivel, etapa, ano
having count(*) > 1
